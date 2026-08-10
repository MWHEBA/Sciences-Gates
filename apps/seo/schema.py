"""
JSON-LD Schema markup generation for structured data.

This module provides utilities for generating structured data markup
for search engines using JSON-LD format according to schema.org vocabulary.
"""
import json
from django.urls import reverse
from django.conf import settings
from django.templatetags.static import static


def _normalize_url(url):
    if not url:
        return url
    if 'www.sciencesgates.com' in url:
        url = url.replace('www.sciencesgates.com', 'sciencesgates.com')
    if url.startswith('http://sciencesgates.com'):
        url = 'https://sciencesgates.com' + url[len('http://sciencesgates.com'):]
    return url


def _get_base_url(request=None):
    """
    Construct canonical base site URL dynamically.
    First checks settings.SITE_URL, falls back to request.build_absolute_uri('/').
    """
    configured = getattr(settings, 'SITE_URL', '').rstrip('/')
    if configured:
        return _normalize_url(configured + '/')
    if request:
        return _normalize_url(request.build_absolute_uri('/'))
    return 'https://sciencesgates.com/'


class SchemaGenerator:
    """Base class for generating JSON-LD schema markup."""
    
    @staticmethod
    def generate_website_schema(request=None):
        base_url = _get_base_url(request)
        logo_url = _normalize_url(request.build_absolute_uri(static('images/og-default.jpg')) if request else f"{base_url}static/images/og-default.jpg")
        
        return {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{base_url}#website",
            "name": "شركة بوابات العلوم",
            "alternateName": ["بوابات العلوم", "Sciences Gates", "بوابات العلوم للدراسة في ماليزيا"],
            "url": base_url,
            "inLanguage": "ar",
            "image": logo_url,
            "publisher": {
                "@id": f"{base_url}#organization"
            }
        }
    
    @staticmethod
    def generate_organization_schema(request=None):
        """
        Generate Organization schema for the website.
        """
        base_url = _get_base_url(request)
        
        from apps.core.models import SiteSettings
        try:
            site_settings = SiteSettings.get_settings()
            raw_links = [item['url'] for item in site_settings.social_links]
        except Exception:
            raw_links = []

        if not raw_links:
            raw_links = [
                "https://www.facebook.com/sciencegates",
                "https://www.twitter.com/sciencegates",
                "https://www.linkedin.com/company/sciencegates"
            ]
        
        # Exclude messaging channels like wa.me / whatsapp from sameAs
        same_as_links = [
            link for link in raw_links 
            if 'wa.me' not in link and 'whatsapp' not in link
        ]
        
        logo_url = _normalize_url(request.build_absolute_uri(static('images/og-default.jpg')) if request else f"{base_url}static/images/og-default.jpg")
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": f"{base_url}#organization",
            "name": "شركة بوابات العلوم",
            "alternateName": ["بوابات العلوم", "Sciences Gates", "بوابات العلوم للدراسة في ماليزيا"],
            "url": base_url,
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
                "telephone": "+601128195437",
                "email": "info@sciencesgates.com",
                "availableLanguage": ["ar", "en"],
                "areaServed": ["MY", "SA", "AE", "EG", "KW", "QA", "OM"]
            },
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Kuala Lumpur",
                "addressCountry": "MY"
            },
            "sameAs": same_as_links
        }
        
        return schema
    
    @staticmethod
    def generate_article_schema(article, request=None):
        base_url = _get_base_url(request)
        article_url = _normalize_url(request.build_absolute_uri(article.get_absolute_url()) if request else f"{base_url}articles/{article.slug}/")
        logo_url = _normalize_url(request.build_absolute_uri(static('images/og-default.jpg')) if request else f"{base_url}static/images/og-default.jpg")

        schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "@id": f"{article_url}#blogposting",
            "headline": article.get_meta_title(),
            "description": article.get_meta_description(),
            "datePublished": article.publish_date.isoformat() if getattr(article, 'publish_date', None) else None,
            "dateModified": article.updated_at.isoformat() if getattr(article, 'updated_at', None) else None,
            "inLanguage": "ar",
            "url": article_url,
            "isPartOf": {
                "@id": f"{base_url}#website"
            },
            "publisher": {
                "@id": f"{base_url}#organization"
            },
            "author": {
                "@type": "Person",
                "@id": f"{base_url}author/dr-mohammad-kayali/#person",
                "name": getattr(article, 'author_display_name', 'د. محمد الكيالي')
            }
        }
        
        if article.featured_image:
            img_url = request.build_absolute_uri(article.featured_image.url) if request else article.featured_image.url
            schema["image"] = {
                "@type": "ImageObject",
                "url": _normalize_url(img_url),
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
        
        return schema
    
    @staticmethod
    def generate_breadcrumb_schema(breadcrumbs, request=None):
        """
        Generate BreadcrumbList schema for navigation.
        """
        base_url = _get_base_url(request)
        items = []
        
        for index, crumb in enumerate(breadcrumbs, 1):
            if hasattr(crumb, 'name') and hasattr(crumb, 'url'):
                name = crumb.name
                url = crumb.url
            elif isinstance(crumb, (tuple, list)) and len(crumb) >= 2:
                name = crumb[0]
                url = crumb[1]
            else:
                continue

            if url is None and request:
                url = request.build_absolute_uri()
            elif url and url.startswith('/'):
                url = request.build_absolute_uri(url) if request else f"{base_url}{url.lstrip('/')}"
            
            items.append({
                "@type": "ListItem",
                "position": index,
                "name": name,
                "item": url or base_url,
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
        """
        questions = []
        for faq in faqs:
            q_text = getattr(faq, 'question', None) or (faq.get('question') if isinstance(faq, dict) else None)
            a_text = getattr(faq, 'answer', None) or (faq.get('answer') if isinstance(faq, dict) else None)
            
            if q_text and a_text:
                questions.append({
                    "@type": "Question",
                    "name": q_text,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": a_text
                    }
                })
        
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": questions
        }
