"""
Template tags for data table rendering and manipulation.
Provides utilities for accessing nested object/dictionary attributes in templates.
"""
from django import template

register = template.Library()


@register.filter
def get_item(obj, key):
    """
    Get an item from a dictionary or object attribute.
    
    Supports both dictionary access and object attribute access.
    Returns empty string if key doesn't exist.
    
    Usage in template:
        {{ row|get_item:"name" }}
        {{ row|get_item:"user.email" }}
        {{ row|get_item:"university_type_display" }}
    
    Args:
        obj: Dictionary or object to access
        key: Key or attribute name (supports dot notation for nested access)
        
    Returns:
        Value at the key/attribute, or empty string if not found
    """
    if not obj or not key:
        return ''
    
    # Handle dot notation for nested access
    if '.' in key:
        keys = key.split('.')
        value = obj
        for k in keys:
            try:
                # Try dictionary access first
                if isinstance(value, dict):
                    value = value[k]
                else:
                    # Try object attribute access
                    value = getattr(value, k, None)
                    if value is None:
                        return ''
            except (KeyError, AttributeError, TypeError):
                return ''
        return value
    
    # Single key access
    try:
        # Try dictionary access first
        if isinstance(obj, dict):
            return obj.get(key, '')
        else:
            # Try object attribute access
            return getattr(obj, key, '')
    except (KeyError, AttributeError, TypeError):
        return ''


@register.filter
def get_status_variant(status_value):
    """
    Map a status value to a badge variant.
    
    Status-to-variant mapping:
    - published → green (منشور)
    - unpublished → gray (غير منشور)
    - new → yellow (جديد)
    - contacted → blue (تم التواصل)
    - read → gray (مقروء)
    - unread → yellow (غير مقروء)
    - urgent → red (عاجل)
    - default → gray (for unmapped values)
    
    Usage in template:
        {% include "dashboard/components/badge.html" with text=status_value variant=status_value|get_status_variant %}
    
    Args:
        status_value: Status value to map
        
    Returns:
        str: Badge variant name
    """
    status_mapping = {
        'published': 'green',
        'unpublished': 'gray',
        'new': 'yellow',
        'contacted': 'blue',
        'read': 'gray',
        'unread': 'yellow',
        'urgent': 'red',
    }
    
    return status_mapping.get(str(status_value).lower(), 'gray')
