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
    
    def get_success_url(self):
        lead_type = self.request.POST.get('lead_type') or 'contact'
        referer = self.request.META.get('HTTP_REFERER', '').lower()
        subtype = 'institute' if 'institute' in referer else 'university'
        return f"{reverse('leads:thank_you')}?lead_type={lead_type}&subtype={subtype}"

    def post(self, request, *args, **kwargs):
        from django.core.cache import cache
        from apps.core.utils import get_client_ip
        ip_address = get_client_ip(request)
        rate_key = f"lead_rate_limit_{ip_address}"
        submissions = cache.get(rate_key, 0)
        
        if submissions >= 3:
            messages.error(request, 'تم تجاوز الحد الأقصى للطلبات المسموحة في الساعة. يرجى المحاولة لاحقاً.')
            form = self.get_form()
            return self.form_invalid(form)
            
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
        
        # Add success message in Arabic
        if lead.lead_type == 'registration':
            msg = 'تم استقبال طلب التسجيل بنجاح. سيتم التواصل معك قريباً.'
        else:
            msg = 'تم استقبال استفسارك بنجاح. سيتم التواصل معك قريباً.'
            
        messages.success(
            self.request,
            msg
        )
        
        # Redirect to thank you page
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """
        Handle invalid form submission.
        
        Display error messages and re-render form.
        """
        # Add error message in Arabic
        messages.error(
            self.request,
            'حدث خطأ في النموذج. يرجى التحقق من البيانات المدخلة.'
        )
        
        return super().form_invalid(form)


def thank_you_view(request):
    """
    Display thank you message after lead submission.
    
    Shows success message and provides link back to home page.
    """
    return render(request, 'leads/thank_you.html')

