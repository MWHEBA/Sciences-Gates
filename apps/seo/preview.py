from django.db.models import Q


def apply_preview_filter(request, queryset):
    """Allow unpublished preview only for SuperAdmin in Phase 1."""
    is_preview = str(request.GET.get("preview", "")).strip() in {"1", "true", "True"}
    user = getattr(request, "user", None)
    is_superadmin = bool(
        user
        and user.is_authenticated
        and hasattr(user, "profile")
        and user.profile.is_super_admin
    )

    if is_preview and is_superadmin:
        return queryset.filter(Q(publish_status="published") | Q(publish_status="unpublished"))
    return queryset.filter(publish_status="published")
