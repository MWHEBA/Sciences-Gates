from django.test import TestCase
from django.urls import reverse
from apps.leads.models import Lead


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


from django.test import override_settings

@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake-cache-test',
    }
})
class VisaTrackingViewTestCase(TestCase):
    """
    اختبارات صفحة متابعة الفيزا ونموذج طلب المساعدة
    """
    def setUp(self):
        from django.core.cache import cache
        cache.clear()


    def test_visa_tracking_page_loads_successfully(self):
        """التحقق من تحميل صفحة تتبع الفيزا بنجاح مع القالب الصحيح"""
        response = self.client.get(reverse('visa_tracking'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'visa_tracking.html')
        self.assertContains(response, 'متابعة حالة التأشيرة')
        self.assertContains(response, 'EMGS')

    def test_visa_tracking_form_submission_success(self):
        """التحقق من إرسال نموذج المساعدة بنجاح وحفظه كـ Lead"""
        url = reverse('visa_tracking')
        form_data = {
            'lead_type': 'contact',
            'name': 'أحمد علي',
            'email': 'ahmed.ali@example.com',
            'phone': '+201234567890',
            'nationality': 'مصر',
            'message': 'أريد مساعدة في تتبع طلبي الموقف عند 35%',
            'website': '',  # حقل الهوني بوت فارغ
        }
        
        response = self.client.post(url, data=form_data)
        
        # التحقق من إعادة التوجيه للصفحة نفسها بعد الإرسال الناجح
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, url)
        
        # التحقق من تخزين البيانات في الداتا بيز
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.name, 'أحمد علي')
        self.assertEqual(lead.email, 'ahmed.ali@example.com')
        self.assertEqual(lead.phone, '+201234567890')
        self.assertIn('[طلب مساعدة في تتبع الفيزا - EMGS]', lead.message)
        self.assertIn('أريد مساعدة في تتبع طلبي الموقف عند 35%', lead.message)
        self.assertIn('visa-tracking', lead.source_page)

    def test_visa_tracking_form_submission_honeypot_spam(self):
        """التحقق من رفض الفورم إذا تم ملء حقل الهوني بوت (سبام)"""
        url = reverse('visa_tracking')
        form_data = {
            'lead_type': 'contact',
            'name': 'سبامر',
            'email': 'spam@example.com',
            'phone': '+201234567890',
            'nationality': 'مصر',
            'message': 'رسالة سبام',
            'website': 'http://spambot.com',  # حقل الهوني بوت مملوء
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)


