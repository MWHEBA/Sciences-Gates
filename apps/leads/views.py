"""
Views for lead form submissions.
نماذج تقديم الرسائل والاستفسارات
"""
from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from apps.seo.mixins import BreadcrumbMixin
from apps.seo.breadcrumbs import BreadcrumbTrail
from .models import Lead
from .forms import LeadForm, ContactLeadForm, RegistrationLeadForm



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

    def get_success_url(self):
        import urllib.parse
        lead_type = self.request.POST.get('lead_type') or 'contact'
        name = self.request.POST.get('name', '').strip()
        referer = self.request.META.get('HTTP_REFERER', '').lower()
        subtype = 'institute' if 'institute' in referer else 'university'
        encoded_name = urllib.parse.quote(name)
        return f"{reverse('leads:thank_you')}?lead_type={lead_type}&subtype={subtype}&name={encoded_name}"

    def post(self, request, *args, **kwargs):
        from django.core.cache import cache
        from apps.core.utils import get_client_ip
        ip_address = get_client_ip(request)
        rate_key = f"lead_rate_limit_{ip_address}"
        from django.conf import settings
        is_testing = getattr(settings, 'TESTING', False)
        submissions = cache.get(rate_key, 0)
        
        if submissions >= 5 and not is_testing:
            messages.error(
                request, 
                'لقد قمت بإرسال الحد الأقصى المسموح به من الاستفسارات (5 طلبات في الساعة) لحماية الخدمة وضمان جودة المتابعة. طلباتك السابقة وصلت وسيتواصل معك مستشارنا قريباً، أو يمكنك التواصل المباشر عبر الواتساب للاستجابة الفورية.'
            )
            form = self.get_form()
            # Set attribute so form_invalid won't append generic error message
            self.rate_limit_exceeded = True
            return super().form_invalid(form)
            
        cache.set(rate_key, submissions + 1, 3600)
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
        """
        # Get form data
        lead = form.save(commit=False)
        
        # Extract source page from request
        lead.source_page = self.request.build_absolute_uri(self.request.path)
        
        # Extract referrer from request headers
        lead.referrer = self.request.META.get('HTTP_REFERER', '')
        

        # Save lead to database
        lead.save()
        
        # Redirect to thank you page
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """
        Handle invalid form submission.
        
        Display error messages and re-render form.
        """
        import logging
        logging.getLogger(__name__).warning(f"Lead form submission invalid. Form errors: {form.errors.as_json()}")

        # Only add generic error if rate limit was not the cause
        if not getattr(self, 'rate_limit_exceeded', False):
            messages.error(
                self.request,
                'حدث خطأ في النموذج. يرجى التحقق من البيانات المدخلة.'
            )
        
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

    lead_type_str = 'طلب التسجيل' if lead_type == 'registration' else 'الاستفسار'
    if lead_name:
        wa_text = f"مرحباً شركة بوابات العلوم، قمت بالتقديم عبر الموقع لـ ({lead_type_str}) باسم: {lead_name}، وأود المتابعة معكم."
    else:
        wa_text = f"مرحباً شركة بوابات العلوم، قمت بالتقديم عبر الموقع لـ ({lead_type_str}) وأود المتابعة معكم لسرعة الإجراءات."

    whatsapp_prefilled_encoded = urllib.parse.quote(wa_text)

    context = {
        'whatsapp_clean': whatsapp_clean,
        'whatsapp_prefilled_encoded': whatsapp_prefilled_encoded,
    }
    return render(request, 'leads/thank_you.html', context)


