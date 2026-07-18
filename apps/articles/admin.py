"""
Django Admin registration for Article models.
Note: Django Admin is for emergency use only. Primary interface is Custom Dashboard.
"""
from django.contrib import admin
from .models import Article, Category, Tag, ArticleAttachment


class ArticleAttachmentInline(admin.TabularInline):
    """Inline admin interface for ArticleAttachment model."""
    model = ArticleAttachment
    extra = 1
    readonly_fields = ('file_size',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    list_display = ('name', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin interface for Tag model."""
    list_display = ('name',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin interface for Article model."""
    list_display = ('title', 'category', 'author', 'publish_status', 'publish_date')
    list_filter = ('publish_status', 'category', 'publish_date')
    search_fields = ('title', 'slug', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'publish_date')
    filter_horizontal = ('tags', 'related_universities', 'related_institutes', 'related_majors')
    inlines = [ArticleAttachmentInline]
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('title', 'slug', 'featured_image')
        }),
        ('المحتوى', {
            'fields': ('content', 'category', 'tags', 'author')
        }),
        ('العلاقات', {
            'fields': ('related_universities', 'related_institutes', 'related_majors')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'focus_keyword', 'canonical_url',
                      'robots_index', 'robots_follow', 'sitemap_include',
                      'og_title', 'og_description', 'og_image')
        }),
        ('النشر', {
            'fields': ('publish_status', 'publish_date')
        }),
        ('الطوابع الزمنية', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
