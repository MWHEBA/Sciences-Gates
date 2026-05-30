from django.test import TestCase
from django.urls import reverse

class AboutViewTestCase(TestCase):
    """
    Test cases for AboutView view and about-us page.
    """
    
    def test_about_us_page_loads_successfully(self):
        """Test that the about-us page loads successfully (returns 200)."""
        response = self.client.get(reverse('about_us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')
        
    def test_about_us_page_content(self):
        """Test that the about-us page displays correct company content."""
        response = self.client.get(reverse('about_us'))
        self.assertContains(response, 'بوابات العلوم')
        self.assertContains(response, 'Sciences Gates')
        self.assertContains(response, 'محمد كيالي')
        self.assertContains(response, 'دكتوراه علوم الحاسوب')
