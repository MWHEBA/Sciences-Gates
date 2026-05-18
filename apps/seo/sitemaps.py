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


class BaseSitemap(Sitemap):
    """Base sitemap class with common configuration."""
    
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'
    
    def get_urls(self, page=1, site=None, protocol=None):
        """
        Override to ensure only published content is included.
        """
        urls = super().get_urls(page=page, site=site, protocol=protocol)
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
    """Sitemap for static pages.
    
    Includes static pages like home.
    """
    
    priority = 0.5
    changefreq = 'monthly'
    
    def items(self):
        """Return static page URLs."""
        return ['home']
    
    def location(self, item):
        """Return the URL for a static page."""
        return reverse(item)


# Sitemap index configuration
# Register all sitemaps in urls.py
sitemaps = {
    'universities': UniversitySitemap,
    'institutes': InstituteSitemap,
    'majors': MajorSitemap,
    'articles': ArticleSitemap,
    'static': StaticSitemap,
}
