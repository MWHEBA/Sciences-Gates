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
