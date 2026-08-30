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
        from django.conf import settings
        from apps.seo.views import robots_txt
        
        request = self.factory.get('/robots.txt')
        response = robots_txt(request)
        content = response.content.decode()
        
        assert f"Disallow: /{settings.ADMIN_URL.strip('/')}/" in content
        assert f"Disallow: /{settings.DASHBOARD_URL.strip('/')}/" in content
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
        assert sitemap.priority('home') == 1.0
        assert sitemap.priority('about_us') == 0.5
        assert sitemap.priority('universities:list') == 0.8
        
        assert sitemap.changefreq('home') == 'daily'
        assert sitemap.changefreq('about_us') == 'monthly'
        assert sitemap.changefreq('universities:list') == 'weekly'
        
        assert 'home' in sitemap.items()
        assert 'about_us' in sitemap.items()
    
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
    
    def test_website_schema_generation(self):
        """Test website schema generation for Google site name."""
        from apps.seo.schema import SchemaGenerator
        
        schema = SchemaGenerator.generate_website_schema(self.request)
        
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'WebSite'
        assert 'بوابات العلوم' in schema['name']
        assert 'بوابات العلوم' in schema['alternateName']
    
    def test_organization_schema_generation(self):
        """Test organization schema generation."""
        from apps.seo.schema import SchemaGenerator
        
        schema = SchemaGenerator.generate_organization_schema(self.request)
        
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'Organization'
        assert 'بوابات العلوم' in schema['name']
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
        assert schema['logo']['width'] == 600
        assert schema['logo']['height'] == 600
    
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
        assert 'بوابات العلوم' in schema['publisher']['name']
    
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
        
        assert 'author' in schema
        assert schema['author']['@type'] == 'Person'
        assert 'بوابات العلوم' in schema['author']['name'] or 'الكيالي' in schema['author']['name']


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
        assert hasattr(seo_tags, 'render_canonical_tag')
    
    def test_schema_tags_module_exists(self):
        """Test that schema_tags module can be imported."""
        from apps.seo.templatetags import schema_tags
        assert hasattr(schema_tags, 'register')
    
    def test_schema_tags_have_required_tags(self):
        """Test that schema_tags module has required template tags."""
        from apps.seo.templatetags import schema_tags
        assert hasattr(schema_tags, 'website_schema')
        assert hasattr(schema_tags, 'organization_schema')
        assert hasattr(schema_tags, 'article_schema')
        assert hasattr(schema_tags, 'breadcrumb_schema')
        assert hasattr(schema_tags, 'faq_schema')


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


@pytest.mark.django_db
class TestUniversitySchemaTag:
    """Test university_schema template tag."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        
    def test_university_schema_with_telephone_and_website(self):
        """Test that university_schema correctly includes telephone and sameAs fields."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.universities.models import University
        from apps.seo.templatetags.schema_tags import university_schema
        import json
        
        university = University.objects.create(
            name="جامعة اختبار",
            slug="test-uni",
            logo=SimpleUploadedFile("logo.png", b"file_content", content_type="image/png"),
            main_image=SimpleUploadedFile("main.png", b"file_content", content_type="image/png"),
            description="وصف اختبار للجامعة",
            location="كوالالمبور",
            telephone="+60 3-1234 5678",
            website="https://test-uni.edu.my"
        )
        
        # Call the template tag
        context = {'request': self.request}
        result_json = university_schema(context, university)
        
        # Parse the JSON safe string result
        schema = json.loads(str(result_json))
        
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'EducationalOrganization'
        assert schema['name'] == 'جامعة اختبار'
        assert schema['telephone'] == '+60 3-1234 5678'
        assert schema['sameAs'] == 'https://test-uni.edu.my'


@pytest.mark.django_db
class TestInstituteSchemaTag:
    """Test institute_schema template tag."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        
    def test_institute_schema_generation(self):
        """Test that institute_schema correctly generates EducationalOrganization schema."""
        from apps.institutes.models import Institute
        from apps.seo.templatetags.schema_tags import institute_schema
        import json
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create a mock image
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        main_image = SimpleUploadedFile("small.gif", small_gif, content_type="image/gif")

        institute = Institute.objects.create(
            name="معهد اختبار",
            slug="test-inst",
            description="وصف اختبار للمعهد",
            location="كوالالمبور",
            website="https://test-inst.edu.my",
            telephone="+60 3-8765 4321",
            main_image=main_image
        )
        
        # Call the template tag
        context = {'request': self.request}
        result_json = institute_schema(context, institute)
        
        # Parse the JSON safe string result
        schema = json.loads(str(result_json))
        
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'EducationalOrganization'
        assert schema['name'] == 'معهد اختبار'
        assert schema['sameAs'] == 'https://test-inst.edu.my'
        assert schema['telephone'] == '+60 3-8765 4321'
        assert 'logo' in schema
        assert 'address' in schema


class TestSEOHTMLParser:
    """Test SEOHTMLParser utility."""
    
    def test_extract_intro_text_fallback(self):
        """Test that intro_text falls back to first 150 words when <p> tag is far down."""
        from apps.seo.services.html_parser import SEOHTMLParser
        
        preceding_text = " ".join(["كلمة"] * 60)
        html_content = f"""
        <div data-seo-content>
            {preceding_text}
            الجامعة الوطنية الماليزية هي جامعة بحثية رائدة.
            <div class="reg-card">
                <p>قم بتحضير الأوراق التالية للخطوة الأولى.</p>
            </div>
        </div>
        """
        parser = SEOHTMLParser(html_content, "[data-seo-content]")
        data = parser.extract_main_content_data()
        
        assert data["intro_text"] != "قم بتحضير الأوراق التالية للخطوة الأولى."
        assert data["intro_text"].startswith("كلمة")
        assert "الجامعة الوطنية الماليزية" in data["intro_text"]


@pytest.mark.django_db
class TestGetTitleForPath:
    """Test get_title_for_path utility function."""
    
    def test_static_urls(self):
        """Test resolving static URLs."""
        from apps.seo.services.gsc_client import get_title_for_path
        
        assert get_title_for_path('/') == 'الرئيسية'
        assert get_title_for_path('/about-us/') == 'من نحن'
        assert get_title_for_path('/visa-tracking') == 'تتبع التأشيرة'
        
    def test_article_url(self):
        """Test resolving article detail URLs."""
        from apps.articles.models import Article
        from apps.seo.services.gsc_client import get_title_for_path
        
        # Create article
        article = Article.objects.create(
            title="معلومات عامة عن ماليزيا",
            slug="info-malaysia",
            publish_status='published'
        )
        
        # Test exact match
        assert get_title_for_path('/articles/info-malaysia/') == 'معلومات عامة عن ماليزيا'
        assert get_title_for_path('info-malaysia') == 'معلومات عامة عن ماليزيا'
        assert get_title_for_path('/info-malaysia/') == 'معلومات عامة عن ماليزيا'


@pytest.mark.django_db
class TestSitemapEnhancements:
    """Test sitemap performance improvements, GSC client url parsing, and rate limiting."""

    def test_clear_sitemap_cache_targeted(self):
        """Test targeted sitemap cache clearing and batch deletion."""
        from django.core.cache import cache
        from apps.seo.sitemaps import clear_sitemap_cache

        # Set some dummy cache keys
        cache.set("sitemap_universitysitemap_page_1", "dummy_uni")
        cache.set("sitemap_articlesitemap_page_1", "dummy_art")

        # Invalidate targeted to universities only
        clear_sitemap_cache(sitemap_type="universities")

        # Universities should be deleted, articles should remain
        assert cache.get("sitemap_universitysitemap_page_1") is None
        assert cache.get("sitemap_articlesitemap_page_1") == "dummy_art"

        # Invalidate everything
        clear_sitemap_cache()
        assert cache.get("sitemap_articlesitemap_page_1") is None

    def test_signals_crash_safety(self):
        """Test signals catch exceptions from caching backend and fail silently."""
        from unittest.mock import patch
        from apps.articles.models import Article

        # Mock clear_sitemap_cache to raise an error
        with patch("apps.seo.signals.clear_sitemap_cache", side_effect=Exception("Cache connection failed")):
            # Save an article - should succeed without raising any exceptions
            article = Article.objects.create(
                title="جديد الجامعات في ماليزيا",
                slug="new-uni-malaysia",
                publish_status='published'
            )
            assert article.pk is not None

    def test_gsc_client_sitemap_url_parsing(self):
        """Test GSC client parses sc-domain prefix and standard url prefixes correctly."""
        from unittest.mock import patch
        from apps.seo.services.gsc_client import GSCClient

        with patch("apps.seo.services.gsc_client.settings") as mock_settings:
            # 1. URL Prefix Property case
            mock_settings.GSC_SITE_URL = "https://sciencesgates.com/"
            mock_settings.GOOGLE_SERVICE_ACCOUNT_JSON = None
            client1 = GSCClient()
            client1._site_url = "https://sciencesgates.com/"
            
            with patch.object(client1, '_get_service') as mock_get_service:
                mock_service = mock_get_service.return_value
                client1.submit_sitemap()
                mock_service.sitemaps().submit.assert_called_with(
                    siteUrl="https://sciencesgates.com/",
                    feedpath="https://sciencesgates.com/sitemap.xml"
                )

            # 2. Domain Property case (starts with sc-domain:)
            client2 = GSCClient()
            client2._site_url = "sc-domain:sciencesgates.com"
            with patch.object(client2, '_get_service') as mock_get_service:
                mock_service = mock_get_service.return_value
                client2.submit_sitemap()
                mock_service.sitemaps().submit.assert_called_with(
                    siteUrl="sc-domain:sciencesgates.com",
                    feedpath="https://sciencesgates.com/sitemap.xml"
                )


from django.test import SimpleTestCase, RequestFactory, override_settings


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', 'sciencesgates.com', 'www.sciencesgates.com'])
class TestCanonicalDomainMiddlewareAndNormalization(SimpleTestCase):
    """Tests for CanonicalDomainMiddleware and canonical URL domain normalization."""

    def test_canonical_middleware_redirects_www(self):
        from apps.seo.middleware import CanonicalDomainMiddleware
        rf = RequestFactory()
        middleware = CanonicalDomainMiddleware(lambda req: None)
        request = rf.get('/universities/', HTTP_HOST='www.sciencesgates.com')
        response = middleware(request)
        assert response is not None
        assert response.status_code == 301
        assert response['Location'] == 'https://sciencesgates.com/universities/'

    def test_canonical_middleware_ignores_non_www(self):
        from apps.seo.middleware import CanonicalDomainMiddleware
        rf = RequestFactory()
        middleware = CanonicalDomainMiddleware(lambda req: None)
        request = rf.get('/universities/', HTTP_HOST='sciencesgates.com')
        response = middleware(request)
        assert response is None

    def test_normalize_canonical_domain(self):
        from apps.seo.templatetags.seo_tags import normalize_canonical_domain
        assert normalize_canonical_domain('https://www.sciencesgates.com/test/') == 'https://sciencesgates.com/test/'
        assert normalize_canonical_domain('http://sciencesgates.com/test/') == 'https://sciencesgates.com/test/'
        assert normalize_canonical_domain('https://sciencesgates.com/test/') == 'https://sciencesgates.com/test/'



