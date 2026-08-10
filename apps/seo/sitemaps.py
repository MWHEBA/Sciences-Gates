"""
XML Sitemap generation for SEO.

This module provides sitemap classes for all content types.
Sitemaps filter by publish_status and sitemap_include fields to ensure
only published content that should be indexed appears in the sitemap.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.db.models import Count, Q, Max
from django.utils import timezone
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major, MajorCategory
from apps.articles.models import Article, Category


def clear_sitemap_cache(sitemap_type=None):
    """
    Centralized utility to clear sitemap cache keys.
    """
    from django.core.cache import cache
    from django.contrib.sites.models import Site
    
    domains = ['sciencesgates.com', 'localhost:8000', '127.0.0.1:8000']
    try:
        current_domain = Site.objects.get_current().domain
        if current_domain not in domains:
            domains.append(current_domain)
    except Exception:
        pass
        
    protocols = ['http', 'https']
    
    type_map = {
        'universities': ['universitysitemap'],
        'institutes': ['institutesitemap'],
        'majors': ['majorsitemap'],
        'articles': ['articlesitemap'],
        'major_categories': ['majorcategorysitemap'],
        'article_categories': ['articlecategorysitemap'],
    }
    
    if sitemap_type in type_map:
        classes_to_clear = type_map[sitemap_type]
    else:
        classes_to_clear = [
            'universitysitemap', 'institutesitemap', 'majorsitemap', 
            'articlesitemap', 'majorcategorysitemap', 'articlecategorysitemap', 'staticsitemap'
        ]
        
    cache_keys = []
    for cls in classes_to_clear:
        for page in range(1, 11):
            cache_keys.append(f"sitemap_{cls}_page_{page}")
            for domain in domains:
                for proto in protocols:
                    cache_keys.append(f"sitemap_{cls}_page_{page}_{domain}_{proto}")
                    
    cache.delete_many(cache_keys)


class BaseSitemap(Sitemap):
    """Base sitemap class with common configuration and 24-hour caching."""
    
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'
    
    def get_urls(self, page=1, site=None, protocol=None):
        from django.core.cache import cache
        from django.contrib.sites.models import Site as DjangoSite
        
        if site is None:
            try:
                resolved_site = DjangoSite.objects.get_current()
            except Exception:
                resolved_site = None
        else:
            resolved_site = site
            
        domain = resolved_site.domain if resolved_site else 'sciencesgates.com'
        proto = protocol or 'https'
        
        cache_key = f"sitemap_{self.__class__.__name__.lower()}_page_{page}_{domain}_{proto}"
        cached_urls = cache.get(cache_key)
        if cached_urls is not None:
            return cached_urls
            
        urls = super().get_urls(page=page, site=site, protocol=protocol)
        # Cache for 24 hours (86400s)
        cache.set(cache_key, urls, 86400)
        return urls


class UniversitySitemap(BaseSitemap):
    """Sitemap for University content."""
    priority = 0.9
    changefreq = 'monthly'
    
    def items(self):
        return University.objects.filter(
            publish_status='published',
            sitemap_include=True
        ).order_by('-updated_at')
    
    def location(self, item):
        return item.get_absolute_url()
    
    def lastmod(self, item):
        return item.updated_at


class InstituteSitemap(BaseSitemap):
    """Sitemap for Institute content."""
    priority = 0.9
    changefreq = 'monthly'
    
    def items(self):
        return Institute.objects.filter(
            publish_status='published',
            sitemap_include=True
        ).order_by('-updated_at')
    
    def location(self, item):
        return item.get_absolute_url()
    
    def lastmod(self, item):
        return item.updated_at


class MajorSitemap(BaseSitemap):
    """Sitemap for Major content."""
    priority = 0.9
    changefreq = 'monthly'
    
    def items(self):
        return Major.objects.filter(
            publish_status='published',
            sitemap_include=True
        ).order_by('-updated_at')
    
    def location(self, item):
        return item.get_absolute_url()
    
    def lastmod(self, item):
        return item.updated_at


class ArticleSitemap(BaseSitemap):
    """Sitemap for Article content."""
    priority = 0.8
    changefreq = 'weekly'
    
    def items(self):
        return Article.objects.filter(
            publish_status='published',
            sitemap_include=True
        ).order_by('-updated_at')
    
    def location(self, item):
        return item.get_absolute_url()
    
    def lastmod(self, item):
        return item.updated_at


class MajorCategorySitemap(BaseSitemap):
    """
    Sitemap for Major Category archive pages.
    Quality Gate: Only includes categories with at least 1 active published major.
    """
    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        return MajorCategory.objects.annotate(
            pub_count=Count('majors', filter=Q(majors__publish_status='published'))
        ).filter(pub_count__gte=1).order_by('-updated_at')

    def location(self, item):
        return item.get_absolute_url()

    def lastmod(self, item):
        return item.updated_at


class ArticleCategorySitemap(BaseSitemap):
    """
    Sitemap for Article Category archive pages.
    Quality Gate: Only includes categories with at least 1 active published article.
    """
    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        return Category.objects.annotate(
            pub_count=Count('articles', filter=Q(articles__publish_status='published'))
        ).filter(pub_count__gte=1).order_by('-updated_at')

    def location(self, item):
        return reverse('articles:category', kwargs={'slug': item.slug})

    def lastmod(self, item):
        return item.updated_at


class StaticSitemap(BaseSitemap):
    """Sitemap for static pages and main listing pages."""
    
    def items(self):
        return [
            'home',
            'about_us',
            'visa_tracking',
            'privacy',
            'terms',
            'universities:list',
            'institutes:list',
            'majors:list',
            'articles:list',
        ]
    
    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        try:
            if item in ['home', 'articles:list']:
                latest = Article.objects.filter(publish_status='published').aggregate(Max('updated_at'))['updated_at__max']
            elif item == 'universities:list':
                latest = University.objects.filter(publish_status='published').aggregate(Max('updated_at'))['updated_at__max']
            elif item == 'majors:list':
                latest = Major.objects.filter(publish_status='published').aggregate(Max('updated_at'))['updated_at__max']
            elif item == 'institutes:list':
                latest = Institute.objects.filter(publish_status='published').aggregate(Max('updated_at'))['updated_at__max']
            else:
                latest = None
            return latest if latest else timezone.now()
        except Exception:
            return timezone.now()

    def priority(self, item):
        if item == 'home':
            return 1.0
        elif item in ['universities:list', 'institutes:list', 'majors:list', 'articles:list']:
            return 0.8
        return 0.5

    def changefreq(self, item):
        if item == 'home':
            return 'daily'
        elif item in ['universities:list', 'institutes:list', 'majors:list', 'articles:list']:
            return 'weekly'
        return 'monthly'


sitemaps = {
    'universities': UniversitySitemap,
    'institutes': InstituteSitemap,
    'majors': MajorSitemap,
    'articles': ArticleSitemap,
    'major_categories': MajorCategorySitemap,
    'article_categories': ArticleCategorySitemap,
    'static': StaticSitemap,
}
