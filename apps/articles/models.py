"""
Article and News content models.
"""
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import pre_save
from django.dispatch import receiver
from apps.core.models import TimestampedModel, PublishableModel, SEOMixin
from apps.html_editor.sanitizer import sanitize_article_html


class Category(TimestampedModel):
    """Article category model."""
    name = models.CharField(
        max_length=200,
        verbose_name='اسم الفئة',
        db_index=True
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='الرابط',
        help_text='رابط الفئة (يدعم الأحرف العربية)',
        allow_unicode=True
    )
    description = models.TextField(
        blank=True,
        verbose_name='الوصف',
        help_text='وصف الفئة'
    )

    class Meta:
        verbose_name = 'فئة'
        verbose_name_plural = 'الفئات'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return the absolute URL for this category."""
        return reverse('articles:category', kwargs={'slug': self.slug})


class Tag(models.Model):
    """Article tag model."""
    name = models.CharField(
        max_length=100,
        verbose_name='اسم الوسم',
        db_index=True
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='الرابط',
        help_text='رابط الوسم (يدعم الأحرف العربية)',
        allow_unicode=True
    )

    class Meta:
        verbose_name = 'وسم'
        verbose_name_plural = 'الوسوم'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return the absolute URL for this tag."""
        return reverse('articles:tag', kwargs={'slug': self.slug})


class Article(TimestampedModel, PublishableModel, SEOMixin):
    """Article/News content model."""
    title = models.CharField(
        max_length=300,
        verbose_name='العنوان',
        db_index=True
    )
    slug = models.SlugField(
        max_length=300,
        unique=True,
        verbose_name='الرابط',
        help_text='رابط المقالة (يدعم الأحرف العربية)',
        allow_unicode=True
    )
    featured_image = models.ImageField(
        upload_to='articles/images/',
        verbose_name='الصورة المميزة',
        help_text='الصورة الرئيسية للمقالة'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='الفئة'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='articles',
        verbose_name='الوسوم'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='الكاتب'
    )
    publish_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ النشر',
        db_index=True
    )
    content = models.TextField(
        verbose_name='المحتوى',
        help_text='محتوى المقالة (HTML محمي)'
    )

    # Relationships
    related_universities = models.ManyToManyField(
        'universities.University',
        blank=True,
        related_name='articles',
        verbose_name='الجامعات المرتبطة'
    )
    related_institutes = models.ManyToManyField(
        'institutes.Institute',
        blank=True,
        related_name='articles',
        verbose_name='المعاهد المرتبطة'
    )
    related_majors = models.ManyToManyField(
        'majors.Major',
        blank=True,
        related_name='articles',
        verbose_name='التخصصات المرتبطة'
    )

    class Meta:
        verbose_name = 'مقالة'
        verbose_name_plural = 'المقالات'
        ordering = ['-publish_date']
        indexes = [
            models.Index(fields=['-publish_date']),
            models.Index(fields=['category', '-publish_date']),
            models.Index(fields=['publish_status']),
            models.Index(fields=['title']),
            models.Index(fields=['publish_status', '-publish_date']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Return the absolute URL for this article."""
        return reverse('articles:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Store old slug for redirect creation if slug changes."""
        if self.pk:
            old_instance = Article.objects.get(pk=self.pk)
            if old_instance.slug != self.slug and old_instance.is_published:
                self._old_slug = old_instance.slug
        super().save(*args, **kwargs)


@receiver(pre_save, sender=Article)
def sanitize_article_content(sender, instance, **kwargs):
    """
    Sanitize article HTML content before saving to prevent XSS attacks.
    
    This signal handler ensures all article content is sanitized using
    the sanitize_article_html function from the html_editor app.
    """
    if instance.content:
        instance.content = sanitize_article_html(instance.content)
