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
def website_schema(context):
    """
    Generate WebSite schema for search engine site name display.
    
    Usage:
        {% load schema_tags %}
        <script type="application/ld+json">
        {% website_schema %}
        </script>
    """
    request = context.get('request')
    if not request:
        return '{}'
    
    schema = SchemaGenerator.generate_website_schema(request)
    return mark_safe(json.dumps(schema, ensure_ascii=False, indent=2))


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
    
    default_img_url = request.build_absolute_uri('/static/images/og-default.jpg')
    
    # Add logo if available
    if university.logo:
        schema["logo"] = {
            "@type": "ImageObject",
            "url": request.build_absolute_uri(university.logo.url)
        }
        schema["image"] = request.build_absolute_uri(university.logo.url)
    else:
        schema["logo"] = {
            "@type": "ImageObject",
            "url": default_img_url,
            "width": 600,
            "height": 600
        }
        schema["image"] = default_img_url
    
    # Add location
    if university.location:
        from bs4 import BeautifulSoup
        clean_loc = BeautifulSoup(str(university.location), 'html.parser').get_text(strip=True)
        if clean_loc:
            city_name = "Kuala Lumpur"
            for known_city in ['Kuala Lumpur', 'كوالالمبور', 'Selangor', 'سيلانجور', 'Johor', 'جوهور', 'Penang', 'بينانج', 'Kedah', 'كداح']:
                if known_city.lower() in clean_loc.lower():
                    city_name = known_city
                    break
            else:
                city_name = clean_loc[:40].split('،')[0].strip() if len(clean_loc) > 50 else clean_loc
            schema["address"] = {
                "@type": "PostalAddress",
                "addressCountry": "MY",
                "addressLocality": city_name
            }
        
    # Add telephone if available
    if getattr(university, 'telephone', None):
        schema["telephone"] = university.telephone
        
    # Add sameAs (website) if available
    if getattr(university, 'website', None):
        schema["sameAs"] = university.website
    
    return mark_safe(json.dumps(schema, ensure_ascii=False, indent=2))


@register.simple_tag(takes_context=True)
def institute_schema(context, institute):
    """
    Generate EducationalOrganization schema for institute content.
    
    Usage:
        {% load schema_tags %}
        <script type="application/ld+json">
        {% institute_schema institute %}
        </script>
    """
    request = context.get('request')
    if not request or not institute:
        return '{}'
    
    default_img_url = request.build_absolute_uri('/static/images/og-default.jpg')
    
    schema = {
        "@context": "https://schema.org",
        "@type": "EducationalOrganization",
        "name": institute.name,
        "description": institute.get_meta_description(),
        "url": request.build_absolute_uri(institute.get_absolute_url()),
        "inLanguage": "ar",
    }
    
    # Add logo if available
    if getattr(institute, 'main_image', None):
        schema["logo"] = {
            "@type": "ImageObject",
            "url": request.build_absolute_uri(institute.main_image.url)
        }
        schema["image"] = request.build_absolute_uri(institute.main_image.url)
    else:
        schema["logo"] = {
            "@type": "ImageObject",
            "url": default_img_url,
            "width": 600,
            "height": 600
        }
        schema["image"] = default_img_url
    
    # Add location
    if getattr(institute, 'location', None):
        from bs4 import BeautifulSoup
        clean_loc = BeautifulSoup(str(institute.location), 'html.parser').get_text(strip=True)
        if clean_loc:
            city_name = "Kuala Lumpur"
            for known_city in ['Kuala Lumpur', 'كوالالمبور', 'Selangor', 'سيلانجور', 'Johor', 'جوهور', 'Penang', 'بينانج']:
                if known_city.lower() in clean_loc.lower():
                    city_name = known_city
                    break
            else:
                city_name = clean_loc[:40].split('،')[0].strip() if len(clean_loc) > 50 else clean_loc
            schema["address"] = {
                "@type": "PostalAddress",
                "addressCountry": "MY",
                "addressLocality": city_name
            }
        
    # Add telephone if available
    if getattr(institute, 'telephone', None):
        schema["telephone"] = institute.telephone
        
    # Add sameAs (website) if available
    if getattr(institute, 'website', None):
        schema["sameAs"] = institute.website
    
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
    
    default_img_url = request.build_absolute_uri('/static/images/og-default.jpg')
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": major.name,
        "description": major.get_meta_description(),
        "provider": {
            "@type": "Organization",
            "name": "Science Gates",
            "logo": {
                "@type": "ImageObject",
                "url": default_img_url
            }
        },
        "image": default_img_url,
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
    from apps.seo.schema import _normalize_url, _CANONICAL_ORIGIN
    request = context.get('request')
    if not request:
        return '{}'

    page_url = _normalize_url(request.build_absolute_uri())
    img_url = _normalize_url(request.build_absolute_uri('/static/images/og-default.jpg'))
    canonical_org_id = f'{_CANONICAL_ORIGIN}/#organization'

    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page_name,
        "url": page_url,
        "inLanguage": "ar",
        "isPartOf": {"@id": f"{_CANONICAL_ORIGIN}/#website"},
        "primaryImageOfPage": {
            "@type": "ImageObject",
            "url": img_url,
            "width": 600,
            "height": 600
        },
        # Reference canonical Organization entity by @id — avoids name mismatch and duplication
        "publisher": {"@id": canonical_org_id}
    }

    return mark_safe(json.dumps(schema, ensure_ascii=False, indent=2))

