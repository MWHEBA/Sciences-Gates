"""
University content models including University, Faculty, Program, and FAQ.
"""
from django.db import models
from django.urls import reverse
from apps.core.models import TimestampedModel, PublishableModel, SEOMixin


class University(TimestampedModel, PublishableModel, SEOMixin):
    """University content model."""
    UNIVERSITY_TYPE_CHOICES = [
        ('public', 'جامعة حكومية'),
        ('private', 'جامعة خاصة'),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name='اسم الجامعة',
        db_index=True
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='الرابط',
        help_text='رابط الصفحة (يدعم الأحرف العربية)',
        allow_unicode=True
    )
    university_type = models.CharField(
        max_length=20,
        choices=UNIVERSITY_TYPE_CHOICES,
        default='private',
        verbose_name='نوع الجامعة',
        help_text='تصنيف الجامعة (حكومية أو خاصة)',
        db_index=True
    )
    logo = models.ImageField(
        upload_to='universities/logos/',
        verbose_name='شعار الجامعة',
        help_text='شعار الجامعة (PNG مع خلفية شفافة مفضل)'
    )
    main_image = models.ImageField(
        upload_to='universities/images/',
        verbose_name='الصورة الرئيسية',
        help_text='صورة رئيسية للجامعة'
    )
    description = models.TextField(
        verbose_name='الوصف',
        help_text='وصف شامل عن الجامعة'
    )
    location = models.CharField(
        max_length=200,
        verbose_name='الموقع',
        help_text='موقع الجامعة (المدينة، الولاية)'
    )
    video_url = models.URLField(
        blank=True,
        verbose_name='رابط الفيديو',
        help_text='رابط فيديو YouTube أو Vimeo'
    )
    admission_requirements = models.TextField(
        verbose_name='شروط القبول',
        help_text='شروط القبول في الجامعة'
    )
    registration_section = models.TextField(
        blank=True,
        verbose_name='قسم التسجيل',
        help_text='معلومات عملية التسجيل والخطوات'
    )

    # Relationships
    related_majors = models.ManyToManyField(
        'majors.Major',
        blank=True,
        related_name='universities',
        verbose_name='التخصصات المرتبطة'
    )
    related_articles = models.ManyToManyField(
        'articles.Article',
        blank=True,
        related_name='universities',
        verbose_name='المقالات المرتبطة'
    )

    class Meta:
        verbose_name = 'جامعة'
        verbose_name_plural = 'الجامعات'
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
        """Return the absolute URL for this university."""
        return reverse('universities:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Store old slug for redirect creation if slug changes."""
        if self.pk:
            old_instance = University.objects.get(pk=self.pk)
            if old_instance.slug != self.slug and old_instance.is_published:
                # Signal to create redirect (handled in dashboard)
                self._old_slug = old_instance.slug
        super().save(*args, **kwargs)


class Faculty(models.Model):
    """Faculty within a university."""
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='faculties',
        verbose_name='الجامعة'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='اسم الكلية'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور الكلية (الأصغر أولاً)'
    )

    class Meta:
        verbose_name = 'كلية'
        verbose_name_plural = 'الكليات'
        ordering = ['sort_order', 'name']
        unique_together = ['university', 'name']

    def __str__(self):
        return f'{self.name} - {self.university.name}'


class Program(models.Model):
    """Program within a faculty."""
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='programs',
        verbose_name='الكلية'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='اسم البرنامج'
    )
    duration = models.CharField(
        max_length=100,
        verbose_name='مدة الدراسة',
        help_text='مثال: 4 سنوات'
    )
    tuition_fees = models.CharField(
        max_length=100,
        verbose_name='الرسوم الدراسية',
        help_text='مثال: 20,000 رنجت ماليزي سنوياً'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور البرنامج (الأصغر أولاً)'
    )

    class Meta:
        verbose_name = 'برنامج'
        verbose_name_plural = 'البرامج'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f'{self.name} - {self.faculty.name}'


class UniversityFAQ(models.Model):
    """FAQ entry for a university."""
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name='الجامعة'
    )
    question = models.CharField(
        max_length=300,
        verbose_name='السؤال'
    )
    answer = models.TextField(
        verbose_name='الإجابة'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور السؤال (الأصغر أولاً)'
    )

    class Meta:
        verbose_name = 'سؤال شائع'
        verbose_name_plural = 'الأسئلة الشائعة'
        ordering = ['sort_order']

    def __str__(self):
        return self.question
