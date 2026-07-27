"""
Institute content models.
"""
from django.db import models
from django.urls import reverse
from apps.core.models import TimestampedModel, PublishableModel, SEOMixin
from apps.universities.models import University
from apps.core.utils import (
    validate_attachment_file,
    cleanup_attachment_file_on_save,
    cleanup_attachment_file_on_delete
)


class Institute(TimestampedModel, PublishableModel, SEOMixin):
    """Institute content model."""
    
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
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور المعهد في صفحات القوائم (الأصغر أولاً)',
        db_index=True
    )
    is_legacy = models.BooleanField(
        default=False,
        verbose_name='رابط قديم',
        help_text='تفعيل هذا الخيار سيجعل الرابط مباشراً بدون بادئة الفئة (مثال: /slug/ بدلاً من /institutes/slug/)'
    )
    state = models.CharField(
        max_length=20,
        choices=University.STATE_CHOICES,
        default='kl',
        verbose_name='الولاية',
        help_text='الولاية التي يقع بها المعهد لتسهيل التصفية والبحث',
        db_index=True
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='المدينة',
        help_text='المدينة التي يقع بها المعهد لتسهيل التصفية والبحث',
        db_index=True
    )
    website = models.URLField(
        blank=True,
        verbose_name='الموقع الرسمي للمعهد',
        help_text='رابط الموقع الإلكتروني الرسمي للمعهد (sameAs)'
    )
    telephone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='رقم الهاتف',
        help_text='رقم هاتف التواصل للمعهد لتسهيل التواصل والبحث المحلي'
    )
    location = models.TextField(
        blank=True,
        verbose_name='الموقع',
        help_text='موقع المعهد (المدينة، الولاية)'
    )
    why_choose_us = models.TextField(
        blank=True,
        verbose_name='لماذا يختار الطلاب العرب هذا المعهد',
        help_text='أسباب اختيار الطلاب العرب للدراسة في هذا المعهد'
    )
    english_study = models.TextField(
        blank=True,
        verbose_name='دراسة اللغة الإنجليزية',
        help_text='معلومات وتفاصيل عن دراسة اللغة الإنجليزية في المعهد'
    )
    logo = models.ImageField(
        upload_to='institutes/logos/',
        null=True,
        blank=True,
        verbose_name='شعار المعهد',
        help_text='شعار المعهد (PNG مع خلفية شفافة مفضل)'
    )
    logo_alt = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='النص البديل للشعار',
        help_text='النص البديل لشعار المعهد (SEO)'
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
    introduction = models.TextField(
        blank=True,
        verbose_name='المقدمة',
        help_text='مقدمة اختيارية تظهر في بداية صفحة المعهد'
    )
    description = models.TextField(
        verbose_name='الوصف',
        help_text='وصف شامل عن المعهد'
    )
    fees_includes = models.TextField(
        blank=True,
        default='',
        verbose_name='الرسوم تشمل',
        help_text='ما تشمله الرسوم الموضحة (مثال: تكاليف الدراسة، ورسوم تأشيرة الطالب...)'
    )
    fees_excludes = models.TextField(
        blank=True,
        default='',
        verbose_name='الرسوم لا تشمل',
        help_text='ما لا تشمله الرسوم الموضحة (مثال: المصروف الشخصي، السكن...)'
    )


    # Relationships
    related_articles = models.ManyToManyField(
        'articles.Article',
        blank=True,
        related_name='institutes',
        verbose_name='المقالات المرتبطة'
    )
    tags = models.ManyToManyField(
        'articles.Tag',
        blank=True,
        related_name='institutes',
        verbose_name='الوسوم'
    )

    class Meta:
        verbose_name = 'معهد'
        verbose_name_plural = 'المعاهد'
        ordering = ['order', 'name']
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

    def get_location_display(self):
        """Returns the formatted location display (e.g. 'Subang Jaya, Selangor' in Arabic)."""
        state_display = self.get_state_display()
        city_name = ""
        if self.state in University.STATE_CITIES:
            for c_slug, c_name in University.STATE_CITIES[self.state]:
                if c_slug == self.city:
                    city_name = c_name
                    break
        
        if city_name and city_name != state_display and "عام" not in city_name:
            return f"{city_name}، {state_display}"
        return state_display


class InstituteFAQ(models.Model):
    """FAQ entry for an institute."""
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name='المعهد'
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


class Course(models.Model):
    """Course within an institute (Fee row)."""
    COURSE_TYPE_CHOICES = [
        ('regular', '4 ساعات'),
        ('intensive', '5 ساعات'),
        ('super_intensive', '6 ساعات'),
        ('undefined', 'بدون ساعات'),
    ]

    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name='المعهد'
    )
    course_type = models.CharField(
        max_length=50,
        choices=COURSE_TYPE_CHOICES,
        default='undefined',
        verbose_name='نوع الكورس'
    )
    duration = models.CharField(
        max_length=100,
        verbose_name='مدة الكورس',
        help_text='مثال: شهر، شهرين، 3 أشهر'
    )
    fees_myr = models.CharField(
        max_length=100,
        verbose_name='التكلفة بالرنجت MYR',
        help_text='مثال: 3,400 MYR'
    )
    fees_usd = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='التكلفة بالدولار USD',
        help_text='مثال: 857 USD'
    )
    fees_sar = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='التكلفة بالريال SAR',
        help_text='مثال: 3,216 SAR'
    )
    visa_duration = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='مدة تأشيرة الطالب',
        help_text='مثال: بدون تأشيرة، 6 أشهر، سنة'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='الترتيب',
        help_text='ترتيب عرض الصف (الأصغر أولاً)'
    )

    class Meta:
        verbose_name = 'رسوم الكورس'
        verbose_name_plural = 'جدول الرسوم'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.duration} - {self.institute.name}'


class InstituteAttachment(TimestampedModel):
    """File attachment for an institute."""
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='المعهد'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان الملف'
    )
    file = models.FileField(
        upload_to='institutes/attachments/',
        validators=[validate_attachment_file],
        verbose_name='الملف'
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name='حجم الملف (بايت)'
    )

    class Meta:
        verbose_name = 'ملف المعهد'
        verbose_name_plural = 'ملفات المعهد'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.institute.name}'

    def save(self, *args, **kwargs):
        cleanup_attachment_file_on_save(self)
        if self.file:
            try:
                self.file_size = self.file.size
            except (FileNotFoundError, OSError, ValueError):
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        cleanup_attachment_file_on_delete(self)
        super().delete(*args, **kwargs)

