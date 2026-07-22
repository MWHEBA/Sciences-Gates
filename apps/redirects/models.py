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

    @staticmethod
    def normalize_path(url):
        import urllib.parse
        url = (url or '').strip()
        if not url:
            return "/"
            
        if url.startswith(('http://', 'https://')):
            parsed = urllib.parse.urlparse(url)
            url = parsed.path
            if parsed.query:
                url += '?' + parsed.query
        elif '/' in url and not url.startswith('/'):
            parts = url.split('/', 1)
            if '.' in parts[0]:
                url = '/' + parts[1]
                
        if not url.startswith('/'):
            url = '/' + url
            
        return url

    def save(self, *args, **kwargs):
        # We check update_fields to avoid infinite loop when incrementing hit count
        update_fields = kwargs.get('update_fields', None)
        if not update_fields or 'old_url' in update_fields:
            self.old_url = self.normalize_path(self.old_url)
        if not update_fields or 'new_url' in update_fields:
            if not self.new_url.startswith(('http://', 'https://')):
                self.new_url = self.normalize_path(self.new_url)
        super().save(*args, **kwargs)

    @property
    def old_url_decoded(self):
        import urllib.parse
        return urllib.parse.unquote(self.old_url)

    @property
    def new_url_decoded(self):
        import urllib.parse
        if self.new_url.startswith(('http://', 'https://')):
            return self.new_url
        return urllib.parse.unquote(self.new_url)

    @property
    def is_active_label(self):
        return "نشط" if self.is_active else "غير نشط"

    def __str__(self):
        return f'{self.old_url_decoded} → {self.new_url_decoded}'

    def increment_hit_count(self):
        """Increment the hit count for this redirect."""
        self.hit_count += 1
        self.save(update_fields=['hit_count'])
