"""
JSON-LD Schema markup generation for structured data.

This module provides utilities for generating structured data markup
for search engines using JSON-LD format according to schema.org vocabulary.
"""
import json
from django.urls import reverse
from django.conf import settings


class SchemaGenerator:
    """Base class for generating JSON-LD schema markup."""
    
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
        site_url = request.build_absolute_uri('/')
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Science Gates",
            "url": site_url,
            "description": "Educational content platform for Malaysian universities and institutes",
            "inLanguage": "ar",
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "Customer Service",
                "availableLanguage": ["ar", "en"]
            },
            "sameAs": [
                "https://www.facebook.com/sciencegates",
                "https://www.twitter.com/sciencegates",
                "https://www.linkedin.com/company/sciencegates"
            ]
        }
        
        # Add logo if available
        logo_url = request.build_absolute_uri('/static/images/logo.svg')
        if logo_url:
            schema["logo"] = {
                "@type": "ImageObject",
                "url": logo_url,
                "width": 250,
                "height": 60
            }
        
        return schema
    
    @staticmethod
    def generate_article_schema(article, request):
        """
        Generate Article schema for article content.
        
        Returns a JSON-LD Article schema with title, description, image, author,
        and publication dates for search engine optimization.
        
        Args:
            article: Article model instance
            request: HTTP request object for building absolute URLs
            
        Returns:
            Dictionary containing Article schema markup
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": article.get_meta_title(),
            "description": article.get_meta_description(),
            "datePublished": article.publish_date.isoformat() if article.publish_date else None,
            "dateModified": article.updated_at.isoformat() if article.updated_at else None,
            "inLanguage": "ar",
            "url": request.build_absolute_uri(article.get_absolute_url()),
        }
        
        # Add featured image if available
        if article.featured_image:
            schema["image"] = {
                "@type": "ImageObject",
                "url": request.build_absolute_uri(article.featured_image.url),
                "width": 1200,
                "height": 630
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
            "name": "Science Gates",
            "logo": {
                "@type": "ImageObject",
                "url": request.build_absolute_uri('/static/images/logo.svg'),
                "width": 250,
                "height": 60
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
