"""
Public views for displaying institute content to end users.
"""
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Prefetch
from django.core.paginator import Paginator
from .models import Institute, Course
from apps.seo.mixins import BreadcrumbMixin
from apps.seo.breadcrumbs import BreadcrumbTrail
from apps.seo.preview import apply_preview_filter


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
        Return only published institutes, ordered by name, filtered by search query and city if provided.
        """
        queryset = Institute.objects.filter(
            publish_status='published'
        ).prefetch_related(
            'related_articles'
        ).order_by('name')
        
        # Apply search filter (q)
        q = self.request.GET.get('q', '').strip()
        if q:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q)
            )
            
        # Apply state filter
        state = self.request.GET.get('state', '').strip().lower()
        if state:
            queryset = queryset.filter(state=state)
            
        # Apply city filter
        city = self.request.GET.get('city', '').strip().lower()
        if city:
            from apps.universities.models import University
            state_codes = [code for code, _ in University.STATE_CHOICES]
            if city in state_codes:
                queryset = queryset.filter(state=city)
            else:
                queryset = queryset.filter(city=city)
                
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add clear_url and city choices to context for resetting filters."""
        context = super().get_context_data(**kwargs)
        from django.urls import reverse
        from apps.universities.models import University
        import json
        context['clear_url'] = reverse('institutes:list')
        context['state_choices'] = University.STATE_CHOICES
        context['state_cities_json'] = json.dumps(University.STATE_CITIES)
        context['selected_state'] = self.request.GET.get('state', '')
        context['selected_city'] = self.request.GET.get('city', '')
        return context

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

    def get_object(self, queryset=None):
        if not hasattr(self, 'object') or self.object is None:
            self.object = super().get_object(queryset)
        return self.object

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.is_legacy and request.resolver_match and request.resolver_match.view_name != 'legacy_detail':
            from django.shortcuts import redirect
            return redirect(obj.get_absolute_url(), permanent=True)
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Return only published institutes with optimized queries.
        
        Uses:
        - select_related: for foreign key relationships (none in this case)
        - prefetch_related: for reverse foreign key relationships (courses, related articles, faqs)
        """
        courses_prefetch = Prefetch(
            'courses',
            Course.objects.all().order_by('sort_order', 'id')
        )
        
        return apply_preview_filter(self.request, Institute.objects).prefetch_related(
            courses_prefetch,
            'related_articles',
            'tags',
            'attachments',
            'faqs'
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
        context['faqs'] = institute.faqs.all()
        
        # Add lead form
        from apps.leads.forms import LeadForm
        if 'form' not in context:
            context['form'] = LeadForm()
        
        return context



class TagInstituteListView(BreadcrumbMixin, ListView):
    """
    Display a paginated list of published institutes associated with a specific tag.
    """
    model = Institute
    template_name = 'institutes/tag.html'
    context_object_name = 'institutes'
    paginate_by = 20

    def get_queryset(self):
        tag_slug = self.kwargs.get('slug')
        return Institute.objects.filter(
            publish_status='published',
            tags__slug=tag_slug
        ).prefetch_related(
            'related_articles'
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.urls import reverse
        from apps.articles.models import Tag
        context['clear_url'] = reverse('institutes:list')
        
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
                .add_section('institutes')
                .current(f'وسم: {tag.name}')
                .build())
        except Tag.DoesNotExist:
            return (BreadcrumbTrail()
                .add_section('home')
                .add_section('institutes')
                .build())
