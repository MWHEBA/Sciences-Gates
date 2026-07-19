from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Admin interface for Lead model (emergency use only)."""
    
    list_display = (
        'name',
        'email',
        'lead_type',
        'is_read',
        'created_at',
    )
    
    search_fields = (
        'name',
        'email',
        'phone',
        'message',
    )
    
    list_filter = (
        'lead_type',
        'is_read',
        'created_at',
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'source_page',
        'referrer',
    )
    
    fieldsets = (
        ('معلومات الرسالة', {
            'fields': (
                'lead_type',
                'name',
                'email',
                'phone',
                'message',
                'is_read',
                'notes',
            )
        }),
        ('معلومات التتبع', {
            'fields': (
                'source_page',
                'referrer',
            ),
            'classes': ('collapse',)
        }),

        ('التواريخ', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
