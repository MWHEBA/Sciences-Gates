"""
Django Admin registration for Institute models.
Note: Django Admin is for emergency use only. Primary interface is Custom Dashboard.
"""
from django.contrib import admin
from .models import Institute, Course, InstituteAttachment


class InstituteAttachmentInline(admin.TabularInline):
    model = InstituteAttachment
    extra = 1
    fields = ('title', 'file', 'file_size')
    readonly_fields = ('file_size',)


@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    """Admin interface for Institute model."""
    inlines = [InstituteAttachmentInline]
    list_display = ('name', 'publish_status', 'created_at')
    list_filter = ('publish_status', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'slug', 'main_image')
        }),
        ('المحتوى', {
            'fields': ('description', 'registration_requirements', 'registration_section')
        }),
        ('العلاقات', {
            'fields': ('related_articles', 'tags')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'focus_keyword', 'canonical_url',
                      'robots_index', 'robots_follow', 'sitemap_include',
                      'og_title', 'og_description', 'og_image')
        }),
        ('النشر', {
            'fields': ('publish_status',)
        }),
        ('الطوابع الزمنية', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin interface for Course model."""
    list_display = ('name', 'institute', 'duration', 'fees')
    list_filter = ('institute',)
    search_fields = ('name', 'institute__name', 'description')
    ordering = ('institute', 'name')
