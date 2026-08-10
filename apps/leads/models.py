from django.db import models
from apps.core.models import TimestampedModel
from urllib.parse import unquote, urlparse


class LeadType(models.TextChoices):
    """Lead type choices."""
    REGISTRATION = 'registration', 'طلب تسجيل'
    CONTACT = 'contact', 'استفسار'


class LeadStatus(models.TextChoices):
    """Lead pipeline status choices."""
    NEW = 'new', 'جديد'
    CONTACTED = 'contacted', 'تم التواصل'
    IN_PROGRESS = 'in_progress', 'قيد المتابعة'
    REGISTERED = 'registered', 'تم التسجيل'
    CANCELLED = 'cancelled', 'ملغي / غير مهتم'



class Lead(TimestampedModel):
    """Lead model for storing form submissions."""
    lead_type = models.CharField(
        max_length=20,
        choices=LeadType.choices,
        verbose_name='نوع الرسالة',
        db_index=True
    )
    name = models.CharField(
        max_length=200,
        verbose_name='الاسم'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='البريد الإلكتروني'
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='رقم الهاتف'
    )
    message = models.TextField(
        blank=True,
        verbose_name='الرسالة'
    )
    
    # Legal & Governance Audit Trail Fields
    privacy_consent = models.BooleanField(
        default=False,
        verbose_name='موافقة سياسة الخصوصية'
    )
    privacy_consent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الموافقة على الخصوصية'
    )
    privacy_policy_version = models.CharField(
        max_length=20,
        blank=True,
        default='1.0',
        verbose_name='إصدار سياسة الخصوصية'
    )
    
    # Additional lead details fields
    nationality = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='الجنسية'
    )
    institution_name = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name='اسم المؤسسة (الجامعة/المعهد)'
    )
    residence_country = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='دولة الإقامة'
    )
    study_level = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='المرحلة الدراسية'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='عنوان الإقامة'
    )

    
    # Tracking fields
    source_page = models.URLField(
        blank=True,
        verbose_name='صفحة المصدر',
        help_text='الصفحة التي تم إرسال النموذج منها'
    )
    referrer = models.URLField(
        blank=True,
        verbose_name='المرجع',
        help_text='رابط المرجع (HTTP Referrer)'
    )

    # Status fields
    status = models.CharField(
        max_length=30,
        choices=LeadStatus.choices,
        default=LeadStatus.NEW,
        verbose_name='حالة المتابعة',
        db_index=True
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='تم قراءتها',
        db_index=True
    )
    is_archived = models.BooleanField(
        default=False,
        verbose_name='مؤرشفة',
        db_index=True
    )
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات'
    )
    
    class Meta:
        verbose_name = 'رسالة'
        verbose_name_plural = 'الرسائل'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['lead_type']),
            models.Index(fields=['is_read']),
            models.Index(fields=['is_archived']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['lead_type', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
            models.Index(fields=['is_archived', 'lead_type', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.name} - {self.get_lead_type_display()}'
    
    def mark_as_read(self):
        """Mark lead as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])

    def archive(self):
        """Archive the lead."""
        self.is_archived = True
        self.save(update_fields=['is_archived'])

    def unarchive(self):
        """Unarchive the lead."""
        self.is_archived = False
        self.save(update_fields=['is_archived'])

    @property
    def source_page_name(self):
        """Extract a readable page name from source_page URL."""
        if not self.source_page:
            return ""
        try:
            decoded_url = unquote(self.source_page)
            parsed = urlparse(decoded_url)
            path = parsed.path.strip('/')
            if not path:
                return "الصفحة الرئيسية"
            
            parts = path.split('/')
            last_part = parts[-1]
            page_name = last_part.replace('-', ' ').replace('_', ' ')
            
            # Map categories to readable names
            if len(parts) > 1:
                category = parts[0]
                if category == 'universities':
                    return f"جامعة: {page_name}"
                elif category == 'institutes':
                    return f"معهد: {page_name}"
                elif category == 'courses':
                    return f"تخصص: {page_name}"
            
            return page_name
        except Exception:
            return self.source_page

    @property
    def referrer_name(self):
        """Extract a readable website name from referrer URL."""
        if not self.referrer:
            return "رابط مباشر"
        try:
            parsed = urlparse(self.referrer)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Treat internal domains as "Direct Link" (رابط مباشر)
            if not domain or domain == 'sciencesgates.com' or domain == 'localhost' or domain == '127.0.0.1':
                return "رابط مباشر"
                
            common_sources = {
                'google.com': 'بحث جوجل (Google)',
                'facebook.com': 'فيسبوك (Facebook)',
                'instagram.com': 'إنستغرام (Instagram)',
                'linkedin.com': 'لينكد إن (LinkedIn)',
                'twitter.com': 'تويتر (Twitter/X)',
                't.co': 'تويتر (Twitter/X)',
                'youtube.com': 'يوتيوب (YouTube)',
            }
            for key, val in common_sources.items():
                if key in domain:
                    return val
            return domain
        except Exception:
            return "رابط مباشر"
