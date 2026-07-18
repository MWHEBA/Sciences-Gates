"""
Public views for displaying article content to end users.
"""
from django.views.generic import ListView, DetailView
from django.db.models import Prefetch, Q
from .models import Article, Category, Tag
from apps.seo.mixins import BreadcrumbMixin
from apps.seo.breadcrumbs import BreadcrumbTrail
from apps.seo.preview import apply_preview_filter


class ArticleListView(BreadcrumbMixin, ListView):
    """
    Display a paginated list of published articles.
    
    Implements pagination with 20 items per page.
    Optimizes queries using select_related for foreign keys.
    Ordered by publish date (newest first).
    """
    model = Article
    template_name = 'articles/list.html'
    context_object_name = 'articles'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Return only published articles, ordered by publish date (newest first).
        Filtered by search query and category if provided.
        """
        queryset = Article.objects.filter(
            publish_status='published'
        ).select_related(
            'category',
            'author'
        ).prefetch_related(
            'tags'
        ).order_by('-publish_date')

        # Apply search filter (q)
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(content__icontains=q)
            )

        # Apply category filter
        category_id = self.request.GET.get('category', '').strip()
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        """Add categories, clear_url, and hub cross-linking data to context."""
        context = super().get_context_data(**kwargs)
        from django.urls import reverse
        from apps.universities.models import University
        from apps.majors.models import Major

        context['categories'] = Category.objects.all().order_by('name')
        context['clear_url'] = reverse('articles:list')

        # Hub Pages SEO: cross-link to universities and majors
        context['popular_universities'] = University.objects.filter(
            publish_status='published'
        ).order_by('name')[:6]

        context['popular_majors'] = Major.objects.filter(
            publish_status='published'
        ).order_by('name')[:6]

        return context
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for article list page."""
        return (BreadcrumbTrail()
            .add_section('home')
            .current('المقالات')
            .build())


class ArticleDetailView(BreadcrumbMixin, DetailView):
    """
    Display detailed information about a specific article.
    
    Includes:
    - Article basic information (title, featured image, category, tags, author, publish date)
    - Article content (sanitized HTML)
    - Related universities, institutes, and majors
    
    Optimizes queries using select_related and prefetch_related to avoid N+1 problems.
    """
    model = Article
    template_name = 'articles/detail.html'
    context_object_name = 'article'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        if not hasattr(self, 'object') or self.object is None:
            self.object = super().get_object(queryset)
        return self.object


    
    def get_queryset(self):
        """
        Return only published articles with optimized queries.
        
        Uses:
        - select_related: for foreign key relationships (category, author)
        - prefetch_related: for many-to-many relationships (tags, related content)
        """
        return apply_preview_filter(self.request, Article.objects).select_related(
            'category',
            'author'
        ).prefetch_related(
            'tags',
            'related_universities',
            'related_institutes',
            'related_majors',
            'faqs',
            'attachments'
        )
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for article detail page."""
        article = self.object
        trail = BreadcrumbTrail().add_section('home').add_section('articles')
        
        # Add category if available
        if article.category:
            trail.add(article.category.name, article.category.get_absolute_url())
        
        # Add current article
        trail.current(article.title)
        
        return trail.build()
    
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
        
        # Get related content (already prefetched)
        article = self.object
        context['related_universities'] = article.related_universities.all()
        context['related_institutes'] = article.related_institutes.all()
        context['related_majors'] = article.related_majors.all()
        context['faqs'] = article.faqs.all()
        
        # Get related articles from the same category
        if article.category:
            context['related_articles'] = Article.objects.filter(
                publish_status='published',
                category=article.category
            ).exclude(pk=article.pk).select_related('category', 'author')[:3]
        
        # Add lead form
        from apps.leads.forms import LeadForm
        if 'form' not in context:
            context['form'] = LeadForm()
        
        return context


class CategoryArticleListView(BreadcrumbMixin, ListView):
    """
    Display a paginated list of published articles in a specific category.
    
    Implements pagination with 20 items per page.
    Filters articles by category slug.
    Ordered by publish date (newest first).
    """
    model = Article
    template_name = 'articles/category.html'
    context_object_name = 'articles'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Return only published articles in the specified category.
        """
        category_slug = self.kwargs.get('slug')
        return Article.objects.filter(
            publish_status='published',
            category__slug=category_slug
        ).select_related(
            'category',
            'author'
        ).prefetch_related(
            'tags'
        ).order_by('-publish_date')
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for category article list page."""
        category_slug = self.kwargs.get('slug')
        try:
            category = Category.objects.get(slug=category_slug)
            return (BreadcrumbTrail()
                .add_section('home')
                .add_section('articles')
                .current(category.name)
                .build())
        except Category.DoesNotExist:
            return (BreadcrumbTrail()
                .add_section('home')
                .add_section('articles')
                .build())
    
    def get_context_data(self, **kwargs):
        """Add category information to context."""
        context = super().get_context_data(**kwargs)
        from django.urls import reverse
        context['clear_url'] = reverse('articles:list')
        
        # Get the category
        category_slug = self.kwargs.get('slug')
        try:
            category = Category.objects.get(slug=category_slug)
            context['category'] = category
        except Category.DoesNotExist:
            context['category'] = None
        
        return context


class TagArticleListView(BreadcrumbMixin, ListView):
    """
    Display a paginated list of published articles with a specific tag.
    
    Implements pagination with 20 items per page.
    Filters articles by tag slug.
    Ordered by publish date (newest first).
    """
    model = Article
    template_name = 'articles/tag.html'
    context_object_name = 'articles'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Return only published articles with the specified tag.
        """
        tag_slug = self.kwargs.get('slug')
        return Article.objects.filter(
            publish_status='published',
            tags__slug=tag_slug
        ).select_related(
            'category',
            'author'
        ).prefetch_related(
            'tags'
        ).order_by('-publish_date').distinct()
    
    def get_breadcrumbs(self):
        """Build breadcrumb trail for tag article list page."""
        tag_slug = self.kwargs.get('slug')
        try:
            tag = Tag.objects.get(slug=tag_slug)
            return (BreadcrumbTrail()
                .add_section('home')
                .add_section('articles')
                .current(f'الوسم: {tag.name}')
                .build())
        except Tag.DoesNotExist:
            return (BreadcrumbTrail()
                .add_section('home')
                .add_section('articles')
                .build())
    
    def get_context_data(self, **kwargs):
        """Add tag information to context."""
        context = super().get_context_data(**kwargs)
        from django.urls import reverse
        context['clear_url'] = reverse('articles:list')
        
        # Get the tag
        tag_slug = self.kwargs.get('slug')
        try:
            tag = Tag.objects.get(slug=tag_slug)
            context['tag'] = tag
        except Tag.DoesNotExist:
            context['tag'] = None
        
        return context
