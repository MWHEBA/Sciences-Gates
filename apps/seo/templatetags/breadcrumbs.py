"""
Breadcrumb navigation template tags.

This module provides template tags for rendering breadcrumb navigation
and breadcrumb schema markup.

Supports both legacy formats (tuples, dicts) and new Breadcrumb objects
for backward compatibility during migration.

Validates: Requirements 10
"""
from django import template
from django.utils.safestring import mark_safe
import json

from apps.seo.schema import SchemaGenerator
from apps.seo.breadcrumbs import Breadcrumb, BreadcrumbTrail

register = template.Library()


@register.inclusion_tag('components/breadcrumb.html')
def render_breadcrumbs(breadcrumbs):
    """
    Render breadcrumb navigation.
    
    Generates HTML breadcrumb navigation with RTL support and Tailwind CSS styling.
    Delegates to components/breadcrumb.html component.
    
    Supports both legacy formats and new Breadcrumb objects:
    - List of Breadcrumb objects (preferred)
    - List of tuples: (name, url)
    - List of dicts: {'name': '...', 'url': '...'}
    
    Args:
        breadcrumbs: List of breadcrumb items
        
    Returns:
        Dictionary with breadcrumb data for template rendering
        
    Example:
        {% render_breadcrumbs breadcrumbs %}
        
    Validates: Requirements 10
    """
    # Convert to Breadcrumb objects if needed
    if not breadcrumbs:
        return {'breadcrumbs': []}
    
    # Check if already Breadcrumb objects
    if isinstance(breadcrumbs[0], Breadcrumb):
        normalized_breadcrumbs = breadcrumbs
    else:
        # Convert legacy format using BreadcrumbTrail
        trail = BreadcrumbTrail.from_legacy(breadcrumbs)
        normalized_breadcrumbs = trail.build()
    
    return {
        'breadcrumbs': normalized_breadcrumbs,
    }


@register.simple_tag
def render_breadcrumb_schema(breadcrumbs, request):
    """
    Render breadcrumb schema markup for structured data.
    
    Generates JSON-LD BreadcrumbList schema for search engine optimization.
    
    Supports both legacy formats and new Breadcrumb objects.
    
    Args:
        breadcrumbs: List of breadcrumb items
        request: HTTP request object for building absolute URLs
        
    Returns:
        JSON-LD script tag as string (marked safe)
        
    Example:
        {% render_breadcrumb_schema breadcrumbs request %}
        
    Validates: Requirements 10
    """
    if not breadcrumbs:
        return ''
    
    # Convert to Breadcrumb objects if needed
    if isinstance(breadcrumbs[0], Breadcrumb):
        normalized_breadcrumbs = breadcrumbs
    else:
        # Convert legacy format using BreadcrumbTrail
        trail = BreadcrumbTrail.from_legacy(breadcrumbs)
        normalized_breadcrumbs = trail.build()
    
    # Convert to tuples for schema generator
    breadcrumb_tuples = [(crumb.name, crumb.url) for crumb in normalized_breadcrumbs]
    
    # Generate schema using SchemaGenerator
    schema = SchemaGenerator.generate_breadcrumb_schema(breadcrumb_tuples, request)
    
    # Convert to JSON-LD
    schema_json = SchemaGenerator.to_json_ld(schema)
    
    # Return as script tag
    script_tag = f'<script type="application/ld+json">\n{schema_json}\n</script>'
    
    return mark_safe(script_tag)
