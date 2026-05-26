"""
Custom template tags and filters for universities app.
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
def to_embed_url(url):
    """
    يحول رابط YouTube العادي لرابط embed يشتغل جوه iframe.
    
    يدعم الصيغ دي:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID (يرجعه زي ما هو)
    """
    if not url:
        return url
    
    # لو الرابط أصلاً embed يرجعه زي ما هو
    if '/embed/' in url:
        return url
    
    # استخراج video ID من صيغة watch
    match = re.match(r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)', url)
    if match:
        return f'https://www.youtube.com/embed/{match.group(1)}'
    
    # استخراج video ID من صيغة youtu.be
    match = re.match(r'https?://youtu\.be/([a-zA-Z0-9_-]+)', url)
    if match:
        return f'https://www.youtube.com/embed/{match.group(1)}'
    
    return url


@register.filter
def clean_university_name(value):
    """
    Splits the string by '|' and returns the first part stripped.
    """
    if not value:
        return value
    return value.split('|')[0].strip()
