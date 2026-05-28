"""
Public views for displaying institute content to end users.
"""
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Prefetch
from django.core.paginator import Paginator
from .models import Institute, Course
from apps.seo.mixins import BreadcrumbMixin
from apps.seo.breadcrumbs import BreadcrumbTrail


class InstituteListView(BreadcrumbMixin, ListView):
    """
    Display a paginated list of published institutes.
    
    Implements pagination with 20 items per page.
    Optimizes queries using select_related for foreign keys.
    """
    model = Institute
    template_name = 'institutes/list.html'
    context_object_name = 'institutes'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Return only published institutes, ordered by name.
        
        Query Optimization:
        - Uses prefetch_related for reverse foreign key relationships
        """
        return Institute.objects.filter(
            publish_status='published'
        ).prefetch_related(
            'related_articles'
        ).order_by('name')
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for institute list page."""
        return (BreadcrumbTrail()
            .add_section('home')
            .current('المعاهد')
            .build())


class InstituteDetailView(BreadcrumbMixin, DetailView):
    """
    Display detailed information about a specific institute.
    
    Includes:
    - Institute basic information (name, main image, description)
    - Registration requirements
    - Courses with their details
    - Registration section
    
    Optimizes queries using select_related and prefetch_related to avoid N+1 problems.
    """
    model = Institute
    template_name = 'institutes/detail.html'
    context_object_name = 'institute'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Return only published institutes with optimized queries.
        
        Uses:
        - select_related: for foreign key relationships (none in this case)
        - prefetch_related: for reverse foreign key relationships (courses, related articles)
        """
        # Prefetch courses
        courses_prefetch = Prefetch(
            'courses',
            Course.objects.all().order_by('name')
        )
        
        return Institute.objects.filter(
            publish_status='published'
        ).prefetch_related(
            courses_prefetch,
            'related_articles'
        )
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for institute detail page."""
        return (BreadcrumbTrail()
            .add_section('home')
            .add_section('institutes')
            .current(self.object.name)
            .build())
    
    def post(self, request, *args, **kwargs):
        """Handle form submission."""
        from apps.leads.forms import LeadForm
        
        form = LeadForm(request.POST)
        if form.is_valid():
            # Save the lead
            lead = form.save(commit=False)
            lead.source_page = request.path
            lead.referrer = request.META.get('HTTP_REFERER', '')
            lead.save()
            
            # Redirect to success page or return success message
            from django.shortcuts import redirect
            return redirect(request.path + '?success=true')
        
        # If form is invalid, re-render with errors
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['form'] = form
        return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        """Add additional context for the template."""
        context = super().get_context_data(**kwargs)
        
        # Get courses (already prefetched)
        institute = self.object
        context['courses'] = institute.courses.all()
        
        # Add lead form
        from apps.leads.forms import LeadForm
        if 'form' not in context:
            context['form'] = LeadForm()
        
        return context


class InstituteTypeListView(BreadcrumbMixin, TemplateView):
    """
    Display institutes filtered by type (language/academic).
    
    Shows paginated list of institutes for a specific type.
    """
    template_name = 'institutes/type_list.html'
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for institute type list page."""
        institute_type = self.kwargs.get('type', 'academic')
        type_labels = {
            'language': 'معاهد اللغة الإنجليزية',
            'academic': 'المعاهد الأكاديمية'
        }
        type_label = type_labels.get(institute_type, 'المعاهد')
        
        return (BreadcrumbTrail()
            .add_section('home')
            .add_section('institutes')
            .current(type_label)
            .build())
    
    def get_context_data(self, **kwargs):
        """Get institutes by type with pagination."""
        context = super().get_context_data(**kwargs)
        institute_type = self.kwargs.get('type')
        
        # Validate type
        if institute_type not in ['language', 'academic']:
            institute_type = 'academic'
        
        # Prefetch courses
        courses_prefetch = Prefetch(
            'courses',
            Course.objects.all().order_by('name')
        )
        
        queryset = Institute.objects.filter(
            publish_status='published',
            institute_type=institute_type
        ).prefetch_related(
            courses_prefetch,
            'related_articles'
        ).order_by('name')
        
        # Pagination
        paginator = Paginator(queryset, 12)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Type labels
        type_labels = {
            'language': 'معاهد اللغة الإنجليزية',
            'academic': 'المعاهد الأكاديمية'
        }
        
        context['institutes'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        context['institute_type'] = institute_type
        context['type_label'] = type_labels.get(institute_type, 'المعاهد')
        context['page_title'] = type_labels.get(institute_type, 'المعاهد')
        
        return context
