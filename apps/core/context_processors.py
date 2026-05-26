"""
Context processors for global template context.
معالجات السياق للسياق العام للقوالب
"""
from apps.leads.models import Lead
from apps.leads.countries import ALL_COUNTRIES, DEFAULT_COUNTRY, DEFAULT_CODE, DEFAULT_PLACEHOLDER
from apps.core.models import SiteSettings


def dashboard_context(request):
    """
    Add dashboard-specific context to all templates.
    إضافة سياق خاص بلوحة التحكم إلى جميع القوالب
    
    Provides:
    - unread_leads_count: Number of unread leads for badge display
    """
    context = {}
    
    # Only add dashboard context if user is authenticated and accessing dashboard
    if request.user.is_authenticated and 'dashboard' in request.path:
        unread_leads_count = Lead.objects.filter(is_read=False).count()
        context['unread_leads_count'] = unread_leads_count
    else:
        context['unread_leads_count'] = 0
    
    return context


def site_settings_context(request):
    """
    Add site settings to all templates.
    إضافة إعدادات الموقع إلى جميع القوالب
    
    Provides:
    - site_settings: SiteSettings singleton instance
    """
    try:
        site_settings = SiteSettings.get_settings()
    except Exception:
        site_settings = None
    
    return {'site_settings': site_settings}


def phone_countries_context(request):
    """
    Add phone country codes to templates that need the lead form.
    إضافة أكواد الدول للقوالب التي تحتاج فورم التواصل
    """
    # Only load for public pages (not dashboard)
    if 'dashboard' in request.path:
        return {}
    
    return {
        'phone_countries': ALL_COUNTRIES,
        'default_country': DEFAULT_COUNTRY,
        'default_code': DEFAULT_CODE,
        'default_placeholder': DEFAULT_PLACEHOLDER,
    }
