"""
Integration tests for SimpleRichTextWidget with forms and sanitization.
"""
from django.test import TestCase
from django import forms
from apps.core.widgets import SimpleRichTextWidget
from apps.core.sanitizer import sanitize_article_html


class TestForm(forms.Form):
    """Test form with SimpleRichTextWidget."""
    description = forms.CharField(
        widget=SimpleRichTextWidget(),
        required=False
    )
    content = forms.CharField(
        widget=SimpleRichTextWidget(attrs={'id': 'content-editor'}),
        required=False
    )


class SimpleRichTextWidgetIntegrationTestCase(TestCase):
    """Integration tests for SimpleRichTextWidget."""
    
    def test_form_submission_with_html(self):
        """Test form submission with HTML content."""
        data = {
            'description': '<p>Test <strong>content</strong></p>',
            'content': '<h2>Title</h2><p>Content</p>'
        }
        form = TestForm(data=data)
        
        # Form should be valid
        self.assertTrue(form.is_valid())
        
        # Check cleaned data
        self.assertEqual(
            form.cleaned_data['description'],
            '<p>Test <strong>content</strong></p>'
        )
    
    def test_form_submission_with_unsafe_html(self):
        """Test form submission with unsafe HTML."""
        data = {
            'description': '<p>Safe</p><script>alert("XSS")</script>',
            'content': '<p>Content</p><img src="x" onerror="alert(\'XSS\')">'
        }
        form = TestForm(data=data)
        
        # Form should be valid
        self.assertTrue(form.is_valid())
        
        # Check that unsafe content is preserved in form (sanitization happens on save)
        self.assertIn('<script>', form.cleaned_data['description'])
    
    def test_widget_media_in_form(self):
        """Test that widget media is included in form."""
        form = TestForm()
        media = form.media
        
        # Check CSS
        self.assertIn('simple-rich-text-editor.css', str(media))
        
        # Check JavaScript
        self.assertIn('simple-rich-text-editor.js', str(media))
    
    def test_sanitize_article_html_integration(self):
        """Test sanitize_article_html with form data."""
        # Simulate form submission with mixed content
        form_data = '<p>Article <strong>content</strong></p><script>alert("XSS")</script>'
        
        # Sanitize the data
        sanitized = sanitize_article_html(form_data)
        
        # Check that safe content is preserved
        self.assertIn('<p>Article', sanitized)
        self.assertIn('<strong>content</strong>', sanitized)
        
        # Check that unsafe content is removed
        self.assertNotIn('<script>', sanitized)
    
    def test_widget_with_arabic_content(self):
        """Test widget with Arabic content."""
        data = {
            'description': '<p>محتوى عربي <strong>غامق</strong></p>',
            'content': '<h2>عنوان</h2><p>محتوى</p>'
        }
        form = TestForm(data=data)
        
        # Form should be valid
        self.assertTrue(form.is_valid())
        
        # Check that Arabic content is preserved
        self.assertIn('محتوى عربي', form.cleaned_data['description'])
        self.assertIn('عنوان', form.cleaned_data['content'])
    
    def test_widget_with_links(self):
        """Test widget with links."""
        data = {
            'description': '<p>Check <a href="https://example.com">this link</a></p>',
            'content': '<p><a href="/about">About</a> and <a href="mailto:test@example.com">Email</a></p>'
        }
        form = TestForm(data=data)
        
        # Form should be valid
        self.assertTrue(form.is_valid())
        
        # Check that links are preserved
        self.assertIn('href="https://example.com"', form.cleaned_data['description'])
        self.assertIn('href="/about"', form.cleaned_data['content'])
        self.assertIn('mailto:test@example.com', form.cleaned_data['content'])
    
    def test_widget_with_lists(self):
        """Test widget with lists."""
        data = {
            'description': '<ul><li>Item 1</li><li>Item 2</li></ul>',
            'content': '<ol><li>First</li><li>Second</li></ol>'
        }
        form = TestForm(data=data)
        
        # Form should be valid
        self.assertTrue(form.is_valid())
        
        # Check that lists are preserved
        self.assertIn('<ul>', form.cleaned_data['description'])
        self.assertIn('<li>Item 1</li>', form.cleaned_data['description'])
        self.assertIn('<ol>', form.cleaned_data['content'])
        self.assertIn('<li>First</li>', form.cleaned_data['content'])
    
    def test_widget_with_headings(self):
        """Test widget with headings."""
        data = {
            'description': '<h2>Heading 2</h2><h3>Heading 3</h3><h4>Heading 4</h4>',
        }
        form = TestForm(data=data)
        
        # Form should be valid
        self.assertTrue(form.is_valid())
        
        # Check that headings are preserved
        self.assertIn('<h2>Heading 2</h2>', form.cleaned_data['description'])
        self.assertIn('<h3>Heading 3</h3>', form.cleaned_data['description'])
        self.assertIn('<h4>Heading 4</h4>', form.cleaned_data['description'])
    
    def test_widget_empty_submission(self):
        """Test widget with empty submission."""
        data = {
            'description': '',
            'content': ''
        }
        form = TestForm(data=data)
        
        # Form should be valid
        self.assertTrue(form.is_valid())
        
        # Check that empty values are preserved
        self.assertEqual(form.cleaned_data['description'], '')
        self.assertEqual(form.cleaned_data['content'], '')
    
    def test_widget_with_br_tags(self):
        """Test widget with br tags."""
        data = {
            'description': '<p>Line 1<br>Line 2<br>Line 3</p>',
        }
        form = TestForm(data=data)
        
        # Form should be valid
        self.assertTrue(form.is_valid())
        
        # Check that br tags are preserved
        self.assertIn('<br', form.cleaned_data['description'])
