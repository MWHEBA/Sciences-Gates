"""
Tests for GeneralFAQ model, caching signals, sanitization, and data provider.
"""
from django.test import TestCase
from django.core.cache import cache
from apps.core.models import GeneralFAQ
from apps.core.faq_data import get_all_faqs, get_faq_categories, get_featured_faqs


class GeneralFAQModelTestCase(TestCase):
    def setUp(self):
        cache.clear()
        GeneralFAQ.objects.all().delete()

    def test_create_general_faq_with_auto_slug(self):
        faq = GeneralFAQ.objects.create(
            question="ما هي شروط القبول؟",
            answer="الشروط تشمل الثانوية العامة.",
            category="admissions",
            order=1,
            is_published=True
        )
        self.assertTrue(faq.slug.startswith("faq-admissions-"))
        self.assertEqual(str(faq), "ما هي شروط القبول؟")

    def test_custom_slug_and_html_sanitization(self):
        faq = GeneralFAQ.objects.create(
            question="ما هي تكاليف الدراسة؟",
            slug="costs-overview",
            answer='<p>تكلفة دراسة الطب <bdi>15,000$</bdi> سنوياً <script>alert("hack")</script></p>',
            category="costs",
            order=2,
            is_published=True
        )
        self.assertEqual(faq.slug, "costs-overview")
        # Ensure script tag is sanitized and bdi is kept
        self.assertNotIn('<script>', faq.answer)
        self.assertIn('<bdi>15,000$</bdi>', faq.answer)

    def test_signals_invalidate_cache_on_save_and_delete(self):
        cache.set('global_faqs_published_all', ['fake_cache'])
        cache.set('global_faqs_home_featured', ['fake_featured'])

        faq = GeneralFAQ.objects.create(
            question="سؤال تجريبي",
            slug="test-faq",
            answer="إجابة تجريبية",
            category="services",
            order=1,
            is_published=True
        )
        self.assertIsNone(cache.get('global_faqs_published_all'))
        self.assertIsNone(cache.get('global_faqs_home_featured'))

        # Set cache again and test deletion invalidation
        cache.set('global_faqs_published_all', ['fake_cache'])
        faq.delete()
        self.assertIsNone(cache.get('global_faqs_published_all'))

    def test_faq_data_provider_integration(self):
        faq1 = GeneralFAQ.objects.create(
            question="سؤال 1",
            slug="faq-1",
            answer="إجابة 1",
            category="visa",
            order=1,
            is_featured=True,
            is_published=True
        )
        faq2 = GeneralFAQ.objects.create(
            question="سؤال 2 غير منشور",
            slug="faq-2",
            answer="إجابة 2",
            category="visa",
            order=2,
            is_featured=False,
            is_published=False
        )

        all_faqs = get_all_faqs()
        self.assertEqual(len(all_faqs), 1)
        self.assertEqual(all_faqs[0]['slug'], 'faq-1')
        self.assertEqual(all_faqs[0]['id'], faq1.id)

        featured = get_featured_faqs(limit=5)
        self.assertEqual(len(featured), 1)
        self.assertEqual(featured[0]['slug'], 'faq-1')

        categories = get_faq_categories()
        visa_cat = next(c for c in categories if c['id'] == 'visa')
        self.assertEqual(visa_cat['count'], 1)
