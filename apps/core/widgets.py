"""
Django form widgets for rich text editing.
Includes SimpleRichTextWidget for structured editors with basic formatting.
"""
from django import forms
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.forms.widgets import Widget
from django.template.loader import render_to_string
import json


class SimpleRichTextWidget(Widget):
    """
    Simple rich text editor widget for structured editors.
    Supports: Bold, Italic, H2, H3, H4, UL, OL, Link
    Sanitizes output to allow only: p, br, strong, em, h2, h3, h4, ul, ol, li, a
    """
    
    template_name = 'widgets/simple_rich_text_editor.html'
    input_type = 'hidden'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'simple-rich-text-editor',
            'rows': 10,
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget using the template."""
        if attrs is None:
            attrs = {}
        
        # Merge default attrs with provided attrs
        final_attrs = self.build_attrs(attrs, {'name': name})
        
        context = {
            'widget': {
                'name': name,
                'value': value or '',
                'attrs': final_attrs,
                'template_name': self.template_name,
            }
        }
        
        return mark_safe(render_to_string(self.template_name, context))
    
    class Media:
        """Include CSS and JavaScript for the widget."""
        css = {
            'all': ('css/simple-rich-text-editor.css',)
        }
        js = ('js/simple-rich-text-editor.js',)
