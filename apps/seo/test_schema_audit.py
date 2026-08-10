from django.test import TestCase, RequestFactory
from apps.seo.schema import SchemaGenerator
from apps.articles.models import Article, Category
from django.utils import timezone
import json


class SchemaAuditAndEntityGraphTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.category = Category.objects.create(name='عام', slug='general')
        self.article = Article.objects.create(
            title='مقال اختبار Schema',
            slug='test-schema-article',
            content='محتوى المقال للاختبار',
            category=self.category,
            publish_status='published',
            publish_date=timezone.now()
        )

    def test_json_ld_validity(self):
        website = SchemaGenerator.generate_website_schema(self.request)
        org = SchemaGenerator.generate_organization_schema(self.request)
        article_schema = SchemaGenerator.generate_article_schema(self.article, self.request)

        # Assert valid JSON structures
        self.assertIsInstance(json.loads(json.dumps(website)), dict)
        self.assertIsInstance(json.loads(json.dumps(org)), dict)
        self.assertIsInstance(json.loads(json.dumps(article_schema)), dict)

    def test_organization_entity_graph(self):
        org = SchemaGenerator.generate_organization_schema(self.request)
        self.assertEqual(org['@type'], 'Organization')
        self.assertTrue(org['@id'].endswith('#organization'))
        self.assertEqual(org['name'], 'شركة بوابات العلوم')

        # ContactPoint assertions
        contact = org['contactPoint']
        self.assertEqual(contact['telephone'], '+601128195437')
        self.assertEqual(contact['email'], 'info@sciencesgates.com')
        self.assertIn('MY', contact['areaServed'])

        # PostalAddress assertions
        address = org['address']
        self.assertEqual(address['addressLocality'], 'Kuala Lumpur')
        self.assertEqual(address['addressCountry'], 'MY')

        # sameAs WhatsApp filtering assertion
        for link in org['sameAs']:
            self.assertNotIn('wa.me', link)
            self.assertNotIn('whatsapp', link)

    def test_article_linked_author_and_publisher(self):
        article_schema = SchemaGenerator.generate_article_schema(self.article, self.request)
        self.assertEqual(article_schema['@type'], 'BlogPosting')
        self.assertTrue(article_schema['publisher']['@id'].endswith('#organization'))
        self.assertTrue(article_schema['author']['@id'].endswith('#person'))

    def test_all_schema_references_same_organization_id(self):
        website = SchemaGenerator.generate_website_schema(self.request)
        org = SchemaGenerator.generate_organization_schema(self.request)
        article_schema = SchemaGenerator.generate_article_schema(self.article, self.request)

        org_id = org['@id']
        self.assertEqual(website['publisher']['@id'], org_id)
        self.assertEqual(article_schema['publisher']['@id'], org_id)

    def test_all_schema_ids_are_absolute(self):
        website = SchemaGenerator.generate_website_schema(self.request)
        org = SchemaGenerator.generate_organization_schema(self.request)
        article_schema = SchemaGenerator.generate_article_schema(self.article, self.request)

        for schema_obj in [website, org, article_schema]:
            schema_id = schema_obj.get('@id', '')
            self.assertTrue(schema_id.startswith('http://') or schema_id.startswith('https://'))
