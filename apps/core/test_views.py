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


class MegaMenuContextTestCase(TestCase):
    """
    Test cases for mega_menu_context context processor.
    """
    
    def test_mega_menu_context_returns_expected_keys(self):
        """Test that mega_menu_context returns the correct context keys."""
        from django.test import RequestFactory
        from apps.core.context_processors import mega_menu_context
        from django.test import override_settings
        
        factory = RequestFactory()
        request = factory.get('/')
        
        # Override TESTING to False to let it execute queries
        with override_settings(TESTING=False):
            context = mega_menu_context(request)
            self.assertIn('menu_public_univs', context)
            self.assertIn('menu_private_univs', context)
            self.assertIn('menu_institutes', context)
            self.assertIn('menu_major_categories', context)
