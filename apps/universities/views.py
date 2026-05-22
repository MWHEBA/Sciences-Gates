"""
Public views for displaying university content to end users.
"""
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Prefetch
from django.core.paginator import Paginator
from .models import University, Faculty, Program, UniversityFAQ
from apps.seo.mixins import BreadcrumbMixin
from apps.seo.breadcrumbs import BreadcrumbTrail


class UniversityListView(ListView):
    """
    Display a paginated list of published universities.
    
    Implements pagination with 20 items per page.
    Optimizes queries using select_related for foreign keys.
    """
    model = University
    template_name = 'universities/list.html'
    context_object_name = 'universities'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Return only published universities, ordered by name.
        
        Query Optimization:
        - Uses select_related for any foreign key relationships
        - Uses prefetch_related for reverse foreign key relationships
        """
        return University.objects.filter(
            publish_status='published'
        ).prefetch_related(
            'related_majors',
            'related_articles'
        ).order_by('name')


class UniversityDetailView(BreadcrumbMixin, DetailView):
    """
    Display detailed information about a specific university.
    
    Includes:
    - University basic information (name, logo, main image, description, location, video)
    - Admission requirements
    - Registration section
    - Faculties with their programs
    - FAQ section with accordion UI
    
    Optimizes queries using select_related and prefetch_related to avoid N+1 problems.
    """
    model = University
    template_name = 'universities/detail.html'
    context_object_name = 'university'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Return only published universities with optimized queries.
        
        Uses:
        - select_related: for foreign key relationships (none in this case)
        - prefetch_related: for reverse foreign key relationships (faculties, FAQs)
        """
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
        
        # Prefetch FAQs
        faqs_prefetch = Prefetch(
            'faqs',
            UniversityFAQ.objects.all().order_by('sort_order')
        )
        
        return University.objects.filter(
            publish_status='published'
        ).prefetch_related(
            faculties_prefetch,
            faqs_prefetch,
            'related_majors',
            'related_articles'
        )
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for university detail page."""
        return (BreadcrumbTrail()
            .add_section('home')
            .add_section('universities')
            .current(self.object.name)
            .build())
    
    def get_context_data(self, **kwargs):
        """Add additional context for the template."""
        context = super().get_context_data(**kwargs)
        
        # Get faculties with programs (already prefetched)
        university = self.object
        context['faculties'] = university.faculties.all()
        context['faqs'] = university.faqs.all()
        
        return context


class UniversityTypeListView(BreadcrumbMixin, TemplateView):
    """
    Display universities filtered by type (public/private).
    
    Shows paginated list of universities for a specific type.
    """
    template_name = 'universities/type_list.html'
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for university type list page."""
        university_type = self.kwargs.get('type', 'public')
        type_labels = {
            'public': 'الجامعات الحكومية',
            'private': 'الجامعات الخاصة'
        }
        type_label = type_labels.get(university_type, 'الجامعات')
        
        return (BreadcrumbTrail()
            .add_section('home')
            .add_section('universities')
            .current(type_label)
            .build())
    
    def get_context_data(self, **kwargs):
        """Get universities by type with pagination."""
        context = super().get_context_data(**kwargs)
        university_type = self.kwargs.get('type')
        
        # Validate type
        if university_type not in ['public', 'private']:
            university_type = 'public'
        
        # Prefetch faculties with programs
        faculties_prefetch = Prefetch(
            'faculties',
            Faculty.objects.prefetch_related(
                Prefetch(
                    'programs',
                    Program.objects.all().order_by('sort_order')
                )
            ).order_by('sort_order')
        )
        
        queryset = University.objects.filter(
            publish_status='published',
            university_type=university_type
        ).prefetch_related(
            faculties_prefetch,
            'related_majors',
            'related_articles'
        ).order_by('name')
        
        # Pagination
        paginator = Paginator(queryset, 12)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Type labels
        type_labels = {
            'public': 'الجامعات الحكومية',
            'private': 'الجامعات الخاصة'
        }
        
        context['universities'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        context['university_type'] = university_type
        context['type_label'] = type_labels.get(university_type, 'الجامعات')
        context['page_title'] = type_labels.get(university_type, 'الجامعات')
        
        return context
