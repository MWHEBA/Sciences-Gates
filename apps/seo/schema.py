"""
JSON-LD Schema markup generation for structured data.

This module provides utilities for generating structured data markup
for search engines using JSON-LD format according to schema.org vocabulary.
"""
import json
from django.urls import reverse
from django.conf import settings
from django.templatetags.static import static


# Canonical production origin — single source of truth for schema URLs
_CANONICAL_ORIGIN = 'https://sciencesgates.com'

# All patterns that must never appear in production schema output
_LOCALHOST_PATTERNS = [
    'http://localhost:8000',
    'https://localhost:8000',
    'http://localhost',
    'https://localhost',
    'http://127.0.0.1:8000',
    'https://127.0.0.1:8000',
    'http://127.0.0.1',
    'https://127.0.0.1',
]


def _normalize_url(url):
    """Normalize a URL to canonical HTTPS production form.

    Converts:
    - www.sciencesgates.com → sciencesgates.com
    - http://sciencesgates.com → https://sciencesgates.com
    - localhost / 127.0.0.1 (any port) → https://sciencesgates.com
    """
    if not url:
        return url
    # Strip www prefix
    if 'www.sciencesgates.com' in url:
        url = url.replace('www.sciencesgates.com', 'sciencesgates.com')
    # Upgrade plain-http to HTTPS
    if url.startswith('http://sciencesgates.com'):
        url = _CANONICAL_ORIGIN + url[len('http://sciencesgates.com'):]
    # Replace any localhost / 127.0.0.1 pattern with the canonical origin
    for pattern in _LOCALHOST_PATTERNS:
        if url.startswith(pattern):
            url = _CANONICAL_ORIGIN + url[len(pattern):]
            break
    return url


def _get_base_url(request=None):
    """
    Construct canonical base site URL dynamically.

    Priority order:
    1. settings.SITE_URL (from .env) — normalized to strip localhost/www/http.
    2. request.build_absolute_uri('/') — normalized similarly.
    3. Hard-coded production fallback.

    IMPORTANT: SITE_URL must be set to 'https://sciencesgates.com' in the
    production .env file.  If it is left as the default 'http://localhost:8000'
    the _normalize_url guard below will still correct the output.
    """
    configured = getattr(settings, 'SITE_URL', '').rstrip('/')
    if configured:
        normalized = _normalize_url(configured + '/')
        # Extra safety: if after normalization we still have localhost, ignore it
        if 'localhost' not in normalized and '127.0.0.1' not in normalized:
            return normalized
    if request:
        normalized = _normalize_url(request.build_absolute_uri('/'))
        if 'localhost' not in normalized and '127.0.0.1' not in normalized:
            return normalized
    return f'{_CANONICAL_ORIGIN}/'


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
            "taxID": "202101038492",
            "identifier": {
                "@type": "PropertyValue",
                "propertyID": "SSM",
                "value": "202101038492"
            },
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
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": article_url
            },
            "headline": article.get_meta_title(),
            "description": article.get_meta_description(),
            "image": [logo_url],
            "datePublished": article.publish_date.replace(microsecond=0).isoformat() if getattr(article, 'publish_date', None) else None,
            "dateModified": article.updated_at.replace(microsecond=0).isoformat() if getattr(article, 'updated_at', None) else None,
            "inLanguage": "ar",
            "url": article_url,
            "author": {
                "@type": "Person",
                "@id": f"{base_url}author/dr-mohammad-kayali/#person",
                "name": article.author_display_name,
                "url": f"{base_url}author/dr-mohammad-kayali/"
            },
            "publisher": {
                "@type": "Organization",
                "@id": f"{base_url}#organization",
                "name": "شركة بوابات العلوم",
                "logo": {
                    "@type": "ImageObject",
                    "url": logo_url
                }
            }
        }
        
        if getattr(article, 'featured_image', None) and hasattr(article.featured_image, 'url'):
            img_url = request.build_absolute_uri(article.featured_image.url) if request else f"{base_url}{article.featured_image.url.lstrip('/')}"
            schema["image"] = {
                "@type": "ImageObject",
                "url": _normalize_url(img_url),
                "width": 1200,
                "height": 630
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
        import re
        from bs4 import BeautifulSoup

        questions = []
        for faq in faqs:
            q_text = getattr(faq, 'question', None) or (faq.get('question') if isinstance(faq, dict) else None)
            a_text = getattr(faq, 'answer', None) or (faq.get('answer') if isinstance(faq, dict) else None)
            
            if q_text and a_text:
                # Strip HTML tags and shortcodes for clean plain-text JSON-LD
                clean_answer = BeautifulSoup(str(a_text), 'html.parser').get_text(separator=' ', strip=True)
                clean_answer = re.sub(r'\[wptb[^\]]*\]', '', clean_answer).strip()
                
                if clean_answer:
                    questions.append({
                        "@type": "Question",
                        "name": str(q_text).strip(),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": clean_answer
                        }
                    })
        
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": questions
        }
