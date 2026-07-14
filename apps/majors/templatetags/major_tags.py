"""
Custom template tags and filters for majors app.
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


@register.filter
def split_prog_names(value):
    """
    Splits academic program names by slashes or commas and returns them as a list,
    grouping translations (e.g. Arabic / English) together on the same line.
    """
    if not value:
        return []
    
    # Split by / or , or Arabic comma (،)
    parts = [part.strip() for part in re.split(r'[/,،]', str(value)) if part.strip()]
    
    def has_arabic(text):
        return bool(re.search(r'[\u0600-\u06FF]', text))
        
    def has_english(text):
        return bool(re.search(r'[a-zA-Z]', text))
        
    grouped_parts = []
    for part in parts:
        if not grouped_parts:
            grouped_parts.append(part)
        else:
            last_part = grouped_parts[-1]
            last_has_arabic = has_arabic(last_part)
            last_has_english = has_english(last_part)
            curr_has_arabic = has_arabic(part)
            curr_has_english = has_english(part)
            
            is_translation = (
                (last_has_arabic and not last_has_english and curr_has_english and not curr_has_arabic) or
                (curr_has_arabic and not curr_has_english and last_has_english and not last_has_arabic)
            )
            if is_translation:
                grouped_parts[-1] = f"{last_part} / {part}"
            else:
                grouped_parts.append(part)
                
    return grouped_parts
@register.filter
def split_subjects(value):
    """
    Splits academic subjects by commas or newlines and returns them as a list.
    """
    if not value:
        return []
    
    # Split by Arabic comma, English comma, or newline
    parts = re.split(r'[،,\n]', str(value))
    return [part.strip() for part in parts if part.strip()]
