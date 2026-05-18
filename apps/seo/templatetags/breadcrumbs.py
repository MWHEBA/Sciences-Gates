"""
Breadcrumb navigation template tags.

This module provides template tags for rendering breadcrumb navigation
and breadcrumb schema markup.

Validates: Requirements 10
"""
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
import json

from apps.seo.schema import SchemaGenerator

register = template.Library()


@register.inclusion_tag('seo/breadcrumbs.html')
def render_breadcrumbs(breadcrumbs):
    """
    Render breadcrumb navigation.
    
    Generates HTML breadcrumb navigation with RTL support and Tailwind CSS styling.
    
    Args:
        breadcrumbs: List of tuples (name, url) or list of dicts with 'name' and 'url' keys
        
    Returns:
        Dictionary with breadcrumb data for template rendering
        
    Example:
        {% render_breadcrumbs breadcrumbs %}
        
    Validates: Requirements 10
    """
    # Normalize breadcrumbs to list of dicts
    normalized_breadcrumbs = []
    for item in breadcrumbs:
        if isinstance(item, tuple):
            normalized_breadcrumbs.append({
                'name': item[0],
                'url': item[1] if len(item) > 1 else None,
            })
        elif isinstance(item, dict):
            normalized_breadcrumbs.append(item)
        else:
            # Skip invalid items
            continue
    
    return {
        'breadcrumbs': normalized_breadcrumbs,
    }


@register.simple_tag
def render_breadcrumb_schema(breadcrumbs, request):
    """
    Render breadcrumb schema markup for structured data.
    
    Generates JSON-LD BreadcrumbList schema for search engine optimization.
    
    Args:
        breadcrumbs: List of tuples (name, url) or list of dicts with 'name' and 'url' keys
        request: HTTP request object for building absolute URLs
        
    Returns:
        JSON-LD script tag as string (marked safe)
        
    Example:
        {% render_breadcrumb_schema breadcrumbs request %}
        
    Validates: Requirements 10
    """
    if not breadcrumbs:
        return ''
    
    # Normalize breadcrumbs to list of tuples
    normalized_breadcrumbs = []
    for item in breadcrumbs:
        if isinstance(item, tuple):
            normalized_breadcrumbs.append(item)
        elif isinstance(item, dict):
            normalized_breadcrumbs.append((item.get('name', ''), item.get('url', '')))
        else:
            continue
    
    # Generate schema using SchemaGenerator
    schema = SchemaGenerator.generate_breadcrumb_schema(normalized_breadcrumbs, request)
    
    # Convert to JSON-LD
    schema_json = SchemaGenerator.to_json_ld(schema)
    
    # Return as script tag
    script_tag = f'<script type="application/ld+json">\n{schema_json}\n</script>'
    
    return mark_safe(script_tag)
