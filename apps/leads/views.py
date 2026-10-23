"""
Views for lead form submissions.
نماذج تقديم الرسائل والاستفسارات
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.generic import FormView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from apps.seo.mixins import BreadcrumbMixin
from apps.seo.breadcrumbs import BreadcrumbTrail
from .models import Lead, LeadType, LeadRejectionLog
from .forms import LeadForm, ContactLeadForm, RegistrationLeadForm, normalize_phone
import logging
import re

logger = logging.getLogger('apps.leads.submissions')

def _is_ajax(request):
    """Detect fetch / AJAX requests expecting JSON."""
    return (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.META.get('HTTP_ACCEPT', '')
        or request.content_type == 'application/json'
    )

# Rate limiting (per hour). Every POST counts toward the per-IP cap, but only
# accepted leads count toward the per-IP+phone cap, so a visitor correcting a
# validation error is never locked out by their own retries.
RATE_LIMIT_WINDOW_SECONDS = 3600
MAX_POSTS_PER_IP = 60
MAX_ACCEPTED_PER_IP_PHONE = 20


def _source_kind(request):
    """Classify where a submission came from (for diagnostics only)."""
    ref = ((request.POST.get('source_page') or '') + ' ' + request.META.get('HTTP_REFERER', '')).lower()
    for kind, needle in (
        ('contact', '/contact'), ('university', '/universities/'), ('institute', '/institutes/'),
        ('major', '/majors/'), ('submit-page', '/leads/submit'),
    ):
        if needle in ref:
            return kind
    return 'other'


def _error_summary(form):
    """Field names and error codes only (never the submitted values)."""
    parts = []
    for field, errs in form.errors.as_data().items():
        codes = ','.join(sorted({(e.code or 'invalid') for e in errs}))
        parts.append(f"{field}[{codes}]")
    return ' '.join(parts)



class LeadSubmitView(BreadcrumbMixin, FormView):
    """
    Handle lead form submissions from public site.
    
    Features:
    - Extracts UTM parameters from GET query string
    - Extracts source_page from request.path
    - Extracts referrer from request.META['HTTP_REFERER']
    - Validates CSRF token (automatic with FormView)
    - Implements honeypot spam protection
    - Saves lead to database
    - Redirects to thank you page
    - Displays success message in Arabic
    
    Requirements: 5, 18
    """
    form_class = ContactLeadForm
    template_name = 'leads/submit.html'
    
    def get(self, request, *args, **kwargs):
        """
        Clear any lingering success messages from prior form submissions when loading
        the GET submit page, preventing unexpected success banners upon page entrance.
        """
        storage = messages.get_messages(request)
        remaining_messages = []
        for message in storage:
            if message.level != messages.SUCCESS:
                remaining_messages.append(message)
        
        for msg in remaining_messages:
            messages.add_message(request, msg.level, msg.message, extra_tags=msg.extra_tags)

        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        import urllib.parse
        lead_type = self.request.POST.get('lead_type') or 'contact'
        name = self.request.POST.get('name', '').strip()
        institution_name = self.request.POST.get('institution_name', '').strip()
        referer = self.request.META.get('HTTP_REFERER', '').lower()
        source_page = (self.request.POST.get('source_page') or '').lower()
        
        # Determine exact subtype
        if 'institutes' in referer or 'institutes' in source_page or 'institute' in referer or 'institute' in source_page:
            subtype = 'institute'
        elif 'majors' in referer or 'majors' in source_page or 'courses' in referer or 'courses' in source_page:
            subtype = 'major'
        elif 'universities' in referer or 'universities' in source_page or 'university' in referer or 'university' in source_page:
            subtype = 'university'
        else:
            subtype = 'university'

        # If lead was created and resolved entity name
        created_lead = getattr(self, 'created_lead', None)
        if not institution_name and created_lead:
            institution_name = created_lead.source_entity_short

        encoded_name = urllib.parse.quote(name)
        encoded_institution = urllib.parse.quote(institution_name)
        return f"{reverse('leads:thank_you')}?lead_type={lead_type}&subtype={subtype}&name={encoded_name}&institution={encoded_institution}"

    def _log_outcome(self, outcome, reason='', level=logging.INFO, **extra):
        """One structured line per submission outcome: accepted / rejected + reason code."""
        from apps.core.utils import get_client_ip
        request = self.request
        extra_str = ' '.join(f"{k}={v}" for k, v in extra.items())
        client_ip = get_client_ip(request)
        source_kind = _source_kind(request)
        lead_type = request.POST.get('lead_type') or 'contact'
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:300]
        source_page = request.POST.get('source_page', '')[:500]

        logger.log(
            level,
            'lead_%s reason=%s type=%s source=%s ip=%s has_csrf_cookie=%s ua=%r %s',
            outcome, reason or '-', lead_type, source_kind,
            client_ip, 'csrftoken' in request.COOKIES,
            user_agent[:160], extra_str,
        )

        # In Phase 5, if the outcome is rejected, record it into LeadRejectionLog for telemetry
        if outcome == 'rejected':
            try:
                LeadRejectionLog.objects.create(
                    reason=reason or 'unknown',
                    lead_type=lead_type,
                    source_kind=source_kind,
                    source_page=source_page,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    details=extra,
                )
            except Exception as e:
                logger.error("Failed to persist LeadRejectionLog: %s", e)

    def _is_testing(self):
        from django.conf import settings
        import sys
        # If explicitly testing rate limits or disabled bypass, do not bypass
        if getattr(settings, 'ENFORCE_RATE_LIMIT_IN_TESTS', False):
            return False
        return getattr(settings, 'TESTING', False) or 'test' in sys.argv

    def _rate_limited_response(self, reason):
        """Visible, explicit rejection when a rate limit is exceeded (never silent)."""
        self._log_outcome('rejected', reason, level=logging.WARNING)
        rate_limit_msg = 'تم تجاوز الحد المسموح به من الطلبات خلال الساعة الأخيرة لحماية الخدمة. طلباتك السابقة وصلت وسيتواصل معك مستشارنا قريباً، أو يمكنك التواصل المباشر عبر الواتساب للاستجابة الفورية.'
        if _is_ajax(self.request):
            return JsonResponse({
                'success': False,
                'rate_limit': True,
                'message': rate_limit_msg,
            }, status=429)

        messages.error(
            self.request,
            rate_limit_msg
        )
        # Set attribute so form_invalid won't append generic error message
        self.rate_limit_exceeded = True
        return super().form_invalid(self.get_form())

    def post(self, request, *args, **kwargs):
        from django.core.cache import cache
        from apps.core.utils import get_client_ip
        ip_address = get_client_ip(request)
        post_key = f"lead_post_count_{ip_address}"
        posts = cache.get(post_key, 0)

        if posts >= MAX_POSTS_PER_IP and not self._is_testing():
            return self._rate_limited_response('rate_limit_ip')

        cache.set(post_key, posts + 1, RATE_LIMIT_WINDOW_SECONDS)
        return super().post(request, *args, **kwargs)

    def get_form_class(self):
        lead_type = self.request.POST.get('lead_type') or self.request.GET.get('lead_type') or 'contact'
        if lead_type == 'registration':
            return RegistrationLeadForm
        return ContactLeadForm
    
    def get_breadcrumbs(self):
        """Define breadcrumbs for lead submit page."""
        return (BreadcrumbTrail()
            .add_section('home')
            .current('تقديم استفسار')
            .build())
            
    def get_context_data(self, **kwargs):
        """Add source page to context for form."""
        context = super().get_context_data(**kwargs)
        # Pass source page to template for hidden field
        context['source_page'] = self.request.build_absolute_uri(self.request.path)
        return context
    
    def form_valid(self, form):
        """
        Process valid form submission.
        
        Extracts tracking information and saves lead to database.
        Includes server-side deduplication against rapid double-clicks (within 10 seconds).
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Q

        email = form.cleaned_data.get('email', '').strip().lower()
        phone = form.cleaned_data.get('phone', '').strip()
        lead_type = form.cleaned_data.get('lead_type')
        institution_name = form.cleaned_data.get('institution_name', '').strip()

        from django.core.cache import cache
        from apps.core.utils import get_client_ip
        ip_address = get_client_ip(self.request)

        # Honeypot tripped: never drop silently. Store the lead flagged as suspected
        # spam (archived, no notifications) and answer with the normal success flow,
        # so a real visitor falsely tripped (e.g. by autofill) is never lost.
        if getattr(form, 'honeypot_tripped', False):
            lead = form.save(commit=False)
            lead.ip_address = ip_address
            lead.is_suspected_spam = True
            lead.is_archived = True
            lead.is_read = True
            lead.save()
            self.created_lead = lead
            self._log_outcome('rejected', 'honeypot', level=logging.WARNING, flagged_saved='yes')
            if _is_ajax(self.request):
                return JsonResponse({
                    'success': True,
                    'redirect_url': self.get_success_url(),
                    'message': 'تم استقبال استفسارك بنجاح! سنتواصل معك في أقرب وقت.'
                })
            messages.success(self.request, 'تم استقبال استفسارك بنجاح! سنتواصل معك في أقرب وقت.')
            return super().form_valid(form)

        # Accepted-lead cap per IP + normalized phone (invalid attempts never count)
        phone_digits = re.sub(r'\D', '', normalize_phone(phone) or '')
        phone_key = f"lead_accepted_{ip_address}_{phone_digits}"
        accepted_count = cache.get(phone_key, 0)
        if phone_digits and accepted_count >= MAX_ACCEPTED_PER_IP_PHONE and not self._is_testing():
            return self._rate_limited_response('rate_limit_phone')

        # Double-submit guard: If an identical lead (by email or phone) was saved in the last 10 seconds, skip duplicate creation
        if (email or phone) and lead_type:
            time_window = timezone.now() - timedelta(seconds=10)
            dup_query = Q(lead_type=lead_type, created_at__gte=time_window)
            if email and phone:
                dup_query &= (Q(email__iexact=email) | Q(phone=phone))
            elif email:
                dup_query &= Q(email__iexact=email)
            else:
                dup_query &= Q(phone=phone)

            if institution_name:
                dup_query &= Q(institution_name=institution_name)

            recent_duplicate = Lead.objects.filter(dup_query).first()
            if recent_duplicate:
                self.created_lead = recent_duplicate
                succ_msg = 'تم استقبال طلب التسجيل بنجاح! سنتواصل معك في أقرب وقت.' if lead_type == LeadType.REGISTRATION else 'تم استقبال استفسارك بنجاح! سنتواصل معك في أقرب وقت.'
                if _is_ajax(self.request):
                    return JsonResponse({
                        'success': True,
                        'redirect_url': self.get_success_url(),
                        'message': succ_msg
                    })
                messages.success(self.request, succ_msg)
                return super().form_valid(form)

        # Save lead to database using form.save()
        lead = form.save(commit=False)
        
        from apps.core.utils import get_client_ip
        lead.ip_address = get_client_ip(self.request)
        
        # Save lead to database
        lead.save()
        self.created_lead = lead

        # Increment accepted count for this IP + phone combination
        if phone_digits:
            cache.set(phone_key, accepted_count + 1, RATE_LIMIT_WINDOW_SECONDS)

        self._log_outcome('accepted', lead_id=lead.pk, lead_type=lead.lead_type)
        
        # Add success message based on lead type
        succ_msg = 'تم استقبال طلب التسجيل بنجاح! سنتواصل معك في أقرب وقت.' if lead.lead_type == LeadType.REGISTRATION else 'تم استقبال استفسارك بنجاح! سنتواصل معك في أقرب وقت.'
        if _is_ajax(self.request):
            return JsonResponse({
                'success': True,
                'redirect_url': self.get_success_url(),
                'message': succ_msg
            })

        messages.success(self.request, succ_msg)

        # Redirect to thank you page
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """
        Handle invalid form submission.
        
        Display error messages and re-render form or redirect back to entity source page.
        """
        # Log validation rejection unless rate_limit_exceeded already logged it
        if not getattr(self, 'rate_limit_exceeded', False):
            self._log_outcome(
                'rejected',
                'validation:' + _error_summary(form),
                level=logging.WARNING,
                errors=form.errors.get_json_data()
            )
            first_error = ""
            for field, errs in form.errors.items():
                if errs:
                    first_error = str(errs[0])
                    break
            err_msg = f"حدث خطأ في النموذج: {first_error}" if first_error else "حدث خطأ في النموذج. يرجى التحقق من البيانات المدخلة."

            if _is_ajax(self.request):
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.get_json_data(),
                    'message': err_msg,
                }, status=400)

            messages.error(
                self.request,
                err_msg
            )
        elif _is_ajax(self.request):
            return JsonResponse({
                'success': False,
                'rate_limit': True,
                'message': 'تم تجاوز الحد المسموح به من الطلبات خلال الساعة الأخيرة لحماية الخدمة.',
            }, status=429)
        
        # If submission originated from university/institute detail modal, redirect back to that page
        source_page = self.request.POST.get('source_page', '').strip()
        if source_page and ('/universities/' in source_page or '/institutes/' in source_page):
            from django.utils.http import url_has_allowed_host_and_scheme
            allowed_hosts = {self.request.get_host(), 'sciencesgates.com', 'www.sciencesgates.com', 'localhost:8000', '127.0.0.1:8000'}
            if url_has_allowed_host_and_scheme(source_page, allowed_hosts=allowed_hosts, require_https=self.request.is_secure()):
                # R1 / Phase 2: Preserve entered data in session and signal template to reopen modal with inline errors
                if hasattr(self.request, 'session'):
                    self.request.session['reg_modal_reopen'] = True
                    self.request.session['reg_modal_data'] = {
                        'name': self.request.POST.get('name', ''),
                        'email': self.request.POST.get('email', ''),
                        'phone_number': self.request.POST.get('phone_number', ''),
                        'nationality': self.request.POST.get('nationality', ''),
                        'custom_nationality': self.request.POST.get('custom_nationality', ''),
                        'study_level': self.request.POST.get('study_level', ''),
                        'residence_country': self.request.POST.get('residence_country', ''),
                        'address': self.request.POST.get('address', ''),
                        'notes': self.request.POST.get('notes', ''),
                    }
                return redirect(source_page)
        
        return super().form_invalid(form)


def thank_you_view(request):
    """
    Display thank you message after lead submission.
    
    Prepares dynamic pre-filled WhatsApp link context for immediate student follow-up.
    """
    import urllib.parse
    from apps.core.models import SiteSettings
    try:
        site_settings = request._site_settings if hasattr(request, '_site_settings') else SiteSettings.get_settings()
        whatsapp_clean = site_settings.whatsapp_primary_clean or '60182638888'
    except Exception:
        whatsapp_clean = '60182638888'

    lead_type = request.GET.get('lead_type', 'contact')
    lead_name = request.GET.get('name', '').strip()
    institution = request.GET.get('institution', '').strip()

    lead_type_str = 'طلب التسجيل' if lead_type == 'registration' else 'الاستفسار'
    if institution and lead_name:
        wa_text = f"مرحباً شركة بوابات العلوم، قمت بالتقديم عبر الموقع لـ ({lead_type_str} في {institution}) باسم: {lead_name}، وأود المتابعة معكم."
    elif institution:
        wa_text = f"مرحباً شركة بوابات العلوم، قمت بالتقديم عبر الموقع لـ ({lead_type_str} في {institution})، وأود المتابعة معكم."
    elif lead_name:
        wa_text = f"مرحباً شركة بوابات العلوم، قمت بالتقديم عبر الموقع لـ ({lead_type_str}) باسم: {lead_name}، وأود المتابعة معكم."
    else:
        wa_text = f"مرحباً شركة بوابات العلوم، قمت بالتقديم عبر الموقع لـ ({lead_type_str}) وأود المتابعة معكم لسرعة الإجراءات."

    whatsapp_prefilled_encoded = urllib.parse.quote(wa_text)

    context = {
        'whatsapp_clean': whatsapp_clean,
        'whatsapp_prefilled_encoded': whatsapp_prefilled_encoded,
    }
    return render(request, 'leads/thank_you.html', context)


