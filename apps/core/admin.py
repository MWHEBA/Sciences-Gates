from django.contrib import admin
from apps.core.models import UserProfile, SiteSettings


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model (emergency use only)."""
    list_display = ('user', 'role', 'created_at', 'updated_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('معلومات المستخدم', {
            'fields': ('user',)
        }),
        ('الدور والصلاحيات', {
            'fields': ('role',)
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin interface for SiteSettings model."""
    list_display = ('site_name', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('معلومات الموقع', {
            'fields': ('site_name', 'site_description')
        }),
        ('خطوات التسجيل', {
            'fields': ('registration_steps_title', 'registration_steps_content'),
            'description': 'هذا المحتوى سيظهر في جميع صفحات الجامعات'
        }),
        ('معلومات التواصل', {
            'fields': ('phone', 'email', 'whatsapp'),
            'classes': ('collapse',)
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent adding new instances (singleton pattern)."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the singleton instance."""
        return False
