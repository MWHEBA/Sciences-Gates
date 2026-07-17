"""
Tests for articles app.

Converted from Django TestCase to pytest for faster test execution.
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.articles.models import Article, Category, Tag

User = get_user_model()


@pytest.mark.django_db
class TestCategoryModel:
    """Test cases for Category model."""
    
    def test_category_creation(self):
        """Test that category is created correctly."""
        from .models import Category
        category = Category.objects.create(
            name='أخبار التعليم',
            slug='news-education',
            description='أخبار وتحديثات عن التعليم'
        )
        assert category.name == 'أخبار التعليم'
        assert category.slug == 'news-education'
    
    def test_category_str(self):
        """Test category string representation."""
        from .models import Category
        category = Category.objects.create(
            name='أخبار التعليم',
            slug='news-education'
        )
        assert str(category) == 'أخبار التعليم'
    
    def test_category_absolute_url(self):
        """Test category absolute URL."""
        from .models import Category
        category = Category.objects.create(
            name='أخبار التعليم',
            slug='news-education'
        )
        url = category.get_absolute_url()
        assert url == reverse('articles:category', kwargs={'slug': 'news-education'})


@pytest.mark.django_db
class TestTagModel:
    """Test cases for Tag model."""
    
    def test_tag_creation(self):
        """Test that tag is created correctly."""
        from .models import Tag
        tag = Tag.objects.create(
            name='ماليزيا',
            slug='malaysia'
        )
        assert tag.name == 'ماليزيا'
        assert tag.slug == 'malaysia'
    
    def test_tag_str(self):
        """Test tag string representation."""
        from .models import Tag
        tag = Tag.objects.create(
            name='ماليزيا',
            slug='malaysia'
        )
        assert str(tag) == 'ماليزيا'
    
    def test_tag_absolute_url(self):
        """Test tag absolute URL."""
        from .models import Tag
        tag = Tag.objects.create(
            name='ماليزيا',
            slug='malaysia'
        )
        url = tag.get_absolute_url()
        assert url == reverse('articles:tag', kwargs={'slug': 'malaysia'})


@pytest.mark.django_db
class TestArticleModel:
    """Test cases for Article model."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test article with related objects."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='أخبار',
            slug='news'
        )
        self.tag = Tag.objects.create(
            name='ماليزيا',
            slug='malaysia'
        )
        self.article = Article.objects.create(
            title='اختبار المقالة',
            slug='test-article',
            featured_image='articles/test.jpg',
            category=self.category,
            author=self.user,
            content='<p>محتوى المقالة</p>',
            publish_status='published'
        )
        self.article.tags.add(self.tag)
    
    def test_article_creation(self):
        """Test that article is created correctly."""
        assert self.article.title == 'اختبار المقالة'
        assert self.article.slug == 'test-article'
        assert self.article.category == self.category
        assert self.article.author == self.user
    
    def test_article_str(self):
        """Test article string representation."""
        assert str(self.article) == 'اختبار المقالة'
    
    def test_article_absolute_url(self):
        """Test article absolute URL."""
        url = self.article.get_absolute_url()
        assert url == reverse('articles:detail', kwargs={'slug': 'test-article'})
    
    def test_article_is_published(self):
        """Test article is_published property."""
        assert self.article.is_published
        
        unpublished_article = Article.objects.create(
            title='مقالة غير منشورة',
            slug='unpublished-article',
            featured_image='articles/test.jpg',
            content='<p>محتوى</p>',
            publish_status='unpublished'
        )
        assert not unpublished_article.is_published
    
    def test_article_content_sanitization(self):
        """Test that article content is sanitized on save."""
        article = Article(
            title='اختبار التطهير',
            slug='sanitization-test',
            featured_image='articles/test.jpg',
            content='<p>محتوى آمن</p><script>alert("XSS")</script>',
            publish_status='published'
        )
        article.save()
        
        assert '<script>' not in article.content
        assert '<p>محتوى آمن</p>' in article.content
    
    def test_article_tags_relationship(self):
        """Test article tags many-to-many relationship."""
        assert self.tag in self.article.tags.all()
        
        tag2 = Tag.objects.create(name='تعليم', slug='education')
        self.article.tags.add(tag2)
        
        assert self.article.tags.count() == 2


@pytest.mark.django_db
class TestArticleListView:
    """Test cases for ArticleListView."""
    
    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Create test data."""
        self.client = client
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='أخبار',
            slug='news'
        )
        
        for i in range(25):
            Article.objects.create(
                title=f'مقالة {i}',
                slug=f'article-{i}',
                featured_image='articles/test.jpg',
                category=self.category,
                author=self.user,
                content=f'<p>محتوى المقالة {i}</p>',
                publish_status='published'
            )
        
        Article.objects.create(
            title='مقالة غير منشورة',
            slug='unpublished-article',
            featured_image='articles/test.jpg',
            content='<p>محتوى</p>',
            publish_status='unpublished'
        )
    
    def test_article_list_view_status_code(self):
        """Test that article list view returns 200."""
        response = self.client.get(reverse('articles:list'))
        assert response.status_code == 200
        assert response.context['clear_url'] == reverse('articles:list')
    
    def test_article_list_view_template(self):
        """Test that article list view uses correct template."""
        response = self.client.get(reverse('articles:list'))
        assert 'articles/list.html' in [t.name for t in response.templates]
    
    def test_article_list_view_pagination(self):
        """Test that article list view paginates correctly."""
        response = self.client.get(reverse('articles:list'))
        
        assert len(response.context['articles']) == 20
        assert response.context['is_paginated']
        assert response.context['page_obj'].number == 1
    
    def test_article_list_view_only_published(self):
        """Test that only published articles are shown."""
        response = self.client.get(reverse('articles:list'))
        
        articles = response.context['articles']
        for article in articles:
            assert article.is_published
    
    def test_article_list_view_ordering(self):
        """Test that articles are ordered by publish date (newest first)."""
        response = self.client.get(reverse('articles:list'))
        
        articles = list(response.context['articles'])
        for i in range(len(articles) - 1):
            assert articles[i].publish_date >= articles[i + 1].publish_date


@pytest.mark.django_db
class TestArticleDetailView:
    """Test cases for ArticleDetailView."""
    
    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Create test article."""
        self.client = client
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='أخبار',
            slug='news'
        )
        self.article = Article.objects.create(
            title='اختبار المقالة',
            slug='test-article',
            featured_image='articles/test.jpg',
            category=self.category,
            author=self.user,
            content='<p>محتوى المقالة</p>',
            publish_status='published'
        )
    
    def test_article_detail_view_status_code(self):
        """Test that article detail view returns 200."""
        response = self.client.get(self.article.get_absolute_url())
        assert response.status_code == 200
    
    def test_article_detail_view_template(self):
        """Test that article detail view uses correct template."""
        response = self.client.get(self.article.get_absolute_url())
        assert 'articles/detail.html' in [t.name for t in response.templates]
    
    def test_article_detail_view_context(self):
        """Test that article detail view has correct context."""
        response = self.client.get(self.article.get_absolute_url())
        
        assert response.context['article'] == self.article
        assert 'related_universities' in response.context
        assert 'related_institutes' in response.context
        assert 'related_majors' in response.context
        assert 'faqs' in response.context
    
    def test_article_detail_view_faqs_in_context(self):
        """Test that article detail view passes faqs in context."""
        from .models import ArticleFAQ
        faq = ArticleFAQ.objects.create(
            article=self.article,
            question='ما هو السؤال؟',
            answer='<p>هذه هي الإجابة</p>',
            sort_order=1
        )
        response = self.client.get(self.article.get_absolute_url())
        assert response.status_code == 200
        assert faq in response.context['faqs']
    
    def test_article_detail_view_unpublished_404(self):
        """Test that unpublished articles return 404."""
        unpublished = Article.objects.create(
            title='مقالة غير منشورة',
            slug='unpublished-article',
            featured_image='articles/test.jpg',
            content='<p>محتوى</p>',
            publish_status='unpublished'
        )
        
        response = self.client.get(unpublished.get_absolute_url())
        assert response.status_code == 404


@pytest.mark.django_db
class TestCategoryArticleListView:
    """Test cases for CategoryArticleListView."""
    
    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Create test data."""
        self.client = client
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category1 = Category.objects.create(
            name='أخبار',
            slug='news'
        )
        self.category2 = Category.objects.create(
            name='تعليم',
            slug='education'
        )
        
        for i in range(5):
            Article.objects.create(
                title=f'مقالة أخبار {i}',
                slug=f'news-article-{i}',
                featured_image='articles/test.jpg',
                category=self.category1,
                author=self.user,
                content=f'<p>محتوى</p>',
                publish_status='published'
            )
        
        for i in range(3):
            Article.objects.create(
                title=f'مقالة تعليم {i}',
                slug=f'education-article-{i}',
                featured_image='articles/test.jpg',
                category=self.category2,
                author=self.user,
                content=f'<p>محتوى</p>',
                publish_status='published'
            )
    
    def test_category_article_list_view_status_code(self):
        """Test that category article list view returns 200."""
        response = self.client.get(self.category1.get_absolute_url())
        assert response.status_code == 200
    
    def test_category_article_list_view_template(self):
        """Test that category article list view uses correct template."""
        response = self.client.get(self.category1.get_absolute_url())
        assert 'articles/category.html' in [t.name for t in response.templates]
    
    def test_category_article_list_view_filters_by_category(self):
        """Test that only articles in the category are shown."""
        response = self.client.get(self.category1.get_absolute_url())
        
        articles = response.context['articles']
        assert len(articles) == 5
        
        for article in articles:
            assert article.category == self.category1
    
    def test_category_article_list_view_context(self):
        """Test that category is in context."""
        response = self.client.get(self.category1.get_absolute_url())
        
        assert response.context['category'] == self.category1
        assert response.context['clear_url'] == reverse('articles:list')


@pytest.mark.django_db
class TestTagArticleListView:
    """Test cases for TagArticleListView."""
    
    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Create test data."""
        self.client = client
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tag1 = Tag.objects.create(
            name='ماليزيا',
            slug='malaysia'
        )
        self.tag2 = Tag.objects.create(
            name='جامعات',
            slug='universities'
        )
        
        for i in range(5):
            article = Article.objects.create(
                title=f'مقالة ماليزيا {i}',
                slug=f'malaysia-article-{i}',
                featured_image='articles/test.jpg',
                author=self.user,
                content=f'<p>محتوى</p>',
                publish_status='published'
            )
            article.tags.add(self.tag1)
        
        for i in range(3):
            article = Article.objects.create(
                title=f'مقالة جامعات {i}',
                slug=f'universities-article-{i}',
                featured_image='articles/test.jpg',
                author=self.user,
                content=f'<p>محتوى</p>',
                publish_status='published'
            )
            article.tags.add(self.tag2)
    
    def test_tag_article_list_view_status_code(self):
        """Test that tag article list view returns 200."""
        response = self.client.get(self.tag1.get_absolute_url())
        assert response.status_code == 200
    
    def test_tag_article_list_view_template(self):
        """Test that tag article list view uses correct template."""
        response = self.client.get(self.tag1.get_absolute_url())
        assert 'articles/tag.html' in [t.name for t in response.templates]
    
    def test_tag_article_list_view_filters_by_tag(self):
        """Test that only articles with the tag are shown."""
        response = self.client.get(self.tag1.get_absolute_url())
        
        articles = response.context['articles']
        assert len(articles) == 5
        
        for article in articles:
            assert self.tag1 in article.tags.all()
    
    def test_tag_article_list_view_context(self):
        """Test that tag is in context."""
        response = self.client.get(self.tag1.get_absolute_url())
        
        assert response.context['tag'] == self.tag1
        assert response.context['clear_url'] == reverse('articles:list')


@pytest.mark.django_db
class TestArticleFAQModel:
    """Test cases for ArticleFAQ model."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test article."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='أخبار',
            slug='news'
        )
        self.article = Article.objects.create(
            title='اختبار المقالة',
            slug='test-article',
            featured_image='articles/test.jpg',
            category=self.category,
            author=self.user,
            content='<p>محتوى المقالة</p>',
            publish_status='published'
        )
        
    def test_faq_creation(self):
        """Test that FAQ is created correctly."""
        from .models import ArticleFAQ
        faq = ArticleFAQ.objects.create(
            article=self.article,
            question='ما هو السؤال؟',
            answer='<p>هذه هي الإجابة</p>',
            sort_order=1
        )
        assert faq.article == self.article
        assert faq.question == 'ما هو السؤال؟'
        assert faq.answer == '<p>هذه هي الإجابة</p>'
        assert faq.sort_order == 1
        
    def test_faq_str(self):
        """Test FAQ string representation."""
        from .models import ArticleFAQ
        faq = ArticleFAQ.objects.create(
            article=self.article,
            question='ما هو السؤال؟',
            answer='<p>هذه هي الإجابة</p>'
        )
        assert str(faq) == 'ما هو السؤال؟'
        
    def test_faq_sanitization(self):
        """Test that FAQ answer is sanitized before saving."""
        from .models import ArticleFAQ
        # Answer with malicious script tag
        faq = ArticleFAQ.objects.create(
            article=self.article,
            question='سؤال أمني؟',
            answer='<p>إجابة آمنة</p><script>alert("XSS")</script>'
        )
        # Script tag should be stripped by sanitizer in pre_save
        assert '<script>' not in faq.answer
        assert 'alert("XSS")' not in faq.answer
        assert '<p>إجابة آمنة</p>' in faq.answer
