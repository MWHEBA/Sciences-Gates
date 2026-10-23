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
        'utm_source',
        'utm_medium',
        'utm_campaign',
        'utm_term',
        'utm_content',
    )
    
    fieldsets = (
        ('معلومات الرسالة', {
            'fields': (
                'lead_type',
                'name',
                'email',
                'phone',
                'institution_name',
                'nationality',
                'study_level',
                'residence_country',
                'address',
                'message',
                'is_read',
                'notes',
            )
        }),
        ('معلومات التتبع', {
            'fields': (
                'source_page',
                'referrer',
                'utm_source',
                'utm_medium',
                'utm_campaign',
                'utm_term',
                'utm_content',
                'ip_address',
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


from .models import LeadRejectionLog

@admin.register(LeadRejectionLog)
class LeadRejectionLogAdmin(admin.ModelAdmin):
    """Admin interface for LeadRejectionLog model (telemetry & audit)."""

    list_display = (
        'created_at',
        'reason',
        'lead_type',
        'source_kind',
        'ip_address',
    )
    search_fields = (
        'reason',
        'ip_address',
        'user_agent',
        'source_page',
    )
    list_filter = (
        'reason',
        'lead_type',
        'source_kind',
        'created_at',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'reason',
        'lead_type',
        'source_kind',
        'source_page',
        'ip_address',
        'user_agent',
        'details',
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

