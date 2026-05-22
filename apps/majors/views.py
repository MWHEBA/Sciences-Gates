"""
Public views for displaying major content to end users.
"""
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Prefetch
from django.core.paginator import Paginator
from .models import Major, SubjectsTable, SalaryTable, CountriesTable
from apps.seo.mixins import BreadcrumbMixin
from apps.seo.breadcrumbs import BreadcrumbTrail


class MajorListView(ListView):
    """
    Display a paginated list of published majors.
    
    Implements pagination with 20 items per page.
    Optimizes queries using select_related for foreign keys.
    """
    model = Major
    template_name = 'majors/list.html'
    context_object_name = 'majors'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Return only published majors, ordered by name.
        
        Query Optimization:
        - Uses prefetch_related for many-to-many relationships
        """
        return Major.objects.filter(
            publish_status='published'
        ).prefetch_related(
            'best_universities',
            'cheap_universities',
            'related_articles'
        ).order_by('name')


class MajorDetailView(BreadcrumbMixin, DetailView):
    """
    Display detailed information about a specific major.
    
    Includes:
    - Major basic information (name, main image, description, study duration)
    - Quick information (tuition fees, study language, practical training, career opportunities)
    - Why study this major section
    - Best universities and cheap universities
    - Dynamic tables (subjects, salary, countries)
    - How to apply section
    
    Optimizes queries using select_related and prefetch_related to avoid N+1 problems.
    """
    model = Major
    template_name = 'majors/detail.html'
    context_object_name = 'major'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Return only published majors with optimized queries.
        
        Uses:
        - select_related: for foreign key relationships (none in this case)
        - prefetch_related: for reverse foreign key relationships and many-to-many
        """
        # Prefetch subjects tables
        subjects_prefetch = Prefetch(
            'subjects_tables',
            SubjectsTable.objects.all().order_by('sort_order')
        )
        
        # Prefetch salary tables
        salary_prefetch = Prefetch(
            'salary_tables',
            SalaryTable.objects.all().order_by('sort_order')
        )
        
        # Prefetch countries tables
        countries_prefetch = Prefetch(
            'countries_tables',
            CountriesTable.objects.all().order_by('sort_order')
        )
        
        return Major.objects.filter(
            publish_status='published'
        ).prefetch_related(
            subjects_prefetch,
            salary_prefetch,
            countries_prefetch,
            'best_universities',
            'cheap_universities',
            'related_articles'
        )
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for major detail page."""
        return (BreadcrumbTrail()
            .add_section('home')
            .add_section('majors')
            .current(self.object.name)
            .build())
    
    def get_context_data(self, **kwargs):
        """Add additional context for the template."""
        context = super().get_context_data(**kwargs)
        
        # Get dynamic tables (already prefetched)
        major = self.object
        context['subjects_tables'] = major.subjects_tables.all()
        context['salary_tables'] = major.salary_tables.all()
        context['countries_tables'] = major.countries_tables.all()
        context['best_universities'] = major.best_universities.all()
        context['cheap_universities'] = major.cheap_universities.all()
        
        return context


class MajorCategoryListView(BreadcrumbMixin, TemplateView):
    """
    Display majors filtered by category.
    
    Shows paginated list of majors for a specific category.
    """
    template_name = 'majors/category_list.html'
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for major category list page."""
        category = self.kwargs.get('category', 'other')
        category_labels = {
            'medical': 'التخصصات الطبية',
            'engineering': 'التخصصات الهندسية',
            'cs': 'الحاسوب والتكنولوجيا',
            'business': 'إدارة الأعمال',
            'science': 'العلوم',
            'other': 'تخصصات أخرى'
        }
        category_label = category_labels.get(category, 'التخصصات')
        
        return (BreadcrumbTrail()
            .add_section('home')
            .add_section('majors')
            .current(category_label)
            .build())
    
    def get_context_data(self, **kwargs):
        """Get majors by category with pagination."""
        context = super().get_context_data(**kwargs)
        category = self.kwargs.get('category')
        
        # Validate category
        valid_categories = ['medical', 'engineering', 'cs', 'business', 'science', 'other']
        if category not in valid_categories:
            category = 'other'
        
        # Prefetch tables
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
        
        queryset = Major.objects.filter(
            publish_status='published',
            major_category=category
        ).prefetch_related(
            subjects_prefetch,
            salary_prefetch,
            countries_prefetch,
            'best_universities',
            'cheap_universities',
            'related_articles'
        ).order_by('name')
        
        # Pagination
        paginator = Paginator(queryset, 12)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Category labels
        category_labels = {
            'medical': 'التخصصات الطبية',
            'engineering': 'التخصصات الهندسية',
            'cs': 'الحاسوب والتكنولوجيا',
            'business': 'إدارة الأعمال',
            'science': 'العلوم',
            'other': 'تخصصات أخرى'
        }
        
        context['majors'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        context['category'] = category
        context['category_label'] = category_labels.get(category, 'التخصصات')
        context['page_title'] = category_labels.get(category, 'التخصصات')
        
        return context
