import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.articles.models import Article, Category
from apps.core.models import MediaFile
from apps.dashboard.forms.article import ArticleForm
from apps.dashboard.forms.university import UniversityForm
from apps.dashboard.forms.institute import InstituteForm
from apps.dashboard.forms.major import MajorForm

User = get_user_model()


@pytest.mark.django_db
class TestArticleSEOAltDashboard:
    """Test cases for Article featured image SEO alt text preservation in the dashboard."""

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
        
        # Create a mock GIF file
        gif_bytes = b'GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x04\x00;'
        self.image1 = SimpleUploadedFile("sunset.gif", gif_bytes, content_type="image/gif")
        self.image2 = SimpleUploadedFile("sunrise.gif", gif_bytes, content_type="image/gif")
        
        self.article = Article.objects.create(
            title='دليل الدراسة في ماليزيا',
            slug='study-malaysia',
            category=self.category,
            author=self.user,
            content='<p>محتوى المقالة</p>',
            featured_image=self.image1,
            publish_status='published'
        )

    def test_form_fields_exclusion(self):
        """Verify that alt text fields are excluded from dashboard form classes."""
        assert 'featured_image_alt' not in ArticleForm().fields
        assert 'logo_alt' not in UniversityForm().fields
        assert 'main_image_alt' not in UniversityForm().fields
        assert 'logo_alt' not in InstituteForm().fields
        assert 'main_image_alt' not in InstituteForm().fields
        assert 'main_image_alt' not in MajorForm().fields

    def test_alt_text_preservation_on_form_save(self):
        """Test that updating an article via the main form preserves the existing alt text."""
        # 1. Verify MediaFile was created via signal and initially has empty alt text
        media_file = MediaFile.objects.filter(
            content_type=ContentType.objects.get_for_model(Article),
            object_id=self.article.pk
        ).first()
        assert media_file is not None
        assert media_file.alt_text == ''
        assert self.article.featured_image_alt == ''

        # 2. Simulate AJAX modal update by setting alt text on both objects
        media_file.alt_text = 'Beautiful sunset image'
        media_file.save()
        
        self.article.featured_image_alt = 'Beautiful sunset image'
        self.article.save()

        # Verify initial database state
        media_file.refresh_from_db()
        self.article.refresh_from_db()
        assert media_file.alt_text == 'Beautiful sunset image'
        assert self.article.featured_image_alt == 'Beautiful sunset image'

        # 3. Submit main Article edit form POST (which doesn't contain featured_image_alt field)
        url = reverse('dashboard:article_edit', kwargs={'pk': self.article.pk})
        
        # We pass the same image path and main fields but omit featured_image_alt
        data = {
            'title': 'عنوان جديد للمقالة',
            'slug': 'study-malaysia',
            'category': self.category.id,
            'content': '<p>محتوى جديد</p>',
            'publish_status': 'published',
            # Simulating keeping the same image without re-uploading
            'imported_main_image_path': self.article.featured_image.url,
            
            # FAQ Formset fields (required by the view)
            'faqs-TOTAL_FORMS': '0',
            'faqs-INITIAL_FORMS': '0',
            'faqs-MIN_NUM_FORMS': '0',
            'faqs-MAX_NUM_FORMS': '1000',
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        # 4. Assert that the alt text was PRESERVED in both database objects
        self.article.refresh_from_db()
        media_file.refresh_from_db()
        
        assert self.article.featured_image_alt == 'Beautiful sunset image'
        assert media_file.alt_text == 'Beautiful sunset image'

    def test_alt_text_cleared_on_image_change(self):
        """Test that replacing the image clears the alt text because it's a new file."""
        # 1. Set initial alt text
        media_file = MediaFile.objects.filter(
            content_type=ContentType.objects.get_for_model(Article),
            object_id=self.article.pk
        ).first()
        media_file.alt_text = 'Old image alt text'
        media_file.save()
        self.article.featured_image_alt = 'Old image alt text'
        self.article.save()

        # 2. Upload a NEW image via the main edit form
        url = reverse('dashboard:article_edit', kwargs={'pk': self.article.pk})
        data = {
            'title': 'تعديل مع تغيير الصورة',
            'slug': 'study-malaysia',
            'category': self.category.id,
            'content': '<p>محتوى جديد</p>',
            'publish_status': 'published',
            'featured_image': self.image2,  # Uploading a new image file
            
            # FAQ Formset fields (required by the view)
            'faqs-TOTAL_FORMS': '0',
            'faqs-INITIAL_FORMS': '0',
            'faqs-MIN_NUM_FORMS': '0',
            'faqs-MAX_NUM_FORMS': '1000',
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 302

        # 3. Assert that both Article and MediaFile alt texts are now reset/cleared
        self.article.refresh_from_db()
        
        # Fetch the updated/re-synced MediaFile
        media_file.refresh_from_db()
        
        assert self.article.featured_image_alt == ''
        assert media_file.alt_text == ''
