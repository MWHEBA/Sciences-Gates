"""
Django Admin registration for Redirect model (emergency use only).
"""
from django.contrib import admin
from .models import Redirect


@admin.register(Redirect)
class RedirectAdmin(admin.ModelAdmin):
    """Admin interface for Redirect model (emergency use only)."""
    list_display = ('old_url', 'new_url', 'is_active', 'hit_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('old_url', 'new_url')
    readonly_fields = ('hit_count', 'created_at', 'updated_at')
    fieldsets = (
        ('معلومات التوجيه', {
            'fields': ('old_url', 'new_url', 'is_active')
        }),
        ('معلومات إضافية', {
            'fields': ('notes', 'hit_count')
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make created_at and updated_at always read-only."""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.extend(['created_at', 'updated_at'])
        return readonly
