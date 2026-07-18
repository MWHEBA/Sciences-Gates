"""
Core abstract models for reusable functionality.
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


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
        max_length=150,
        blank=True,
        verbose_name='عنوان SEO',
        help_text='يظهر في نتائج البحث (150 حرف كحد أقصى)'
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
    keyphrase_synonyms = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='مرادفات الكلمة المفتاحية',
        help_text='مرادفات للكلمة المفتاحية الرئيسية مفصولة بفواصل (، أو ,)'
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
        max_length=150,
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

    # Phase 1 Analyzer Fields
    seo_score = models.PositiveIntegerField(
        default=0,
        verbose_name='درجة SEO'
    )
    seo_grade = models.CharField(
        max_length=20,
        default='needs_improvement',
        verbose_name='تقييم SEO'
    )
    seo_critical_count = models.PositiveIntegerField(
        default=0,
        verbose_name='الأخطاء الحرجة'
    )
    seo_warning_count = models.PositiveIntegerField(
        default=0,
        verbose_name='التحذيرات'
    )
    seo_last_analysis = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ آخر تحليل'
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
    
    # SEO Settings
    ga4_measurement_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Google Analytics 4 Measurement ID',
        help_text='معرف GA4 (مثال: G-XXXXXXXXXX) - يُستخدم لتتبع الزوار'
    )
    google_site_verification = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Google Site Verification Code',
        help_text='كود التحقق من Google Search Console'
    )
    enable_ga4 = models.BooleanField(
        default=True,
        verbose_name='تفعيل Google Analytics',
        help_text='تفعيل/إيقاف تتبع Google Analytics'
    )
    sitemap_last_generated = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخر توليد لخريطة الموقع'
    )
    
    # Maintenance Settings
    maintenance_mode = models.BooleanField(
        default=False,
        verbose_name='تفعيل وضع الصيانة',
        help_text='إغلاق الموقع للزوار وعرض صفحة الصيانة'
    )
    maintenance_title = models.CharField(
        max_length=200,
        default='صيانة مجدولة',
        verbose_name='عنوان صفحة الصيانة'
    )
    maintenance_message = models.TextField(
        default='الموقع قيد الصيانة حالياً لتقديم تجربة أفضل. سنعود قريباً.',
        verbose_name='رسالة صفحة الصيانة'
    )
    maintenance_estimated_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='موعد الانتهاء المتوقع',
        help_text='تحديد موعد الانتهاء يعرض عداداً تنازلياً ويساعد محركات البحث في جدولة الزيارة القادمة'
    )
    maintenance_bypass_ips = models.TextField(
        blank=True,
        verbose_name='عناوين IP المستثناة',
        help_text='أدخل عناوين IP المسموح لها بتصفح الموقع مفصولة بأسطر أو فواصل (مثال: 127.0.0.1)'
    )
    maintenance_bypass_staff = models.BooleanField(
        default=True,
        verbose_name='السماح لمدراء الموقع بالتصفح',
        help_text='عند التفعيل، يمكن للمستخدمين المسجلين دخولهم كـ Staff تصفح الموقع بشكل طبيعي'
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

    def update_maintenance_cache(self):
        """Write current maintenance state to a local JSON file to prevent DB hits."""
        import json
        from django.conf import settings
        from django.core.serializers.json import DjangoJSONEncoder
        
        cache_dir = settings.BASE_DIR / 'cache'
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / 'maintenance_state.json'
        
        data = {
            'maintenance_mode': self.maintenance_mode,
            'maintenance_title': self.maintenance_title,
            'maintenance_message': self.maintenance_message,
            'maintenance_estimated_end': self.maintenance_estimated_end.isoformat() if self.maintenance_estimated_end else None,
            'maintenance_bypass_ips': self.maintenance_bypass_ips,
            'maintenance_bypass_staff': self.maintenance_bypass_staff,
            'whatsapp': self.whatsapp,
            'email': self.email,
            'phone': self.phone,
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2)

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        self.pk = 1
        super().save(*args, **kwargs)
        try:
            self.update_maintenance_cache()
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        """Prevent deletion of the singleton instance."""
        pass

    @classmethod
    def get_settings(cls):
        """Get or create the singleton instance."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


@receiver(post_save, sender=SiteSettings)
def sync_maintenance_cache(sender, instance, **kwargs):
    """Sync maintenance cache file when SiteSettings is saved."""
    try:
        instance.update_maintenance_cache()
    except Exception:
        pass


    @property
    def whatsapp_list(self):
        """Get a list of WhatsApp numbers from the setting."""
        if not self.whatsapp:
            return []
        import re
        raw_list = re.split(r'[,;\s]+', self.whatsapp)
        clean_list = []
        for num in raw_list:
            cleaned = num.strip()
            if cleaned:
                clean_list.append(cleaned)
        return clean_list

    @property
    def whatsapp_primary(self):
        """Get the primary (first) WhatsApp number from the setting."""
        numbers = self.whatsapp_list
        return numbers[0] if numbers else None


    @property
    def facebook(self):
        """Placeholder for facebook link since the field doesn't exist in the database."""
        return None

    @property
    def instagram(self):
        """Placeholder for instagram link since the field doesn't exist in the database."""
        return None


def media_upload_path(instance, filename):
    """Generate dynamic upload path for MediaFile based on source type."""
    import os
    folder = instance.source_type or 'editor'
    return os.path.join(f'media_library/{folder}', filename)


class MediaFile(TimestampedModel):
    """Tracks all uploaded images in the system for centralized management."""
    
    class SourceType(models.TextChoices):
        EDITOR = 'editor', 'محرر المحتوى'
        UNIVERSITY_LOGO = 'university_logo', 'شعار جامعة'
        UNIVERSITY_IMAGE = 'university_image', 'صورة جامعة'
        INSTITUTE_LOGO = 'institute_logo', 'شعار معهد'
        INSTITUTE_IMAGE = 'institute_image', 'صورة معهد'
        MAJOR_IMAGE = 'major_image', 'صورة تخصص'
        ARTICLE_IMAGE = 'article_image', 'صورة مقالة'
    
    file = models.ImageField(upload_to=media_upload_path)
    original_filename = models.CharField(max_length=500)
    file_size = models.PositiveIntegerField(default=0)  # bytes
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    
    # SEO Fields (ordered by importance for 2026)
    alt_text = models.CharField(
        max_length=500, 
        blank=True, 
        verbose_name='النص البديل (Alt Text)',
        help_text='الأهم للـ SEO - وصف دقيق للصورة (80-140 حرف مثالي)'
    )
    caption = models.TextField(
        max_length=300, 
        blank=True, 
        verbose_name='التسمية التوضيحية (Caption)',
        help_text='نص مرئي يظهر للزوار أسفل الصورة - مفيد للسياق والـ SEO'
    )
    title = models.CharField(
        max_length=500, 
        blank=True, 
        verbose_name='عنوان الصورة (Title)',
        help_text='يظهر عند التمرير على الصورة'
    )
    description = models.TextField(
        blank=True,
        verbose_name='وصف داخلي',
        help_text='وصف تفصيلي للاستخدام الداخلي وإدارة المكتبة'
    )
    
    # Source tracking for WordPress imports
    source_url = models.URLField(
        max_length=1000,
        blank=True,
        verbose_name='رابط المصدر الأصلي',
        help_text='رابط الصورة في الموقع القديم (لمنع التكرار)',
        db_index=True
    )
    
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    
    # Generic FK for content object relation
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        verbose_name = 'ملف وسائط'
        verbose_name_plural = 'ملفات الوسائط'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source_type']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['alt_text']),
            models.Index(fields=['source_url']),
        ]

    @property
    def file_extension(self):
        """Returns the uppercase file extension of the original filename."""
        import os
        name = self.original_filename or self.file.name
        if not name:
            return ''
        _, ext = os.path.splitext(name)
        return ext.lstrip('.').upper()

    @property
    def completion_score(self):
        """Returns the number of filled SEO fields (0 to 4)."""
        score = 0
        if self.alt_text:
            score += 1
        if self.caption:
            score += 1
        if self.title:
            score += 1
        if self.description:
            score += 1
        return score

    def __str__(self):
        return self.original_filename


class ContentLock(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='content_locks'
    )
    client_token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = 'Content Lock'
        verbose_name_plural = 'Content Locks'
        unique_together = ('content_type', 'object_id')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Lock on {self.content_type.model} #{self.object_id} by {self.user.username}"


