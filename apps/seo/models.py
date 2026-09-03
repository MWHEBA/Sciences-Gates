"""
SEO app models.
"""
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class SEOAnalysisDetail(models.Model):
    """Stores heavy SEO analysis JSON separate from core content tables."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    analysis_report_json = models.JSONField(default=dict, verbose_name="تقرير التحليل التفصيلي")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                name="unique_seo_analysis_detail_per_object",
            )
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
        verbose_name = "تفاصيل تحليل SEO"
        verbose_name_plural = "تفاصيل تحليلات SEO"


class Page404Log(models.Model):
    """Logs 404 page requests for content optimization."""
    path = models.CharField(max_length=1024, unique=True, verbose_name="المسار المطلوب")
    hits = models.PositiveIntegerField(default=0, verbose_name="عدد المحاولات")
    last_hit = models.DateTimeField(auto_now=True, verbose_name="تاريخ آخر محاولة")
    referrers = models.JSONField(default=dict, blank=True, verbose_name="مصادر الزيارة (Referrers)")
    user_agents = models.JSONField(default=dict, blank=True, verbose_name="المتصفحات / الأجهزة")
    daily_hits = models.JSONField(default=dict, blank=True, verbose_name="الزيارات اليومية")
    is_ignored = models.BooleanField(default=False, verbose_name="متجاهل")

    class Meta:
        verbose_name = "سجل صفحة 404"
        verbose_name_plural = "سجلات صفحات 404"
        ordering = ["-hits", "-last_hit"]

    def __str__(self):
        return f"{self.path} ({self.hits} hits)"
