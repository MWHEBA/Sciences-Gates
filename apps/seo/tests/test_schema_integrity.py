import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.articles.models import Article, Category
from apps.core.models import AuthorProfile, PublishStatus

class SchemaIntegrityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='dr-mohammad-kayali', first_name='Dr Mohammad', last_name='Kayali')
        self.author_profile, _ = AuthorProfile.objects.get_or_create(
            slug='dr-mohammad-kayali',
            defaults={
                'name': 'د. محمد الكيالي',
                'title_credentials': 'دكتوراه في علوم الحاسوب (UKM)',
                'bio': 'خبير استشارات تعليمية في ماليزيا',
            }
        )
        self.category = Category.objects.create(name='الدراسة في ماليزيا', slug='study-in-malaysia')
        self.article = Article.objects.create(
            title='دليل الدراسة في ماليزيا 2026',
            slug='study-in-malaysia-guide',
            content='<p>محتوى اختبار دليل الدراسة في ماليزيا...</p>',
            author=self.user,
            category=self.category,
            publish_status=PublishStatus.PUBLISHED,
        )

    def test_homepage_schema_graph(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('https://schema.org', content)
        self.assertIn('"@type": "WebSite"', content)
        self.assertIn('"@type": "Organization"', content)
        self.assertIn('"@type": "WebPage"', content)
        self.assertIn('"@type": "BreadcrumbList"', content)

    def test_universities_list_schema(self):
        response = self.client.get('/universities/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('"@type": "WebPage"', content)
        self.assertIn('"@type": "BreadcrumbList"', content)

    def test_author_person_schema_has_id_and_worksfor(self):
        response = self.client.get('/author/dr-mohammad-kayali/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('"@type": "Person"', content)
        self.assertIn('"@id": "https://sciencesgates.com/author/dr-mohammad-kayali/#person"', content)
        self.assertIn('"@id": "https://sciencesgates.com/#organization"', content)

    def test_article_schema_blogposting(self):
        response = self.client.get(f'/articles/{self.article.slug}/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('"@type": "BlogPosting"', content)
        self.assertIn('"headline":', content)

    def test_indexnow_txt_endpoint(self):
        response = self.client.get('/indexnow.txt')
        self.assertEqual(response.status_code, 200)
        self.assertIn('c7a8b9f0e1d2c3b4a5f6e7d8c9b0a1f2', response.content.decode('utf-8'))

    def test_contact_page_200_ok(self):
        response = self.client.get('/contact/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('"@type": "ContactPage"', content)
