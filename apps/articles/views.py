"""
Public views for displaying article content to end users.
"""
from django.views.generic import ListView, DetailView
from django.db.models import Prefetch, Q
from .models import Article, Category, Tag


class ArticleListView(ListView):
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
        """
        return Article.objects.filter(
            publish_status='published'
        ).select_related(
            'category',
            'author'
        ).prefetch_related(
            'tags'
        ).order_by('-publish_date')


class ArticleDetailView(DetailView):
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
    
    def get_queryset(self):
        """
        Return only published articles with optimized queries.
        
        Uses:
        - select_related: for foreign key relationships (category, author)
        - prefetch_related: for many-to-many relationships (tags, related content)
        """
        return Article.objects.filter(
            publish_status='published'
        ).select_related(
            'category',
            'author'
        ).prefetch_related(
            'tags',
            'related_universities',
            'related_institutes',
            'related_majors'
        )
    
    def get_context_data(self, **kwargs):
        """Add additional context for the template."""
        context = super().get_context_data(**kwargs)
        
        # Get related content (already prefetched)
        article = self.object
        context['related_universities'] = article.related_universities.all()
        context['related_institutes'] = article.related_institutes.all()
        context['related_majors'] = article.related_majors.all()
        
        # Add breadcrumbs for SEO
        breadcrumbs = [
            ('الرئيسية', '/'),
            ('المقالات', '/articles/'),
        ]
        
        # Add category if available
        if article.category:
            breadcrumbs.append((article.category.name, article.category.get_absolute_url()))
        
        # Add current article
        breadcrumbs.append((article.title, None))
        
        context['breadcrumbs'] = breadcrumbs
        
        return context


class CategoryArticleListView(ListView):
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
    
    def get_context_data(self, **kwargs):
        """Add category information to context."""
        context = super().get_context_data(**kwargs)
        
        # Get the category
        category_slug = self.kwargs.get('slug')
        try:
            category = Category.objects.get(slug=category_slug)
            context['category'] = category
            
            # Add breadcrumbs for SEO
            context['breadcrumbs'] = [
                ('الرئيسية', '/'),
                ('المقالات', '/articles/'),
                (category.name, None),  # Current page
            ]
        except Category.DoesNotExist:
            context['category'] = None
            context['breadcrumbs'] = [
                ('الرئيسية', '/'),
                ('المقالات', '/articles/'),
            ]
        
        return context


class TagArticleListView(ListView):
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
    
    def get_context_data(self, **kwargs):
        """Add tag information to context."""
        context = super().get_context_data(**kwargs)
        
        # Get the tag
        tag_slug = self.kwargs.get('slug')
        try:
            tag = Tag.objects.get(slug=tag_slug)
            context['tag'] = tag
            
            # Add breadcrumbs for SEO
            context['breadcrumbs'] = [
                ('الرئيسية', '/'),
                ('المقالات', '/articles/'),
                (f'الوسم: {tag.name}', None),  # Current page
            ]
        except Tag.DoesNotExist:
            context['tag'] = None
            context['breadcrumbs'] = [
                ('الرئيسية', '/'),
                ('المقالات', '/articles/'),
            ]
        
        return context
