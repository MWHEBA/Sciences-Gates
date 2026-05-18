"""
Django Admin registration for University models.
Note: Django Admin is for emergency use only. Primary interface is Custom Dashboard.
"""
from django.contrib import admin
from .models import University, Faculty, Program, UniversityFAQ


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    """Admin interface for University model."""
    list_display = ('name', 'location', 'publish_status', 'created_at')
    list_filter = ('publish_status', 'created_at')
    search_fields = ('name', 'location', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'slug', 'location')
        }),
        ('الصور', {
            'fields': ('logo', 'main_image')
        }),
        ('المحتوى', {
            'fields': ('description', 'admission_requirements', 'registration_section')
        }),
        ('الفيديو', {
            'fields': ('video_url',)
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


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    """Admin interface for Faculty model."""
    list_display = ('name', 'university', 'sort_order')
    list_filter = ('university', 'sort_order')
    search_fields = ('name', 'university__name')
    ordering = ('university', 'sort_order')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    """Admin interface for Program model."""
    list_display = ('name', 'faculty', 'duration', 'tuition_fees', 'sort_order')
    list_filter = ('faculty__university', 'faculty', 'sort_order')
    search_fields = ('name', 'faculty__name', 'faculty__university__name')
    ordering = ('faculty', 'sort_order')


@admin.register(UniversityFAQ)
class UniversityFAQAdmin(admin.ModelAdmin):
    """Admin interface for UniversityFAQ model."""
    list_display = ('question', 'university', 'sort_order')
    list_filter = ('university', 'sort_order')
    search_fields = ('question', 'answer', 'university__name')
    ordering = ('university', 'sort_order')
