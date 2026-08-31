# Technical Design Document

## Introduction

This document provides the comprehensive technical design for the Science Gates platform (شركة بوابات العلوم للدراسة في ماليزيا), an Arabic-language educational content platform focused on Malaysian universities, institutes, study majors, and educational articles. The platform is built with Django, MySQL/MariaDB, Django Templates, Tailwind CSS, and Alpine.js, designed for cPanel deployment.

**Version 1 Scope**: Arabic-only with RTL support, architecture designed for future multilingual expansion without rebuilding.

**Primary Admin Interface**: Custom Dashboard (NOT Django Admin) - professional custom-built interface for all content and lead management.

**Content Editor**: Custom HTML Editor (NOT CKEditor or TinyMCE) - custom-built editor integrated into Custom Dashboard.

### Design Principles

1. **Simplicity First**: No overengineering - use Django's built-in features wherever possible
2. **Arabic RTL Native**: Design with RTL as the primary layout direction, not an afterthought
3. **cPanel Compatible**: All architectural decisions must support shared hosting deployment
4. **Future-Ready**: Architecture supports future multilingual expansion without rebuilding
5. **Performance Without Complexity**: Optimize using file-based caching and query optimization, not complex infrastructure
6. **Custom Dashboard First**: Professional custom-built admin interface as primary management tool (Django Admin for emergency use only)
7. **Custom HTML Editor**: Built specifically for the platform - no third-party WYSIWYG editors
8. **Security by Design**: Built-in protection against XSS, CSRF, SQL injection, and other common vulnerabilities
9. **No Overengineering**: Sized appropriately for ~200 articles and moderate content volume

### Technology Stack

- **Backend**: Django 4.2+ (LTS)
- **Database**: MySQL 8.0+ or MariaDB 10.6+
- **Templates**: Django Templates with RTL-first design
- **CSS Framework**: Tailwind CSS 3.x with RTL configuration
- **JavaScript**: Alpine.js 3.x for interactive components
- **HTML Editor**: Custom-built HTML editor (NOT CKEditor or TinyMCE)
- **Admin Interface**: Custom Dashboard (Django Admin for emergency use only)
- **Deployment**: cPanel with Passenger WSGI
- **Caching**: File-based cache (baseline), optional Redis if available
- **Search**: Django ORM Q objects (no Elasticsearch)
- **Image Processing**: Pillow for image optimization and WebP conversion
- **Security**: Django's built-in security + bleach for HTML sanitization
- **Email**: Django's email backend for lead notifications

### What We're NOT Using

- ❌ CKEditor or TinyMCE (using Custom HTML Editor)
- ❌ Django Admin as primary interface (using Custom Dashboard)
- ❌ Wagtail CMS
- ❌ React or Vue.js
- ❌ Elasticsearch or Meilisearch
- ❌ Redis (required) - optional only
- ❌ Complex caching infrastructure
- ❌ Complex editorial workflows
- ❌ Enterprise permission systems

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser (Arabic RTL)                │
│                  (Desktop, Tablet, Mobile)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    cPanel + Passenger WSGI                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Django Application Layer                 │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │   Public   │  │  Custom    │  │   Django   │     │   │
│  │  │   Views    │  │ Dashboard  │  │   Admin    │     │   │
│  │  │   (RTL)    │  │  (Arabic)  │  │(Emergency) │     │   │
│  │  └────────────┘  └────────────┘  └────────────┘     │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │   Models   │  │   Custom   │  │ Middleware │     │   │
│  │  │  (Content) │  │HTML Editor │  │ (Redirect) │     │   │
│  │  └────────────┘  └────────────┘  └────────────┘     │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ↓                ↓                ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    MySQL/    │  │  File-based  │  │    Media     │
│   MariaDB    │  │    Cache     │  │   Storage    │
│  (Content)   │  │  (Optional   │  │   (Images)   │
│              │  │    Redis)    │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Request Flow

#### Public Content Request
```
User → Nginx/Apache → Passenger WSGI → Django URLconf
  → View (with select_related/prefetch_related)
  → Template (RTL, Arabic)
  → Response (with SEO meta tags, schema markup)
```

#### Custom Dashboard Request
```
Admin User → Login → Custom Dashboard View
  → Role Check (Super Admin / Content Admin / SEO Admin)
  → Dashboard Template (Arabic RTL)
  → CRUD Operations → Database
  → Success/Error Message → Redirect
```

#### Lead Form Submission
```
Visitor → Lead Form → CSRF Check → Honeypot/reCAPTCHA
  → Validation → Save to Database
  → Email Notification → Admin
  → Thank You Page → Visitor
```

#### URL Redirect
```
User → Old URL → Redirect Middleware
  → Check Active Redirects → 301 Redirect → New URL
```


### Application Structure

```
science_gates/
├── config/                      # Django project settings
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py             # Shared settings
│   │   ├── local.py            # Development settings
│   │   └── production.py       # Production settings (cPanel)
│   ├── urls.py                 # Root URL configuration
│   ├── wsgi.py                 # WSGI application
│   ├── asgi.py                 # ASGI application (future)
│   └── __init__.py
├── apps/
│   ├── core/                   # Core functionality
│   │   ├── models.py           # Base models, mixins
│   │   ├── views.py            # Homepage, static pages
│   │   ├── context_processors.py  # Global template context
│   │   ├── middleware.py       # Custom middleware
│   │   ├── utils.py            # Utility functions
│   │   └── __init__.py
│   ├── dashboard/              # Custom Dashboard (PRIMARY ADMIN INTERFACE)
│   │   ├── views/              # Dashboard views
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Login, logout, user management
│   │   │   ├── home.py         # Dashboard home with statistics
│   │   │   ├── universities.py # University CRUD
│   │   │   ├── institutes.py  # Institute CRUD
│   │   │   ├── majors.py       # Major CRUD
│   │   │   ├── articles.py     # Article CRUD
│   │   │   ├── leads.py        # Lead management, filtering, export
│   │   │   ├── redirects.py    # Redirect management
│   │   │   ├── categories.py   # Category management
│   │   │   └── users.py        # User management (Super Admin only)
│   │   ├── forms/              # Dashboard forms
│   │   │   ├── __init__.py
│   │   │   ├── university.py   # University forms with inline FAQ
│   │   │   ├── institute.py    # Institute forms with inline Course
│   │   │   ├── major.py        # Major forms with dynamic tables
│   │   │   ├── article.py      # Article forms with Custom HTML Editor
│   │   │   ├── redirect.py     # Redirect forms
│   │   │   └── user.py         # User management forms
│   │   ├── decorators.py       # Role-based access decorators
│   │   ├── mixins.py           # Dashboard view mixins
│   │   ├── urls.py             # Dashboard URL patterns
│   │   ├── utils.py            # Dashboard utilities
│   │   └── __init__.py
│   ├── html_editor/            # Custom HTML Editor
│   │   ├── widgets.py          # Django form widget
│   │   ├── sanitizer.py        # HTML sanitization with bleach
│   │   ├── validators.py       # Content validation
│   │   ├── blocks.py           # Editor block types
│   │   ├── static/
│   │   │   ├── js/
│   │   │   │   └── html_editor.js  # Editor JavaScript
│   │   │   └── css/
│   │   │       └── html_editor.css # Editor styles
│   │   ├── templates/
│   │   │   └── html_editor/
│   │   │       ├── widget.html     # Editor template
│   │   │       └── preview.html    # Preview template
│   │   └── __init__.py
│   ├── universities/           # University content
│   │   ├── models.py           # University, Faculty, Program, FAQ
│   │   ├── admin.py            # Django Admin (emergency only)
│   │   ├── views.py            # Public views (list, detail)
│   │   ├── urls.py             # URL patterns
│   │   └── __init__.py
│   ├── institutes/             # Institute content
│   │   ├── models.py           # Institute, Course
│   │   ├── admin.py            # Django Admin (emergency only)
│   │   ├── views.py            # Public views (list, detail)
│   │   ├── urls.py             # URL patterns
│   │   └── __init__.py
│   ├── majors/                 # Major content
│   │   ├── models.py           # Major, SubjectsTable, SalaryTable, CountriesTable
│   │   ├── admin.py            # Django Admin (emergency only)
│   │   ├── views.py            # Public views (list, detail)
│   │   ├── urls.py             # URL patterns
│   │   └── __init__.py
│   ├── articles/               # Article/News content
│   │   ├── models.py           # Article, Category, Tag
│   │   ├── admin.py            # Django Admin (emergency only)
│   │   ├── views.py            # Public views (list, detail, category, tag)
│   │   ├── urls.py             # URL patterns
│   │   └── __init__.py
│   ├── leads/                  # Lead generation
│   │   ├── models.py           # Lead, LeadType
│   │   ├── admin.py            # Django Admin (emergency only)
│   │   ├── forms.py            # Lead forms with spam protection
│   │   ├── views.py            # Form submission
│   │   ├── signals.py          # Email notifications
│   │   └── __init__.py
│   ├── seo/                    # SEO functionality
│   │   ├── models.py           # SEO mixin
│   │   ├── sitemaps.py         # XML sitemap generation
│   │   ├── views.py            # robots.txt
│   │   ├── templatetags/       # SEO template tags
│   │   │   ├── __init__.py
│   │   │   ├── seo_tags.py     # Meta tags, schema markup
│   │   │   └── breadcrumbs.py  # Breadcrumb navigation
│   │   ├── schema.py           # Structured data generation
│   │   └── __init__.py
│   ├── redirects/              # URL redirect management
│   │   ├── models.py           # Redirect model
│   │   ├── admin.py            # Django Admin (emergency only)
│   │   ├── middleware.py       # 301 redirect middleware
│   │   └── __init__.py
│   ├── search/                 # Search functionality
│   │   ├── views.py            # Search view (Django ORM)
│   │   ├── forms.py            # Search form
│   │   ├── utils.py            # Search query builder
│   │   ├── urls.py             # URL patterns
│   │   └── __init__.py
│   └── __init__.py
├── templates/
│   ├── base.html               # Base template (RTL)
│   ├── dashboard/              # Custom Dashboard templates
│   │   ├── base.html           # Dashboard base template
│   │   ├── login.html          # Login page
│   │   ├── home.html           # Dashboard home with statistics
│   │   ├── universities/       # University management templates
│   │   │   ├── list.html
│   │   │   ├── create.html
│   │   │   ├── edit.html
│   │   │   └── delete_confirm.html
│   │   ├── institutes/         # Institute management templates
│   │   │   ├── list.html
│   │   │   ├── create.html
│   │   │   ├── edit.html
│   │   │   └── delete_confirm.html
│   │   ├── majors/             # Major management templates
│   │   │   ├── list.html
│   │   │   ├── create.html
│   │   │   ├── edit.html
│   │   │   └── delete_confirm.html
│   │   ├── articles/           # Article management templates
│   │   │   ├── list.html
│   │   │   ├── create.html
│   │   │   ├── edit.html
│   │   │   └── delete_confirm.html
│   │   ├── leads/              # Lead management templates
│   │   │   ├── list.html
│   │   │   ├── detail.html
│   │   │   └── export.html
│   │   ├── redirects/          # Redirect management templates
│   │   │   ├── list.html
│   │   │   ├── create.html
│   │   │   └── edit.html
│   │   ├── users/              # User management templates
│   │   │   ├── list.html
│   │   │   ├── create.html
│   │   │   └── edit.html
│   │   └── components/         # Dashboard components
│   │       ├── sidebar.html
│   │       ├── header.html
│   │       ├── pagination.html
│   │       ├── messages.html
│   │       └── form_field.html
│   ├── components/             # Public reusable components
│   │   ├── header.html
│   │   ├── footer.html
│   │   ├── lead_form.html
│   │   ├── breadcrumbs.html
│   │   └── pagination.html
│   ├── universities/           # University public templates
│   │   ├── list.html
│   │   └── detail.html
│   ├── institutes/             # Institute public templates
│   │   ├── list.html
│   │   └── detail.html
│   ├── majors/                 # Major public templates
│   │   ├── list.html
│   │   └── detail.html
│   ├── articles/               # Article public templates
│   │   ├── list.html
│   │   ├── detail.html
│   │   ├── category.html
│   │   └── tag.html
│   ├── search/                 # Search templates
│   │   └── results.html
│   └── includes/               # Partials
│       ├── head.html
│       ├── scripts.html
│       └── seo_meta.html
├── static/
│   ├── css/
│   │   ├── tailwind.css        # Tailwind source (RTL configured)
│   │   ├── dashboard.css       # Dashboard styles
│   │   └── custom.css          # Custom public styles
│   ├── js/
│   │   ├── alpine-components.js  # Alpine.js components
│   │   ├── dashboard.js        # Dashboard JavaScript
│   │   └── main.js             # Global JavaScript
│   └── images/                 # Static images
│       ├── logo.svg
│       └── placeholder.jpg
├── media/                      # User-uploaded content
│   ├── universities/
│   │   ├── logos/
│   │   └── images/
│   ├── institutes/
│   │   └── images/
│   ├── majors/
│   │   └── images/
│   ├── articles/
│   │   └── images/
│   ├── og_images/              # Open Graph images
│   └── temp/                   # Temporary uploads
├── locale/                     # Future: Translation files
│   └── ar/                     # Arabic translations (future)
│       └── LC_MESSAGES/
├── passenger_wsgi.py           # cPanel Passenger entry point
├── requirements.txt            # Python dependencies
├── manage.py                   # Django management script
├── .env.example                # Environment variables template
└── README.md                   # Project documentation
```


---

## Data Models

### Core Models and Mixins

#### TimestampedModel (Abstract Base)

```python
from django.db import models

class TimestampedModel(models.Model):
    """Abstract base model providing timestamp fields."""
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='تاريخ التحديث'
    )
    
    class Meta:
        abstract = True
```

#### PublishableModel (Abstract Base)

```python
class PublishStatus(models.TextChoices):
    PUBLISHED = 'published', 'منشور'
    UNPUBLISHED = 'unpublished', 'غير منشور'

class PublishableModel(models.Model):
    """Abstract base model providing publish status."""
    publish_status = models.CharField(
        max_length=20,
        choices=PublishStatus.choices,
        default=PublishStatus.UNPUBLISHED,
        verbose_name='حالة النشر',
        help_text='المحتوى المنشور فقط يظهر للزوار',
        db_index=True
    )
    
    class Meta:
        abstract = True
    
    @property
    def is_published(self):
        """Check if content is published."""
        return self.publish_status == PublishStatus.PUBLISHED
    
    def publish(self):
        """Publish the content."""
        self.publish_status = PublishStatus.PUBLISHED
        self.save(update_fields=['publish_status', 'updated_at'])
    
    def unpublish(self):
        """Unpublish the content."""
        self.publish_status = PublishStatus.UNPUBLISHED
        self.save(update_fields=['publish_status', 'updated_at'])
```

#### SEOMixin (Abstract Base)

```python
class SEOMixin(models.Model):
    """Abstract mixin providing SEO fields for all content types."""
    # Basic SEO
    meta_title = models.CharField(
        max_length=60, 
        blank=True, 
        verbose_name='عنوان SEO',
        help_text='يظهر في نتائج البحث (60 حرف كحد أقصى)'
    )
    meta_description = models.TextField(
        max_length=160, 
        blank=True, 
        verbose_name='وصف SEO',
        help_text='يظهر في نتائج البحث (160 حرف كحد أقصى)'
    )
    focus_keyword = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='الكلمة المفتاحية',
        help_text='الكلمة المفتاحية الرئيسية للصفحة'
    )
    canonical_url = models.URLField(
        blank=True, 
        verbose_name='الرابط الأساسي',
        help_text='اتركه فارغاً لاستخدام الرابط الافتراضي'
    )
    
    # Robots
    robots_index = models.BooleanField(
        default=True, 
        verbose_name='السماح بالفهرسة',
        help_text='السماح لمحركات البحث بفهرسة هذه الصفحة'
    )
    robots_follow = models.BooleanField(
        default=True, 
        verbose_name='السماح بتتبع الروابط',
        help_text='السماح لمحركات البحث بتتبع الروابط في هذه الصفحة'
    )
    sitemap_include = models.BooleanField(
        default=True, 
        verbose_name='تضمين في خريطة الموقع',
        help_text='تضمين هذه الصفحة في ملف sitemap.xml'
    )
    
    # Open Graph
    og_title = models.CharField(
        max_length=60, 
        blank=True, 
        verbose_name='عنوان Open Graph',
        help_text='العنوان عند المشاركة على وسائل التواصل'
    )
    og_description = models.TextField(
        max_length=160, 
        blank=True, 
        verbose_name='وصف Open Graph',
        help_text='الوصف عند المشاركة على وسائل التواصل'
    )
    og_image = models.ImageField(
        upload_to='og_images/', 
        blank=True, 
        verbose_name='صورة Open Graph',
        help_text='الصورة عند المشاركة على وسائل التواصل (1200x630 بكسل)'
    )
    
    class Meta:
        abstract = True
    
    def get_meta_title(self):
        """Return meta title or fallback to main title."""
        return self.meta_title or getattr(self, 'name', '') or getattr(self, 'title', '')
    
    def get_meta_description(self):
        """Return meta description or generate from content."""
        if self.meta_description:
            return self.meta_description
        description = getattr(self, 'description', '')
        return description[:160] if description else ''
    
    def get_robots_content(self):
        """Generate robots meta tag content."""
        index = 'index' if self.robots_index else 'noindex'
        follow = 'follow' if self.robots_follow else 'nofollow'
        return f'{index}, {follow}'
    
    def get_og_title(self):
        """Return OG title or fallback to meta title."""
        return self.og_title or self.get_meta_title()
    
    def get_og_description(self):
        """Return OG description or fallback to meta description."""
        return self.og_description or self.get_meta_description()
    
    def get_og_image_url(self):
        """Return OG image URL or fallback to main image."""
        if self.og_image:
            return self.og_image.url
        main_image = getattr(self, 'main_image', None) or getattr(self, 'featured_image', None)
        return main_image.url if main_image else None
```

### University Models

#### University Model

```python
from django.db import models
from django.urls import reverse
from apps.core.models import TimestampedModel, PublishableModel, SEOMixin

class University(TimestampedModel, PublishableModel, SEOMixin):
    """University content model."""
    name = models.CharField(
        max_length=200, 
        verbose_name='اسم الجامعة',
        db_index=True
    )
    slug = models.SlugField(
        max_length=200, 
        unique=True, 
        verbose_name='الرابط',
        help_text='رابط الصفحة (يدعم الأحرف العربية)',
        allow_unicode=True
    )
    logo = models.ImageField(
        upload_to='universities/logos/', 
        verbose_name='شعار الجامعة',
        help_text='شعار الجامعة (PNG مع خلفية شفافة مفضل)'
    )
    main_image = models.ImageField(
        upload_to='universities/images/', 
        verbose_name='الصورة الرئيسية',
        help_text='صورة رئيسية للجامعة'
    )
    description = models.TextField(
        verbose_name='الوصف',
        help_text='وصف شامل عن الجامعة'
    )
    location = models.CharField(
        max_length=200, 
        verbose_name='الموقع',
        help_text='موقع الجامعة (المدينة، الولاية)'
    )
    video_url = models.URLField(
        blank=True, 
        verbose_name='رابط الفيديو',
        help_text='رابط فيديو YouTube أو Vimeo'
    )
    admission_requirements = models.TextField(
        verbose_name='شروط القبول',
        help_text='شروط القبول في الجامعة'
    )
    
    # Relationships
    related_majors = models.ManyToManyField(
        'majors.Major',
        blank=True,
        related_name='universities',
        verbose_name='التخصصات المرتبطة'
    )
    related_articles = models.ManyToManyField(
        'articles.Article',
        blank=True,
        related_name='universities',
        verbose_name='المقالات المرتبطة'
    )
    
    class Meta:
        verbose_name = 'جامعة'
        verbose_name_plural = 'الجامعات'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('universities:detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        # Store old slug for redirect creation
        if self.pk:
            old_instance = University.objects.get(pk=self.pk)
            if old_instance.slug != self.slug and old_instance.is_published:
                # Signal to create redirect (handled in dashboard)
                self._old_slug = old_instance.slug
        super().save(*args, **kwargs)
```

#### Faculty Model

```python
class Faculty(models.Model):
    """Faculty within a university."""
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='faculties',
        verbose_name='الجامعة'
    )
    name = models.CharField(
        max_length=200, 
        verbose_name='اسم الكلية'
    )
    sort_order = models.PositiveIntegerField(
        default=0, 
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور الكلية (الأصغر أولاً)'
    )
    
    class Meta:
        verbose_name = 'كلية'
        verbose_name_plural = 'الكليات'
        ordering = ['sort_order', 'name']
        unique_together = ['university', 'name']
    
    def __str__(self):
        return f'{self.name} - {self.university.name}'
```

#### Program Model

```python
class Program(models.Model):
    """Program within a faculty."""
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='programs',
        verbose_name='الكلية'
    )
    name = models.CharField(
        max_length=200, 
        verbose_name='اسم البرنامج'
    )
    duration = models.CharField(
        max_length=100, 
        verbose_name='مدة الدراسة',
        help_text='مثال: 4 سنوات'
    )
    tuition_fees = models.CharField(
        max_length=100, 
        verbose_name='الرسوم الدراسية',
        help_text='مثال: 20,000 رنجت ماليزي سنوياً'
    )
    sort_order = models.PositiveIntegerField(
        default=0, 
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور البرنامج (الأصغر أولاً)'
    )
    
    class Meta:
        verbose_name = 'برنامج'
        verbose_name_plural = 'البرامج'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f'{self.name} - {self.faculty.name}'
```

#### UniversityFAQ Model

```python
class UniversityFAQ(models.Model):
    """FAQ entry for a university."""
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name='الجامعة'
    )
    question = models.CharField(
        max_length=300, 
        verbose_name='السؤال'
    )
    answer = models.TextField(
        verbose_name='الإجابة'
    )
    sort_order = models.PositiveIntegerField(
        default=0, 
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور السؤال (الأصغر أولاً)'
    )
    
    class Meta:
        verbose_name = 'سؤال شائع'
        verbose_name_plural = 'الأسئلة الشائعة'
        ordering = ['sort_order']
    
    def __str__(self):
        return self.question
```


### Institute Models

#### Institute Model

```python
class Institute(TimestampedModel, PublishableModel, SEOMixin):
    """Institute content model."""
    name = models.CharField(
        max_length=200, 
        verbose_name='اسم المعهد',
        db_index=True
    )
    slug = models.SlugField(
        max_length=200, 
        unique=True, 
        verbose_name='الرابط',
        help_text='رابط الصفحة (يدعم الأحرف العربية)',
        allow_unicode=True
    )
    main_image = models.ImageField(
        upload_to='institutes/images/', 
        verbose_name='الصورة الرئيسية'
    )
    description = models.TextField(
        verbose_name='الوصف',
        help_text='وصف شامل عن المعهد'
    )
    registration_requirements = models.TextField(
        verbose_name='شروط التسجيل',
        help_text='شروط التسجيل في المعهد'
    )
    
    # Relationships
    related_articles = models.ManyToManyField(
        'articles.Article',
        blank=True,
        related_name='institutes',
        verbose_name='المقالات المرتبطة'
    )
    
    class Meta:
        verbose_name = 'معهد'
        verbose_name_plural = 'المعاهد'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('institutes:detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = Institute.objects.get(pk=self.pk)
            if old_instance.slug != self.slug and old_instance.is_published:
                self._old_slug = old_instance.slug
        super().save(*args, **kwargs)
```

#### Course Model

```python
class Course(models.Model):
    """Course within an institute."""
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name='المعهد'
    )
    name = models.CharField(
        max_length=200, 
        verbose_name='اسم الدورة'
    )
    duration = models.CharField(
        max_length=100, 
        verbose_name='مدة الدورة',
        help_text='مثال: 6 أشهر'
    )
    fees = models.CharField(
        max_length=100, 
        verbose_name='الرسوم',
        help_text='مثال: 5,000 رنجت ماليزي'
    )
    description = models.TextField(
        verbose_name='الوصف',
        help_text='وصف الدورة'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات',
        help_text='ملاحظات إضافية عن الدورة'
    )
    
    class Meta:
        verbose_name = 'دورة'
        verbose_name_plural = 'الدورات'
        ordering = ['name']
    
    def __str__(self):
        return f'{self.name} - {self.institute.name}'
```

### Major Models

#### Major Model

```python
class Major(TimestampedModel, PublishableModel, SEOMixin):
    """Major/Specialization content model."""
    name = models.CharField(
        max_length=200, 
        verbose_name='اسم التخصص',
        db_index=True
    )
    slug = models.SlugField(
        max_length=200, 
        unique=True, 
        verbose_name='الرابط',
        help_text='رابط الصفحة (يدعم الأحرف العربية)',
        allow_unicode=True
    )
    main_image = models.ImageField(
        upload_to='majors/images/', 
        verbose_name='الصورة الرئيسية'
    )
    description = models.TextField(
        verbose_name='الوصف',
        help_text='وصف شامل عن التخصص'
    )
    study_duration = models.CharField(
        max_length=100, 
        verbose_name='مدة الدراسة',
        help_text='مثال: 4 سنوات'
    )
    
    # Quick Information Fields
    tuition_fees = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='الرسوم الدراسية',
        help_text='مثال: 15,000 - 25,000 رنجت سنوياً'
    )
    study_language = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='لغة الدراسة',
        help_text='مثال: الإنجليزية'
    )
    practical_training = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='التدريب العملي',
        help_text='مثال: متاح في السنة الأخيرة'
    )
    career_opportunities = models.TextField(
        blank=True,
        verbose_name='فرص العمل',
        help_text='وصف موجز لفرص العمل'
    )
    
    # Content Sections
    why_study_section = models.TextField(
        blank=True,
        verbose_name='لماذا دراسة هذا التخصص',
        help_text='محتوى قسم "لماذا دراسة هذا التخصص"'
    )
    how_to_apply_section = models.TextField(
        blank=True,
        verbose_name='كيفية التقديم',
        help_text='محتوى قسم "كيفية التقديم"'
    )
    
    # Relationships
    best_universities = models.ManyToManyField(
        'universities.University',
        blank=True,
        related_name='best_for_majors',
        verbose_name='أفضل الجامعات'
    )
    cheap_universities = models.ManyToManyField(
        'universities.University',
        blank=True,
        related_name='cheap_for_majors',
        verbose_name='الجامعات الأرخص'
    )
    related_articles = models.ManyToManyField(
        'articles.Article',
        blank=True,
        related_name='majors',
        verbose_name='المقالات المرتبطة'
    )
    
    class Meta:
        verbose_name = 'تخصص'
        verbose_name_plural = 'التخصصات'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('majors:detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = Major.objects.get(pk=self.pk)
            if old_instance.slug != self.slug and old_instance.is_published:
                self._old_slug = old_instance.slug
        super().save(*args, **kwargs)
```

#### Dynamic Table Models

```python
class SubjectsTable(models.Model):
    """Subjects table for a major (Academic Year → Subjects)."""
    major = models.ForeignKey(
        Major,
        on_delete=models.CASCADE,
        related_name='subjects_table',
        verbose_name='التخصص'
    )
    academic_year = models.CharField(
        max_length=100, 
        verbose_name='السنة الدراسية',
        help_text='مثال: السنة الأولى'
    )
    subjects = models.TextField(
        verbose_name='المواد',
        help_text='قائمة المواد (سطر لكل مادة)'
    )
    sort_order = models.PositiveIntegerField(
        default=0, 
        verbose_name='ترتيب العرض'
    )
    
    class Meta:
        verbose_name = 'جدول المواد'
        verbose_name_plural = 'جداول المواد'
        ordering = ['sort_order']
    
    def __str__(self):
        return f'{self.academic_year} - {self.major.name}'

class SalaryTable(models.Model):
    """Salary table for a major (Job Title → Average Monthly Salary)."""
    major = models.ForeignKey(
        Major,
        on_delete=models.CASCADE,
        related_name='salary_table',
        verbose_name='التخصص'
    )
    job_title = models.CharField(
        max_length=200, 
        verbose_name='المسمى الوظيفي'
    )
    average_monthly_salary = models.CharField(
        max_length=100, 
        verbose_name='متوسط الراتب الشهري',
        help_text='مثال: 5,000 - 8,000 رنجت'
    )
    sort_order = models.PositiveIntegerField(
        default=0, 
        verbose_name='ترتيب العرض'
    )
    
    class Meta:
        verbose_name = 'جدول الرواتب'
        verbose_name_plural = 'جداول الرواتب'
        ordering = ['sort_order']
    
    def __str__(self):
        return f'{self.job_title} - {self.major.name}'

class CountriesTable(models.Model):
    """Countries table for a major (Destination → Duration, Fees, Living Cost)."""
    major = models.ForeignKey(
        Major,
        on_delete=models.CASCADE,
        related_name='countries_table',
        verbose_name='التخصص'
    )
    destination = models.CharField(
        max_length=100, 
        verbose_name='الوجهة',
        help_text='مثال: ماليزيا'
    )
    study_duration = models.CharField(
        max_length=100, 
        verbose_name='مدة الدراسة',
        help_text='مثال: 4 سنوات'
    )
    annual_fees = models.CharField(
        max_length=100, 
        verbose_name='الرسوم السنوية',
        help_text='مثال: 20,000 رنجت'
    )
    living_cost = models.CharField(
        max_length=100, 
        verbose_name='تكلفة المعيشة',
        help_text='مثال: 1,500 رنجت شهرياً'
    )
    sort_order = models.PositiveIntegerField(
        default=0, 
        verbose_name='ترتيب العرض'
    )
    
    class Meta:
        verbose_name = 'جدول الدول'
        verbose_name_plural = 'جداول الدول'
        ordering = ['sort_order']
    
    def __str__(self):
        return f'{self.destination} - {self.major.name}'
```


### Article Models

#### Category Model

```python
class Category(TimestampedModel):
    """Article category."""
    name = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='اسم التصنيف',
        db_index=True
    )
    slug = models.SlugField(
        max_length=100, 
        unique=True, 
        verbose_name='الرابط',
        allow_unicode=True
    )
    description = models.TextField(
        blank=True,
        verbose_name='الوصف'
    )
    
    class Meta:
        verbose_name = 'تصنيف'
        verbose_name_plural = 'التصنيفات'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('articles:category', kwargs={'slug': self.slug})
```

#### Tag Model

```python
class Tag(models.Model):
    """Article tag."""
    name = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='اسم الوسم',
        db_index=True
    )
    slug = models.SlugField(
        max_length=50, 
        unique=True, 
        verbose_name='الرابط',
        allow_unicode=True
    )
    
    class Meta:
        verbose_name = 'وسم'
        verbose_name_plural = 'الوسوم'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('articles:tag', kwargs={'slug': self.slug})
```

#### Article Model

```python
from apps.html_editor.widgets import CustomHTMLEditorWidget

class Article(TimestampedModel, PublishableModel, SEOMixin):
    """Article/News content model."""
    title = models.CharField(
        max_length=200, 
        verbose_name='العنوان',
        db_index=True
    )
    slug = models.SlugField(
        max_length=200, 
        unique=True, 
        verbose_name='الرابط',
        help_text='رابط الصفحة (يدعم الأحرف العربية)',
        allow_unicode=True
    )
    featured_image = models.ImageField(
        upload_to='articles/images/', 
        verbose_name='الصورة المميزة'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='articles',
        verbose_name='التصنيف'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='articles',
        verbose_name='الوسوم'
    )
    author = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='articles',
        verbose_name='الكاتب'
    )
    publish_date = models.DateTimeField(
        verbose_name='تاريخ النشر',
        help_text='تاريخ ووقت نشر المقال'
    )
    
    # Content (uses Custom HTML Editor)
    content = models.TextField(
        verbose_name='المحتوى',
        help_text='محتوى المقال (HTML)'
    )
    
    # Relationships
    related_universities = models.ManyToManyField(
        'universities.University',
        blank=True,
        related_name='related_articles',
        verbose_name='الجامعات المرتبطة'
    )
    related_institutes = models.ManyToManyField(
        'institutes.Institute',
        blank=True,
        related_name='related_articles',
        verbose_name='المعاهد المرتبطة'
    )
    related_majors = models.ManyToManyField(
        'majors.Major',
        blank=True,
        related_name='related_articles',
        verbose_name='التخصصات المرتبطة'
    )
    
    class Meta:
        verbose_name = 'مقال'
        verbose_name_plural = 'المقالات'
        ordering = ['-publish_date']
        indexes = [
            models.Index(fields=['-publish_date']),
            models.Index(fields=['category', '-publish_date']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('articles:detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = Article.objects.get(pk=self.pk)
            if old_instance.slug != self.slug and old_instance.is_published:
                self._old_slug = old_instance.slug
        super().save(*args, **kwargs)
```

### Lead Models

#### Lead Model

```python
class LeadType(models.TextChoices):
    REGISTRATION = 'registration', 'طلب تسجيل'
    CONTACT = 'contact', 'طلب تواصل'

class Lead(TimestampedModel):
    """Lead form submission."""
    # Form Type
    lead_type = models.CharField(
        max_length=20,
        choices=LeadType.choices,
        verbose_name='نوع الطلب',
        db_index=True
    )
    
    # User Information
    name = models.CharField(
        max_length=100, 
        verbose_name='الاسم'
    )
    email = models.EmailField(
        verbose_name='البريد الإلكتروني'
    )
    phone = models.CharField(
        max_length=20, 
        verbose_name='رقم الهاتف'
    )
    message = models.TextField(
        verbose_name='الرسالة'
    )
    
    # Tracking Information
    source_page = models.URLField(
        verbose_name='صفحة المصدر',
        help_text='الصفحة التي تم إرسال النموذج منها'
    )
    referrer = models.URLField(
        blank=True,
        verbose_name='المُحيل',
        help_text='الصفحة التي جاء منها الزائر'
    )
    
    # UTM Parameters
    utm_source = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='UTM Source'
    )
    utm_medium = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='UTM Medium'
    )
    utm_campaign = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='UTM Campaign'
    )
    utm_term = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='UTM Term'
    )
    utm_content = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='UTM Content'
    )
    
    # Status
    is_read = models.BooleanField(
        default=False,
        verbose_name='تم القراءة'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات',
        help_text='ملاحظات داخلية (لا تظهر للزائر)'
    )
    
    class Meta:
        verbose_name = 'طلب'
        verbose_name_plural = 'الطلبات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['lead_type', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.get_lead_type_display()} - {self.name} - {self.created_at.strftime("%Y-%m-%d")}'
```

### Redirect Model

```python
class Redirect(TimestampedModel):
    """URL redirect for preserving SEO when URLs change."""
    old_url = models.CharField(
        max_length=500,
        unique=True,
        verbose_name='الرابط القديم',
        help_text='الرابط القديم (بدون النطاق، مثال: /universities/old-slug/)',
        db_index=True
    )
    new_url = models.CharField(
        max_length=500,
        verbose_name='الرابط الجديد',
        help_text='الرابط الجديد (بدون النطاق، مثال: /universities/new-slug/)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        help_text='تفعيل أو تعطيل التحويل',
        db_index=True
    )
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات',
        help_text='ملاحظات داخلية عن سبب التحويل'
    )
    hit_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد الزيارات',
        help_text='عدد المرات التي تم استخدام هذا التحويل'
    )
    
    class Meta:
        verbose_name = 'تحويل'
        verbose_name_plural = 'التحويلات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.old_url} → {self.new_url}'
    
    def increment_hit_count(self):
        """Increment hit count when redirect is used."""
        self.hit_count += 1
        self.save(update_fields=['hit_count'])
```

### User Role Model

```python
from django.contrib.auth.models import User

class UserRole(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'مدير عام'
    CONTENT_ADMIN = 'content_admin', 'مدير محتوى'
    SEO_ADMIN = 'seo_admin', 'مدير SEO'

class UserProfile(models.Model):
    """Extended user profile with role."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='المستخدم'
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CONTENT_ADMIN,
        verbose_name='الدور',
        db_index=True
    )
    
    class Meta:
        verbose_name = 'ملف المستخدم'
        verbose_name_plural = 'ملفات المستخدمين'
    
    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'
    
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN
    
    def is_content_admin(self):
        return self.role in [UserRole.SUPER_ADMIN, UserRole.CONTENT_ADMIN]
    
    def is_seo_admin(self):
        return self.role in [UserRole.SUPER_ADMIN, UserRole.SEO_ADMIN]
```


---

## Custom Dashboard Design

### Overview

The Custom Dashboard is the **primary admin interface** for the Science Gates platform. It is a professional, custom-built interface designed specifically for content and lead management, built with Django views, forms, and templates.

**Key Characteristics:**
- Arabic RTL interface throughout
- Role-based access control (Super Admin, Content Admin, SEO Admin)
- Intuitive navigation and organized sections
- Inline editing for related entities (Program, Course, FAQ, Dynamic Tables)
- Separate Faculty management views with inline Programs
- Integrated Custom HTML Editor for article content
- Lead management with filtering and CSV export
- Redirect management with automatic creation on slug changes
- Simple statistics dashboard (total leads, leads by type, current month leads)

**Django Admin Role:**
- Django Admin is maintained for emergency or technical use only
- Not the primary interface for content management
- Used for database-level operations if needed

### Dashboard Architecture

#### URL Structure

```
/dashboard/                          # Dashboard home (statistics)
/dashboard/login/                    # Login page
/dashboard/logout/                   # Logout

# Universities
/dashboard/universities/             # List universities
/dashboard/universities/create/      # Create university
/dashboard/universities/<id>/edit/   # Edit university (with inline FAQ, Faculty list)
/dashboard/universities/<id>/delete/ # Delete university
/dashboard/universities/<id>/faculties/  # List faculties for university
/dashboard/universities/<id>/faculties/create/  # Create faculty with inline Programs
/dashboard/faculties/<id>/edit/      # Edit faculty with inline Programs
/dashboard/faculties/<id>/delete/    # Delete faculty

# Institutes
/dashboard/institutes/               # List institutes
/dashboard/institutes/create/        # Create institute
/dashboard/institutes/<id>/edit/     # Edit institute (with inline Course)
/dashboard/institutes/<id>/delete/   # Delete institute

# Majors
/dashboard/majors/                   # List majors
/dashboard/majors/create/            # Create major
/dashboard/majors/<id>/edit/         # Edit major (with inline Dynamic Tables)
/dashboard/majors/<id>/delete/       # Delete major

# Articles
/dashboard/articles/                 # List articles
/dashboard/articles/create/          # Create article (with Custom HTML Editor)
/dashboard/articles/<id>/edit/       # Edit article (with Custom HTML Editor)
/dashboard/articles/<id>/delete/     # Delete article
/dashboard/articles/<id>/preview/    # Preview article

# Categories & Tags
/dashboard/categories/               # Manage categories
/dashboard/tags/                     # Manage tags

# Leads
/dashboard/leads/                    # List leads (with filters)
/dashboard/leads/<id>/                # View lead detail
/dashboard/leads/export/             # Export leads to CSV

# Redirects
/dashboard/redirects/                # List redirects
/dashboard/redirects/create/         # Create redirect
/dashboard/redirects/<id>/edit/      # Edit redirect
/dashboard/redirects/<id>/delete/    # Delete redirect

# Users (Super Admin only)
/dashboard/users/                    # List users
/dashboard/users/create/             # Create user
/dashboard/users/<id>/edit/          # Edit user
/dashboard/users/<id>/delete/        # Delete user
```

#### View Architecture

**Base Dashboard View Mixin:**

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages

class DashboardMixin(LoginRequiredMixin):
    """Base mixin for all dashboard views."""
    login_url = '/dashboard/login/'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user has profile
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'ليس لديك صلاحية للوصول إلى لوحة التحكم')
            return redirect('dashboard:login')
        return super().dispatch(request, *args, **kwargs)

class ContentAdminRequiredMixin(DashboardMixin):
    """Mixin requiring Content Admin or Super Admin role."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.profile.is_content_admin():
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)

class SEOAdminRequiredMixin(DashboardMixin):
    """Mixin requiring SEO Admin or Super Admin role."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.profile.is_seo_admin():
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)

class SuperAdminRequiredMixin(DashboardMixin):
    """Mixin requiring Super Admin role."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.profile.is_super_admin():
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
```

**Dashboard Home View:**

```python
from django.views.generic import TemplateView
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime

class DashboardHomeView(DashboardMixin, TemplateView):
    """Dashboard home with simple statistics."""
    template_name = 'dashboard/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Simple statistics
        context['total_leads'] = Lead.objects.count()
        context['registration_leads'] = Lead.objects.filter(
            lead_type=LeadType.REGISTRATION
        ).count()
        context['contact_leads'] = Lead.objects.filter(
            lead_type=LeadType.CONTACT
        ).count()
        
        # Current month leads
        now = timezone.now()
        context['current_month_leads'] = Lead.objects.filter(
            created_at__year=now.year,
            created_at__month=now.month
        ).count()
        
        # Content counts
        context['published_universities'] = University.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).count()
        context['published_institutes'] = Institute.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).count()
        context['published_majors'] = Major.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).count()
        context['published_articles'] = Article.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).count()
        
        # Recent leads (last 10)
        context['recent_leads'] = Lead.objects.select_related().order_by('-created_at')[:10]
        
        return context
```

**University CRUD Views:**

**IMPORTANT ARCHITECTURAL NOTE:** 
Due to the nested relationship (University → Faculty → Program), we use **separate management pages** for Faculty and Program instead of complex nested inline formsets. This approach is simpler, more maintainable, and provides better UX.

**University Management Flow:**
1. University Edit Page: Manage university data + inline FAQ
2. Faculty List Page (for specific university): View/manage faculties
3. Faculty Edit Page: Manage faculty data + inline Programs

```python
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.forms import inlineformset_factory

class UniversityListView(ContentAdminRequiredMixin, ListView):
    """List all universities."""
    model = University
    template_name = 'dashboard/universities/list.html'
    context_object_name = 'universities'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = University.objects.all().order_by('-created_at')
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(slug__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(publish_status=status)
        
        return queryset

class UniversityCreateView(ContentAdminRequiredMixin, CreateView):
    """Create a new university with inline FAQ only."""
    model = University
    template_name = 'dashboard/universities/create.html'
    fields = [
        'name', 'slug', 'logo', 'main_image', 'description', 
        'location', 'video_url', 'admission_requirements',
        'publish_status', 'related_majors', 'related_articles',
        # SEO fields
        'meta_title', 'meta_description', 'focus_keyword',
        'canonical_url', 'robots_index', 'robots_follow',
        'sitemap_include', 'og_title', 'og_description', 'og_image'
    ]
    success_url = reverse_lazy('dashboard:universities')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Inline FAQ formset only
        FAQFormSet = inlineformset_factory(
            University, UniversityFAQ,
            fields=['question', 'answer', 'sort_order'],
            extra=1, can_delete=True
        )
        
        if self.request.POST:
            context['faq_formset'] = FAQFormSet(self.request.POST)
        else:
            context['faq_formset'] = FAQFormSet()
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        faq_formset = context['faq_formset']
        
        if faq_formset.is_valid():
            self.object = form.save()
            faq_formset.instance = self.object
            faq_formset.save()
            
            messages.success(self.request, 'تم إنشاء الجامعة بنجاح')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

class UniversityUpdateView(ContentAdminRequiredMixin, UpdateView):
    """Edit an existing university with inline FAQ and faculty list."""
    model = University
    template_name = 'dashboard/universities/edit.html'
    fields = [
        'name', 'slug', 'logo', 'main_image', 'description', 
        'location', 'video_url', 'admission_requirements',
        'publish_status', 'related_majors', 'related_articles',
        # SEO fields
        'meta_title', 'meta_description', 'focus_keyword',
        'canonical_url', 'robots_index', 'robots_follow',
        'sitemap_include', 'og_title', 'og_description', 'og_image'
    ]
    success_url = reverse_lazy('dashboard:universities')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if slug changed
        if self.object.pk:
            old_instance = University.objects.get(pk=self.object.pk)
            if old_instance.slug != self.object.slug and old_instance.is_published:
                context['slug_changed'] = True
                context['old_slug'] = old_instance.slug
        
        # Inline FAQ formset
        FAQFormSet = inlineformset_factory(
            University, UniversityFAQ,
            fields=['question', 'answer', 'sort_order'],
            extra=1, can_delete=True
        )
        
        if self.request.POST:
            context['faq_formset'] = FAQFormSet(self.request.POST, instance=self.object)
        else:
            context['faq_formset'] = FAQFormSet(instance=self.object)
        
        # Get faculties for display (read-only list with edit links)
        context['faculties'] = self.object.faculties.prefetch_related('programs').all()
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        faq_formset = context['faq_formset']
        
        if faq_formset.is_valid():
            self.object = form.save()
            faq_formset.save()
            
            # Check if slug changed and offer to create redirect
            if hasattr(self.object, '_old_slug'):
                create_redirect = self.request.POST.get('create_redirect')
                if create_redirect == 'yes':
                    Redirect.objects.create(
                        old_url=f'/universities/{self.object._old_slug}/',
                        new_url=f'/universities/{self.object.slug}/',
                        is_active=True,
                        notes=f'تحويل تلقائي من تغيير slug الجامعة: {self.object.name}'
                    )
                    messages.success(self.request, 'تم إنشاء تحويل تلقائي للرابط القديم')
            
            messages.success(self.request, 'تم تحديث الجامعة بنجاح')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

class UniversityDeleteView(ContentAdminRequiredMixin, DeleteView):
    """Delete a university."""
    model = University
    template_name = 'dashboard/universities/delete_confirm.html'
    success_url = reverse_lazy('dashboard:universities')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف الجامعة بنجاح')
        return super().delete(request, *args, **kwargs)
```

**Faculty Management Views (Separate Pages):**

```python
class FacultyListView(ContentAdminRequiredMixin, ListView):
    """List faculties for a specific university."""
    model = Faculty
    template_name = 'dashboard/faculties/list.html'
    context_object_name = 'faculties'
    
    def get_queryset(self):
        university_id = self.kwargs['university_id']
        return Faculty.objects.filter(university_id=university_id).prefetch_related('programs')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['university'] = University.objects.get(pk=self.kwargs['university_id'])
        return context

class FacultyCreateView(ContentAdminRequiredMixin, CreateView):
    """Create a new faculty with inline programs."""
    model = Faculty
    template_name = 'dashboard/faculties/create.html'
    fields = ['name', 'sort_order']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['university'] = University.objects.get(pk=self.kwargs['university_id'])
        
        # Inline Program formset
        ProgramFormSet = inlineformset_factory(
            Faculty, Program,
            fields=['name', 'duration', 'tuition_fees', 'sort_order'],
            extra=1, can_delete=True
        )
        
        if self.request.POST:
            context['program_formset'] = ProgramFormSet(self.request.POST)
        else:
            context['program_formset'] = ProgramFormSet()
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        program_formset = context['program_formset']
        
        if program_formset.is_valid():
            form.instance.university_id = self.kwargs['university_id']
            self.object = form.save()
            program_formset.instance = self.object
            program_formset.save()
            
            messages.success(self.request, 'تم إنشاء الكلية بنجاح')
            return redirect('dashboard:faculties', university_id=self.kwargs['university_id'])
        else:
            return self.form_invalid(form)

class FacultyUpdateView(ContentAdminRequiredMixin, UpdateView):
    """Edit an existing faculty with inline programs."""
    model = Faculty
    template_name = 'dashboard/faculties/edit.html'
    fields = ['name', 'sort_order']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['university'] = self.object.university
        
        # Inline Program formset
        ProgramFormSet = inlineformset_factory(
            Faculty, Program,
            fields=['name', 'duration', 'tuition_fees', 'sort_order'],
            extra=1, can_delete=True
        )
        
        if self.request.POST:
            context['program_formset'] = ProgramFormSet(self.request.POST, instance=self.object)
        else:
            context['program_formset'] = ProgramFormSet(instance=self.object)
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        program_formset = context['program_formset']
        
        if program_formset.is_valid():
            self.object = form.save()
            program_formset.save()
            
            messages.success(self.request, 'تم تحديث الكلية بنجاح')
            return redirect('dashboard:faculties', university_id=self.object.university_id)
        else:
            return self.form_invalid(form)

class FacultyDeleteView(ContentAdminRequiredMixin, DeleteView):
    """Delete a faculty."""
    model = Faculty
    template_name = 'dashboard/faculties/delete_confirm.html'
    
    def get_success_url(self):
        return reverse_lazy('dashboard:faculties', kwargs={'university_id': self.object.university_id})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف الكلية بنجاح')
        return super().delete(request, *args, **kwargs)
```

**Lead Management Views:**

```python
import csv
from django.http import HttpResponse

class LeadListView(DashboardMixin, ListView):
    """List all leads with filtering."""
    model = Lead
    template_name = 'dashboard/leads/list.html'
    context_object_name = 'leads'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Lead.objects.all().order_by('-created_at')
        
        # Type filter
        lead_type = self.request.GET.get('type')
        if lead_type:
            queryset = queryset.filter(lead_type=lead_type)
        
        # Date range filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(email__icontains=search) | 
                Q(phone__icontains=search)
            )
        
        # Read status filter
        is_read = self.request.GET.get('is_read')
        if is_read:
            queryset = queryset.filter(is_read=(is_read == 'true'))
        
        return queryset

class LeadDetailView(DashboardMixin, DetailView):
    """View lead detail."""
    model = Lead
    template_name = 'dashboard/leads/detail.html'
    context_object_name = 'lead'
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Mark as read
        if not self.object.is_read:
            self.object.is_read = True
            self.object.save(update_fields=['is_read'])
        return response

class LeadExportView(DashboardMixin, View):
    """Export leads to CSV."""
    
    def get(self, request):
        # Get filtered queryset (same filters as list view)
        queryset = Lead.objects.all().order_by('-created_at')
        
        # Apply filters (same as LeadListView)
        # ...
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="leads.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'النوع', 'الاسم', 'البريد الإلكتروني', 'الهاتف', 
            'الرسالة', 'صفحة المصدر', 'التاريخ',
            'UTM Source', 'UTM Medium', 'UTM Campaign'
        ])
        
        for lead in queryset:
            writer.writerow([
                lead.get_lead_type_display(),
                lead.name,
                lead.email,
                lead.phone,
                lead.message,
                lead.source_page,
                lead.created_at.strftime('%Y-%m-%d %H:%M'),
                lead.utm_source,
                lead.utm_medium,
                lead.utm_campaign
            ])
        
        return response
```

### Dashboard UI Components

#### Sidebar Navigation

```html
<!-- templates/dashboard/components/sidebar.html -->
<aside class="dashboard-sidebar" dir="rtl">
    <div class="sidebar-header">
        <h2>لوحة التحكم</h2>
        <p>{{ user.username }}</p>
        <span class="user-role">{{ user.profile.get_role_display }}</span>
    </div>
    
    <nav class="sidebar-nav">
        <a href="{% url 'dashboard:home' %}" class="nav-item">
            <span class="icon">📊</span>
            <span>الرئيسية</span>
        </a>
        
        {% if user.profile.is_content_admin %}
        <div class="nav-section">
            <h3>المحتوى</h3>
            <a href="{% url 'dashboard:universities' %}" class="nav-item">
                <span class="icon">🎓</span>
                <span>الجامعات</span>
            </a>
            <a href="{% url 'dashboard:institutes' %}" class="nav-item">
                <span class="icon">🏫</span>
                <span>المعاهد</span>
            </a>
            <a href="{% url 'dashboard:majors' %}" class="nav-item">
                <span class="icon">📚</span>
                <span>التخصصات</span>
            </a>
            <a href="{% url 'dashboard:articles' %}" class="nav-item">
                <span class="icon">📝</span>
                <span>المقالات</span>
            </a>
            <a href="{% url 'dashboard:categories' %}" class="nav-item">
                <span class="icon">🏷️</span>
                <span>التصنيفات والوسوم</span>
            </a>
        </div>
        {% endif %}
        
        <div class="nav-section">
            <h3>الطلبات</h3>
            <a href="{% url 'dashboard:leads' %}" class="nav-item">
                <span class="icon">📧</span>
                <span>الطلبات</span>
                {% if unread_leads_count > 0 %}
                <span class="badge">{{ unread_leads_count }}</span>
                {% endif %}
            </a>
        </div>
        
        {% if user.profile.is_seo_admin %}
        <div class="nav-section">
            <h3>SEO</h3>
            <a href="{% url 'dashboard:redirects' %}" class="nav-item">
                <span class="icon">🔀</span>
                <span>التحويلات</span>
            </a>
        </div>
        {% endif %}
        
        {% if user.profile.is_super_admin %}
        <div class="nav-section">
            <h3>الإدارة</h3>
            <a href="{% url 'dashboard:users' %}" class="nav-item">
                <span class="icon">👥</span>
                <span>المستخدمون</span>
            </a>
        </div>
        {% endif %}
        
        <a href="{% url 'dashboard:logout' %}" class="nav-item logout">
            <span class="icon">🚪</span>
            <span>تسجيل الخروج</span>
        </a>
    </nav>
</aside>
```

#### Dashboard Statistics Cards

```html
<!-- templates/dashboard/home.html -->
<div class="stats-grid" dir="rtl">
    <div class="stat-card">
        <div class="stat-icon">📧</div>
        <div class="stat-content">
            <h3>إجمالي الطلبات</h3>
            <p class="stat-number">{{ total_leads }}</p>
        </div>
    </div>
    
    <div class="stat-card">
        <div class="stat-icon">📝</div>
        <div class="stat-content">
            <h3>طلبات التسجيل</h3>
            <p class="stat-number">{{ registration_leads }}</p>
        </div>
    </div>
    
    <div class="stat-card">
        <div class="stat-icon">💬</div>
        <div class="stat-content">
            <h3>طلبات التواصل</h3>
            <p class="stat-number">{{ contact_leads }}</p>
        </div>
    </div>
    
    <div class="stat-card">
        <div class="stat-icon">📅</div>
        <div class="stat-content">
            <h3>طلبات هذا الشهر</h3>
            <p class="stat-number">{{ current_month_leads }}</p>
        </div>
    </div>
</div>

<div class="content-stats" dir="rtl">
    <h2>إحصائيات المحتوى</h2>
    <div class="content-grid">
        <div class="content-stat">
            <span class="icon">🎓</span>
            <span class="label">الجامعات المنشورة</span>
            <span class="count">{{ published_universities }}</span>
        </div>
        <div class="content-stat">
            <span class="icon">🏫</span>
            <span class="label">المعاهد المنشورة</span>
            <span class="count">{{ published_institutes }}</span>
        </div>
        <div class="content-stat">
            <span class="icon">📚</span>
            <span class="label">التخصصات المنشورة</span>
            <span class="count">{{ published_majors }}</span>
        </div>
        <div class="content-stat">
            <span class="icon">📝</span>
            <span class="label">المقالات المنشورة</span>
            <span class="count">{{ published_articles }}</span>
        </div>
    </div>
</div>
```


---

---

## Structured Template Editors for Content Types

### Overview

Universities, Institutes, and Majors use **Structured Template Editors** instead of free-form HTML editors. This approach ensures:
- **Content Consistency**: All pages of the same type follow the same structure
- **SEO Optimization**: Predefined sections ensure proper heading hierarchy and content organization
- **Design Safety**: Limited formatting options prevent design breakage
- **Ease of Use**: Clear, organized forms are easier to fill than free-form editors
- **Maintainability**: Structured data is easier to update and migrate

**Key Principle:** Only Articles use the flexible Custom HTML Editor. Universities, Institutes, and Majors use structured forms with predefined sections.

### University Structured Template Editor

#### Form Sections

**1. Basic Information Section (معلومات أساسية)**
```python
# Django Form Fields
name = forms.CharField(max_length=200, label='اسم الجامعة')
slug = forms.SlugField(max_length=200, label='الرابط', allow_unicode=True)
logo = forms.ImageField(label='شعار الجامعة')
main_image = forms.ImageField(label='الصورة الرئيسية')
location = forms.CharField(max_length=200, label='الموقع')
video_url = forms.URLField(required=False, label='رابط الفيديو')
```

**2. Rich Text Sections (أقسام نصية)**
```python
# Simple Rich Text Fields (NOT full HTML editor)
description = forms.CharField(
    widget=SimpleRichTextWidget(),  # Bold, Italic, H2-H4, Lists, Links only
    label='وصف الجامعة'
)
admission_requirements = forms.CharField(
    widget=SimpleRichTextWidget(),
    label='شروط القبول'
)
registration_section = forms.CharField(
    widget=SimpleRichTextWidget(),
    required=False,
    label='قسم التسجيل'
)
```

**3. Structured Data Section (بيانات منظمة)**
- Faculties: Managed in separate page with inline Programs
- FAQ: Inline formset within University form

**4. Relationships Section (العلاقات)**
```python
related_majors = forms.ModelMultipleChoiceField(
    queryset=Major.objects.filter(publish_status='published'),
    required=False,
    label='التخصصات المرتبطة'
)
related_articles = forms.ModelMultipleChoiceField(
    queryset=Article.objects.filter(publish_status='published'),
    required=False,
    label='المقالات المرتبطة'
)
```

**5. SEO Section (SEO)**
- All SEO fields from SEOMixin

#### Template Structure

```html
<!-- Dashboard University Form Template -->
<form method="post" enctype="multipart/form-data" dir="rtl">
    {% csrf_token %}
    
    <!-- Basic Information -->
    <section class="form-section">
        <h2>معلومات أساسية</h2>
        {{ form.name }}
        {{ form.slug }}
        {{ form.logo }}
        {{ form.main_image }}
        {{ form.location }}
        {{ form.video_url }}
    </section>
    
    <!-- Rich Text Sections -->
    <section class="form-section">
        <h2>أقسام نصية</h2>
        {{ form.description }}  <!-- Simple Rich Text Widget -->
        {{ form.admission_requirements }}  <!-- Simple Rich Text Widget -->
        {{ form.registration_section }}  <!-- Simple Rich Text Widget -->
    </section>
    
    <!-- FAQ Inline Formset -->
    <section class="form-section">
        <h2>الأسئلة الشائعة</h2>
        {{ faq_formset.management_form }}
        <div id="faq-forms">
            {% for faq_form in faq_formset %}
                <div class="inline-form">
                    {{ faq_form.question }}
                    {{ faq_form.answer }}
                    {{ faq_form.sort_order }}
                    {{ faq_form.DELETE }}
                </div>
            {% endfor %}
        </div>
        <button type="button" class="add-faq">إضافة سؤال</button>
    </section>
    
    <!-- Faculties (Read-only list with links) -->
    <section class="form-section">
        <h2>الكليات والبرامج</h2>
        {% if object.pk %}
            <div class="faculties-list">
                {% for faculty in object.faculties.all %}
                    <div class="faculty-item">
                        <span>{{ faculty.name }}</span>
                        <span>({{ faculty.programs.count }} برنامج)</span>
                        <a href="{% url 'dashboard:faculty-edit' faculty.pk %}">تعديل</a>
                        <a href="{% url 'dashboard:faculty-delete' faculty.pk %}">حذف</a>
                    </div>
                {% endfor %}
            </div>
            <a href="{% url 'dashboard:faculty-create' object.pk %}" class="btn">إضافة كلية</a>
        {% else %}
            <p>احفظ الجامعة أولاً لإضافة الكليات</p>
        {% endif %}
    </section>
    
    <!-- Relationships -->
    <section class="form-section">
        <h2>العلاقات</h2>
        {{ form.related_majors }}
        {{ form.related_articles }}
    </section>
    
    <!-- SEO -->
    <section class="form-section collapsible">
        <h2>SEO</h2>
        {{ form.meta_title }}
        {{ form.meta_description }}
        {{ form.focus_keyword }}
        <!-- ... other SEO fields -->
    </section>
    
    <!-- Publishing -->
    <section class="form-section">
        <h2>النشر</h2>
        {{ form.publish_status }}
    </section>
    
    <button type="submit" class="btn-primary">حفظ</button>
</form>
```

### Institute Structured Template Editor

#### Form Sections

**1. Basic Information**
- name, slug, main_image

**2. Rich Text Sections**
- description (Simple Rich Text)
- registration_requirements (Simple Rich Text)
- registration_section (Simple Rich Text)

**3. Structured Data**
- Courses: Inline formset

**4. Relationships**
- related_articles

**5. SEO**
- All SEO fields

### Major Structured Template Editor

#### Form Sections

**1. Basic Information**
- name, slug, main_image

**2. Rich Text Sections**
- description (Simple Rich Text)
- why_study_section (Simple Rich Text)
- how_to_apply_section (Simple Rich Text)

**3. Quick Information Fields**
- study_duration, tuition_fees, study_language, practical_training, career_opportunities

**4. Structured Data (Dynamic Tables)**
- Subjects Table: Inline formset
- Salary Table: Inline formset
- Countries Table: Inline formset

**5. University Relationships**
- best_universities (Many-to-Many)
- cheap_universities (Many-to-Many)

**6. Relationships**
- related_articles

**7. SEO**
- All SEO fields

### Simple Rich Text Widget

**Purpose:** Provide basic formatting for text sections WITHOUT full HTML editor complexity.

**Allowed Formatting:**
- Bold (`<strong>`)
- Italic (`<em>`)
- Headings H2, H3, H4 (`<h2>`, `<h3>`, `<h4>`)
- Unordered Lists (`<ul>`, `<li>`)
- Ordered Lists (`<ol>`, `<li>`)
- Links (`<a href="">`)
- Paragraphs (`<p>`)

**NOT Allowed:**
- Images
- Videos
- Tables
- Complex HTML blocks
- Custom CSS
- JavaScript

**Implementation:**

```python
# apps/core/widgets.py

from django import forms
from django.utils.safestring import mark_safe
import bleach

class SimpleRichTextWidget(forms.Textarea):
    """Simple rich text widget with basic formatting toolbar."""
    
    template_name = 'widgets/simple_rich_text.html'
    
    class Media:
        css = {
            'all': ('css/simple_rich_text.css',)
        }
        js = ('js/simple_rich_text.js',)
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'simple-rich-text',
            'rows': 10,
            'dir': 'rtl'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

# Sanitization for Simple Rich Text
SIMPLE_ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'a']
SIMPLE_ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}

def sanitize_simple_rich_text(html_content):
    """Sanitize simple rich text content."""
    if not html_content:
        return ''
    
    return bleach.clean(
        html_content,
        tags=SIMPLE_ALLOWED_TAGS,
        attributes=SIMPLE_ALLOWED_ATTRIBUTES,
        strip=True
    )
```

```javascript
// static/js/simple_rich_text.js

class SimpleRichTextEditor {
    constructor(textarea) {
        this.textarea = textarea;
        this.createToolbar();
    }
    
    createToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'simple-toolbar';
        toolbar.innerHTML = `
            <button type="button" data-cmd="bold" title="غامق"><strong>B</strong></button>
            <button type="button" data-cmd="italic" title="مائل"><em>I</em></button>
            <button type="button" data-cmd="h2" title="عنوان 2">H2</button>
            <button type="button" data-cmd="h3" title="عنوان 3">H3</button>
            <button type="button" data-cmd="h4" title="عنوان 4">H4</button>
            <button type="button" data-cmd="ul" title="قائمة نقطية">• List</button>
            <button type="button" data-cmd="ol" title="قائمة مرقمة">1. List</button>
            <button type="button" data-cmd="link" title="رابط">🔗</button>
        `;
        
        this.textarea.parentNode.insertBefore(toolbar, this.textarea);
        
        toolbar.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.executeCommand(btn.dataset.cmd);
            });
        });
    }
    
    executeCommand(cmd) {
        const start = this.textarea.selectionStart;
        const end = this.textarea.selectionEnd;
        const selected = this.textarea.value.substring(start, end);
        const before = this.textarea.value.substring(0, start);
        const after = this.textarea.value.substring(end);
        
        let replacement = '';
        
        switch(cmd) {
            case 'bold':
                replacement = `<strong>${selected}</strong>`;
                break;
            case 'italic':
                replacement = `<em>${selected}</em>`;
                break;
            case 'h2':
                replacement = `<h2>${selected}</h2>`;
                break;
            case 'h3':
                replacement = `<h3>${selected}</h3>`;
                break;
            case 'h4':
                replacement = `<h4>${selected}</h4>`;
                break;
            case 'ul':
                replacement = `<ul>\n  <li>${selected}</li>\n</ul>`;
                break;
            case 'ol':
                replacement = `<ol>\n  <li>${selected}</li>\n</ol>`;
                break;
            case 'link':
                const url = prompt('أدخل الرابط:', 'https://');
                if (url) {
                    replacement = `<a href="${url}">${selected || 'نص الرابط'}</a>`;
                }
                break;
        }
        
        if (replacement) {
            this.textarea.value = before + replacement + after;
            this.textarea.focus();
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.simple-rich-text').forEach(textarea => {
        new SimpleRichTextEditor(textarea);
    });
});
```

---

## Custom HTML Editor Design (For Articles Only)

### Overview

The Custom HTML Editor is a **custom-built HTML editor** integrated into the Custom Dashboard **exclusively for Article and News content editing**. It is NOT CKEditor or TinyMCE - it's built specifically for the Science Gates platform.

**IMPORTANT:** This editor is used **ONLY for Articles**. Universities, Institutes, and Majors use Structured Template Editors (see previous section).

**V1 Scope (Simplified):**
- Simple textarea-based editor with formatting toolbar
- Basic formatting: Bold, Italic, Headings (H2-H4), Lists (UL/OL), Links, Images
- Arabic RTL text entry and editing
- Safe HTML sanitization to prevent XSS attacks
- Image upload with alt text
- NO block-based editor in V1
- NO preview mode in V1
- Can be upgraded to block-based editor in future versions

**Key Features:**
- Toolbar with essential formatting buttons
- Arabic RTL text entry and editing
- Safe HTML sanitization to prevent XSS attacks
- Image upload with alt text
- Link insertion (internal and external)
- Simple and intuitive interface
- **Used exclusively for Articles** - provides maximum flexibility for news and blog content

### Editor Architecture

#### Django Form Widget

```python
# apps/html_editor/widgets.py

from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
import json

class CustomHTMLEditorWidget(forms.Textarea):
    """Custom HTML Editor widget for Django forms - FOR ARTICLES ONLY."""
    
    template_name = 'html_editor/widget.html'
    
    class Media:
        css = {
            'all': ('html_editor/css/html_editor.css',)
        }
        js = ('html_editor/js/html_editor.js',)
    
    def __init__(self, attrs=None):
        default_attrs = {'class': 'custom-html-editor'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the editor widget."""
        context = {
            'name': name,
            'value': value or '',
            'attrs': attrs,
            'widget_id': attrs.get('id', f'id_{name}')
        }
        return mark_safe(render_to_string(self.template_name, context))
```

#### HTML Sanitizer

```python
# apps/html_editor/sanitizer.py

import bleach
from bleach.css_sanitizer import CSSSanitizer

# Allowed HTML tags (V1 - simplified)
ALLOWED_TAGS = [
    # Text formatting
    'p', 'br', 'strong', 'em', 'span',
    # Headings
    'h2', 'h3', 'h4',
    # Lists
    'ul', 'ol', 'li',
    # Links
    'a',
    # Images
    'img',
    # Blocks
    'div',
]

# Allowed attributes
ALLOWED_ATTRIBUTES = {
    '*': ['class', 'dir'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
}

# Allowed CSS properties (minimal)
ALLOWED_STYLES = [
    'text-align', 'direction',
]

css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_STYLES)

def sanitize_html(html_content):
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Args:
        html_content: Raw HTML string
    
    Returns:
        Sanitized HTML string safe for rendering
    """
    if not html_content:
        return ''
    
    # Clean HTML
    clean_html = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        strip=True
    )
    
    # Add rel="noopener noreferrer" to external links
    clean_html = bleach.linkify(
        clean_html,
        callbacks=[add_noopener_callback]
    )
    
    return clean_html

def add_noopener_callback(attrs, new=False):
    """Add rel="noopener noreferrer" to external links."""
    href = attrs.get((None, 'href'), '')
    if href.startswith('http') and not href.startswith(('http://sciencegates.com', 'https://sciencegates.com')):
        rel = attrs.get((None, 'rel'), '')
        if rel:
            attrs[(None, 'rel')] = f'{rel} noopener noreferrer'
        else:
            attrs[(None, 'rel')] = 'noopener noreferrer'
    return attrs
```

#### Editor Toolbar (V1 - Simplified)

```javascript
// apps/html_editor/static/js/html_editor.js

class SimpleHTMLEditor {
    constructor(textarea) {
        this.textarea = textarea;
        this.toolbar = null;
        this.init();
    }
    
    init() {
        this.createToolbar();
        this.attachEventListeners();
    }
    
    createToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'html-editor-toolbar';
        toolbar.innerHTML = `
            <button type="button" data-command="bold" title="غامق">
                <strong>B</strong>
            </button>
            <button type="button" data-command="italic" title="مائل">
                <em>I</em>
            </button>
            <button type="button" data-command="heading2" title="عنوان 2">
                H2
            </button>
            <button type="button" data-command="heading3" title="عنوان 3">
                H3
            </button>
            <button type="button" data-command="heading4" title="عنوان 4">
                H4
            </button>
            <button type="button" data-command="ul" title="قائمة نقطية">
                • List
            </button>
            <button type="button" data-command="ol" title="قائمة مرقمة">
                1. List
            </button>
            <button type="button" data-command="link" title="رابط">
                🔗 Link
            </button>
            <button type="button" data-command="image" title="صورة">
                🖼️ Image
            </button>
        `;
        
        this.textarea.parentNode.insertBefore(toolbar, this.textarea);
        this.toolbar = toolbar;
    }
    
    attachEventListeners() {
        this.toolbar.querySelectorAll('button').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const command = button.dataset.command;
                this.executeCommand(command);
            });
        });
    }
    
    executeCommand(command) {
        const textarea = this.textarea;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = textarea.value.substring(start, end);
        const beforeText = textarea.value.substring(0, start);
        const afterText = textarea.value.substring(end);
        
        let newText = '';
        let cursorOffset = 0;
        
        switch(command) {
            case 'bold':
                newText = `<strong>${selectedText}</strong>`;
                cursorOffset = 8; // length of <strong>
                break;
            case 'italic':
                newText = `<em>${selectedText}</em>`;
                cursorOffset = 4; // length of <em>
                break;
            case 'heading2':
                newText = `<h2>${selectedText}</h2>`;
                cursorOffset = 4; // length of <h2>
                break;
            case 'heading3':
                newText = `<h3>${selectedText}</h3>`;
                cursorOffset = 4;
                break;
            case 'heading4':
                newText = `<h4>${selectedText}</h4>`;
                cursorOffset = 4;
                break;
            case 'ul':
                newText = `<ul>\n  <li>${selectedText}</li>\n</ul>`;
                cursorOffset = 10; // length of <ul>\n  <li>
                break;
            case 'ol':
                newText = `<ol>\n  <li>${selectedText}</li>\n</ol>`;
                cursorOffset = 10;
                break;
            case 'link':
                const url = prompt('أدخل الرابط:', 'https://');
                if (url) {
                    newText = `<a href="${url}">${selectedText || 'نص الرابط'}</a>`;
                    cursorOffset = 9 + url.length; // length of <a href="url">
                }
                break;
            case 'image':
                this.openImageUpload();
                return;
        }
        
        if (newText) {
            textarea.value = beforeText + newText + afterText;
            textarea.selectionStart = start + cursorOffset;
            textarea.selectionEnd = start + cursorOffset + selectedText.length;
            textarea.focus();
        }
    }
    
    openImageUpload() {
        // Create image upload modal
        const modal = document.createElement('div');
        modal.className = 'html-editor-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>إضافة صورة</h3>
                <input type="file" accept="image/*" id="imageUpload">
                <input type="text" placeholder="النص البديل (Alt Text)" id="imageAlt">
                <button type="button" id="insertImage">إدراج</button>
                <button type="button" id="cancelImage">إلغاء</button>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Handle image insertion
        modal.querySelector('#insertImage').addEventListener('click', () => {
            const file = modal.querySelector('#imageUpload').files[0];
            const alt = modal.querySelector('#imageAlt').value;
            
            if (file) {
                // Upload image via AJAX and insert
                this.uploadImage(file, alt);
            }
            document.body.removeChild(modal);
        });
        
        modal.querySelector('#cancelImage').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
    }
    
    uploadImage(file, alt) {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('alt', alt);
        
        fetch('/dashboard/upload-image/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const imgTag = `<img src="${data.url}" alt="${alt}">`;
                this.insertAtCursor(imgTag);
            }
        });
    }
    
    insertAtCursor(text) {
        const textarea = this.textarea;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const beforeText = textarea.value.substring(0, start);
        const afterText = textarea.value.substring(end);
        
        textarea.value = beforeText + text + afterText;
        textarea.selectionStart = start + text.length;
        textarea.selectionEnd = start + text.length;
        textarea.focus();
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

// Initialize editor on page load
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.custom-html-editor').forEach(textarea => {
        new SimpleHTMLEditor(textarea);
    });
});
```

**Note:** This is a simplified V1 implementation. Future versions can upgrade to a block-based editor with drag-and-drop, preview mode, and more advanced features.

---

## SEO System Design

### SEO Components

#### XML Sitemap Generation

```python
# apps/seo/sitemaps.py

from django.contrib.sitemaps import Sitemap
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article

class UniversitySitemap(Sitemap):
    """Sitemap for universities."""
    changefreq = 'weekly'
    priority = 0.9
    
    def items(self):
        return University.objects.filter(
            publish_status='published',
            sitemap_include=True
        )
    
    def lastmod(self, obj):
        return obj.updated_at

class InstituteSitemap(Sitemap):
    """Sitemap for institutes."""
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Institute.objects.filter(
            publish_status='published',
            sitemap_include=True
        )
    
    def lastmod(self, obj):
        return obj.updated_at

class MajorSitemap(Sitemap):
    """Sitemap for majors."""
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Major.objects.filter(
            publish_status='published',
            sitemap_include=True
        )
    
    def lastmod(self, obj):
        return obj.updated_at

class ArticleSitemap(Sitemap):
    """Sitemap for articles."""
    changefreq = 'daily'
    priority = 0.7
    
    def items(self):
        return Article.objects.filter(
            publish_status='published',
            sitemap_include=True
        ).order_by('-publish_date')
    
    def lastmod(self, obj):
        return obj.updated_at

# Register sitemaps in urls.py
sitemaps = {
    'universities': UniversitySitemap,
    'institutes': InstituteSitemap,
    'majors': MajorSitemap,
    'articles': ArticleSitemap,
}
```

#### Robots.txt

```python
# apps/seo/views.py

from django.http import HttpResponse
from django.views import View

class RobotsTxtView(View):
    """Generate robots.txt dynamically."""
    
    def get(self, request):
        lines = [
            'User-agent: *',
            'Allow: /',
            '',
            '# Disallow admin areas',
            'Disallow: /dashboard/',
            'Disallow: /admin/',
            '',
            '# Sitemap',
            f'Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml',
        ]
        return HttpResponse('\n'.join(lines), content_type='text/plain')
```

#### SEO Template Tags

```python
# apps/seo/templatetags/seo_tags.py

from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.inclusion_tag('seo/meta_tags.html')
def render_seo_meta(obj):
    """Render SEO meta tags for a content object."""
    return {
        'meta_title': obj.get_meta_title(),
        'meta_description': obj.get_meta_description(),
        'canonical_url': obj.canonical_url or obj.get_absolute_url(),
        'robots_content': obj.get_robots_content(),
        'og_title': obj.get_og_title(),
        'og_description': obj.get_og_description(),
        'og_image': obj.get_og_image_url(),
        'og_url': obj.get_absolute_url(),
    }

@register.simple_tag
def render_breadcrumbs(items):
    """Render breadcrumb navigation with schema markup."""
    breadcrumb_list = {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': []
    }
    
    for i, item in enumerate(items, 1):
        breadcrumb_list['itemListElement'].append({
            '@type': 'ListItem',
            'position': i,
            'name': item['name'],
            'item': item['url']
        })
    
    html = '<nav class="breadcrumbs" dir="rtl">'
    html += '<ol>'
    for item in items:
        html += f'<li><a href="{item["url"]}">{item["name"]}</a></li>'
    html += '</ol>'
    html += f'<script type="application/ld+json">{json.dumps(breadcrumb_list, ensure_ascii=False)}</script>'
    html += '</nav>'
    
    return mark_safe(html)

@register.simple_tag
def render_organization_schema():
    """Render Organization schema markup."""
    schema = {
        '@context': 'https://schema.org',
        '@type': 'Organization',
        'name': 'شركة بوابات العلوم للدراسة في ماليزيا',
        'url': 'https://sciencegates.com',
        'logo': 'https://sciencegates.com/static/images/logo.png',
        'sameAs': [
            # Social media profiles
        ]
    }
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>')

@register.simple_tag
def render_article_schema(article):
    """Render Article schema markup."""
    schema = {
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': article.title,
        'image': article.featured_image.url if article.featured_image else None,
        'datePublished': article.publish_date.isoformat(),
        'dateModified': article.updated_at.isoformat(),
        'author': {
            '@type': 'Person',
            'name': article.author.get_full_name() or article.author.username
        },
        'publisher': {
            '@type': 'Organization',
            'name': 'شركة بوابات العلوم للدراسة في ماليزيا',
            'logo': {
                '@type': 'ImageObject',
                'url': 'https://sciencegates.com/static/images/logo.png'
            }
        },
        'description': article.get_meta_description()
    }
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>')

@register.simple_tag
def render_faq_schema(faqs):
    """Render FAQ schema markup."""
    schema = {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': []
    }
    
    for faq in faqs:
        schema['mainEntity'].append({
            '@type': 'Question',
            'name': faq.question,
            'acceptedAnswer': {
                '@type': 'Answer',
                'text': faq.answer
            }
        })
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>')
```

#### SEO Meta Tags Template

```html
<!-- templates/seo/meta_tags.html -->
<title>{{ meta_title }}</title>
<meta name="description" content="{{ meta_description }}">
<meta name="robots" content="{{ robots_content }}">
<link rel="canonical" href="{{ canonical_url }}">

<!-- Open Graph -->
<meta property="og:title" content="{{ og_title }}">
<meta property="og:description" content="{{ og_description }}">
<meta property="og:url" content="{{ og_url }}">
<meta property="og:type" content="website">
{% if og_image %}
<meta property="og:image" content="{{ og_image }}">
{% endif %}
<meta property="og:locale" content="ar_AR">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ og_title }}">
<meta name="twitter:description" content="{{ og_description }}">
{% if og_image %}
<meta name="twitter:image" content="{{ og_image }}">
{% endif %}
```

### Redirect Middleware

```python
# apps/redirects/middleware.py

from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from apps.redirects.models import Redirect

class RedirectMiddleware(MiddlewareMixin):
    """Middleware to handle 301 redirects."""
    
    def process_request(self, request):
        # Get current path
        path = request.path
        
        # Check if redirect exists
        try:
            redirect_obj = Redirect.objects.get(
                old_url=path,
                is_active=True
            )
            
            # Increment hit count
            redirect_obj.increment_hit_count()
            
            # Return 301 redirect
            return redirect(redirect_obj.new_url, permanent=True)
        
        except Redirect.DoesNotExist:
            # No redirect found, continue normally
            return None
```

---

## Security Implementation

### Security Measures

#### 1. CSRF Protection

```python
# config/settings/base.py

# CSRF settings
CSRF_COOKIE_SECURE = True  # Production only
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = False
```

All forms include CSRF token:

```html
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

#### 2. XSS Protection

**HTML Sanitization:**

```python
# apps/html_editor/sanitizer.py
# (Already defined above)

# Usage in Article model save
def save(self, *args, **kwargs):
    # Sanitize content before saving
    from apps.html_editor.sanitizer import sanitize_html
    self.content = sanitize_html(self.content)
    super().save(*args, **kwargs)
```

**Template Auto-escaping:**

Django templates auto-escape by default. Use `|safe` filter only for sanitized content:

```html
<!-- Safe: sanitized content -->
{{ article.content|safe }}

<!-- Unsafe: user input -->
{{ user_input }}  <!-- Auto-escaped -->
```

#### 3. SQL Injection Protection

Use Django ORM parameterized queries:

```python
# Safe: parameterized query
universities = University.objects.filter(name__icontains=search_query)

# Unsafe: raw SQL (avoid)
# cursor.execute(f"SELECT * FROM universities WHERE name LIKE '%{search_query}%'")
```

#### 4. Password Security

```python
# config/settings/base.py

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]
```

#### 5. Secure Cookies

```python
# config/settings/production.py

# Secure cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
```

#### 6. Rate Limiting for Lead Forms

```python
# apps/leads/views.py

from django.core.cache import cache
from django.http import HttpResponseForbidden

class LeadFormView(View):
    """Lead form submission with rate limiting."""
    
    def post(self, request):
        # Rate limiting: max 3 submissions per hour per IP
        ip_address = self.get_client_ip(request)
        cache_key = f'lead_form_{ip_address}'
        
        submission_count = cache.get(cache_key, 0)
        if submission_count >= 3:
            return HttpResponseForbidden('تم تجاوز الحد الأقصى للطلبات. يرجى المحاولة لاحقاً.')
        
        # Process form
        # ...
        
        # Increment counter
        cache.set(cache_key, submission_count + 1, 3600)  # 1 hour
        
        return redirect('thank_you')
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

#### 7. Honeypot Anti-Spam

```python
# apps/leads/forms.py

from django import forms

class LeadForm(forms.ModelForm):
    """Lead form with honeypot field."""
    
    # Honeypot field (hidden from users, bots will fill it)
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'display:none',
            'tabindex': '-1',
            'autocomplete': 'off'
        })
    )
    
    class Meta:
        model = Lead
        fields = ['name', 'email', 'phone', 'message']
    
    def clean_website(self):
        """Reject if honeypot is filled."""
        website = self.cleaned_data.get('website')
        if website:
            raise forms.ValidationError('Spam detected')
        return website
```

#### 8. Security Headers

```python
# config/settings/production.py

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

#### 9. Debug Mode

```python
# config/settings/production.py

# CRITICAL: Debug must be False in production
DEBUG = False
ALLOWED_HOSTS = ['sciencegates.com', 'www.sciencegates.com']
```

---

## Performance Optimization

### Performance Strategies

#### 1. Database Query Optimization

```python
# Use select_related for ForeignKey
universities = University.objects.select_related('category').filter(publish_status='published')

# Use prefetch_related for ManyToMany and reverse ForeignKey
university = University.objects.prefetch_related(
    'faculties__programs',
    'faqs',
    'related_majors',
    'related_articles'
).get(slug=slug)

# Avoid N+1 queries
# Bad:
for university in universities:
    print(university.faculties.count())  # N+1 query

# Good:
universities = University.objects.annotate(
    faculty_count=Count('faculties')
)
for university in universities:
    print(university.faculty_count)  # Single query
```

#### 2. Pagination

```python
# apps/universities/views.py

from django.core.paginator import Paginator

class UniversityListView(ListView):
    """List universities with pagination."""
    model = University
    paginate_by = 20  # 20 items per page
    
    def get_queryset(self):
        return University.objects.filter(
            publish_status='published'
        ).select_related().order_by('name')
```

#### 3. Image Optimization

```python
# apps/core/utils.py

from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

def optimize_image(image_field, max_width=1920, max_height=1080, quality=85):
    """
    Optimize uploaded image: resize and compress.
    
    Args:
        image_field: ImageField instance
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        quality: JPEG quality (1-100)
    
    Returns:
        Optimized image file
    """
    img = Image.open(image_field)
    
    # Convert RGBA to RGB if needed
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    # Resize if needed
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    
    # Save to BytesIO
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    # Create InMemoryUploadedFile
    return InMemoryUploadedFile(
        output,
        'ImageField',
        f"{image_field.name.split('.')[0]}.jpg",
        'image/jpeg',
        sys.getsizeof(output),
        None
    )

# Usage in model save
def save(self, *args, **kwargs):
    if self.main_image:
        self.main_image = optimize_image(self.main_image)
    super().save(*args, **kwargs)
```

#### 4. Lazy Loading Images

```html
<!-- templates/components/image.html -->
<img 
    src="{{ image.url }}" 
    alt="{{ alt_text }}"
    loading="lazy"
    width="{{ width }}"
    height="{{ height }}"
>
```

#### 5. Static File Optimization

```python
# config/settings/production.py

# Static files
STATIC_ROOT = '/home/username/public_html/static/'
STATIC_URL = '/static/'

# Whitenoise for serving static files
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # After SecurityMiddleware
    # ... other middleware
]

# Whitenoise compression and caching
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

#### 6. File-Based Caching

```python
# config/settings/base.py

# File-based cache (baseline)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Optional: Redis cache if available
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#     }
# }
```

#### 7. Template Fragment Caching

```html
{% load cache %}

<!-- Cache university list for 15 minutes -->
{% cache 900 university_list %}
    {% for university in universities %}
        <!-- university card -->
    {% endfor %}
{% endcache %}
```

#### 8. CSS/JS Minification

```python
# config/settings/production.py

# Django Compressor (optional)
INSTALLED_APPS += ['compressor']

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter',
]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
]
```


---

## Arabic RTL Support

### RTL Implementation Strategy

#### 1. Tailwind CSS RTL Configuration

```javascript
// tailwind.config.js

module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      // Custom RTL-aware spacing, etc.
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
  // RTL support
  corePlugins: {
    // Enable RTL utilities
  },
}
```

#### 2. Base Template RTL Setup

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    {% include 'includes/seo_meta.html' %}
    
    <!-- Tailwind CSS (RTL configured) -->
    <link rel="stylesheet" href="{% static 'css/tailwind.css' %}">
    <link rel="stylesheet" href="{% static 'css/custom.css' %}">
    
    {% block extra_css %}{% endblock %}
</head>
<body dir="rtl" class="rtl">
    {% include 'components/header.html' %}
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    {% include 'components/footer.html' %}
    
    <!-- Alpine.js -->
    <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    
    <!-- Custom JS -->
    <script src="{% static 'js/main.js' %}"></script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### 3. RTL-Aware CSS

```css
/* static/css/custom.css */

/* RTL-specific styles */
[dir="rtl"] {
    text-align: right;
}

/* RTL table alignment */
[dir="rtl"] table {
    direction: rtl;
}

[dir="rtl"] th,
[dir="rtl"] td {
    text-align: right;
}

/* RTL form alignment */
[dir="rtl"] input,
[dir="rtl"] textarea,
[dir="rtl"] select {
    text-align: right;
}

/* RTL navigation */
[dir="rtl"] .breadcrumbs li::after {
    content: "←";
    margin: 0 0.5rem;
}

/* RTL accordion icons */
[dir="rtl"] .accordion-icon {
    transform: rotate(180deg);
}

[dir="rtl"] .accordion-icon.open {
    transform: rotate(90deg);
}

/* RTL pagination */
[dir="rtl"] .pagination {
    direction: rtl;
}

/* RTL mobile menu */
[dir="rtl"] .mobile-menu {
    right: auto;
    left: 0;
}
```

#### 4. RTL-Aware Components

**Accordion (Alpine.js):**

```html
<!-- templates/components/accordion.html -->
<div x-data="{ open: false }" class="accordion-item" dir="rtl">
    <button 
        @click="open = !open"
        class="accordion-header"
        :aria-expanded="open"
    >
        <span>{{ question }}</span>
        <svg 
            class="accordion-icon"
            :class="{ 'open': open }"
            xmlns="http://www.w3.org/2000/svg" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
        >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
    </button>
    <div 
        x-show="open"
        x-transition
        class="accordion-content"
    >
        <p>{{ answer }}</p>
    </div>
</div>
```

**Mobile Navigation (Alpine.js):**

```html
<!-- templates/components/header.html -->
<header dir="rtl" x-data="{ mobileMenuOpen: false }">
    <nav class="navbar">
        <div class="navbar-container">
            <!-- Logo -->
            <a href="{% url 'home' %}" class="navbar-logo">
                <img src="{% static 'images/logo.svg' %}" alt="شركة بوابات العلوم">
            </a>
            
            <!-- Desktop Menu -->
            <ul class="navbar-menu hidden md:flex">
                <li><a href="{% url 'universities:list' %}">الجامعات</a></li>
                <li><a href="{% url 'institutes:list' %}">المعاهد</a></li>
                <li><a href="{% url 'majors:list' %}">التخصصات</a></li>
                <li><a href="{% url 'articles:list' %}">المقالات</a></li>
                <li><a href="{% url 'search:search' %}">البحث</a></li>
            </ul>
            
            <!-- Mobile Menu Button -->
            <button 
                @click="mobileMenuOpen = !mobileMenuOpen"
                class="mobile-menu-button md:hidden"
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
            </button>
        </div>
        
        <!-- Mobile Menu -->
        <div 
            x-show="mobileMenuOpen"
            x-transition
            class="mobile-menu md:hidden"
        >
            <ul>
                <li><a href="{% url 'universities:list' %}">الجامعات</a></li>
                <li><a href="{% url 'institutes:list' %}">المعاهد</a></li>
                <li><a href="{% url 'majors:list' %}">التخصصات</a></li>
                <li><a href="{% url 'articles:list' %}">المقالات</a></li>
                <li><a href="{% url 'search:search' %}">البحث</a></li>
            </ul>
        </div>
    </nav>
</header>
```

**Responsive Tables:**

```html
<!-- templates/components/responsive_table.html -->
<div class="table-container" dir="rtl">
    <table class="responsive-table">
        <thead>
            <tr>
                <th>{{ header1 }}</th>
                <th>{{ header2 }}</th>
                <th>{{ header3 }}</th>
            </tr>
        </thead>
        <tbody>
            {% for row in rows %}
            <tr>
                <td data-label="{{ header1 }}">{{ row.col1 }}</td>
                <td data-label="{{ header2 }}">{{ row.col2 }}</td>
                <td data-label="{{ header3 }}">{{ row.col3 }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<style>
/* Mobile: Stack table cells */
@media (max-width: 768px) {
    .responsive-table thead {
        display: none;
    }
    
    .responsive-table tr {
        display: block;
        margin-bottom: 1rem;
        border: 1px solid #ddd;
    }
    
    .responsive-table td {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem;
        border-bottom: 1px solid #eee;
    }
    
    .responsive-table td::before {
        content: attr(data-label);
        font-weight: bold;
        margin-left: 1rem;
    }
}
</style>
```

#### 5. Future Multilingual Architecture

```python
# config/settings/base.py

# Language settings (prepared for future expansion)
LANGUAGE_CODE = 'ar'
LANGUAGES = [
    ('ar', 'العربية'),
    # Future: ('en', 'English'),
]

USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Middleware (ready for i18n)
MIDDLEWARE = [
    # ...
    # Future: 'django.middleware.locale.LocaleMiddleware',
    # ...
]
```

---

## cPanel Deployment Configuration

### Deployment Files

#### passenger_wsgi.py

```python
# passenger_wsgi.py

import sys
import os

# Add project directory to path
INTERP = "/home/username/virtualenv/science_gates/bin/python3"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, '/home/username/science_gates')
sys.path.insert(0, '/home/username/science_gates/config')

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

#### .htaccess

```apache
# .htaccess

# Passenger configuration
PassengerAppRoot /home/username/science_gates
PassengerBaseURI /
PassengerPython /home/username/virtualenv/science_gates/bin/python3

# Force HTTPS
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Static files
Alias /static /home/username/public_html/static
Alias /media /home/username/public_html/media

<Directory /home/username/public_html/static>
    Require all granted
</Directory>

<Directory /home/username/public_html/media>
    Require all granted
</Directory>
```

#### requirements.txt

```
Django==4.2.7
mysqlclient==2.2.0
Pillow==10.1.0
bleach==6.1.0
python-dotenv==1.0.0
whitenoise==6.6.0
gunicorn==21.2.0
```

#### .env.example

```bash
# .env.example

# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=sciencegates.com,www.sciencegates.com

# Database
DB_NAME=science_gates_db
DB_USER=science_gates_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=3306

# Email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@sciencegates.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@sciencegates.com
ADMIN_EMAIL=admin@sciencegates.com

# Media and Static
MEDIA_ROOT=/home/username/public_html/media
STATIC_ROOT=/home/username/public_html/static

# Cache (optional Redis)
# REDIS_URL=redis://127.0.0.1:6379/1
```

### Production Settings

```python
# config/settings/production.py

from .base import *
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Security
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# Static and Media
STATIC_ROOT = os.getenv('STATIC_ROOT')
MEDIA_ROOT = os.getenv('MEDIA_ROOT')
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/home/username/logs/django_errors.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

### Deployment Checklist

```markdown
# Deployment Checklist

## Pre-Deployment
- [ ] Set DEBUG=False in production settings
- [ ] Configure ALLOWED_HOSTS
- [ ] Set strong SECRET_KEY
- [ ] Configure database credentials
- [ ] Configure email settings
- [ ] Test all forms with CSRF protection
- [ ] Test file uploads
- [ ] Run security checks: `python manage.py check --deploy`

## cPanel Setup
- [ ] Create MySQL database and user
- [ ] Create Python virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Configure passenger_wsgi.py with correct paths
- [ ] Set up .htaccess for Passenger
- [ ] Configure static and media directories

## Django Setup
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Test admin login
- [ ] Test dashboard login

## SSL Configuration
- [ ] Install SSL certificate via cPanel
- [ ] Force HTTPS in .htaccess
- [ ] Verify HTTPS redirect works
- [ ] Test secure cookies

## Post-Deployment
- [ ] Test all public pages
- [ ] Test Custom Dashboard
- [ ] Test lead form submission
- [ ] Test email notifications
- [ ] Test image uploads
- [ ] Test Custom HTML Editor
- [ ] Verify sitemap.xml
- [ ] Verify robots.txt
- [ ] Test redirects
- [ ] Check error logs

## Backup Setup
- [ ] Configure automated database backups
- [ ] Configure automated media backups
- [ ] Test backup restoration
- [ ] Document backup procedures
```


---

## Incremental Development Phases

### Overview

The Science Gates platform will be developed across **8 sequential phases**, each building on the previous phase. Each phase has clear deliverables and acceptance criteria.

---

### Phase 1: Foundation & Project Setup

**Duration:** 1-2 weeks

**Objective:** Establish Django project structure, database connection, Custom Dashboard foundation, and cPanel-compatible configuration.

#### Deliverables

1. **Django Project Structure**
   - Create Django project with `config/` directory
   - Set up `apps/` directory structure
   - Configure settings split (base, local, production)
   - Create `passenger_wsgi.py` for cPanel
   - Create `.htaccess` for Passenger configuration

2. **Database Configuration**
   - Configure MySQL/MariaDB connection
   - Test database connectivity
   - Create initial migrations

3. **Core App**
   - Create `apps/core/` app
   - Implement `TimestampedModel` abstract base
   - Implement `PublishableModel` abstract base
   - Implement `SEOMixin` abstract base
   - Create homepage view and template

4. **Custom Dashboard Foundation**
   - Create `apps/dashboard/` app
   - Implement authentication (login, logout)
   - Create dashboard base template with RTL support
   - Implement role-based access mixins
   - Create dashboard home view with placeholder statistics

5. **User Management**
   - Create `UserProfile` model with role field
   - Implement user creation signal for profile
   - Create user management views (Super Admin only)

6. **Static Assets Setup**
   - Configure Tailwind CSS with RTL support
   - Set up Alpine.js
   - Create base templates (public and dashboard)
   - Configure static files handling

7. **Environment Configuration**
   - Create `.env.example` file
   - Configure `python-dotenv`
   - Set up local and production settings

#### Acceptance Criteria

- ✅ Django project runs locally
- ✅ MySQL database connection works
- ✅ Custom Dashboard login works
- ✅ Dashboard home displays with Arabic RTL
- ✅ User roles (Super Admin, Content Admin, SEO Admin) work
- ✅ Base templates render correctly with RTL
- ✅ Static files serve correctly
- ✅ `passenger_wsgi.py` is configured for cPanel

#### Testing

- Manual testing of dashboard login
- Manual testing of role-based access
- Verify RTL layout in dashboard
- Test database queries

---

### Phase 2: Universities System

**Duration:** 2-3 weeks

**Objective:** Complete University content type with Faculty, Program, FAQ, and full CRUD in Custom Dashboard.

#### Deliverables

1. **University Models**
   - Create `University` model with all fields
   - Create `Faculty` model
   - Create `Program` model
   - Create `UniversityFAQ` model
   - Add SEO fields via `SEOMixin`
   - Add publish status via `PublishableModel`

2. **Custom Dashboard - University Management (Structured Template Editor)**
   - **IMPORTANT:** Universities use Structured Template Editor (predefined form sections), NOT Custom HTML Editor
   - Rich text fields (description, admission_requirements, registration_section) use **SimpleRichTextWidget** (basic formatting only: Bold, Italic, H2-H4, Lists, Links)
   - This is a structured form approach with organized sections, NOT free-form editing
   - Create university list view with search and filters
   - Create university create view with inline FAQ formset only
   - Create university edit view with:
     - University basic data fields
     - Inline FAQ formset
     - Read-only list of Faculties with Edit/Delete links
     - "Add Faculty" button linking to separate Faculty management
   - Create university delete view with confirmation
   - Implement slug change detection and redirect offer

3. **Custom Dashboard - Faculty Management** (Separate Views)
   - Create faculty list view (filtered by university)
   - Create faculty create view with inline Program formset
   - Create faculty edit view with inline Program formset
   - Create faculty delete view with confirmation
   - Faculty views are accessed from University edit page

4. **Public University Views**
   - Create university list view (paginated)
   - Create university detail view
   - Optimize queries with `select_related` and `prefetch_related`

5. **University Templates**
   - Create dashboard templates:
     - University: list, create, edit, delete
     - Faculty: list, create, edit, delete (separate from University)
   - Create public templates (list, detail)
   - Implement accordion for FAQ using Alpine.js
   - Ensure RTL support throughout

6. **Image Handling**
   - Implement image upload for logo and main image
   - Add image optimization on upload
   - Configure media storage

#### Acceptance Criteria

- ✅ Content Admin can create universities with FAQs
- ✅ Content Admin can manage Faculties separately with inline Programs
- ✅ University edit page shows read-only Faculty list with management links
- ✅ Inline formsets work correctly for FAQ and Program
- ✅ University list displays with search and status filters
- ✅ University detail page displays all sections in correct order
- ✅ FAQ accordion works with Alpine.js
- ✅ Images upload and display correctly
- ✅ Slug change detection offers to create redirect
- ✅ Published/Unpublished status works correctly
- ✅ SEO fields are editable in dashboard
- ✅ Public pages show only published universities
- ✅ RTL layout works on all pages

#### Testing

- Create 5 test universities with FAQs
- Create test faculties with programs for each university
- Test Faculty management from University edit page
- Test inline formset add/delete functionality for FAQ and Program
- Test search and filter functionality
- Test image upload and optimization
- Verify N+1 query prevention with Django Debug Toolbar
- Test navigation between University and Faculty management views

---

### Phase 3: Institutes System

**Duration:** 1-2 weeks

**Objective:** Complete Institute content type with Course and full CRUD in Custom Dashboard.

#### Deliverables

1. **Institute Models**
   - Create `Institute` model with all fields
   - Create `Course` model
   - Add SEO fields via `SEOMixin`
   - Add publish status via `PublishableModel`

2. **Custom Dashboard - Institute Management (Structured Template Editor)**
   - **IMPORTANT:** Institutes use Structured Template Editor (predefined form sections), NOT Custom HTML Editor
   - Rich text fields (description, registration_requirements, registration_section) use **SimpleRichTextWidget** (basic formatting only: Bold, Italic, H2-H4, Lists, Links)
   - This is a structured form approach with organized sections, NOT free-form editing
   - Create institute list view with search and filters
   - Create institute create view with inline Course formset
   - Create institute edit view with inline formset
   - Create institute delete view with confirmation
   - Implement slug change detection and redirect offer

3. **Public Institute Views**
   - Create institute list view (paginated)
   - Create institute detail view
   - Optimize queries

4. **Institute Templates**
   - Create dashboard templates (list, create, edit, delete)
   - Create public templates (list, detail)
   - Ensure RTL support throughout

#### Acceptance Criteria

- ✅ Content Admin can create institutes with courses
- ✅ Inline formsets work correctly for Course
- ✅ Institute list displays with search and status filters
- ✅ Institute detail page displays all sections in correct order
- ✅ Images upload and display correctly
- ✅ Slug change detection offers to create redirect
- ✅ Published/Unpublished status works correctly
- ✅ SEO fields are editable in dashboard
- ✅ Public pages show only published institutes
- ✅ RTL layout works on all pages

#### Testing

- Create 3 test institutes with courses
- Test inline formset functionality
- Test search and filter functionality
- Verify query optimization

---

### Phase 4: Majors System

**Duration:** 2-3 weeks

**Objective:** Complete Major content type with Dynamic Tables and full CRUD in Custom Dashboard.

#### Deliverables

1. **Major Models**
   - Create `Major` model with all fields
   - Create `SubjectsTable` model
   - Create `SalaryTable` model
   - Create `CountriesTable` model
   - Add SEO fields via `SEOMixin`
   - Add publish status via `PublishableModel`
   - Add relationships to universities

2. **Custom Dashboard - Major Management (Structured Template Editor)**
   - **IMPORTANT:** Majors use Structured Template Editor (predefined form sections with dynamic tables), NOT Custom HTML Editor
   - Rich text fields (description, why_study_section, how_to_apply_section) use **SimpleRichTextWidget** (basic formatting only: Bold, Italic, H2-H4, Lists, Links)
   - This is a structured form approach with organized sections and inline formsets for dynamic tables, NOT free-form editing
   - Create major list view with search and filters
   - Create major create view with inline Dynamic Table formsets
   - Create major edit view with inline formsets
   - Create major delete view with confirmation
   - Implement slug change detection and redirect offer
   - Implement university relationship management (best/cheap)

3. **Public Major Views**
   - Create major list view (paginated)
   - Create major detail view
   - Display dynamic tables with RTL support
   - Optimize queries

4. **Major Templates**
   - Create dashboard templates (list, create, edit, delete)
   - Create public templates (list, detail)
   - Create responsive table components
   - Ensure RTL support throughout

#### Acceptance Criteria

- ✅ Content Admin can create majors with dynamic tables
- ✅ Inline formsets work correctly for all three table types
- ✅ Major list displays with search and status filters
- ✅ Major detail page displays all sections in correct order
- ✅ Dynamic tables display correctly with RTL
- ✅ Tables are responsive on mobile
- ✅ University relationships (best/cheap) work correctly
- ✅ Images upload and display correctly
- ✅ Slug change detection offers to create redirect
- ✅ Published/Unpublished status works correctly
- ✅ SEO fields are editable in dashboard
- ✅ Public pages show only published majors
- ✅ RTL layout works on all pages

#### Testing

- Create 5 test majors with all dynamic tables
- Test inline formset functionality for tables
- Test university relationship selection
- Test responsive table display on mobile
- Verify query optimization

---

### Phase 5: Articles System with Custom HTML Editor

**⚠️ IMPORTANT: Custom HTML Editor is ONLY for Articles. Universities, Institutes, and Majors use Structured Template Editors (see "Structured Template Editors for Content Types" section).**

**Duration:** 3-4 weeks

**Objective:** Complete Article content type with Custom HTML Editor, categories, tags, and full CRUD in Custom Dashboard.

**Key Distinction:**
- **Articles ONLY:** Use flexible Custom HTML Editor for free-form content creation
- **Universities, Institutes, Majors:** Use Structured Template Editors with predefined sections and SimpleRichTextWidget

#### Deliverables

1. **Custom HTML Editor (V1 - Simplified)**
   - Create `apps/html_editor/` app
   - Implement `CustomHTMLEditorWidget` Django widget (textarea-based)
   - Implement simple formatting toolbar (Bold, Italic, H2-H4, Lists, Links, Images)
   - Implement HTML sanitizer with bleach (simplified tag list)
   - Create editor JavaScript for toolbar functionality
   - Create editor CSS with RTL support
   - Implement image upload for editor
   - NO block-based editor in V1
   - NO preview mode in V1

2. **Article Models**
   - Create `Category` model
   - Create `Tag` model
   - Create `Article` model with Custom HTML Editor field
   - Add SEO fields via `SEOMixin`
   - Add publish status via `PublishableModel`
   - Add relationships to universities, institutes, majors

3. **Custom Dashboard - Article Management**
   - Create article list view with search and filters
   - Create article create view with Custom HTML Editor
   - Create article edit view with Custom HTML Editor
   - Create article delete view with confirmation
   - Create article preview view
   - Implement slug change detection and redirect offer
   - Create category management views
   - Create tag management views

4. **Public Article Views**
   - Create article list view (paginated)
   - Create article detail view
   - Create category view
   - Create tag view
   - Optimize queries

5. **Article Templates**
   - Create dashboard templates (list, create, edit, delete, preview)
   - Create public templates (list, detail, category, tag)
   - Ensure RTL support throughout
   - Style rendered article content

#### Acceptance Criteria

- ✅ Custom HTML Editor (V1 simplified) works in dashboard
- ✅ Toolbar formatting buttons work correctly (Bold, Italic, Headings, Lists, Links, Images)
- ✅ Editor supports Arabic RTL text entry
- ✅ Image upload works in editor
- ✅ HTML sanitization prevents XSS attacks
- ✅ Content Admin can create articles with editor
- ✅ Article list displays with search and filters
- ✅ Article detail page displays rendered content correctly
- ✅ Category and tag filtering works
- ✅ Content relationships work correctly
- ✅ Images upload and display correctly
- ✅ Slug change detection offers to create redirect
- ✅ Published/Unpublished status works correctly
- ✅ SEO fields are editable in dashboard
- ✅ Public pages show only published articles
- ✅ RTL layout works on all pages

#### Testing

- Create 10 test articles with various HTML content
- Test all toolbar formatting buttons
- Test HTML sanitization with malicious input
- Test category and tag filtering
- Verify XSS protection
- Verify query optimization
- Test image upload in editor

---

### Phase 6: SEO, Search, and Redirects

**Duration:** 2-3 weeks

**Objective:** Complete SEO system, search functionality, and redirect management.

#### Deliverables

1. **SEO System**
   - Create `apps/seo/` app
   - Implement XML sitemap generation
   - Implement robots.txt view
   - Create SEO template tags (meta tags, schema markup)
   - Implement breadcrumb navigation
   - Implement Organization schema
   - Implement Article schema
   - Implement FAQ schema

2. **Search System**
   - Create `apps/search/` app
   - Implement search view with Django ORM
   - Create search form
   - Implement search across all content types
   - Implement pagination for search results
   - Support Arabic search queries

3. **Redirect System**
   - Create `apps/redirects/` app
   - Create `Redirect` model
   - Implement redirect middleware
   - Create redirect management views in dashboard
   - Implement automatic redirect creation on slug change

4. **Dashboard - SEO & Redirect Management**
   - Ensure SEO fields are accessible for SEO Admin role
   - Create redirect list view
   - Create redirect create/edit views
   - Display redirect hit counts

5. **Templates**
   - Create search results template
   - Create redirect management templates
   - Add SEO meta tags to all public templates
   - Add schema markup to relevant templates

#### Acceptance Criteria

- ✅ XML sitemap generates correctly with all published content
- ✅ robots.txt serves correctly
- ✅ SEO meta tags render on all public pages
- ✅ Open Graph tags render correctly
- ✅ Twitter Card tags render correctly
- ✅ Breadcrumb navigation displays with schema markup
- ✅ Organization schema renders on homepage
- ✅ Article schema renders on article pages
- ✅ FAQ schema renders on university pages
- ✅ Search works across all content types
- ✅ Search supports Arabic queries
- ✅ Search results paginate correctly
- ✅ Redirect middleware works correctly
- ✅ 301 redirects preserve SEO value
- ✅ Redirect hit counts increment correctly
- ✅ SEO Admin can edit SEO fields
- ✅ Automatic redirect creation works on slug change

#### Testing

- Test sitemap generation with various content
- Test robots.txt
- Validate schema markup with Google Rich Results Test
- Test search with Arabic queries
- Test redirect middleware with various URLs
- Test automatic redirect creation
- Verify SEO meta tags on all pages

---

### Phase 7: Frontend, RTL, and Performance

**Duration:** 2-3 weeks

**Objective:** Complete responsive frontend with RTL support, performance optimizations, and lead generation.

#### Deliverables

1. **Lead Generation System**
   - Create `apps/leads/` app
   - Create `Lead` model
   - Create lead forms (Registration, Contact)
   - Implement honeypot anti-spam
   - Implement rate limiting
   - Implement email notifications
   - Create lead management views in dashboard
   - Implement lead filtering and CSV export

2. **Responsive Frontend**
   - Finalize all public templates
   - Implement mobile-first responsive design
   - Create responsive navigation with Alpine.js
   - Create responsive tables
   - Create responsive forms
   - Ensure touch-friendly elements

3. **RTL Support**
   - Verify RTL layout on all pages
   - Test RTL on mobile devices
   - Fix any RTL layout issues
   - Test accordion, navigation, tables with RTL

4. **Performance Optimization**
   - Implement image lazy loading
   - Optimize database queries
   - Implement pagination on all lists
   - Minify CSS and JavaScript
   - Configure file-based caching
   - Implement template fragment caching
   - Optimize image uploads

5. **Dashboard - Lead Management**
   - Create lead list view with filters
   - Create lead detail view
   - Implement lead export to CSV
   - Display simple statistics on dashboard home

#### Acceptance Criteria

- ✅ Lead forms work on all content pages
- ✅ Honeypot anti-spam works
- ✅ Rate limiting prevents abuse
- ✅ Email notifications send correctly
- ✅ Lead management works in dashboard
- ✅ Lead filtering works (type, date, search)
- ✅ CSV export works correctly
- ✅ All pages are responsive on mobile
- ✅ Navigation works on mobile
- ✅ Tables are responsive
- ✅ Forms work on mobile
- ✅ RTL layout works on all devices
- ✅ Images lazy load correctly
- ✅ No N+1 query problems
- ✅ Pagination works on all lists
- ✅ CSS and JS are minified
- ✅ File-based caching works
- ✅ Dashboard statistics display correctly

#### Testing

- Test lead form submission
- Test spam protection
- Test rate limiting
- Test email notifications
- Test lead export
- Test responsive design on various devices
- Test RTL on mobile
- Test performance with Django Debug Toolbar
- Verify lazy loading
- Test caching

---

### Phase 8: Deployment and Production Hardening

**Duration:** 1-2 weeks

**Objective:** Deploy to production cPanel hosting with SSL, backups, and security hardening.

#### Deliverables

1. **cPanel Deployment**
   - Set up cPanel hosting account
   - Create MySQL database
   - Create Python virtual environment
   - Install dependencies
   - Configure `passenger_wsgi.py`
   - Configure `.htaccess`
   - Set up static and media directories
   - Run migrations
   - Create superuser
   - Collect static files

2. **SSL Configuration**
   - Install SSL certificate
   - Force HTTPS redirect
   - Configure secure cookies
   - Test HTTPS

3. **Security Hardening**
   - Set `DEBUG=False`
   - Configure `ALLOWED_HOSTS`
   - Set strong `SECRET_KEY`
   - Configure security headers
   - Test CSRF protection
   - Test XSS protection
   - Run `python manage.py check --deploy`

4. **Backup Configuration**
   - Set up automated database backups
   - Set up automated media backups
   - Test backup restoration
   - Document backup procedures

5. **Monitoring and Logging**
   - Configure error logging
   - Set up email error notifications
   - Test error handling

6. **Documentation**
   - Create deployment documentation
   - Create user manual for Custom Dashboard
   - Create maintenance procedures
   - Create troubleshooting guide

7. **Final Testing**
   - Test all public pages
   - Test Custom Dashboard
   - Test lead form submission
   - Test email notifications
   - Test image uploads
   - Test Custom HTML Editor
   - Verify sitemap and robots.txt
   - Test redirects
   - Check error logs

#### Acceptance Criteria

- ✅ Platform is deployed to production cPanel
- ✅ SSL certificate is installed and working
- ✅ HTTPS redirect works
- ✅ All security checks pass
- ✅ Database backups are automated
- ✅ Media backups are automated
- ✅ Error logging works
- ✅ Email notifications work
- ✅ All public pages work correctly
- ✅ Custom Dashboard works correctly
- ✅ Lead forms work correctly
- ✅ Custom HTML Editor works correctly
- ✅ Image uploads work correctly
- ✅ Sitemap and robots.txt work
- ✅ Redirects work correctly
- ✅ Documentation is complete

#### Testing

- Full end-to-end testing on production
- Security testing
- Performance testing
- Backup and restoration testing
- Error handling testing
- Load testing (basic)

---

## Phase Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1** | 1-2 weeks | Django project, database, Custom Dashboard foundation, user roles |
| **Phase 2** | 2-3 weeks | Universities with Faculty/Program/FAQ, CRUD in dashboard |
| **Phase 3** | 1-2 weeks | Institutes with Course, CRUD in dashboard |
| **Phase 4** | 2-3 weeks | Majors with Dynamic Tables, CRUD in dashboard |
| **Phase 5** | 3-4 weeks | Articles with Custom HTML Editor, categories, tags |
| **Phase 6** | 2-3 weeks | SEO system, search, redirects |
| **Phase 7** | 2-3 weeks | Lead generation, responsive frontend, RTL, performance |
| **Phase 8** | 1-2 weeks | cPanel deployment, SSL, backups, security hardening |

**Total Estimated Duration:** 15-22 weeks (approximately 4-5 months)

---

## Post-Launch Maintenance

### Ongoing Tasks

1. **Content Management**
   - Regular content updates via Custom Dashboard
   - Monitor lead submissions
   - Respond to inquiries

2. **Performance Monitoring**
   - Monitor page load times
   - Check error logs
   - Optimize slow queries

3. **Security Updates**
   - Keep Django and dependencies updated
   - Monitor security advisories
   - Regular security audits

4. **Backup Verification**
   - Regularly test backup restoration
   - Verify backup integrity
   - Update backup procedures

5. **SEO Monitoring**
   - Monitor search rankings
   - Update meta tags as needed
   - Add new content regularly

### Future Enhancements (Post-V1)

1. **Multilingual Support**
   - Add English language
   - Implement language switcher
   - Translate content

2. **Advanced Analytics**
   - Integrate Google Analytics
   - Add dashboard analytics
   - Track conversion rates

3. **Advanced Search**
   - Consider Elasticsearch if needed
   - Add filters and facets
   - Improve search relevance

4. **User Features**
   - User registration
   - Saved favorites
   - Application tracking

5. **Performance Enhancements**
   - Add Redis caching if needed
   - Implement CDN for static files
   - Further optimize images


---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Published Content Visibility

*For any* content entity (University, Institute, Major, Article) with `publish_status='published'`, that entity SHALL appear in public-facing pages, search results, and sitemaps.

**Validates: Requirements 13.6**

### Property 2: Unpublished Content Exclusion

*For any* content entity (University, Institute, Major, Article) with `publish_status='unpublished'`, that entity SHALL NOT appear in public-facing pages, search results, or sitemaps.

**Validates: Requirements 13.3, 13.4, 13.5**

### Property 3: HTML Sanitization Safety

*For any* HTML content processed through the Custom HTML Editor sanitizer, the output SHALL NOT contain unsafe script tags or malicious code.

**Validates: Requirements 3.12, 3.13, 8.7, 17.2**

### Property 4: Slug Uniqueness

*For any* content type (University, Institute, Major, Article), no two published entities of the same type SHALL have the same slug value.

**Validates: Requirements 10.4**

### Property 5: Redirect Preservation

*For any* active redirect with `old_url` and `new_url`, when a user requests `old_url`, the system SHALL respond with HTTP 301 status and redirect to `new_url`.

**Validates: Requirements 11.3**

### Property 6: Role-Based Access Control

*For any* Custom Dashboard view requiring Content Admin role, users without Content Admin or Super Admin role SHALL be denied access.

**Validates: Requirements 14.4, 14.6**

### Property 7: CSRF Protection

*For any* form submission (lead form, dashboard form), the request SHALL include a valid CSRF token, otherwise the submission SHALL be rejected.

**Validates: Requirements 4.10, 17.1**

### Property 8: Lead Form Tracking

*For any* lead form submission, the system SHALL record source page URL, timestamp, referrer, and UTM parameters.

**Validates: Requirements 4.3, 4.4, 4.5, 4.6**

### Property 9: SEO Meta Tag Rendering

*For any* published content page, the system SHALL render meta title, meta description, canonical URL, Open Graph tags, and Twitter Card tags.

**Validates: Requirements 9.10, 9.11**

### Property 10: Image Optimization

*For any* uploaded image exceeding maximum dimensions, the system SHALL automatically resize and compress the image.

**Validates: Requirements 15.2, 15.3**

### Property 11: Search Query Coverage

*For any* search query, the system SHALL search across University, Institute, Major, and Article content types.

**Validates: Requirements 12.2**

### Property 12: Arabic RTL Layout

*For any* page (public or dashboard), the system SHALL apply RTL text direction and correct text alignment for Arabic content.

**Validates: Requirements 1.2, 1.3**

### Property 13: Inline Formset Integrity

*For any* university with faculties and programs, when editing the university, all existing faculties and programs SHALL be editable inline, and new ones SHALL be addable.

**Validates: Requirements 2.12**

### Property 14: Dynamic Table Persistence

*For any* major with dynamic tables (Subjects, Salary, Countries), when editing the major, all table rows SHALL persist correctly and be editable.

**Validates: Requirements 7.3, 7.4, 7.5**

### Property 15: Email Notification Delivery

*For any* lead form submission, the system SHALL send an email notification to administrators.

**Validates: Requirements 4.7**

### Property 16: Rate Limiting Protection

*For any* IP address submitting more than 3 lead forms within 1 hour, subsequent submissions SHALL be rejected.

**Validates: Requirements 17.7**

### Property 17: Sitemap Inclusion Control

*For any* content entity with `sitemap_include=False`, that entity SHALL NOT appear in the XML sitemap.

**Validates: Requirements 9.3**

### Property 18: Breadcrumb Navigation

*For any* content detail page, the system SHALL render breadcrumb navigation with correct hierarchy.

**Validates: Requirements 9.5**

### Property 19: Schema Markup Rendering

*For any* article page, the system SHALL render Article schema markup with headline, image, dates, author, and publisher.

**Validates: Requirements 9.7**

### Property 20: FAQ Schema Rendering

*For any* university page with FAQs, the system SHALL render FAQ schema markup with questions and answers.

**Validates: Requirements 9.8**

### Property 21: Responsive Table Display

*For any* table on mobile devices, the system SHALL render the table responsively with horizontal scrolling or stacking.

**Validates: Requirements 18.3**

### Property 22: Mobile Navigation

*For any* mobile device, the navigation menu SHALL render appropriately using Alpine.js.

**Validates: Requirements 18.4**

### Property 23: Image Lazy Loading

*For any* image below the fold, the system SHALL implement lazy loading.

**Validates: Requirements 15.7, 16.2**

### Property 24: Query Optimization

*For any* content list or detail view, the system SHALL use `select_related` or `prefetch_related` to avoid N+1 query problems.

**Validates: Requirements 16.4**

### Property 25: Pagination

*For any* content list exceeding 20 items, the system SHALL paginate the results.

**Validates: Requirements 16.1**

### Property 26: Content Relationships

*For any* article linked to universities, institutes, or majors, those relationships SHALL display correctly on the article detail page.

**Validates: Requirements 21.7, 21.8**

### Property 27: Lead Export

*For any* set of filtered leads, the system SHALL export them to CSV format with all relevant fields.

**Validates: Requirements 22.6**

### Property 28: Dashboard Statistics

*For any* dashboard home view, the system SHALL display total lead count, lead count by type, and current month lead count.

**Validates: Requirements 22.7**

### Property 29: Slug Change Warning

*For any* published content with slug change, the Custom Dashboard SHALL display a warning and offer to create a redirect.

**Validates: Requirements 10.6, 10.7**

### Property 30: Arabic Search Support

*For any* Arabic search query, the system SHALL return relevant results matching the query.

**Validates: Requirements 12.6**

---

## Conclusion

This technical design document provides a comprehensive blueprint for the Science Gates platform. The design emphasizes:

1. **Custom Dashboard First**: Professional custom-built admin interface as the primary management tool
2. **Custom HTML Editor**: Built specifically for the platform, not third-party WYSIWYG editors
3. **Arabic RTL Native**: Designed with RTL as the primary layout direction
4. **Security by Design**: Built-in protection against common web vulnerabilities
5. **Performance Without Complexity**: Optimized using simple, effective techniques
6. **cPanel Compatible**: All architectural decisions support shared hosting deployment
7. **Incremental Development**: 8 sequential phases with clear deliverables

The platform is sized appropriately for ~200 articles and moderate content volume, avoiding overengineering while maintaining professional quality and future extensibility.

### Key Design Decisions

- **Django + MySQL/MariaDB**: Proven, stable, well-documented stack
- **Django Templates**: Server-side rendering for SEO and simplicity
- **Tailwind CSS + Alpine.js**: Modern, lightweight frontend stack
- **Custom Dashboard**: Purpose-built for Science Gates, not generic admin
- **Custom HTML Editor**: Full control over features and security
- **File-Based Caching**: Simple, reliable, cPanel-compatible
- **Django ORM Search**: Sufficient for moderate content volume
- **Simple Publishing**: Published/Unpublished only, no complex workflows
- **Simple Roles**: Three roles only, no enterprise complexity

### Success Criteria

The platform will be considered successful when:

1. Content admins can manage all content types efficiently through Custom Dashboard
2. Articles can be created with rich content using Custom HTML Editor
3. All pages render correctly with Arabic RTL on all devices
4. Lead forms capture inquiries with proper tracking
5. SEO system generates proper meta tags, sitemaps, and schema markup
6. Platform performs well with optimized queries and caching
7. Security measures protect against common vulnerabilities
8. Platform deploys successfully to cPanel hosting
9. All 30 correctness properties are validated through testing

### Next Steps

1. Review and approve this design document
2. Set up development environment
3. Begin Phase 1: Foundation & Project Setup
4. Follow incremental development phases
5. Test each phase thoroughly before proceeding
6. Deploy to production after Phase 8 completion

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Status:** Ready for Implementation

