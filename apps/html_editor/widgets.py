"""
Django form widgets for custom HTML editing.
Includes CustomHTMLEditorWidget for article content with basic formatting.

V1 Scope: Bold, Italic, H2-H4, UL, OL, Link, Image only
Future enhancements: Video embeds, tables, CTA blocks
"""
from django import forms
from django.utils.html import escape
from django.utils.safestring import mark_safe
import json


class CustomHTMLEditorWidget(forms.Textarea):
    """
    Custom HTML editor widget for article content.
    
    V1 Features:
    - Bold, Italic text formatting
    - Headings: H2, H3, H4
    - Lists: Unordered (UL), Ordered (OL)
    - Links: Insert and remove links
    - Images: Insert images with alt text
    
    Future enhancements:
    - Video embeds
    - Tables
    - CTA blocks
    
    Sanitizes output to allow only safe tags:
    p, br, strong, em, h2, h3, h4, ul, ol, li, a, img
    
    RTL Support: Full support for Arabic and RTL text
    """
    
    template_name = 'widgets/html_editor.html'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'html-editor-widget',
            'rows': 15,
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
    
    def get_context(self, name, value, attrs):
        """Get context for widget rendering."""
        context = super().get_context(name, value, attrs)
        context['widget']['template_name'] = self.template_name
        return context
    
    class Media:
        """Include CSS and JavaScript for the widget."""
        css = {
            'all': ('css/html_editor.css',)
        }
        js = ('js/html_editor.js',)
