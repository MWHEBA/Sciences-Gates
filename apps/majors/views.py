"""
Public views for displaying major content to end users.
"""
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Prefetch, Q
from django.core.paginator import Paginator
from .models import Major, SubjectsTable, SalaryTable, CountriesTable, MajorFAQ, MajorAttachment
from apps.seo.mixins import BreadcrumbMixin
from apps.seo.breadcrumbs import BreadcrumbTrail
from apps.seo.preview import apply_preview_filter


class MajorListView(BreadcrumbMixin, ListView):
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
        Return only published majors, ordered by name, filtered by search query if provided.
        
        Query Optimization:
        - Uses prefetch_related for many-to-many relationships
        """
        queryset = Major.objects.filter(
            publish_status='published'
        ).prefetch_related(
            'best_universities',
            'cheap_universities',
            'related_articles'
        ).order_by('name')

        # Apply search filter (q)
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q)
            )

        return queryset
    
    def get_context_data(self, **kwargs):
        """Add clear_url and hub cross-linking data to context."""
        context = super().get_context_data(**kwargs)
        from django.urls import reverse
        from apps.universities.models import University
        from apps.articles.models import Article

        context['clear_url'] = reverse('majors:list')

        # Hub Pages SEO: cross-link to popular universities and latest articles
        context['popular_universities'] = University.objects.filter(
            publish_status='published'
        ).order_by('name')[:6]

        context['latest_articles'] = Article.objects.filter(
            publish_status='published'
        ).select_related('category').order_by('-publish_date')[:5]

        return context

    def get_breadcrumbs(self):
        """Build breadcrumb trail for major list page."""
        return (BreadcrumbTrail()
            .add_section('home')
            .current('التخصصات')
            .build())


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
        Return only published majors with optimized queries.
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
        
        # Prefetch FAQs
        faqs_prefetch = Prefetch(
            'faqs',
            MajorFAQ.objects.all().order_by('sort_order')
        )
        
        # Prefetch Attachments
        attachments_prefetch = Prefetch(
            'attachments',
            MajorAttachment.objects.all().order_by('-created_at')
        )
        
        # Prefetch Programs offering this major
        from apps.universities.models import Program
        programs_prefetch = Prefetch(
            'programs',
            Program.objects.select_related('faculty__university').all().order_by('sort_order')
        )
        
        return apply_preview_filter(self.request, Major.objects).prefetch_related(
            subjects_prefetch,
            salary_prefetch,
            countries_prefetch,
            faqs_prefetch,
            attachments_prefetch,
            programs_prefetch,
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
        
        # Get dynamic tables (already prefetched)
        major = self.object
        context['subjects_tables'] = major.subjects_tables.all()
        context['salary_tables'] = major.salary_tables.all()
        context['countries_tables'] = major.countries_tables.all()
        context['best_universities'] = major.best_universities.all()
        context['cheap_universities'] = major.cheap_universities.all()
        
        # Add new prefetched relations
        context['faqs'] = major.faqs.all()
        context['attachments'] = major.attachments.all()
        context['programs'] = major.programs.all()
        
        # Group subjects by track_name for tabbed rendering
        from collections import defaultdict
        subjects_by_track = defaultdict(list)
        for subject in major.subjects_tables.all():
            track = subject.track_name or 'عام'
            subjects_by_track[track].append(subject)
        context['subjects_by_track'] = dict(subjects_by_track)
        
        # Add lead form
        from apps.leads.forms import LeadForm
        if 'form' not in context:
            context['form'] = LeadForm()
        
        return context


class MajorCategoryListView(BreadcrumbMixin, TemplateView):
    """
    Display majors filtered by category.
    
    Shows paginated list of majors for a specific category.
    """
    template_name = 'majors/category_list.html'
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for major category list page."""
        from django.shortcuts import get_object_or_404
        from apps.majors.models import MajorCategory
        category_slug = self.kwargs.get('category')
        cat_obj = get_object_or_404(MajorCategory, slug=category_slug)
        
        return (BreadcrumbTrail()
            .add_section('home')
            .add_section('majors')
            .current(cat_obj.name)
            .build())
    
    def get_context_data(self, **kwargs):
        """Get majors by category with pagination."""
        from django.shortcuts import get_object_or_404
        from apps.majors.models import MajorCategory
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('category')
        cat_obj = get_object_or_404(MajorCategory, slug=category_slug)
        
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
            category=cat_obj
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
        
        context['majors'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        context['category'] = category_slug
        context['category_label'] = cat_obj.name
        context['page_title'] = cat_obj.name
        context['category_obj'] = cat_obj
        
        return context
