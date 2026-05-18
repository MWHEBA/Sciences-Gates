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
