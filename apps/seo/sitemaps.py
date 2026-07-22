"""
XML Sitemap generation for SEO.

This module provides sitemap classes for all content types.
Sitemaps filter by publish_status and sitemap_include fields to ensure
only published content that should be indexed appears in the sitemap.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article


def clear_sitemap_cache(sitemap_type=None):
    """
    Centralized utility to clear sitemap cache keys.
    If sitemap_type is provided (e.g. 'universities', 'institutes', 'majors', 'articles'),
    only that specific sitemap class's cache is cleared.
    """
    from django.core.cache import cache
    from django.contrib.sites.models import Site
    
    # We clear sitemaps for the production domain, local environments, and the active site domain
    domains = ['sciencesgates.com', 'localhost:8000', '127.0.0.1:8000']
    try:
        current_domain = Site.objects.get_current().domain
        if current_domain not in domains:
            domains.append(current_domain)
    except Exception:
        pass
        
    protocols = ['http', 'https']
    
    # Map type to sitemap class lower name
    type_map = {
        'universities': ['universitysitemap'],
        'institutes': ['institutesitemap'],
        'majors': ['majorsitemap'],
        'articles': ['articlesitemap'],
    }
    
    if sitemap_type in type_map:
        classes_to_clear = type_map[sitemap_type]
    else:
        # Clear all sitemaps
        classes_to_clear = ['universitysitemap', 'institutesitemap', 'majorsitemap', 'articlesitemap', 'staticsitemap']
        
    cache_keys = []
    for cls in classes_to_clear:
        for page in range(1, 11):
            # Clear key without domain/proto for legacy fallback
            cache_keys.append(f"sitemap_{cls}_page_{page}")
            # Clear keys with domains and protocols
            for domain in domains:
                for proto in protocols:
                    cache_keys.append(f"sitemap_{cls}_page_{page}_{domain}_{proto}")
                    
    cache.delete_many(cache_keys)


class BaseSitemap(Sitemap):
    """Base sitemap class with common configuration and caching."""
    
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'
    
    def get_urls(self, page=1, site=None, protocol=None):
        """
        Override to add caching and ensure only published content is included.
        """
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
        # Cache for 24 hours
        cache.set(cache_key, urls, 86400)
        return urls


class UniversitySitemap(BaseSitemap):
    """Sitemap for University content.
    
    Includes only published universities with sitemap_include=True.
    """
    
    priority = 0.9
    changefreq = 'monthly'
    
    def items(self):
        """Return published universities with sitemap inclusion enabled."""
        return University.objects.filter(
            publish_status='published',
            sitemap_include=True
        ).order_by('-updated_at')
    
    def location(self, item):
        """Return the URL for a university."""
        return item.get_absolute_url()
    
    def lastmod(self, item):
        """Return the last modification date."""
        return item.updated_at


class InstituteSitemap(BaseSitemap):
    """Sitemap for Institute content.
    
    Includes only published institutes with sitemap_include=True.
    """
    
    priority = 0.9
    changefreq = 'monthly'
    
    def items(self):
        """Return published institutes with sitemap inclusion enabled."""
        return Institute.objects.filter(
            publish_status='published',
            sitemap_include=True
        ).order_by('-updated_at')
    
    def location(self, item):
        """Return the URL for an institute."""
        return item.get_absolute_url()
    
    def lastmod(self, item):
        """Return the last modification date."""
        return item.updated_at


class MajorSitemap(BaseSitemap):
    """Sitemap for Major content.
    
    Includes only published majors with sitemap_include=True.
    """
    
    priority = 0.9
    changefreq = 'monthly'
    
    def items(self):
        """Return published majors with sitemap inclusion enabled."""
        return Major.objects.filter(
            publish_status='published',
            sitemap_include=True
        ).order_by('-updated_at')
    
    def location(self, item):
        """Return the URL for a major."""
        return item.get_absolute_url()
    
    def lastmod(self, item):
        """Return the last modification date."""
        return item.updated_at


class ArticleSitemap(BaseSitemap):
    """Sitemap for Article content.
    
    Includes only published articles with sitemap_include=True.
    """
    
    priority = 0.8
    changefreq = 'weekly'
    
    def items(self):
        """Return published articles with sitemap inclusion enabled."""
        return Article.objects.filter(
            publish_status='published',
            sitemap_include=True
        ).order_by('-updated_at')
    
    def location(self, item):
        """Return the URL for an article."""
        return item.get_absolute_url()
    
    def lastmod(self, item):
        """Return the last modification date."""
        return item.updated_at


class StaticSitemap(BaseSitemap):
    """Sitemap for static pages and listing pages.
    
    Includes main pages like home, about us, visa tracking, and main section list pages.
    """
    
    def items(self):
        """Return static and list page URL names."""
        return [
            'home',
            'about_us',
            'visa_tracking',
            'universities:list',
            'institutes:list',
            'majors:list',
            'articles:list',
        ]
    
    def location(self, item):
        """Return the URL for a static page."""
        return reverse(item)

    def priority(self, item):
        """Return priority per page type."""
        if item == 'home':
            return 1.0
        elif item in ['universities:list', 'institutes:list', 'majors:list', 'articles:list']:
            return 0.8
        return 0.5

    def changefreq(self, item):
        """Return change frequency per page type."""
        if item == 'home':
            return 'daily'
        elif item in ['universities:list', 'institutes:list', 'majors:list', 'articles:list']:
            return 'weekly'
        return 'monthly'


# Sitemap index configuration
# Register all sitemaps in urls.py
sitemaps = {
    'universities': UniversitySitemap,
    'institutes': InstituteSitemap,
    'majors': MajorSitemap,
    'articles': ArticleSitemap,
    'static': StaticSitemap,
}
