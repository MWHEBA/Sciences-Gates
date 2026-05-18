"""
HTML sanitization utilities for article content.
Sanitizes HTML to prevent XSS attacks while allowing safe formatting for articles.

V1 Scope: Allows basic formatting tags (bold, italic, headings, lists, links, images)
Future enhancements: video embeds, tables, CTA blocks
"""
import bleach
from django.utils.html import escape
from django.utils.safestring import mark_safe


# V1 Allowed HTML tags for article content
# Includes: p, br, strong, em, h2-h6, ul, ol, li, a, img
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'a', 'img'
]

# Allowed attributes for each tag
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
}

# Allowed protocols for URLs
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_article_html(html_content):
    """
    Sanitize HTML content for articles.
    
    Allows only safe tags and attributes for article content:
    - Tags: p, br, strong, em, h2, h3, h4, h5, h6, ul, ol, li, a, img
    - Attributes: 
      - Links: href, title, target
      - Images: src, alt, title, width, height
    
    V1 Scope: Basic formatting only
    Future enhancements: video embeds, tables, CTA blocks
    
    Args:
        html_content (str): Raw HTML content from editor
        
    Returns:
        str: Sanitized HTML content safe for display
    """
    if not html_content:
        return ''
    
    # Use bleach to sanitize
    cleaned = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True
    )
    
    # Additional validation for links and images
    cleaned = _validate_links(cleaned)
    cleaned = _validate_images(cleaned)
    
    return cleaned


def _validate_links(html_content):
    """
    Validate and sanitize links in HTML content.
    Removes links with invalid protocols or suspicious URLs.
    
    Args:
        html_content (str): HTML content with links
        
    Returns:
        str: HTML with validated links
    """
    from html.parser import HTMLParser
    
    class LinkValidator(HTMLParser):
        def __init__(self):
            super().__init__()
            self.result = []
            
        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                # Validate href attribute
                attrs_dict = dict(attrs)
                href = attrs_dict.get('href', '')
                
                # Check if URL is safe
                if not _is_safe_url(href):
                    # Remove href if unsafe
                    attrs = [(k, v) for k, v in attrs if k != 'href']
                
                # Reconstruct tag
                attr_str = ' '.join(f'{k}="{escape(v)}"' for k, v in attrs)
                if attr_str:
                    self.result.append(f'<{tag} {attr_str}>')
                else:
                    self.result.append(f'<{tag}>')
            else:
                # Other tags
                attr_str = ' '.join(f'{k}="{escape(v)}"' for k, v in attrs)
                if attr_str:
                    self.result.append(f'<{tag} {attr_str}>')
                else:
                    self.result.append(f'<{tag}>')
        
        def handle_endtag(self, tag):
            self.result.append(f'</{tag}>')
        
        def handle_data(self, data):
            self.result.append(escape(data))
        
        def get_result(self):
            return ''.join(self.result)
    
    try:
        parser = LinkValidator()
        parser.feed(html_content)
        return parser.get_result()
    except Exception:
        # If parsing fails, return original content
        return html_content


def _validate_images(html_content):
    """
    Validate and sanitize images in HTML content.
    Ensures images have alt text and valid src attributes.
    
    Args:
        html_content (str): HTML content with images
        
    Returns:
        str: HTML with validated images
    """
    from html.parser import HTMLParser
    
    class ImageValidator(HTMLParser):
        def __init__(self):
            super().__init__()
            self.result = []
            
        def handle_starttag(self, tag, attrs):
            if tag == 'img':
                attrs_dict = dict(attrs)
                src = attrs_dict.get('src', '')
                alt = attrs_dict.get('alt', '')
                
                # Validate src is not empty
                if not src:
                    # Skip image without src
                    return
                
                # Ensure alt text exists (accessibility requirement)
                if not alt:
                    attrs = [(k, v) for k, v in attrs]
                    attrs.append(('alt', ''))
                
                # Reconstruct tag
                attr_str = ' '.join(f'{k}="{escape(v)}"' for k, v in attrs)
                if attr_str:
                    self.result.append(f'<{tag} {attr_str}>')
                else:
                    self.result.append(f'<{tag}>')
            else:
                # Other tags
                attr_str = ' '.join(f'{k}="{escape(v)}"' for k, v in attrs)
                if attr_str:
                    self.result.append(f'<{tag} {attr_str}>')
                else:
                    self.result.append(f'<{tag}>')
        
        def handle_endtag(self, tag):
            self.result.append(f'</{tag}>')
        
        def handle_data(self, data):
            self.result.append(escape(data))
        
        def get_result(self):
            return ''.join(self.result)
    
    try:
        parser = ImageValidator()
        parser.feed(html_content)
        return parser.get_result()
    except Exception:
        # If parsing fails, return original content
        return html_content


def _is_safe_url(url):
    """
    Check if URL is safe and allowed.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is safe, False otherwise
    """
    if not url:
        return False
    
    # Allow relative URLs
    if url.startswith('/') or url.startswith('#'):
        return True
    
    # Allow mailto links
    if url.startswith('mailto:'):
        return True
    
    # Check protocol for absolute URLs
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # Check if protocol is allowed
        if parsed.scheme and parsed.scheme not in ALLOWED_PROTOCOLS:
            return False
        
        # Check for javascript: protocol
        if url.lower().startswith('javascript:'):
            return False
        
        # Check for data: protocol
        if url.lower().startswith('data:'):
            return False
        
        return True
    except Exception:
        return False


def get_safe_html(html_content):
    """
    Get sanitized HTML marked as safe for template rendering.
    
    Args:
        html_content (str): Raw HTML content
        
    Returns:
        SafeString: Sanitized HTML marked as safe
    """
    sanitized = sanitize_article_html(html_content)
    return mark_safe(sanitized)
