"""
Custom template tags and filters for institutes app.
"""
import re
from django import template

register = template.Library()


@register.filter
def remove_html_comments(value):
    """
    Remove HTML comments from text.
    
    Removes patterns like <!--StartFragment--><!--EndFragment-->
    """
    if not value:
        return value
    
    # Remove HTML comments
    pattern = r'<!--.*?-->'
    return re.sub(pattern, '', value, flags=re.DOTALL)


@register.filter
def clean_desc(value):
    """
    Cleans up description text, removing tags, comments and non-breaking spaces.
    """
    from apps.core.utils import clean_description
    return clean_description(value)

