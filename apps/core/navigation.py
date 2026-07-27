"""
Core navigation helpers and fallback engine.
مساعدات تنقل النظام ومحرك الاستكمال التلقائي ومنع التكرار
"""
from django.db import transaction, models
from apps.core.models import SiteNavigation


def get_next_order(model_class, filter_kwargs=None):
    """Returns max(order) + 1 for new items."""
    qs = model_class.objects.all()
    if filter_kwargs:
        qs = qs.filter(**filter_kwargs)
    max_order = qs.aggregate(models.Max('order'))['order__max']
    return (max_order or 0) + 1


@transaction.atomic
def auto_shift_order_if_changed(form, model_class, instance, filter_kwargs=None):
    """
    Triggers order auto-shift (+1) only if the 'order' field has actually changed or if creating a new instance.
    """
    if not instance.pk or 'order' in form.changed_data:
        target_order = form.cleaned_data.get('order')
        if target_order is None:
            return
        qs = model_class.objects.all()
        if filter_kwargs:
            qs = qs.filter(**filter_kwargs)
        if instance.pk:
            qs = qs.exclude(pk=instance.pk)
        if qs.filter(order=target_order).exists():
            qs.filter(order__gte=target_order).update(order=models.F('order') + 1)


def build_curated_list_with_dedup_fallback(assigned_items_dict, pool_queryset, total_needed):
    """
    Builds a curated list of entities (Universities, Institutes, Majors):
    1. Collects all valid published assigned items.
    2. Collects all assigned entity IDs to exclude them from the fallback pool.
    3. For any slot without a valid assigned item, fills it with the first available item 
       from pool_queryset (filtered by publish_status='published') that is NOT in assigned_ids,
       ordered by ('order', 'name').
    4. Returns a list of exactly `total_needed` items (or as many as available).
    """
    assigned_ids = set()
    for slot_num, item in assigned_items_dict.items():
        if item and getattr(item, 'publish_status', None) == 'published':
            assigned_ids.add(item.pk)

    final_list = []
    try:
        qs = pool_queryset.filter(publish_status='published')
        if assigned_ids:
            qs = qs.exclude(pk__in=assigned_ids)
        available_fallbacks = list(qs.order_by('order', 'name')[:total_needed])
    except Exception:
        qs = pool_queryset.filter(publish_status='published')
        if assigned_ids:
            qs = qs.exclude(pk__in=assigned_ids)
        available_fallbacks = list(qs.order_by('name')[:total_needed])
    fallback_idx = 0

    for slot_num in range(1, total_needed + 1):
        item = assigned_items_dict.get(slot_num)
        if item and getattr(item, 'publish_status', None) == 'published':
            final_list.append(item)
        else:
            # Pick next available fallback item
            if fallback_idx < len(available_fallbacks):
                fallback = available_fallbacks[fallback_idx]
                final_list.append(fallback)
                assigned_ids.add(fallback.pk)
                fallback_idx += 1

    return final_list


def get_all_navigation_slots_dict():
    """
    Returns a dictionary of section_name -> {slot_number -> entity_instance}.
    Executed in 1 single database query.
    """
    try:
        slots = (
            SiteNavigation.objects.all()
            .select_related('university', 'institute', 'major')
            .order_by('slot_number')
        )
        res = {}
        for slot in slots:
            if slot.section not in res:
                res[slot.section] = {}
            if slot.university:
                res[slot.section][slot.slot_number] = slot.university
            elif slot.institute:
                res[slot.section][slot.slot_number] = slot.institute
            elif slot.major:
                res[slot.section][slot.slot_number] = slot.major
        return res
    except Exception:
        return {}


def get_navigation_slots_dict(section_name):
    """
    Returns a dictionary of slot_number -> entity instance for a given section.
    Handles missing table/columns gracefully.
    """
    try:
        slots = (
            SiteNavigation.objects.filter(section=section_name)
            .select_related('university', 'institute', 'major')
            .order_by('slot_number')
        )
        res = {}
        for slot in slots:
            if slot.university:
                res[slot.slot_number] = slot.university
            elif slot.institute:
                res[slot.slot_number] = slot.institute
            elif slot.major:
                res[slot.slot_number] = slot.major
        return res
    except Exception:
        return {}

