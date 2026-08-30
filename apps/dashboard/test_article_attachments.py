import pytest
import os
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.articles.models import Article, ArticleAttachment, Category
from apps.core.utils import validate_attachment_file

User = get_user_model()


@pytest.mark.django_db
class TestArticleAttachmentValidation:
    """Test case for ArticleAttachment validation and cleanup."""

    def test_file_size_validation(self):
        """Test that file sizes over 30MB are rejected."""
        # Create a mock file with size 31MB
        large_file = SimpleUploadedFile("large.pdf", b"a" * (31 * 1024 * 1024))
        with pytest.raises(ValidationError) as exc_info:
            validate_attachment_file(large_file)
        assert 'حجم الملف كبير جداً' in str(exc_info.value)

        # File size 29MB should pass
        small_file = SimpleUploadedFile("small.pdf", b"a" * (29 * 1024 * 1024))
        validate_attachment_file(small_file)  # Should not raise exception

    def test_file_extension_validation(self):
        """Test that only allowed extensions are accepted."""
        # Allowed extension (pdf) should pass
        ok_file = SimpleUploadedFile("test.pdf", b"dummy content")
        validate_attachment_file(ok_file)

        # Disallowed extension (exe) should fail
        bad_file = SimpleUploadedFile("malicious.exe", b"dummy content")
        with pytest.raises(ValidationError) as exc_info:
            validate_attachment_file(bad_file)
        assert 'امتداد الملف غير مسموح به' in str(exc_info.value)


@pytest.mark.django_db
class TestArticleAttachmentDashboard:
    """Test cases for Article Attachment management in the dashboard."""

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
            featured_image='articles/test.jpg',
            publish_status='published'
        )

    def test_article_create_view_with_attachments(self):
        """Test creating an article with attachments in dashboard view."""
        url = reverse('dashboard:article_create')
        
        # Create a mock 1x1 valid GIF image to satisfy Pillow validation in ImageField
        gif_bytes = b'GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x04\x00;'
        mock_image = SimpleUploadedFile("test_image.gif", gif_bytes, content_type="image/gif")
        mock_pdf = SimpleUploadedFile("guide.pdf", b"PDF content", content_type="application/pdf")
        
        data = {
            'title': 'مقالة جديدة مع مرفقات',
            'slug': 'new-article-with-attachments',
            'category': self.category.id,
            'content': '<p>محتوى المقال</p>',
            'publish_status': 'published',
            'featured_image': mock_image,
            
            # FAQ Formset (required for validation)
            'faqs-TOTAL_FORMS': '0',
            'faqs-INITIAL_FORMS': '0',
            'faqs-MIN_NUM_FORMS': '0',
            'faqs-MAX_NUM_FORMS': '1000',
            
            # Attachment Formset fields
            'attachments-TOTAL_FORMS': '1',
            'attachments-INITIAL_FORMS': '0',
            'attachments-MIN_NUM_FORMS': '0',
            'attachments-MAX_NUM_FORMS': '1000',
            
            'attachments-0-id': '',
            'attachments-0-title': 'دليل التسجيل للطلاب',
            'attachments-0-file': mock_pdf,
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        new_article = Article.objects.get(slug='new-article-with-attachments')
        assert new_article.attachments.count() == 1
        
        attachment = new_article.attachments.first()
        assert attachment.title == 'دليل التسجيل للطلاب'
        assert attachment.file_size > 0
        
        # Clean up files created
        if attachment.file:
            attachment.file.delete(save=False)

    def test_article_update_view_attachment_cleanup(self):
        """Test file cleanup on updating/replacing and deleting attachments."""
        mock_file1 = SimpleUploadedFile("original.pdf", b"Original content", content_type="application/pdf")
        attachment = ArticleAttachment.objects.create(
            article=self.article,
            title='الملف الأصلي',
            file=mock_file1
        )
        
        file_path = attachment.file.path
        assert os.path.exists(file_path)
        
        # 1. Test update (replacing the file)
        url = reverse('dashboard:article_edit', kwargs={'pk': self.article.pk})
        mock_file2 = SimpleUploadedFile("replacement.pdf", b"Replacement content", content_type="application/pdf")
        
        data = {
            'title': self.article.title,
            'slug': self.article.slug,
            'category': self.category.id,
            'content': self.article.content,
            'publish_status': self.article.publish_status,
            'featured_image': 'articles/test.jpg',
            
            # FAQ Formset
            'faqs-TOTAL_FORMS': '0',
            'faqs-INITIAL_FORMS': '0',
            'faqs-MIN_NUM_FORMS': '0',
            'faqs-MAX_NUM_FORMS': '1000',
            
            # Attachment Formset
            'attachments-TOTAL_FORMS': '1',
            'attachments-INITIAL_FORMS': '1',
            'attachments-MIN_NUM_FORMS': '0',
            'attachments-MAX_NUM_FORMS': '1000',
            
            'attachments-0-id': attachment.id,
            'attachments-0-title': 'الملف المحدث',
            'attachments-0-file': mock_file2,
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        # Original file should be deleted from disk
        assert not os.path.exists(file_path)
        
        attachment.refresh_from_db()
        assert attachment.title == 'الملف المحدث'
        new_file_path = attachment.file.path
        assert os.path.exists(new_file_path)
        
        # 2. Test deletion
        data['attachments-0-DELETE'] = 'on'
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        # Both model and physical file should be deleted
        assert not ArticleAttachment.objects.filter(id=attachment.id).exists()
        assert not os.path.exists(new_file_path)
