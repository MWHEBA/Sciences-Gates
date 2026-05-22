"""
Django form widgets for custom HTML editing.
Includes CustomHTMLEditorWidget — a professional rich-text editor
with full RTL support, SVG toolbar icons, undo/redo, link modal,
word count, and keyboard shortcuts.
"""
from django import forms
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string


class CustomHTMLEditorWidget(forms.Widget):
    """
    Professional HTML editor widget for rich-text fields.

    Features:
    - Bold, Italic, Underline, Strikethrough
    - Headings: H2, H3, H4
    - Lists: Unordered (UL), Ordered (OL)
    - Blockquote
    - Link insertion with modal (URL, link text, open-in-new-tab)
    - Unlink
    - Undo / Redo
    - Clear formatting
    - Word count footer
    - Keyboard shortcuts: Ctrl+B/I/U/Z/Y/K
    - RTL-first design (Arabic)
    - Paste sanitization (strips unsafe tags/attributes)

    Allowed output tags:
        p, br, strong, em, u, s, h2, h3, h4, ul, ol, li, a, blockquote

    Usage in a ModelForm:
        from apps.html_editor.widgets import CustomHTMLEditorWidget

        class MyForm(forms.ModelForm):
            class Meta:
                widgets = {
                    'body': CustomHTMLEditorWidget(attrs={'data-placeholder': 'اكتب هنا...'}),
                }
    """

    template_name = 'widgets/html_editor.html'
    input_type = None  # Not a standard input element

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'pro-editor-mount',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget using the html_editor.html template."""
        final_attrs = self.build_attrs(self.attrs, attrs or {})
        # Ensure a stable id for the mount element
        if 'id' not in final_attrs:
            final_attrs['id'] = f'id_{name}'

        context = {
            'widget': {
                'name': name,
                'value': value or '',
                'attrs': final_attrs,
            }
        }
        return mark_safe(render_to_string(self.template_name, context))

    def value_from_datadict(self, data, files, name):
        """Read the submitted HTML value from POST data."""
        return data.get(name, '')

    class Media:
        css = {
            'all': ('css/html_editor.css',)
        }
        js = ('js/html_editor.js',)
