from django.test import TestCase, Client
from django.conf import settings


class TechnicalSEORegressionTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_ai_bot_policy_in_robots_txt(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Allowed discovery bots
        self.assertIn("User-agent: ChatGPT-User\nAllow: /", content)
        self.assertIn("User-agent: ClaudeBot\nAllow: /", content)
        self.assertIn("User-agent: Google-Extended\nAllow: /", content)
        self.assertIn("User-agent: PerplexityBot\nAllow: /", content)

        # Blocked scrapers
        self.assertIn("User-agent: GPTBot\nDisallow: /", content)
        self.assertIn("User-agent: CCBot\nDisallow: /", content)
        self.assertIn("User-agent: Bytespider\nDisallow: /", content)

    def test_specific_bots_retain_admin_disallows(self):
        response = self.client.get('/robots.txt')
        content = response.content.decode('utf-8')
        admin_url = settings.ADMIN_URL.strip('/')
        self.assertIn(f"Disallow: /{admin_url}/", content)
        self.assertIn("Disallow: /api/", content)

    def test_no_deprecated_crawl_delay(self):
        response = self.client.get('/robots.txt')
        content = response.content.decode('utf-8')
        self.assertNotIn("Crawl-delay", content)

    def test_robots_declares_sitemap(self):
        response = self.client.get('/robots.txt')
        content = response.content.decode('utf-8')
        self.assertIn("Sitemap:", content)

    def test_indexnow_key_file_endpoint(self):
        key = getattr(settings, 'INDEXNOW_KEY', 'c7a8b9f0e1d2c3b4a5f6e7d8c9b0a1f2')
        response = self.client.get(f'/{key}.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8').strip(), key)
