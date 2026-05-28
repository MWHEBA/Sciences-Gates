"""
Core abstract models for reusable functionality.
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class TimestampedModel(models.Model):
    """Abstract base model providing timestamp fields."""
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )

    class Meta:
        abstract = True


class PublishStatus(models.TextChoices):
    """Publish status choices for content."""
    PUBLISHED = 'published', 'منشور'
    UNPUBLISHED = 'unpublished', 'غير منشور'


class PublishableModel(models.Model):
    """Abstract base model providing publish status."""
    publish_status = models.CharField(
        max_length=20,
        choices=PublishStatus.choices,
        default=PublishStatus.UNPUBLISHED,
        verbose_name='حالة النشر',
        help_text='المحتوى المنشور فقط يظهر للزوار',
        db_index=True
    )

    class Meta:
        abstract = True

    @property
    def is_published(self):
        """Check if content is published."""
        return self.publish_status == PublishStatus.PUBLISHED

    def publish(self):
        """Publish the content."""
        self.publish_status = PublishStatus.PUBLISHED
        self.save(update_fields=['publish_status'])

    def unpublish(self):
        """Unpublish the content."""
        self.publish_status = PublishStatus.UNPUBLISHED
        self.save(update_fields=['publish_status'])


class SEOMixin(models.Model):
    """Abstract mixin providing SEO fields for all content types."""
    # Basic SEO
    meta_title = models.CharField(
        max_length=60,
        blank=True,
        verbose_name='عنوان SEO',
        help_text='يظهر في نتائج البحث (60 حرف كحد أقصى)'
    )
    meta_description = models.TextField(
        max_length=160,
        blank=True,
        verbose_name='وصف SEO',
        help_text='يظهر في نتائج البحث (160 حرف كحد أقصى)'
    )
    focus_keyword = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='الكلمة المفتاحية',
        help_text='الكلمة المفتاحية الرئيسية للصفحة'
    )
    canonical_url = models.URLField(
        blank=True,
        verbose_name='الرابط الأساسي',
        help_text='اتركه فارغاً لاستخدام الرابط الافتراضي'
    )

    # Robots
    robots_index = models.BooleanField(
        default=True,
        verbose_name='السماح بالفهرسة',
        help_text='السماح لمحركات البحث بفهرسة هذه الصفحة'
    )
    robots_follow = models.BooleanField(
        default=True,
        verbose_name='السماح بتتبع الروابط',
        help_text='السماح لمحركات البحث بتتبع الروابط في هذه الصفحة'
    )
    sitemap_include = models.BooleanField(
        default=True,
        verbose_name='تضمين في خريطة الموقع',
        help_text='تضمين هذه الصفحة في ملف sitemap.xml'
    )

    # Open Graph
    og_title = models.CharField(
        max_length=60,
        blank=True,
        verbose_name='عنوان Open Graph',
        help_text='العنوان عند المشاركة على وسائل التواصل'
    )
    og_description = models.TextField(
        max_length=160,
        blank=True,
        verbose_name='وصف Open Graph',
        help_text='الوصف عند المشاركة على وسائل التواصل'
    )
    og_image = models.ImageField(
        upload_to='og_images/',
        blank=True,
        verbose_name='صورة Open Graph',
        help_text='الصورة عند المشاركة على وسائل التواصل (1200x630 بكسل)'
    )

    class Meta:
        abstract = True

    def get_meta_title(self):
        """Return meta title or fallback to main title."""
        return self.meta_title or getattr(self, 'name', '') or getattr(self, 'title', '')

    def get_meta_description(self):
        """Return meta description or generate from content."""
        if self.meta_description:
            return self.meta_description
        description = getattr(self, 'description', '')
        return description[:160] if description else ''

    def get_robots_content(self):
        """Generate robots meta tag content."""
        index = 'index' if self.robots_index else 'noindex'
        follow = 'follow' if self.robots_follow else 'nofollow'
        return f'{index}, {follow}'

    def get_og_title(self):
        """Return OG title or fallback to meta title."""
        return self.og_title or self.get_meta_title()

    def get_og_description(self):
        """Return OG description or fallback to meta description."""
        return self.og_description or self.get_meta_description()

    def get_og_image_url(self):
        """Return OG image URL or fallback to main image."""
        if self.og_image:
            return self.og_image.url
        main_image = getattr(self, 'main_image', None) or getattr(self, 'featured_image', None)
        return main_image.url if main_image else None


class UserRole(models.TextChoices):
    """User role choices for dashboard access control."""
    SUPER_ADMIN = 'super_admin', 'مسؤول النظام'
    CONTENT_ADMIN = 'content_admin', 'مسؤول المحتوى'
    SEO_ADMIN = 'seo_admin', 'مسؤول SEO'


class UserProfile(models.Model):
    """User profile model with role management for dashboard access control."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='المستخدم'
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CONTENT_ADMIN,
        verbose_name='الدور',
        help_text='دور المستخدم في لوحة التحكم'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )

    class Meta:
        verbose_name = 'ملف المستخدم'
        verbose_name_plural = 'ملفات المستخدمين'

    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'

    @property
    def is_super_admin(self):
        """Check if user is super admin."""
        return self.role == UserRole.SUPER_ADMIN

    @property
    def is_content_admin(self):
        """Check if user is content admin."""
        return self.role == UserRole.CONTENT_ADMIN

    @property
    def is_seo_admin(self):
        """Check if user is SEO admin."""
        return self.role == UserRole.SEO_ADMIN


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile automatically when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class SiteSettings(models.Model):
    """Singleton model for site-wide settings."""
    # Singleton pattern - only one instance should exist
    id = models.AutoField(primary_key=True)
    
    # Registration Steps Section
    registration_steps_title = models.CharField(
        max_length=200,
        default='خطوات التسجيل',
        verbose_name='عنوان قسم خطوات التسجيل',
        help_text='العنوان الذي يظهر في جميع صفحات الجامعات'
    )
    registration_steps_content = models.TextField(
        blank=True,
        verbose_name='محتوى خطوات التسجيل',
        help_text='محتوى HTML يظهر في جميع صفحات الجامعات (يدعم HTML)'
    )
    
    # General Settings
    site_name = models.CharField(
        max_length=200,
        default='بوابات العلوم',
        verbose_name='اسم الموقع'
    )
    site_description = models.TextField(
        blank=True,
        verbose_name='وصف الموقع'
    )
    
    # Contact Information
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='رقم الهاتف'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='البريد الإلكتروني'
    )
    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='رقم WhatsApp'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )

    class Meta:
        verbose_name = 'إعدادات الموقع'
        verbose_name_plural = 'إعدادات الموقع'

    def __str__(self):
        return 'إعدادات الموقع'

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of the singleton instance."""
        pass

    @classmethod
    def get_settings(cls):
        """Get or create the singleton instance."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

    @property
    def facebook(self):
        """Placeholder for facebook link since the field doesn't exist in the database."""
        return None

    @property
    def instagram(self):
        """Placeholder for instagram link since the field doesn't exist in the database."""
        return None

