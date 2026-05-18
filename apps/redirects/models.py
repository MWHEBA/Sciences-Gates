"""
Redirect models for managing URL redirects.
"""
from django.db import models
from apps.core.models import TimestampedModel


class Redirect(TimestampedModel):
    """Model for managing 301 redirects."""
    old_url = models.CharField(
        max_length=500,
        verbose_name='الرابط القديم',
        help_text='الرابط القديم الذي سيتم إعادة توجيهه',
        db_index=True
    )
    new_url = models.CharField(
        max_length=500,
        verbose_name='الرابط الجديد',
        help_text='الرابط الجديد الذي سيتم التوجيه إليه'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        help_text='تفعيل أو تعطيل هذا التوجيه',
        db_index=True
    )
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات',
        help_text='ملاحظات إضافية عن سبب التوجيه'
    )
    hit_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد الزيارات',
        help_text='عدد المرات التي تم استخدام هذا التوجيه'
    )

    class Meta:
        verbose_name = 'إعادة توجيه'
        verbose_name_plural = 'إعادات التوجيه'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['old_url', 'is_active']),
        ]

    def __str__(self):
        return f'{self.old_url} → {self.new_url}'

    def increment_hit_count(self):
        """Increment the hit count for this redirect."""
        self.hit_count += 1
        self.save(update_fields=['hit_count'])
