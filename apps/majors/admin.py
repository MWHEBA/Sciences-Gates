"""
Django Admin registration for Major models.
Note: Django Admin is for emergency use only. Primary interface is Custom Dashboard.
"""
from django.contrib import admin
from .models import Major, MajorCategory, SubjectsTable, SalaryTable, CountriesTable


@admin.register(MajorCategory)
class MajorCategoryAdmin(admin.ModelAdmin):
    """Admin interface for MajorCategory model."""
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}


class SubjectsTableInline(admin.TabularInline):
    """Inline admin for SubjectsTable."""
    model = SubjectsTable
    extra = 1
    fields = ('academic_year', 'subjects', 'sort_order')


class SalaryTableInline(admin.TabularInline):
    """Inline admin for SalaryTable."""
    model = SalaryTable
    extra = 1
    fields = ('job_title', 'average_monthly_salary', 'sort_order')


class CountriesTableInline(admin.TabularInline):
    """Inline admin for CountriesTable."""
    model = CountriesTable
    extra = 1
    fields = ('destination', 'study_duration', 'annual_fees', 'living_cost', 'sort_order')


@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    """Admin interface for Major model."""
    list_display = ('name', 'study_duration', 'publish_status', 'created_at')
    list_filter = ('publish_status', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SubjectsTableInline, SalaryTableInline, CountriesTableInline]
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'slug', 'category', 'main_image')
        }),
        ('المحتوى', {
            'fields': ('description', 'study_duration', 'why_study_section', 'how_to_apply_section')
        }),
        ('معلومات سريعة', {
            'fields': ('tuition_fees', 'study_language', 'practical_training', 'career_opportunities')
        }),
        ('العلاقات', {
            'fields': ('best_universities', 'cheap_universities', 'related_articles')
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


@admin.register(SubjectsTable)
class SubjectsTableAdmin(admin.ModelAdmin):
    """Admin interface for SubjectsTable model."""
    list_display = ('academic_year', 'major', 'sort_order')
    list_filter = ('major', 'sort_order')
    search_fields = ('academic_year', 'subjects', 'major__name')
    ordering = ('major', 'sort_order')


@admin.register(SalaryTable)
class SalaryTableAdmin(admin.ModelAdmin):
    """Admin interface for SalaryTable model."""
    list_display = ('job_title', 'major', 'average_monthly_salary', 'sort_order')
    list_filter = ('major', 'sort_order')
    search_fields = ('job_title', 'major__name')
    ordering = ('major', 'sort_order')


@admin.register(CountriesTable)
class CountriesTableAdmin(admin.ModelAdmin):
    """Admin interface for CountriesTable model."""
    list_display = ('destination', 'major', 'annual_fees', 'sort_order')
    list_filter = ('major', 'sort_order')
    search_fields = ('destination', 'major__name')
    ordering = ('major', 'sort_order')
