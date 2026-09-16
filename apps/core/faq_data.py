"""
Unified Dynamic FAQ Data Provider for Sciences Gates Platform.
Provides categorized, verified, and E-E-A-T compliant frequently asked questions
dynamically queried from the GeneralFAQ database model with smart in-memory caching.
"""
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

CATEGORY_ICONS = {
    'admissions': 'academic-cap',
    'visa': 'identification',
    'costs': 'currency-dollar',
    'english': 'translate',
    'recognition': 'badge-check',
    'services': 'sparkles',
}


def get_all_faqs():
    """
    Return all published FAQ items dynamically from GeneralFAQ model
    with smart in-memory caching (24h TTL, invalidated on DB change).
    """
    cached = cache.get('global_faqs_published_all')
    if cached is not None:
        return cached

    from apps.core.models import GeneralFAQ
    try:
        db_faqs = list(GeneralFAQ.objects.filter(is_published=True).order_by('order', 'created_at'))
        cat_name_map = dict(GeneralFAQ.CATEGORY_CHOICES)
        result = []
        for item in db_faqs:
            result.append({
                'id': item.id,
                'slug': item.slug,
                'category': item.category,
                'category_name': cat_name_map.get(item.category, item.category),
                'question': item.question,
                'answer': item.answer,
                'featured': item.is_featured,
            })
        cache.set('global_faqs_published_all', result, 86400)
        return result
    except Exception as e:
        logger.error(f"Error fetching GeneralFAQs from database: {e}")
        return []


def get_faq_categories():
    """
    Return all FAQ categories dynamically from GeneralFAQ.CATEGORY_CHOICES
    with live question count per category.
    """
    from apps.core.models import GeneralFAQ
    all_faqs = get_all_faqs()
    counts = {}
    for faq in all_faqs:
        cat = faq['category']
        counts[cat] = counts.get(cat, 0) + 1

    categories = []
    for cat_id, cat_name in GeneralFAQ.CATEGORY_CHOICES:
        categories.append({
            'id': cat_id,
            'key': cat_id,
            'name': cat_name,
            'icon': CATEGORY_ICONS.get(cat_id, 'sparkles'),
            'count': counts.get(cat_id, 0),
        })
    return categories


def get_featured_faqs(limit=5):
    """
    Return featured FAQs for homepage and quick widgets with smart in-memory caching.
    """
    cached = cache.get('global_faqs_home_featured')
    if cached is not None:
        return cached[:limit]

    all_faqs = get_all_faqs()
    featured = [faq for faq in all_faqs if faq.get('featured')]
    if len(featured) < limit:
        non_featured = [faq for faq in all_faqs if not faq.get('featured')]
        featured.extend(non_featured[:limit - len(featured)])

    result = featured[:limit]
    cache.set('global_faqs_home_featured', result, 86400)
    return result
