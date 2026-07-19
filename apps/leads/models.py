from django.db import models
from apps.core.models import TimestampedModel


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
    
    # New fields matching Fluent Forms export
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
    
    # UTM parameters
    utm_source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='UTM Source'
    )
    utm_medium = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='UTM Medium'
    )
    utm_campaign = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='UTM Campaign'
    )
    utm_term = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='UTM Term'
    )
    utm_content = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='UTM Content'
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
            models.Index(fields=['-created_at']),
            models.Index(fields=['lead_type', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.name} - {self.get_lead_type_display()}'
    
    def mark_as_read(self):
        """Mark lead as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])
