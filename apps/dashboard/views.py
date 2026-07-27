"""
Dashboard views for authentication and dashboard management.
"""
import logging

logger = logging.getLogger(__name__)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from datetime import timedelta
from django.db import transaction
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from apps.leads.models import Lead, LeadType
from apps.redirects.models import Redirect
from apps.universities.models import University, Faculty, Program
from apps.institutes.models import Institute, Course
from apps.majors.models import Major, MajorCategory
from apps.articles.models import Article, Category, Tag, IgnoredSimilarity
from apps.core.models import SiteSettings, ContentLock, UserProfile, UserRole
from apps.dashboard.mixins import SuperAdminRequiredMixin, SEOAdminRequiredMixin, ContentAdminRequiredMixin, ContentOrSEOAdminRequiredMixin, DashboardMixin
from apps.dashboard.forms import (
    UserCreateForm, UserUpdateForm, RedirectForm, 
    UniversityForm, UniversityFAQFormSet, UniversityFacultyFormSet, FacultyForm, ProgramFormSet, UniversityAttachmentFormSet,
    InstituteForm, CourseFormSet, InstituteAttachmentFormSet, InstituteFAQFormSet,
    MajorForm, MajorCategoryForm, SubjectsTableFormSet, SalaryTableFormSet, CountriesTableFormSet, MajorFAQFormSet, MajorAttachmentFormSet,
    ArticleForm, ArticleFAQFormSet, ArticleAttachmentFormSet, CategoryForm, TagForm, SiteSettingsForm, SiteSEOSettingsForm,
    DashboardPasswordResetForm
)
from apps.articles.models import Category, Tag
from apps.seo.mixins import DashboardBreadcrumbMixin
from apps.seo.breadcrumbs import BreadcrumbTrail


class DashboardLoginView(View):
    """
    Handle user login to the dashboard.
    يتعامل مع تسجيل دخول المستخدمين إلى لوحة التحكم
    """
    template_name = 'dashboard/login.html'

    @method_decorator(csrf_protect)
    def get(self, request):
        """Display login form."""
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('dashboard:home')
            else:
                return redirect('home')
        return render(request, self.template_name)

    @method_decorator(csrf_protect)
    def post(self, request):
        """Handle login form submission."""
        from django.utils.http import url_has_allowed_host_and_scheme
        from django.core.cache import cache
        
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', request.GET.get('next', ''))

        # Lockout check by IP
        ip_address = request.META.get('REMOTE_ADDR')
        lockout_key = f"login_lockout_{ip_address}"
        attempts_key = f"login_attempts_{ip_address}"
        
        if cache.get(lockout_key):
            messages.error(request, 'تم قفل محاولات تسجيل الدخول مؤقتاً بسبب عدد كبير من المحاولات الخاطئة. يرجى المحاولة بعد قليل.')
            return render(request, self.template_name, {'next': next_url})

        if not username or not password:
            messages.error(request, 'يرجى إدخال اسم المستخدم وكلمة المرور')
            return render(request, self.template_name, {'next': next_url})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if user is staff (has dashboard access)
            if not user.is_staff:
                messages.error(request, 'ليس لديك صلاحيات للوصول إلى لوحة التحكم')
                return render(request, self.template_name, {'next': next_url})

            # Clear attempts on successful login
            cache.delete(attempts_key)
            cache.delete(lockout_key)

            login(request, user)
            messages.success(request, f'أهلاً وسهلاً {user.first_name or user.username}')
            
            # Redirect to next URL if provided and safe, otherwise to home
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard:home')
        else:
            # Increment attempts
            attempts = cache.get(attempts_key, 0) + 1
            cache.set(attempts_key, attempts, 300)  # Reset attempts after 5 minutes
            if attempts >= 5:
                cache.set(lockout_key, True, 900)  # Lockout for 15 minutes
                messages.error(request, 'تم قفل محاولات تسجيل الدخول مؤقتاً بسبب محاولات خاطئة متتالية. يرجى المحاولة بعد 15 دقيقة.')
            else:
                messages.error(request, f'اسم المستخدم أو كلمة المرور غير صحيحة. المحاولات المتبقية: {5 - attempts}')
            return render(request, self.template_name, {'username': username, 'next': next_url})


class DashboardLogoutView(View):
    """
    Handle user logout from the dashboard.
    يتعامل مع تسجيل خروج المستخدمين من لوحة التحكم
    """

    @method_decorator(login_required(login_url='dashboard:login'))
    def get(self, request):
        """Handle logout."""
        logout(request)
        messages.success(request, 'تم تسجيل الخروج بنجاح')
        return redirect('dashboard:login')


class DashboardPasswordResetView(PasswordResetView):
    """
    طلب استعادة كلمة المرور للمستخدمين الإداريين
    """
    template_name = 'dashboard/auth/password_reset_form.html'
    form_class = DashboardPasswordResetForm
    email_template_name = 'dashboard/auth/password_reset_email.txt'
    html_email_template_name = 'dashboard/auth/password_reset_email.html'
    subject_template_name = 'dashboard/auth/password_reset_subject.txt'
    success_url = reverse_lazy('dashboard:password_reset_done')

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
            'domain_override': self.request.get_host(),
        }
        form.save(**opts)
        return redirect(self.get_success_url())


class DashboardPasswordResetDoneView(PasswordResetDoneView):
    """
    تأكيد إرسال رابط استعادة كلمة المرور للبريد الإلكتروني
    """
    template_name = 'dashboard/auth/password_reset_done.html'


class DashboardPasswordResetConfirmView(PasswordResetConfirmView):
    """
    إدخال كلمة المرور الجديدة وتأكيدها باستخدام الرابط المرسل
    """
    template_name = 'dashboard/auth/password_reset_confirm.html'
    success_url = reverse_lazy('dashboard:password_reset_complete')


class DashboardPasswordResetCompleteView(PasswordResetCompleteView):
    """
    تأكيد إتمام تعيين كلمة المرور الجديدة بنجاح
    """
    template_name = 'dashboard/auth/password_reset_complete.html'


class DashboardHomeView(DashboardMixin, View):
    """
    Dashboard home page with statistics.
    صفحة لوحة التحكم الرئيسية مع الإحصائيات
    
    Displays:
    - Total leads count
    - Leads by type (REGISTRATION, CONTACT)
    - Current month leads
    - Published content counts (Universities, Institutes, Majors, Articles)
    - Recent 10 leads in a table
    
    Query Optimization:
    - Uses aggregation for lead statistics to minimize database queries
    - Prefetches recent leads without unnecessary relationships
    """
    template_name = 'dashboard/home.html'
    login_url = 'dashboard:login'

    def get(self, request):
        """Display dashboard home with statistics."""
        from django.db.models import Count, Q
        
        # Calculate lead statistics - optimized with aggregation
        today = timezone.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (first_day_of_month - timedelta(days=1)).replace(day=1)
        
        # Get all statistics in a single query using aggregation
        lead_stats = Lead.objects.aggregate(
            total=Count('id'),
            registration=Count('id', filter=Q(lead_type=LeadType.REGISTRATION)),
            contact=Count('id', filter=Q(lead_type=LeadType.CONTACT)),
            this_month=Count('id', filter=Q(created_at__gte=first_day_of_month)),
            last_month=Count('id', filter=Q(
                created_at__gte=last_month_start,
                created_at__lt=first_day_of_month
            )),
            unread=Count('id', filter=Q(is_read=False)),
        )
        
        # Calculate trend percentage
        trend = 0
        if lead_stats['last_month'] > 0:
            trend = round(
                ((lead_stats['this_month'] - lead_stats['last_month'])
                 / lead_stats['last_month']) * 100
            )
        
        # Store absolute trend for template display
        trend_abs = abs(trend)
        
        # Recent 10 leads (ordered by creation date, newest first) - optimized
        recent_leads = Lead.objects.all().order_by('-created_at')[:10]
        
        # Published content counts with unpublished counts
        content_stats = {}
        
        # Try to import and count published content if models exist
        try:
            from apps.universities.models import University
            content_stats['universities'] = {
                'published': University.objects.filter(publish_status='published').count(),
                'total': University.objects.count(),
                'unpublished': University.objects.filter(publish_status='unpublished').count(),
                'list_url': reverse_lazy('dashboard:university_list'),
                'create_url': reverse_lazy('dashboard:university_create'),
            }
        except (ImportError, Exception):
            content_stats['universities'] = {
                'published': 0, 'total': 0, 'unpublished': 0,
                'list_url': '#', 'create_url': '#'
            }
        
        try:
            from apps.institutes.models import Institute
            content_stats['institutes'] = {
                'published': Institute.objects.filter(publish_status='published').count(),
                'total': Institute.objects.count(),
                'unpublished': Institute.objects.filter(publish_status='unpublished').count(),
                'list_url': reverse_lazy('dashboard:institute_list'),
                'create_url': reverse_lazy('dashboard:institute_create'),
            }
        except (ImportError, Exception):
            content_stats['institutes'] = {
                'published': 0, 'total': 0, 'unpublished': 0,
                'list_url': '#', 'create_url': '#'
            }
        
        try:
            from apps.majors.models import Major
            content_stats['majors'] = {
                'published': Major.objects.filter(publish_status='published').count(),
                'total': Major.objects.count(),
                'unpublished': Major.objects.filter(publish_status='unpublished').count(),
                'list_url': reverse_lazy('dashboard:major_list'),
                'create_url': reverse_lazy('dashboard:major_create'),
            }
        except (ImportError, Exception):
            content_stats['majors'] = {
                'published': 0, 'total': 0, 'unpublished': 0,
                'list_url': '#', 'create_url': '#'
            }
        
        try:
            from apps.articles.models import Article
            content_stats['articles'] = {
                'published': Article.objects.filter(publish_status='published').count(),
                'total': Article.objects.count(),
                'unpublished': Article.objects.filter(publish_status='unpublished').count(),
                'list_url': reverse_lazy('dashboard:article_list'),
                'create_url': reverse_lazy('dashboard:article_create'),
            }
        except (ImportError, Exception):
            content_stats['articles'] = {
                'published': 0, 'total': 0, 'unpublished': 0,
                'list_url': '#', 'create_url': '#'
            }
        
        # Calculate total pending (unpublished) content
        total_pending = sum(v['unpublished'] for v in content_stats.values())
        
        # Build a list of pending content text summaries (excluding 0 counts)
        pending_breakdown = []
        if content_stats.get('universities', {}).get('unpublished', 0) > 0:
            pending_breakdown.append(f"{content_stats['universities']['unpublished']} جامعات")
        if content_stats.get('institutes', {}).get('unpublished', 0) > 0:
            pending_breakdown.append(f"{content_stats['institutes']['unpublished']} معاهد")
        if content_stats.get('majors', {}).get('unpublished', 0) > 0:
            pending_breakdown.append(f"{content_stats['majors']['unpublished']} تخصصات")
        if content_stats.get('articles', {}).get('unpublished', 0) > 0:
            pending_breakdown.append(f"{content_stats['articles']['unpublished']} مقالات")
            
        pending_breakdown_str = "، و".join(pending_breakdown)
        
        context = {
            'page_title': 'لوحة التحكم',
            'lead_stats': lead_stats,
            'content_stats': content_stats,
            'total_pending': total_pending,
            'pending_breakdown_str': pending_breakdown_str,
            'recent_leads': recent_leads,
            'trend': trend,
            'trend_abs': trend_abs,
            # For backward compatibility
            'total_leads': lead_stats['total'],
            'registration_leads': lead_stats['registration'],
            'contact_leads': lead_stats['contact'],
            'current_month_leads': lead_stats['this_month'],
        }

        # Quick Wins from GSC — shown on home page if GSC is connected
        try:
            from apps.seo.services.gsc_client import GSCClient
            gsc = GSCClient()
            if gsc.is_connected():
                context['gsc_quick_wins'] = gsc.get_quick_wins(days=28)
                context['gsc_connected'] = True
            else:
                context['gsc_quick_wins'] = []
                context['gsc_connected'] = False
        except Exception:
            context['gsc_quick_wins'] = []
            context['gsc_connected'] = False

        return render(request, self.template_name, context)


class AnalyticsView(SEOAdminRequiredMixin, View):
    """
    Google Analytics overview page for SEO/Super admins.
    صفحة Analytics — تعرض تقارير GA4 من الكاش المحلي.
    """
    template_name = 'dashboard/analytics.html'

    def get(self, request):
        """Display analytics page with cached report data."""
        from apps.core.models import SiteSettings, GA4CachedReport

        days = int(request.GET.get('days', 28))
        if days not in (7, 14, 28, 90):
            days = 28

        try:
            site_settings = SiteSettings.get_settings()
            ga4_id = site_settings.ga4_measurement_id
            ga4_property_id = site_settings.ga4_property_id
            ga4_enabled = site_settings.enable_ga4
        except Exception:
            ga4_id = ''
            ga4_property_id = ''
            ga4_enabled = False

        context = {
            'ga4_measurement_id': ga4_id,
            'ga4_property_id': ga4_property_id,
            'ga4_enabled': ga4_enabled,
            'ga4_configured': bool(ga4_id and ga4_property_id),
            'selected_days': days,
            'report_data': None,
            'updated_at': None,
        }

        if context['ga4_configured']:
            cached_report = GA4CachedReport.objects.filter(days=days).first()
            if cached_report:
                context['report_data'] = cached_report.payload
                context['updated_at'] = cached_report.updated_at

        return render(request, self.template_name, context)


class AnalyticsRealtimeApi(SEOAdminRequiredMixin, View):
    """
    AJAX API endpoint for retrieving active users count (cached for 2 minutes).
    """
    def get(self, request):
        from apps.core.models import SiteSettings
        from apps.seo.services.ga4_client import GA4Client, GA4APIError
        from django.core.cache import cache
        from django.http import JsonResponse

        try:
            site_settings = SiteSettings.get_settings()
            property_id = site_settings.ga4_property_id
        except Exception:
            return JsonResponse({'error': 'Error loading settings'}, status=400)

        if not property_id:
            return JsonResponse({'error': 'Property ID not configured'}, status=400)

        cache_key = f"ga4_realtime_users_{property_id}"
        cached_users = cache.get(cache_key)
        
        if cached_users is not None:
            return JsonResponse({'active_users': cached_users, 'cached': True})

        client = GA4Client()
        try:
            active_users = client.get_realtime_active_users(property_id)
            cache.set(cache_key, active_users, 120)  # cache for 2 minutes
            return JsonResponse({'active_users': active_users, 'cached': False})
        except GA4APIError as exc:
            return JsonResponse({'error': str(exc)}, status=500)
        except Exception as exc:
            return JsonResponse({'error': f"Unexpected error: {str(exc)}"}, status=500)


class AnalyticsSyncApi(SEOAdminRequiredMixin, View):
    """
    AJAX API endpoint to trigger a manual forced sync of GA4 data (rate limited to once per 15 minutes).
    """
    def post(self, request):
        from apps.core.models import SiteSettings
        from django.core.cache import cache
        from django.http import JsonResponse
        from django.core.management import call_command

        try:
            site_settings = SiteSettings.get_settings()
            property_id = site_settings.ga4_property_id
        except Exception:
            return JsonResponse({'success': False, 'error': 'خطأ في تحميل الإعدادات.'}, status=400)

        if not property_id:
            return JsonResponse({'success': False, 'error': 'معرف Property ID غير معرّف في الإعدادات.'}, status=400)

        cache_key = f"ga4_sync_rate_limit_{property_id}"
        if cache.get(cache_key):
            return JsonResponse({
                'success': False, 
                'error': 'عذراً، يمكنك المزامنة مرة واحدة فقط كل 15 دقيقة لحماية كوتا جوجل.'
            }, status=429)

        try:
            # Trigger management command synchronously
            call_command('sync_ga4_data')
            # Set rate limit cache lock for 15 minutes (900 seconds)
            cache.set(cache_key, True, 900)
            return JsonResponse({'success': True, 'message': 'تمت مزامنة البيانات من Google Analytics بنجاح!'})
        except Exception as exc:
            return JsonResponse({'success': False, 'error': f"فشلت المزامنة: {str(exc)}"}, status=500)


class SearchConsoleView(SEOAdminRequiredMixin, View):
    """
    Google Search Console data page for SEO/Super admins.
    صفحة Search Console — تعرض بيانات GSC API مباشرة في الداشبورد.
    """
    template_name = 'dashboard/search_console.html'

    def get(self, request):
        """Display Search Console data."""
        from apps.seo.services.gsc_client import GSCClient

        days = int(request.GET.get('days', 28))
        if days not in (7, 14, 28, 90):
            days = 28

        gsc = GSCClient()
        connected = gsc.is_connected()

        context = {
            'gsc_connected': connected,
            'selected_days': days,
            'summary': {},
            'bracketted_pages': {},
            'top_queries': [],
            'gsc_data_stale': False,
        }

        if connected:
            try:
                summary_data = gsc.get_summary(days)
                bracketted_data = gsc.get_bracketted_pages(days)
                top_queries_data = gsc.get_top_queries(days, limit=10)

                # Fetch 404 logs from database and group by path variations (trailing slash)
                from apps.seo.models import Page404Log
                from collections import defaultdict
                
                grouped_logs = defaultdict(lambda: {
                    "hits": 0,
                    "last_hit": None,
                    "referrers": {},
                    "user_agents": {},
                    "paths": set()
                })
                
                for log in Page404Log.objects.filter(is_ignored=False):
                    path_key = log.path.rstrip('/')
                    if not path_key:
                        path_key = '/'
                    
                    data = grouped_logs[path_key]
                    data["hits"] += log.hits
                    if not data["last_hit"] or log.last_hit > data["last_hit"]:
                        data["last_hit"] = log.last_hit
                        
                    for ref, count in (log.referrers or {}).items():
                        data["referrers"][ref] = data["referrers"].get(ref, 0) + count
                    for ua, count in (log.user_agents or {}).items():
                        data["user_agents"][ua] = data["user_agents"].get(ua, 0) + count
                    
                    data["paths"].add(log.path)
                
                # Sort groups by hits descending, then by last_hit descending
                sorted_groups = sorted(
                    grouped_logs.items(),
                    key=lambda x: (x[1]["hits"], x[1]["last_hit"]),
                    reverse=True
                )
                
                broken_pages = []
                for path_key, data in sorted_groups[:15]:
                    # Display the variation with the trailing slash if it exists
                    display_path = sorted(list(data["paths"]), key=len, reverse=True)[0]
                    
                    sorted_refs = sorted(data["referrers"].items(), key=lambda x: x[1], reverse=True)
                    top_refs = [ref for ref, count in sorted_refs[:3]]
                    top_refs_str = ", ".join(top_refs) if top_refs else "direct"
                    
                    broken_pages.append({
                        "url": display_path,
                        "path": display_path,
                        "title": display_path,
                        "type": "broken",
                        "type_label": "خطأ 404",
                        "clicks": data["hits"],
                        "impressions": top_refs_str,
                        "ctr": data["last_hit"].strftime("%Y-%m-%d") if data["last_hit"] else "",
                        "position": data["hits"],
                        "sau_position": None,
                        "egy_position": None,
                        "top_query": None,
                    })
                bracketted_data["broken"] = broken_pages

                context['summary'] = summary_data
                context['bracketted_pages'] = bracketted_data
                context['top_queries'] = top_queries_data.get('queries', [])

                if (summary_data.get('is_stale') or 
                        bracketted_data.get('is_stale') or 
                        top_queries_data.get('is_stale')):
                    context['gsc_data_stale'] = True
            except Exception as exc:
                logger.warning("SearchConsoleView: %s", exc)
                context['gsc_error'] = str(exc)

        return render(request, self.template_name, context)


class SearchConsoleCannibalizationApi(SEOAdminRequiredMixin, View):
    """
    AJAX API endpoint for loading keyword cannibalization details asynchronously.
    """
    def get(self, request):
        from apps.seo.services.gsc_client import GSCClient
        days = int(request.GET.get('days', 28))
        if days not in (7, 14, 28, 90):
            days = 28

        gsc = GSCClient()
        if not gsc.is_connected():
            return JsonResponse({'error': 'GSC not connected'}, status=400)

        try:
            data = gsc.get_cannibalized_keywords(days)
            return JsonResponse(data)
        except Exception as exc:
            logger.warning("SearchConsoleCannibalizationApi error: %s", exc)
            return JsonResponse({'error': str(exc), 'keywords': [], 'is_stale': True}, status=200)


class SearchConsoleRedirectCreateApi(SEOAdminRequiredMixin, View):
    """
    AJAX API endpoint for creating redirects and removing corresponding 404 logs.
    """
    def post(self, request):
        import json
        from apps.redirects.models import Redirect
        from apps.seo.models import Page404Log

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'success': False, 'error': 'بيانات غير صالحة.'}, status=400)

        old_url = data.get('old_url', '').strip()
        new_url = data.get('new_url', '').strip()

        if not old_url or not new_url:
            return JsonResponse({'success': False, 'error': 'الرابط القديم والجديد مطلوبان.'}, status=400)

        old_url_norm = Redirect.normalize_path(old_url)
        if new_url.startswith(('http://', 'https://')):
            new_url_norm = new_url.strip()
        else:
            new_url_norm = Redirect.normalize_path(new_url)

        if old_url_norm == new_url_norm:
            return JsonResponse({'success': False, 'error': 'الرابط القديم والجديد يجب أن يكونا مختلفين.'}, status=400)

        try:
            redirect_obj, created = Redirect.objects.update_or_create(
                old_url=old_url_norm,
                defaults={
                    'new_url': new_url_norm,
                    'is_active': True,
                    'notes': 'تم الإنشاء تلقائياً من لوحة تحكم Search Console لحل خطأ 404.'
                }
            )

            # Clean up the 404 log for this URL (all variations of slash/no-slash)
            variations = [old_url_norm, old_url_norm.rstrip('/'), old_url_norm.rstrip('/') + '/']
            Page404Log.objects.filter(path__in=variations).delete()

            return JsonResponse({'success': True})
        except Exception as exc:
            logger.warning("SearchConsoleRedirectCreateApi: %s", exc)
            return JsonResponse({'success': False, 'error': str(exc)}, status=500)


class SearchConsole404IgnoreApi(SEOAdminRequiredMixin, View):
    """
    AJAX API endpoint for marking 404 page logs as ignored.
    """
    def post(self, request):
        import json
        from apps.seo.models import Page404Log
        from apps.redirects.models import Redirect

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'success': False, 'error': 'بيانات غير صالحة.'}, status=400)

        path = data.get('path', '').strip()
        if not path:
            return JsonResponse({'success': False, 'error': 'المسار مطلوب.'}, status=400)

        try:
            # Normalize path and handle slash variations
            normalized_path = Redirect.normalize_path(path)
            variations = [normalized_path, normalized_path.rstrip('/'), normalized_path.rstrip('/') + '/']
            
            # Mark all variations as ignored
            for var in variations:
                Page404Log.objects.update_or_create(
                    path=var,
                    defaults={'is_ignored': True}
                )
            
            return JsonResponse({'success': True})
        except Exception as exc:
            logger.warning("SearchConsole404IgnoreApi: %s", exc)
            return JsonResponse({'success': False, 'error': str(exc)}, status=500)


class UserListView(SuperAdminRequiredMixin, DashboardBreadcrumbMixin, ListView):
    """
    List all users with their roles.
    عرض قائمة بجميع المستخدمين مع أدوارهم
    """
    model = User
    template_name = 'dashboard/users/list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_breadcrumbs(self):
        """Build breadcrumb trail for user list page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('المستخدمون')
            .build())

    def get_queryset(self):
        """Get all staff users filtered by search query and role, ordered by username."""
        queryset = User.objects.filter(is_staff=True).select_related('profile').order_by('username')
        
        # Search query filtering
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
            
        # Role filtering
        role_filter = self.request.GET.get('role', '').strip()
        if role_filter:
            queryset = queryset.filter(profile__role=role_filter)
            
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title and forms to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إدارة المستخدمين'
        context['page_description'] = 'إدارة جميع مستخدمي النظام وأدوارهم الصلاحيات الخاصة بهم'
        context['search_placeholder'] = 'ابحث عن اسم مستخدم أو بريد إلكتروني...'
        context['search_value'] = self.request.GET.get('search', '')
        context['base_url'] = reverse_lazy('dashboard:user_list')
        
        # Action button for topbar (with javascript function call to open modal)
        context['action_buttons'] = [
            {
                'url': 'javascript:openCreateModal()',
                'label': 'إضافة مستخدم جديد',
                'variant': 'primary',
            }
        ]
        
        # Filters definition for unified filter bar
        context['filters'] = [
            {
                'name': 'role',
                'label': 'الدور',
                'selected': self.request.GET.get('role', ''),
                'options': [
                    {'value': 'super_admin', 'label': 'مسؤول عام'},
                    {'value': 'content_admin', 'label': 'مسؤول محتوى'},
                    {'value': 'seo_admin', 'label': 'مسؤول SEO'},
                ]
            }
        ]
        
        context['empty_state_icon'] = '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>'
        
        # Add items for list_page.html template
        context['items'] = context.get('users', context.get('object_list', []))
        
        # Query params for pagination
        context['query_params'] = '&'.join([f'{k}={v}' for k, v in self.request.GET.items() if k != 'page'])
        
        # Instantiate empty forms for use in the modals (using prefixes to prevent ID conflicts)
        context['create_form'] = UserCreateForm(prefix='create')
        context['update_form'] = UserUpdateForm(prefix='edit')
        return context


class UserCreateView(SuperAdminRequiredMixin, CreateView):
    """
    Create a new user with profile and role.
    إنشاء مستخدم جديد مع الملف الشخصي والدور
    """
    model = User
    form_class = UserCreateForm
    template_name = 'dashboard/users/create.html'
    success_url = reverse_lazy('dashboard:user_list')

    def get_form_kwargs(self):
        """Pass the 'create' prefix to the form."""
        kwargs = super().get_form_kwargs()
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('json') == '1':
            kwargs['prefix'] = 'create'
        return kwargs

    def get(self, request, *args, **kwargs):
        """Redirect GET requests to list page since creation is done via modal."""
        return redirect(self.success_url)

    def form_valid(self, form):
        """Handle successful form submission."""
        self.object = form.save()
        success_message = f'تم إنشاء المستخدم {self.object.username} بنجاح'
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('json') == '1':
            messages.success(self.request, success_message)
            return JsonResponse({
                'status': 'success',
                'message': success_message,
                'user': {
                    'id': self.object.id,
                    'username': self.object.username,
                    'email': self.object.email,
                }
            })
            
        messages.success(self.request, success_message)
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('json') == '1':
            # Extract first error for each field
            errors = {field: errs[0] for field, errs in form.errors.items()}
            return JsonResponse({
                'status': 'error',
                'errors': errors
            }, status=400)
            
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return redirect(self.success_url)


class UserUpdateView(SuperAdminRequiredMixin, UpdateView):
    """
    Update an existing user and their role.
    تحديث مستخدم موجود ودوره
    """
    model = User
    form_class = UserUpdateForm
    template_name = 'dashboard/users/edit.html'
    success_url = reverse_lazy('dashboard:user_list')

    def get_form_kwargs(self):
        """Pass the 'edit' prefix to the form."""
        kwargs = super().get_form_kwargs()
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('json') == '1':
            kwargs['prefix'] = 'edit'
        return kwargs

    def get_queryset(self):
        """Get only staff users."""
        return User.objects.filter(is_staff=True).select_related('profile')

    def get(self, request, *args, **kwargs):
        """Return JSON for AJAX modal populating, redirect to list page otherwise."""
        self.object = self.get_object()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('json') == '1':
            return JsonResponse({
                'status': 'success',
                'username': self.object.username,
                'email': self.object.email,
                'first_name': self.object.first_name,
                'last_name': self.object.last_name,
                'role': self.object.profile.role if hasattr(self.object, 'profile') else '',
                'receive_registration_emails': self.object.profile.receive_registration_emails if hasattr(self.object, 'profile') else True,
                'receive_inquiry_emails': self.object.profile.receive_inquiry_emails if hasattr(self.object, 'profile') else True,
            })
        return redirect(self.success_url)

    def form_valid(self, form):
        """Handle successful form submission."""
        self.object = form.save()
        success_message = f'تم تحديث بيانات المستخدم {self.object.username} بنجاح'
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('json') == '1':
            messages.success(self.request, success_message)
            return JsonResponse({
                'status': 'success',
                'message': success_message,
                'user': {
                    'id': self.object.id,
                    'username': self.object.username,
                    'email': self.object.email,
                }
            })
            
        messages.success(self.request, success_message)
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('json') == '1':
            errors = {field: errs[0] for field, errs in form.errors.items()}
            return JsonResponse({
                'status': 'error',
                'errors': errors
            }, status=400)
            
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return redirect(self.success_url)


class UserDeleteView(SuperAdminRequiredMixin, DeleteView):
    """
    Delete a user with confirmation.
    حذف مستخدم مع تأكيد
    """
    model = User
    template_name = 'dashboard/users/delete_confirm.html'
    success_url = reverse_lazy('dashboard:user_list')

    def get_queryset(self):
        """Get only staff users."""
        return User.objects.filter(is_staff=True).select_related('profile')

    def get(self, request, *args, **kwargs):
        """Return JSON for AJAX delete modal, redirect to list page otherwise."""
        self.object = self.get_object()
        if self.object == request.user:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('json') == '1':
                return JsonResponse({
                    'status': 'error',
                    'message': 'لا يمكنك حذف حسابك الشخصي الذي تستخدمه حالياً.'
                }, status=400)
            messages.error(request, 'لا يمكنك حذف حسابك الشخصي الذي تستخدمه حالياً.')
            return redirect(self.success_url)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('json') == '1':
            return JsonResponse({
                'status': 'success',
                'username': self.object.username,
                'email': self.object.email,
                'first_name': self.object.first_name,
                'last_name': self.object.last_name,
                'role': self.object.profile.get_role_display() if hasattr(self.object, 'profile') else '',
            })
        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        """Handle deletion with success message or AJAX response."""
        self.object = self.get_object()
        if self.object == request.user:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('json') == '1':
                return JsonResponse({
                    'status': 'error',
                    'message': 'لا يمكنك حذف حسابك الشخصي الذي تستخدمه حالياً.'
                }, status=400)
            messages.error(request, 'لا يمكنك حذف حسابك الشخصي الذي تستخدمه حالياً.')
            return redirect(self.success_url)

        username = self.object.username
        self.object.delete()
        success_message = f'تم حذف المستخدم {username} بنجاح'
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('json') == '1':
            messages.success(request, success_message)
            return JsonResponse({
                'status': 'success',
                'message': success_message
            })
            
        messages.success(request, success_message)
        return redirect(self.success_url)


class RedirectListView(ContentOrSEOAdminRequiredMixin, DashboardBreadcrumbMixin, ListView):
    """
    List all redirects with search and filtering.
    عرض قائمة بجميع إعادات التوجيه مع البحث والتصفية
    
    Features:
    - Search by old_url and new_url
    - Filter by is_active status
    - Display hit_count for each redirect
    - Pagination (20 per page)
    - Show is_active status with toggle option
    """
    model = Redirect
    template_name = 'dashboard/redirects/list.html'
    context_object_name = 'redirects'
    paginate_by = 20

    def get_breadcrumbs(self):
        """Build breadcrumb trail for redirect list page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('إعادات التوجيه')
            .build())

    def get_queryset(self):
        """Get redirects with optional search and filtering."""
        queryset = Redirect.objects.all().order_by('-created_at')
        
        # Search by old_url or new_url (support both quoted and unquoted versions of Arabic strings)
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            import urllib.parse
            quoted_query = urllib.parse.quote(search_query)
            queryset = queryset.filter(
                Q(old_url__icontains=search_query) |
                Q(new_url__icontains=search_query) |
                Q(old_url__icontains=quoted_query) |
                Q(new_url__icontains=quoted_query)
            )
        
        # Filter by is_active status
        status_filter = self.request.GET.get('status', '').strip()
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title and search/filter info to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إدارة إعادات التوجيه'
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        
        # Define table columns for list_page.html template using decoded URLs
        context['columns'] = [
            {
                'label': 'الرابط القديم (المكسور)',
                'key': 'old_url_decoded',
                'type': 'text',
                'direction': 'ltr',
            },
            {
                'label': 'الرابط الجديد (التحويل)',
                'key': 'new_url_decoded',
                'type': 'text',
                'direction': 'ltr',
            },
            {
                'label': 'الحالة',
                'key': 'is_active_label',
                'type': 'badge',
                'badge_status_key': 'is_active_label',
            },
            {
                'label': 'عدد الزيارات',
                'key': 'hit_count',
                'type': 'text',
            },
            {
                'label': 'تاريخ الإنشاء',
                'key': 'created_at',
                'type': 'date',
            }
        ]
        context['edit_url_name'] = 'dashboard:redirect_edit'
        context['delete_url_name'] = 'dashboard:redirect_delete'
        
        # Add items for list_page.html template
        context['items'] = context.get('redirects', context.get('object_list', []))
        return context


class RedirectCreateView(ContentOrSEOAdminRequiredMixin, CreateView):
    """
    Create a new redirect.
    إنشاء إعادة توجيه جديدة
    
    Features:
    - URL validation (must start with /)
    - Prevent duplicate old_url entries
    - Validate old_url != new_url
    - Arabic success message
    """
    model = Redirect
    form_class = RedirectForm
    template_name = 'dashboard/redirects/create.html'
    success_url = reverse_lazy('dashboard:redirect_list')

    def form_valid(self, form):
        """Handle successful form submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'تم إنشاء إعادة التوجيه من {self.object.old_url} إلى {self.object.new_url} بنجاح'
        )
        return response

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إنشاء إعادة توجيه جديدة'
        return context


class RedirectUpdateView(ContentOrSEOAdminRequiredMixin, UpdateView):
    """
    Update an existing redirect.
    تحديث إعادة توجيه موجودة
    
    Features:
    - Edit old_url, new_url, is_active, notes
    - URL validation
    - Arabic success message
    """
    model = Redirect
    form_class = RedirectForm
    template_name = 'dashboard/redirects/edit.html'
    success_url = reverse_lazy('dashboard:redirect_list')

    def form_valid(self, form):
        """Handle successful form submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'تم تحديث إعادة التوجيه بنجاح'
        )
        return response

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'تحديث إعادة التوجيه: {self.object.old_url}'
        return context


class RedirectDeleteView(ContentOrSEOAdminRequiredMixin, DeleteView):
    """
    Delete a redirect with confirmation.
    حذف إعادة توجيه مع تأكيد
    
    Features:
    - Confirmation page
    - Arabic success message
    """
    model = Redirect
    template_name = 'dashboard/redirects/delete_confirm.html'
    success_url = reverse_lazy('dashboard:redirect_list')

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        redirect_obj = self.get_object()
        old_url = redirect_obj.old_url
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'تم حذف إعادة التوجيه {old_url} بنجاح'
        )
        return response

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'حذف إعادة التوجيه: {self.object.old_url}'
        return context


# ============================================================================
# University Management Views
# ============================================================================

class UniversityListView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, ListView):
    """
    List all universities with search and status filters.
    عرض قائمة بجميع الجامعات مع البحث والتصفية حسب الحالة
    
    Features:
    - Search by name and slug
    - Filter by publish_status (published/unpublished)
    - Display faculty count for each university
    - Pagination (20 per page)
    - Show publish status with visual indicator
    
    Query Optimization:
    - Uses prefetch_related for faculties to avoid N+1 queries
    - Uses prefetch_related for related_majors and related_articles
    """
    model = University
    template_name = 'dashboard/universities/list.html'
    context_object_name = 'universities'
    paginate_by = 20

    def get_breadcrumbs(self):
        """Build breadcrumb trail for university list page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('الجامعات')
            .build())

    def get_queryset(self):
        """Get universities with optional search and filtering."""
        from django.db.models import Prefetch
        
        # Prefetch faculties with their programs
        faculties_prefetch = Prefetch(
            'faculties',
            Faculty.objects.prefetch_related(
                Prefetch(
                    'programs',
                    Program.objects.all().order_by('sort_order')
                )
            ).order_by('sort_order')
        )
        
        queryset = University.objects.all().prefetch_related(
            faculties_prefetch,
            'related_majors',
            'related_articles'
        ).order_by('order', 'name')
        
        # Search by name, slug, state, or city
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(slug__icontains=search_query) |
                Q(state__icontains=search_query) |
                Q(city__icontains=search_query)
            )
        
        # Filter by publish_status
        status_filter = self.request.GET.get('status', '').strip()
        if status_filter == 'published':
            queryset = queryset.filter(publish_status='published')
        elif status_filter == 'unpublished':
            queryset = queryset.filter(publish_status='unpublished')
        
        # Filter by university_type
        type_filter = self.request.GET.get('type', '').strip()
        if type_filter in ['public', 'private']:
            queryset = queryset.filter(university_type=type_filter)
        
        # Filter by state
        state_filter = self.request.GET.get('state', '').strip().lower()
        if state_filter:
            queryset = queryset.filter(state=state_filter)
            
        # Filter by city
        city_filter = self.request.GET.get('city', '').strip().lower()
        if city_filter:
            queryset = queryset.filter(city=city_filter)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title and search/filter info to context."""
        from django.urls import reverse
        
        context = super().get_context_data(**kwargs)
        
        # Clean expired and get active locks for universities
        try:
            ContentLock.objects.filter(expires_at__lt=timezone.now()).delete()
        except Exception:
            pass
        ct = ContentType.objects.get_for_model(University)
        active_locks = ContentLock.objects.filter(content_type=ct).select_related('user')
        context['locked_objects'] = {
            lock.object_id: lock.user.get_full_name() or lock.user.username 
            for lock in active_locks
        }

        context['page_title'] = 'إدارة الجامعات'
        context['page_type'] = 'universities'
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['type_filter'] = self.request.GET.get('type', '')
        context['state_filter'] = self.request.GET.get('state', '')
        context['city_filter'] = self.request.GET.get('city', '')
        
        # Add items for list_page.html template
        # context_object_name is 'universities', but list_page.html expects 'items'
        context['items'] = context.get('universities', context.get('object_list', []))
        
        # Add required context variables for list_page.html
        context['search_placeholder'] = 'ابحث عن اسم الجامعة...'
        context['search_value'] = context['search_query']
        context['base_url'] = reverse('dashboard:university_list')
        context['bulk_action_url'] = reverse('dashboard:university_bulk_action')
        
        # Get only the states and cities that are actually assigned
        used_states = University.objects.values_list('state', flat=True).order_by().distinct()
        state_choices_dict = dict(University.STATE_CHOICES)
        used_state_options = []
        for code in used_states:
            if code and code in state_choices_dict:
                used_state_options.append({'value': code, 'label': state_choices_dict[code]})
        used_state_options.sort(key=lambda x: x['label'])

        used_cities = University.objects.values_list('city', flat=True).order_by().distinct()
        city_choices_dict = {}
        for state_code, cities in University.STATE_CITIES.items():
            for c_slug, c_name in cities:
                city_choices_dict[c_slug] = c_name
        
        used_city_options = []
        for code in used_cities:
            if code and code in city_choices_dict:
                used_city_options.append({'value': code, 'label': city_choices_dict[code]})
        used_city_options.sort(key=lambda x: x['label'])

        # Filters
        context['filters'] = [
            {
                'name': 'status',
                'label': 'حالة النشر',
                'options': [
                    {'value': 'published', 'label': 'منشور'},
                    {'value': 'unpublished', 'label': 'غير منشور'},
                ],
                'selected': context['status_filter'],
            },
            {
                'name': 'type',
                'label': 'نوع الجامعة',
                'options': [
                    {'value': 'public', 'label': 'حكومية'},
                    {'value': 'private', 'label': 'خاصة'},
                ],
                'selected': context['type_filter'],
            },
            {
                'name': 'state',
                'label': 'الولاية',
                'options': used_state_options,
                'selected': context['state_filter'],
            },
            {
                'name': 'city',
                'label': 'المدينة',
                'options': used_city_options,
                'selected': context['city_filter'],
            },
        ]
        
        # Columns for data table
        context['columns'] = [
            {'label': 'الترتيب', 'key': 'order', 'type': 'text'},
            {'label': 'اسم الجامعة', 'key': 'name', 'type': 'link', 'link_url_name': 'dashboard:university_edit', 'link_param': 'pk'},
            {'label': 'المدينة', 'key': 'city_display', 'type': 'text'},
            {'label': 'النوع', 'key': 'university_type_display', 'type': 'text'},
            {'label': 'الكليات', 'key': 'faculties_count', 'type': 'text'},
            {'label': 'الحالة', 'key': 'publish_status', 'type': 'status_badge'},
            {'label': 'تاريخ النشر', 'key': 'created_at', 'type': 'date'},
            {'label': 'تاريخ التحديث', 'key': 'updated_at', 'type': 'date'},
        ]
        
        context['edit_url_name'] = 'dashboard:university_edit'
        context['delete_url_name'] = 'dashboard:university_delete'
        
        # Pagination info
        paginator = context.get('paginator')
        context['is_paginated'] = paginator.num_pages > 1 if paginator else False
        context['page_obj'] = context.get('page_obj')
        
        # Build query params for pagination
        query_params = '&'.join([f'{k}={v}' for k, v in self.request.GET.items() if k != 'page'])
        context['query_params'] = query_params
        
        # Add computed properties to each university
        for university in context['items']:
            university.faculties_count = university.faculties.count()
            university.university_type_display = university.get_university_type_display()
            university.publish_status_display = university.get_publish_status_display()
            university.city_display = university.get_location_display()
        
        return context


class UniversityCreateView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, CreateView):
    """
    Create a new university with inline FAQ formset.
    إنشاء جامعة جديدة مع نموذج الأسئلة الشائعة المدمج
    
    Features:
    - Create university with all fields
    - Add FAQ entries inline
    - Arabic success message
    - Redirect to edit page after creation
    """
    model = University
    form_class = UniversityForm
    template_name = 'dashboard/universities/form.html'

    def get_breadcrumbs(self):
        """Build breadcrumb trail for university create page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_universities')
            .current('إضافة جامعة')
            .build())

    def get_context_data(self, **kwargs):
        """Add formsets to context with nested program formsets."""
        context = super().get_context_data(**kwargs)
        import json
        context['state_cities_json'] = json.dumps(University.STATE_CITIES)
        
        if self.request.POST:
            context['faq_formset'] = UniversityFAQFormSet(self.request.POST, instance=self.object)
            context['faculty_formset'] = UniversityFacultyFormSet(self.request.POST, instance=self.object)
            context['attachment_formset'] = UniversityAttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['faq_formset'] = UniversityFAQFormSet(instance=self.object)
            context['faculty_formset'] = UniversityFacultyFormSet(instance=self.object)
            context['attachment_formset'] = UniversityAttachmentFormSet(instance=self.object)
        
        # Attach nested program formsets to each faculty form
        context['faculty_formset'] = self._attach_program_formsets(
            context['faculty_formset'],
            self.request.POST if self.request.POST else None
        )
        
        # Add recently used relations to context
        recent_uni_ids = University.objects.order_by('-updated_at').values_list('id', flat=True)[:10]
        context['recently_used_majors'] = list(Major.objects.filter(universities__in=recent_uni_ids).distinct()[:5])
        context['recently_used_articles'] = list(Article.objects.filter(universities__in=recent_uni_ids).distinct()[:5])
        context['recently_used_tags'] = list(Tag.objects.filter(universities__in=recent_uni_ids).distinct()[:5])
        
        context['page_title'] = 'إنشاء جامعة جديدة'
        return context

    def _attach_program_formsets(self, faculty_formset, post_data=None):
        """Attach nested program formsets to each faculty form."""
        from apps.dashboard.forms.university import NestedProgramFormSet
        
        for i, faculty_form in enumerate(faculty_formset):
            if faculty_form.instance.pk:
                # Existing faculty — load programs from DB
                if post_data:
                    faculty_form.program_formset = NestedProgramFormSet(
                        post_data,
                        instance=faculty_form.instance,
                        prefix=f'faculty-{i}-programs'
                    )
                else:
                    faculty_form.program_formset = NestedProgramFormSet(
                        instance=faculty_form.instance,
                        prefix=f'faculty-{i}-programs'
                    )
            else:
                # New faculty — empty formset
                if post_data:
                    faculty_form.program_formset = NestedProgramFormSet(
                        post_data,
                        prefix=f'faculty-{i}-programs'
                    )
                else:
                    faculty_form.program_formset = NestedProgramFormSet(
                        prefix=f'faculty-{i}-programs'
                    )
        
        return faculty_formset

    def form_valid(self, form):
        """Handle successful form submission with nested formsets.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        context = self.get_context_data()
        faq_formset = context['faq_formset']
        faculty_formset = context['faculty_formset']
        attachment_formset = context['attachment_formset']
        
        import logging
        logger = logging.getLogger(__name__)
        
        # التحقق من صحة كل الـ formsets قبل أي حفظ
        all_valid = faq_formset.is_valid() and faculty_formset.is_valid() and attachment_formset.is_valid()
        
        # Check nested program formsets
        if all_valid:
            for faculty_form in faculty_formset:
                if hasattr(faculty_form, 'program_formset'):
                    if not faculty_form.program_formset.is_valid():
                        all_valid = False
                        logger.debug(f"Program formset errors: {faculty_form.program_formset.errors}")
                        break
        
        if all_valid:
            try:
                with transaction.atomic():
                    # حفظ الجامعة
                    self.object = form.save()
                    
                    # حفظ الأسئلة الشائعة
                    faq_formset.instance = self.object
                    faq_formset.save()
                    
                    # حفظ الكليات والبرامج
                    faculty_formset.instance = self.object
                    faculty_formset.save()
                    
                    for faculty_form in faculty_formset:
                        if hasattr(faculty_form, 'program_formset'):
                            faculty_form.program_formset.instance = faculty_form.instance
                            faculty_form.program_formset.save()
                    
                    # حفظ المرفقات
                    attachment_formset.instance = self.object
                    attachment_formset.save()
                
                messages.success(
                    self.request,
                    f'تم إنشاء الجامعة "{self.object.name}" بنجاح'
                )
                return redirect('dashboard:university_edit', pk=self.object.pk)
            except Exception as e:
                logger.error(f"Error saving university: {e}")
                messages.error(self.request, 'حدث خطأ أثناء حفظ الجامعة. لم يتم حفظ أي بيانات.')
                return self.form_invalid(form)
        else:
            # عرض الأخطاء بدون حفظ أي شيء
            logger.debug(f"FAQ Formset errors: {faq_formset.errors}")
            logger.debug(f"Faculty Formset errors: {faculty_formset.errors}")
            logger.debug(f"Attachment Formset errors: {attachment_formset.errors}")
            
            for error in faq_formset.non_form_errors():
                messages.error(self.request, f'خطأ في الأسئلة الشائعة: {error}')
            for error_dict in faq_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في الأسئلة الشائعة: {error}')
            
            for error in faculty_formset.non_form_errors():
                messages.error(self.request, f'خطأ في الكليات: {error}')
            for error_dict in faculty_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في الكليات: {error}')
            
            for faculty_form in faculty_formset:
                if hasattr(faculty_form, 'program_formset'):
                    for error in faculty_form.program_formset.non_form_errors():
                        messages.error(self.request, f'خطأ في البرامج: {error}')
                    for error_dict in faculty_form.program_formset.errors:
                        for field, errors in error_dict.items():
                            for error in errors:
                                messages.error(self.request, f'خطأ في البرامج: {error}')
            
            for error in attachment_formset.non_form_errors():
                messages.error(self.request, f'خطأ في مرفقات الجامعة: {error}')
            for error_dict in attachment_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في مرفقات الجامعة: {error}')
            
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Form errors: {form.errors}")
        if self._is_ajax():
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)


class LockValidationMixin:
    """
    Mixin to check if content is locked by another user before allowing edit POST requests.
    If locked, re-renders the form with submitted data so inputs are not lost.
    """
    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        ct = ContentType.objects.get_for_model(obj)
        
        # Clean expired
        try:
            ContentLock.objects.filter(expires_at__lt=timezone.now()).delete()
        except Exception:
            pass
        
        lock = ContentLock.objects.filter(content_type=ct, object_id=obj.id).first()
        if lock and lock.user != request.user:
            user_name = lock.user.get_full_name() or lock.user.username
            messages.error(
                request, 
                f'لا يمكن حفظ التغييرات: تم الاستحواذ على قفل تعديل هذا العنصر بواسطة "{user_name}". يرجى نسخ تعديلاتك يدوياً لتجنب فقدانها.'
            )
            self.object = obj
            form = self.get_form()
            return self.form_invalid(form)
            
        return super().post(request, *args, **kwargs)


class UniversityUpdateView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, LockValidationMixin, UpdateView):
    """
    Update an existing university with inline FAQ formset and faculty list display.
    تحديث جامعة موجودة مع نموذج الأسئلة الشائعة المدمج وعرض قائمة الكليات
    
    Features:
    - Edit all university fields
    - Edit FAQ entries inline
    - Display list of faculties with edit/delete options
    - Show slug change warning if slug was modified
    - Offer to create redirect for old slug
    - Arabic success message
    """
    model = University
    form_class = UniversityForm
    template_name = 'dashboard/universities/form.html'
    success_url = reverse_lazy('dashboard:university_list')

    def get_success_url(self):
        return reverse('dashboard:university_edit', kwargs={'pk': self.object.pk})

    def _is_ajax(self):
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def get_breadcrumbs(self):
        """Build breadcrumb trail for university update page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_universities')
            .current('تعديل الجامعة')
            .build())

    def get_context_data(self, **kwargs):
        """Add formsets and faculties to context with nested programs."""
        context = super().get_context_data(**kwargs)
        import json
        context['state_cities_json'] = json.dumps(University.STATE_CITIES)
        
        if self.request.POST:
            context['faq_formset'] = UniversityFAQFormSet(self.request.POST, instance=self.object)
            context['faculty_formset'] = UniversityFacultyFormSet(self.request.POST, instance=self.object)
            context['attachment_formset'] = UniversityAttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['faq_formset'] = UniversityFAQFormSet(instance=self.object)
            context['faculty_formset'] = UniversityFacultyFormSet(instance=self.object)
            context['attachment_formset'] = UniversityAttachmentFormSet(instance=self.object)
        
        # Attach nested program formsets to each faculty form
        context['faculty_formset'] = self._attach_program_formsets(
            context['faculty_formset'],
            self.request.POST if self.request.POST else None
        )
        
        context['page_title'] = f'تحديث الجامعة: {self.object.name}'
        
        # Check if slug was changed and show warning
        if hasattr(self.object, '_old_slug'):
            context['slug_changed'] = True
            context['old_slug'] = self.object._old_slug
            
        # Add recently used relations to context
        recent_uni_ids = University.objects.order_by('-updated_at').values_list('id', flat=True)[:10]
        context['recently_used_majors'] = list(Major.objects.filter(universities__in=recent_uni_ids).distinct()[:5])
        context['recently_used_articles'] = list(Article.objects.filter(universities__in=recent_uni_ids).distinct()[:5])
        context['recently_used_tags'] = list(Tag.objects.filter(universities__in=recent_uni_ids).distinct()[:5])
        
        return context

    def _attach_program_formsets(self, faculty_formset, post_data=None):
        """Attach nested program formsets to each faculty form."""
        from apps.dashboard.forms.university import NestedProgramFormSet
        
        for i, faculty_form in enumerate(faculty_formset):
            if faculty_form.instance.pk:
                # Existing faculty — load programs from DB
                if post_data:
                    faculty_form.program_formset = NestedProgramFormSet(
                        post_data,
                        instance=faculty_form.instance,
                        prefix=f'faculty-{i}-programs'
                    )
                else:
                    faculty_form.program_formset = NestedProgramFormSet(
                        instance=faculty_form.instance,
                        prefix=f'faculty-{i}-programs'
                    )
            else:
                # New faculty — empty formset
                if post_data:
                    faculty_form.program_formset = NestedProgramFormSet(
                        post_data,
                        prefix=f'faculty-{i}-programs'
                    )
                else:
                    faculty_form.program_formset = NestedProgramFormSet(
                        prefix=f'faculty-{i}-programs'
                    )
        
        return faculty_formset

    def form_valid(self, form):
        """Handle successful form submission with nested formsets.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        context = self.get_context_data()
        faq_formset = context['faq_formset']
        faculty_formset = context['faculty_formset']
        attachment_formset = context['attachment_formset']
        
        import logging
        logger = logging.getLogger(__name__)
        
        # التحقق من صحة كل الـ formsets قبل أي حفظ
        all_valid = faq_formset.is_valid() and faculty_formset.is_valid() and attachment_formset.is_valid()
        
        # Check nested program formsets
        if all_valid:
            for faculty_form in faculty_formset:
                if hasattr(faculty_form, 'program_formset'):
                    if not faculty_form.program_formset.is_valid():
                        all_valid = False
                        logger.debug(f"Program formset errors: {faculty_form.program_formset.errors}")
                        break
        
        if all_valid:
            try:
                with transaction.atomic():
                    # Capture pre-save version snapshot of DB state before applying updates
                    from apps.core.services.versioning import VersioningService
                    VersioningService.capture_pre_save_snapshot(
                        self.object,
                        user=self.request.user,
                        change_reason='تحديث الجامعة'
                    )

                    # حفظ الـ slug القديم قبل الحفظ
                    old_slug = self.object.slug
                    
                    # حفظ الجامعة
                    self.object = form.save()
                    
                    # حفظ الأسئلة الشائعة
                    faq_formset.instance = self.object
                    faq_formset.save()
                    
                    # حفظ الكليات والبرامج
                    faculty_formset.instance = self.object
                    faculty_formset.save()
                    
                    for faculty_form in faculty_formset:
                        if hasattr(faculty_form, 'program_formset'):
                            faculty_form.program_formset.instance = faculty_form.instance
                            faculty_form.program_formset.save()
                    
                    # حفظ المرفقات
                    attachment_formset.instance = self.object
                    attachment_formset.save()
                    
                    if not self._is_ajax():
                        messages.success(
                            self.request,
                            f'تم تحديث الجامعة "{self.object.name}" بنجاح'
                        )
                
                if self._is_ajax():
                    return JsonResponse({"status": "success", "message": "تم حفظ المسودة بنجاح."})
                return redirect(self.get_success_url())
            except Exception as e:
                logger.error(f"Error updating university: {e}")
                messages.error(self.request, 'حدث خطأ أثناء تحديث الجامعة. لم يتم حفظ أي تغييرات.')
                return self.form_invalid(form)
        else:
            # عرض الأخطاء بدون حفظ أي شيء
            logger.debug(f"FAQ Formset errors: {faq_formset.errors}")
            logger.debug(f"Faculty Formset errors: {faculty_formset.errors}")
            logger.debug(f"Attachment Formset errors: {attachment_formset.errors}")
            
            for error in faq_formset.non_form_errors():
                messages.error(self.request, f'خطأ في الأسئلة الشائعة: {error}')
            for error_dict in faq_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في الأسئلة الشائعة: {error}')
            
            for error in faculty_formset.non_form_errors():
                messages.error(self.request, f'خطأ في الكليات: {error}')
            for error_dict in faculty_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في الكليات: {error}')
            
            for faculty_form in faculty_formset:
                if hasattr(faculty_form, 'program_formset'):
                    for error in faculty_form.program_formset.non_form_errors():
                        messages.error(self.request, f'خطأ في البرامج: {error}')
                    for error_dict in faculty_form.program_formset.errors:
                        for field, errors in error_dict.items():
                            for error in errors:
                                messages.error(self.request, f'خطأ في البرامج: {error}')
                                
            for error in attachment_formset.non_form_errors():
                messages.error(self.request, f'خطأ في مرفقات الجامعة: {error}')
            for error_dict in attachment_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في مرفقات الجامعة: {error}')
            
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        if self._is_ajax():
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)


class UniversityDeleteView(ContentAdminRequiredMixin, DeleteView):
    """
    Delete a university with confirmation.
    حذف جامعة مع تأكيد
    
    Features:
    - Confirmation page showing university name
    - Arabic success message
    - Cascade delete of related faculties, programs, and FAQs
    """
    model = University
    template_name = 'dashboard/universities/delete_confirm.html'
    success_url = reverse_lazy('dashboard:university_list')

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        university = self.get_object()
        university_name = university.name
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'تم حذف الجامعة "{university_name}" وجميع بيانات الكليات والبرامج المرتبطة بها بنجاح'
        )
        return response

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'حذف الجامعة: {self.object.name}'
        return context


# ============================================================================
# Faculty Management Views
# ============================================================================

class FacultyListView(DashboardBreadcrumbMixin, ContentAdminRequiredMixin, ListView):
    """
    List all faculties for a specific university.
    عرض قائمة بجميع الكليات لجامعة معينة
    
    Features:
    - Display faculties for a specific university
    - Show program count for each faculty
    - Breadcrumb navigation showing university context
    - Edit and delete options for each faculty
    - Add new faculty button
    - Pagination (20 per page)
    """
    model = Faculty
    template_name = 'dashboard/faculties/list.html'
    context_object_name = 'faculties'
    paginate_by = 20

    def get_queryset(self):
        """Get faculties for the specific university."""
        university_id = self.kwargs.get('university_id')
        return Faculty.objects.filter(
            university_id=university_id
        ).prefetch_related('programs').order_by('sort_order', 'name')

    def get_breadcrumbs(self):
        """Build breadcrumb trail for faculty list page."""
        university_id = self.kwargs.get('university_id')
        university = get_object_or_404(University, pk=university_id)
        
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_universities')
            .add(university.name, reverse_lazy('dashboard:university_edit', kwargs={'pk': university.pk}))
            .current('الكليات')
            .build())

    def get_context_data(self, **kwargs):
        """Add university to context."""
        context = super().get_context_data(**kwargs)
        university_id = self.kwargs.get('university_id')
        university = get_object_or_404(University, pk=university_id)
        
        context['university'] = university
        context['page_title'] = f'إدارة الكليات: {university.name}'
        return context


class FacultyCreateView(DashboardBreadcrumbMixin, ContentAdminRequiredMixin, CreateView):
    """
    Create a new faculty with inline Program formset.
    إنشاء كلية جديدة مع نموذج البرامج المدمج
    
    Features:
    - Create faculty with name and sort order
    - Add programs inline
    - Breadcrumb navigation showing university context
    - Arabic success message
    - Redirect to faculty list after creation
    """
    model = Faculty
    form_class = FacultyForm
    template_name = 'dashboard/faculties/create.html'

    def get_breadcrumbs(self):
        """Build breadcrumb trail for faculty create page."""
        university_id = self.kwargs.get('university_id')
        university = get_object_or_404(University, pk=university_id)
        
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_universities')
            .add(university.name, reverse_lazy('dashboard:university_edit', kwargs={'pk': university.pk}))
            .add('الكليات', reverse_lazy('dashboard:faculty_list', kwargs={'university_id': university.pk}))
            .current('إنشاء جديد')
            .build())

    def get_context_data(self, **kwargs):
        """Add formset and university to context."""
        context = super().get_context_data(**kwargs)
        university_id = self.kwargs.get('university_id')
        university = get_object_or_404(University, pk=university_id)
        
        if self.request.POST:
            context['program_formset'] = ProgramFormSet(self.request.POST, instance=self.object)
        else:
            context['program_formset'] = ProgramFormSet(instance=self.object)
        
        context['university'] = university
        context['page_title'] = f'إنشاء كلية جديدة: {university.name}'
        return context

    def form_valid(self, form):
        """Handle successful form submission with formset.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        context = self.get_context_data()
        program_formset = context['program_formset']
        university_id = self.kwargs.get('university_id')
        university = get_object_or_404(University, pk=university_id)
        
        if program_formset.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save(commit=False)
                    self.object.university = university
                    self.object.save()
                    
                    program_formset.instance = self.object
                    program_formset.save()
                
                messages.success(
                    self.request,
                    f'تم إنشاء الكلية "{self.object.name}" بنجاح'
                )
                return redirect('dashboard:faculty_list', university_id=university.pk)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error saving faculty: {e}")
                messages.error(self.request, 'حدث خطأ أثناء حفظ الكلية. لم يتم حفظ أي بيانات.')
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        if self._is_ajax():
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)


class FacultyUpdateView(DashboardBreadcrumbMixin, ContentAdminRequiredMixin, UpdateView):
    """
    Update an existing faculty with inline Program formset.
    تحديث كلية موجودة مع نموذج البرامج المدمج
    
    Features:
    - Edit faculty name and sort order
    - Edit programs inline
    - Breadcrumb navigation showing university context
    - Arabic success message
    - Redirect to faculty list after update
    """
    model = Faculty
    form_class = FacultyForm
    template_name = 'dashboard/faculties/edit.html'

    def get_breadcrumbs(self):
        """Build breadcrumb trail for faculty update page."""
        university = self.object.university
        
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_universities')
            .add(university.name, reverse_lazy('dashboard:university_edit', kwargs={'pk': university.pk}))
            .add('الكليات', reverse_lazy('dashboard:faculty_list', kwargs={'university_id': university.pk}))
            .current(self.object.name)
            .build())

    def get_context_data(self, **kwargs):
        """Add formset and university to context."""
        context = super().get_context_data(**kwargs)
        university = self.object.university
        
        if self.request.POST:
            context['program_formset'] = ProgramFormSet(self.request.POST, instance=self.object)
        else:
            context['program_formset'] = ProgramFormSet(instance=self.object)
        
        context['university'] = university
        context['page_title'] = f'تحديث الكلية: {self.object.name}'
        return context

    def form_valid(self, form):
        """Handle successful form submission with formset.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        context = self.get_context_data()
        program_formset = context['program_formset']
        
        if program_formset.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save()
                    program_formset.instance = self.object
                    program_formset.save()
                
                messages.success(
                    self.request,
                    f'تم تحديث الكلية "{self.object.name}" بنجاح'
                )
                return redirect('dashboard:faculty_list', university_id=self.object.university.pk)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error updating faculty: {e}")
                messages.error(self.request, 'حدث خطأ أثناء تحديث الكلية. لم يتم حفظ أي تغييرات.')
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        if self._is_ajax():
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)


class FacultyDeleteView(DashboardBreadcrumbMixin, ContentAdminRequiredMixin, DeleteView):
    """
    Delete a faculty with confirmation.
    حذف كلية مع تأكيد
    
    Features:
    - Confirmation page showing faculty name and program count
    - Breadcrumb navigation showing university context
    - Arabic success message
    - Cascade delete of related programs
    """
    model = Faculty
    template_name = 'dashboard/faculties/delete_confirm.html'

    def get_breadcrumbs(self):
        """Build breadcrumb trail for faculty delete page."""
        university = self.object.university
        
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_universities')
            .add(university.name, reverse_lazy('dashboard:university_edit', kwargs={'pk': university.pk}))
            .add('الكليات', reverse_lazy('dashboard:faculty_list', kwargs={'university_id': university.pk}))
            .current('حذف')
            .build())

    def get_success_url(self):
        """Return success URL with university context."""
        return reverse_lazy('dashboard:faculty_list', kwargs={'university_id': self.object.university.pk})

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        faculty = self.get_object()
        faculty_name = faculty.name
        university = faculty.university
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'تم حذف الكلية "{faculty_name}" وجميع البرامج المرتبطة بها بنجاح'
        )
        return response

    def get_context_data(self, **kwargs):
        """Add page title and university to context."""
        context = super().get_context_data(**kwargs)
        university = self.object.university
        
        context['page_title'] = f'حذف الكلية: {self.object.name}'
        context['university'] = university
        return context


# ============================================================================
# Institute Management Views
# ============================================================================

class InstituteListView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, ListView):
    """
    List all institutes with search and status filters.
    عرض قائمة بجميع المعاهد مع البحث والتصفية حسب الحالة
    
    Features:
    - Search by name and slug
    - Filter by publish_status (published/unpublished)
    - Display course count for each institute
    - Pagination (20 per page)
    - Show publish status with visual indicator
    
    Query Optimization:
    - Uses prefetch_related for courses to avoid N+1 queries
    """
    model = Institute
    template_name = 'dashboard/institutes/list.html'
    context_object_name = 'institutes'
    paginate_by = 20

    def get_breadcrumbs(self):
        """Build breadcrumb trail for institute list page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('المعاهد')
            .build())

    def get_queryset(self):
        """Get institutes with optional search and filtering."""
        queryset = Institute.objects.all().prefetch_related(
            'courses',
            'related_articles'
        ).order_by('order', 'name')
        
        # Search by name or slug
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(slug__icontains=search_query) |
                Q(state__icontains=search_query) |
                Q(city__icontains=search_query)
            )
        
        # Filter by publish_status
        status_filter = self.request.GET.get('status', '').strip()
        if status_filter == 'published':
            queryset = queryset.filter(publish_status='published')
        elif status_filter == 'unpublished':
            queryset = queryset.filter(publish_status='unpublished')
            
        # Filter by state
        state_filter = self.request.GET.get('state', '').strip().lower()
        if state_filter:
            queryset = queryset.filter(state=state_filter)
            
        # Filter by city
        city_filter = self.request.GET.get('city', '').strip().lower()
        if city_filter:
            queryset = queryset.filter(city=city_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add page title and search/filter info to context."""
        from django.urls import reverse
        from apps.universities.models import University
        import json
        
        context = super().get_context_data(**kwargs)
        
        # Clean expired and get active locks for institutes
        try:
            ContentLock.objects.filter(expires_at__lt=timezone.now()).delete()
        except Exception:
            pass
        ct = ContentType.objects.get_for_model(Institute)
        active_locks = ContentLock.objects.filter(content_type=ct).select_related('user')
        context['locked_objects'] = {
            lock.object_id: lock.user.get_full_name() or lock.user.username 
            for lock in active_locks
        }

        context['page_title'] = 'إدارة المعاهد'
        context['page_type'] = 'institutes'
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['state_filter'] = self.request.GET.get('state', '')
        context['city_filter'] = self.request.GET.get('city', '')
        
        # Add items for list_page.html template
        context['items'] = context.get('institutes', context.get('object_list', []))
        
        # Add required context variables for list_page.html
        context['search_placeholder'] = 'ابحث عن اسم المعهد...'
        context['search_value'] = context['search_query']
        context['base_url'] = reverse('dashboard:institute_list')
        context['bulk_action_url'] = reverse('dashboard:institute_bulk_action')
        
        # Get only the states and cities that are actually assigned
        used_states = Institute.objects.values_list('state', flat=True).order_by().distinct()
        state_choices_dict = dict(University.STATE_CHOICES)
        used_state_options = []
        for code in used_states:
            if code and code in state_choices_dict:
                used_state_options.append({'value': code, 'label': state_choices_dict[code]})
        used_state_options.sort(key=lambda x: x['label'])

        used_cities = Institute.objects.values_list('city', flat=True).order_by().distinct()
        city_choices_dict = {}
        for state_code, cities in University.STATE_CITIES.items():
            for c_slug, c_name in cities:
                city_choices_dict[c_slug] = c_name
        
        used_city_options = []
        for code in used_cities:
            if code and code in city_choices_dict:
                used_city_options.append({'value': code, 'label': city_choices_dict[code]})
        used_city_options.sort(key=lambda x: x['label'])

        # Filters
        context['filters'] = [
            {
                'name': 'status',
                'label': 'حالة النشر',
                'options': [
                    {'value': 'published', 'label': 'منشور'},
                    {'value': 'unpublished', 'label': 'غير منشور'},
                ],
                'selected': context['status_filter'],
            },
            {
                'name': 'state',
                'label': 'الولاية',
                'options': used_state_options,
                'selected': context['state_filter'],
            },
            {
                'name': 'city',
                'label': 'المدينة',
                'options': used_city_options,
                'selected': context['city_filter'],
            },
        ]
        
        # Columns for data table
        context['columns'] = [
            {'label': 'الترتيب', 'key': 'order', 'type': 'text'},
            {'label': 'اسم المعهد', 'key': 'name', 'type': 'link', 'link_url_name': 'dashboard:institute_edit', 'link_param': 'pk'},
            {'label': 'الموقع', 'key': 'city_display', 'type': 'text'},
            {'label': 'الدورات', 'key': 'courses_count', 'type': 'text'},
            {'label': 'الحالة', 'key': 'publish_status', 'type': 'status_badge'},
            {'label': 'تاريخ النشر', 'key': 'created_at', 'type': 'date'},
            {'label': 'تاريخ التحديث', 'key': 'updated_at', 'type': 'date'},
        ]
        
        context['edit_url_name'] = 'dashboard:institute_edit'
        context['delete_url_name'] = 'dashboard:institute_delete'
        
        # Pagination info
        paginator = context.get('paginator')
        context['is_paginated'] = paginator.num_pages > 1 if paginator else False
        context['page_obj'] = context.get('page_obj')
        
        # Build query params for pagination
        query_params = '&'.join([f'{k}={v}' for k, v in self.request.GET.items() if k != 'page'])
        context['query_params'] = query_params
        
        # Add computed properties to each institute
        for institute in context['items']:
            institute.courses_count = institute.courses.count()
            institute.city_display = institute.get_location_display()
            
        return context


class InstituteCreateView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, CreateView):
    """
    Create a new institute with inline Course formset.
    إنشاء معهد جديد مع نموذج الدورات المدمج
    
    Features:
    - Create institute with all fields
    - Add course entries inline
    - Arabic success message
    - Redirect to edit page after creation
    """
    model = Institute
    form_class = InstituteForm
    template_name = 'dashboard/institutes/form.html'

    def get_breadcrumbs(self):
        """Build breadcrumb trail for institute create page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_institutes')
            .current('إضافة معهد')
            .build())

    def get_context_data(self, **kwargs):
        """Add formsets to context."""
        context = super().get_context_data(**kwargs)
        import json
        from apps.universities.models import University
        context['state_cities_json'] = json.dumps(University.STATE_CITIES)
        if self.request.POST:
            context['course_formset'] = CourseFormSet(self.request.POST, instance=self.object)
            context['attachment_formset'] = InstituteAttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
            context['faq_formset'] = InstituteFAQFormSet(self.request.POST, instance=self.object)
        else:
            context['course_formset'] = CourseFormSet(instance=self.object)
            context['attachment_formset'] = InstituteAttachmentFormSet(instance=self.object)
            context['faq_formset'] = InstituteFAQFormSet(instance=self.object)
        context['page_title'] = 'إنشاء معهد جديد'
        
        # Add recently used relations to context
        from apps.articles.models import Article, Tag
        recent_inst_ids = Institute.objects.order_by('-updated_at').values_list('id', flat=True)[:10]
        context['recently_used_articles'] = list(Article.objects.filter(institutes__in=recent_inst_ids).distinct()[:5])
        context['recently_used_tags'] = list(Tag.objects.filter(institutes__in=recent_inst_ids).distinct()[:5])
        
        return context

    def form_valid(self, form):
        """Handle successful form submission with formset.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        context = self.get_context_data()
        course_formset = context['course_formset']
        attachment_formset = context['attachment_formset']
        faq_formset = context['faq_formset']
        
        if course_formset.is_valid() and attachment_formset.is_valid() and faq_formset.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save()
                    course_formset.instance = self.object
                    course_formset.save()
                    attachment_formset.instance = self.object
                    attachment_formset.save()
                    faq_formset.instance = self.object
                    faq_formset.save()
                
                messages.success(
                    self.request,
                    f'تم إنشاء المعهد "{self.object.name}" بنجاح'
                )
                return redirect('dashboard:institute_edit', pk=self.object.pk)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error saving institute: {e}")
                messages.error(self.request, 'حدث خطأ أثناء حفظ المعهد. لم يتم حفظ أي بيانات.')
                return self.form_invalid(form)
        else:
            # Add error messages for formsets
            for error in course_formset.non_form_errors():
                messages.error(self.request, f'خطأ في الدورات: {error}')
            for error_dict in course_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في الدورات: {error}')
                        
            for error in attachment_formset.non_form_errors():
                messages.error(self.request, f'خطأ في المرفقات: {error}')
            for error_dict in attachment_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في المرفقات: {error}')

            for error in faq_formset.non_form_errors():
                messages.error(self.request, f'خطأ في الأسئلة الشائعة: {error}')
            for error_dict in faq_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في الأسئلة الشائعة: {error}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)


class InstituteUpdateView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, LockValidationMixin, UpdateView):
    """
    Update an existing institute with inline Course formset.
    تحديث معهد موجود مع نموذج الدورات المدمج
    
    Features:
    - Edit all institute fields
    - Edit course entries inline
    - Show slug change warning if slug was modified
    - Offer to create redirect for old slug
    - Arabic success message
    """
    model = Institute
    form_class = InstituteForm
    template_name = 'dashboard/institutes/form.html'
    success_url = reverse_lazy('dashboard:institute_list')

    def get_breadcrumbs(self):
        """Build breadcrumb trail for institute update page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_institutes')
            .current('تعديل المعهد')
            .build())

    def get_success_url(self):
        return reverse('dashboard:institute_edit', kwargs={'pk': self.object.pk})

    def _is_ajax(self):
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def get_context_data(self, **kwargs):
        """Add formset and courses to context."""
        context = super().get_context_data(**kwargs)
        import json
        from apps.universities.models import University
        context['state_cities_json'] = json.dumps(University.STATE_CITIES)
        if self.request.POST:
            context['course_formset'] = CourseFormSet(self.request.POST, instance=self.object)
            context['attachment_formset'] = InstituteAttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
            context['faq_formset'] = InstituteFAQFormSet(self.request.POST, instance=self.object)
        else:
            context['course_formset'] = CourseFormSet(instance=self.object)
            context['attachment_formset'] = InstituteAttachmentFormSet(instance=self.object)
            context['faq_formset'] = InstituteFAQFormSet(instance=self.object)
        
        # Add courses list
        context['courses'] = self.object.courses.all().order_by('sort_order', 'id')
        context['page_title'] = f'تحديث المعهد: {self.object.name}'
        
        # Add recently used relations to context
        from apps.articles.models import Article, Tag
        recent_inst_ids = Institute.objects.order_by('-updated_at').values_list('id', flat=True)[:10]
        context['recently_used_articles'] = list(Article.objects.filter(institutes__in=recent_inst_ids).distinct()[:5])
        context['recently_used_tags'] = list(Tag.objects.filter(institutes__in=recent_inst_ids).distinct()[:5])
        
        # Check if slug was changed and show warning
        if hasattr(self.object, '_old_slug'):
            context['slug_changed'] = True
            context['old_slug'] = self.object._old_slug
        
        return context

    def form_valid(self, form):
        """Handle successful form submission with formset.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        context = self.get_context_data()
        course_formset = context['course_formset']
        attachment_formset = context['attachment_formset']
        faq_formset = context['faq_formset']
        
        if course_formset.is_valid() and attachment_formset.is_valid() and faq_formset.is_valid():
            try:
                with transaction.atomic():
                    # Capture pre-save version snapshot of DB state before applying updates
                    from apps.core.services.versioning import VersioningService
                    VersioningService.capture_pre_save_snapshot(
                        self.object,
                        user=self.request.user,
                        change_reason='تحديث المعهد'
                    )

                    # حفظ الـ slug القديم قبل الحفظ
                    old_slug = self.object.slug
                    
                    self.object = form.save()
                    course_formset.instance = self.object
                    course_formset.save()
                    attachment_formset.instance = self.object
                    attachment_formset.save()
                    faq_formset.instance = self.object
                    faq_formset.save()
                    
                    if not self._is_ajax():
                        messages.success(
                            self.request,
                            f'تم تحديث المعهد "{self.object.name}" بنجاح'
                        )
                
                if self._is_ajax():
                    return JsonResponse({"status": "success", "message": "تم حفظ المسودة بنجاح."})
                return redirect(self.get_success_url())
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error updating institute: {e}")
                messages.error(self.request, 'حدث خطأ أثناء تحديث المعهد. لم يتم حفظ أي تغييرات.')
                return self.form_invalid(form)
        else:
            # Add error messages for formsets
            for error in course_formset.non_form_errors():
                messages.error(self.request, f'خطأ في الدورات: {error}')
            for error_dict in course_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في الدورات: {error}')
                        
            for error in attachment_formset.non_form_errors():
                messages.error(self.request, f'خطأ في المرفقات: {error}')
            for error_dict in attachment_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في المرفقات: {error}')

            for error in faq_formset.non_form_errors():
                messages.error(self.request, f'خطأ في الأسئلة الشائعة: {error}')
            for error_dict in faq_formset.errors:
                for field, errors in error_dict.items():
                    for error in errors:
                        messages.error(self.request, f'خطأ في الأسئلة الشائعة: {error}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)


class InstituteDeleteView(ContentAdminRequiredMixin, DeleteView):
    """
    Delete an institute with confirmation.
    حذف معهد مع تأكيد
    
    Features:
    - Confirmation page showing institute name
    - Arabic success message
    - Cascade delete of related courses
    """
    model = Institute
    template_name = 'dashboard/institutes/delete_confirm.html'
    success_url = reverse_lazy('dashboard:institute_list')

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        institute = self.get_object()
        institute_name = institute.name
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'تم حذف المعهد "{institute_name}" وجميع الدورات المرتبطة به بنجاح'
        )
        return response

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'حذف المعهد: {self.object.name}'
        return context


# ============================================================================
# Major Management Views
# ============================================================================

class MajorListView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, ListView):
    """
    List all majors with search and status filters.
    عرض قائمة بجميع التخصصات مع البحث والتصفية حسب الحالة
    
    Features:
    - Search by name and slug
    - Filter by publish_status (published/unpublished)
    - Display dynamic table counts for each major
    - Pagination (20 per page)
    - Show publish status with visual indicator
    """
    model = Major
    template_name = 'dashboard/majors/list.html'
    context_object_name = 'majors'
    paginate_by = 20

    def get_breadcrumbs(self):
        """Build breadcrumb trail for major list page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('التخصصات')
            .build())

    def get_queryset(self):
        """Get majors with optional search and filtering."""
        queryset = Major.objects.all().select_related('category').prefetch_related(
            'subjects_tables', 'salary_tables', 'countries_tables',
            'best_universities', 'cheap_universities', 'related_articles'
        ).order_by('order', 'name')
        
        # Search by name or slug
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(slug__icontains=search_query)
            )
        
        # Filter by publish_status
        status_filter = self.request.GET.get('status', '').strip()
        if status_filter == 'published':
            queryset = queryset.filter(publish_status='published')
        elif status_filter == 'unpublished':
            queryset = queryset.filter(publish_status='unpublished')
        
        # Filter by category slug
        category_filter = self.request.GET.get('category', '').strip()
        if category_filter:
            queryset = queryset.filter(category__slug=category_filter)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title and search/filter info to context."""
        from django.urls import reverse
        
        context = super().get_context_data(**kwargs)
        
        # Clean expired and get active locks for majors
        try:
            ContentLock.objects.filter(expires_at__lt=timezone.now()).delete()
        except Exception:
            pass
        ct = ContentType.objects.get_for_model(Major)
        active_locks = ContentLock.objects.filter(content_type=ct).select_related('user')
        context['locked_objects'] = {
            lock.object_id: lock.user.get_full_name() or lock.user.username 
            for lock in active_locks
        }

        context['page_title'] = 'إدارة التخصصات'
        context['page_type'] = 'majors'
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['category_filter'] = self.request.GET.get('category', '')
        
        # Add items for list_page.html template
        context['items'] = context.get('majors', context.get('object_list', []))
        
        # Add required context variables for list_page.html
        context['search_placeholder'] = 'ابحث عن اسم التخصص...'
        context['search_value'] = context['search_query']
        context['base_url'] = reverse('dashboard:major_list')
        context['bulk_action_url'] = reverse('dashboard:major_bulk_action')
        
        # Filters
        # Populate category filter options from database
        from apps.majors.models import MajorCategory
        category_options = [
            {'value': cat.slug, 'label': cat.name}
            for cat in MajorCategory.objects.all().order_by('name')
        ]

        context['filters'] = [
            {
                'name': 'status',
                'label': 'حالة النشر',
                'options': [
                    {'value': 'published', 'label': 'منشور'},
                    {'value': 'unpublished', 'label': 'غير منشور'},
                ],
                'selected': context['status_filter'],
            },
            {
                'name': 'category',
                'label': 'تصنيف التخصص',
                'options': category_options,
                'selected': context['category_filter'],
            },
        ]
        
        # Columns for data table
        context['columns'] = [
            {'label': 'الترتيب', 'key': 'order', 'type': 'text'},
            {'label': 'اسم التخصص', 'key': 'name', 'type': 'link', 'link_url_name': 'dashboard:major_edit', 'link_param': 'pk'},
            {'label': 'التصنيف', 'key': 'major_category_display', 'type': 'text'},
            {'label': 'الحالة', 'key': 'publish_status', 'type': 'status_badge'},
            {'label': 'تاريخ النشر', 'key': 'created_at', 'type': 'date'},
            {'label': 'تاريخ التحديث', 'key': 'updated_at', 'type': 'date'},
        ]
        
        # Row actions
        context['edit_url_name'] = 'dashboard:major_edit'
        context['delete_url_name'] = 'dashboard:major_delete'
        
        # Pagination info
        paginator = context.get('paginator')
        context['is_paginated'] = paginator.num_pages > 1 if paginator else False
        context['page_obj'] = context.get('page_obj')
        
        # Build query params for pagination
        query_params = '&'.join([f'{k}={v}' for k, v in self.request.GET.items() if k != 'page'])
        context['query_params'] = query_params
        
        # Add computed properties to each major
        for major in context['items']:
            major.major_category_display = major.category.name if major.category else 'غير مصنف'
            
        return context


class MajorCreateView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, CreateView):
    """
    Create a new major with all inline formsets.
    إنشاء تخصص جديد مع نماذج الجداول والمرفقات والأسئلة الشائعة المدمجة
    """
    model = Major
    form_class = MajorForm
    template_name = 'dashboard/majors/form.html'

    def get_breadcrumbs(self):
        """Build breadcrumb trail for major create page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_majors')
            .current('إضافة تخصص')
            .build())

    def get_context_data(self, **kwargs):
        """Add formsets to context."""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['subjects_formset'] = SubjectsTableFormSet(self.request.POST, instance=self.object)
            context['salary_formset'] = SalaryTableFormSet(self.request.POST, instance=self.object)
            context['countries_formset'] = CountriesTableFormSet(self.request.POST, instance=self.object)
            context['faqs_formset'] = MajorFAQFormSet(self.request.POST, instance=self.object)
            context['attachments_formset'] = MajorAttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['subjects_formset'] = SubjectsTableFormSet(instance=self.object)
            context['salary_formset'] = SalaryTableFormSet(instance=self.object)
            context['countries_formset'] = CountriesTableFormSet(instance=self.object)
            context['faqs_formset'] = MajorFAQFormSet(instance=self.object)
            context['attachments_formset'] = MajorAttachmentFormSet(instance=self.object)
        context['page_title'] = 'إنشاء تخصص جديد'
        
        # Add recently used relations to context
        recent_majors_ids = Major.objects.order_by('-updated_at').values_list('id', flat=True)[:10]
        context['recently_used_universities'] = list(University.objects.filter(
            Q(best_majors__in=recent_majors_ids) | 
            Q(cheap_majors__in=recent_majors_ids) |
            Q(related_majors__in=recent_majors_ids)
        ).distinct()[:5])
        if len(context['recently_used_universities']) < 5:
            current_ids = [u.id for u in context['recently_used_universities']]
            extra_universities = University.objects.exclude(id__in=current_ids).order_by('-updated_at')[:5 - len(current_ids)]
            context['recently_used_universities'] = list(context['recently_used_universities']) + list(extra_universities)

        context['recently_used_articles'] = list(Article.objects.filter(majors__in=recent_majors_ids).distinct()[:5])
        if len(context['recently_used_articles']) < 5:
            current_ids = [a.id for a in context['recently_used_articles']]
            extra_articles = Article.objects.exclude(id__in=current_ids).order_by('-updated_at')[:5 - len(current_ids)]
            context['recently_used_articles'] = list(context['recently_used_articles']) + list(extra_articles)

        return context

    def form_valid(self, form):
        """Handle successful form submission with formsets."""
        context = self.get_context_data()
        subjects_formset = context['subjects_formset']
        salary_formset = context['salary_formset']
        countries_formset = context['countries_formset']
        faqs_formset = context['faqs_formset']
        attachments_formset = context['attachments_formset']
        
        if (subjects_formset.is_valid() and salary_formset.is_valid() and 
            countries_formset.is_valid() and faqs_formset.is_valid() and 
            attachments_formset.is_valid()):
            try:
                with transaction.atomic():
                    self.object = form.save()
                    
                    subjects_formset.instance = self.object
                    subjects_formset.save()
                    
                    salary_formset.instance = self.object
                    salary_formset.save()
                    
                    countries_formset.instance = self.object
                    countries_formset.save()
                    
                    faqs_formset.instance = self.object
                    faqs_formset.save()
                    
                    attachments_formset.instance = self.object
                    attachments_formset.save()
                
                messages.success(
                    self.request,
                    f'تم إنشاء التخصص "{self.object.name}" بنجاح'
                )
                return redirect('dashboard:major_edit', pk=self.object.pk)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error saving major: {e}")
                messages.error(self.request, 'حدث خطأ أثناء حفظ التخصص. لم يتم حفظ أي بيانات.')
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)


class MajorUpdateView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, LockValidationMixin, UpdateView):
    """
    Update an existing major with all inline formsets.
    تحديث تخصص موجود مع نماذج الجداول والمرفقات والأسئلة الشائعة المدمجة
    """
    model = Major
    form_class = MajorForm
    template_name = 'dashboard/majors/form.html'

    def get_success_url(self):
        return reverse('dashboard:major_edit', kwargs={'pk': self.object.pk})

    def get_breadcrumbs(self):
        """Build breadcrumb trail for major edit page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_majors')
            .current(f'تعديل: {self.object.name}')
            .build())

    def _is_ajax(self):
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def get_context_data(self, **kwargs):
        """Add formsets to context."""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['subjects_formset'] = SubjectsTableFormSet(self.request.POST, instance=self.object)
            context['salary_formset'] = SalaryTableFormSet(self.request.POST, instance=self.object)
            context['countries_formset'] = CountriesTableFormSet(self.request.POST, instance=self.object)
            context['faqs_formset'] = MajorFAQFormSet(self.request.POST, instance=self.object)
            context['attachments_formset'] = MajorAttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['subjects_formset'] = SubjectsTableFormSet(instance=self.object)
            context['salary_formset'] = SalaryTableFormSet(instance=self.object)
            context['countries_formset'] = CountriesTableFormSet(instance=self.object)
            context['faqs_formset'] = MajorFAQFormSet(instance=self.object)
            context['attachments_formset'] = MajorAttachmentFormSet(instance=self.object)
        
        context['page_title'] = f'تحديث التخصص: {self.object.name}'
        
        # Add recently used relations to context
        recent_majors_ids = Major.objects.order_by('-updated_at').values_list('id', flat=True)[:10]
        context['recently_used_universities'] = list(University.objects.filter(
            Q(best_majors__in=recent_majors_ids) | 
            Q(cheap_majors__in=recent_majors_ids) |
            Q(related_majors__in=recent_majors_ids)
        ).distinct()[:5])
        if len(context['recently_used_universities']) < 5:
            current_ids = [u.id for u in context['recently_used_universities']]
            extra_universities = University.objects.exclude(id__in=current_ids).order_by('-updated_at')[:5 - len(current_ids)]
            context['recently_used_universities'] = list(context['recently_used_universities']) + list(extra_universities)

        context['recently_used_articles'] = list(Article.objects.filter(majors__in=recent_majors_ids).distinct()[:5])
        if len(context['recently_used_articles']) < 5:
            current_ids = [a.id for a in context['recently_used_articles']]
            extra_articles = Article.objects.exclude(id__in=current_ids).order_by('-updated_at')[:5 - len(current_ids)]
            context['recently_used_articles'] = list(context['recently_used_articles']) + list(extra_articles)
        
        # Check if slug was changed and show warning
        if hasattr(self.object, '_old_slug'):
            context['slug_changed'] = True
            context['old_slug'] = self.object._old_slug
        
        return context

    def form_valid(self, form):
        """Handle successful form submission with formsets."""
        context = self.get_context_data()
        subjects_formset = context['subjects_formset']
        salary_formset = context['salary_formset']
        countries_formset = context['countries_formset']
        faqs_formset = context['faqs_formset']
        attachments_formset = context['attachments_formset']
        
        if (subjects_formset.is_valid() and salary_formset.is_valid() and 
            countries_formset.is_valid() and faqs_formset.is_valid() and 
            attachments_formset.is_valid()):
            try:
                with transaction.atomic():
                    # Capture pre-save version snapshot of DB state before applying updates
                    from apps.core.services.versioning import VersioningService
                    VersioningService.capture_pre_save_snapshot(
                        self.object,
                        user=self.request.user,
                        change_reason='تحديث التخصص'
                    )

                    # حفظ الـ slug القديم قبل الحفظ
                    old_slug = self.object.slug
                    
                    self.object = form.save()
                    
                    subjects_formset.instance = self.object
                    subjects_formset.save()
                    
                    salary_formset.instance = self.object
                    salary_formset.save()
                    
                    countries_formset.instance = self.object
                    countries_formset.save()
                    
                    faqs_formset.instance = self.object
                    faqs_formset.save()
                    
                    attachments_formset.instance = self.object
                    attachments_formset.save()
                    
                    if not self._is_ajax():
                        messages.success(
                            self.request,
                            f'تم تحديث التخصص "{self.object.name}" بنجاح'
                        )
                
                if self._is_ajax():
                    return JsonResponse({"status": "success", "message": "تم حفظ المسودة بنجاح."})
                return redirect(self.get_success_url())
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error updating major: {e}")
                messages.error(self.request, 'حدث خطأ أثناء تحديث التخصص. لم يتم حفظ أي تغييرات.')
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)



class MajorDeleteView(ContentAdminRequiredMixin, DeleteView):
    """
    Delete a major with confirmation.
    حذف تخصص مع تأكيد
    
    Features:
    - Confirmation page showing major name
    - Arabic success message
    - Cascade delete of related dynamic tables
    """
    model = Major
    template_name = 'dashboard/majors/delete_confirm.html'
    success_url = reverse_lazy('dashboard:major_list')

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        major = self.get_object()
        major_name = major.name
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'تم حذف التخصص "{major_name}" وجميع الجداول الديناميكية المرتبطة به بنجاح'
        )
        return response

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'حذف التخصص: {self.object.name}'
        return context


# ============================================================================
# Major Category Management Views
# ============================================================================

class MajorCategoryListView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, ListView):
    """
    List all major categories with search filter.
    عرض قائمة بجميع تصنيفات التخصصات مع البحث والتصفية
    """
    model = MajorCategory
    template_name = 'dashboard/major_categories/list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_breadcrumbs(self):
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('تصنيفات التخصصات')
            .build())

    def get_queryset(self):
        from django.db.models import Count
        queryset = MajorCategory.objects.all().annotate(majors_count=Count('majors')).order_by('sort_order', 'name')
        
        # Search by name or slug
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(slug__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = context.get('categories', context.get('object_list', []))
        context['page_title'] = 'إدارة تصنيفات التخصصات'
        context['page_description'] = 'إدارة جميع تصنيفات التخصصات'
        context['search_query'] = self.request.GET.get('search', '')
        context['base_url'] = reverse_lazy('dashboard:major_category_list')
        context['search_placeholder'] = 'ابحث عن اسم التصنيف أو الرابط...'
        context['empty_state_icon'] = '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path></svg>'
        
        # Action button for topbar
        context['action_buttons'] = [
            {
                'url': reverse_lazy('dashboard:major_category_create'),
                'label': 'إضافة تصنيف جديد',
                'variant': 'primary',
            }
        ]
        
        # Columns definition
        context['columns'] = [
            {'label': 'اسم التصنيف', 'key': 'name', 'type': 'link', 'link_url_name': 'dashboard:major_category_edit', 'link_param': 'id'},
            {'label': 'الرابط (Slug)', 'key': 'slug', 'type': 'text'},
            {'label': 'عدد التخصصات', 'key': 'majors_count', 'type': 'text'},
            {'label': 'ترتيب العرض', 'key': 'sort_order', 'type': 'text'},
        ]
        
        # Row action configurations
        context['edit_url_name'] = 'dashboard:major_category_edit'
        context['delete_url_name'] = 'dashboard:major_category_delete'
        
        return context


class MajorCategoryCreateView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, CreateView):
    """
    Create a new major category.
    إنشاء تصنيف تخصص جديد
    """
    model = MajorCategory
    form_class = MajorCategoryForm
    template_name = 'dashboard/major_categories/form.html'
    success_url = reverse_lazy('dashboard:major_category_list')

    def get_breadcrumbs(self):
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('major_category_list')
            .current('إضافة تصنيف')
            .build())

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء تصنيف التخصص "{self.object.name}" بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إضافة تصنيف تخصص جديد'
        context['submit_label'] = 'حفظ التصنيف'
        context['cancel_url'] = self.success_url
        return context


class MajorCategoryUpdateView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, UpdateView):
    """
    Update an existing major category.
    تعديل تصنيف تخصص موجود
    """
    model = MajorCategory
    form_class = MajorCategoryForm
    template_name = 'dashboard/major_categories/form.html'
    success_url = reverse_lazy('dashboard:major_category_list')

    def get_breadcrumbs(self):
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('major_category_list')
            .current(f'تعديل: {self.object.name}')
            .build())

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث تصنيف التخصص "{self.object.name}" بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'تعديل تصنيف التخصص: {self.object.name}'
        context['submit_label'] = 'حفظ التعديلات'
        context['cancel_url'] = self.success_url
        return context


class MajorCategoryDeleteView(ContentAdminRequiredMixin, DeleteView):
    """
    Delete a major category with confirmation.
    حذف تصنيف تخصص مع تأكيد
    """
    model = MajorCategory
    template_name = 'dashboard/major_categories/delete_confirm.html'
    success_url = reverse_lazy('dashboard:major_category_list')

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        category_name = category.name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'تم حذف تصنيف التخصص "{category_name}" بنجاح')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'حذف تصنيف التخصص: {self.object.name}'
        context['item_name'] = self.object.name
        context['cancel_url'] = self.success_url
        context['delete_url'] = self.request.path
        return context


# ============================================================================
# Category Management Views
# ============================================================================

class CategoryListView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, ListView):
    """
    List all article categories with search filter.
    عرض قائمة بجميع فئات المقالات مع البحث
    
    Features:
    - Search by name and slug
    - Display article count for each category
    - Pagination (20 per page)
    - Edit and delete options for each category
    """
    model = Category
    template_name = 'dashboard/categories/list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_breadcrumbs(self):
        """Build breadcrumb trail for category list page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('فئات المقالات')
            .build())

    def get_queryset(self):
        """Get categories with optional search."""
        from django.db.models import Count
        queryset = Category.objects.all().annotate(articles_count=Count('articles')).order_by('name')
        
        # Search by name or slug
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(slug__icontains=search_query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title and search info to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إدارة تصنيفات المقالات'
        context['page_description'] = 'إدارة جميع تصنيفات المقالات'
        context['search_query'] = self.request.GET.get('search', '')
        context['base_url'] = reverse_lazy('dashboard:category_list')
        context['search_placeholder'] = 'ابحث عن اسم التصنيف أو الرابط...'
        context['empty_state_icon'] = '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path></svg>'
        
        # Action button for topbar
        context['action_buttons'] = [
            {
                'url': reverse_lazy('dashboard:category_create'),
                'label': 'إضافة تصنيف جديد',
                'variant': 'primary',
            }
        ]
        
        # Columns definition
        context['columns'] = [
            {'label': 'اسم التصنيف', 'key': 'name', 'type': 'link', 'link_url_name': 'dashboard:category_edit', 'link_param': 'id'},
            {'label': 'الرابط', 'key': 'slug', 'type': 'text'},
            {'label': 'عدد المقالات', 'key': 'articles_count', 'type': 'text'},
            {'label': 'تاريخ الإنشاء', 'key': 'created_at', 'type': 'date'},
        ]
        
        context['edit_url_name'] = 'dashboard:category_edit'
        context['delete_url_name'] = 'dashboard:category_delete'
        
        # Add items for list_page.html template
        context['items'] = context.get('categories', context.get('object_list', []))
        context['query_params'] = '&'.join([f'{k}={v}' for k, v in self.request.GET.items() if k != 'page'])
        return context


class CategoryCreateView(ContentAdminRequiredMixin, CreateView):
    """
    Create a new article category via modal/redirect.
    """
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy('dashboard:category_list')

    def get(self, request, *args, **kwargs):
        """Redirect GET requests to list page since creation is done via modal."""
        return redirect(self.success_url)

    def form_valid(self, form):
        """Handle successful form submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'تم إنشاء التصنيف \"{self.object.name}\" بنجاح'
        )
        return response

    def form_invalid(self, form):
        """Handle form errors and redirect to list page."""
        for field, errors in form.errors.items():
            for error in errors:
                label = form.fields[field].label if field in form.fields else field
                messages.error(self.request, f'{label}: {error}')
        return redirect(self.success_url)


class CategoryUpdateView(ContentAdminRequiredMixin, UpdateView):
    """
    Update an existing article category.
    """
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy('dashboard:category_list')

    def get(self, request, *args, **kwargs):
        """Return JSON for AJAX modal populating, redirect to list page otherwise."""
        self.object = self.get_object()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('json') == '1':
            return JsonResponse({
                'id': self.object.id,
                'name': self.object.name,
                'slug': self.object.slug,
                'description': self.object.description
            })
        return redirect(self.success_url)

    def form_valid(self, form):
        """Handle successful form submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'تم تحديث التصنيف \"{self.object.name}\" بنجاح'
        )
        return response

    def form_invalid(self, form):
        """Handle form errors and redirect to list page."""
        for field, errors in form.errors.items():
            for error in errors:
                label = form.fields[field].label if field in form.fields else field
                messages.error(self.request, f'{label}: {error}')
        return redirect(self.success_url)


class CategoryDeleteView(ContentAdminRequiredMixin, DeleteView):
    """
    Delete an article category with confirmation.
    حذف فئة مقالات مع تأكيد
    
    Features:
    - Confirmation page showing category name and article count
    - Arabic success message
    - Note about articles that will be affected
    """
    model = Category
    template_name = 'dashboard/categories/delete_confirm.html'
    success_url = reverse_lazy('dashboard:category_list')

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        category = self.get_object()
        category_name = category.name
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'تم حذف التصنيف "{category_name}" بنجاح'
        )
        return response

    def get_context_data(self, **kwargs):
        """Add page title and article count to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'حذف التصنيف: {self.object.name}'
        context['article_count'] = self.object.articles.count()
        return context


# ============================================================================
# Tag Management Views
# ============================================================================

class TagListView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, ListView):
    """
    List all tags with search filter dynamically grouped by type.
    عرض قائمة بالوسوم حسب النوع المختار مع البحث
    """
    model = Tag
    template_name = 'dashboard/tags/list.html'
    context_object_name = 'tags'
    paginate_by = 20

    def get_breadcrumbs(self):
        """Build breadcrumb trail for tag list page."""
        tag_type = self.request.GET.get('type', 'article')
        if tag_type == 'university':
            current_label = 'وسوم الجامعات'
        elif tag_type == 'institute':
            current_label = 'وسوم المعاهد'
        else:
            current_label = 'وسوم المقالات'

        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current(current_label)
            .build())

    def get_queryset(self):
        """Get tags with optional search."""
        from django.db.models import Count
        tag_type = self.request.GET.get('type', 'article')
        
        if tag_type == 'university':
            queryset = Tag.objects.all().annotate(item_count=Count('universities'))
        elif tag_type == 'institute':
            queryset = Tag.objects.all().annotate(item_count=Count('institutes'))
        else:
            queryset = Tag.objects.all().annotate(item_count=Count('articles'))
            
        queryset = queryset.order_by('name')
        
        # Search by name or slug
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(slug__icontains=search_query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title and search info to context."""
        context = super().get_context_data(**kwargs)
        tag_type = self.request.GET.get('type', 'article')
        context['tag_type'] = tag_type
        
        if tag_type == 'university':
            context['page_title'] = 'إدارة وسوم الجامعات'
            context['page_description'] = 'إدارة جميع وسوم الجامعات'
            count_label = 'عدد الجامعات'
        elif tag_type == 'institute':
            context['page_title'] = 'إدارة وسوم المعاهد'
            context['page_description'] = 'إدارة جميع وسوم المعاهد'
            count_label = 'عدد المعاهد'
        else:
            context['page_title'] = 'إدارة وسوم المقالات'
            context['page_description'] = 'إدارة جميع وسوم المقالات'
            count_label = 'عدد المقالات'

        context['search_query'] = self.request.GET.get('search', '')
        context['base_url'] = reverse_lazy('dashboard:tag_list')
        context['search_placeholder'] = 'ابحث عن اسم الوسم أو الرابط...'
        context['empty_state_icon'] = '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path></svg>'
        
        # Action button for topbar
        context['action_buttons'] = [
            {
                'url': f"{reverse_lazy('dashboard:tag_create')}?type={tag_type}",
                'label': 'إضافة وسم جديد',
                'variant': 'primary',
            }
        ]
        
        # Columns definition
        context['columns'] = [
            {'label': 'اسم الوسم', 'key': 'name', 'type': 'link', 'link_url_name': 'dashboard:tag_edit', 'link_param': 'id'},
            {'label': 'الرابط', 'key': 'slug', 'type': 'text'},
            {'label': count_label, 'key': 'item_count', 'type': 'text'},
        ]
        
        context['edit_url_name'] = 'dashboard:tag_edit'
        context['delete_url_name'] = 'dashboard:tag_delete'
        
        # Add items for list_page.html template
        context['items'] = context.get('tags', context.get('object_list', []))
        context['query_params'] = '&'.join([f'{k}={v}' for k, v in self.request.GET.items() if k != 'page'])
        return context


class TagCreateView(ContentAdminRequiredMixin, CreateView):
    """
    Create a new tag via modal/redirect.
    """
    model = Tag
    form_class = TagForm

    def get_success_url(self):
        tag_type = self.request.GET.get('type', 'article')
        return f"{reverse_lazy('dashboard:tag_list')}?type={tag_type}"

    def get(self, request, *args, **kwargs):
        """Redirect GET requests to list page since creation is done via modal."""
        return redirect(self.get_success_url())

    def form_valid(self, form):
        """Handle successful form submission."""
        self.object = form.save()
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('json') == '1':
            return JsonResponse({
                'status': 'success',
                'id': self.object.id,
                'name': self.object.name,
                'slug': self.object.slug
            })
        messages.success(
            self.request,
            f'تم إنشاء الوسم "{self.object.name}" بنجاح'
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        """Handle form errors and redirect or return JSON."""
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('json') == '1':
            errors = {field: errs[0] for field, errs in form.errors.items()}
            return JsonResponse({
                'status': 'error',
                'errors': errors
            }, status=400)
        for field, errors in form.errors.items():
            for error in errors:
                label = form.fields[field].label if field in form.fields else field
                messages.error(self.request, f'{label}: {error}')
        return redirect(self.get_success_url())


class TagUpdateView(ContentAdminRequiredMixin, UpdateView):
    """
    Update an existing tag.
    """
    model = Tag
    form_class = TagForm

    def get_success_url(self):
        tag_type = self.request.GET.get('type', 'article')
        return f"{reverse_lazy('dashboard:tag_list')}?type={tag_type}"

    def get(self, request, *args, **kwargs):
        """Return JSON for AJAX modal populating, redirect to list page otherwise."""
        self.object = self.get_object()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('json') == '1':
            return JsonResponse({
                'id': self.object.id,
                'name': self.object.name,
                'slug': self.object.slug,
            })
        return redirect(self.get_success_url())

    def form_valid(self, form):
        """Handle successful form submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'تم تحديث الوسم "{self.object.name}" بنجاح'
        )
        return response

    def form_invalid(self, form):
        """Handle form errors and redirect to list page."""
        for field, errors in form.errors.items():
            for error in errors:
                label = form.fields[field].label if field in form.fields else field
                messages.error(self.request, f'{label}: {error}')
        return redirect(self.get_success_url())


class TagDeleteView(ContentAdminRequiredMixin, DeleteView):
    """
    Delete a tag with confirmation.
    حذف وسم مع تأكيد
    """
    model = Tag
    template_name = 'dashboard/tags/delete_confirm.html'

    def get_success_url(self):
        tag_type = self.request.GET.get('type', 'article')
        return f"{reverse_lazy('dashboard:tag_list')}?type={tag_type}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_type = self.request.GET.get('type', 'article')
        context['tag_type'] = tag_type
        
        # Calculate dynamic counts and labels
        if tag_type == 'university':
            context['entity_name'] = 'جامعة'
            context['entity_plural'] = 'جامعات'
            context['relation_count'] = self.object.universities.count()
        elif tag_type == 'institute':
            context['entity_name'] = 'معهد'
            context['entity_plural'] = 'معاهد'
            context['relation_count'] = self.object.institutes.count()
        else:
            context['entity_name'] = 'مقالة'
            context['entity_plural'] = 'مقالات'
            context['relation_count'] = self.object.articles.count()
            
        return context

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        tag = self.get_object()
        tag_name = tag.name
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'تم حذف الوسم "{tag_name}" بنجاح'
        )
        return response

    def get_context_data(self, **kwargs):
        """Add page title and article count to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'حذف الوسم: {self.object.name}'
        context['article_count'] = self.object.articles.count()
        return context


# ============================================================================
# Article Management Views
# ============================================================================

class ArticleListView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, ListView):
    """
    List all articles with search, category, and status filters.
    عرض قائمة بجميع المقالات مع البحث والتصفية حسب الفئة والحالة
    
    Features:
    - Search by title and slug
    - Filter by category
    - Filter by publish_status (published/unpublished)
    - Display author and publish date for each article
    - Pagination (20 per page)
    - Show publish status with visual indicator
    """
    model = Article
    template_name = 'dashboard/articles/list.html'
    context_object_name = 'articles'
    paginate_by = 20

    def get_breadcrumbs(self):
        """Build breadcrumb trail for article list page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('المقالات')
            .build())

    def get_queryset(self):
        """Get articles with optional search and filtering."""
        queryset = Article.objects.all().select_related(
            'category', 'author'
        ).prefetch_related(
            'tags',
            'related_universities',
            'related_institutes',
            'related_majors'
        ).order_by('-publish_date')
        
        # Search by title or slug
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(slug__icontains=search_query)
            )
        
        # Filter by category
        category_filter = self.request.GET.get('category', '').strip()
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)
        
        # Filter by publish_status
        status_filter = self.request.GET.get('status', '').strip()
        if status_filter == 'published':
            queryset = queryset.filter(publish_status='published')
        elif status_filter == 'unpublished':
            queryset = queryset.filter(publish_status='unpublished')
        
        # Filter by author
        author_filter = self.request.GET.get('author', '').strip()
        if author_filter:
            if author_filter == 'none':
                queryset = queryset.filter(author__isnull=True)
            else:
                queryset = queryset.filter(author_id=author_filter)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title, search/filter info, and categories to context."""
        from django.urls import reverse
        context = super().get_context_data(**kwargs)
        
        # Clean expired and get active locks for articles
        try:
            ContentLock.objects.filter(expires_at__lt=timezone.now()).delete()
        except Exception:
            pass
        ct = ContentType.objects.get_for_model(Article)
        active_locks = ContentLock.objects.filter(content_type=ct).select_related('user')
        context['locked_objects'] = {
            lock.object_id: lock.user.get_full_name() or lock.user.username 
            for lock in active_locks
        }

        context['page_title'] = 'إدارة المقالات'
        context['page_type'] = 'articles'
        context['search_query'] = self.request.GET.get('search', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['author_filter'] = self.request.GET.get('author', '')
        context['categories'] = Category.objects.all().order_by('name')
        context['authors'] = User.objects.filter(articles__isnull=False).distinct().order_by('first_name', 'username')
        context['all_users'] = User.objects.filter(is_active=True).order_by('first_name', 'username')
        
        # Add items for list_page.html/data_table template
        context['items'] = context.get('articles', context.get('object_list', []))
        
        # Add required context variables for filter_bar.html
        context['search_placeholder'] = 'ابحث عن عنوان المقالة أو الرابط...'
        context['search_value'] = context['search_query']
        context['base_url'] = reverse('dashboard:article_list')
        context['add_new_url'] = reverse('dashboard:article_create')
        context['bulk_action_url'] = reverse('dashboard:article_bulk_action')
        
        # Filters
        category_options = []
        for cat in context['categories']:
            category_options.append({'value': str(cat.id), 'label': cat.name})
            
        author_options = []
        if Article.objects.filter(author__isnull=True).exists():
            author_options.append({'value': 'none', 'label': 'بدون كاتب'})
        for auth in context['authors']:
            name = auth.get_full_name().strip() or auth.username
            author_options.append({'value': str(auth.id), 'label': name})
            
        context['filters'] = [
            {
                'name': 'status',
                'label': 'حالة النشر',
                'options': [
                    {'value': 'published', 'label': 'منشور'},
                    {'value': 'unpublished', 'label': 'غير منشور'},
                ],
                'selected': context['status_filter'],
            },
            {
                'name': 'category',
                'label': 'التصنيف',
                'options': category_options,
                'selected': context['category_filter'],
            },
            {
                'name': 'author',
                'label': 'الكاتب',
                'options': author_options,
                'selected': context['author_filter'],
            },
        ]
        
        # Columns for data table
        context['columns'] = [
            {'label': 'العنوان', 'key': 'title', 'type': 'link', 'link_url_name': 'dashboard:article_edit', 'link_param': 'pk'},
            {'label': 'التصنيف', 'key': 'category_name', 'type': 'text'},
            {'label': 'الكاتب', 'key': 'author_name', 'type': 'text'},
            {'label': 'الحالة', 'key': 'publish_status', 'type': 'status_badge'},
            {'label': 'تاريخ النشر', 'key': 'publish_date', 'type': 'date'},
            {'label': 'تاريخ التحديث', 'key': 'updated_at', 'type': 'date'},
        ]
        
        context['edit_url_name'] = 'dashboard:article_edit'
        context['delete_url_name'] = 'dashboard:article_delete'
        
        # Pagination info
        paginator = context.get('paginator')
        context['is_paginated'] = paginator.num_pages > 1 if paginator else False
        context['page_obj'] = context.get('page_obj')
        
        # Build query params for pagination
        query_params = '&'.join([f'{k}={v}' for k, v in self.request.GET.items() if k != 'page'])
        context['query_params'] = query_params
        
        # Add computed properties to each article
        for article in context['items']:
            article.category_name = article.category.name if article.category else 'بدون تصنيف'
            article.author_name = article.author.get_full_name() or article.author.username if article.author else 'غير معروف'
            
        return context


class ArticleCreateView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, CreateView):
    """
    Create a new article with Custom HTML Editor.
    إنشاء مقالة جديدة مع محرر HTML المخصص
    
    Features:
    - Create article with all fields
    - Use Custom HTML Editor for content (V1: Bold, Italic, H2-H4, Lists, Links, Images)
    - Sanitize HTML content before saving
    - Auto-set author to current user
    - Arabic success message
    - Redirect to edit page after creation
    """
    model = Article
    form_class = ArticleForm
    template_name = 'dashboard/articles/form.html'

    def get_breadcrumbs(self):
        """Build breadcrumb trail for article create page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_articles')
            .current('إضافة مقالة')
            .build())

    def form_valid(self, form):
        """Handle successful form submission.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        context = self.get_context_data()
        faq_formset = context['faq_formset']
        attachment_formset = context['attachment_formset']
        
        if faq_formset.is_valid() and attachment_formset.is_valid():
            try:
                with transaction.atomic():
                    # Set author to selected user or current user
                    self.object = form.save(commit=False)
                    if not self.object.author:
                        self.object.author = self.request.user
                    
                    # Sanitize HTML content before saving
                    from apps.html_editor.sanitizer import sanitize_article_html
                    self.object.content = sanitize_article_html(self.object.content)
                    
                    self.object.save()
                    form.save_m2m()  # Save many-to-many relationships
                    
                    # Save FAQs
                    faq_formset.instance = self.object
                    faq_formset.save()

                    # Save Attachments
                    attachment_formset.instance = self.object
                    attachment_formset.save()
                
                messages.success(
                    self.request,
                    f'تم إنشاء المقالة "{self.object.title}" بنجاح'
                )
                return redirect('dashboard:article_edit', pk=self.object.pk)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error saving article: {e}")
                messages.error(self.request, 'حدث خطأ أثناء حفظ المقالة. لم يتم حفظ أي بيانات.')
                return self.form_invalid(form)
        else:
            # Add formset errors to messages
            for formset in [faq_formset, attachment_formset]:
                for error in formset.non_form_errors():
                    messages.error(self.request, f'{error}')
                for error_dict in formset.errors:
                    for field, field_errors in error_dict.items():
                        for error in field_errors:
                            messages.error(self.request, f'{error}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add page title and recently used relations to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إنشاء مقالة جديدة'
        
        if self.request.POST:
            context['faq_formset'] = ArticleFAQFormSet(self.request.POST, instance=self.object)
            context['attachment_formset'] = ArticleAttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['faq_formset'] = ArticleFAQFormSet(instance=self.object)
            context['attachment_formset'] = ArticleAttachmentFormSet(instance=self.object)
        
        # Add recently used relations to context with fallback
        recent_art_ids = Article.objects.order_by('-updated_at').values_list('id', flat=True)[:10]
        
        recently_used_universities = list(University.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_universities) < 5:
            recently_used_universities = list(University.objects.order_by('-updated_at')[:5])
        context['recently_used_universities'] = recently_used_universities
        
        recently_used_institutes = list(Institute.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_institutes) < 5:
            recently_used_institutes = list(Institute.objects.order_by('-updated_at')[:5])
        context['recently_used_institutes'] = recently_used_institutes
        
        recently_used_majors = list(Major.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_majors) < 5:
            recently_used_majors = list(Major.objects.order_by('-updated_at')[:5])
        context['recently_used_majors'] = recently_used_majors
        
        recently_used_tags = list(Tag.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_tags) < 5:
            recently_used_tags = list(Tag.objects.order_by('-name')[:5])
        context['recently_used_tags'] = recently_used_tags
        
        return context


class ArticleUpdateView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, LockValidationMixin, UpdateView):
    """
    Update an existing article with Custom HTML Editor.
    تحديث مقالة موجودة مع محرر HTML المخصص
    
    Features:
    - Edit all article fields
    - Use Custom HTML Editor for content
    - Sanitize HTML content before saving
    - Show slug change warning if slug was modified
    - Offer to create redirect for old slug
    - Arabic success message
    """
    model = Article
    form_class = ArticleForm
    template_name = 'dashboard/articles/form.html'
    success_url = reverse_lazy('dashboard:article_list')

    def get_breadcrumbs(self):
        """Build breadcrumb trail for article edit page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_articles')
            .current('تعديل مقالة')
            .build())

    def get_success_url(self):
        return reverse('dashboard:article_edit', kwargs={'pk': self.object.pk})

    def _is_ajax(self):
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def get_context_data(self, **kwargs):
        """Add page title, slug change warning, and recently used relations to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'تحديث المقالة: {self.object.title}'
        
        if self.request.POST:
            context['faq_formset'] = ArticleFAQFormSet(self.request.POST, instance=self.object)
            context['attachment_formset'] = ArticleAttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['faq_formset'] = ArticleFAQFormSet(instance=self.object)
            context['attachment_formset'] = ArticleAttachmentFormSet(instance=self.object)
            
        # Check if slug was changed and show warning
        if hasattr(self.object, '_old_slug'):
            context['slug_changed'] = True
            context['old_slug'] = self.object._old_slug
            
        # Add recently used relations to context with fallback
        recent_art_ids = Article.objects.order_by('-updated_at').values_list('id', flat=True)[:10]
        
        recently_used_universities = list(University.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_universities) < 5:
            recently_used_universities = list(University.objects.order_by('-updated_at')[:5])
        context['recently_used_universities'] = recently_used_universities
        
        recently_used_institutes = list(Institute.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_institutes) < 5:
            recently_used_institutes = list(Institute.objects.order_by('-updated_at')[:5])
        context['recently_used_institutes'] = recently_used_institutes
        
        recently_used_majors = list(Major.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_majors) < 5:
            recently_used_majors = list(Major.objects.order_by('-updated_at')[:5])
        context['recently_used_majors'] = recently_used_majors
        
        recently_used_tags = list(Tag.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_tags) < 5:
            recently_used_tags = list(Tag.objects.order_by('-name')[:5])
        context['recently_used_tags'] = recently_used_tags
        
        return context

    def form_valid(self, form):
        """Handle successful form submission.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        context = self.get_context_data()
        faq_formset = context['faq_formset']
        attachment_formset = context['attachment_formset']
        
        if faq_formset.is_valid() and attachment_formset.is_valid():
            try:
                with transaction.atomic():
                    # Capture pre-save version snapshot of DB state before applying updates
                    from apps.core.services.versioning import VersioningService
                    VersioningService.capture_pre_save_snapshot(
                        self.object,
                        user=self.request.user,
                        change_reason='تحديث المقالة'
                    )

                    # حفظ الـ slug القديم قبل الحفظ
                    old_slug = self.object.slug
                    
                    # Sanitize HTML content before saving
                    from apps.html_editor.sanitizer import sanitize_article_html
                    self.object = form.save(commit=False)
                    self.object.content = sanitize_article_html(self.object.content)
                    self.object.save()
                    form.save_m2m()  # Save many-to-many relationships
                    
                    # Save FAQs
                    faq_formset.instance = self.object
                    faq_formset.save()

                    # Save Attachments
                    attachment_formset.instance = self.object
                    attachment_formset.save()
                    
                    if not self._is_ajax():
                        messages.success(
                            self.request,
                            f'تم تحديث المقالة "{self.object.title}" بنجاح'
                        )
                
                if self._is_ajax():
                    return JsonResponse({"status": "success", "message": "تم حفظ المسودة بنجاح."})
                return redirect(self.get_success_url())
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error updating article: {e}")
                messages.error(self.request, 'حدث خطأ أثناء تحديث المقالة. لم يتم حفظ أي تغييرات.')
                return self.form_invalid(form)
        else:
            # Add formset errors to messages
            for formset in [faq_formset, attachment_formset]:
                for error in formset.non_form_errors():
                    messages.error(self.request, f'{error}')
                for error_dict in formset.errors:
                    for field, field_errors in error_dict.items():
                        for error in field_errors:
                            messages.error(self.request, f'{error}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)


class ArticleDeleteView(ContentAdminRequiredMixin, DeleteView):
    """
    Delete an article with confirmation.
    حذف مقالة مع تأكيد
    
    Features:
    - Confirmation page showing article title
    - Arabic success message
    """
    model = Article
    template_name = 'dashboard/articles/delete_confirm.html'
    success_url = reverse_lazy('dashboard:article_list')

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        article = self.get_object()
        article_title = article.title
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'تم حذف المقالة "{article_title}" بنجاح'
        )
        return response

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'حذف المقالة: {self.object.title}'
        return context


# ============================================================================
# Lead Management Views
# ============================================================================

class LeadListView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, ListView):
    """
    List all leads with filters: type, date range, search, read status.
    عرض قائمة بجميع الرسائل مع التصفية حسب: النوع، نطاق التاريخ، البحث، حالة القراءة
    
    Features:
    - Filter by lead_type (REGISTRATION, CONTACT)
    - Filter by date range (from_date, to_date)
    - Search by name, email, or phone
    - Filter by read status (read, unread, all)
    - Display lead details: name, email, type, date, read status
    - Pagination (20 per page)
    - Show unread badge count
    - Export button linking to CSV export
    - Mark as read/unread toggle
    
    Requirements: 2, 23
    """
    model = Lead
    template_name = 'dashboard/leads/list.html'
    context_object_name = 'leads'
    paginate_by = 20

    def get_breadcrumbs(self):
        """Build breadcrumb trail for lead list page."""
        lead_type = self.request.GET.get('lead_type', 'registration').strip()
        current_name = 'طلبات التسجيل' if lead_type == 'registration' else 'إدارة الرسائل والاستفسارات'
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current(current_name)
            .build())

    def get_queryset(self):
        """Get leads with optional filtering."""
        queryset = Lead.objects.all().order_by('-created_at')
        
        # Filter by lead_type (default to registration)
        lead_type_filter = self.request.GET.get('lead_type', 'registration').strip()
        if lead_type_filter in [LeadType.REGISTRATION, LeadType.CONTACT]:
            queryset = queryset.filter(lead_type=lead_type_filter)
        
        # Filter by date range
        from_date = self.request.GET.get('from_date', '').strip()
        to_date = self.request.GET.get('to_date', '').strip()
        
        if from_date:
            try:
                from datetime import datetime
                from_datetime = datetime.strptime(from_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=from_datetime)
            except ValueError:
                pass
        
        if to_date:
            try:
                from datetime import datetime, timedelta
                to_datetime = datetime.strptime(to_date, '%Y-%m-%d')
                # Add one day to include the entire to_date day
                to_datetime = to_datetime + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=to_datetime)
            except ValueError:
                pass
        
        # Search by name, email, phone, nationality, institution_name, residence_country, study_level, address, message
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(nationality__icontains=search_query) |
                Q(institution_name__icontains=search_query) |
                Q(residence_country__icontains=search_query) |
                Q(study_level__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(message__icontains=search_query)
            )
        
        # Filter by read status
        read_status = self.request.GET.get('read_status', '').strip()
        if read_status == 'read':
            queryset = queryset.filter(is_read=True)
        elif read_status == 'unread':
            queryset = queryset.filter(is_read=False)
        
        # Filter by registration specific fields
        nationality_val = self.request.GET.get('nationality', '').strip()
        if nationality_val:
            queryset = queryset.filter(nationality=nationality_val)

        study_level_val = self.request.GET.get('study_level', '').strip()
        if study_level_val:
            queryset = queryset.filter(study_level=study_level_val)

        residence_country_val = self.request.GET.get('residence_country', '').strip()
        if residence_country_val:
            queryset = queryset.filter(residence_country=residence_country_val)

        institution_name_val = self.request.GET.get('institution_name', '').strip()
        if institution_name_val:
            queryset = queryset.filter(institution_name=institution_name_val)
            
        # Store base filtered queryset (without archive filter) to count active/archived counts correctly
        self.base_filtered_queryset = queryset

        # Filter by archive status
        archive_status = self.request.GET.get('archive_status', 'active').strip()
        if archive_status == 'archived':
            queryset = queryset.filter(is_archived=True)
        elif archive_status == 'all':
            pass
        else: # active (default)
            queryset = queryset.filter(is_archived=False)

        return queryset

    def get_context_data(self, **kwargs):
        """Add page title, filters, and statistics to context."""
        context = super().get_context_data(**kwargs)
        
        # Add filter values for form
        lead_type_filter = self.request.GET.get('lead_type', 'registration').strip()
        context['lead_type_filter'] = lead_type_filter
        
        # Add page title dynamically
        if lead_type_filter == 'registration':
            context['page_title'] = 'طلبات التسجيل'
        else:
            context['page_title'] = 'إدارة الرسائل والاستفسارات'
        
        context['from_date'] = self.request.GET.get('from_date', '')
        context['to_date'] = self.request.GET.get('to_date', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['read_status'] = self.request.GET.get('read_status', '')
        
        context['nationality_val'] = self.request.GET.get('nationality', '')
        context['study_level_val'] = self.request.GET.get('study_level', '')
        context['residence_country_val'] = self.request.GET.get('residence_country', '')
        context['institution_name_val'] = self.request.GET.get('institution_name', '')

        # Add archive status filter
        archive_status = self.request.GET.get('archive_status', 'active').strip()
        context['archive_status'] = archive_status

        # Calculate counts for active and archived tabs
        base_qs = getattr(self, 'base_filtered_queryset', Lead.objects.filter(lead_type=lead_type_filter))
        # Ensure count matches the current lead type
        base_qs = base_qs.filter(lead_type=lead_type_filter)
        context['active_count'] = base_qs.filter(is_archived=False).count()
        context['archived_count'] = base_qs.filter(is_archived=True).count()

        # Get existing unique filter choices from DB for registrations
        context['existing_nationalities'] = Lead.objects.filter(lead_type=LeadType.REGISTRATION).exclude(nationality='').values_list('nationality', flat=True).distinct().order_by('nationality')
        context['existing_residences'] = Lead.objects.filter(lead_type=LeadType.REGISTRATION).exclude(residence_country='').values_list('residence_country', flat=True).distinct().order_by('residence_country')
        context['existing_institutions'] = Lead.objects.filter(lead_type=LeadType.REGISTRATION).exclude(institution_name='').values_list('institution_name', flat=True).distinct().order_by('institution_name')
        
        # Predefined study levels
        from apps.leads.forms import STUDY_LEVEL_CHOICES
        context['study_levels'] = [c[0] for c in STUDY_LEVEL_CHOICES if c[0]]
        
        # Add lead type choices
        context['lead_types'] = LeadType.choices
        
        # Add unread count (only active/unarchived leads)
        context['unread_count'] = Lead.objects.filter(is_read=False, is_archived=False).count()
        
        # Build query string for export
        query_params = []
        if context['lead_type_filter']:
            query_params.append(f'lead_type={context["lead_type_filter"]}')
        if context['from_date']:
            query_params.append(f'from_date={context["from_date"]}')
        if context['to_date']:
            query_params.append(f'to_date={context["to_date"]}')
        if context['search_query']:
            query_params.append(f'search={context["search_query"]}')
        if context['read_status']:
            query_params.append(f'read_status={context["read_status"]}')
        if context['nationality_val']:
            query_params.append(f'nationality={context["nationality_val"]}')
        if context['study_level_val']:
            query_params.append(f'study_level={context["study_level_val"]}')
        if context['residence_country_val']:
            query_params.append(f'residence_country={context["residence_country_val"]}')
        if context['institution_name_val']:
            query_params.append(f'institution_name={context["institution_name_val"]}')
        if context['archive_status']:
            query_params.append(f'archive_status={context["archive_status"]}')
        
        context['export_url'] = f'?{"&".join(query_params)}' if query_params else ''
        
        # Add items for list_page.html template
        context['items'] = context.get('leads', context.get('object_list', []))
        context['query_params'] = '&'.join([f'{k}={v}' for k, v in self.request.GET.items() if k != 'page'])
        
        return context


class LeadDetailView(ContentAdminRequiredMixin, View):
    """
    Display lead details and mark as read on view.
    عرض تفاصيل الرسالة وتحديد حالة القراءة عند العرض
    
    Features:
    - Display all lead information: name, email, phone, message
    - Display tracking info: source_page, referrer, UTM parameters
    - Display submission timestamp
    - Mark lead as read when viewed (if not already read)
    - Show read status indicator
    - Display notes field (editable)
    - Back button to lead list
    - Edit notes button
    - Delete button
    
    Requirements: 2, 23
    """
    template_name = 'dashboard/leads/detail.html'

    def get(self, request, pk):
        """Display lead details and mark as read."""
        lead = get_object_or_404(Lead, pk=pk)
        
        # Mark as read if not already read
        if not lead.is_read:
            lead.mark_as_read()
        
        context = {
            'page_title': f'تفاصيل الرسالة: {lead.name}',
            'lead': lead,
            'lead_type_display': lead.get_lead_type_display(),
        }
        
        return render(request, self.template_name, context)

    def post(self, request, pk):
        """Handle notes update."""
        lead = get_object_or_404(Lead, pk=pk)
        
        # Update notes if provided
        notes = request.POST.get('notes', '').strip()
        if notes is not None:
            lead.notes = notes
            lead.save(update_fields=['notes'])
            messages.success(request, 'تم تحديث الملاحظات بنجاح')
        
        return redirect('dashboard:lead_detail', pk=lead.pk)


class LeadExportView(ContentAdminRequiredMixin, View):
    """
    Export filtered leads to CSV format.
    تصدير الرسائل المصفاة إلى صيغة CSV
    
    Features:
    - Export all leads or filtered leads based on query parameters
    - Include all lead fields in CSV: name, email, phone, message, type, date, read status
    - Include tracking fields: source_page, referrer, UTM parameters
    - CSV filename includes export date
    - Proper CSV encoding for Arabic text
    - Support same filters as LeadListView: type, date range, search, read status
    
    Requirements: 2, 23
    """

    def get(self, request):
        """Export leads to CSV."""
        import csv
        from datetime import datetime
        
        # Get filtered queryset using same logic as LeadListView
        queryset = Lead.objects.all().order_by('-created_at')
        
        # Apply same filters as LeadListView
        lead_type_filter = request.GET.get('lead_type', 'registration').strip()
        if lead_type_filter in [LeadType.REGISTRATION, LeadType.CONTACT]:
            queryset = queryset.filter(lead_type=lead_type_filter)
        
        from_date = request.GET.get('from_date', '').strip()
        to_date = request.GET.get('to_date', '').strip()
        
        if from_date:
            try:
                from_datetime = datetime.strptime(from_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=from_datetime)
            except ValueError:
                pass
        
        if to_date:
            try:
                from datetime import timedelta
                to_datetime = datetime.strptime(to_date, '%Y-%m-%d')
                to_datetime = to_datetime + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=to_datetime)
            except ValueError:
                pass
        
        search_query = request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(nationality__icontains=search_query) |
                Q(institution_name__icontains=search_query) |
                Q(residence_country__icontains=search_query) |
                Q(study_level__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(message__icontains=search_query)
            )
        
        read_status = request.GET.get('read_status', '').strip()
        if read_status == 'read':
            queryset = queryset.filter(is_read=True)
        elif read_status == 'unread':
            queryset = queryset.filter(is_read=False)
            
        # Filter by registration specific fields
        nationality_val = request.GET.get('nationality', '').strip()
        if nationality_val:
            queryset = queryset.filter(nationality=nationality_val)

        study_level_val = request.GET.get('study_level', '').strip()
        if study_level_val:
            queryset = queryset.filter(study_level=study_level_val)

        residence_country_val = request.GET.get('residence_country', '').strip()
        if residence_country_val:
            queryset = queryset.filter(residence_country=residence_country_val)

        institution_name_val = request.GET.get('institution_name', '').strip()
        if institution_name_val:
            queryset = queryset.filter(institution_name=institution_name_val)
        
        # Filter by archive status
        archive_status = request.GET.get('archive_status', 'active').strip()
        if archive_status == 'archived':
            queryset = queryset.filter(is_archived=True)
        elif archive_status == 'all':
            pass
        else: # active (default)
            queryset = queryset.filter(is_archived=False)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        filename_prefix = "registrations" if lead_type_filter == LeadType.REGISTRATION else "contacts"
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Add BOM for proper UTF-8 encoding in Excel
        response.write('\ufeff')
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header and rows depending on lead_type
        if lead_type_filter == LeadType.REGISTRATION:
            writer.writerow([
                'الاسم',
                'البريد الإلكتروني',
                'رقم الهاتف',
                'الجنسية',
                'المؤسسة التعليمية',
                'دولة الإقامة',
                'المرحلة الدراسية',
                'عنوان الإقامة',
                'ملاحظات إضافية',
                'صفحة المصدر',
                'المرجع',
                'تاريخ الإرسال',
                'تم قراءتها',
                'مؤرشفة',
                'الملاحظات (الإدارة)',
            ])
            for lead in queryset:
                writer.writerow([
                    lead.name,
                    lead.email,
                    lead.phone,
                    lead.nationality,
                    lead.institution_name,
                    lead.residence_country,
                    lead.study_level,
                    lead.address,
                    lead.message,
                    lead.source_page,
                    lead.referrer,
                    lead.created_at.strftime('%Y-%m-%d %H:%M:%S') if lead.created_at else '',
                    'نعم' if lead.is_read else 'لا',
                    'نعم' if lead.is_archived else 'لا',
                    lead.notes,
                ])
        else:
            writer.writerow([
                'الاسم',
                'البريد الإلكتروني',
                'رقم الهاتف',
                'الجنسية',
                'الرسالة الاستفسارية',
                'صفحة المصدر',
                'المرجع',
                'تاريخ الإرسال',
                'تم قراءتها',
                'مؤرشفة',
                'الملاحظات (الإدارة)',
            ])
            for lead in queryset:
                writer.writerow([
                    lead.name,
                    lead.email,
                    lead.phone,
                    lead.nationality,
                    lead.message,
                    lead.source_page,
                    lead.referrer,
                    lead.created_at.strftime('%Y-%m-%d %H:%M:%S') if lead.created_at else '',
                    'نعم' if lead.is_read else 'لا',
                    'نعم' if lead.is_archived else 'لا',
                    lead.notes,
                ])
        
        messages.success(
            request,
            f'تم تصدير {queryset.count()} رسالة بنجاح'
        )
        
        return response


class LeadToggleArchiveView(ContentAdminRequiredMixin, View):
    """
    Toggle is_archived status of a lead.
    تعديل حالة الأرشفة لرسالة محددة
    """
    def post(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)
        
        # Toggle archive status
        if lead.is_archived:
            lead.unarchive()
            action_msg = 'إلغاء أرشفة'
        else:
            lead.archive()
            action_msg = 'أرشفة'
            
        success_message = f'تم {action_msg} الرسالة "{lead.name}" بنجاح'
        
        # Check if requested via AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Recalculate counts
            lead_type = lead.lead_type
            active_count = Lead.objects.filter(lead_type=lead_type, is_archived=False).count()
            archived_count = Lead.objects.filter(lead_type=lead_type, is_archived=True).count()
            unread_count = Lead.objects.filter(is_read=False, is_archived=False).count()
            
            return JsonResponse({
                'status': 'success',
                'message': success_message,
                'is_archived': lead.is_archived,
                'active_count': active_count,
                'archived_count': archived_count,
                'unread_count': unread_count,
            })
            
        messages.success(request, success_message)
        # Redirect back to lead list (with correct lead_type)
        return redirect(f"{reverse_lazy('dashboard:lead_list')}?lead_type={lead.lead_type}")


class LeadBulkArchiveView(ContentAdminRequiredMixin, View):
    """
    Bulk archive/unarchive leads.
    أرشفة أو إلغاء أرشفة مجموعة رسائل دفعة واحدة
    """
    def post(self, request):
        lead_ids = request.POST.getlist('lead_ids[]')
        action = request.POST.get('action', '').strip() # 'archive' or 'unarchive'
        
        if not lead_ids:
            return JsonResponse({'status': 'error', 'message': 'لم يتم تحديد أي رسائل'}, status=400)
            
        leads = Lead.objects.filter(id__in=lead_ids)
        count = leads.count()
        
        if action == 'archive':
            leads.update(is_archived=True)
            action_msg = 'أرشفة'
        elif action == 'unarchive':
            leads.update(is_archived=False)
            action_msg = 'إلغاء أرشفة'
        else:
            return JsonResponse({'status': 'error', 'message': 'إجراء غير معروف'}, status=400)
            
        success_message = f'تم {action_msg} {count} رسالة بنجاح'
        
        # Get lead_type from the first lead if exists to return relevant counts
        first_lead = leads.first()
        lead_type = first_lead.lead_type if first_lead else 'registration'
        
        active_count = Lead.objects.filter(lead_type=lead_type, is_archived=False).count()
        archived_count = Lead.objects.filter(lead_type=lead_type, is_archived=True).count()
        unread_count = Lead.objects.filter(is_read=False, is_archived=False).count()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': success_message,
                'active_count': active_count,
                'archived_count': archived_count,
                'unread_count': unread_count,
            })
            
        messages.success(request, success_message)
        return redirect(f"{reverse_lazy('dashboard:lead_list')}?lead_type={lead_type}")


# ============================================================================
# SEO Management Views
# ============================================================================




# ============================================================================
# Bulk Actions Views
# ============================================================================

class UniversityBulkActionView(ContentAdminRequiredMixin, View):
    """
    Bulk publish/unpublish/delete for universities.
    الإجراءات الجماعية على الجامعات.
    
    Features:
    - Bulk publish selected universities
    - Bulk unpublish selected universities
    - Bulk delete selected universities
    - Confirmation before delete
    - Success message with count
    - Redirect back to list
    
    Requirements: 8
    """
    def post(self, request):
        """Handle bulk actions."""
        action = request.POST.get('action')
        ids = request.POST.getlist('selected_ids')

        if not ids:
            messages.warning(request, 'لم يتم تحديد أي عناصر')
            return redirect('dashboard:university_list')

        qs = University.objects.filter(pk__in=ids)

        if action == 'publish':
            qs.update(publish_status='published')
            messages.success(request, f'تم نشر {qs.count()} جامعة')
        elif action == 'unpublish':
            qs.update(publish_status='unpublished')
            messages.success(request, f'تم إلغاء نشر {qs.count()} جامعة')
        elif action == 'delete':
            count = qs.count()
            qs.delete()
            messages.success(request, f'تم حذف {count} جامعة')

        return redirect('dashboard:university_list')


class InstituteBulkActionView(ContentAdminRequiredMixin, View):
    """Bulk actions for institutes."""
    def post(self, request):
        """Handle bulk actions."""
        action = request.POST.get('action')
        ids = request.POST.getlist('selected_ids')

        if not ids:
            messages.warning(request, 'لم يتم تحديد أي عناصر')
            return redirect('dashboard:institute_list')

        qs = Institute.objects.filter(pk__in=ids)

        if action == 'publish':
            qs.update(publish_status='published')
            messages.success(request, f'تم نشر {qs.count()} معهد')
        elif action == 'unpublish':
            qs.update(publish_status='unpublished')
            messages.success(request, f'تم إلغاء نشر {qs.count()} معهد')
        elif action == 'delete':
            count = qs.count()
            qs.delete()
            messages.success(request, f'تم حذف {count} معهد')

        return redirect('dashboard:institute_list')


class MajorBulkActionView(ContentAdminRequiredMixin, View):
    """Bulk actions for majors."""
    def post(self, request):
        """Handle bulk actions."""
        action = request.POST.get('action')
        ids = request.POST.getlist('selected_ids')

        if not ids:
            messages.warning(request, 'لم يتم تحديد أي عناصر')
            return redirect('dashboard:major_list')

        qs = Major.objects.filter(pk__in=ids)

        if action == 'publish':
            qs.update(publish_status='published')
            messages.success(request, f'تم نشر {qs.count()} تخصص')
        elif action == 'unpublish':
            qs.update(publish_status='unpublished')
            messages.success(request, f'تم إلغاء نشر {qs.count()} تخصص')
        elif action == 'delete':
            count = qs.count()
            qs.delete()
            messages.success(request, f'تم حذف {count} تخصص')

        return redirect('dashboard:major_list')


class ArticleBulkActionView(ContentAdminRequiredMixin, View):
    """Bulk actions for articles."""
    def post(self, request):
        """Handle bulk actions."""
        action = request.POST.get('action')
        ids = request.POST.getlist('selected_ids')

        if not ids:
            messages.warning(request, 'لم يتم تحديد أي عناصر')
            return redirect('dashboard:article_list')

        qs = Article.objects.filter(pk__in=ids)

        if action == 'publish':
            qs.update(publish_status='published')
            messages.success(request, f'تم نشر {qs.count()} مقالة')
        elif action == 'unpublish':
            qs.update(publish_status='unpublished')
            messages.success(request, f'تم إلغاء نشر {qs.count()} مقالة')
        elif action == 'delete':
            count = qs.count()
            qs.delete()
            messages.success(request, f'تم حذف {count} مقالة')
        elif action == 'change_author':
            new_author_id = request.POST.get('new_author_id')
            if new_author_id == 'none':
                qs.update(author=None)
                messages.success(request, f'تم إزالة الكاتب من {qs.count()} مقالة بنجاح')
            elif new_author_id:
                try:
                    new_author = User.objects.get(id=new_author_id)
                    qs.update(author=new_author)
                    messages.success(request, f'تم تغيير الكاتب لـ {qs.count()} مقالة بنجاح إلى "{new_author.get_full_name() or new_author.username}"')
                except User.DoesNotExist:
                    messages.error(request, 'الكاتب المحدد غير موجود')
            else:
                messages.error(request, 'يرجى اختيار الكاتب الجديد لتطبيق التغيير الجماعي')

        return redirect('dashboard:article_list')



# ═══════════════════════════════════════════════════════════════════════════
# ─── EDITOR IMAGE UPLOAD ──────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.middleware.csrf import get_token
from PIL import Image
import io
import os
from datetime import datetime


@require_http_methods(["POST"])
@login_required
def editor_image_upload(request):
    """
    Handle image upload for the HTML editor.
    يتعامل مع رفع الصور للمحرر
    """
    try:
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'لا توجد صورة'}, status=400)

        image_file = request.FILES['image']
        
        # Validate file size (max 5MB)
        if image_file.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'حجم الصورة كبير جداً (الحد الأقصى 5MB)'}, status=400)

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if image_file.content_type not in allowed_types:
            return JsonResponse({'error': 'نوع الملف غير مدعوم'}, status=400)

        # Open and validate image
        try:
            img = Image.open(image_file)
            img.verify()
            img = Image.open(image_file)  # Re-open after verify
        except Exception as e:
            return JsonResponse({'error': 'الملف ليس صورة صحيحة'}, status=400)

        # Optimize image
        max_width = 1200
        max_height = 1200
        
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # Convert to RGB and strip all EXIF/GPS metadata (by pasting onto a new clean RGB image)
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'RGBA':
            rgb_img.paste(img, mask=img.split()[-1])
        else:
            rgb_img.paste(img)
        img = rgb_img

        # Save optimized image
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)

        # Generate filename with better SEO-friendly naming
        from apps.core.models import MediaFile
        from django.utils.text import slugify
        import uuid
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # Try to create SEO-friendly filename from original name
        base_name = os.path.splitext(image_file.name)[0]
        # Slugify for SEO (handles Arabic and special characters)
        seo_slug = slugify(base_name, allow_unicode=False)[:50]
        
        # If slugify produces empty string (e.g., all Arabic), use generic name
        if not seo_slug:
            seo_slug = 'image'
        
        filename = f"{seo_slug}_{timestamp}_{unique_id}.jpg"

        # Create MediaFile instance
        media_file = MediaFile(
            original_filename=image_file.name,
            file_size=len(output.getvalue()),
            width=img.width,
            height=img.height,
            source_type=MediaFile.SourceType.EDITOR,
            uploaded_by=request.user
        )
        
        # Save file to media library
        media_file.file.save(filename, ContentFile(output.getvalue()), save=True)
        url = media_file.file.url

        return JsonResponse({
            'success': True,
            'url': url,
            'filename': os.path.basename(media_file.file.name),
            'size': {
                'width': img.width,
                'height': img.height,
            }
        })

    except Exception as e:
        return JsonResponse({'error': f'خطأ في الرفع: {str(e)}'}, status=500)


class EditorImageUploadView(DashboardMixin, View):
    """
    Class-based view for image upload (alternative to function-based view).
    """
    def post(self, request):
        return editor_image_upload(request)


class SiteSettingsUpdateView(SuperAdminRequiredMixin, DashboardBreadcrumbMixin, UpdateView):
    """
    View for updating site-wide settings.
    عرض تعديل إعدادات الموقع العامة
    """
    model = SiteSettings
    form_class = SiteSettingsForm
    template_name = 'dashboard/settings.html'
    success_url = reverse_lazy('dashboard:settings')

    def get_object(self, queryset=None):
        """Get the singleton SiteSettings instance."""
        return SiteSettings.get_settings()

    def get_breadcrumbs(self):
        """Build breadcrumbs for settings page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('الإعدادات العامة')
            .build())

    def post(self, request, *args, **kwargs):
        """Handle settings saving per tab, supporting AJAX submissions."""
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true':
            self.object = self.get_object()
            submit_tab = request.POST.get('submit_tab')
            
            # Map of tabs to their corresponding fields
            tab_fields = {
                'general': ['site_name', 'site_description'],
                'contact': ['phone', 'email', 'whatsapp'],
                'social': [
                    'facebook', 'instagram', 'twitter', 'youtube',
                    'linkedin', 'tiktok', 'telegram', 'snapchat'
                ],
                'steps': ['registration_steps_title', 'registration_steps_content'],
                'maintenance': [
                    'maintenance_mode', 'maintenance_title', 'maintenance_message',
                    'maintenance_estimated_end', 'maintenance_bypass_ips', 'maintenance_bypass_staff'
                ],
                'email': [
                    'email_smtp_use_dynamic', 'email_smtp_host', 'email_smtp_port',
                    'email_smtp_user', 'email_smtp_password', 'email_smtp_use_tls',
                    'email_smtp_use_ssl', 'email_from_address'
                ],
            }
            
            fields_to_validate = tab_fields.get(submit_tab)
            if not fields_to_validate:
                return JsonResponse({'success': False, 'message': 'إجراء غير صالح'}, status=400)
                
            form = SiteSettingsForm(request.POST, request.FILES, instance=self.object)
            
            # Clean fields dynamically by removing unneeded fields from the form
            for field_name in list(form.fields.keys()):
                if field_name not in fields_to_validate:
                    del form.fields[field_name]
                    
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'تم حفظ التعديلات بنجاح'
                })
            else:
                # Return validation errors as JSON
                errors = {}
                for field, err_list in form.errors.items():
                    label = form.fields[field].label or field
                    errors[field] = f"{label}: {err_list[0]}"
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)
                
        # Fallback to standard generic form submission if not AJAX
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add custom variables for page rendering."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'الإعدادات العامة للموقع'
        context['cancel_url'] = reverse_lazy('dashboard:home')
        return context


class SMTPTestView(SuperAdminRequiredMixin, View):
    """
    View for testing SMTP credentials via AJAX before saving.
    عرض لاختبار إعدادات الـ SMTP عبر AJAX قبل الحفظ.
    """
    def post(self, request, *args, **kwargs):
        from django.core.mail import get_connection, EmailMessage
        from apps.core.utils import SMTPCryptography
        from apps.core.models import SiteSettings
        import traceback

        host = request.POST.get('email_smtp_host')
        port_str = request.POST.get('email_smtp_port')
        user = request.POST.get('email_smtp_user')
        password = request.POST.get('email_smtp_password')
        use_tls = request.POST.get('email_smtp_use_tls') == 'true'
        use_ssl = request.POST.get('email_smtp_use_ssl') == 'true'
        from_email = request.POST.get('email_from_address')
        test_recipient = request.POST.get('test_recipient')

        if not test_recipient:
            return JsonResponse({'success': False, 'error': 'البريد الإلكتروني للمستلم مطلوب لإجراء الاختبار.'})

        # If password is dot placeholders, retrieve from DB and decrypt
        if password == '••••••••' or not password:
            site_settings = SiteSettings.get_settings()
            encrypted = site_settings.email_smtp_password
            password = SMTPCryptography.decrypt(encrypted) if encrypted else ""

        try:
            port = int(port_str) if port_str else 587
        except ValueError:
            return JsonResponse({'success': False, 'error': 'منفذ SMTP غير صالح.'})

        try:
            # Create connection using standard Django EmailBackend
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=host,
                port=port,
                username=user,
                password=password,
                use_tls=use_tls,
                use_ssl=use_ssl,
                timeout=5,  # Short timeout to avoid blocking WSGI workers
            )
            
            # Open connection
            connection.open()
            
            # Send test email
            email = EmailMessage(
                subject='Sciences Gates - اختبار إعدادات الـ SMTP',
                body=(
                    'مرحباً،\n\n'
                    'هذه رسالة تلقائية لتأكيد نجاح اتصال وإعدادات خادم البريد (SMTP) الخاص بموقع بوابات العلوم (Sciences Gates).\n\n'
                    f'الإعدادات المستخدمة:\n'
                    f'- الخادم: {host}\n'
                    f'- المنفذ: {port}\n'
                    f'- المستخدم: {user}\n'
                    f'- نوع التشفير: {"TLS" if use_tls else "SSL" if use_ssl else "بلا تشفير"}\n\n'
                    'إذا استلمت هذه الرسالة، فهذا يعني أن الإعدادات تعمل بنجاح 100%! ويمكنك حفظ التغييرات الآن بأمان.'
                ),
                from_email=from_email or user,
                to=[test_recipient],
                connection=connection
            )
            email.send(fail_silently=False)
            
            return JsonResponse({'success': True})
        except Exception as e:
            error_msg = str(e)
            
            # Friendly messaging for common errors
            if "Authentication failed" in error_msg or "Username and Password not accepted" in error_msg or "535" in error_msg:
                friendly_msg = "فشل في تسجيل الدخول. يرجى التأكد من اسم المستخدم وكلمة المرور. إذا كنت تستخدم Google Workspace، تأكد من استخدام كلمة مرور التطبيق (App Password) بدلاً من كلمة مرور الحساب العادية، وتأكد من تفعيل التحقق بخطوتين في حساب جوجل."
            elif "Connection refused" in error_msg or "Timeout" in error_msg or "timed out" in error_msg or "unreachable" in error_msg or "101" in error_msg:
                friendly_msg = "فشل الاتصال بالخادم (الشبكة غير متاحة). يرجى التحقق من خادم SMTP والمنفذ المستخدمين، والتأكد من أن الاستضافة لا تفرض قيوداً على الاتصالات الخارجية (SMTP Restrictions) تمنع الاتصال الخارجي عبر المنفذ المحدد."
            elif "starttls" in error_msg or "SSL" in error_msg or "TLS" in error_msg:
                friendly_msg = "فشل تأمين الاتصال. يرجى التحقق من توافق خيارات التشفير (TLS/SSL) مع المنفذ المحدد (مثال: TLS للمنفذ 587، أو SSL للمنفذ 465)."
            else:
                friendly_msg = f"حدث خطأ أثناء الاتصال بالخادم: {error_msg}"
                
            return JsonResponse({
                'success': False,
                'error': friendly_msg,
                'technical_details': traceback.format_exc()
            })


class NavigationManagerView(SuperAdminRequiredMixin, DashboardBreadcrumbMixin, TemplateView):
    """
    View for managing curated navigation slots for Mega Menu and Homepage.
    عرض وإدارة الخانات الثابتة للقوائم والصفحة الرئيسية
    """
    template_name = 'dashboard/navigation_manager.html'

    def get_breadcrumbs(self):
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('إدارة القوائم والصفحة الرئيسية')
            .build())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.core.models import SiteNavigation
        from apps.universities.models import University
        from apps.institutes.models import Institute
        from apps.majors.models import Major
        from apps.core.navigation import build_curated_list_with_dedup_fallback, get_navigation_slots_dict

        sections_config = [
            {
                'key': 'mega_menu_public_univ',
                'title': 'القائمة الرئيسية - الجامعات الحكومية',
                'description': 'الجامعات الحكومية الظاهرة في القائمة المنسدلة في الهيدر (8 خانات)',
                'max_slots': 8,
                'type': 'university',
                'pool': University.objects.filter(publish_status='published', university_type='public').order_by('order', 'name'),
            },
            {
                'key': 'mega_menu_private_univ',
                'title': 'القائمة الرئيسية - الجامعات الخاصة',
                'description': 'الجامعات الخاصة الظاهرة في القائمة المنسدلة في الهيدر (8 خانات)',
                'max_slots': 8,
                'type': 'university',
                'pool': University.objects.filter(publish_status='published', university_type='private').order_by('order', 'name'),
            },
            {
                'key': 'mega_menu_institute',
                'title': 'القائمة الرئيسية - معاهد اللغة',
                'description': 'معاهد اللغة الإنجليزية الظاهرة في القائمة المنسدلة في الهيدر (8 خانات)',
                'max_slots': 8,
                'type': 'institute',
                'pool': Institute.objects.filter(publish_status='published').order_by('order', 'name'),
            },
            {
                'key': 'home_featured_univ',
                'title': 'الصفحة الرئيسية - الجامعات المميزة',
                'description': 'الجامعات المعروضة في قسم النخبة بالصفحة الرئيسية (6 خانات)',
                'max_slots': 6,
                'type': 'university',
                'pool': University.objects.filter(publish_status='published').order_by('order', 'name'),
            },
            {
                'key': 'home_featured_institute',
                'title': 'الصفحة الرئيسية - المعاهد الموصى بها',
                'description': 'المعاهد المعروضة في قسم معاهد اللغة بالصفحة الرئيسية (4 خانات)',
                'max_slots': 4,
                'type': 'institute',
                'pool': Institute.objects.filter(publish_status='published').order_by('order', 'name'),
            },
            {
                'key': 'home_featured_major',
                'title': 'الصفحة الرئيسية - التخصصات الأكثر طلباً',
                'description': 'التخصصات المعروضة في قسم التخصصات بالصفحة الرئيسية (6 خانات)',
                'max_slots': 6,
                'type': 'major',
                'pool': Major.objects.filter(publish_status='published').order_by('order', 'name'),
            },
        ]

        rendered_sections = []
        for sec in sections_config:
            slots_dict = get_navigation_slots_dict(sec['key'])
            curated_list = build_curated_list_with_dedup_fallback(slots_dict, sec['pool'], sec['max_slots'])
            
            slots_data = []
            for slot_num in range(1, sec['max_slots'] + 1):
                assigned_item = slots_dict.get(slot_num)
                effective_item = curated_list[slot_num - 1] if slot_num <= len(curated_list) else None
                is_manual = bool(assigned_item and getattr(assigned_item, 'publish_status', '') == 'published')
                
                slots_data.append({
                    'slot_number': slot_num,
                    'assigned_item': assigned_item,
                    'effective_item': effective_item,
                    'is_manual': is_manual,
                })
                
            rendered_sections.append({
                'key': sec['key'],
                'title': sec['title'],
                'description': sec['description'],
                'max_slots': sec['max_slots'],
                'type': sec['type'],
                'slots': slots_data,
            })

        context['page_title'] = 'إدارة القوائم والصفحة الرئيسية'
        context['sections'] = rendered_sections
        context['all_public_univs'] = list(University.objects.filter(publish_status='published', university_type='public').order_by('name'))
        context['all_private_univs'] = list(University.objects.filter(publish_status='published', university_type='private').order_by('name'))
        context['all_institutes'] = list(Institute.objects.filter(publish_status='published').order_by('name'))
        context['all_majors'] = list(Major.objects.filter(publish_status='published').order_by('name'))
        return context

    def post(self, request, *args, **kwargs):
        from apps.core.models import SiteNavigation
        from apps.universities.models import University
        from apps.institutes.models import Institute
        from apps.majors.models import Major
        from django.core.cache import cache

        section = request.POST.get('section')
        slot_number = request.POST.get('slot_number')
        entity_type = request.POST.get('entity_type')
        entity_id = request.POST.get('entity_id')

        if not section or not slot_number:
            return JsonResponse({'success': False, 'message': 'بيانات الخانة غير كافية.'}, status=400)

        try:
            slot_number = int(slot_number)
            nav_slot, created = SiteNavigation.objects.get_or_create(
                section=section,
                slot_number=slot_number
            )

            if not entity_id or str(entity_id) in ('0', '', 'none'):
                nav_slot.university = None
                nav_slot.institute = None
                nav_slot.major = None
                nav_slot.save()
            else:
                entity_id = int(entity_id)
                if entity_type == 'university':
                    nav_slot.university = University.objects.get(pk=entity_id)
                    nav_slot.institute = None
                    nav_slot.major = None
                elif entity_type == 'institute':
                    nav_slot.institute = Institute.objects.get(pk=entity_id)
                    nav_slot.university = None
                    nav_slot.major = None
                elif entity_type == 'major':
                    nav_slot.major = Major.objects.get(pk=entity_id)
                    nav_slot.university = None
                    nav_slot.institute = None
                nav_slot.save()

            cache.delete('mega_menu_data')

            return JsonResponse({
                'success': True,
                'message': f'تم تحديث الخانة رقم {slot_number} بنجاح ✨'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'حدث خطأ: {str(e)}'}, status=400)


class SEOManagementView(SEOAdminRequiredMixin, DashboardBreadcrumbMixin, View):
    """
    View for SEO management, settings, and health overview.
    عرض إدارة وأدوات وإعدادات وصحة SEO الموحدة.
    """
    template_name = 'dashboard/seo_management.html'
    SEO_FIELDS = ['meta_title', 'meta_description', 'focus_keyword', 'og_title', 'og_description']

    def get_seo_score(self, obj):
        """Calculate SEO completion score (0-100%)."""
        filled = sum(1 for f in self.SEO_FIELDS if getattr(obj, f, ''))
        return int((filled / len(self.SEO_FIELDS)) * 100)

    def get_breadcrumbs(self):
        """Build breadcrumbs for SEO management page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('إدارة SEO')
            .build())

    def get_health_items(self, content_type):
        """Retrieve and score items for the health checklist table."""
        from django.urls import reverse
        
        model_map = {
            'universities': (University, 'جامعة', 'universities'),
            'institutes': (Institute, 'معهد', 'institutes'),
            'majors': (Major, 'تخصص', 'majors'),
            'articles': (Article, 'مقالة', 'articles'),
        }

        health_items = []

        if content_type == 'all':
            types_to_fetch = model_map.keys()
        elif content_type in model_map:
            types_to_fetch = [content_type]
        else:
            types_to_fetch = []

        for ct_key in types_to_fetch:
            model_cls, label, ct_str = model_map[ct_key]
            # Fetch published items
            items = model_cls.objects.filter(publish_status='published')
            for item in items:
                score = self.get_seo_score(item)
                
                # Resolve edit url
                edit_url = ''
                if ct_str == 'universities':
                    edit_url = reverse('dashboard:university_edit', kwargs={'pk': item.pk})
                elif ct_str == 'institutes':
                    edit_url = reverse('dashboard:institute_edit', kwargs={'pk': item.pk})
                elif ct_str == 'majors':
                    edit_url = reverse('dashboard:major_edit', kwargs={'pk': item.pk})
                elif ct_str == 'articles':
                    edit_url = reverse('dashboard:article_edit', kwargs={'pk': item.pk})

                health_items.append({
                    'obj': item,
                    'content_type': ct_str,
                    'type_label': label,
                    'score': score,
                    'score_color': 'var(--danger)' if score < 40 else 'var(--warning)' if score < 80 else 'var(--success)',
                    'edit_url': edit_url
                })

        # Sort by score (lowest first)
        health_items = sorted(health_items, key=lambda x: x['score'])
        return health_items

    def get(self, request):
        """Render the unified SEO dashboard."""
        from apps.dashboard.forms.settings import SEOSettingsForm
        
        # Get active tab from request, defaulting to 'overview'
        active_tab = request.GET.get('tab', 'overview')
        
        # Handle content type filtering for the health tab
        health_content_type = request.GET.get('content_type', 'all')
        
        # Fetch scored items for the health tab
        health_items = self.get_health_items(health_content_type)
        health_total = len(health_items)
        health_needs_attention = sum(1 for i in health_items if i['score'] < 60)

        # Get settings
        settings = SiteSettings.get_settings()

        # Instantiate forms
        form = SEOSettingsForm()
        settings_form = SiteSEOSettingsForm(instance=settings)

        # GSC API connection status
        try:
            from apps.seo.services.gsc_client import GSCClient
            gsc_api_connected = GSCClient().is_connected()
        except Exception:
            gsc_api_connected = False

        # Build context
        context = {
            'page_title': 'إدارة SEO',
            'cancel_url': reverse_lazy('dashboard:home'),
            'active_tab': active_tab,

            # Forms
            'form': form,
            'settings_form': settings_form,

            # Settings stats
            'ga4_configured': bool(settings.ga4_measurement_id),
            'ga4_measurement_id': settings.ga4_measurement_id or '',
            'gsc_api_connected': gsc_api_connected,
            'ga4_enabled': settings.enable_ga4,
            'sitemap_last_generated': settings.sitemap_last_generated,
            'sitemap_last_submitted': settings.sitemap_last_submitted,
            'sitemap_gsc_status': settings.sitemap_gsc_status,

            # Content stats
            'total_universities': University.objects.filter(publish_status='published').count(),
            'total_institutes': Institute.objects.filter(publish_status='published').count(),
            'total_majors': Major.objects.filter(publish_status='published').count(),
            'total_articles': Article.objects.filter(publish_status='published').count(),
            'total_pages': (
                University.objects.filter(publish_status='published').count() +
                Institute.objects.filter(publish_status='published').count() +
                Major.objects.filter(publish_status='published').count() +
                Article.objects.filter(publish_status='published').count() +
                3  # Home, Universities List, Majors List, Articles List
            ),

            # SEO health overview — coverage bars
            'universities_with_meta': University.objects.filter(publish_status='published').exclude(meta_title='').count(),
            'majors_with_meta': Major.objects.filter(publish_status='published').exclude(meta_title='').count(),
            'articles_with_meta': Article.objects.filter(publish_status='published').exclude(meta_title='').count(),

            # Detailed SEO health
            'health_items': health_items,
            'health_total': health_total,
            'health_needs_attention': health_needs_attention,
            'health_content_type': health_content_type,
            'health_content_type_choices': [
                ('all', 'الكل'),
                ('universities', 'الجامعات'),
                ('institutes', 'المعاهد'),
                ('majors', 'التخصصات'),
                ('articles', 'المقالات'),
            ],
        }

        return render(request, self.template_name, context)


    def post(self, request):
        """Handle POST actions for both SEO settings and tools."""
        form_type = request.POST.get('form_type', 'tools')
        settings = SiteSettings.get_settings()

        if form_type == 'settings':
            settings_form = SiteSEOSettingsForm(request.POST, instance=settings)
            if settings_form.is_valid():
                settings_form.save()
                messages.success(request, 'تم حفظ إعدادات محركات البحث (SEO) بنجاح')
                return redirect(f"{reverse_lazy('dashboard:seo_management')}?tab=settings")
            else:
                for field, errors in settings_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{settings_form.fields[field].label}: {error}')
                return redirect(f"{reverse_lazy('dashboard:seo_management')}?tab=settings")

        elif form_type == 'tools':
            from apps.dashboard.forms.settings import SEOSettingsForm
            form = SEOSettingsForm(request.POST)
            if form.is_valid():
                action = form.cleaned_data['action']
                if action == 'regenerate_sitemap':
                    result = self._regenerate_sitemap()
                elif action == 'submit_sitemap_to_google':
                    result = self._submit_sitemap_to_google()
                elif action == 'clear_seo_cache':
                    result = self._clear_seo_cache()
                elif action == 'test_ga4':
                    result = self._test_ga4_connection()
                else:
                    result = {'success': False, 'message': 'إجراء غير معروف'}

                if result['success']:
                    messages.success(request, result['message'])
                else:
                    messages.error(request, result['message'])
            else:
                messages.error(request, 'حدث خطأ في معالجة طلب الأداة')
            
            return redirect(f"{reverse_lazy('dashboard:seo_management')}?tab=overview")

        return redirect('dashboard:seo_management')

    def _regenerate_sitemap(self):
        """Regenerate sitemap.xml, update timestamp, and selectively warm cache."""
        try:
            settings = SiteSettings.get_settings()
            settings.sitemap_last_generated = timezone.now()
            settings.save(update_fields=['sitemap_last_generated'])
            
            # Clear sitemap cache
            self._clear_seo_cache()
            
            # Warm up cache selectively: warm only page 1 for each sitemap
            # to keep the dashboard response time instantaneous.
            from apps.seo.sitemaps import sitemaps
            for name, sitemap_class in sitemaps.items():
                try:
                    sitemap_instance = sitemap_class()
                    sitemap_instance.get_urls(page=1)
                except Exception as exc:
                    logger.warning("SEO: Failed to warm cache for %s: %s", name, exc)
                    
            return {
                'success': True,
                'message': 'تم تحديث خريطة الموقع وتجهيز الكاش بنجاح. يمكن الوصول إليها من: /sitemap.xml'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'فشل تحديث خريطة الموقع: {str(e)}'
            }

    def _clear_seo_cache(self):
        """Clear SEO-related cache using the centralized helper."""
        try:
            from apps.seo.sitemaps import clear_sitemap_cache
            clear_sitemap_cache()
            return {
                'success': True,
                'message': 'تم مسح ذاكرة التخزين المؤقت لـ SEO بنجاح'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'فشل مسح ذاكرة التخزين المؤقت: {str(e)}'
            }

    def _submit_sitemap_to_google(self):
        """Submit sitemap to Google Search Console via API with rate-limiting and error safety."""
        from django.core.cache import cache
        from apps.seo.services.gsc_client import GSCClient, GSCAPIError
        
        # 1. Rate Limit Check (15 minutes)
        lock_key = 'sitemap_gsc_submit_lock'
        if cache.get(lock_key):
            return {
                'success': False,
                'message': 'تم إرسال خريطة الموقع مؤخراً. يرجى الانتظار 15 دقيقة قبل المحاولة مرة أخرى لتجنب تجاوز كوتا جوجل.'
            }
            
        try:
            gsc = GSCClient()
            if not gsc.is_connected():
                settings = SiteSettings.get_settings()
                settings.sitemap_gsc_status = 'حساب الخدمة غير متصل. يرجى التحقق من ملف الاعتمادات.'
                settings.save(update_fields=['sitemap_gsc_status'])
                return {
                    'success': False,
                    'message': 'حساب خدمة Google Search Console غير متصل. يرجى التحقق من الإعدادات وملف الاعتمادات.'
                }
                
            # Submit Sitemap
            gsc.submit_sitemap()
            
            # Update settings on success
            settings = SiteSettings.get_settings()
            settings.sitemap_last_submitted = timezone.now()
            settings.sitemap_gsc_status = 'تم الإرسال بنجاح لمحرك البحث'
            settings.save(update_fields=['sitemap_last_submitted', 'sitemap_gsc_status'])
            
            # Set rate limit lock for 15 minutes (900 seconds)
            cache.set(lock_key, True, 900)
            
            return {
                'success': True,
                'message': 'تم إرسال خريطة الموقع (sitemap.xml) بنجاح إلى Google Search Console!'
            }
        except GSCAPIError as exc:
            err_msg = str(exc)
            # Parse common permission/scope errors
            if "403" in err_msg or "permission" in err_msg.lower():
                friendly_status = 'خطأ 403: صلاحيات غير كافية لحساب الخدمة في Google Search Console.'
                friendly_msg = 'فشل الإرسال: حساب خدمة جوجل لا يمتلك صلاحية كتابة (Owner/Full access) على هذه الخاصية في Search Console.'
            elif "404" in err_msg:
                friendly_status = 'خطأ 404: لم يتم العثور على موقع الخاصية في Google Search Console.'
                friendly_msg = 'فشل الإرسال: الخاصية غير مسجلة أو غير متطابقة في حساب Search Console.'
            else:
                friendly_status = f'فشل الإرسال: {err_msg[:150]}'
                friendly_msg = f'فشل إرسال خريطة الموقع لمحرك بحث جوجل: {err_msg}'
                
            settings = SiteSettings.get_settings()
            settings.sitemap_gsc_status = friendly_status
            settings.save(update_fields=['sitemap_gsc_status'])
            
            return {
                'success': False,
                'message': friendly_msg
            }
        except Exception as e:
            err_msg = str(e)
            settings = SiteSettings.get_settings()
            settings.sitemap_gsc_status = f'خطأ غير متوقع: {err_msg[:150]}'
            settings.save(update_fields=['sitemap_gsc_status'])
            return {
                'success': False,
                'message': f'حدث خطأ غير متوقع أثناء إرسال خريطة الموقع لجوجل: {err_msg}'
            }

    def _test_ga4_connection(self):
        """Test GA4 configuration."""
        try:
            settings = SiteSettings.get_settings()
            if not settings.ga4_measurement_id:
                return {
                    'success': False,
                    'message': 'لم يتم تعيين Google Analytics 4 Measurement ID في الإعدادات'
                }
            if not settings.enable_ga4:
                return {
                    'success': False,
                    'message': 'Google Analytics معطّل حالياً في الإعدادات'
                }
            if not settings.ga4_measurement_id.startswith('G-'):
                return {
                    'success': False,
                    'message': 'صيغة GA4 Measurement ID غير صحيحة. يجب أن يبدأ بـ G-'
                }
            return {
                'success': True,
                'message': f'GA4 مُعدّ بشكل صحيح: {settings.ga4_measurement_id}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في فحص GA4: {str(e)}'
            }


# ============================================================================
# Draft Preview System Views
# ============================================================================
import re
from django.db.models import Prefetch
from apps.dashboard.mixins import ContentAdminRequiredMixin
from apps.articles.views import ArticleDetailView
from apps.universities.views import UniversityDetailView
from apps.institutes.views import InstituteDetailView
from apps.majors.views import MajorDetailView

from apps.articles.models import Article
from apps.universities.models import University, Faculty, Program, UniversityFAQ
from apps.institutes.models import Institute, Course
from apps.majors.models import Major, SubjectsTable, SalaryTable, CountriesTable


class PreviewMetaAndBannerMixin:
    """
    Mixin to inject draft warning banner and robots noindex meta tags
    into the HTML response for dashboard preview views, and set noindex header.
    """
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response['X-Robots-Tag'] = 'noindex, nofollow'
        return response

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response.render()
        
        try:
            html_content = response.content.decode('utf-8', errors='replace')
            modified = False

            # 1. Inject robots noindex meta tag into the <head>
            # Match <head ...> case-insensitively
            head_pattern = re.compile(r'<head[^>]*>', re.IGNORECASE)
            head_match = head_pattern.search(html_content)
            if head_match:
                insert_pos = head_match.end()
                meta_tag = '\n    <meta name="robots" content="noindex,nofollow">'
                html_content = html_content[:insert_pos] + meta_tag + html_content[insert_pos:]
                modified = True

            # 2. Inject draft warning banner into the <body>
            # Match <body ...> case-insensitively
            body_pattern = re.compile(r'<body[^>]*>', re.IGNORECASE)
            body_match = body_pattern.search(html_content)
            if body_match:
                insert_pos = body_match.end()
                banner_html = (
                    '\n    <div class="draft-preview-banner" style="background-color: var(--secondary-light); '
                    'color: var(--secondary); text-align: center; padding: 12px 24px; font-weight: bold; '
                    'font-size: 1.1rem; border-bottom: 2px solid var(--secondary); z-index: 99999; '
                    'position: relative; font-family: var(--font-sans, sans-serif); direction: rtl;">'
                    'هذه معاينة مسودة — غير منشورة للعموم'
                    '</div>'
                )
                html_content = html_content[:insert_pos] + banner_html + html_content[insert_pos:]
                modified = True

            if modified:
                response.content = html_content.encode('utf-8')
        except Exception:
            # Fallback: return the rendered HTML response unchanged to avoid breaking the page
            pass

        return response


class PreviewArticleDetailView(ContentAdminRequiredMixin, PreviewMetaAndBannerMixin, ArticleDetailView):
    pk_url_kwarg = 'pk'
    slug_field = None
    slug_url_kwarg = None

    def get_queryset(self):
        return Article.objects.select_related(
            'category',
            'author'
        ).prefetch_related(
            'tags',
            'related_universities',
            'related_institutes',
            'related_majors'
        )


class PreviewUniversityDetailView(ContentAdminRequiredMixin, PreviewMetaAndBannerMixin, UniversityDetailView):
    pk_url_kwarg = 'pk'
    slug_field = None
    slug_url_kwarg = None

    def get_queryset(self):
        faculties_prefetch = Prefetch(
            'faculties',
            Faculty.objects.prefetch_related(
                Prefetch(
                    'programs',
                    Program.objects.all().order_by('sort_order')
                )
            ).order_by('sort_order')
        )
        faqs_prefetch = Prefetch(
            'faqs',
            UniversityFAQ.objects.all().order_by('sort_order')
        )
        return University.objects.prefetch_related(
            faculties_prefetch,
            faqs_prefetch,
            'related_majors',
            'related_articles'
        )


class PreviewInstituteDetailView(ContentAdminRequiredMixin, PreviewMetaAndBannerMixin, InstituteDetailView):
    pk_url_kwarg = 'pk'
    slug_field = None
    slug_url_kwarg = None

    def get_queryset(self):
        courses_prefetch = Prefetch(
            'courses',
            Course.objects.all().order_by('sort_order', 'id')
        )
        return Institute.objects.prefetch_related(
            courses_prefetch,
            'related_articles'
        )


class PreviewMajorDetailView(ContentAdminRequiredMixin, PreviewMetaAndBannerMixin, MajorDetailView):
    pk_url_kwarg = 'pk'
    slug_field = None
    slug_url_kwarg = None

    def get_queryset(self):
        subjects_prefetch = Prefetch(
            'subjects_tables',
            SubjectsTable.objects.all().order_by('sort_order')
        )
        salary_prefetch = Prefetch(
            'salary_tables',
            SalaryTable.objects.all().order_by('sort_order')
        )
        countries_prefetch = Prefetch(
            'countries_tables',
            CountriesTable.objects.all().order_by('sort_order')
        )
        return Major.objects.prefetch_related(
            subjects_prefetch,
            salary_prefetch,
            countries_prefetch,
            'best_universities',
            'cheap_universities',
            'related_articles'
        )


# ============================================================================
# Centralized Media Library Views
# ============================================================================
import json
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.core.models import MediaFile

class MediaLibraryView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, View):
    """
    Centralized media management page.
    صفحة إدارة الوسائط المركزية
    """
    def get(self, request):
        source = request.GET.get('source', 'all')
        missing_alt = request.GET.get('missing_alt', '') == 'true'
        search = request.GET.get('q', '')
        
        qs = MediaFile.objects.all()
        
        if source != 'all':
            qs = qs.filter(source_type=source)
        if missing_alt:
            qs = qs.filter(alt_text='')
        if search:
            qs = qs.filter(original_filename__icontains=search)
            
        paginator = Paginator(qs, 48)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Calculate stats
        total_count = MediaFile.objects.count()
        missing_alt_count = MediaFile.objects.filter(alt_text='').count()
        results_count = qs.count()
        
        context = {
            'page_obj': page_obj,
            'source': source,
            'missing_alt': missing_alt,
            'q': search,
            'total_count': total_count,
            'missing_alt_count': missing_alt_count,
            'results_count': results_count,
            'source_choices': MediaFile.SourceType.choices,
            'page_title': 'مكتبة الوسائط',
            'query_params': '&'.join([f'{k}={v}' for k, v in request.GET.items() if k != 'page']),
        }
        return render(request, 'dashboard/media/library.html', context)

    def get_breadcrumbs(self):
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('مكتبة الوسائط')
            .build())


@method_decorator(csrf_exempt, name='dispatch')
class MediaFileFindByUrlView(ContentAdminRequiredMixin, View):
    """
    AJAX view to find MediaFile by image URL.
    البحث عن ملف وسائط باستخدام رابط الصورة
    """
    def get(self, request):
        try:
            from urllib.parse import urlparse
            import os
            
            url = request.GET.get('url', '').strip()
            if not url:
                return JsonResponse({'success': False, 'error': 'URL مطلوب'}, status=400)
            
            # Parse URL to extract path
            parsed = urlparse(url)
            path = parsed.path
            
            # Remove /media/ prefix if exists
            if path.startswith('/media/'):
                path = path[7:]  # Remove '/media/'
            
            # Find MediaFile by file path
            media = MediaFile.objects.filter(file=path).first()
            
            if not media:
                return JsonResponse({'success': False, 'error': 'لم يتم العثور على الملف'}, status=404)
            
            return JsonResponse({
                'success': True,
                'media_file': {
                    'id': media.pk,
                    'file_url': media.file.url,
                    'original_filename': media.original_filename,
                    'file_size': media.file_size,
                    'width': media.width or 0,
                    'height': media.height or 0,
                    'alt_text': media.alt_text or '',
                    'caption': media.caption or '',
                    'title': media.title or '',
                    'description': media.description or '',
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class MediaFileUpdateView(ContentAdminRequiredMixin, View):
    """
    AJAX view to update alt text, caption, title, and description of a MediaFile.
    تحديث النص البديل والتسمية التوضيحية وعنوان ووصف ملف الوسائط
    """
    def post(self, request, pk):
        try:
            media = get_object_or_404(MediaFile, pk=pk)
            data = json.loads(request.body)
            
            media.alt_text = data.get('alt_text', '').strip()
            media.caption = data.get('caption', '').strip()
            media.title = data.get('title', '').strip()
            media.description = data.get('description', '').strip()
            media.save()
            
            # Sync back to the related entity (for alt_text only)
            obj = media.content_object
            if obj:
                mapping = {
                    MediaFile.SourceType.UNIVERSITY_LOGO: 'logo_alt',
                    MediaFile.SourceType.UNIVERSITY_IMAGE: 'main_image_alt',
                    MediaFile.SourceType.INSTITUTE_LOGO: 'logo_alt',
                    MediaFile.SourceType.INSTITUTE_IMAGE: 'main_image_alt',
                    MediaFile.SourceType.MAJOR_IMAGE: 'main_image_alt',
                    MediaFile.SourceType.ARTICLE_IMAGE: 'featured_image_alt',
                }
                field_name = mapping.get(media.source_type)
                if field_name and hasattr(obj, field_name):
                    setattr(obj, field_name, media.alt_text)
                    obj.save(update_fields=[field_name])
                    
            return JsonResponse({
                'success': True, 
                'alt_text': media.alt_text,
                'caption': media.caption,
                'title': media.title,
                'description': media.description
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class MediaFileDeleteView(ContentAdminRequiredMixin, View):
    """
    AJAX view to delete a MediaFile and its file from disk.
    حذف ملف وسائط من النظام والقرص
    """
    def post(self, request, pk):
        try:
            media = get_object_or_404(MediaFile, pk=pk)
            # Delete physical file
            if media.file:
                media.file.delete(save=False)
            media.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class MediaFileBulkDeleteView(ContentAdminRequiredMixin, View):
    """
    AJAX view to bulk delete MediaFiles.
    حذف جماعي لملفات وسائط من النظام والقرص
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            if not ids:
                return JsonResponse({'success': False, 'error': 'لم يتم تحديد أي ملفات لحذفها.'}, status=400)
            
            medias = MediaFile.objects.filter(pk__in=ids)
            count = 0
            for media in medias:
                if media.file:
                    media.file.delete(save=False)
                media.delete()
                count += 1
            return JsonResponse({'success': True, 'deleted_count': count})
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Error in MediaFileBulkDeleteView:")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


class TagSearchAPIView(ContentAdminRequiredMixin, View):
    """
    API view to search tags by query string.
    """
    def get(self, request, *args, **kwargs):
        q = request.GET.get('q', '').strip()
        tags = Tag.objects.all()
        if q:
            tags = tags.filter(name__icontains=q)
        
        tags_list = [{'id': tag.id, 'name': tag.name, 'slug': tag.slug} for tag in tags[:20]]
        return JsonResponse({'results': tags_list})


@method_decorator(csrf_exempt, name='dispatch')
class TagCreateAPIView(ContentAdminRequiredMixin, View):
    """
    API view to create a tag inline and return its info.
    """
    def post(self, request, *args, **kwargs):
        import re
        import json
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                name = data.get('name', '').strip()
            else:
                name = request.POST.get('name', '').strip()
        except Exception:
            name = request.POST.get('name', '').strip()
            
        if not name:
            return JsonResponse({'success': False, 'error': 'اسم الوسم مطلوب.'}, status=400)
            
        # Check if tag already exists (case-insensitive)
        tag = Tag.objects.filter(name__iexact=name).first()
        if tag:
            return JsonResponse({
                'success': True,
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug,
                'created': False
            })
            
        # Generate a unique slug
        slug_base = name.replace(' ', '-')
        slug_base = re.sub(r'[^\w\s-]', '', slug_base)
        slug_base = re.sub(r'[-\s]+', '-', slug_base)
        slug_base = slug_base.lower()
        if not slug_base:
            slug_base = 'tag'
            
        slug = slug_base
        counter = 1
        while Tag.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{counter}"
            counter += 1
            
        try:
            tag = Tag.objects.create(name=name, slug=slug)
            return JsonResponse({
                'success': True,
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug,
                'created': True
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class ContentLockAPIView(View):
    """
    API View to handle resource lock lifecycle: acquire, refresh, release, and force takeover.
    """
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

        try:
            data = json.loads(request.body)
            action = data.get('action')
            model_name = data.get('model')
            object_id = data.get('object_id')
            client_token = data.get('client_token')
            force = data.get('force', False)

            if not all([action, model_name, object_id, client_token]):
                return JsonResponse({'status': 'error', 'message': 'Missing arguments'}, status=400)

            # Resolve content type
            app_label = self._get_app_label(model_name)
            try:
                ct = ContentType.objects.get(app_label=app_label, model=model_name)
            except ContentType.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid model type'}, status=400)

            # Clean expired locks (older than 2 minutes)
            try:
                ContentLock.objects.filter(expires_at__lt=timezone.now()).delete()
            except Exception:
                pass

            # Find active lock
            lock = ContentLock.objects.filter(content_type=ct, object_id=object_id).first()
            user_profile = getattr(request.user, 'profile', None)

            if action == 'acquire':
                if lock:
                    if lock.client_token == client_token:
                        # Tab session already owns it, renew lock
                        lock.expires_at = timezone.now() + timedelta(seconds=90)
                        lock.save()
                        return JsonResponse({'status': 'success', 'locked': True, 'owned': True})
                    
                    elif force:
                        # Role priority check before force takeover
                        owner_profile = getattr(lock.user, 'profile', None)
                        can_kick = self._check_role_priority(user_profile, owner_profile)
                        
                        if can_kick:
                            lock.delete()
                            ContentLock.objects.create(
                                content_type=ct,
                                object_id=object_id,
                                user=request.user,
                                client_token=client_token,
                                expires_at=timezone.now() + timedelta(seconds=90)
                            )
                            return JsonResponse({'status': 'success', 'locked': True, 'owned': True, 'kicked_previous': True})
                        else:
                            owner_name = lock.user.get_full_name() or lock.user.username
                            return JsonResponse({
                                'status': 'insufficient_privileges',
                                'message': f'لا يمكنك طرد {owner_name} بسبب هرمية الصلاحيات.'
                            }, status=403)
                    
                    else:
                        # Locked by someone else
                        user_name = lock.user.get_full_name() or lock.user.username
                        is_same_user = (lock.user == request.user)
                        
                        # Check if current user is allowed to kick
                        owner_profile = getattr(lock.user, 'profile', None)
                        can_kick = self._check_role_priority(user_profile, owner_profile)
                        
                        return JsonResponse({
                            'status': 'locked',
                            'locked_by': user_name,
                            'is_same_user': is_same_user,
                            'can_kick': can_kick,
                            'expires_in': int((lock.expires_at - timezone.now()).total_seconds())
                        })
                else:
                    # Acquire new lock
                    ContentLock.objects.create(
                        content_type=ct,
                        object_id=object_id,
                        user=request.user,
                        client_token=client_token,
                        expires_at=timezone.now() + timedelta(seconds=90)
                    )
                    return JsonResponse({'status': 'success', 'locked': True, 'owned': True})

            elif action == 'refresh':
                if lock:
                    if lock.client_token == client_token:
                        lock.expires_at = timezone.now() + timedelta(seconds=90)
                        lock.save()
                        return JsonResponse({'status': 'success', 'refreshed': True})
                    else:
                        # Kicked by takeover or tab collision
                        user_name = lock.user.get_full_name() or lock.user.username
                        return JsonResponse({
                            'status': 'kicked', 
                            'locked_by': user_name
                        })
                else:
                    # Lock expired/deleted, try to re-acquire
                    ContentLock.objects.create(
                        content_type=ct,
                        object_id=object_id,
                        user=request.user,
                        client_token=client_token,
                        expires_at=timezone.now() + timedelta(seconds=90)
                    )
                    return JsonResponse({'status': 'success', 'reacquired': True})

            elif action == 'release':
                if lock and lock.client_token == client_token:
                    lock.delete()
                    return JsonResponse({'status': 'success', 'released': True})
                return JsonResponse({'status': 'success', 'noop': True})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def _get_app_label(self, model_name):
        mapping = {
            'university': 'universities',
            'institute': 'institutes',
            'major': 'majors',
            'article': 'articles'
        }
        return mapping.get(model_name, 'core')

    def _check_role_priority(self, user_profile, owner_profile):
        """
        Hierarchy: super_admin (3) > content_admin/seo_admin (2)
        """
        if not user_profile:
            return False
        if not owner_profile:
            return True
            
        def get_role_weight(profile):
            if profile.role == UserRole.SUPER_ADMIN:
                return 3
            return 2
            
        return get_role_weight(user_profile) >= get_role_weight(owner_profile)


# ============================================================================
# Article Duplicate & Similarity Analyzer Views
# ============================================================================
from django.views.generic import TemplateView
import re

COUNTRY_MAP = {
    "السعوديه": "saudi", "سعوديه": "saudi", "سعودي": "saudi", "المملكه العربيه السعوديه": "saudi",
    "تركيا": "turkey", "التركيه": "turkey", "تركيه": "turkey", "تركي": "turkey",
    "ماليزيا": "malaysia", "الماليزيه": "malaysia", "ماليزيه": "malaysia", "ماليزي": "malaysia",
    "مصر": "egypt", "المصريه": "egypt", "مصريه": "egypt", "مصري": "egypt",
    "المانيا": "germany", "الالمانيه": "germany", "المانيه": "germany", "الماني": "germany",
    "روسيا": "russia", "الروسيه": "russia", "روسيه": "russia", "روسي": "russia",
    "الاردن": "jordan", "الاردنيه": "jordan", "اردنيه": "jordan", "اردني": "jordan", "الاردني": "jordan",
    "الامارات": "uae", "الاماراتيه": "uae", "اماراتيه": "uae", "اماراتي": "uae",
    "قطر": "qatar", "القطريه": "qatar", "قطريه": "qatar", "قطري": "qatar",
    "البحرين": "bahrain", "البحرينيه": "bahrain", "بحرينيه": "bahrain", "بحريني": "bahrain",
    "الكويت": "kuwait", "الكويتيه": "kuwait", "كويتيه": "kuwait", "كويتي": "kuwait",
    "عمان": "oman", "العمانيه": "oman", "عمانيه": "oman", "عماني": "oman",
    "السودان": "sudan", "السودانيه": "sudan", "سودانيه": "sudan", "سوداني": "sudan",
    "اليمن": "yemen", "اليمنيه": "yemen", "يمنيه": "yemen", "يمني": "yemen",
    "العراق": "iraq", "العراقيه": "iraq", "عراقيه": "iraq", "عراقي": "iraq",
    "سوريا": "syria", "سوريه": "syria", "السوريه": "syria", "سوري": "syria",
    "لبنان": "lebanon", "اللبنانيه": "lebanon", "لبنانيه": "lebanon", "لبناني": "lebanon",
    "فلسطين": "palestine", "الفلسطينيه": "palestine", "فلسطينيه": "palestine", "فلسطيني": "palestine",
    "ليبيا": "libya", "الليبيه": "libya", "ليبيه": "libya", "ليبي": "libya",
    "تونس": "tunisia", "التونسيه": "tunisia", "تونسيه": "tunisia", "تونسي": "tunisia",
    "الجزائر": "algeria", "الجزائريه": "algeria", "جزائريه": "algeria", "جزائري": "algeria",
    "المغرب": "morocco", "المغربيه": "morocco", "مغربيه": "morocco", "مغربي": "morocco",
    "بريطانيا": "uk", "البريطانيه": "uk", "بريطانيه": "uk", "بريطاني": "uk", "المملكه المتحده": "uk",
    "امريكا": "usa", "الامريكيه": "usa", "امريكيه": "usa", "امريكي": "usa", "الولايات المتحده": "usa",
    "كندا": "canada", "الكنديه": "canada", "كنديه": "canada", "كندي": "canada",
    "استراليا": "australia", "الاستراليه": "australia", "استراليه": "australia", "استرالي": "australia",
    "اوكرانيا": "ukraine", "الاوكرانيه": "ukraine", "اوكرانيه": "ukraine", "اوكراني": "ukraine",
    "قبرص": "cyprus", "القبرصيه": "cyprus", "قبرصيه": "cyprus", "قبرصي": "cyprus",
    "جورجيا": "georgia", "الجورجيه": "georgia", "جورجيه": "georgia", "جورجي": "georgia",
    "اذربيجان": "azerbaijan", "الاذربيجانيه": "azerbaijan", "اذربيجانيه": "azerbaijan", "اذربيجاني": "azerbaijan",
    "المجر": "hungary", "المجريه": "hungary", "مجريه": "hungary", "مجري": "hungary",
    "بولندا": "poland", "البولنديه": "poland", "بولنديه": "poland", "بولندي": "poland",
    "رومانيا": "romania", "الرومانيه": "romania", "رومانيه": "romania", "روماني": "romania",
    "قيرغيزستان": "kyrgyzstan", "قيرغيزيا": "kyrgyzstan",
    "كازاخستان": "kazakhstan",
    "فرنسا": "france", "الفرنسيه": "france", "فرنسيه": "france", "فرنسي": "france",
    "ايطاليا": "italy", "الايطاليه": "italy", "ايطاليه": "italy", "ايطالي": "italy",
    "اسبانيا": "spain", "الاسبانيه": "spain", "اسبانيه": "spain", "اسباني": "spain",
    "الصين": "china", "الصينيه": "china", "صينيه": "china", "صيني": "china",
    "اليابان": "japan", "اليابانيه": "japan", "يابانيه": "japan", "ياباني": "japan",
    "الهند": "india", "الهنديه": "india", "هنديه": "india", "هندي": "india",
}

def normalize_arabic_for_countries(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    return " ".join(text.split())

def get_countries_from_title(title):
    normalized = normalize_arabic_for_countries(title)
    found_countries = set()
    
    # Check multi-word first
    multi_words = {
        "المملكه العربيه السعوديه": "saudi",
        "الولايات المتحده": "usa",
        "المملكه المتحده": "uk",
        "قبرص التركيه": "northern_cyprus",
        "شمال قبرص": "northern_cyprus",
        "سلطنه عمان": "oman",
    }
    for phrase, country in multi_words.items():
        if phrase in normalized:
            found_countries.add(country)
            normalized = normalized.replace(phrase, "")
            
    # Check single words
    words = normalized.split()
    for w in words:
        if w in COUNTRY_MAP:
            found_countries.add(COUNTRY_MAP[w])
            
    return found_countries

class ArticleSimilarityView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, TemplateView):
    """
    Scan articles and display duplicates side-by-side with recommendations.
    عرض وتحليل المقالات المتشابهة والمكررة واقتراح الحلول
    """
    template_name = 'dashboard/articles/similarity.html'

    def get_breadcrumbs(self):
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_articles')
            .current('تحليل التكرار والتشابه')
            .build())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'تحليل التكرار والتشابه للمقالات'
        
        # Ignored count and total count
        context['ignored_count'] = IgnoredSimilarity.objects.count()
        context['total_articles'] = Article.objects.count()
        
        # Ignored list
        ignored_list = IgnoredSimilarity.objects.all().select_related('article_a', 'article_b')
        context['ignored_pairs'] = ignored_list
        
        scan = self.request.GET.get('scan', '').strip() == 'true'
        if scan:
            threshold = float(self.request.GET.get('threshold', 70)) / 100.0
            mode = self.request.GET.get('mode', 'both')
            
            # Fetch all articles
            articles = list(Article.objects.all().select_related('category', 'author').prefetch_related('tags'))
            
            import re
            def clean_text(html_text):
                if not html_text:
                    return ""
                # Strip HTML tags
                text = re.sub(r'<[^>]+>', ' ', html_text)
                # Keep alphanumeric and spaces, lowercase
                text = re.sub(r'[^\w\s]', ' ', text)
                return text.lower().strip()

            def get_ngram_set(text):
                stopwords = {
                    "من", "إلى", "عن", "على", "في", "حتى", "إذ", "إذا", "أن", "أو", "ثم", 
                    "التي", "الذي", "الذين", "هذا", "هذه", "هؤلاء", "ذلك", "تلك", "كان", 
                    "يكون", "تم", "مع", "بعد", "قبل", "عند", "بين", "كل", "بعض", "غير", 
                    "لا", "ما", "لو", "لم", "لن", "إلا", "هو", "هي", "هم", "هن"
                }
                cleaned = clean_text(text)
                words = cleaned.split()
                ngrams = set()
                for w in words:
                    if w in stopwords or len(w) < 2:
                        continue
                    if len(w) < 3:
                        ngrams.add(w)
                    else:
                        for idx in range(len(w) - 2):
                            ngrams.add(w[idx:idx+3])
                return ngrams

            # Precalculate ngram sets
            article_data = []
            for art in articles:
                title_set = get_ngram_set(art.title)
                content_set = get_ngram_set(art.content)
                article_data.append({
                    'article': art,
                    'title_set': title_set,
                    'content_set': content_set,
                })
                
            # Get ignored pairs
            ignored_ids = set()
            for ip in ignored_list:
                a_id, b_id = min(ip.article_a_id, ip.article_b_id), max(ip.article_a_id, ip.article_b_id)
                ignored_ids.add((a_id, b_id))
                
            # Strength score calculator
            def calculate_strength_score(art):
                score = 0
                if art.publish_status == 'published':
                    score += 15
                word_count = len(art.content.split())
                score += min(word_count // 50, 20)  # max 20 points
                if art.featured_image:
                    score += 10
                if art.category_id:
                    score += 5
                if len(art.tags.all()) > 0:
                    score += 5
                if art.meta_title:
                    score += 5
                if art.meta_description:
                    score += 10
                if art.focus_keyword:
                    score += 5
                return score

            def calculate_jaccard(set_a, set_b):
                if not set_a or not set_b:
                    return 0.0
                return len(set_a.intersection(set_b)) / len(set_a.union(set_b))

            duplicate_pairs = []
            n = len(article_data)
            
            for i in range(n):
                for j in range(i + 1, n):
                    art_a = article_data[i]
                    art_b = article_data[j]
                    
                    pair_key = (min(art_a['article'].id, art_b['article'].id), max(art_a['article'].id, art_b['article'].id))
                    if pair_key in ignored_ids:
                        continue
                        
                    countries_a = get_countries_from_title(art_a['article'].title)
                    countries_b = get_countries_from_title(art_b['article'].title)
                    if countries_a != countries_b:
                        title_sim = 0.0
                    else:
                        title_sim = calculate_jaccard(art_a['title_set'], art_b['title_set'])
                    content_sim = calculate_jaccard(art_a['content_set'], art_b['content_set'])
                    
                    is_match = False
                    if mode == 'title':
                        is_match = title_sim >= threshold
                    elif mode == 'content':
                        is_match = content_sim >= threshold
                    elif mode == 'either':
                        is_match = title_sim >= threshold or content_sim >= threshold
                    else:  # both
                        is_match = title_sim >= threshold and content_sim >= threshold
                        
                    if is_match:
                        score_a = calculate_strength_score(art_a['article'])
                        score_b = calculate_strength_score(art_b['article'])
                        
                        if score_a >= score_b:
                            keep = art_a['article']
                            keep_score = score_a
                            delete = art_b['article']
                            delete_score = score_b
                        else:
                            keep = art_b['article']
                            keep_score = score_b
                            delete = art_a['article']
                            delete_score = score_a
                            
                        duplicate_pairs.append({
                            'article_a': art_a['article'],
                            'article_b': art_b['article'],
                            'title_similarity': round(title_sim * 100, 1),
                            'content_similarity': round(content_sim * 100, 1),
                            'keep': keep,
                            'keep_score': keep_score,
                            'delete': delete,
                            'delete_score': delete_score,
                            'word_count_a': len(art_a['article'].content.split()),
                            'word_count_b': len(art_b['article'].content.split()),
                        })
                        
            context['duplicate_pairs'] = duplicate_pairs
            context['scanned'] = True
            context['threshold_pct'] = int(threshold * 100)
            context['mode'] = mode
            
        return context


class ArticleSimilarityActionView(ContentAdminRequiredMixin, View):
    """
    AJAX handler for similarity scanner actions (ignore, restore, auto-merge, delete_only).
    التعامل مع طلبات الـ AJAX لعمليات التجاهل والدمج والحذف
    """
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        a_id = int(request.POST.get('article_a_id', 0))
        b_id = int(request.POST.get('article_b_id', 0))
        
        if not a_id or not b_id:
            return JsonResponse({'status': 'error', 'message': 'Missing article IDs.'}, status=400)
            
        article_a = get_object_or_404(Article, id=a_id)
        article_b = get_object_or_404(Article, id=b_id)
        
        low_id = min(a_id, b_id)
        high_id = max(a_id, b_id)
        
        if action == 'ignore':
            IgnoredSimilarity.objects.get_or_create(
                article_a_id=low_id,
                article_b_id=high_id
            )
            return JsonResponse({'status': 'success', 'message': 'تم تجاهل التشابه بنجاح.'})
            
        elif action == 'restore':
            IgnoredSimilarity.objects.filter(
                article_a_id=low_id,
                article_b_id=high_id
            ).delete()
            return JsonResponse({'status': 'success', 'message': 'تم إلغاء التجاهل واستعادة الثنائي.'})
            
        elif action == 'auto_merge':
            keep_id = int(request.POST.get('keep_id', 0))
            delete_id = int(request.POST.get('delete_id', 0))
            
            if not keep_id or not delete_id:
                return JsonResponse({'status': 'error', 'message': 'Missing keep/delete IDs.'}, status=400)
                
            keep_art = get_object_or_404(Article, id=keep_id)
            delete_art = get_object_or_404(Article, id=delete_id)
            
            with transaction.atomic():
                # 1. Merge FAQs (avoiding duplicates)
                keep_faqs = {faq.question: faq for faq in keep_art.faqs.all()}
                for faq in delete_art.faqs.all():
                    if faq.question not in keep_faqs:
                        faq.article = keep_art
                        faq.save()
                        
                # 2. Merge Tags
                for tag in delete_art.tags.all():
                    keep_art.tags.add(tag)
                    
                # 3. Merge related links
                for uni in delete_art.related_universities.all():
                    keep_art.related_universities.add(uni)
                for inst in delete_art.related_institutes.all():
                    keep_art.related_institutes.add(inst)
                for major in delete_art.related_majors.all():
                    keep_art.related_majors.add(major)
                    
                # 4. Create Redirects (old to new)
                old_path_standard = f"/articles/{delete_art.slug}/"
                new_path = f"/articles/{keep_art.slug}/"
                
                Redirect.objects.get_or_create(
                    old_url=old_path_standard,
                    defaults={
                        'new_url': new_path,
                        'is_active': True,
                        'notes': f"توجيه تلقائي من دمج المقالات المكررة: {delete_art.title} -> {keep_art.title}"
                    }
                )
                
                old_path_legacy = f"/{delete_art.slug}/"
                Redirect.objects.get_or_create(
                    old_url=old_path_legacy,
                    defaults={
                        'new_url': new_path,
                        'is_active': True,
                        'notes': f"توجيه تلقائي من دمج المقالات المكررة (رابط قديم): {delete_art.title} -> {keep_art.title}"
                    }
                )
                
                # 5. Delete IgnoredSimilarity entries containing deleted article
                IgnoredSimilarity.objects.filter(Q(article_a=delete_art) | Q(article_b=delete_art)).delete()
                
                # 6. Delete duplicate article
                delete_art.delete()
                
            return JsonResponse({'status': 'success', 'message': 'تم الدمج التلقائي وحذف المقالة المكررة وإنشاء التوجيهات بنجاح.'})
            
        elif action == 'delete_only':
            delete_id = int(request.POST.get('delete_id', 0))
            if not delete_id:
                return JsonResponse({'status': 'error', 'message': 'Missing delete ID.'}, status=400)
            delete_art = get_object_or_404(Article, id=delete_id)
            
            with transaction.atomic():
                IgnoredSimilarity.objects.filter(Q(article_a=delete_art) | Q(article_b=delete_art)).delete()
                delete_art.delete()
                
            return JsonResponse({'status': 'success', 'message': 'تم حذف المقالة المكررة نهائياً بدون توجيه.'})
            
        return JsonResponse({'status': 'error', 'message': 'Invalid action.'}, status=400)


class ArticleManualMergeView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, View):
    """
    Dedicated workspace for side-by-side editing and manual merging of duplicate articles.
    مساحة عمل مخصصة للمقارنة والدمج اليدوي للمقالات المكررة
    """
    template_name = 'dashboard/articles/manual_merge.html'

    def get_breadcrumbs(self, keep_art):
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .add_section('dash_articles')
            .add('تحليل التكرار والتشابه', reverse('dashboard:article_similarity'))
            .current('مساحة العمل للدمج اليدوي')
            .build())

    def get_additional_context(self, keep_art):
        recent_art_ids = Article.objects.order_by('-updated_at').values_list('id', flat=True)[:10]
        
        recently_used_universities = list(University.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_universities) < 5:
            recently_used_universities = list(University.objects.order_by('-updated_at')[:5])
        
        recently_used_institutes = list(Institute.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_institutes) < 5:
            recently_used_institutes = list(Institute.objects.order_by('-updated_at')[:5])
        
        recently_used_majors = list(Major.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_majors) < 5:
            recently_used_majors = list(Major.objects.order_by('-updated_at')[:5])
        
        recently_used_tags = list(Tag.objects.filter(articles__in=recent_art_ids).distinct()[:5])
        if len(recently_used_tags) < 5:
            recently_used_tags = list(Tag.objects.order_by('-name')[:5])
            
        return {
            'recently_used_universities': recently_used_universities,
            'recently_used_institutes': recently_used_institutes,
            'recently_used_majors': recently_used_majors,
            'recently_used_tags': recently_used_tags,
        }

    def get(self, request, keep_id, delete_id, *args, **kwargs):
        keep_art = get_object_or_404(Article, id=keep_id)
        delete_art = get_object_or_404(Article, id=delete_id)
        
        form = ArticleForm(instance=keep_art)
        faq_formset = ArticleFAQFormSet(instance=keep_art)
        
        context = {
            'page_title': 'مساحة العمل للدمج اليدوي للمقالات',
            'breadcrumbs': self.get_breadcrumbs(keep_art),
            'form': form,
            'faq_formset': faq_formset,
            'keep_art': keep_art,
            'delete_art': delete_art,
            'word_count_keep': len(keep_art.content.split()),
            'word_count_delete': len(delete_art.content.split()),
        }
        context.update(self.get_additional_context(keep_art))
        return render(request, self.template_name, context)

    def post(self, request, keep_id, delete_id, *args, **kwargs):
        keep_art = get_object_or_404(Article, id=keep_id)
        delete_art = get_object_or_404(Article, id=delete_id)
        
        form = ArticleForm(request.POST, request.FILES, instance=keep_art)
        faq_formset = ArticleFAQFormSet(request.POST, instance=keep_art)
        
        if form.is_valid() and faq_formset.is_valid():
            with transaction.atomic():
                # Save keep article edits
                keep_art = form.save()
                faq_formset.save()
                
                # Merge FAQs from delete_art to keep_art (avoiding duplicates)
                keep_faqs = {faq.question: faq for faq in keep_art.faqs.all()}
                for faq in delete_art.faqs.all():
                    if faq.question not in keep_faqs:
                        faq.article = keep_art
                        faq.save()
                        
                # Merge Tags
                for tag in delete_art.tags.all():
                    keep_art.tags.add(tag)
                    
                # Merge relations
                for uni in delete_art.related_universities.all():
                    keep_art.related_universities.add(uni)
                for inst in delete_art.related_institutes.all():
                    keep_art.related_institutes.add(inst)
                for major in delete_art.related_majors.all():
                    keep_art.related_majors.add(major)
                    
                # Create Redirects
                old_path_standard = f"/articles/{delete_art.slug}/"
                new_path = f"/articles/{keep_art.slug}/"
                
                Redirect.objects.get_or_create(
                    old_url=old_path_standard,
                    defaults={
                        'new_url': new_path,
                        'is_active': True,
                        'notes': f"توجيه تلقائي من دمج يدوي للمقالات: {delete_art.title} -> {keep_art.title}"
                    }
                )
                
                old_path_legacy = f"/{delete_art.slug}/"
                Redirect.objects.get_or_create(
                    old_url=old_path_legacy,
                    defaults={
                        'new_url': new_path,
                        'is_active': True,
                        'notes': f"توجيه تلقائي من دمج يدوي للمقالات (رابط قديم): {delete_art.title} -> {keep_art.title}"
                    }
                )
                
                # Delete ignored pairs
                IgnoredSimilarity.objects.filter(Q(article_a=delete_art) | Q(article_b=delete_art)).delete()
                
                # Delete duplicate article
                delete_art.delete()
                
            messages.success(request, 'تم الحفظ والدمج بنجاح وإنشاء التوجيهات.')
            return redirect('dashboard:article_similarity')
            
        context = {
            'page_title': 'مساحة العمل للدمج اليدوي للمقالات',
            'breadcrumbs': self.get_breadcrumbs(keep_art),
            'form': form,
            'faq_formset': faq_formset,
            'keep_art': keep_art,
            'delete_art': delete_art,
            'word_count_keep': len(keep_art.content.split()),
            'word_count_delete': len(delete_art.content.split()),
        }
        context.update(self.get_additional_context(keep_art))
        return render(request, self.template_name, context)


class LinkSearchApiView(LoginRequiredMixin, View):
    """
    API view for searching published internal entities (Universities, Institutes, Majors, Articles)
    with Arabic normalization for use in the HTML Editor link insertion modal.
    """
    def get(self, request, *args, **kwargs):
        from apps.search.utils import get_db_search_variations
        
        query_str = request.GET.get('q', '').strip()
        entity_type = request.GET.get('type', 'all').strip().lower()

        results = []
        limit_per_type = 10 if entity_type != 'all' else 5

        words = [w for w in query_str.split() if len(w) > 0]

        def build_name_filter(field_name='name'):
            if not words:
                return Q()
            q_comb = Q()
            for w in words:
                variations = get_db_search_variations(w)
                if not variations:
                    variations = [w]
                word_q = Q()
                for var in variations:
                    kw = {f'{field_name}__icontains': var}
                    word_q |= Q(**kw)
                q_comb &= word_q
            return q_comb

        # 1. Universities
        if entity_type in ('all', 'university', 'universities'):
            uni_q = Q(publish_status='published') & build_name_filter('name')
            unis = University.objects.filter(uni_q).order_by('name')[:limit_per_type]
            for u in unis:
                results.append({
                    'id': u.id,
                    'title': u.name,
                    'url': u.get_absolute_url(),
                    'type': 'university',
                    'type_label': 'جامعة'
                })

        # 2. Institutes
        if entity_type in ('all', 'institute', 'institutes'):
            inst_q = Q(publish_status='published') & build_name_filter('name')
            insts = Institute.objects.filter(inst_q).order_by('name')[:limit_per_type]
            for i in insts:
                results.append({
                    'id': i.id,
                    'title': i.name,
                    'url': i.get_absolute_url(),
                    'type': 'institute',
                    'type_label': 'معهد'
                })

        # 3. Majors
        if entity_type in ('all', 'major', 'majors'):
            maj_q = Q(publish_status='published') & build_name_filter('name')
            majs = Major.objects.filter(maj_q).order_by('name')[:limit_per_type]
            for m in majs:
                results.append({
                    'id': m.id,
                    'title': m.name,
                    'url': m.get_absolute_url(),
                    'type': 'major',
                    'type_label': 'تخصص'
                })

        # 4. Articles
        if entity_type in ('all', 'article', 'articles'):
            art_q = Q(publish_status='published') & build_name_filter('title')
            arts = Article.objects.filter(art_q).order_by('-created_at')[:limit_per_type]
            for a in arts:
                results.append({
                    'id': a.id,
                    'title': a.title,
                    'url': a.get_absolute_url(),
                    'type': 'article',
                    'type_label': 'مقال'
                })

        return JsonResponse({'success': True, 'results': results[:20]})


class ContentVersionListView(ContentAdminRequiredMixin, View):
    """
    Get list of latest 5 versions for a given model and object ID via AJAX.
    """
    def get(self, request, model_name, object_id):
        from django.apps import apps
        from apps.core.services.versioning import VersioningService

        model_map = {
            'article': 'articles.Article',
            'university': 'universities.University',
            'institute': 'institutes.Institute',
            'major': 'majors.Major'
        }

        app_model = model_map.get(model_name.lower())
        if not app_model:
            return JsonResponse({'error': 'نوع المحتوى غير مدعوم'}, status=400)

        try:
            model_cls = apps.get_model(app_model)
            instance = model_cls.objects.get(pk=object_id)
        except (LookupError, model_cls.DoesNotExist):
            return JsonResponse({'error': 'المحتوى غير موجود'}, status=404)

        versions = VersioningService.get_versions(instance)
        data = []
        for v in versions:
            user_name = (v.created_by.get_full_name() or v.created_by.username) if v.created_by else 'النظام'
            data.append({
                'id': v.id,
                'version_number': v.version_number,
                'created_at': v.created_at.strftime('%Y-%m-%d %H:%M'),
                'created_by': user_name,
                'change_reason': v.change_reason or 'نسخة سابقة'
            })
        return JsonResponse({'status': 'success', 'versions': data})


class ContentVersionDetailView(ContentAdminRequiredMixin, View):
    """
    Get version detail data snapshot via AJAX for previewing.
    """
    def get(self, request, version_id):
        from apps.core.models import ContentVersion
        try:
            version = ContentVersion.objects.select_related('created_by').get(pk=version_id)
        except ContentVersion.DoesNotExist:
            return JsonResponse({'error': 'النسخة غير موجودة'}, status=404)

        user_name = (version.created_by.get_full_name() or version.created_by.username) if version.created_by else 'النظام'

        return JsonResponse({
            'status': 'success',
            'version': {
                'id': version.id,
                'version_number': version.version_number,
                'created_at': version.created_at.strftime('%Y-%m-%d %H:%M'),
                'created_by': user_name,
                'change_reason': version.change_reason or 'نسخة سابقة',
                'data': version.data
            }
        })


class ContentVersionRestoreView(ContentAdminRequiredMixin, View):
    """
    Restore a specific version via AJAX/POST (excluding SEO and URL).
    """
    def post(self, request, version_id, *args, **kwargs):
        from apps.core.services.versioning import VersioningService
        import logging
        logger = logging.getLogger(__name__)

        try:
            restored_instance = VersioningService.restore_version(version_id, user=request.user)
            if not restored_instance:
                return JsonResponse({'error': 'فشل استرجاع النسخة: النسخة أو المحتوى غير موجود.'}, status=400)

            messages.success(request, 'تم استرجاع النسخة بنجاح (مع الاحتفاظ بإعدادات SEO والرابط الحالية).')
            return JsonResponse({
                'status': 'success',
                'message': 'تم استرجاع النسخة بنجاح.',
                'redirect_url': request.META.get('HTTP_REFERER')
            })
        except Exception as e:
            logger.error(f"Error restoring version {version_id}: {e}", exc_info=True)
            return JsonResponse({'error': f'حدث خطأ أثناء استرجاع النسخة: {str(e)}'}, status=500)











