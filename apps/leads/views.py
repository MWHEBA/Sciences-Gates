"""
Views for lead form submissions.
نماذج تقديم الرسائل والاستفسارات
"""
from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from apps.seo.mixins import BreadcrumbMixin
from apps.seo.breadcrumbs import BreadcrumbTrail
from .models import Lead
from .forms import LeadForm


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
    form_class = LeadForm
    template_name = 'leads/submit.html'
    success_url = reverse_lazy('leads:thank_you')
    
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
        
        # Extract UTM parameters from GET query string
        lead.utm_source = self.request.GET.get('utm_source', '')
        lead.utm_medium = self.request.GET.get('utm_medium', '')
        lead.utm_campaign = self.request.GET.get('utm_campaign', '')
        lead.utm_term = self.request.GET.get('utm_term', '')
        lead.utm_content = self.request.GET.get('utm_content', '')
        
        # Save lead to database
        lead.save()
        
        # Add success message in Arabic
        messages.success(
            self.request,
            'تم استقبال استفسارك بنجاح. سيتم التواصل معك قريباً.'
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

