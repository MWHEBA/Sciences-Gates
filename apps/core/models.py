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
        if self.robots_index:
            return f'{index}, {follow}, max-image-preview:large, max-snippet:-1, max-video-preview:-1'
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

    def clean(self):
        """Validate unique meta title among published records of the same model."""
        super().clean()
        if self.meta_title:
            publish_status = getattr(self, 'publish_status', None)
            if publish_status == 'published':
                queryset = self.__class__.objects.filter(
                    meta_title=self.meta_title,
                    publish_status='published'
                )
                if self.pk:
                    queryset = queryset.exclude(pk=self.pk)
                if queryset.exists():
                    from django.core.exceptions import ValidationError
                    raise ValidationError({
                        'meta_title': 'عنوان SEO هذا مستخدم بالفعل في صفحة أخرى منشورة. يرجى اختيار عنوان فريد لتجنب عقوبات المحتوى المكرر.'
                    })


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
    receive_registration_emails = models.BooleanField(
        default=True,
        verbose_name='استقبال إيميلات التسجيل',
        help_text='تفعيل استقبال إشعارات طلبات التسجيل الجديدة عبر البريد الإلكتروني'
    )
    receive_inquiry_emails = models.BooleanField(
        default=True,
        verbose_name='استقبال إيميلات الاستفسارات',
        help_text='تفعيل استقبال إشعارات الاستفسارات الجديدة عبر البريد الإلكتروني'
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
        return self.role == UserRole.SUPER_ADMIN or getattr(self.user, 'is_superuser', False)

    @property
    def is_content_admin(self):
        """Check if user is content admin."""
        return self.role == UserRole.CONTENT_ADMIN or self.is_super_admin

    @property
    def is_seo_admin(self):
        """Check if user is SEO admin."""
        return self.role == UserRole.SEO_ADMIN or self.is_super_admin


class AuthorProfile(models.Model):
    """
    Author profile model for E-E-A-T credentials and Person JSON-LD Schema.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='author_profile',
        verbose_name='حساب المستخدم'
    )
    name = models.CharField(
        max_length=200,
        default='د. محمد الكيالي',
        verbose_name='اسم الكاتب'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        default='dr-mohammad-kayali',
        verbose_name='رابط الكاتب'
    )
    title_credentials = models.CharField(
        max_length=250,
        default='دكتوراه في علوم الحاسوب (UKM) - خبير الاستشارات التعليمية في ماليزيا',
        verbose_name='المؤهل واللقب المهني'
    )
    bio = models.TextField(
        default='مؤسس ومدير شركة بوابات العلوم للدراسة في ماليزيا. حاصل على درجة الدكتوراه في علوم الحاسوب من جامعة UKM الماليزية، يملك أكثر من 10 سنوات خبرة في تقديم الاستشارات الأكاديمية وإرشادات القبول الجامعي لأكثر من 3000 طالب عربي.',
        verbose_name='السيرة الذاتية والخبرة'
    )
    avatar = models.ImageField(
        upload_to='authors/',
        blank=True,
        null=True,
        verbose_name='صورة الكاتب'
    )
    linkedin_url = models.URLField(
        blank=True,
        default='https://www.linkedin.com/in/mohammad-kayali/',
        verbose_name='رابط لينكد إن'
    )
    university_profile_url = models.URLField(
        blank=True,
        default='https://www.ukm.my/',
        verbose_name='رابط الملف الجامعي / الرسمي'
    )

    class Meta:
        verbose_name = 'ملف الكاتب (E-E-A-T)'
        verbose_name_plural = 'ملفات الكتاب (E-E-A-T)'

    def __str__(self):
        return f'{self.name} - {self.title_credentials}'

    @property
    def same_as_urls(self):
        urls = []
        if self.linkedin_url:
            urls.append(self.linkedin_url)
        if self.university_profile_url:
            urls.append(self.university_profile_url)
        return urls


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
        default='شركة بوابات العلوم',
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
    
    # Social Media Links
    facebook = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='رابط فيسبوك'
    )
    instagram = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='رابط انستغرام'
    )
    twitter = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='رابط منصة X (تويتر)'
    )
    youtube = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='رابط يوتيوب'
    )
    linkedin = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='رابط لينكد إن'
    )
    tiktok = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='رابط تيك توك'
    )
    telegram = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='رابط تليجرام'
    )
    snapchat = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='رابط سناب شات'
    )
    
    # SEO Settings
    ga4_measurement_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Google Analytics 4 Measurement ID',
        help_text='معرف GA4 (مثال: G-XXXXXXXXXX) - يُسخدم لتتبع الزوار'
    )
    ga4_property_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Google Analytics 4 Property ID',
        help_text='معرف الخاصية الرقمي في GA4 (مثال: 448834920) - يُسخدم لجلب بيانات التقارير'
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
    sitemap_last_submitted = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخر إرسال لخريطة الموقع لجوجل'
    )
    sitemap_gsc_status = models.CharField(
        max_length=255,
        default='لم يتم الإرسال بعد',
        verbose_name='حالة الإرسال لمحرك بحث جوجل'
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
    
    # Dynamic SMTP Settings
    email_smtp_use_dynamic = models.BooleanField(
        default=False,
        verbose_name='تفعيل إعدادات SMTP مخصصة',
        help_text='عند التفعيل، سيقوم النظام بإرسال رسائل البريد الإلكتروني باستخدام هذه الإعدادات بدلاً من الإعدادات الافتراضية في ملف .env'
    )
    email_smtp_host = models.CharField(
        max_length=255,
        default='smtp.gmail.com',
        blank=True,
        verbose_name='خادم SMTP',
        help_text='عنوان خادم SMTP الخاص بمزود الخدمة (مثال لـ Google Workspace: smtp.gmail.com)'
    )
    email_smtp_port = models.PositiveIntegerField(
        default=587,
        verbose_name='منفذ SMTP',
        help_text='المنفذ المستخدم للإرسال (مثال: 587 للـ TLS أو 465 للـ SSL)'
    )
    email_smtp_user = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='اسم مستخدم SMTP',
        help_text='البريد الإلكتروني بالكامل المستخدم لتسجيل الدخول (مثال: mail@sciencesgates.com)'
    )
    email_smtp_password = models.CharField(
        max_length=1000,
        blank=True,
        verbose_name='كلمة مرور SMTP',
        help_text='كلمة مرور الحساب. في حالة استخدام Google Workspace، يرجى إنشاء واستخدام كلمة مرور تطبيق (App Password).'
    )
    email_smtp_use_tls = models.BooleanField(
        default=True,
        verbose_name='تفعيل TLS',
        help_text='تأمين الاتصال باستخدام TLS (مستحسن ومطلوب للمنفذ 587)'
    )
    email_smtp_use_ssl = models.BooleanField(
        default=False,
        verbose_name='تفعيل SSL',
        help_text='تأمين الاتصال باستخدام SSL (مستحسن ومطلوب للمنفذ 465)'
    )
    email_from_address = models.EmailField(
        default='noreply@example.com',
        blank=True,
        verbose_name='بريد المرسل الافتراضي',
        help_text='البريد الذي سيظهر للمستلمين كمستلم للرسالة (مثال: noreply@sciencesgates.com)'
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
            'whatsapp': self.whatsapp_primary_clean,
            'email': self.email,
            'phone': self.phone,
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2)

    def update_smtp_cache(self):
        """Write current SMTP settings to a local JSON file to prevent DB hits."""
        import json
        from django.conf import settings
        
        cache_dir = settings.BASE_DIR / 'cache'
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / 'smtp_config.json'
        
        data = {
            'email_smtp_use_dynamic': self.email_smtp_use_dynamic,
            'email_smtp_host': self.email_smtp_host,
            'email_smtp_port': self.email_smtp_port,
            'email_smtp_user': self.email_smtp_user,
            'email_smtp_password': self.email_smtp_password,  # Stored encrypted
            'email_smtp_use_tls': self.email_smtp_use_tls,
            'email_smtp_use_ssl': self.email_smtp_use_ssl,
            'email_from_address': self.email_from_address,
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern) and normalize social URLs."""
        self.pk = 1
        self.facebook = self.clean_social_url(self.facebook)
        self.instagram = self.clean_social_url(self.instagram)
        self.twitter = self.clean_social_url(self.twitter)
        self.youtube = self.clean_social_url(self.youtube)
        self.linkedin = self.clean_social_url(self.linkedin)
        self.tiktok = self.clean_social_url(self.tiktok)
        self.telegram = self.clean_social_url(self.telegram)
        self.snapchat = self.clean_social_url(self.snapchat)
        super().save(*args, **kwargs)
        try:
            from django.core.cache import cache
            cache.delete('site_settings_instance')
        except Exception:
            pass
        try:
            self.update_maintenance_cache()
        except Exception:
            pass
        try:
            self.update_smtp_cache()
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        """Prevent deletion of the singleton instance."""
        pass

    @classmethod
    def get_settings(cls):
        """Get or create the singleton instance with caching."""
        from django.core.cache import cache
        try:
            settings_inst = cache.get('site_settings_instance')
            if not settings_inst:
                settings_inst, _ = cls.objects.get_or_create(pk=1)
                cache.set('site_settings_instance', settings_inst, 86400)
            return settings_inst
        except Exception:
            settings_inst, _ = cls.objects.get_or_create(pk=1)
            return settings_inst

    @staticmethod
    def clean_social_url(url):
        """Ensure social URL starts with http:// or https://."""
        if not url:
            return ""
        url = url.strip()
        if not url:
            return ""
        if not (url.startswith('http://') or url.startswith('https://')):
            return f"https://{url}"
        return url

    @staticmethod
    def clean_whatsapp_number(number):
        """Clean a phone number for use in WhatsApp wa.me links."""
        if not number:
            return ""
        import re
        # Strip all non-digits
        cleaned = re.sub(r'\D', '', number)
        # Strip leading '00' if present
        if cleaned.startswith('00'):
            cleaned = cleaned[2:]
        # Remove redundant zero after common country codes
        # Egypt: 2001... -> 201...
        if cleaned.startswith('2001'):
            cleaned = '20' + cleaned[3:]
        # Saudi Arabia: 96605... -> 9665...
        elif cleaned.startswith('96605'):
            cleaned = '966' + cleaned[4:]
        # Malaysia: 6001... -> 601...
        elif cleaned.startswith('6001'):
            cleaned = '60' + cleaned[3:]
        return cleaned

    @property
    def whatsapp_list(self):
        """Get a list of WhatsApp numbers from the setting."""
        if not self.whatsapp:
            return []
        import re
        # Split by comma or semicolon
        raw_list = re.split(r'[,;]+', self.whatsapp)
        # If there are no commas or semicolons, but there are multiple numbers starting with '+' or clearly separated, we handle that.
        if ',' not in self.whatsapp and ';' not in self.whatsapp:
            temp_parts = re.split(r'\s+', self.whatsapp.strip())
            is_multiple = len(temp_parts) > 1 and all(len(re.sub(r'\D', '', p)) >= 7 for p in temp_parts)
            if is_multiple:
                raw_list = temp_parts
        
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
    def whatsapp_primary_clean(self):
        """Get the primary WhatsApp number cleaned for use in API links (digits only, no leading + or 00)."""
        primary = self.whatsapp_primary
        return self.clean_whatsapp_number(primary)

    @property
    def phone_clean(self):
        """Get the phone number cleaned for use in tel: links."""
        if not self.phone:
            return ""
        import re
        cleaned = re.sub(r'[^\d+]', '', self.phone.strip())
        return cleaned

    @staticmethod
    def format_display_number(number):
        """Format a phone number cleanly with spaces (e.g. +60 12 345 6789 or +20 122 960 9292)."""
        if not number:
            return ""
        import re
        cleaned = re.sub(r'[^\d+]', '', number.strip())
        if not cleaned.startswith('+'):
            if cleaned.startswith('00'):
                cleaned = '+' + cleaned[2:]
            else:
                cleaned = '+' + cleaned
        
        if cleaned.startswith('+60'):
            digits = cleaned[3:]
            if len(digits) == 9:
                return f"+60 {digits[0:2]} {digits[2:5]} {digits[5:]}"
            elif len(digits) == 10:
                return f"+60 {digits[0:2]} {digits[2:6]} {digits[6:]}"
        
        if cleaned.startswith('+20'):
            digits = cleaned[3:]
            if len(digits) == 10:
                return f"+20 {digits[0:3]} {digits[3:6]} {digits[6:]}"
            elif len(digits) == 9:
                return f"+20 {digits[0:2]} {digits[2:5]} {digits[5:]}"

        return cleaned

    @property
    def phone_formatted(self):
        """Get the phone number formatted for display."""
        if not self.phone:
            return ""
        return self.format_display_number(self.phone)

    @property
    def whatsapp_primary_formatted(self):
        """Get the primary WhatsApp number formatted for display."""
        primary = self.whatsapp_primary
        if not primary:
            return ""
        return self.format_display_number(primary)

    @property
    def social_links(self):
        """Return list of active social media profiles with metadata."""
        links = []
        if self.facebook:
            links.append({'key': 'facebook', 'name': 'فيسبوك', 'url': self.facebook, 'icon': 'facebook'})
        if self.instagram:
            links.append({'key': 'instagram', 'name': 'انستغرام', 'url': self.instagram, 'icon': 'instagram'})
        if self.twitter:
            links.append({'key': 'twitter', 'name': 'X (تويتر)', 'url': self.twitter, 'icon': 'twitter'})
        if self.youtube:
            links.append({'key': 'youtube', 'name': 'يوتيوب', 'url': self.youtube, 'icon': 'youtube'})
        if self.linkedin:
            links.append({'key': 'linkedin', 'name': 'لينكد إن', 'url': self.linkedin, 'icon': 'linkedin'})
        if self.tiktok:
            links.append({'key': 'tiktok', 'name': 'تيك توك', 'url': self.tiktok, 'icon': 'tiktok'})
        if self.telegram:
            links.append({'key': 'telegram', 'name': 'تليجرام', 'url': self.telegram, 'icon': 'telegram'})
        if self.snapchat:
            links.append({'key': 'snapchat', 'name': 'سناب شات', 'url': self.snapchat, 'icon': 'snapchat'})
        if self.whatsapp_primary_clean:
            links.append({'key': 'whatsapp', 'name': 'واتساب', 'url': f'https://wa.me/{self.whatsapp_primary_clean}', 'icon': 'whatsapp'})
        return links

    @property
    def whatsapp_list_parsed(self):
        """Get a list of parsed WhatsApp numbers (each is a dict with 'raw' and 'clean' keys)."""
        numbers = self.whatsapp_list
        parsed = []
        for num in numbers:
            parsed.append({
                'raw': num,
                'clean': self.clean_whatsapp_number(num)
            })
        return parsed



@receiver(post_save, sender=SiteSettings)
def sync_maintenance_cache(sender, instance, **kwargs):
    """Sync maintenance cache file when SiteSettings is saved."""
    try:
        instance.update_maintenance_cache()
    except Exception:
        pass


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


class GA4CachedReport(models.Model):
    """
    Model for caching Google Analytics 4 API reports locally.
    """
    days = models.IntegerField(unique=True, verbose_name="عدد الأيام")
    payload = models.JSONField(verbose_name="بيانات التقرير")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "تقرير GA4 مخزن مؤقتاً"
        verbose_name_plural = "تقارير GA4 مخزنة مؤقتاً"

    def __str__(self):
        return f"GA4 Report ({self.days} days) - {self.updated_at}"


class SiteNavigation(TimestampedModel):
    """
    Model for managing curated navigation slots for Mega Menu and Homepage.
    إدارة التخصيص بالخانات الثابتة للقوائم والصفحة الرئيسية
    """
    SECTION_CHOICES = [
        ('mega_menu_public_univ', 'القائمة الرئيسية - جامعات حكومية'),
        ('mega_menu_private_univ', 'القائمة الرئيسية - جامعات خاصة'),
        ('mega_menu_institute', 'القائمة الرئيسية - معاهد اللغة'),
        ('home_featured_univ', 'الصفحة الرئيسية - جامعات مميزة'),
        ('home_featured_institute', 'الصفحة الرئيسية - معاهد مميزة'),
        ('home_featured_major', 'الصفحة الرئيسية - تخصصات مميزة'),
    ]

    section = models.CharField(
        max_length=50,
        choices=SECTION_CHOICES,
        verbose_name='القسم',
        db_index=True
    )
    slot_number = models.PositiveIntegerField(
        verbose_name='رقم الخانة',
        help_text='رقم الخانة (من 1 إلى الحد الأقصى للقسم)'
    )
    university = models.ForeignKey(
        'universities.University',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='navigation_slots',
        verbose_name='الجامعة'
    )
    institute = models.ForeignKey(
        'institutes.Institute',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='navigation_slots',
        verbose_name='المعهد'
    )
    major = models.ForeignKey(
        'majors.Major',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='navigation_slots',
        verbose_name='التخصص'
    )

    class Meta:
        verbose_name = 'تخصيص خانة قائمة'
        verbose_name_plural = 'تخصيصات خانات القوائم'
        unique_together = ('section', 'slot_number')
        ordering = ['section', 'slot_number']

    def __str__(self):
        return f"{self.get_section_display()} - خانة {self.slot_number}"


class ContentVersion(models.Model):
    """
    Model for storing content snapshots / version history (max 5 versions per object).
    """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='نوع المحتوى'
    )
    object_id = models.PositiveIntegerField(
        verbose_name='معرف المحتوى'
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    version_number = models.PositiveIntegerField(
        verbose_name='رقم النسخة'
    )
    data = models.JSONField(
        verbose_name='بيانات النسخة',
        help_text='لقطة من بيانات الموديل والعلاقات المخزنة كـ JSON'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='content_versions',
        verbose_name='أنشئت بواسطة'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الحفظ'
    )
    change_reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='سبب التعديل'
    )

    class Meta:
        verbose_name = 'نسخة محتوى'
        verbose_name_plural = 'نسخ المحتوى'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.content_type.model} #{self.object_id} - v{self.version_number}"





