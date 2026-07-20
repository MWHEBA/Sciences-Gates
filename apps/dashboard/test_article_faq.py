import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.articles.models import Article, ArticleFAQ, Category
from apps.importer.services.bulk_saver import _save_article

User = get_user_model()


@pytest.mark.django_db
class TestArticleFAQDashboard:
    """Test cases for Article FAQ management in the dashboard."""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.client.login(username='admin', password='testpass123')
        
        self.category = Category.objects.create(
            name='أخبار التعليم',
            slug='edu-news'
        )
        self.article = Article.objects.create(
            title='دليل الدراسة في ماليزيا',
            slug='study-malaysia',
            category=self.category,
            author=self.user,
            content='<p>محتوى المقالة</p>',
            featured_image='articles/test.jpg',  # Provide default to avoid form validation requirement on update
            publish_status='published'
        )

    def test_article_create_view_with_faqs(self):
        """Test creating an article with FAQs in dashboard view."""
        url = reverse('dashboard:article_create')
        
        # Create a mock 1x1 valid GIF image to satisfy Pillow validation in ImageField
        gif_bytes = b'GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x04\x00;'
        mock_image = SimpleUploadedFile("test_image.gif", gif_bytes, content_type="image/gif")
        
        data = {
            'title': 'مقالة جديدة مع أسئلة شائعة',
            'slug': 'new-article-with-faqs',
            'category': self.category.id,
            'content': '<p>محتوى المقال</p>',
            'publish_status': 'published',
            'featured_image': mock_image,
            
            # FAQ Formset fields
            'faqs-TOTAL_FORMS': '2',
            'faqs-INITIAL_FORMS': '0',
            'faqs-MIN_NUM_FORMS': '0',
            'faqs-MAX_NUM_FORMS': '1000',
            
            # Attachment Formset fields
            'attachments-TOTAL_FORMS': '0',
            'attachments-INITIAL_FORMS': '0',
            'attachments-MIN_NUM_FORMS': '0',
            'attachments-MAX_NUM_FORMS': '1000',
            
            'faqs-0-id': '',
            'faqs-0-question': 'Question 1?',
            'faqs-0-answer': 'Answer 1.',
            'faqs-0-sort_order': '0',
            
            'faqs-1-id': '',
            'faqs-1-question': 'Question 2?',
            'faqs-1-answer': 'Answer 2.',
            'faqs-1-sort_order': '1',
        }
        
        response = self.client.post(url, data)
        # Should redirect to edit page of the newly created article
        assert response.status_code == 302
        
        new_article = Article.objects.get(slug='new-article-with-faqs')
        assert new_article.faqs.count() == 2
        
        faq1 = new_article.faqs.get(sort_order=0)
        assert faq1.question == 'Question 1?'
        assert faq1.answer == 'Answer 1.'
        
        faq2 = new_article.faqs.get(sort_order=1)
        assert faq2.question == 'Question 2?'
        assert faq2.answer == 'Answer 2.'

    def test_article_update_view_add_modify_delete_faqs(self):
        """Test updating, deleting and adding FAQs to an existing article."""
        # Create initial FAQ
        faq_to_modify = ArticleFAQ.objects.create(
            article=self.article,
            question='Initial Question 1?',
            answer='Initial Answer 1.',
            sort_order=0
        )
        faq_to_delete = ArticleFAQ.objects.create(
            article=self.article,
            question='Initial Question 2?',
            answer='Initial Answer 2.',
            sort_order=1
        )
        
        url = reverse('dashboard:article_edit', kwargs={'pk': self.article.pk})
        data = {
            'title': self.article.title,
            'slug': self.article.slug,
            'category': self.category.id,
            'content': self.article.content,
            'publish_status': self.article.publish_status,
            
            # FAQ Formset fields
            'faqs-TOTAL_FORMS': '3', # Modify 1, Delete 1, Add 1 = 3 total forms
            'faqs-INITIAL_FORMS': '2',
            'faqs-MIN_NUM_FORMS': '0',
            'faqs-MAX_NUM_FORMS': '1000',
            
            # Attachment Formset fields
            'attachments-TOTAL_FORMS': '0',
            'attachments-INITIAL_FORMS': '0',
            'attachments-MIN_NUM_FORMS': '0',
            'attachments-MAX_NUM_FORMS': '1000',
            
            # Form 0: Modify existing
            'faqs-0-id': str(faq_to_modify.id),
            'faqs-0-question': 'Modified Question 1?',
            'faqs-0-answer': 'Modified Answer 1.',
            'faqs-0-sort_order': '0',
            
            # Form 1: Delete existing
            'faqs-1-id': str(faq_to_delete.id),
            'faqs-1-question': faq_to_delete.question,
            'faqs-1-answer': faq_to_delete.answer,
            'faqs-1-sort_order': '1',
            'faqs-1-DELETE': 'on', # Mark for deletion
            
            # Form 2: Add new
            'faqs-2-id': '',
            'faqs-2-question': 'New Question 3?',
            'faqs-2-answer': 'New Answer 3.',
            'faqs-2-sort_order': '2',
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        # Verify changes in DB
        assert self.article.faqs.count() == 2
        
        # Check modified
        faq_modified = self.article.faqs.get(id=faq_to_modify.id)
        assert faq_modified.question == 'Modified Question 1?'
        assert faq_modified.answer == 'Modified Answer 1.'
        
        # Check deleted
        assert not ArticleFAQ.objects.filter(id=faq_to_delete.id).exists()
        
        # Check new
        faq_new = self.article.faqs.exclude(id=faq_to_modify.id).first()
        assert faq_new.question == 'New Question 3?'
        assert faq_new.answer == 'New Answer 3.'
        assert faq_new.sort_order == 2

    def test_bulk_save_article_with_faqs(self):
        """Test importing and saving an article with FAQs using bulk saver service."""
        mapped_data = {
            'form_initial': {
                'title': 'mgal al-isteerad',
                'slug': 'bulk-import-article',
                'category': self.category.id,
                'content': '<p>mحتوى المقالة المستوردة</p>',
                'publish_status': 'published',
            },
            'image_paths': {},
            'faqs_data': [
                {
                    'question': 'Imported Question 1?',
                    'answer': 'Imported Answer 1.',
                },
                {
                    'question': 'Imported Question 2?',
                    'answer': 'Imported Answer 2.',
                }
            ]
        }
        
        instance, action_type = _save_article(mapped_data, self.user)
        assert action_type == 'created'
        assert instance.slug == 'bulk-import-article'
        
        # Verify FAQs are saved
        assert instance.faqs.count() == 2
        faq1 = instance.faqs.get(sort_order=0)
        assert faq1.question == 'Imported Question 1?'
        assert faq1.answer == 'Imported Answer 1.'
        
        # Verify WebP generation error in signals.py was handled gracefully or didn't break import
        faq2 = instance.faqs.get(sort_order=1)
        assert faq2.question == 'Imported Question 2?'
        assert faq2.answer == 'Imported Answer 2.'

    def test_article_publish_date_update(self):
        """Test that Article publish_date is editable in the dashboard and updates correctly."""
        from django.utils import timezone
        import datetime
        
        url = reverse('dashboard:article_edit', kwargs={'pk': self.article.pk})
        
        # 1. Test get response contains publish_date initial value formatted correctly
        response = self.client.get(url)
        assert response.status_code == 200
        form = response.context['form']
        assert 'publish_date' in form.initial
        assert form.initial['publish_date'] == self.article.publish_date.strftime('%Y-%m-%d')
        
        # 2. Test updating publish_date
        new_date_str = '2025-12-25'
        
        data = {
            'title': 'عنوان جديد',
            'slug': self.article.slug,
            'category': self.category.id,
            'content': self.article.content,
            'publish_status': self.article.publish_status,
            'publish_date': new_date_str,
            'faqs-TOTAL_FORMS': '0',
            'faqs-INITIAL_FORMS': '0',
            'faqs-MIN_NUM_FORMS': '0',
            'faqs-MAX_NUM_FORMS': '1000',
            
            # Attachment Formset fields
            'attachments-TOTAL_FORMS': '0',
            'attachments-INITIAL_FORMS': '0',
            'attachments-MIN_NUM_FORMS': '0',
            'attachments-MAX_NUM_FORMS': '1000',
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        # Refresh from DB and assert
        self.article.refresh_from_db()
        assert self.article.title == 'عنوان جديد'
        # Compare dates (ignoring hours and minutes since input is date-only)
        local_pub_date = timezone.localtime(self.article.publish_date)
        assert local_pub_date.year == 2025
        assert local_pub_date.month == 12
        assert local_pub_date.day == 25

