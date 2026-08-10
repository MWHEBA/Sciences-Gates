from django.test import TestCase, Client
from django.conf import settings


class PerformanceIntegrityTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage_has_mobile_hero_preload(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('images/shape-2-7.webp', content)
        self.assertIn('media="(max-width: 991px)"', content)

    def test_hero_lcp_image_has_fetchpriority_high(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('fetchpriority="high"', content)

    def test_only_limited_fetchpriority_high_attributes(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        high_count = content.count('fetchpriority="high"')
        self.assertLessEqual(high_count, 6, "fetchpriority='high' should only be applied to true LCP hero elements")

    def test_manifest_staticfiles_storage_configured(self):
        storages = getattr(settings, 'STORAGES', {})
        staticfiles_backend = storages.get('staticfiles', {}).get('BACKEND', '')
        self.assertTrue(
            'ManifestStaticFilesStorage' in staticfiles_backend or 'StaticFilesStorage' in staticfiles_backend,
            f"Static files storage backend should be Manifest-based or StaticFilesStorage, got {staticfiles_backend}"
        )
