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
