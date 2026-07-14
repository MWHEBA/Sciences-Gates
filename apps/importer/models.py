import uuid
from django.db import models

class ImportJob(models.Model):
    """
    Model to track the status and progress of asynchronous background import tasks.
    متابعة حالة وتقدم عمليات الاستيراد في الخلفية.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=500, verbose_name='رابط الاستيراد')
    content_type = models.CharField(max_length=100, verbose_name='نوع المحتوى')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='الحالة')
    progress = models.PositiveIntegerField(default=0, verbose_name='نسبة التقدم')
    status_message = models.CharField(max_length=500, blank=True, verbose_name='رسالة الحالة')
    result_url = models.CharField(max_length=500, blank=True, verbose_name='رابط النتيجة')
    result_data = models.TextField(blank=True, verbose_name='بيانات النتيجة (JSON)')
    error_message = models.TextField(blank=True, verbose_name='رسالة الخطأ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'عملية استيراد'
        verbose_name_plural = 'عمليات الاستيراد'
        ordering = ['-created_at']

    def __str__(self):
        return f"Import {self.content_type} ({self.status}) - {self.url}"
