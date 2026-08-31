from django.test import TestCase, Client
from apps.majors.models import Major, MajorCategory
from apps.articles.models import Article, Category
from django.utils import timezone
import xml.etree.ElementTree as ET
from datetime import datetime


class SitemapAuditTests(TestCase):
    def setUp(self):
        from apps.seo.sitemaps import clear_sitemap_cache
        clear_sitemap_cache()
        self.client = Client()
        self.major_cat = MajorCategory.objects.create(
            name='هندسة',
            slug='engineering'
        )
        self.major = Major.objects.create(
            name='هندسة طيران',
            slug='aerospace-engineering',
            category=self.major_cat,
            publish_status='published',
            sitemap_include=True
        )

    def test_sitemap_xml_returns_200_valid_xml(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('<urlset', content)
        self.assertIn('<lastmod>', content)

    def test_sitemap_includes_legal_pages(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('/privacy/', content)
        self.assertIn('/terms/', content)

    def test_sitemap_includes_quality_gated_category_archives(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('/majors/category/engineering/', content)

    def test_sitemap_urls_are_indexable(self):
        sample_urls = ['/privacy/', '/terms/', '/about-us/', '/visa-tracking/']
        for url in sample_urls:
            resp = self.client.get(url, follow=True)
            self.assertEqual(resp.status_code, 200)
            content = resp.content.decode('utf-8').lower()
            self.assertNotIn('noindex', content)

    def test_lastmod_timestamps_not_in_future(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        tree = ET.fromstring(response.content)
        namespace = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        today = timezone.localdate()

        for lastmod_node in tree.findall('.//sm:lastmod', namespace):
            lastmod_str = lastmod_node.text
            lastmod_date = datetime.strptime(lastmod_str, '%Y-%m-%d').date()
            self.assertLessEqual(lastmod_date, today)

    def test_tag_pages_have_noindex_on_both_robots_and_googlebot(self):
        from apps.articles.models import Tag
        tag = Tag.objects.create(name='اختبار', slug='test-tag')
        response = self.client.get(f'/articles/tag/{tag.slug}/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('<meta name="robots" content="noindex, follow">', content)
        self.assertIn('<meta name="googlebot" content="noindex, follow">', content)
