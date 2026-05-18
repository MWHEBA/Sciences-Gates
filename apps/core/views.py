"""
Core views for the Science Gates platform.
"""
from django.views.generic import TemplateView
from django.db.models import Q
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article
from apps.core.models import PublishStatus


class HomeView(TemplateView):
    """
    Homepage view displaying featured content from all content types.
    
    Fetches and displays:
    - Featured universities (published, limited to 6)
    - Featured institutes (published, limited to 6)
    - Featured majors (published, limited to 6)
    - Recent articles (published, limited to 6)
    
    Requirements: 1, 19
    """
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        """
        Fetch featured content for the homepage.
        
        Uses select_related and prefetch_related for query optimization.
        Only includes published content.
        
        Query Optimization:
        - Uses select_related for foreign key relationships
        - Uses prefetch_related for many-to-many and reverse foreign key relationships
        - Limits results to 6 items per content type
        """
        context = super().get_context_data(**kwargs)
        
        # Fetch featured universities (published only)
        universities = University.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).prefetch_related(
            'faculties__programs',
            'faqs',
            'related_majors',
            'related_articles'
        )[:6]
        
        # Fetch featured institutes (published only)
        institutes = Institute.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).prefetch_related(
            'courses',
            'related_articles'
        )[:6]
        
        # Fetch featured majors (published only)
        majors = Major.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).prefetch_related(
            'best_universities',
            'cheap_universities',
            'related_articles',
            'subjects_tables',
            'salary_tables',
            'countries_tables'
        )[:6]
        
        # Fetch recent articles (published only)
        articles = Article.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).select_related(
            'category',
            'author'
        ).prefetch_related(
            'tags',
            'related_universities',
            'related_institutes',
            'related_majors'
        ).order_by('-publish_date')[:6]
        
        context.update({
            'universities': universities,
            'institutes': institutes,
            'majors': majors,
            'articles': articles,
        })
        
        return context
