"""
Article and News content models.
"""
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from apps.core.models import TimestampedModel, PublishableModel, SEOMixin
from apps.html_editor.sanitizer import sanitize_article_html
from apps.core.utils import (
    validate_attachment_file,
    cleanup_attachment_file_on_save,
    cleanup_attachment_file_on_delete
)


class Category(TimestampedModel):
    """Article category model."""
    name = models.CharField(
        max_length=200,
        verbose_name='اسم التصنيف',
        db_index=True
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='الرابط',
        help_text='رابط التصنيف (يدعم الأحرف العربية)',
        allow_unicode=True
    )
    description = models.TextField(
        blank=True,
        verbose_name='الوصف',
        help_text='وصف التصنيف'
    )

    class Meta:
        verbose_name = 'تصنيف'
        verbose_name_plural = 'التصنيفات'
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
    is_legacy = models.BooleanField(
        default=False,
        verbose_name='رابط قديم',
        help_text='تفعيل هذا الخيار سيجعل الرابط مباشراً بدون بادئة الفئة (مثال: /slug/ بدلاً من /articles/slug/)'
    )
    featured_image = models.ImageField(
        upload_to='articles/images/',
        verbose_name='الصورة المميزة',
        help_text='الصورة الرئيسية للمقالة'
    )
    featured_image_alt = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='النص البديل للصورة المميزة',
        help_text='النص البديل للصورة المميزة للمقالة (SEO)'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='التصنيف'
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
        default=timezone.now,
        blank=True,
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

    @property
    def author_display_name(self):
        """Return the author's full name, username, or a default fallback."""
        if self.author:
            return self.author.get_full_name() or self.author.username
        return "شركة بوابات العلوم"

    def save(self, *args, **kwargs):
        """Store old slug for redirect creation if slug changes."""
        if not self.publish_date:
            self.publish_date = timezone.now()
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


class ArticleFAQ(models.Model):
    """FAQ entry for an article.
    الأسئلة الشائعة للمقالة
    """
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name='المقالة'
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
        verbose_name = 'سؤال شائع للمقالة'
        verbose_name_plural = 'الأسئلة الشائعة للمقالات'
        ordering = ['sort_order']

    def __str__(self):
        return self.question


@receiver(pre_save, sender=ArticleFAQ)
def sanitize_article_faq_content(sender, instance, **kwargs):
    """Sanitize FAQ answer HTML content before saving."""
    if instance.answer:
        instance.answer = sanitize_article_html(instance.answer)


class IgnoredSimilarity(models.Model):
    """Model to store ignored duplicate/similarity article pairs."""
    article_a = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='ignored_similarities_a')
    article_b = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='ignored_similarities_b')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('article_a', 'article_b')
        verbose_name = 'تشابه متجاهل'
        verbose_name_plural = 'التشابهات المتجاهلة'


class ArticleAttachment(TimestampedModel):
    """File attachment for an article."""
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='المقالة'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان الملف'
    )
    file = models.FileField(
        upload_to='articles/attachments/',
        validators=[validate_attachment_file],
        verbose_name='الملف'
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name='حجم الملف (بايت)'
    )

    class Meta:
        verbose_name = 'ملف المقالة'
        verbose_name_plural = 'ملفات المقالة'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.article.title}'

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

