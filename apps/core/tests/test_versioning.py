"""
Tests for ContentVersion and VersioningService.
"""
import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from apps.articles.models import Article, Category
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.core.models import ContentVersion
from apps.core.services.versioning import VersioningService


@pytest.mark.django_db
class TestContentVersioning:
    """Test suite for pre-save version snapshotting and restoration."""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.user = User.objects.create_user(username='testeditor', password='password123')
        self.category = Category.objects.create(name='اختبارات', slug='tests')
        self.article = Article.objects.create(
            title='المقال الأصلي',
            slug='original-article-slug',
            content='<p>محتوى المقال الأصلي</p>',
            category=self.category,
            meta_title='SEO Title Original',
            meta_description='SEO Meta Original'
        )

    def test_pre_save_snapshot_creation_and_seo_exclusion(self):
        """Verify pre-save snapshot captures DB state and excludes SEO & slug fields."""
        # Update article title and content
        self.article.title = 'المقال المعدل الأول'
        self.article.content = '<p>المحتوى الجديد 1</p>'
        
        version = VersioningService.capture_pre_save_snapshot(
            self.article, 
            user=self.user, 
            change_reason='التعديل الأول'
        )
        self.article.save()

        assert version is not None
        assert version.version_number == 1
        assert version.data['title'] == 'المقال الأصلي'
        assert 'slug' not in version.data
        assert 'meta_title' not in version.data
        assert 'meta_description' not in version.data

    def test_max_5_versions_pruning_limit(self):
        """Verify that older versions beyond 5 are automatically pruned."""
        for i in range(1, 8):
            self.article.title = f'تعديل رقم {i}'
            VersioningService.capture_pre_save_snapshot(
                self.article,
                user=self.user,
                change_reason=f'تعديل {i}'
            )
            self.article.save()

        versions = VersioningService.get_versions(self.article)
        assert len(versions) == 5
        # Ensure latest 5 remain
        version_numbers = [v.version_number for v in versions]
        assert version_numbers == [7, 6, 5, 4, 3]

    def test_version_restoration_preserves_active_seo_and_slug(self):
        """Verify restoration updates body content while keeping active SEO & URL slug intact."""
        # Version 1 snapshot captured
        self.article.title = 'تعديل 2'
        self.article.content = '<p>محتوى 2</p>'
        v1 = VersioningService.capture_pre_save_snapshot(
            self.article, 
            user=self.user, 
            change_reason='تعديل 1'
        )
        self.article.save()

        # Active SEO & Slug changed on live record
        self.article.slug = 'new-active-slug'
        self.article.meta_title = 'New Active SEO Title'
        self.article.save()

        # Restore Version 1
        restored = VersioningService.restore_version(v1.id, user=self.user)
        assert restored is not None
        assert restored.title == 'المقال الأصلي'
        assert restored.content == '<p>محتوى المقال الأصلي</p>'
        # Slug and SEO remain untouched
        assert restored.slug == 'new-active-slug'
        assert restored.meta_title == 'New Active SEO Title'

    def test_university_versioning(self):
        """Verify versioning works seamlessly on University model."""
        uni = University.objects.create(
            name='جامعة كوالالمبور',
            slug='unikl',
            description='وصف الجامعة الأصلي'
        )
        
        uni.description = 'وصف الجامعة الجديد'
        version = VersioningService.capture_pre_save_snapshot(
            uni,
            user=self.user,
            change_reason='تحديث وصف الجامعة'
        )
        uni.save()

        assert version is not None
        assert version.data['name'] == 'جامعة كوالالمبور'
        assert version.data['description'] == 'وصف الجامعة الأصلي'
        assert 'slug' not in version.data

    def test_institute_versioning(self):
        """Verify versioning works seamlessly on Institute model."""
        inst = Institute.objects.create(
            name='معهد التكنولوجيا',
            slug='tech-inst',
            description='وصف المعهد الأصلي'
        )

        inst.description = 'وصف المعهد الجديد'
        version = VersioningService.capture_pre_save_snapshot(
            inst,
            user=self.user,
            change_reason='تحديث وصف المعهد'
        )
        inst.save()

        assert version is not None
        assert version.data['name'] == 'معهد التكنولوجيا'
        assert version.data['description'] == 'وصف المعهد الأصلي'

    def test_major_versioning(self):
        """Verify versioning works seamlessly on Major model."""
        major = Major.objects.create(
            name='هندسة البرمجيات',
            slug='software-engineering',
            description='وصف التخصص الأصلي'
        )

        major.description = 'وصف التخصص الجديد'
        version = VersioningService.capture_pre_save_snapshot(
            major,
            user=self.user,
            change_reason='تحديث وصف التخصص'
        )
        major.save()

        assert version is not None
        assert version.data['name'] == 'هندسة البرمجيات'
        assert version.data['description'] == 'وصف التخصص الأصلي'
