"""
JSON-LD Schema markup generation for structured data.

This module provides utilities for generating structured data markup
for search engines using JSON-LD format according to schema.org vocabulary.
"""
import json
from django.urls import reverse
from django.conf import settings


def _normalize_url(url):
    if not url:
        return url
    if 'www.sciencesgates.com' in url:
        url = url.replace('www.sciencesgates.com', 'sciencesgates.com')
    if url.startswith('http://sciencesgates.com'):
        url = 'https://sciencesgates.com' + url[len('http://sciencesgates.com'):]
    return url


class SchemaGenerator:
    """Base class for generating JSON-LD schema markup."""
    
    @staticmethod
    def generate_website_schema(request):
        site_url = _normalize_url(request.build_absolute_uri('/'))
        logo_url = _normalize_url(request.build_absolute_uri('/static/images/og-default.jpg'))
        
        return {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "شركة بوابات العلوم للدراسة في ماليزيا",
            "alternateName": ["بوابات العلوم", "Science Gates"],
            "url": site_url,
            "image": logo_url
        }
    
    @staticmethod
    def generate_organization_schema(request):
        """
        Generate Organization schema for the website.
        
        Returns a JSON-LD Organization schema with site name, logo, contact info,
        and social profiles for search engine optimization.
        
        Args:
            request: HTTP request object for building absolute URLs
            
        Returns:
            Dictionary containing Organization schema markup
        """
        site_url = _normalize_url(request.build_absolute_uri('/'))
        
        from apps.core.models import SiteSettings
        try:
            site_settings = SiteSettings.get_settings()
            same_as_links = [item['url'] for item in site_settings.social_links]
        except Exception:
            same_as_links = []

        if not same_as_links:
            same_as_links = [
                "https://www.facebook.com/sciencegates",
                "https://www.twitter.com/sciencegates",
                "https://www.linkedin.com/company/sciencegates"
            ]
        
        logo_url = _normalize_url(request.build_absolute_uri('/static/images/og-default.jpg'))
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "شركة بوابات العلوم للدراسة في ماليزيا",
            "alternateName": ["بوابات العلوم", "Science Gates"],
            "url": site_url,
            "description": "منصة متخصصة في القبولات الجامعية والخدمات التعليمية للدراسة في ماليزيا",
            "inLanguage": "ar",
            "logo": {
                "@type": "ImageObject",
                "url": logo_url,
                "width": 600,
                "height": 600
            },
            "image": {
                "@type": "ImageObject",
                "url": logo_url,
                "width": 600,
                "height": 600
            },
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "Customer Service",
                "availableLanguage": ["ar", "en"]
            },
            "sameAs": same_as_links
        }
        
        return schema
    
    @staticmethod
    def generate_article_schema(article, request):
        schema = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": article.get_meta_title(),
            "description": article.get_meta_description(),
            "datePublished": article.publish_date.isoformat() if article.publish_date else None,
            "dateModified": article.updated_at.isoformat() if article.updated_at else None,
            "inLanguage": "ar",
            "url": _normalize_url(request.build_absolute_uri(article.get_absolute_url())),
        }
        
        logo_url = _normalize_url(request.build_absolute_uri('/static/images/og-default.jpg'))
        
        # Add featured image if available
        if article.featured_image:
            schema["image"] = {
                "@type": "ImageObject",
                "url": _normalize_url(request.build_absolute_uri(article.featured_image.url)),
                "width": 1200,
                "height": 630
            }
        else:
            schema["image"] = {
                "@type": "ImageObject",
                "url": logo_url,
                "width": 600,
                "height": 600
            }
        
        # Add author information
        if article.author:
            schema["author"] = {
                "@type": "Person",
                "name": article.author_display_name
            }
        else:
            schema["author"] = {
                "@type": "Organization",
                "name": article.author_display_name
            }
        
        # Add publisher information
        schema["publisher"] = {
            "@type": "Organization",
            "name": "شركة بوابات العلوم للدراسة في ماليزيا",
            "logo": {
                "@type": "ImageObject",
                "url": logo_url,
                "width": 600,
                "height": 600
            }
        }
        
        return schema
    
    @staticmethod
    def generate_breadcrumb_schema(breadcrumbs, request):
        """
        Generate BreadcrumbList schema for navigation.
        
        Returns a JSON-LD BreadcrumbList schema for search engine optimization
        and breadcrumb navigation display.
        
        Args:
            breadcrumbs: List of tuples (name, url)
            request: HTTP request object for building absolute URLs
            
        Returns:
            Dictionary containing BreadcrumbList schema markup
        """
        items = []
        for index, (name, url) in enumerate(breadcrumbs, 1):
            # For the current page (last item), url is None — use the request's full path
            if url is None:
                url = request.build_absolute_uri()
            elif url.startswith('/'):
                url = request.build_absolute_uri(url)
            items.append({
                "@type": "ListItem",
                "position": index,
                "name": name,
                "item": url,
            })
        
        schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": items,
        }
        return schema
    
    @staticmethod
    def generate_faq_schema(faqs):
        """
        Generate FAQPage schema for FAQ sections.
        
        Returns a JSON-LD FAQPage schema with questions and answers for
        search engine optimization and rich snippets.
        
        Args:
            faqs: List of dictionaries with 'question' and 'answer' keys,
                  or list of FAQ model instances with question and answer attributes
            
        Returns:
            Dictionary containing FAQPage schema markup
        """
        main_entity = []
        
        for faq in faqs:
            # Handle both dictionary and model instance formats
            if isinstance(faq, dict):
                question = faq.get('question', '')
                answer = faq.get('answer', '')
            else:
                # Assume it's a model instance
                question = getattr(faq, 'question', '')
                answer = getattr(faq, 'answer', '')
            
            if question and answer:
                main_entity.append({
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": answer,
                    }
                })
        
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": main_entity,
        }
        
        return schema
    
    @staticmethod
    def to_json_ld(schema):
        """
        Convert schema dictionary to JSON-LD string.
        
        Args:
            schema: Dictionary containing schema data
            
        Returns:
            JSON string representation of the schema
        """
        return json.dumps(schema, ensure_ascii=False, indent=2)
