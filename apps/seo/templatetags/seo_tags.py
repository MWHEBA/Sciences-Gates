"""
SEO template tags for rendering meta tags and schema markup.

This module provides template tags for:
- Meta tags (title, description, robots, canonical)
- Open Graph tags
- Twitter Card tags
- JSON-LD schema markup

Validates: Requirements 10
"""
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def render_meta_tags(obj):
    """
    Render SEO meta tags for a content object.
    
    Generates HTML meta tags for:
    - title (via meta_title or fallback)
    - description (via meta_description or fallback)
    - robots (index/noindex, follow/nofollow)
    - keywords (focus_keyword if available)
    
    Args:
        obj: Content object with SEO fields (must have SEOMixin)
        
    Returns:
        HTML string with meta tags (marked safe)
        
    Example:
        {% render_meta_tags article %}
    """
    if not obj:
        return ''
    
    meta_tags = []
    
    # Meta title
    meta_title = getattr(obj, 'get_meta_title', lambda: '')()
    if meta_title:
        meta_tags.append(f'<meta name="title" content="{escape(meta_title)}">')
    
    # Meta description
    meta_description = getattr(obj, 'get_meta_description', lambda: '')()
    if meta_description:
        meta_tags.append(f'<meta name="description" content="{escape(meta_description)}">')
    
    # Robots meta tag
    robots_content = getattr(obj, 'get_robots_content', lambda: '')()
    if robots_content:
        meta_tags.append(f'<meta name="robots" content="{escape(robots_content)}">')
    
    # Focus keyword
    focus_keyword = getattr(obj, 'focus_keyword', '')
    if focus_keyword:
        meta_tags.append(f'<meta name="keywords" content="{escape(focus_keyword)}">')
    
    return mark_safe('\n    '.join(meta_tags))


@register.simple_tag
def render_og_tags(obj, request=None):
    """
    Render Open Graph meta tags for social media sharing.
    
    Generates HTML meta tags for:
    - og:title
    - og:description
    - og:image
    - og:url
    - og:type (defaults to 'website')
    
    Args:
        obj: Content object with SEO fields (must have SEOMixin)
        request: HTTP request object for building absolute URLs (optional)
        
    Returns:
        HTML string with Open Graph meta tags (marked safe)
        
    Example:
        {% render_og_tags article request %}
    """
    if not obj:
        return ''
    
    og_tags = []
    
    # OG title
    og_title = getattr(obj, 'get_og_title', lambda: '')()
    if og_title:
        og_tags.append(f'<meta property="og:title" content="{escape(og_title)}">')
    
    # OG description
    og_description = getattr(obj, 'get_og_description', lambda: '')()
    if og_description:
        og_tags.append(f'<meta property="og:description" content="{escape(og_description)}">')
    
    # OG image
def normalize_canonical_domain(url):
    """
    Ensures URL uses the non-www production domain (https://sciencesgates.com).
    Strips www. for sciencesgates.com and ensures https scheme.
    """
    if not url:
        return url
    if 'www.sciencesgates.com' in url:
        url = url.replace('www.sciencesgates.com', 'sciencesgates.com')
    if url.startswith('http://sciencesgates.com'):
        url = 'https://sciencesgates.com' + url[len('http://sciencesgates.com'):]
    return url


@register.simple_tag
def render_open_graph_tags(obj, request=None):
    if not obj:
        return ''
    
    og_tags = []
    
    # OG Title
    og_title = getattr(obj, 'get_og_title', lambda: getattr(obj, 'get_meta_title', lambda: '')())()
    if og_title:
        og_tags.append(f'<meta property="og:title" content="{escape(og_title)}">')
    
    # OG Description
    og_description = getattr(obj, 'get_og_description', lambda: getattr(obj, 'get_meta_description', lambda: '')())()
    if og_description:
        og_tags.append(f'<meta property="og:description" content="{escape(og_description)}">')
    
    # OG Image
    og_image_url = getattr(obj, 'get_og_image_url', lambda: '')()
    if not og_image_url:
        from django.templatetags.static import static
        og_image_url = static('images/og-default.jpg')
    
    if request and not og_image_url.startswith('http'):
        og_image_url = request.build_absolute_uri(og_image_url)
        
    og_image_url = normalize_canonical_domain(og_image_url)
    
    og_tags.append(f'<meta property="og:image" content="{escape(og_image_url)}">')
    og_tags.append(f'<meta property="og:image:secure_url" content="{escape(og_image_url)}">')
    og_tags.append('<meta property="og:image:width" content="600">')
    og_tags.append('<meta property="og:image:height" content="600">')
    img_type = 'image/png' if og_image_url.lower().endswith('.png') else 'image/jpeg'
    og_tags.append(f'<meta property="og:image:type" content="{img_type}">')
    
    # Thumbnail tags for Google Search & legacy link previewers
    og_tags.append(f'<meta name="thumbnail" content="{escape(og_image_url)}">')
    og_tags.append(f'<link rel="image_src" href="{escape(og_image_url)}">')
    
    # OG URL
    if request and hasattr(obj, 'get_absolute_url'):
        og_url = request.build_absolute_uri(obj.get_absolute_url())
        og_url = normalize_canonical_domain(og_url)
        og_tags.append(f'<meta property="og:url" content="{escape(og_url)}">')
    
    # OG type (default to website)
    og_type = getattr(obj, 'og_type', 'website')
    og_tags.append(f'<meta property="og:type" content="{escape(og_type)}">')
    
    return mark_safe('\n    '.join(og_tags))


@register.simple_tag
def render_twitter_card_tags(obj, request=None):
    if not obj:
        return ''
    
    twitter_tags = []
    
    # Twitter card type
    twitter_card_type = getattr(obj, 'twitter_card_type', 'summary_large_image')
    twitter_tags.append(f'<meta name="twitter:card" content="{escape(twitter_card_type)}">')
    
    # Twitter title
    twitter_title = getattr(obj, 'get_meta_title', lambda: '')()
    if twitter_title:
        twitter_tags.append(f'<meta name="twitter:title" content="{escape(twitter_title)}">')
    
    # Twitter description
    twitter_description = getattr(obj, 'get_meta_description', lambda: '')()
    if twitter_description:
        twitter_tags.append(f'<meta name="twitter:description" content="{escape(twitter_description)}">')
    
    # Twitter image
    twitter_image_url = getattr(obj, 'get_og_image_url', lambda: '')()
    if not twitter_image_url:
        from django.templatetags.static import static
        twitter_image_url = static('images/og-default.jpg')
        
    if request and not twitter_image_url.startswith('http'):
        twitter_image_url = request.build_absolute_uri(twitter_image_url)
    twitter_image_url = normalize_canonical_domain(twitter_image_url)
    twitter_tags.append(f'<meta name="twitter:image" content="{escape(twitter_image_url)}">')
    
    return mark_safe('\n    '.join(twitter_tags))


@register.simple_tag
def render_canonical_tag(obj, request=None):
    if not obj:
        return ''
    
    # Use custom canonical URL if provided
    canonical_url = getattr(obj, 'canonical_url', '')
    
    # Fall back to object's absolute URL
    if not canonical_url and hasattr(obj, 'get_absolute_url'):
        canonical_url = obj.get_absolute_url()
    
    if not canonical_url:
        return ''
    
    # Make absolute URL if request is provided and URL is relative
    if request and not canonical_url.startswith('http'):
        canonical_url = request.build_absolute_uri(canonical_url)
        
    canonical_url = normalize_canonical_domain(canonical_url)
    
    return mark_safe(f'<link rel="canonical" href="{escape(canonical_url)}">')
