"""
Tests for SEO app functionality.

Converted from Django TestCase to pytest for faster test execution.

Tests verify:
- robots.txt view returns correct response
- Sitemap classes are properly configured
- Schema generation utilities work correctly
- Template tags are properly registered
"""
import pytest
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from apps.articles.models import Category, Article
from apps.seo.schema import SchemaGenerator


@pytest.mark.django_db
class TestRobotsTxtView:
    """Test robots.txt view functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    def test_robots_txt_returns_200(self):
        """Test that robots.txt view returns 200 status code."""
        from apps.seo.views import robots_txt
        
        request = self.factory.get('/robots.txt')
        response = robots_txt(request)
        assert response.status_code == 200
    
    def test_robots_txt_content_type(self):
        """Test that robots.txt returns text/plain content type."""
        from apps.seo.views import robots_txt
        
        request = self.factory.get('/robots.txt')
        response = robots_txt(request)
        assert response.get('Content-Type') == 'text/plain'
    
    def test_robots_txt_contains_disallow_rules(self):
        """Test that robots.txt contains expected disallow rules."""
        from apps.seo.views import robots_txt
        
        request = self.factory.get('/robots.txt')
        response = robots_txt(request)
        content = response.content.decode()
        
        assert 'Disallow: /admin/' in content
        assert 'Disallow: /dashboard/' in content
        assert 'User-agent: *' in content
    
    def test_robots_txt_contains_sitemap_reference(self):
        """Test that robots.txt contains sitemap reference."""
        from apps.seo.views import robots_txt
        
        request = self.factory.get('/robots.txt')
        response = robots_txt(request)
        content = response.content.decode()
        
        assert 'Sitemap:' in content
        assert '/sitemap.xml' in content


@pytest.mark.django_db
class TestSitemapClasses:
    """Test sitemap classes configuration."""
    
    def test_base_sitemap_configuration(self):
        """Test BaseSitemap has correct configuration."""
        from apps.seo.sitemaps import BaseSitemap
        sitemap = BaseSitemap()
        assert sitemap.changefreq == 'weekly'
        assert sitemap.priority == 0.8
        assert sitemap.protocol == 'https'
    
    def test_university_sitemap_configuration(self):
        """Test UniversitySitemap has correct configuration."""
        from apps.seo.sitemaps import UniversitySitemap
        
        sitemap = UniversitySitemap()
        assert sitemap.priority == 0.9
        assert sitemap.changefreq == 'monthly'
        assert list(sitemap.items()) == []
    
    def test_institute_sitemap_configuration(self):
        """Test InstituteSitemap has correct configuration."""
        from apps.seo.sitemaps import InstituteSitemap
        
        sitemap = InstituteSitemap()
        assert sitemap.priority == 0.9
        assert sitemap.changefreq == 'monthly'
        assert list(sitemap.items()) == []
    
    def test_major_sitemap_configuration(self):
        """Test MajorSitemap has correct configuration."""
        from apps.seo.sitemaps import MajorSitemap
        
        sitemap = MajorSitemap()
        assert sitemap.priority == 0.9
        assert sitemap.changefreq == 'monthly'
        assert list(sitemap.items()) == []
    
    def test_article_sitemap_configuration(self):
        """Test ArticleSitemap has correct configuration."""
        from apps.seo.sitemaps import ArticleSitemap
        
        sitemap = ArticleSitemap()
        assert sitemap.priority == 0.8
        assert sitemap.changefreq == 'weekly'
        assert list(sitemap.items()) == []
    
    def test_static_sitemap_configuration(self):
        """Test StaticSitemap has correct configuration."""
        from apps.seo.sitemaps import StaticSitemap
        
        sitemap = StaticSitemap()
        assert sitemap.priority == 0.5
        assert sitemap.changefreq == 'monthly'
        assert sitemap.items() == ['home']
    
    def test_sitemaps_dictionary_contains_all_sitemaps(self):
        """Test that sitemaps dictionary contains all sitemap classes."""
        from apps.seo.sitemaps import (
            UniversitySitemap, InstituteSitemap,
            MajorSitemap, ArticleSitemap, StaticSitemap, sitemaps
        )
        
        assert 'universities' in sitemaps
        assert 'institutes' in sitemaps
        assert 'majors' in sitemaps
        assert 'articles' in sitemaps
        assert 'static' in sitemaps
        
        assert sitemaps['universities'] == UniversitySitemap
        assert sitemaps['institutes'] == InstituteSitemap
        assert sitemaps['majors'] == MajorSitemap
        assert sitemaps['articles'] == ArticleSitemap
        assert sitemaps['static'] == StaticSitemap


@pytest.mark.django_db
class TestSchemaGenerator:
    """Test schema generation utilities."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
    
    def test_organization_schema_generation(self):
        """Test organization schema generation."""
        from apps.seo.schema import SchemaGenerator
        
        schema = SchemaGenerator.generate_organization_schema(self.request)
        
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'Organization'
        assert schema['name'] == 'Science Gates'
        assert schema['inLanguage'] == 'ar'
    
    def test_organization_schema_has_contact_point(self):
        """Test organization schema includes contact point."""
        from apps.seo.schema import SchemaGenerator
        
        schema = SchemaGenerator.generate_organization_schema(self.request)
        
        assert 'contactPoint' in schema
        assert schema['contactPoint']['@type'] == 'ContactPoint'
        assert schema['contactPoint']['contactType'] == 'Customer Service'
    
    def test_organization_schema_has_social_profiles(self):
        """Test organization schema includes social profiles."""
        from apps.seo.schema import SchemaGenerator
        
        schema = SchemaGenerator.generate_organization_schema(self.request)
        
        assert 'sameAs' in schema
        assert isinstance(schema['sameAs'], list)
        assert len(schema['sameAs']) > 0
    
    def test_organization_schema_has_logo(self):
        """Test organization schema includes logo."""
        from apps.seo.schema import SchemaGenerator
        
        schema = SchemaGenerator.generate_organization_schema(self.request)
        
        assert 'logo' in schema
        assert schema['logo']['@type'] == 'ImageObject'
        assert 'url' in schema['logo']
        assert schema['logo']['width'] == 250
        assert schema['logo']['height'] == 60
    
    def test_breadcrumb_schema_generation(self):
        """Test breadcrumb schema generation."""
        from apps.seo.schema import SchemaGenerator
        
        breadcrumbs = [
            ('الرئيسية', '/'),
            ('الجامعات', '/universities/'),
        ]
        schema = SchemaGenerator.generate_breadcrumb_schema(breadcrumbs, self.request)
        
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'BreadcrumbList'
        assert len(schema['itemListElement']) == 2
        assert schema['itemListElement'][0]['position'] == 1
        assert schema['itemListElement'][0]['name'] == 'الرئيسية'
    
    def test_faq_schema_generation_with_dict_list(self):
        """Test FAQ schema generation with dictionary list."""
        from apps.seo.schema import SchemaGenerator
        
        faqs = [
            {'question': 'ما هي الجامعة؟', 'answer': 'الجامعة هي مؤسسة تعليمية...'},
            {'question': 'كيف أتقدم؟', 'answer': 'يمكنك التقدم عبر الموقع...'},
        ]
        schema = SchemaGenerator.generate_faq_schema(faqs)
        
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'FAQPage'
        assert len(schema['mainEntity']) == 2
        assert schema['mainEntity'][0]['@type'] == 'Question'
        assert schema['mainEntity'][0]['name'] == 'ما هي الجامعة؟'
        assert schema['mainEntity'][0]['acceptedAnswer']['text'] == 'الجامعة هي مؤسسة تعليمية...'
    
    def test_faq_schema_generation_with_empty_list(self):
        """Test FAQ schema generation with empty list."""
        from apps.seo.schema import SchemaGenerator
        
        faqs = []
        schema = SchemaGenerator.generate_faq_schema(faqs)
        
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'FAQPage'
        assert len(schema['mainEntity']) == 0
    
    def test_faq_schema_ignores_incomplete_entries(self):
        """Test FAQ schema ignores entries with missing question or answer."""
        from apps.seo.schema import SchemaGenerator
        
        faqs = [
            {'question': 'ما هي الجامعة؟', 'answer': 'الجامعة هي مؤسسة تعليمية...'},
            {'question': 'سؤال بدون إجابة', 'answer': ''},
            {'question': '', 'answer': 'إجابة بدون سؤال'},
        ]
        schema = SchemaGenerator.generate_faq_schema(faqs)
        
        assert len(schema['mainEntity']) == 1
    
    def test_schema_to_json_ld(self):
        """Test schema conversion to JSON-LD string."""
        from apps.seo.schema import SchemaGenerator
        
        schema = {'@context': 'https://schema.org', '@type': 'Organization'}
        json_ld = SchemaGenerator.to_json_ld(schema)
        
        assert '@context' in json_ld
        assert '@type' in json_ld
        assert 'Organization' in json_ld
    
    def test_schema_to_json_ld_preserves_arabic(self):
        """Test that JSON-LD conversion preserves Arabic characters."""
        from apps.seo.schema import SchemaGenerator
        
        schema = {'@context': 'https://schema.org', 'name': 'بوابات العلوم'}
        json_ld = SchemaGenerator.to_json_ld(schema)
        
        assert 'بوابات العلوم' in json_ld


@pytest.mark.django_db
class TestArticleSchemaGenerator:
    """Test article schema generation."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        
        self.category = Category.objects.create(
            name='أخبار',
            slug='news'
        )
    
    def test_article_schema_generation_basic(self):
        """Test basic article schema generation."""
        article = Article.objects.create(
            title='مقالة اختبار',
            slug='test-article',
            category=self.category,
            author=self.user,
            content='<p>محتوى المقالة</p>',
            meta_title='عنوان SEO',
            meta_description='وصف SEO'
        )
        
        schema = SchemaGenerator.generate_article_schema(article, self.request)
        
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'NewsArticle'
        assert schema['headline'] == 'عنوان SEO'
        assert schema['description'] == 'وصف SEO'
        assert schema['inLanguage'] == 'ar'
    
    def test_article_schema_includes_dates(self):
        """Test article schema includes publication and modification dates."""
        article = Article.objects.create(
            title='مقالة اختبار',
            slug='test-article',
            category=self.category,
            author=self.user,
            content='<p>محتوى المقالة</p>',
            meta_title='عنوان SEO',
            meta_description='وصف SEO'
        )
        
        schema = SchemaGenerator.generate_article_schema(article, self.request)
        
        assert 'datePublished' in schema
        assert 'dateModified' in schema
        assert schema['datePublished'] is not None
        assert schema['dateModified'] is not None
    
    def test_article_schema_includes_author(self):
        """Test article schema includes author information."""
        article = Article.objects.create(
            title='مقالة اختبار',
            slug='test-article',
            category=self.category,
            author=self.user,
            content='<p>محتوى المقالة</p>',
            meta_title='عنوان SEO',
            meta_description='وصف SEO'
        )
        
        schema = SchemaGenerator.generate_article_schema(article, self.request)
        
        assert 'author' in schema
        assert schema['author']['@type'] == 'Person'
        assert schema['author']['name'] == 'Test User'
    
    def test_article_schema_includes_publisher(self):
        """Test article schema includes publisher information."""
        article = Article.objects.create(
            title='مقالة اختبار',
            slug='test-article',
            category=self.category,
            author=self.user,
            content='<p>محتوى المقالة</p>',
            meta_title='عنوان SEO',
            meta_description='وصف SEO'
        )
        
        schema = SchemaGenerator.generate_article_schema(article, self.request)
        
        assert 'publisher' in schema
        assert schema['publisher']['@type'] == 'Organization'
        assert schema['publisher']['name'] == 'Science Gates'
    
    def test_article_schema_includes_url(self):
        """Test article schema includes article URL."""
        article = Article.objects.create(
            title='مقالة اختبار',
            slug='test-article',
            category=self.category,
            author=self.user,
            content='<p>محتوى المقالة</p>',
            meta_title='عنوان SEO',
            meta_description='وصف SEO'
        )
        
        schema = SchemaGenerator.generate_article_schema(article, self.request)
        
        assert 'url' in schema
        assert 'test-article' in schema['url']
    
    def test_article_schema_without_author(self):
        """Test article schema generation without author."""
        article = Article.objects.create(
            title='مقالة اختبار',
            slug='test-article',
            category=self.category,
            content='<p>محتوى المقالة</p>',
            meta_title='عنوان SEO',
            meta_description='وصف SEO'
        )
        
        schema = SchemaGenerator.generate_article_schema(article, self.request)
        
        assert 'author' not in schema


@pytest.mark.django_db
class TestTemplateTagsRegistration:
    """Test that template tags are properly registered."""
    
    def test_seo_tags_module_exists(self):
        """Test that seo_tags module can be imported."""
        from apps.seo.templatetags import seo_tags
        assert hasattr(seo_tags, 'register')
    
    def test_breadcrumbs_tags_module_exists(self):
        """Test that breadcrumbs module can be imported."""
        from apps.seo.templatetags import breadcrumbs
        assert hasattr(breadcrumbs, 'register')
    
    def test_seo_tags_have_required_tags(self):
        """Test that seo_tags module has required template tags."""
        from apps.seo.templatetags import seo_tags
        
        assert 'render_meta_tags' in seo_tags.register.tags
        assert 'render_og_tags' in seo_tags.register.tags
        assert 'render_twitter_card_tags' in seo_tags.register.tags
        assert 'render_canonical_tag' in seo_tags.register.tags
    
    def test_breadcrumbs_tags_have_required_tags(self):
        """Test that breadcrumbs module has required template tags."""
        from apps.seo.templatetags import breadcrumbs
        
        assert 'render_breadcrumbs' in breadcrumbs.register.tags
        assert 'render_breadcrumb_schema' in breadcrumbs.register.tags


@pytest.mark.django_db
class TestSEOAppConfig:
    """Test SEO app configuration."""
    
    def test_seo_app_is_installed(self):
        """Test that SEO app is installed in INSTALLED_APPS."""
        from django.conf import settings
        assert 'apps.seo' in settings.INSTALLED_APPS
    
    def test_seo_app_config_name(self):
        """Test that SEO app config has correct name."""
        from django.apps import apps
        config = apps.get_app_config('seo')
        assert config.name == 'apps.seo'
        assert config.verbose_name == 'SEO'
