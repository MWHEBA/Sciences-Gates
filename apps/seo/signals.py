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

    if kwargs.get('created') or not kwargs.get('raw'):
        try:
            if hasattr(instance, 'get_absolute_url'):
                full_url = f"https://sciencesgates.com{instance.get_absolute_url()}"
                schedule_indexnow_ping(full_url)
        except Exception:
            pass


import threading
import urllib.request
import json
from django.db import transaction
from django.conf import settings


def send_indexnow_request(url):
    try:
        key = getattr(settings, 'INDEXNOW_KEY', 'c7a8b9f0e1d2c3b4a5f6e7d8c9b0a1f2')
        host = 'sciencesgates.com'
        payload = json.dumps({
            "host": host,
            "key": key,
            "keyLocation": f"https://{host}/{key}.txt",
            "urlList": [url]
        }).encode('utf-8')
        
        req = urllib.request.Request(
            'https://api.indexnow.org/indexnow',
            data=payload,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            pass
    except Exception as e:
        logger.warning("IndexNow ping failed for %s: %s", url, e, exc_info=True)


def schedule_indexnow_ping(url):
    def dispatch():
        threading.Thread(target=send_indexnow_request, args=[url], daemon=True).start()
    transaction.on_commit(dispatch)

