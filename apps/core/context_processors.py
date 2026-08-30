"""
Context processors for global template context.
معالجات السياق للسياق العام للقوالب
"""
from django.conf import settings
from apps.leads.models import Lead, LeadType
from apps.leads.countries import ALL_COUNTRIES, DEFAULT_COUNTRY, DEFAULT_CODE, DEFAULT_PLACEHOLDER, get_country_info
from apps.core.models import SiteSettings


def dashboard_context(request):
    """
    Add dashboard-specific context to all templates.
    إضافة سياق خاص بلوحة التحكم إلى جميع القوالب
    
    Provides:
    - unread_leads_count: Number of unread leads for badge display
    - unread_registrations_count: Number of unread registration requests
    - unread_contacts_count: Number of unread general inquiries
    """
    context = {}
    
    # Only add dashboard context if user is authenticated and accessing dashboard
    dashboard_segment = f"/{settings.DASHBOARD_URL.strip('/')}"
    is_dashboard = request.path == dashboard_segment or request.path.startswith(f"{dashboard_segment}/")
    if request.user.is_authenticated and is_dashboard:
        unread_leads_count = Lead.objects.filter(is_read=False).count()
        context['unread_leads_count'] = unread_leads_count
        context['unread_registrations_count'] = Lead.objects.filter(lead_type=LeadType.REGISTRATION, is_read=False).count()
        context['unread_contacts_count'] = Lead.objects.filter(lead_type=LeadType.CONTACT, is_read=False).count()
    else:
        context['unread_leads_count'] = 0
        context['unread_registrations_count'] = 0
        context['unread_contacts_count'] = 0
    
    return context


def site_settings_context(request):
    """
    Add site settings and SEO configs to all templates.
    إضافة إعدادات الموقع وإعدادات SEO إلى جميع القوالب
    
    Provides:
    - site_settings: SiteSettings singleton instance
    - GA4_MEASUREMENT_ID: From database (fallback to .env)
    - GOOGLE_SITE_VERIFICATION: From database (fallback to .env)
    - ENABLE_GA4: From database
    """
    from django.conf import settings
    
    try:
        # Use request-level cache to avoid duplicate DB query when middleware already fetched it
        if hasattr(request, '_site_settings'):
            site_settings = request._site_settings
        else:
            site_settings = SiteSettings.get_settings()
            request._site_settings = site_settings
        
        # Only use database settings
        ga4_id = site_settings.ga4_measurement_id if site_settings else ''
        enable_ga4 = site_settings.enable_ga4 if site_settings else True
        
    except Exception:
        site_settings = None
        ga4_id = ''
        enable_ga4 = True
    
    return {
        'site_settings': site_settings,
        'GA4_MEASUREMENT_ID': ga4_id,
        'ENABLE_GA4': enable_ga4,
    }


def phone_countries_context(request):
    """
    Add phone country codes to templates that need the lead form.
    إضافة أكواد الدول للقوالب التي تحتاج فورم التواصل مع اكتشاف دولة الزائر من الـ Proxy Headers
    """
    # Only load for public pages (not dashboard)
    dashboard_segment = f"/{settings.DASHBOARD_URL.strip('/')}"
    is_dashboard = request.path == dashboard_segment or request.path.startswith(f"{dashboard_segment}/")
    if is_dashboard:
        return {}

    # Try detecting user's country from proxy headers (Cloudflare, Vercel, GeoIP)
    detected_iso = None
    for header in ('HTTP_CF_IPCOUNTRY', 'HTTP_X_VERCEL_IP_COUNTRY', 'GEOIP_COUNTRY_CODE', 'HTTP_X_COUNTRY_CODE'):
        val = request.META.get(header)
        if val and val.lower() != 'xx' and len(val) == 2:
            detected_iso = val.lower()
            break

    default_country, default_code, default_placeholder = get_country_info(detected_iso)
    
    return {
        'phone_countries': ALL_COUNTRIES,
        'default_country': default_country,
        'default_code': default_code,
        'default_placeholder': default_placeholder,
    }


def mega_menu_context(request):
    """
    Globally injects cached menu data for Universities and Institutes.
    Filters out helper/auxiliary pages.
    """
    # Only load for public pages (not dashboard or admin)
    dashboard_segment = f"/{settings.DASHBOARD_URL.strip('/')}"
    admin_segment = f"/{settings.ADMIN_URL.strip('/')}"
    is_dashboard = request.path == dashboard_segment or request.path.startswith(f"{dashboard_segment}/")
    is_admin = request.path == admin_segment or request.path.startswith(f"{admin_segment}/")
    if is_dashboard or is_admin:
        return {}
    
    # Skip during testing to avoid extra queries in assert_num_queries tests
    if getattr(settings, 'TESTING', False):
        return {
            'menu_public_univs': [],
            'menu_private_univs': [],
            'menu_institutes': [],
            'menu_major_categories': [],
        }
    
    from django.core.cache import cache
    from django.db.models import Count, Q
    from apps.universities.models import University
    from apps.institutes.models import Institute
    from apps.majors.models import MajorCategory
    from apps.core.navigation import get_all_navigation_slots_dict, build_curated_list_with_dedup_fallback
    
    menu_data = cache.get('mega_menu_data')
    if not menu_data:
        all_slots = get_all_navigation_slots_dict()
        public_slots = all_slots.get('mega_menu_public_univ', {})
        private_slots = all_slots.get('mega_menu_private_univ', {})
        institute_slots = all_slots.get('mega_menu_institute', {})

        # Public Universities Pool
        public_pool = (
            University.objects.filter(publish_status='published', university_type='public')
            .exclude(slug__icontains='السكن')
            .exclude(slug__icontains='الاعترافات')
            .exclude(slug__icontains='التعاقدات')
            .exclude(slug__startswith='سكن-')
            .order_by('order', 'name')
        )
        public_univs = build_curated_list_with_dedup_fallback(public_slots, public_pool, 8, append_remaining=True)

        # Private Universities Pool
        private_pool = (
            University.objects.filter(publish_status='published', university_type='private')
            .exclude(slug__icontains='السكن')
            .exclude(slug__icontains='الاعترافات')
            .exclude(slug__icontains='التعاقدات')
            .exclude(slug__startswith='سكن-')
            .order_by('order', 'name')
        )
        private_univs = build_curated_list_with_dedup_fallback(private_slots, private_pool, 8, append_remaining=True)

        # Language Institutes Pool
        institute_pool = (
            Institute.objects.filter(publish_status='published')
            .exclude(slug__icontains='اختبار')
            .exclude(slug__icontains='معاهد')
            .order_by('order', 'name')
        )
        institutes = build_curated_list_with_dedup_fallback(institute_slots, institute_pool, 8, append_remaining=True)

        # Fetch Major Categories with at least one published major
        major_categories = list(
            MajorCategory.objects.annotate(
                num_majors=Count('majors', filter=Q(majors__publish_status='published'))
            )
            .filter(num_majors__gt=0)
            .order_by('sort_order', 'name')
        )

        menu_data = {
            'menu_public_univs': public_univs,
            'menu_private_univs': private_univs,
            'menu_institutes': institutes,
            'menu_major_categories': major_categories,
        }
        
        # Cache results for 24 hours
        cache.set('mega_menu_data', menu_data, 86400)

    return menu_data

