"""
Tests for SimpleRichTextWidget and HTML sanitization.
"""
from django.test import TestCase
from django.forms import Form
from apps.core.widgets import SimpleRichTextWidget
from apps.core.sanitizer import (
    sanitize_html,
    sanitize_article_html,
    get_safe_html,
    _is_safe_url
)


class SimpleRichTextWidgetTestCase(TestCase):
    """Test SimpleRichTextWidget functionality."""
    
    def test_widget_initialization(self):
        """Test that widget initializes correctly."""
        widget = SimpleRichTextWidget()
        self.assertIsNotNone(widget)
        self.assertEqual(widget.template_name, 'widgets/simple_rich_text_editor.html')
    
    def test_widget_media_includes_css(self):
        """Test that widget includes CSS media."""
        widget = SimpleRichTextWidget()
        media = widget.media
        self.assertIn('css/simple-rich-text-editor.css', str(media))
    
    def test_widget_media_includes_js(self):
        """Test that widget includes JavaScript media."""
        widget = SimpleRichTextWidget()
        media = widget.media
        self.assertIn('js/simple-rich-text-editor.js', str(media))
    
    def test_widget_attrs(self):
        """Test that widget has correct default attributes."""
        widget = SimpleRichTextWidget()
        self.assertEqual(widget.attrs['class'], 'simple-rich-text-editor')
        self.assertEqual(widget.attrs['rows'], 10)
    
    def test_widget_custom_attrs(self):
        """Test that widget accepts custom attributes."""
        custom_attrs = {'id': 'my-editor', 'data-test': 'value'}
        widget = SimpleRichTextWidget(attrs=custom_attrs)
        self.assertEqual(widget.attrs['id'], 'my-editor')
        self.assertEqual(widget.attrs['data-test'], 'value')
        self.assertEqual(widget.attrs['class'], 'simple-rich-text-editor')


class HTMLSanitizationTestCase(TestCase):
    """Test HTML sanitization functionality."""
    
    def test_sanitize_empty_content(self):
        """Test sanitizing empty content."""
        result = sanitize_html('')
        self.assertEqual(result, '')
    
    def test_sanitize_none_content(self):
        """Test sanitizing None content."""
        result = sanitize_html(None)
        self.assertEqual(result, '')
    
    def test_sanitize_plain_text(self):
        """Test sanitizing plain text."""
        text = 'This is plain text'
        result = sanitize_html(text)
        self.assertEqual(result, text)
    
    def test_sanitize_allowed_tags(self):
        """Test that allowed tags are preserved."""
        html = '<p>This is <strong>bold</strong> and <em>italic</em></p>'
        result = sanitize_html(html)
        self.assertIn('<strong>bold</strong>', result)
        self.assertIn('<em>italic</em>', result)
    
    def test_sanitize_headings(self):
        """Test that heading tags are preserved."""
        html = '<h2>Heading 2</h2><h3>Heading 3</h3><h4>Heading 4</h4>'
        result = sanitize_html(html)
        self.assertIn('<h2>Heading 2</h2>', result)
        self.assertIn('<h3>Heading 3</h3>', result)
        self.assertIn('<h4>Heading 4</h4>', result)
    
    def test_sanitize_lists(self):
        """Test that list tags are preserved."""
        html = '<ul><li>Item 1</li><li>Item 2</li></ul>'
        result = sanitize_html(html)
        self.assertIn('<ul>', result)
        self.assertIn('<li>Item 1</li>', result)
        self.assertIn('</ul>', result)
    
    def test_sanitize_links(self):
        """Test that safe links are preserved."""
        html = '<a href="https://example.com">Link</a>'
        result = sanitize_html(html)
        self.assertIn('href="https://example.com"', result)
        self.assertIn('Link</a>', result)
    
    def test_sanitize_removes_script_tags(self):
        """Test that script tags are removed."""
        html = '<p>Text</p><script>alert("XSS")</script>'
        result = sanitize_html(html)
        self.assertNotIn('<script>', result)
    
    def test_sanitize_removes_onclick(self):
        """Test that onclick attributes are removed."""
        html = '<p onclick="alert(\'XSS\')">Click me</p>'
        result = sanitize_html(html)
        self.assertNotIn('onclick', result)
    
    def test_sanitize_removes_style_tags(self):
        """Test that style tags are removed."""
        html = '<p>Text</p><style>body { display: none; }</style>'
        result = sanitize_html(html)
        self.assertNotIn('<style>', result)
    
    def test_sanitize_removes_disallowed_tags(self):
        """Test that disallowed tags are removed."""
        html = '<p>Text</p><div>Div content</div><span>Span</span>'
        result = sanitize_html(html)
        self.assertNotIn('<div>', result)
        self.assertNotIn('<span>', result)
    
    def test_sanitize_javascript_protocol(self):
        """Test that javascript: protocol is removed."""
        html = '<a href="javascript:alert(\'XSS\')">Click</a>'
        result = sanitize_html(html)
        self.assertNotIn('javascript:', result)
    
    def test_sanitize_data_protocol(self):
        """Test that data: protocol is removed."""
        html = '<a href="data:text/html,<script>alert(\'XSS\')</script>">Click</a>'
        result = sanitize_html(html)
        self.assertNotIn('data:', result)
    
    def test_sanitize_preserves_relative_urls(self):
        """Test that relative URLs are preserved."""
        html = '<a href="/about">About</a>'
        result = sanitize_html(html)
        self.assertIn('href="/about"', result)
    
    def test_sanitize_preserves_mailto(self):
        """Test that mailto links are preserved."""
        html = '<a href="mailto:test@example.com">Email</a>'
        result = sanitize_html(html)
        self.assertIn('mailto:test@example.com', result)
    
    def test_sanitize_article_html(self):
        """Test sanitize_article_html function."""
        html = '<p>Article <strong>content</strong></p><script>alert("XSS")</script>'
        result = sanitize_article_html(html)
        self.assertIn('<strong>content</strong>', result)
        self.assertNotIn('<script>', result)
    
    def test_get_safe_html(self):
        """Test get_safe_html returns SafeString."""
        html = '<p>Safe <strong>content</strong></p>'
        result = get_safe_html(html)
        # Check that result is marked as safe
        self.assertTrue(hasattr(result, '__html__'))


class URLValidationTestCase(TestCase):
    """Test URL validation for links."""
    
    def test_is_safe_url_empty(self):
        """Test that empty URL is not safe."""
        self.assertFalse(_is_safe_url(''))
    
    def test_is_safe_url_none(self):
        """Test that None URL is not safe."""
        self.assertFalse(_is_safe_url(None))
    
    def test_is_safe_url_relative(self):
        """Test that relative URLs are safe."""
        self.assertTrue(_is_safe_url('/about'))
        self.assertTrue(_is_safe_url('/page/123'))
    
    def test_is_safe_url_hash(self):
        """Test that hash URLs are safe."""
        self.assertTrue(_is_safe_url('#section'))
    
    def test_is_safe_url_http(self):
        """Test that HTTP URLs are safe."""
        self.assertTrue(_is_safe_url('http://example.com'))
    
    def test_is_safe_url_https(self):
        """Test that HTTPS URLs are safe."""
        self.assertTrue(_is_safe_url('https://example.com'))
    
    def test_is_safe_url_mailto(self):
        """Test that mailto URLs are safe."""
        self.assertTrue(_is_safe_url('mailto:test@example.com'))
    
    def test_is_safe_url_javascript(self):
        """Test that javascript: URLs are not safe."""
        self.assertFalse(_is_safe_url('javascript:alert("XSS")'))
    
    def test_is_safe_url_data(self):
        """Test that data: URLs are not safe."""
        self.assertFalse(_is_safe_url('data:text/html,<script>alert("XSS")</script>'))
    
    def test_is_safe_url_vbscript(self):
        """Test that vbscript: URLs are not safe."""
        self.assertFalse(_is_safe_url('vbscript:alert("XSS")'))


class ComplexHTMLSanitizationTestCase(TestCase):
    """Test complex HTML sanitization scenarios."""
    
    def test_sanitize_complex_article(self):
        """Test sanitizing complex article content."""
        html = '''
        <h2>Article Title</h2>
        <p>Introduction paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
        <h3>Section 1</h3>
        <p>Content with <a href="https://example.com">link</a>.</p>
        <ul>
            <li>List item 1</li>
            <li>List item 2</li>
        </ul>
        <h4>Subsection</h4>
        <ol>
            <li>Numbered item 1</li>
            <li>Numbered item 2</li>
        </ol>
        '''
        result = sanitize_html(html)
        
        # Check that allowed content is preserved
        self.assertIn('<h2>Article Title</h2>', result)
        self.assertIn('<strong>bold</strong>', result)
        self.assertIn('<em>italic</em>', result)
        self.assertIn('href="https://example.com"', result)
        self.assertIn('<ul>', result)
        self.assertIn('<ol>', result)
    
    def test_sanitize_mixed_safe_unsafe(self):
        """Test sanitizing mixed safe and unsafe content."""
        html = '''
        <p>Safe paragraph</p>
        <script>alert("XSS")</script>
        <p>Another safe paragraph with <strong>bold</strong></p>
        <img src="x" onerror="alert('XSS')">
        <a href="javascript:alert('XSS')">Click</a>
        '''
        result = sanitize_html(html)
        
        # Check safe content is preserved
        self.assertIn('Safe paragraph', result)
        self.assertIn('<strong>bold</strong>', result)
        
        # Check unsafe content is removed
        self.assertNotIn('<script>', result)
        self.assertNotIn('onerror', result)
        self.assertNotIn('javascript:', result)
    
    def test_sanitize_arabic_content(self):
        """Test sanitizing Arabic content."""
        html = '<p>محتوى عربي <strong>غامق</strong> و<em>مائل</em></p>'
        result = sanitize_html(html)
        
        self.assertIn('محتوى عربي', result)
        self.assertIn('<strong>غامق</strong>', result)
        self.assertIn('<em>مائل</em>', result)
    
    def test_sanitize_preserves_br_tags(self):
        """Test that br tags are preserved."""
        html = '<p>Line 1<br>Line 2<br>Line 3</p>'
        result = sanitize_html(html)
        
        self.assertIn('<br', result)
