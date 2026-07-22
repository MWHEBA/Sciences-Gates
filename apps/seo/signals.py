import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article
from apps.seo.sitemaps import clear_sitemap_cache

logger = logging.getLogger(__name__)


@receiver(post_save, sender=University)
@receiver(post_delete, sender=University)
def university_sitemap_handler(sender, instance, **kwargs):
    if kwargs.get('raw'):
        return
    try:
        clear_sitemap_cache(sitemap_type='universities')
    except Exception as exc:
        logger.error("SEO Invalidation: Failed to clear university sitemap cache: %s", exc)


@receiver(post_save, sender=Institute)
@receiver(post_delete, sender=Institute)
def institute_sitemap_handler(sender, instance, **kwargs):
    if kwargs.get('raw'):
        return
    try:
        clear_sitemap_cache(sitemap_type='institutes')
    except Exception as exc:
        logger.error("SEO Invalidation: Failed to clear institute sitemap cache: %s", exc)


@receiver(post_save, sender=Major)
@receiver(post_delete, sender=Major)
def major_sitemap_handler(sender, instance, **kwargs):
    if kwargs.get('raw'):
        return
    try:
        clear_sitemap_cache(sitemap_type='majors')
    except Exception as exc:
        logger.error("SEO Invalidation: Failed to clear major sitemap cache: %s", exc)


@receiver(post_save, sender=Article)
@receiver(post_delete, sender=Article)
def article_sitemap_handler(sender, instance, **kwargs):
    if kwargs.get('raw'):
        return
    try:
        clear_sitemap_cache(sitemap_type='articles')
    except Exception as exc:
        logger.error("SEO Invalidation: Failed to clear article sitemap cache: %s", exc)
