"""
Major/Specialization content models.
"""
from django.db import models
from django.urls import reverse
from apps.core.models import TimestampedModel, PublishableModel, SEOMixin


class Major(TimestampedModel, PublishableModel, SEOMixin):
    """Major/Specialization content model."""
    MAJOR_CATEGORY_CHOICES = [
        ('medical', 'التخصصات الطبية'),
        ('engineering', 'التخصصات الهندسية'),
        ('cs', 'الحاسوب والتكنولوجيا'),
        ('business', 'إدارة الأعمال'),
        ('science', 'العلوم'),
        ('other', 'تخصصات أخرى'),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name='اسم التخصص',
        db_index=True
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='الرابط',
        help_text='رابط الصفحة (يدعم الأحرف العربية)',
        allow_unicode=True
    )
    major_category = models.CharField(
        max_length=20,
        choices=MAJOR_CATEGORY_CHOICES,
        default='other',
        verbose_name='تصنيف التخصص',
        help_text='تصنيف التخصص حسب المجال',
        db_index=True
    )
    main_image = models.ImageField(
        upload_to='majors/images/',
        verbose_name='الصورة الرئيسية'
    )
    main_image_alt = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='النص البديل للصورة الرئيسية',
        help_text='النص البديل للصورة الرئيسية للتخصص (SEO)'
    )
    description = models.TextField(
        verbose_name='الوصف',
        help_text='وصف شامل عن التخصص'
    )
    study_duration = models.CharField(
        max_length=100,
        verbose_name='مدة الدراسة (عام)',
        help_text='مثال: 4 سنوات (سيتم استبدالها بالحقول المفصلة أدناه)'
    )
    
    # Detailed study duration by degree
    bachelor_duration = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='مدة البكالوريوس',
        help_text='مثال: 4 سنوات'
    )
    master_duration = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='مدة الماجستير',
        help_text='مثال: سنتان'
    )
    phd_duration = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='مدة الدكتوراه',
        help_text='مثال: 3-4 سنوات'
    )

    # Quick Information Fields
    tuition_fees = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='الرسوم الدراسية',
        help_text='مثال: 15,000 - 25,000 رنجت سنوياً'
    )
    study_language = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='لغة الدراسة',
        help_text='مثال: الإنجليزية'
    )
    practical_training = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='التدريب العملي',
        help_text='مثال: متاح في السنة الأخيرة'
    )
    career_opportunities = models.TextField(
        blank=True,
        verbose_name='فرص العمل',
        help_text='فرص العمل المتاحة بعد التخرج'
    )

    # Content Sections
    why_study_section = models.TextField(
        blank=True,
        verbose_name='لماذا تدرس هذا التخصص',
        help_text='أسباب دراسة هذا التخصص'
    )
    how_to_apply_section = models.TextField(
        blank=True,
        verbose_name='كيفية التقديم',
        help_text='خطوات التقديم للتخصص'
    )

    # Relationships
    best_universities = models.ManyToManyField(
        'universities.University',
        blank=True,
        related_name='best_majors',
        verbose_name='أفضل الجامعات'
    )
    cheap_universities = models.ManyToManyField(
        'universities.University',
        blank=True,
        related_name='cheap_majors',
        verbose_name='الجامعات الاقتصادية'
    )
    related_articles = models.ManyToManyField(
        'articles.Article',
        blank=True,
        related_name='majors',
        verbose_name='المقالات المرتبطة'
    )

    class Meta:
        verbose_name = 'تخصص'
        verbose_name_plural = 'التخصصات'
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
        """Return the absolute URL for this major."""
        return reverse('majors:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Store old slug for redirect creation if slug changes."""
        if self.pk:
            old_instance = Major.objects.get(pk=self.pk)
            if old_instance.slug != self.slug and old_instance.is_published:
                self._old_slug = old_instance.slug
        super().save(*args, **kwargs)


class SubjectsTable(models.Model):
    """Subjects table for a major."""
    major = models.ForeignKey(
        Major,
        on_delete=models.CASCADE,
        related_name='subjects_tables',
        verbose_name='التخصص'
    )
    academic_year = models.CharField(
        max_length=100,
        verbose_name='السنة الدراسية',
        help_text='مثال: السنة الأولى'
    )
    subjects = models.TextField(
        verbose_name='المواد',
        help_text='المواد الدراسية (يمكن فصلها بفواصل)'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور الصف (الأصغر أولاً)'
    )

    class Meta:
        verbose_name = 'جدول المواد'
        verbose_name_plural = 'جداول المواد'
        ordering = ['sort_order', 'academic_year']

    def __str__(self):
        return f'{self.academic_year} - {self.major.name}'


class SalaryTable(models.Model):
    """Salary table for a major."""
    major = models.ForeignKey(
        Major,
        on_delete=models.CASCADE,
        related_name='salary_tables',
        verbose_name='التخصص'
    )
    job_title = models.CharField(
        max_length=200,
        verbose_name='المسمى الوظيفي',
        help_text='مثال: مهندس برمجيات'
    )
    average_monthly_salary = models.CharField(
        max_length=100,
        verbose_name='متوسط الراتب الشهري',
        help_text='مثال: 5,000 - 8,000 رنجت ماليزي'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور الصف (الأصغر أولاً)'
    )

    class Meta:
        verbose_name = 'جدول الرواتب'
        verbose_name_plural = 'جداول الرواتب'
        ordering = ['sort_order', 'job_title']

    def __str__(self):
        return f'{self.job_title} - {self.major.name}'


class CountriesTable(models.Model):
    """Countries table for a major."""
    major = models.ForeignKey(
        Major,
        on_delete=models.CASCADE,
        related_name='countries_tables',
        verbose_name='التخصص'
    )
    destination = models.CharField(
        max_length=200,
        verbose_name='الوجهة',
        help_text='مثال: ماليزيا'
    )
    study_duration = models.CharField(
        max_length=100,
        verbose_name='مدة الدراسة',
        help_text='مثال: 4 سنوات'
    )
    annual_fees = models.CharField(
        max_length=100,
        verbose_name='الرسوم السنوية',
        help_text='مثال: 20,000 - 30,000 رنجت ماليزي'
    )
    living_cost = models.CharField(
        max_length=100,
        verbose_name='تكلفة المعيشة',
        help_text='مثال: 1,500 - 2,500 رنجت ماليزي شهرياً'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور الصف (الأصغر أولاً)'
    )

    class Meta:
        verbose_name = 'جدول الدول'
        verbose_name_plural = 'جداول الدول'
        ordering = ['sort_order', 'destination']

    def __str__(self):
        return f'{self.destination} - {self.major.name}'
