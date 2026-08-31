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
        self.assertContains(response, 'شركة بوابات العلوم')
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

    def test_build_curated_list_with_append_remaining(self):
        """Test that build_curated_list_with_dedup_fallback returns all items when append_remaining=True."""
        from apps.core.navigation import build_curated_list_with_dedup_fallback
        from apps.universities.models import University
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create dummy image
        img = SimpleUploadedFile("test.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82", content_type="image/png")
        
        univs = []
        for i in range(12):
            univ = University.objects.create(
                name=f'University {i+1:02d}',
                slug=f'univ-{i+1:02d}',
                university_type='public',
                publish_status='published',
                order=i+1,
                logo=img,
                main_image=img,
                description='Test Description',
                location='kl',
            )
            univs.append(univ)

        pool = University.objects.filter(publish_status='published', university_type='public').order_by('order', 'name')
        
        # Test without append_remaining (should return exactly 8)
        limited_list = build_curated_list_with_dedup_fallback({}, pool, total_needed=8, append_remaining=False)
        self.assertEqual(len(limited_list), 8)

        # Test with append_remaining (should return all 12)
        full_list = build_curated_list_with_dedup_fallback({}, pool, total_needed=8, append_remaining=True)
        self.assertEqual(len(full_list), 12)


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


class CsrfFailureHandlerTestCase(TestCase):
    """
    اختبارات دالة التعامل مع فشل رمز الحماية csrf_failure
    """

    def test_public_visitor_csrf_failure_redirects_to_referer_not_dashboard_login(self):
        """التحقق من عدم تحويل الزائر العام إلى لوحة التحكم عند فشل CSRF وإنما توجيهه لصفحته السابقة"""
        from apps.core.views import csrf_failure
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post('/leads/submit/', data={'source_page': '/universities/ukm/'})
        request.META['HTTP_REFERER'] = 'https://sciencesgates.com/universities/ukm/'
        
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

        response = csrf_failure(request)
        self.assertEqual(response.status_code, 302)
        # يجب ألا يوجه الزائر لصفحة دخول الأدمن نهائياً
        self.assertNotIn('/dashboard/login/', response.url)
        self.assertNotIn('/sg/login/', response.url)
        self.assertEqual(response.url, '/universities/ukm/')

    def test_ajax_csrf_failure_returns_json_403(self):
        """التحقق من إرجاع استجابة JSON 403 عند فشل CSRF في طلبات AJAX"""
        from apps.core.views import csrf_failure
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post('/leads/submit/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

        response = csrf_failure(request)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('csrf_error', response.content.decode('utf-8'))

    def test_dashboard_csrf_failure_redirects_to_dashboard_login(self):
        """التحقق من توجيه مسؤول النظام إلى صفحة تسجيل دخول الأدمن إذا فشل CSRF أثناء التواجد باللوحة"""
        from apps.core.views import csrf_failure
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post('/sg/login/')
        request.META['HTTP_REFERER'] = 'https://sciencesgates.com/sg/login/'
        
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

        response = csrf_failure(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:login'))

    def test_absolute_source_page_csrf_failure_redirects_to_source_page(self):
        """التحقق من دعم الروابط الكاملة في source_page والتوجيه إليها بدلاً من الرئيسية"""
        from apps.core.views import csrf_failure
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.post('/leads/submit/', data={'source_page': 'https://sciencesgates.com/leads/submit/'})
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        request.user = AnonymousUser()

        response = csrf_failure(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://sciencesgates.com/leads/submit/')

    def test_missing_referer_and_source_page_falls_back_to_request_path(self):
        """التحقق من التوجيه التلقائي إلى مسار الطلب الحالي عند غياب source_page والـ Referer"""
        from apps.core.views import csrf_failure
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.post('/leads/submit/', data={})
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        request.user = AnonymousUser()

        response = csrf_failure(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/leads/submit/')

    def test_malicious_open_redirect_source_page_rejected(self):
        """التحقق من رفض الروابط الخارجية الخبيثة والتوجيه لمسار الصفحة الآمنة"""
        from apps.core.views import csrf_failure
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.post('/leads/submit/', data={'source_page': 'https://malicious-phishing-site.com/steal'})
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        request.user = AnonymousUser()

        response = csrf_failure(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/leads/submit/')





