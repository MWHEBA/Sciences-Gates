"""
Institute content models.
"""
from django.db import models
from django.urls import reverse
from apps.core.models import TimestampedModel, PublishableModel, SEOMixin


class Institute(TimestampedModel, PublishableModel, SEOMixin):
    """Institute content model."""
    INSTITUTE_TYPE_CHOICES = [
        ('language', 'معهد لغة'),
        ('academic', 'معهد أكاديمي'),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name='اسم المعهد',
        db_index=True
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='الرابط',
        help_text='رابط الصفحة (يدعم الأحرف العربية)',
        allow_unicode=True
    )
    institute_type = models.CharField(
        max_length=20,
        choices=INSTITUTE_TYPE_CHOICES,
        default='academic',
        verbose_name='نوع المعهد',
        help_text='تصنيف المعهد (لغة أو أكاديمي)',
        db_index=True
    )
    main_image = models.ImageField(
        upload_to='institutes/images/',
        verbose_name='الصورة الرئيسية'
    )
    main_image_alt = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='النص البديل للصورة الرئيسية',
        help_text='النص البديل للصورة الرئيسية للمعهد (SEO)'
    )
    description = models.TextField(
        verbose_name='الوصف',
        help_text='وصف شامل عن المعهد'
    )
    registration_requirements = models.TextField(
        verbose_name='شروط التسجيل',
        help_text='شروط التسجيل في المعهد'
    )
    registration_section = models.TextField(
        blank=True,
        verbose_name='قسم التسجيل',
        help_text='معلومات عملية التسجيل والخطوات'
    )

    # Relationships
    related_articles = models.ManyToManyField(
        'articles.Article',
        blank=True,
        related_name='institutes',
        verbose_name='المقالات المرتبطة'
    )

    class Meta:
        verbose_name = 'معهد'
        verbose_name_plural = 'المعاهد'
        ordering = ['name']
        indexes = [
            models.Index(fields=['publish_status']),
            models.Index(fields=['name']),
            models.Index(fields=['publish_status', 'name']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return the absolute URL for this institute."""
        return reverse('institutes:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Store old slug for redirect creation if slug changes."""
        if self.pk:
            old_instance = Institute.objects.get(pk=self.pk)
            if old_instance.slug != self.slug and old_instance.is_published:
                self._old_slug = old_instance.slug
        super().save(*args, **kwargs)


class Course(models.Model):
    """Course within an institute."""
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name='المعهد'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='اسم الدورة'
    )
    duration = models.CharField(
        max_length=100,
        verbose_name='مدة الدورة',
        help_text='مثال: 6 أشهر'
    )
    fees = models.CharField(
        max_length=100,
        verbose_name='الرسوم',
        help_text='مثال: 5,000 رنجت ماليزي'
    )
    description = models.TextField(
        verbose_name='الوصف',
        help_text='وصف الدورة'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات',
        help_text='ملاحظات إضافية عن الدورة'
    )

    class Meta:
        verbose_name = 'دورة'
        verbose_name_plural = 'الدورات'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} - {self.institute.name}'
