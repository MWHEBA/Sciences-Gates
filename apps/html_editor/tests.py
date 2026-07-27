"""
Tests for HTML sanitizer for article content.
"""
from django.test import TestCase
from apps.html_editor.sanitizer import sanitize_article_html, get_safe_html


class SanitizeArticleHTMLTests(TestCase):
    """Test cases for sanitize_article_html function."""
    
    def test_empty_content(self):
        """Test that empty content returns empty string."""
        result = sanitize_article_html('')
        self.assertEqual(result, '')
        
        result = sanitize_article_html(None)
        self.assertEqual(result, '')
    
    def test_allowed_tags_preserved(self):
        """Test that allowed tags are preserved."""
        # Test paragraph
        html = '<p>This is a paragraph</p>'
        result = sanitize_article_html(html)
        self.assertIn('<p>This is a paragraph</p>', result)
        
        # Test bold
        html = '<strong>Bold text</strong>'
        result = sanitize_article_html(html)
        self.assertIn('<strong>Bold text</strong>', result)
        
        # Test italic
        html = '<em>Italic text</em>'
        result = sanitize_article_html(html)
        self.assertIn('<em>Italic text</em>', result)
        
        # Test headings
        for h in ['h2', 'h3', 'h4', 'h5', 'h6']:
            html = f'<{h}>Heading</{h}>'
            result = sanitize_article_html(html)
            self.assertIn(f'<{h}>Heading</{h}>', result)
        
        # Test lists
        html = '<ul><li>Item 1</li><li>Item 2</li></ul>'
        result = sanitize_article_html(html)
        self.assertIn('<ul>', result)
        self.assertIn('<li>Item 1</li>', result)
        
        # Test ordered list
        html = '<ol><li>First</li><li>Second</li></ol>'
        result = sanitize_article_html(html)
        self.assertIn('<ol>', result)
        self.assertIn('<li>First</li>', result)
        
        # Test line break
        html = 'Line 1<br>Line 2'
        result = sanitize_article_html(html)
        self.assertIn('<br>', result)
    
    def test_links_with_safe_urls(self):
        """Test that links with safe URLs are preserved."""
        # Test http link
        html = '<a href="http://example.com">Link</a>'
        result = sanitize_article_html(html)
        self.assertIn('href="http://example.com"', result)
        
        # Test https link
        html = '<a href="https://example.com">Link</a>'
        result = sanitize_article_html(html)
        self.assertIn('href="https://example.com"', result)
        
        # Test relative link
        html = '<a href="/articles/test">Link</a>'
        result = sanitize_article_html(html)
        self.assertIn('href="/articles/test"', result)
        
        # Test anchor link
        html = '<a href="#section">Link</a>'
        result = sanitize_article_html(html)
        self.assertIn('href="#section"', result)
        
        # Test mailto link
        html = '<a href="mailto:test@example.com">Email</a>'
        result = sanitize_article_html(html)
        self.assertIn('href="mailto:test@example.com"', result)
    
    def test_links_with_attributes(self):
        """Test that link attributes are preserved."""
        html = '<a href="http://example.com" title="Example" target="_blank">Link</a>'
        result = sanitize_article_html(html)
        self.assertIn('href="http://example.com"', result)
        self.assertIn('title="Example"', result)
        self.assertIn('target="_blank"', result)
    
    def test_images_with_safe_attributes(self):
        """Test that images with safe attributes are preserved."""
        html = '<img src="/media/image.jpg" alt="Test image">'
        result = sanitize_article_html(html)
        self.assertIn('src="/media/image.jpg"', result)
        self.assertIn('alt="Test image"', result)
        
        # Test with title
        html = '<img src="/media/image.jpg" alt="Test" title="Image title">'
        result = sanitize_article_html(html)
        self.assertIn('title="Image title"', result)
        
        # Test with dimensions
        html = '<img src="/media/image.jpg" alt="Test" width="300" height="200">'
        result = sanitize_article_html(html)
        self.assertIn('width="300"', result)
        self.assertIn('height="200"', result)
    
    def test_images_without_alt_text(self):
        """Test that images without alt text get empty alt attribute."""
        html = '<img src="/media/image.jpg">'
        result = sanitize_article_html(html)
        self.assertIn('src="/media/image.jpg"', result)
        self.assertIn('alt=""', result)
    
    def test_images_without_src_removed(self):
        """Test that images without src are removed."""
        html = '<img alt="No source">'
        result = sanitize_article_html(html)
        self.assertNotIn('<img', result)
    
    def test_dangerous_tags_removed(self):
        """Test that dangerous tags are removed."""
        # Test script tag
        html = '<p>Text</p><script>alert("XSS")</script>'
        result = sanitize_article_html(html)
        self.assertNotIn('<script>', result)
        # Script tag is removed, content is escaped
        self.assertNotIn('<script>', result)
        
        # Test iframe tag (not allowed in V1)
        html = '<iframe src="http://example.com"></iframe>'
        result = sanitize_article_html(html)
        self.assertNotIn('<iframe>', result)
        
        # Test video tag (not allowed in V1)
        html = '<video src="video.mp4"></video>'
        result = sanitize_article_html(html)
        self.assertNotIn('<video>', result)
        
        # Test table tag (allowed)
        html = '<table><tr><td>Cell</td></tr></table>'
        result = sanitize_article_html(html)
        self.assertIn('<table>', result)
        self.assertIn('<tr>', result)
        self.assertIn('<td>Cell</td>', result)
    
    def test_dangerous_attributes_removed(self):
        """Test that dangerous attributes are removed."""
        # Test onclick attribute
        html = '<p onclick="alert(\'XSS\')">Text</p>'
        result = sanitize_article_html(html)
        self.assertNotIn('onclick', result)
        
        # Test onerror attribute on image
        html = '<img src="/media/image.jpg" alt="Test" onerror="alert(\'XSS\')">'
        result = sanitize_article_html(html)
        self.assertNotIn('onerror', result)
    
    def test_javascript_protocol_removed(self):
        """Test that javascript: protocol is removed from links."""
        html = '<a href="javascript:alert(\'XSS\')">Click</a>'
        result = sanitize_article_html(html)
        # href should be removed or empty
        self.assertNotIn('javascript:', result)
    
    def test_data_protocol_removed(self):
        """Test that data: protocol is removed from links."""
        html = '<a href="data:text/html,<script>alert(\'XSS\')</script>">Click</a>'
        result = sanitize_article_html(html)
        self.assertNotIn('data:', result)
    
    def test_complex_article_content(self):
        """Test sanitization of complex article content."""
        html = '''
        <h2>Article Title</h2>
        <p>This is the <strong>first paragraph</strong> with <em>italic text</em>.</p>
        <h3>Section 1</h3>
        <p>Some content with a <a href="http://example.com">link</a>.</p>
        <ul>
            <li>List item 1</li>
            <li>List item 2</li>
        </ul>
        <img src="/media/image.jpg" alt="Article image">
        <p>Final paragraph.</p>
        '''
        result = sanitize_article_html(html)
        
        # Check that allowed content is preserved
        self.assertIn('<h2>Article Title</h2>', result)
        self.assertIn('<strong>first paragraph</strong>', result)
        self.assertIn('<em>italic text</em>', result)
        self.assertIn('href="http://example.com"', result)
        self.assertIn('<ul>', result)
        self.assertIn('<li>List item 1</li>', result)
        self.assertIn('src="/media/image.jpg"', result)
    
    def test_h1_tag_not_allowed(self):
        """Test that H1 tag is not allowed (only H2-H6)."""
        html = '<h1>Main Title</h1>'
        result = sanitize_article_html(html)
        self.assertNotIn('<h1>', result)
        # Content should be preserved but tag removed
        self.assertIn('Main Title', result)
    
    def test_comments_removed(self):
        """Test that HTML comments are removed."""
        html = '<p>Text</p><!-- This is a comment --><p>More text</p>'
        result = sanitize_article_html(html)
        self.assertNotIn('<!--', result)
        self.assertNotIn('This is a comment', result)
    
    def test_get_safe_html(self):
        """Test that get_safe_html returns SafeString."""
        html = '<p>Test content</p>'
        result = get_safe_html(html)
        
        # Check that result is marked as safe
        from django.utils.safestring import SafeString
        self.assertIsInstance(result, SafeString)
        self.assertIn('<p>Test content</p>', str(result))
    
    def test_nested_tags(self):
        """Test that nested tags are properly handled."""
        html = '<p>This is <strong><em>bold and italic</em></strong> text.</p>'
        result = sanitize_article_html(html)
        self.assertIn('<strong>', result)
        self.assertIn('<em>', result)
        self.assertIn('bold and italic', result)
    
    def test_mixed_content_with_xss_attempts(self):
        """Test that mixed content with XSS attempts is properly sanitized."""
        html = '''
        <p>Normal text</p>
        <img src="/media/image.jpg" alt="Image" onerror="alert('XSS')">
        <a href="javascript:void(0)">Click me</a>
        <script>alert('XSS')</script>
        <p>More text</p>
        '''
        result = sanitize_article_html(html)
        
        # Check that safe content is preserved
        self.assertIn('Normal text', result)
        self.assertIn('More text', result)
        
        # Check that dangerous content is removed
        self.assertNotIn('onerror', result)
        self.assertNotIn('javascript:', result)
        self.assertNotIn('<script>', result)

    def test_alignment_and_direction_attributes(self):
        """Test that alignment styles (text-align) and dir/align attributes are preserved on block elements."""
        html = '<p style="text-align: right;" dir="rtl">محتوى لليمين</p>'
        result = sanitize_article_html(html)
        self.assertIn('style="text-align: right;"', result)
        self.assertIn('dir="rtl"', result)

        html_h2 = '<h2 style="text-align: center;">عنوان رئيسي</h2>'
        result_h2 = sanitize_article_html(html_h2)
        self.assertIn('style="text-align: center;"', result_h2)

        html_align = '<div align="center">محتوى بالمنتصف</div>'
        result_align = sanitize_article_html(html_align)
        self.assertIn('align="center"', result_align)

        html_justify = '<p style="text-align: justify;">نص متباعد ومتساوي الحواف</p>'
        result_justify = sanitize_article_html(html_justify)
        self.assertIn('style="text-align: justify;"', result_justify)


