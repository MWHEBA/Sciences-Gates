"""
JSON-LD Schema template tags for structured data.

يوفر template tags لإنشاء Schema markup بسهولة في القوالب.
"""
from django import template
from django.utils.safestring import mark_safe
from apps.seo.schema import SchemaGenerator
import json

register = template.Library()


@register.simple_tag(takes_context=True)
def organization_schema(context):
    """
    Generate Organization schema for the website.
    
    Usage:
        {% load schema_tags %}
        <script type="application/ld+json">
        {% organization_schema %}
        </script>
    """
    request = context.get('request')
    if not request:
        return '{}'
    
    schema = SchemaGenerator.generate_organization_schema(request)
    return mark_safe(json.dumps(schema, ensure_ascii=False, indent=2))


@register.simple_tag(takes_context=True)
def article_schema(context, article):
    """
    Generate Article schema for article content.
    
    Usage:
        {% load schema_tags %}
        <script type="application/ld+json">
        {% article_schema article %}
        </script>
    """
    request = context.get('request')
    if not request or not article:
        return '{}'
    
    schema = SchemaGenerator.generate_article_schema(article, request)
    return mark_safe(json.dumps(schema, ensure_ascii=False, indent=2))


@register.simple_tag(takes_context=True)
def breadcrumb_schema(context):
    """
    Generate BreadcrumbList schema from breadcrumbs in context.
    
    Usage:
        {% load schema_tags %}
        <script type="application/ld+json">
        {% breadcrumb_schema %}
        </script>
    """
    request = context.get('request')
    breadcrumbs = context.get('breadcrumbs', [])
    
    if not request or not breadcrumbs:
        return '{}'
    
    # Convert breadcrumbs to tuples if they're objects
    breadcrumb_tuples = []
    for crumb in breadcrumbs:
        if hasattr(crumb, 'name') and hasattr(crumb, 'url'):
            breadcrumb_tuples.append((crumb.name, crumb.url))
        elif isinstance(crumb, (tuple, list)) and len(crumb) >= 2:
            breadcrumb_tuples.append((crumb[0], crumb[1]))
    
    schema = SchemaGenerator.generate_breadcrumb_schema(breadcrumb_tuples, request)
    return mark_safe(json.dumps(schema, ensure_ascii=False, indent=2))


@register.simple_tag
def faq_schema(faqs):
    """
    Generate FAQPage schema for FAQ sections.
    
    Usage:
        {% load schema_tags %}
        {% if faqs %}
        <script type="application/ld+json">
        {% faq_schema faqs %}
        </script>
        {% endif %}
    """
    if not faqs:
        return '{}'
    
    schema = SchemaGenerator.generate_faq_schema(faqs)
    return mark_safe(json.dumps(schema, ensure_ascii=False, indent=2))


@register.simple_tag(takes_context=True)
def university_schema(context, university):
    """
    Generate EducationalOrganization schema for university content.
    
    Usage:
        {% load schema_tags %}
        <script type="application/ld+json">
        {% university_schema university %}
        </script>
    """
    request = context.get('request')
    if not request or not university:
        return '{}'
    
    schema = {
        "@context": "https://schema.org",
        "@type": "EducationalOrganization",
        "name": university.name,
        "description": university.get_meta_description(),
        "url": request.build_absolute_uri(university.get_absolute_url()),
        "inLanguage": "ar",
    }
    
    # Add logo if available
    if university.logo:
        schema["logo"] = {
            "@type": "ImageObject",
            "url": request.build_absolute_uri(university.logo.url)
        }
    
    # Add location
    if university.location:
        schema["address"] = {
            "@type": "PostalAddress",
            "addressCountry": "MY",
            "addressLocality": university.location
        }
        
    # Add telephone if available
    if getattr(university, 'telephone', None):
        schema["telephone"] = university.telephone
        
    # Add sameAs (website) if available
    if getattr(university, 'website', None):
        schema["sameAs"] = university.website
    
    return mark_safe(json.dumps(schema, ensure_ascii=False, indent=2))


@register.simple_tag(takes_context=True)
def major_course_schema(context, major):
    """
    Generate Course schema for major/specialization content.
    
    Usage:
        {% load schema_tags %}
        <script type="application/ld+json">
        {% major_course_schema major %}
        </script>
    """
    request = context.get('request')
    if not request or not major:
        return '{}'
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": major.name,
        "description": major.get_meta_description(),
        "provider": {
            "@type": "Organization",
            "name": "Science Gates"
        },
        "inLanguage": "ar",
    }
    
    # Add study duration if available
    if major.bachelor_duration:
        schema["timeRequired"] = major.bachelor_duration
    elif major.study_duration:
        schema["timeRequired"] = major.study_duration
    
    # Add URL
    schema["url"] = request.build_absolute_uri(major.get_absolute_url())
    
    return mark_safe(json.dumps(schema, ensure_ascii=False, indent=2))


@register.simple_tag(takes_context=True)
def webpage_schema(context, page_name):
    """
    Generate WebPage schema for general pages.
    
    Usage:
        {% load schema_tags %}
        <script type="application/ld+json">
        {% webpage_schema "الصفحة الرئيسية" %}
        </script>
    """
    request = context.get('request')
    if not request:
        return '{}'
    
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page_name,
        "url": request.build_absolute_uri(),
        "inLanguage": "ar",
        "publisher": {
            "@type": "Organization",
            "name": "Science Gates"
        }
    }
    
    return mark_safe(json.dumps(schema, ensure_ascii=False, indent=2))
