"""
Public views for displaying university content to end users.
"""
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Prefetch
from django.core.paginator import Paginator
from .models import University, Faculty, Program, UniversityFAQ
from apps.seo.mixins import BreadcrumbMixin
from apps.seo.breadcrumbs import BreadcrumbTrail
from apps.seo.preview import apply_preview_filter


class UniversityListView(BreadcrumbMixin, ListView):
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
        Return only published universities, ordered by name, filtered by search query, type, and city if provided.
        
        Query Optimization:
        - Uses select_related for any foreign key relationships
        - Uses prefetch_related for reverse foreign key relationships
        """
        queryset = University.objects.filter(
            publish_status='published'
        ).prefetch_related(
            'related_majors',
            'related_articles'
        ).order_by('name')
        
        # Apply search filter (q)
        q = self.request.GET.get('q', '').strip()
        if q:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(location__icontains=q)
            )
            
        # Apply university type filter (public/private/foreign)
        university_type = self.request.GET.get('type', '').strip()
        if university_type:
            queryset = queryset.filter(university_type=university_type)
            
        # Apply state filter
        state = self.request.GET.get('state', '').strip().lower()
        if state:
            queryset = queryset.filter(state=state)
            
        # Apply city/location filter (e.g. kl, subang-jaya, etc.)
        city = self.request.GET.get('city', '').strip().lower()
        if city:
            state_codes = [code for code, _ in University.STATE_CHOICES]
            if city in state_codes:
                queryset = queryset.filter(state=city)
            else:
                queryset = queryset.filter(city=city)
                
        return queryset

    def get_context_data(self, **kwargs):
        """Add clear_url, city choices, and hub cross-linking data to context."""
        context = super().get_context_data(**kwargs)
        from django.urls import reverse
        from apps.majors.models import Major
        from apps.articles.models import Article
        import json

        context['clear_url'] = reverse('universities:list')
        context['state_choices'] = University.STATE_CHOICES
        context['state_cities_json'] = json.dumps(University.STATE_CITIES)
        context['selected_state'] = self.request.GET.get('state', '')
        context['selected_city'] = self.request.GET.get('city', '')

        # Hub Pages SEO: cross-link to popular majors and latest articles
        context['popular_majors'] = Major.objects.filter(
            publish_status='published'
        ).order_by('name')[:8]

        context['latest_articles'] = Article.objects.filter(
            publish_status='published'
        ).select_related('category').order_by('-publish_date')[:5]

        return context
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for university list page."""
        return (BreadcrumbTrail()
            .add_section('home')
            .current('الجامعات')
            .build())


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

    def get_object(self, queryset=None):
        if not hasattr(self, 'object') or self.object is None:
            self.object = super().get_object(queryset)
        return self.object


    
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
        
        return apply_preview_filter(self.request, University.objects).prefetch_related(
            faculties_prefetch,
            faqs_prefetch,
            'related_majors',
            'related_articles',
            'tags',
            'attachments'
        )
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for university detail page."""
        return (BreadcrumbTrail()
            .add_section('home')
            .add_section('universities')
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
        
        # Get faculties with programs (already prefetched)
        university = self.object
        context['faculties'] = university.faculties.all()
        context['faqs'] = university.faqs.all()
        
        # Add lead form
        from apps.leads.forms import LeadForm
        if 'form' not in context:
            context['form'] = LeadForm()
        
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


class TagUniversityListView(BreadcrumbMixin, ListView):
    """
    Display a paginated list of published universities associated with a specific tag.
    """
    model = University
    template_name = 'universities/tag.html'
    context_object_name = 'universities'
    paginate_by = 20

    def get_queryset(self):
        tag_slug = self.kwargs.get('slug')
        return University.objects.filter(
            publish_status='published',
            tags__slug=tag_slug
        ).prefetch_related(
            'related_majors',
            'related_articles'
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.urls import reverse
        from apps.articles.models import Tag
        context['clear_url'] = reverse('universities:list')
        
        tag_slug = self.kwargs.get('slug')
        try:
            context['tag'] = Tag.objects.get(slug=tag_slug)
        except Tag.DoesNotExist:
            context['tag'] = None
        
        return context

    def get_breadcrumbs(self):
        tag_slug = self.kwargs.get('slug')
        from apps.articles.models import Tag
        try:
            tag = Tag.objects.get(slug=tag_slug)
            return (BreadcrumbTrail()
                .add_section('home')
                .add_section('universities')
                .current(f'وسم: {tag.name}')
                .build())
        except Tag.DoesNotExist:
            return (BreadcrumbTrail()
                .add_section('home')
                .add_section('universities')
                .build())
