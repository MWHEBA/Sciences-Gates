"""
Dashboard views for authentication and dashboard management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from django.urls import reverse_lazy
from datetime import timedelta
from django.db import transaction
from apps.leads.models import Lead, LeadType
from apps.redirects.models import Redirect
from apps.universities.models import University, Faculty, Program
from apps.institutes.models import Institute, Course
from apps.majors.models import Major
from apps.articles.models import Article, Category, Tag
from apps.core.models import SiteSettings
from apps.dashboard.mixins import SuperAdminRequiredMixin, SEOAdminRequiredMixin, ContentAdminRequiredMixin
from apps.dashboard.forms import (
    UserCreateForm, UserUpdateForm, RedirectForm, 
    UniversityForm, UniversityFAQFormSet, UniversityFacultyFormSet, FacultyForm, ProgramFormSet, 
    InstituteForm, CourseFormSet,
    MajorForm, SubjectsTableFormSet, SalaryTableFormSet, CountriesTableFormSet,
    ArticleForm, CategoryForm, TagForm, SiteSettingsForm
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
            return redirect('dashboard:home')
        return render(request, self.template_name)

    @method_decorator(csrf_protect)
    def post(self, request):
        """Handle login form submission."""
        from django.utils.http import url_has_allowed_host_and_scheme
        
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', request.GET.get('next', ''))

        if not username or not password:
            messages.error(request, 'يرجى إدخال اسم المستخدم وكلمة المرور')
            return render(request, self.template_name, {'next': next_url})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if user is staff (has dashboard access)
            if not user.is_staff:
                messages.error(request, 'ليس لديك صلاحيات للوصول إلى لوحة التحكم')
                return render(request, self.template_name, {'next': next_url})

            login(request, user)
            messages.success(request, f'أهلاً وسهلاً {user.first_name or user.username}')
            
            # Redirect to next URL if provided and safe, otherwise to home
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard:home')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
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


class DashboardHomeView(LoginRequiredMixin, View):
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
        
        context = {
            'page_title': 'لوحة التحكم',
            'lead_stats': lead_stats,
            'content_stats': content_stats,
            'total_pending': total_pending,
            'recent_leads': recent_leads,
            'trend': trend,
            'trend_abs': trend_abs,
            # For backward compatibility
            'total_leads': lead_stats['total'],
            'registration_leads': lead_stats['registration'],
            'contact_leads': lead_stats['contact'],
            'current_month_leads': lead_stats['this_month'],
        }
        return render(request, self.template_name, context)


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
        """Get all users ordered by username."""
        return User.objects.filter(is_staff=True).select_related('profile').order_by('username')

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إدارة المستخدمين'
        # Add items for list_page.html template
        context['items'] = context.get('users', context.get('object_list', []))
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

    def form_valid(self, form):
        """Handle successful form submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'تم إنشاء المستخدم {self.object.username} بنجاح'
        )
        return response

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إنشاء مستخدم جديد'
        return context


class UserUpdateView(SuperAdminRequiredMixin, UpdateView):
    """
    Update an existing user and their role.
    تحديث مستخدم موجود ودوره
    """
    model = User
    form_class = UserUpdateForm
    template_name = 'dashboard/users/edit.html'
    success_url = reverse_lazy('dashboard:user_list')

    def get_queryset(self):
        """Get only staff users."""
        return User.objects.filter(is_staff=True).select_related('profile')

    def form_valid(self, form):
        """Handle successful form submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'تم تحديث بيانات المستخدم {self.object.username} بنجاح'
        )
        return response

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'تحديث المستخدم: {self.object.username}'
        return context


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

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        user = self.get_object()
        username = user.username
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'تم حذف المستخدم {username} بنجاح'
        )
        return response

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'حذف المستخدم: {self.object.username}'
        return context


class RedirectListView(SEOAdminRequiredMixin, DashboardBreadcrumbMixin, ListView):
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
        
        # Search by old_url or new_url
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(old_url__icontains=search_query) |
                Q(new_url__icontains=search_query)
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
        # Add items for list_page.html template
        context['items'] = context.get('redirects', context.get('object_list', []))
        return context


class RedirectCreateView(SEOAdminRequiredMixin, CreateView):
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


class RedirectUpdateView(SEOAdminRequiredMixin, UpdateView):
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


class RedirectDeleteView(SEOAdminRequiredMixin, DeleteView):
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
        ).order_by('-created_at')
        
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
        
        # Filter by university_type
        type_filter = self.request.GET.get('type', '').strip()
        if type_filter in ['public', 'private']:
            queryset = queryset.filter(university_type=type_filter)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title and search/filter info to context."""
        from django.urls import reverse
        
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إدارة الجامعات'
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['type_filter'] = self.request.GET.get('type', '')
        
        # Add items for list_page.html template
        # context_object_name is 'universities', but list_page.html expects 'items'
        context['items'] = context.get('universities', context.get('object_list', []))
        
        # Add required context variables for list_page.html
        context['search_placeholder'] = 'ابحث عن اسم الجامعة...'
        context['search_value'] = context['search_query']
        context['base_url'] = reverse('dashboard:university_list')
        
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
        ]
        
        # Columns for data table
        context['columns'] = [
            {'label': 'اسم الجامعة', 'key': 'name', 'type': 'link', 'link_url_name': 'dashboard:university_edit', 'link_param': 'pk'},
            {'label': 'النوع', 'key': 'university_type_display', 'type': 'text'},
            {'label': 'الكليات', 'key': 'faculties_count', 'type': 'text'},
            {'label': 'الحالة', 'key': 'publish_status', 'type': 'status_badge'},
            {'label': 'التاريخ', 'key': 'created_at', 'type': 'date'},
        ]
        
        context['edit_url_name'] = 'dashboard:university_edit'
        context['delete_url_name'] = 'dashboard:university_delete'
        
        # Pagination info
        context['is_paginated'] = self.paginator.num_pages > 1 if hasattr(self, 'paginator') else False
        context['page_obj'] = context.get('page_obj')
        
        # Build query params for pagination
        query_params = '&'.join([f'{k}={v}' for k, v in self.request.GET.items() if k != 'page'])
        context['query_params'] = query_params
        
        # Add computed properties to each university
        for university in context['items']:
            university.faculties_count = university.faculties.count()
            university.university_type_display = university.get_university_type_display()
            university.publish_status_display = university.get_publish_status_display()
        
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
        
        if self.request.POST:
            context['faq_formset'] = UniversityFAQFormSet(self.request.POST, instance=self.object)
            context['faculty_formset'] = UniversityFacultyFormSet(self.request.POST, instance=self.object)
        else:
            context['faq_formset'] = UniversityFAQFormSet(instance=self.object)
            context['faculty_formset'] = UniversityFacultyFormSet(instance=self.object)
        
        # Attach nested program formsets to each faculty form
        context['faculty_formset'] = self._attach_program_formsets(
            context['faculty_formset'],
            self.request.POST if self.request.POST else None
        )
        
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
        
        import logging
        logger = logging.getLogger(__name__)
        
        # التحقق من صحة كل الـ formsets قبل أي حفظ
        all_valid = faq_formset.is_valid() and faculty_formset.is_valid()
        
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
            
            for field, errors in faq_formset.errors.items():
                for error in errors:
                    messages.error(self.request, f'خطأ في الأسئلة الشائعة: {error}')
            
            for field, errors in faculty_formset.errors.items():
                for error in errors:
                    messages.error(self.request, f'خطأ في الكليات: {error}')
            
            for faculty_form in faculty_formset:
                if hasattr(faculty_form, 'program_formset'):
                    for field, errors in faculty_form.program_formset.errors.items():
                        for error in errors:
                            messages.error(self.request, f'خطأ في البرامج: {error}')
            
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Form errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)


class UniversityUpdateView(ContentAdminRequiredMixin, DashboardBreadcrumbMixin, UpdateView):
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
        
        if self.request.POST:
            context['faq_formset'] = UniversityFAQFormSet(self.request.POST, instance=self.object)
            context['faculty_formset'] = UniversityFacultyFormSet(self.request.POST, instance=self.object)
        else:
            context['faq_formset'] = UniversityFAQFormSet(instance=self.object)
            context['faculty_formset'] = UniversityFacultyFormSet(instance=self.object)
        
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
        
        import logging
        logger = logging.getLogger(__name__)
        
        # التحقق من صحة كل الـ formsets قبل أي حفظ
        all_valid = faq_formset.is_valid() and faculty_formset.is_valid()
        
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
                    
                    # إنشاء redirect لو الـ slug اتغير
                    new_slug = form.cleaned_data.get('slug')
                    if old_slug != new_slug and self.object.is_published:
                        create_redirect = self.request.POST.get('create_redirect') == 'on'
                        if create_redirect:
                            old_url = f'/universities/{old_slug}/'
                            new_url = f'/universities/{new_slug}/'
                            Redirect.objects.update_or_create(
                                old_url=old_url,
                                defaults={
                                    'new_url': new_url,
                                    'is_active': True,
                                    'notes': f'تم إنشاؤه تلقائياً عند تغيير رابط الجامعة: {self.object.name}'
                                }
                            )
                            messages.success(
                                self.request,
                                f'تم تحديث الجامعة وإنشاء إعادة توجيه من {old_url} إلى {new_url} بنجاح'
                            )
                        else:
                            messages.warning(
                                self.request,
                                f'تم تحديث الجامعة، لكن لم يتم إنشاء إعادة توجيه للرابط القديم'
                            )
                    else:
                        messages.success(
                            self.request,
                            f'تم تحديث الجامعة "{self.object.name}" بنجاح'
                        )
                
                return redirect(self.success_url)
            except Exception as e:
                logger.error(f"Error updating university: {e}")
                messages.error(self.request, 'حدث خطأ أثناء تحديث الجامعة. لم يتم حفظ أي تغييرات.')
                return self.form_invalid(form)
        else:
            # عرض الأخطاء بدون حفظ أي شيء
            logger.debug(f"FAQ Formset errors: {faq_formset.errors}")
            logger.debug(f"Faculty Formset errors: {faculty_formset.errors}")
            
            for field, errors in faq_formset.errors.items():
                for error in errors:
                    messages.error(self.request, f'خطأ في الأسئلة الشائعة: {error}')
            
            for field, errors in faculty_formset.errors.items():
                for error in errors:
                    messages.error(self.request, f'خطأ في الكليات: {error}')
            
            for faculty_form in faculty_formset:
                if hasattr(faculty_form, 'program_formset'):
                    for field, errors in faculty_form.program_formset.errors.items():
                        for error in errors:
                            messages.error(self.request, f'خطأ في البرامج: {error}')
            
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
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
        ).order_by('-created_at')
        
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
        
        # Filter by institute_type
        type_filter = self.request.GET.get('type', '').strip()
        if type_filter in ['language', 'academic']:
            queryset = queryset.filter(institute_type=type_filter)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title and search/filter info to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إدارة المعاهد'
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['type_filter'] = self.request.GET.get('type', '')
        # Add items for list_page.html template
        context['items'] = context.get('institutes', context.get('object_list', []))
        return context
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class InstituteCreateView(ContentAdminRequiredMixin, CreateView):
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
    template_name = 'dashboard/institutes/create.html'

    def get_context_data(self, **kwargs):
        """Add formset to context."""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['course_formset'] = CourseFormSet(self.request.POST, instance=self.object)
        else:
            context['course_formset'] = CourseFormSet(instance=self.object)
        context['page_title'] = 'إنشاء معهد جديد'
        return context

    def form_valid(self, form):
        """Handle successful form submission with formset.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        context = self.get_context_data()
        course_formset = context['course_formset']
        
        if course_formset.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save()
                    course_formset.instance = self.object
                    course_formset.save()
                
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
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)


class InstituteUpdateView(ContentAdminRequiredMixin, UpdateView):
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
    template_name = 'dashboard/institutes/edit.html'
    success_url = reverse_lazy('dashboard:institute_list')

    def get_context_data(self, **kwargs):
        """Add formset and courses to context."""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['course_formset'] = CourseFormSet(self.request.POST, instance=self.object)
        else:
            context['course_formset'] = CourseFormSet(instance=self.object)
        
        # Add courses list
        context['courses'] = self.object.courses.all().order_by('name')
        context['page_title'] = f'تحديث المعهد: {self.object.name}'
        
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
        
        if course_formset.is_valid():
            try:
                with transaction.atomic():
                    # حفظ الـ slug القديم قبل الحفظ
                    old_slug = self.object.slug
                    
                    self.object = form.save()
                    course_formset.instance = self.object
                    course_formset.save()
                    
                    # إنشاء redirect لو الـ slug اتغير
                    new_slug = form.cleaned_data.get('slug')
                    if old_slug != new_slug and self.object.is_published:
                        create_redirect = self.request.POST.get('create_redirect') == 'on'
                        if create_redirect:
                            old_url = f'/institutes/{old_slug}/'
                            new_url = f'/institutes/{new_slug}/'
                            Redirect.objects.update_or_create(
                                old_url=old_url,
                                defaults={
                                    'new_url': new_url,
                                    'is_active': True,
                                    'notes': f'تم إنشاؤه تلقائياً عند تغيير رابط المعهد: {self.object.name}'
                                }
                            )
                            messages.success(
                                self.request,
                                f'تم تحديث المعهد وإنشاء إعادة توجيه من {old_url} إلى {new_url} بنجاح'
                            )
                        else:
                            messages.warning(
                                self.request,
                                f'تم تحديث المعهد، لكن لم يتم إنشاء إعادة توجيه للرابط القديم'
                            )
                    else:
                        messages.success(
                            self.request,
                            f'تم تحديث المعهد "{self.object.name}" بنجاح'
                        )
                
                return redirect(self.success_url)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error updating institute: {e}")
                messages.error(self.request, 'حدث خطأ أثناء تحديث المعهد. لم يتم حفظ أي تغييرات.')
                return self.form_invalid(form)
        else:
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
        queryset = Major.objects.all().prefetch_related(
            'subjects_tables', 'salary_tables', 'countries_tables',
            'best_universities', 'cheap_universities', 'related_articles'
        ).order_by('-created_at')
        
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
        
        # Filter by major_category
        category_filter = self.request.GET.get('category', '').strip()
        if category_filter in ['medical', 'engineering', 'cs', 'business', 'science', 'other']:
            queryset = queryset.filter(major_category=category_filter)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title and search/filter info to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إدارة التخصصات'
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['category_filter'] = self.request.GET.get('category', '')
        # Add items for list_page.html template
        context['items'] = context.get('majors', context.get('object_list', []))
        return context


class MajorCreateView(ContentAdminRequiredMixin, CreateView):
    """
    Create a new major with all three inline formsets.
    إنشاء تخصص جديد مع نماذج الجداول الديناميكية الثلاثة المدمجة
    
    Features:
    - Create major with all fields
    - Add subjects table entries inline
    - Add salary table entries inline
    - Add countries table entries inline
    - Arabic success message
    - Redirect to edit page after creation
    """
    model = Major
    form_class = MajorForm
    template_name = 'dashboard/majors/create.html'

    def get_context_data(self, **kwargs):
        """Add formsets to context."""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['subjects_formset'] = SubjectsTableFormSet(self.request.POST, instance=self.object)
            context['salary_formset'] = SalaryTableFormSet(self.request.POST, instance=self.object)
            context['countries_formset'] = CountriesTableFormSet(self.request.POST, instance=self.object)
        else:
            context['subjects_formset'] = SubjectsTableFormSet(instance=self.object)
            context['salary_formset'] = SalaryTableFormSet(instance=self.object)
            context['countries_formset'] = CountriesTableFormSet(instance=self.object)
        context['page_title'] = 'إنشاء تخصص جديد'
        return context

    def form_valid(self, form):
        """Handle successful form submission with formsets.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        context = self.get_context_data()
        subjects_formset = context['subjects_formset']
        salary_formset = context['salary_formset']
        countries_formset = context['countries_formset']
        
        if (subjects_formset.is_valid() and salary_formset.is_valid() and 
            countries_formset.is_valid()):
            try:
                with transaction.atomic():
                    self.object = form.save()
                    
                    subjects_formset.instance = self.object
                    subjects_formset.save()
                    
                    salary_formset.instance = self.object
                    salary_formset.save()
                    
                    countries_formset.instance = self.object
                    countries_formset.save()
                
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


class MajorUpdateView(ContentAdminRequiredMixin, UpdateView):
    """
    Update an existing major with all three inline formsets.
    تحديث تخصص موجود مع نماذج الجداول الديناميكية الثلاثة المدمجة
    
    Features:
    - Edit all major fields
    - Edit subjects table entries inline
    - Edit salary table entries inline
    - Edit countries table entries inline
    - Show slug change warning if slug was modified
    - Offer to create redirect for old slug
    - Arabic success message
    """
    model = Major
    form_class = MajorForm
    template_name = 'dashboard/majors/edit.html'
    success_url = reverse_lazy('dashboard:major_list')

    def get_context_data(self, **kwargs):
        """Add formsets to context."""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['subjects_formset'] = SubjectsTableFormSet(self.request.POST, instance=self.object)
            context['salary_formset'] = SalaryTableFormSet(self.request.POST, instance=self.object)
            context['countries_formset'] = CountriesTableFormSet(self.request.POST, instance=self.object)
        else:
            context['subjects_formset'] = SubjectsTableFormSet(instance=self.object)
            context['salary_formset'] = SalaryTableFormSet(instance=self.object)
            context['countries_formset'] = CountriesTableFormSet(instance=self.object)
        
        context['page_title'] = f'تحديث التخصص: {self.object.name}'
        
        # Check if slug was changed and show warning
        if hasattr(self.object, '_old_slug'):
            context['slug_changed'] = True
            context['old_slug'] = self.object._old_slug
        
        return context

    def form_valid(self, form):
        """Handle successful form submission with formsets.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        context = self.get_context_data()
        subjects_formset = context['subjects_formset']
        salary_formset = context['salary_formset']
        countries_formset = context['countries_formset']
        
        if (subjects_formset.is_valid() and salary_formset.is_valid() and 
            countries_formset.is_valid()):
            try:
                with transaction.atomic():
                    # حفظ الـ slug القديم قبل الحفظ
                    old_slug = self.object.slug
                    
                    self.object = form.save()
                    
                    subjects_formset.instance = self.object
                    subjects_formset.save()
                    
                    salary_formset.instance = self.object
                    salary_formset.save()
                    
                    countries_formset.instance = self.object
                    countries_formset.save()
                    
                    # إنشاء redirect لو الـ slug اتغير
                    new_slug = form.cleaned_data.get('slug')
                    if old_slug != new_slug and self.object.is_published:
                        create_redirect = self.request.POST.get('create_redirect') == 'on'
                        if create_redirect:
                            old_url = f'/majors/{old_slug}/'
                            new_url = f'/majors/{new_slug}/'
                            Redirect.objects.update_or_create(
                                old_url=old_url,
                                defaults={
                                    'new_url': new_url,
                                    'is_active': True,
                                    'notes': f'تم إنشاؤه تلقائياً عند تغيير رابط التخصص: {self.object.name}'
                                }
                            )
                            messages.success(
                                self.request,
                                f'تم تحديث التخصص وإنشاء إعادة توجيه من {old_url} إلى {new_url} بنجاح'
                            )
                        else:
                            messages.warning(
                                self.request,
                                f'تم تحديث التخصص، لكن لم يتم إنشاء إعادة توجيه للرابط القديم'
                            )
                    else:
                        messages.success(
                            self.request,
                            f'تم تحديث التخصص "{self.object.name}" بنجاح'
                        )
                
                return redirect(self.success_url)
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
    List all article tags with search filter.
    عرض قائمة بجميع وسوم المقالات مع البحث
    
    Features:
    - Search by name and slug
    - Display article count for each tag
    - Pagination (20 per page)
    - Edit and delete options for each tag
    """
    model = Tag
    template_name = 'dashboard/tags/list.html'
    context_object_name = 'tags'
    paginate_by = 20

    def get_breadcrumbs(self):
        """Build breadcrumb trail for tag list page."""
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('وسوم المقالات')
            .build())

    def get_queryset(self):
        """Get tags with optional search."""
        from django.db.models import Count
        queryset = Tag.objects.all().annotate(articles_count=Count('articles')).order_by('name')
        
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
        context['page_title'] = 'إدارة وسوم المقالات'
        context['page_description'] = 'إدارة جميع وسوم المقالات'
        context['search_query'] = self.request.GET.get('search', '')
        context['base_url'] = reverse_lazy('dashboard:tag_list')
        context['search_placeholder'] = 'ابحث عن اسم الوسم أو الرابط...'
        context['empty_state_icon'] = '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path></svg>'
        
        # Action button for topbar
        context['action_buttons'] = [
            {
                'url': reverse_lazy('dashboard:tag_create'),
                'label': 'إضافة وسم جديد',
                'variant': 'primary',
            }
        ]
        
        # Columns definition
        context['columns'] = [
            {'label': 'اسم الوسم', 'key': 'name', 'type': 'link', 'link_url_name': 'dashboard:tag_edit', 'link_param': 'id'},
            {'label': 'الرابط', 'key': 'slug', 'type': 'text'},
            {'label': 'عدد المقالات', 'key': 'articles_count', 'type': 'text'},
        ]
        
        context['edit_url_name'] = 'dashboard:tag_edit'
        context['delete_url_name'] = 'dashboard:tag_delete'
        
        # Add items for list_page.html template
        context['items'] = context.get('tags', context.get('object_list', []))
        context['query_params'] = '&'.join([f'{k}={v}' for k, v in self.request.GET.items() if k != 'page'])
        return context


class TagCreateView(ContentAdminRequiredMixin, CreateView):
    """
    Create a new article tag via modal/redirect.
    """
    model = Tag
    form_class = TagForm
    success_url = reverse_lazy('dashboard:tag_list')

    def get(self, request, *args, **kwargs):
        """Redirect GET requests to list page since creation is done via modal."""
        return redirect(self.success_url)

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
        return redirect(self.success_url)

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
        return redirect(self.success_url)


class TagUpdateView(ContentAdminRequiredMixin, UpdateView):
    """
    Update an existing article tag.
    """
    model = Tag
    form_class = TagForm
    success_url = reverse_lazy('dashboard:tag_list')

    def get(self, request, *args, **kwargs):
        """Return JSON for AJAX modal populating, redirect to list page otherwise."""
        self.object = self.get_object()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('json') == '1':
            return JsonResponse({
                'id': self.object.id,
                'name': self.object.name,
                'slug': self.object.slug,
            })
        return redirect(self.success_url)

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
        return redirect(self.success_url)


class TagDeleteView(ContentAdminRequiredMixin, DeleteView):
    """
    Delete an article tag with confirmation.
    حذف وسم مقالات مع تأكيد
    
    Features:
    - Confirmation page showing tag name and article count
    - Arabic success message
    - Note about articles that will be affected
    """
    model = Tag
    template_name = 'dashboard/tags/delete_confirm.html'
    success_url = reverse_lazy('dashboard:tag_list')

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
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title, search/filter info, and categories to context."""
        from django.urls import reverse
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إدارة المقالات'
        context['search_query'] = self.request.GET.get('search', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['categories'] = Category.objects.all().order_by('name')
        
        # Add items for list_page.html/data_table template
        context['items'] = context.get('articles', context.get('object_list', []))
        
        # Add required context variables for filter_bar.html
        context['search_placeholder'] = 'ابحث عن عنوان المقالة أو الرابط...'
        context['search_value'] = context['search_query']
        context['base_url'] = reverse('dashboard:article_list')
        context['add_new_url'] = reverse('dashboard:article_create')
        
        # Filters
        category_options = [{'value': '', 'label': 'كل التصنيفات'}]
        for cat in context['categories']:
            category_options.append({'value': str(cat.id), 'label': cat.name})
            
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
        ]
        
        # Columns for data table
        context['columns'] = [
            {'label': 'العنوان', 'key': 'title', 'type': 'link', 'link_url_name': 'dashboard:article_edit', 'link_param': 'pk'},
            {'label': 'التصنيف', 'key': 'category_name', 'type': 'text'},
            {'label': 'الكاتب', 'key': 'author_name', 'type': 'text'},
            {'label': 'الحالة', 'key': 'publish_status', 'type': 'status_badge'},
            {'label': 'تاريخ النشر', 'key': 'publish_date', 'type': 'date'},
        ]
        
        context['edit_url_name'] = 'dashboard:article_edit'
        context['delete_url_name'] = 'dashboard:article_delete'
        
        # Pagination info
        context['is_paginated'] = self.paginator.num_pages > 1 if hasattr(self, 'paginator') else False
        context['page_obj'] = context.get('page_obj')
        
        # Build query params for pagination
        query_params = '&'.join([f'{k}={v}' for k, v in self.request.GET.items() if k != 'page'])
        context['query_params'] = query_params
        
        # Add computed properties to each article
        for article in context['items']:
            article.category_name = article.category.name if article.category else 'بدون تصنيف'
            article.author_name = article.author.get_full_name() or article.author.username if article.author else 'غير معروف'
            
        return context


class ArticleCreateView(ContentAdminRequiredMixin, CreateView):
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

    def form_valid(self, form):
        """Handle successful form submission.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        try:
            with transaction.atomic():
                # Set author to current user
                self.object = form.save(commit=False)
                self.object.author = self.request.user
                
                # Sanitize HTML content before saving
                from apps.html_editor.sanitizer import sanitize_article_html
                self.object.content = sanitize_article_html(self.object.content)
                
                self.object.save()
                form.save_m2m()  # Save many-to-many relationships
            
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

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'إنشاء مقالة جديدة'
        return context


class ArticleUpdateView(ContentAdminRequiredMixin, UpdateView):
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

    def get_context_data(self, **kwargs):
        """Add page title and slug change warning to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'تحديث المقالة: {self.object.title}'
        
        # Check if slug was changed and show warning
        if hasattr(self.object, '_old_slug'):
            context['slug_changed'] = True
            context['old_slug'] = self.object._old_slug
        
        return context

    def form_valid(self, form):
        """Handle successful form submission.
        كل عمليات الحفظ داخل transaction — لو أي حاجة فشلت، كل شيء يترجع
        """
        try:
            with transaction.atomic():
                # حفظ الـ slug القديم قبل الحفظ
                old_slug = self.object.slug
                
                # Sanitize HTML content before saving
                from apps.html_editor.sanitizer import sanitize_article_html
                self.object = form.save(commit=False)
                self.object.content = sanitize_article_html(self.object.content)
                self.object.save()
                form.save_m2m()  # Save many-to-many relationships
                
                # إنشاء redirect لو الـ slug اتغير
                new_slug = form.cleaned_data.get('slug')
                if old_slug != new_slug and self.object.is_published:
                    create_redirect = self.request.POST.get('create_redirect') == 'on'
                    if create_redirect:
                        old_url = f'/articles/{old_slug}/'
                        new_url = f'/articles/{new_slug}/'
                        Redirect.objects.update_or_create(
                            old_url=old_url,
                            defaults={
                                'new_url': new_url,
                                'is_active': True,
                                'notes': f'تم إنشاؤه تلقائياً عند تغيير رابط المقالة: {self.object.title}'
                            }
                        )
                        messages.success(
                            self.request,
                            f'تم تحديث المقالة وإنشاء إعادة توجيه من {old_url} إلى {new_url} بنجاح'
                        )
                    else:
                        messages.warning(
                            self.request,
                            f'تم تحديث المقالة، لكن لم يتم إنشاء إعادة توجيه للرابط القديم'
                        )
                else:
                    messages.success(
                        self.request,
                        f'تم تحديث المقالة "{self.object.title}" بنجاح'
                    )
            
            return redirect(self.success_url)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error updating article: {e}")
            messages.error(self.request, 'حدث خطأ أثناء تحديث المقالة. لم يتم حفظ أي تغييرات.')
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
        return (BreadcrumbTrail()
            .add_section('dashboard')
            .current('الرسائل')
            .build())

    def get_queryset(self):
        """Get leads with optional filtering."""
        queryset = Lead.objects.all().order_by('-created_at')
        
        # Filter by lead_type
        lead_type_filter = self.request.GET.get('lead_type', '').strip()
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
        
        # Search by name, email, or phone
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        
        # Filter by read status
        read_status = self.request.GET.get('read_status', '').strip()
        if read_status == 'read':
            queryset = queryset.filter(is_read=True)
        elif read_status == 'unread':
            queryset = queryset.filter(is_read=False)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add page title, filters, and statistics to context."""
        context = super().get_context_data(**kwargs)
        
        # Add page title
        context['page_title'] = 'إدارة الرسائل والاستفسارات'
        
        # Add filter values for form
        context['lead_type_filter'] = self.request.GET.get('lead_type', '')
        context['from_date'] = self.request.GET.get('from_date', '')
        context['to_date'] = self.request.GET.get('to_date', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['read_status'] = self.request.GET.get('read_status', '')
        
        # Add lead type choices
        context['lead_types'] = LeadType.choices
        
        # Add unread count
        context['unread_count'] = Lead.objects.filter(is_read=False).count()
        
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
        
        context['export_url'] = f'?{"&".join(query_params)}' if query_params else ''
        
        # Add items for list_page.html template
        context['items'] = context.get('leads', context.get('object_list', []))
        
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
        lead_type_filter = request.GET.get('lead_type', '').strip()
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
                Q(phone__icontains=search_query)
            )
        
        read_status = request.GET.get('read_status', '').strip()
        if read_status == 'read':
            queryset = queryset.filter(is_read=True)
        elif read_status == 'unread':
            queryset = queryset.filter(is_read=False)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Add BOM for proper UTF-8 encoding in Excel
        response.write('\ufeff')
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header row in Arabic
        writer.writerow([
            'الاسم',
            'البريد الإلكتروني',
            'رقم الهاتف',
            'نوع الرسالة',
            'الرسالة',
            'صفحة المصدر',
            'المرجع',
            'UTM Source',
            'UTM Medium',
            'UTM Campaign',
            'UTM Term',
            'UTM Content',
            'تاريخ الإرسال',
            'تم قراءتها',
            'الملاحظات',
        ])
        
        # Write data rows
        for lead in queryset:
            writer.writerow([
                lead.name,
                lead.email,
                lead.phone,
                lead.get_lead_type_display(),
                lead.message,
                lead.source_page,
                lead.referrer,
                lead.utm_source,
                lead.utm_medium,
                lead.utm_campaign,
                lead.utm_term,
                lead.utm_content,
                lead.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'نعم' if lead.is_read else 'لا',
                lead.notes,
            ])
        
        messages.success(
            request,
            f'تم تصدير {queryset.count()} رسالة بنجاح'
        )
        
        return response


# ============================================================================
# SEO Management Views
# ============================================================================

class SEOOverviewView(SEOAdminRequiredMixin, View):
    """
    SEO overview — shows all published content with SEO field completion scores.
    صفحة نظرة عامة على SEO لجميع أنواع المحتوى المنشور.
    
    Features:
    - Display all published content (Universities, Institutes, Majors, Articles)
    - Calculate SEO completion score for each item (0-100%)
    - Show which SEO fields are filled: meta_title, meta_description, focus_keyword, og_title, og_description
    - Filter by content type
    - Sort by SEO score (lowest first - needs attention)
    - Display visual progress bar for each item
    - Color-coded scores: Red (<40%), Yellow (40-80%), Green (≥80%)
    - Link to edit page for each item
    
    Requirements: 7
    """
    template_name = 'dashboard/seo/overview.html'
    
    SEO_FIELDS = ['meta_title', 'meta_description', 'focus_keyword', 'og_title', 'og_description']
    
    def get_seo_score(self, obj):
        """Calculate SEO completion score (0-100%)."""
        filled = sum(1 for f in self.SEO_FIELDS if getattr(obj, f, ''))
        return int((filled / len(self.SEO_FIELDS)) * 100)
    
    def get(self, request):
        """Display SEO overview."""
        content_type = request.GET.get('type', 'universities')
        
        model_map = {
            'universities': University,
            'institutes': Institute,
            'majors': Major,
            'articles': Article,
        }
        
        model = model_map.get(content_type, University)
        items = model.objects.filter(publish_status='published')
        
        # Calculate SEO scores
        items_with_score = []
        for item in items:
            score = self.get_seo_score(item)
            items_with_score.append({
                'obj': item,
                'score': score,
                'score_color': 'var(--danger)' if score < 40 else 'var(--warning)' if score < 80 else 'var(--success)',
            })
        
        # Sort by score (lowest first)
        items_with_score = sorted(items_with_score, key=lambda x: x['score'])
        
        context = {
            'page_title': 'نظرة عامة على SEO',
            'content_type': content_type,
            'items': items_with_score,
            'total': len(items_with_score),
            'needs_attention': sum(1 for i in items_with_score if i['score'] < 60),
            'content_types': [
                {'value': 'universities', 'label': 'الجامعات'},
                {'value': 'institutes', 'label': 'المعاهد'},
                {'value': 'majors', 'label': 'التخصصات'},
                {'value': 'articles', 'label': 'المقالات'},
            ],
        }
        
        return render(request, self.template_name, context)


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

        # Convert to RGB if necessary (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img

        # Save optimized image
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'editor/{request.user.id}/{timestamp}_{image_file.name.split(".")[0]}.jpg'

        # Save to storage
        path = default_storage.save(filename, ContentFile(output.getvalue()))
        url = default_storage.url(path)

        return JsonResponse({
            'success': True,
            'url': url,
            'filename': os.path.basename(path),
            'size': {
                'width': img.width,
                'height': img.height,
            }
        })

    except Exception as e:
        return JsonResponse({'error': f'خطأ في الرفع: {str(e)}'}, status=500)


class EditorImageUploadView(LoginRequiredMixin, View):
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

    def form_valid(self, form):
        """Add success message upon successful saving."""
        response = super().form_valid(form)
        messages.success(self.request, 'تم حفظ الإعدادات العامة بنجاح')
        return response

    def get_context_data(self, **kwargs):
        """Add custom variables for page rendering."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'الإعدادات العامة للموقع'
        context['cancel_url'] = reverse_lazy('dashboard:home')
        return context

