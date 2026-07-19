"""
Template tags for advanced image optimization and serving.
Provides utilities for serving WebP images with fallback to original format.
Includes lazy loading support with intersection observer fallback.
"""
import os
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def webp_url(image_url):
    """
    Convert image URL to WebP version URL.
    
    Usage in template:
        {{ image.url|webp_url }}
    
    Args:
        image_url: URL of the original image
        
    Returns:
        str: URL of the WebP version
    """
    if not image_url:
        return ''
    
    base_url = os.path.splitext(str(image_url))[0]
    return f'{base_url}.webp'


@register.simple_tag
def responsive_image(image_url, alt_text='', css_class='', loading='lazy', placeholder=True):
    """
    Generate a responsive image tag with WebP support and fallback.
    Includes lazy loading with intersection observer support.
    
    Usage in template:
        {% responsive_image image.url "Alt text" "w-full h-auto" %}
        {% responsive_image image.url "Alt text" "w-full h-auto" "eager" %}
        {% responsive_image image.url "Alt text" "w-full h-auto" "lazy" False %}
    
    Args:
        image_url: URL of the original image
        alt_text: Alt text for accessibility
        css_class: CSS classes to apply to the img tag
        loading: Loading strategy ('lazy' or 'eager')
        placeholder: Whether to add placeholder support (default: True)
        
    Returns:
        str: HTML picture element with WebP and fallback
    """
    if not image_url:
        return ''
    
    webp_url_value = os.path.splitext(str(image_url))[0] + '.webp'
    
    # Add placeholder class if lazy loading is enabled
    placeholder_class = 'lazy-placeholder' if loading == 'lazy' and placeholder else ''
    combined_class = f'{css_class} {placeholder_class}'.strip()
    
    html = f'''<picture>
    <source srcset="{webp_url_value}" type="image/webp">
    <img src="{image_url}" alt="{alt_text}" class="{combined_class}" loading="{loading}">
</picture>'''
    
    return mark_safe(html)


@register.simple_tag
def responsive_image_with_sizes(image_url, alt_text='', sizes='', css_class='', loading='lazy', placeholder=True):
    """
    Generate a responsive image tag with WebP support, sizes attribute, and fallback.
    Includes lazy loading with intersection observer support.
    
    Usage in template:
        {% responsive_image_with_sizes image.url "Alt text" "(max-width: 768px) 100vw, 50vw" "w-full" %}
    
    Args:
        image_url: URL of the original image
        alt_text: Alt text for accessibility
        sizes: CSS media query sizes for responsive images
        css_class: CSS classes to apply to the img tag
        loading: Loading strategy ('lazy' or 'eager')
        placeholder: Whether to add placeholder support (default: True)
        
    Returns:
        str: HTML picture element with WebP, sizes, and fallback
    """
    if not image_url:
        return ''
    
    webp_url_value = os.path.splitext(str(image_url))[0] + '.webp'
    sizes_attr = f'sizes="{sizes}"' if sizes else ''
    
    # Add placeholder class if lazy loading is enabled
    placeholder_class = 'lazy-placeholder' if loading == 'lazy' and placeholder else ''
    combined_class = f'{css_class} {placeholder_class}'.strip()
    
    html = f'''<picture>
    <source srcset="{webp_url_value}" type="image/webp" {sizes_attr}>
    <img src="{image_url}" alt="{alt_text}" class="{combined_class}" loading="{loading}" {sizes_attr}>
</picture>'''
    
    return mark_safe(html)


@register.simple_tag
def image_with_fallback(image_url, alt_text='', css_class='', loading='lazy', placeholder=True):
    """
    Generate an img tag with WebP fallback using picture element.
    Simpler version of responsive_image for basic use cases.
    Includes lazy loading support.
    
    Usage in template:
        {% image_with_fallback image.url "Alt text" "w-full h-auto" %}
    
    Args:
        image_url: URL of the original image
        alt_text: Alt text for accessibility
        css_class: CSS classes to apply to the img tag
        loading: Loading strategy ('lazy' or 'eager')
        placeholder: Whether to add placeholder support (default: True)
        
    Returns:
        str: HTML picture element with WebP and fallback
    """
    return responsive_image(image_url, alt_text, css_class, loading, placeholder)


@register.simple_tag
def lazy_image(image_url, alt_text='', css_class='', placeholder=True):
    """
    Generate a lazy-loaded image tag with WebP support.
    Convenience function for lazy loading images.
    
    Usage in template:
        {% lazy_image image.url "Alt text" "w-full h-auto" %}
    
    Args:
        image_url: URL of the original image
        alt_text: Alt text for accessibility
        css_class: CSS classes to apply to the img tag
        placeholder: Whether to add placeholder support (default: True)
        
    Returns:
        str: HTML picture element with lazy loading
    """
    return responsive_image(image_url, alt_text, css_class, 'lazy', placeholder)


@register.simple_tag
def eager_image(image_url, alt_text='', css_class=''):
    """
    Generate an eagerly-loaded image tag with WebP support.
    Use for above-the-fold images that should load immediately.
    
    Usage in template:
        {% eager_image image.url "Alt text" "w-full h-auto" %}
    
    Args:
        image_url: URL of the original image
        alt_text: Alt text for accessibility
        css_class: CSS classes to apply to the img tag
        
    Returns:
        str: HTML picture element with eager loading
    """
    return responsive_image(image_url, alt_text, css_class, 'eager', False)


@register.simple_tag
def seo_image(image_url, alt_text='', caption='', width=None, height=None, css_class='', loading='lazy'):
    """
    Generate an SEO-optimized image with Schema.org ImageObject markup.
    Follows 2026 best practices including structured data and proper attributes.
    
    Usage in template:
        {% seo_image media.file.url media.alt_text media.caption media.width media.height "w-full" %}
        {% load image_tags %}
        {% seo_image university.main_image.url university.main_image_alt "" 800 600 %}
    
    Args:
        image_url: URL of the image
        alt_text: Alt text for accessibility and SEO (required for best SEO)
        caption: Caption text visible to users (optional but recommended)
        width: Image width in pixels (improves CLS)
        height: Image height in pixels (improves CLS)
        css_class: CSS classes to apply
        loading: Loading strategy ('lazy' or 'eager')
        
    Returns:
        str: HTML figure element with Schema.org markup
    """
    if not image_url:
        return ''
    
    webp_url_value = os.path.splitext(str(image_url))[0] + '.webp'
    
    # Dimension attributes for better CLS (Core Web Vitals)
    dimensions = ''
    if width and height:
        dimensions = f'width="{width}" height="{height}"'
    
    # Build the HTML with Schema.org markup
    if caption:
        # With caption - full figure element with Schema markup
        html = f'''<figure itemscope itemtype="https://schema.org/ImageObject" class="seo-image-figure">
    <picture>
        <source srcset="{webp_url_value}" type="image/webp">
        <img src="{image_url}" 
             alt="{alt_text}" 
             class="{css_class}" 
             loading="{loading}"
             {dimensions}
             itemprop="contentUrl">
    </picture>
    <figcaption itemprop="caption" class="seo-image-caption">{caption}</figcaption>
</figure>'''
    else:
        # Without caption - just picture with Schema markup on img
        html = f'''<picture itemscope itemtype="https://schema.org/ImageObject">
    <source srcset="{webp_url_value}" type="image/webp">
    <img src="{image_url}" 
         alt="{alt_text}" 
         class="{css_class}" 
         loading="{loading}"
         {dimensions}
         itemprop="contentUrl">
</picture>'''
    
    return mark_safe(html)


@register.simple_tag
def media_file_image(media_file, css_class='', loading='lazy'):
    """
    Generate SEO-optimized image HTML from MediaFile instance.
    Automatically uses all SEO fields (alt_text, caption, dimensions).
    
    Usage in template:
        {% media_file_image media_obj "w-full rounded-lg" %}
        {% load image_tags %}
        {% media_file_image article.featured_image_mediafile %}
    
    Args:
        media_file: MediaFile model instance
        css_class: CSS classes to apply
        loading: Loading strategy ('lazy' or 'eager')
        
    Returns:
        str: HTML with full SEO optimization
    """
    if not media_file or not media_file.file:
        return ''
    
    return seo_image(
        image_url=media_file.file.url,
        alt_text=media_file.alt_text or media_file.original_filename,
        caption=media_file.caption or '',
        width=media_file.width,
        height=media_file.height,
        css_class=css_class,
        loading=loading
    )


@register.filter
def thumbnail_url(image_url, size_str):
    """
    Generate or retrieve a thumbnail URL for the given image URL and size.
    Size string format: 'widthxheight' (e.g. '360x240').
    Saves the thumbnail as compressed WebP.
    """
    if not image_url:
        return ''
    
    import urllib.parse
    from django.conf import settings
    
    try:
        # Parse width and height
        width, height = map(int, size_str.split('x'))
    except ValueError:
        return image_url # Return original if invalid size format
        
    # Standardize image url
    parsed_url = urllib.parse.urlparse(str(image_url))
    url_path = parsed_url.path
    
    # Check if URL starts with MEDIA_URL
    media_url = settings.MEDIA_URL
    if not url_path.startswith(media_url):
        return image_url # Not a media file, return original
        
    # Get relative path from media url
    rel_path = url_path[len(media_url):]
    # Ensure safe path join by stripping leading slashes
    rel_path_clean = rel_path.lstrip('/')
    source_file_path = os.path.join(settings.MEDIA_ROOT, rel_path_clean)
    
    if not os.path.exists(source_file_path):
        return image_url # Original file not found
        
    # Define cache directory and thumbnail path
    cache_dir_rel = os.path.join('cache', 'thumbnails', os.path.dirname(rel_path_clean))
    cache_dir_abs = os.path.join(settings.MEDIA_ROOT, cache_dir_rel)
    
    # Filename with size and webp extension
    base_name = os.path.splitext(os.path.basename(rel_path_clean))[0]
    thumb_name = f"{base_name}_{size_str}.webp"
    thumb_file_path = os.path.join(cache_dir_abs, thumb_name)
    
    # Clean URL building for the response
    thumb_url_rel = os.path.join(cache_dir_rel, thumb_name).replace('\\', '/')
    thumb_url = urllib.parse.urljoin(media_url, thumb_url_rel)
    
    # If thumbnail exists, return it
    if os.path.exists(thumb_file_path):
        return thumb_url
        
    # Otherwise, generate the thumbnail
    try:
        from PIL import Image
        os.makedirs(cache_dir_abs, exist_ok=True)
        img = Image.open(source_file_path)
        
        # Convert to RGB if in RGBA mode for JPEG/WebP compatibility
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                # Convert palette to RGBA to merge transparent color properly
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[3]) # 3 is alpha channel
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Crop and resize to match the target aspect ratio
        img_ratio = img.width / img.height
        target_ratio = width / height
        
        if img_ratio > target_ratio:
            # Source is wider than target
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # Source is taller than target
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))
            
        # Resize using Lanczos resampling
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # Save as optimized WebP
        img.save(thumb_file_path, 'WEBP', quality=60)
        return thumb_url
    except Exception as e:
        # Log to console and fail gracefully by returning original url
        print(f"Error generating thumbnail for {source_file_path}: {e}")
        return image_url
