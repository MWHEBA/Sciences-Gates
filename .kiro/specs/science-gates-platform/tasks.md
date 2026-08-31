# Implementation Plan: Science Gates Platform

## Overview

This implementation plan breaks down the Science Gates platform (شركة بوابات العلوم للدراسة في ماليزيا) into 8 sequential phases. The platform is an Arabic-language educational content platform built with Django, MySQL/MariaDB, Django Templates, Tailwind CSS, and Alpine.js, designed for cPanel deployment.

**Key Architecture Decisions:**
- **Custom Dashboard** as primary admin interface (NOT Django Admin)
- **Custom HTML Editor** for articles only (NOT CKEditor or TinyMCE) - **V1 is BASIC**: Bold, Italic, Headers (H2-H4), Lists (UL/OL), Links, Images only. Video embeds, tables, and CTA blocks are future enhancements.
- **Structured Template Editors** for Universities, Institutes, and Majors
- **Arabic RTL native** design throughout
- **Simple, maintainable** approach without overengineering

**Implementation Language:** Python (Django framework)

**Phase Organization:**
- **Phase 1**: Foundation, SEO Base, Project Setup
- **Phase 2**: User Management, Dashboard Foundation, Redirects (moved early for slug system support)
- **Phase 3**: University Content System
- **Phase 4**: Institute Content System
- **Phase 5**: Major Content System
- **Phase 6**: Article System with Custom HTML Editor
- **Phase 7**: Lead Generation (lighter phase)
- **Phase 8**: Search, Frontend, RTL, Performance, Deployment

## Tasks

- [x] 1. Phase 1: Foundation, SEO Base, and Project Setup
  - [x] 1.1 Initialize Django project with split settings structure
    - Create Django project named `science_gates`
    - Set up `config/settings/` directory with `base.py`, `local.py`, `production.py`
    - Configure MySQL/MariaDB database connection
    - Set up environment variables using python-decouple
    - Create `.env.example` file with all required variables
    - _Requirements: 20, 21.2_

  - [x] 1.2 Create core app with base models and mixins
    - Create `apps/core/` Django app
    - Implement `TimestampedModel` abstract base class
    - Implement `PublishableModel` abstract base class with `PublishStatus` choices
    - Implement `SEOMixin` abstract base class with all SEO fields (meta_title, meta_description, focus_keyword, canonical_url, robots_index, robots_follow, sitemap_include, og_title, og_description, og_image)
    - Add helper methods: `get_meta_title()`, `get_meta_description()`, `get_robots_content()`, `get_og_title()`, `get_og_description()`, `get_og_image_url()`
    - _Requirements: 10, 14_

  - [x] 1.3 Set up static files and media handling with basic image validation
    - Configure `STATIC_ROOT`, `STATIC_URL`, `MEDIA_ROOT`, `MEDIA_URL` in settings
    - Create `static/` directory structure: `css/`, `js/`, `images/`
    - Create `media/` directory structure with subdirectories for each content type
    - Install and configure Pillow for image processing
    - Create `apps/core/utils.py` with basic image validation utilities
    - Implement max file size validation (e.g., 5MB limit)
    - Implement basic image resize on upload (e.g., max 1920px width)
    - _Requirements: 16, 20_

  - [x] 1.4 Configure Tailwind CSS with RTL support
    - Install Tailwind CSS via npm
    - Create `tailwind.config.js` with RTL plugin configuration
    - Set up `static/css/tailwind.css` with RTL directives
    - Configure build script for CSS compilation
    - _Requirements: 1, 19_

  - [x] 1.5 Create SEO app with base structure and sitemap foundation
    - Create `apps/seo/` Django app
    - Create `apps/seo/models.py` (empty, SEOMixin is in core app)
    - Create `apps/seo/sitemaps.py` with base sitemap classes (will be populated with content in Phase 7)
    - Create `apps/seo/views.py` with `robots_txt` view returning text/plain response
    - Configure robots.txt URL in root URLconf
    - Create `apps/seo/templatetags/` directory structure for future template tags
    - Create `apps/seo/schema.py` (empty structure for JSON-LD schema generation in Phase 7)
    - _Requirements: 10_

  - [x] 1.6 Create cPanel deployment configuration
    - Create `passenger_wsgi.py` file for cPanel Passenger WSGI
    - Create `requirements.txt` with all Python dependencies
    - Configure static file serving for cPanel environment
    - Set up file-based caching configuration
    - _Requirements: 20_


- [x] 2. Phase 2: User Management, Custom Dashboard Foundation, and Redirects
  - [x] 2.1 Create user profile model with role management
    - Create `UserRole` choices: SUPER_ADMIN, CONTENT_ADMIN, SEO_ADMIN
    - Create `UserProfile` model with OneToOne relationship to User
    - Add role field with default CONTENT_ADMIN
    - Implement role check methods: `is_super_admin()`, `is_content_admin()`, `is_seo_admin()`
    - Create signal to auto-create profile on user creation
    - _Requirements: 15_

  - [x] 2.2 Create dashboard app with authentication views
    - Create `apps/dashboard/` Django app
    - Implement login view with Arabic RTL template
    - Implement logout view
    - Create dashboard base template with RTL layout
    - Add CSRF protection to all forms
    - _Requirements: 2, 18_

  - [x] 2.3 Implement dashboard access control mixins
    - Create `DashboardMixin` requiring login and profile
    - Create `ContentAdminRequiredMixin` for content management
    - Create `SEOAdminRequiredMixin` for SEO management
    - Create `SuperAdminRequiredMixin` for user management
    - Add Arabic error messages for unauthorized access
    - _Requirements: 2, 15_

  - [x] 2.4 Create dashboard home view with statistics
    - Implement `DashboardHomeView` with statistics calculation
    - Calculate total leads, leads by type, current month leads
    - Calculate published content counts for all content types
    - Fetch recent 10 leads for display
    - Create Arabic RTL dashboard home template with statistics cards
    - _Requirements: 2, 23_

  - [x] 2.5 Create dashboard sidebar navigation component
    - Create `templates/dashboard/components/sidebar.html`
    - Add navigation sections: Home, Content, Leads, SEO, Administration
    - Implement role-based visibility for navigation items
    - Add unread leads badge counter
    - Style with Tailwind CSS for RTL layout
    - _Requirements: 2_

  - [x] 2.6 Create user management dashboard views (Super Admin only)
    - Implement `UserListView` with SuperAdminRequiredMixin
    - Implement `UserCreateView` creating User and UserProfile
    - Implement `UserUpdateView` for editing user and role
    - Implement `UserDeleteView` with confirmation
    - Create templates for user management in `templates/dashboard/users/`
    - Add success/error messages in Arabic
    - _Requirements: 2, 15_

  - [x] 2.7 Create user management dashboard templates
    - Create `templates/dashboard/users/list.html` with user list and roles
    - Create `templates/dashboard/users/create.html` with user creation form
    - Create `templates/dashboard/users/edit.html` with user edit form
    - Create `templates/dashboard/users/delete_confirm.html`
    - Style with Tailwind CSS for RTL layout
    - _Requirements: 2, 15_

  - [x] 2.8 Create redirect model and middleware
    - Create `apps/redirects/` Django app
    - Implement `Redirect` model inheriting from `TimestampedModel`
    - Add fields: old_url, new_url, is_active, notes, hit_count
    - Add database index for old_url and is_active
    - Implement `increment_hit_count()` method
    - Create `apps/redirects/middleware.py` with `RedirectMiddleware`
    - Check for active redirects matching request path
    - Return 301 redirect if match found
    - Increment hit count on redirect
    - _Requirements: 11, 12_

  - [x] 2.9 Create redirect management dashboard views
    - Implement `RedirectListView` with search filter
    - Implement `RedirectCreateView`
    - Implement `RedirectUpdateView`
    - Implement `RedirectDeleteView`
    - Add success/error messages in Arabic
    - _Requirements: 2, 12_

  - [x] 2.10 Create redirect management dashboard templates
    - Create `templates/dashboard/redirects/list.html` with search
    - Create `templates/dashboard/redirects/create.html`
    - Create `templates/dashboard/redirects/edit.html`
    - Show hit_count in list view
    - Style with Tailwind CSS for RTL layout
    - _Requirements: 2, 12_

  - [x] 2.11 Register redirect models in Django Admin (emergency use)
    - Create `apps/redirects/admin.py`
    - Register Redirect model
    - Add basic list_display, search_fields, and filters
    - _Requirements: 2_


- [x] 3. Phase 3: University Content System
  - [x] 3.1 Create university models
    - Create `apps/universities/` Django app
    - Implement `University` model inheriting from `TimestampedModel`, `PublishableModel`, `SEOMixin`
    - Add fields: name, slug (with `allow_unicode=True`), logo, main_image, description, location, video_url, admission_requirements, registration_section
    - Add ManyToMany relationships: related_majors, related_articles
    - Implement `get_absolute_url()` method
    - Add slug change detection in `save()` method for redirect creation
    - _Requirements: 6, 11_

  - [x] 3.2 Create faculty and program models
    - Implement `Faculty` model with ForeignKey to University
    - Add fields: name, sort_order
    - Add unique_together constraint on university and name
    - Implement `Program` model with ForeignKey to Faculty
    - Add fields: name, duration, tuition_fees, sort_order
    - _Requirements: 6_

  - [x] 3.3 Create university FAQ model
    - Implement `UniversityFAQ` model with ForeignKey to University
    - Add fields: question, answer, sort_order
    - Set ordering by sort_order
    - _Requirements: 6_

  - [x] 3.4 Create simple rich text widget for structured editors
    - Create `apps/core/widgets.py` with `SimpleRichTextWidget`
    - Implement toolbar with buttons: Bold, Italic, H2, H3, H4, UL, OL, Link
    - Create JavaScript for toolbar functionality with RTL support
    - Implement HTML sanitization allowing only: p, br, strong, em, h2, h3, h4, ul, ol, li, a
    - Create CSS for simple rich text editor styling
    - _Requirements: 4_

  - [x] 3.5 Create university dashboard forms
    - Create `apps/dashboard/forms/university.py`
    - Implement `UniversityForm` with all university fields
    - Use `SimpleRichTextWidget` for description, admission_requirements, registration_section fields
    - Create inline formset for FAQ entries
    - Add Arabic labels and help text for all fields
    - _Requirements: 2, 4_

  - [x] 3.6 Create university dashboard CRUD views
    - Implement `UniversityListView` with search and status filters
    - Implement `UniversityCreateView` with inline FAQ formset
    - Implement `UniversityUpdateView` with inline FAQ formset and faculty list display
    - Add slug change warning and redirect creation option
    - Implement `UniversityDeleteView` with confirmation
    - Add success/error messages in Arabic
    - _Requirements: 2, 11, 12_

  - [x] 3.7 Create faculty management views (separate pages)
    - Implement `FacultyListView` for specific university
    - Implement `FacultyCreateView` with inline Program formset
    - Implement `FacultyUpdateView` with inline Program formset
    - Implement `FacultyDeleteView` with confirmation
    - Add breadcrumb navigation showing university context
    - _Requirements: 2, 6_

  - [x] 3.8 Create university dashboard templates
    - Create `templates/dashboard/universities/list.html` with filters and pagination
    - Create `templates/dashboard/universities/create.html` with FAQ formset
    - Create `templates/dashboard/universities/edit.html` with FAQ formset and faculty list
    - Create `templates/dashboard/universities/delete_confirm.html`
    - Create `templates/dashboard/faculties/` templates for faculty management
    - Style all templates with Tailwind CSS for RTL layout
    - _Requirements: 2, 19_

  - [x] 3.9 Create university public views and templates
    - Implement `UniversityListView` for public site with pagination
    - Implement `UniversityDetailView` with select_related and prefetch_related optimization
    - Create `templates/universities/list.html` with RTL layout
    - Create `templates/universities/detail.html` showing all sections including registration_section
    - Implement accordion UI for FAQ using Alpine.js
    - Add lazy loading for images
    - _Requirements: 6, 17, 19_

  - [x] 3.10 Register university models in Django Admin (emergency use)
    - Create `apps/universities/admin.py`
    - Register University, Faculty, Program, UniversityFAQ models
    - Add basic list_display and search_fields
    - Add note that Django Admin is for emergency use only
    - _Requirements: 2_


- [x] 4. Phase 4: Institute Content System
  - [x] 4.1 Create institute models
    - Create `apps/institutes/` Django app
    - Implement `Institute` model inheriting from `TimestampedModel`, `PublishableModel`, `SEOMixin`
    - Add fields: name, slug (with `allow_unicode=True`), main_image, description, registration_requirements, registration_section
    - Add ManyToMany relationship: related_articles
    - Implement `get_absolute_url()` method
    - Add slug change detection in `save()` method
    - _Requirements: 7, 11_

  - [x] 4.2 Create course model
    - Implement `Course` model with ForeignKey to Institute
    - Add fields: name, duration, fees, description, notes
    - Set ordering by name
    - _Requirements: 7_

  - [x] 4.3 Create institute dashboard forms
    - Create `apps/dashboard/forms/institute.py`
    - Implement `InstituteForm` with all institute fields
    - Use `SimpleRichTextWidget` for description, registration_requirements, registration_section fields
    - Create inline formset for Course entries
    - Add Arabic labels and help text
    - _Requirements: 2, 4_

  - [x] 4.4 Create institute dashboard CRUD views
    - Implement `InstituteListView` with search and status filters
    - Implement `InstituteCreateView` with inline Course formset
    - Implement `InstituteUpdateView` with inline Course formset
    - Add slug change warning and redirect creation option
    - Implement `InstituteDeleteView` with confirmation
    - Add success/error messages in Arabic
    - _Requirements: 2, 11, 12_

  - [x] 4.5 Create institute dashboard templates
    - Create `templates/dashboard/institutes/list.html` with filters
    - Create `templates/dashboard/institutes/create.html` with Course formset
    - Create `templates/dashboard/institutes/edit.html` with Course formset
    - Create `templates/dashboard/institutes/delete_confirm.html`
    - Style with Tailwind CSS for RTL layout
    - _Requirements: 2, 19_

  - [x] 4.6 Create institute public views and templates
    - Implement `InstituteListView` for public site with pagination
    - Implement `InstituteDetailView` with select_related optimization
    - Create `templates/institutes/list.html` with RTL layout
    - Create `templates/institutes/detail.html` showing all sections including registration_section
    - Add lazy loading for images
    - _Requirements: 7, 17, 19_

  - [x] 4.7 Register institute models in Django Admin (emergency use)
    - Create `apps/institutes/admin.py`
    - Register Institute and Course models
    - Add basic list_display and search_fields
    - _Requirements: 2_


- [x] 5. Phase 5: Major Content System with Dynamic Tables
  - [x] 5.1 Create major model
    - Create `apps/majors/` Django app
    - Implement `Major` model inheriting from `TimestampedModel`, `PublishableModel`, `SEOMixin`
    - Add fields: name, slug, main_image, description, study_duration
    - Add quick info fields: tuition_fees, study_language, practical_training, career_opportunities
    - Add content sections: why_study_section, how_to_apply_section
    - Add ManyToMany relationships: best_universities, cheap_universities, related_articles
    - Implement `get_absolute_url()` and slug change detection
    - _Requirements: 8, 11_

  - [x] 5.2 Create dynamic table models
    - Implement `SubjectsTable` model with ForeignKey to Major
    - Add fields: academic_year, subjects, sort_order
    - Implement `SalaryTable` model with ForeignKey to Major
    - Add fields: job_title, average_monthly_salary, sort_order
    - Implement `CountriesTable` model with ForeignKey to Major
    - Add fields: destination, study_duration, annual_fees, living_cost, sort_order
    - _Requirements: 8_

  - [x] 5.3 Create major dashboard forms
    - Create `apps/dashboard/forms/major.py`
    - Implement `MajorForm` with all major fields
    - Use `SimpleRichTextWidget` for description, why_study_section, how_to_apply_section
    - Create inline formsets for SubjectsTable, SalaryTable, CountriesTable
    - Add Arabic labels and help text
    - _Requirements: 2, 4_

  - [x] 5.4 Create major dashboard CRUD views
    - Implement `MajorListView` with search and status filters
    - Implement `MajorCreateView` with all three inline formsets
    - Implement `MajorUpdateView` with all three inline formsets
    - Add slug change warning and redirect creation option
    - Implement `MajorDeleteView` with confirmation
    - Add success/error messages in Arabic
    - _Requirements: 2, 11, 12_

  - [x] 5.5 Create major dashboard templates
    - Create `templates/dashboard/majors/list.html` with filters
    - Create `templates/dashboard/majors/create.html` with three formsets
    - Create `templates/dashboard/majors/edit.html` with three formsets
    - Create `templates/dashboard/majors/delete_confirm.html`
    - Add JavaScript for dynamic formset management
    - Style with Tailwind CSS for RTL layout
    - _Requirements: 2, 19_

  - [x] 5.6 Create major public views and templates
    - Implement `MajorListView` for public site with pagination
    - Implement `MajorDetailView` with select_related and prefetch_related optimization
    - Create `templates/majors/list.html` with RTL layout
    - Create `templates/majors/detail.html` showing all sections and tables
    - Render dynamic tables with proper RTL styling
    - Add lazy loading for images
    - _Requirements: 8, 17, 19_

  - [x] 5.7 Register major models in Django Admin (emergency use)
    - Create `apps/majors/admin.py`
    - Register Major, SubjectsTable, SalaryTable, CountriesTable models
    - Add basic list_display and search_fields
    - _Requirements: 2_


- [x] 6. Phase 6: Article System with Custom HTML Editor
  - [x] 6.1 Create article category and tag models
    - Create `apps/articles/` Django app
    - Implement `Category` model inheriting from `TimestampedModel`
    - Add fields: name, slug (with `allow_unicode=True`), description
    - Implement `Tag` model with fields: name, slug
    - Implement `get_absolute_url()` for both models
    - _Requirements: 9_

  - [x] 6.2 Create article model
    - Implement `Article` model inheriting from `TimestampedModel`, `PublishableModel`, `SEOMixin`
    - Add fields: title, slug, featured_image, category (ForeignKey), tags (ManyToMany), author (ForeignKey to User), publish_date, content
    - Add ManyToMany relationships: related_universities, related_institutes, related_majors
    - Add database indexes for publish_date and category+publish_date
    - Implement `get_absolute_url()` and slug change detection
    - _Requirements: 9, 11_

  - [x] 6.3 Create custom HTML editor widget (V1 BASIC version)
    - Create `apps/html_editor/` Django app
    - Create `apps/html_editor/widgets.py` with `CustomHTMLEditorWidget`
    - **V1 SCOPE**: Implement toolbar with buttons: Bold, Italic, H2-H4, UL, OL, Link, Image ONLY
    - **NOTE**: Video embeds, tables, and CTA blocks are FUTURE enhancements (not in V1)
    - Create `static/html_editor/js/html_editor.js` with basic editor functionality
    - Support Arabic RTL text entry and editing
    - Add image upload functionality with alt text
    - Create `static/html_editor/css/html_editor.css` for editor styling
    - _Requirements: 3_

  - [x] 6.4 Create HTML sanitizer for article content
    - Create `apps/html_editor/sanitizer.py`
    - Implement sanitization using bleach library
    - **V1 SCOPE**: Define allowed tags: p, br, strong, em, h2, h3, h4, h5, h6, ul, ol, li, a, img
    - **NOTE**: table, video, iframe tags are NOT allowed in V1 (future enhancement)
    - Define allowed attributes for each tag
    - Create `sanitize_article_html()` function
    - _Requirements: 3, 9, 18_

  - [x] 6.5 Create article dashboard forms
    - Create `apps/dashboard/forms/article.py`
    - Implement `ArticleForm` with all article fields
    - Use `CustomHTMLEditorWidget` for content field
    - Add Arabic labels and help text
    - Add form validation for required fields
    - Add help text clarifying V1 editor capabilities (Bold, Italic, Headers, Lists, Links, Images)
    - _Requirements: 2, 3_

  - [x] 6.6 Create category and tag management views
    - Implement `CategoryListView`, `CategoryCreateView`, `CategoryUpdateView`, `CategoryDeleteView`
    - Implement `TagListView`, `TagCreateView`, `TagUpdateView`, `TagDeleteView`
    - Create templates for category and tag management
    - Add Arabic success/error messages
    - _Requirements: 2, 9_

  - [x] 6.7 Create article dashboard CRUD views
    - Implement `ArticleListView` with search, category, and status filters
    - Implement `ArticleCreateView` with Custom HTML Editor
    - Implement `ArticleUpdateView` with Custom HTML Editor
    - Add slug change warning and redirect creation option
    - Implement `ArticleDeleteView` with confirmation
    - Sanitize HTML content before saving
    - Add success/error messages in Arabic
    - _Requirements: 2, 3, 11, 12_

  - [x] 6.8 Create article dashboard templates
    - Create `templates/dashboard/articles/list.html` with filters
    - Create `templates/dashboard/articles/create.html` with Custom HTML Editor
    - Create `templates/dashboard/articles/edit.html` with Custom HTML Editor
    - Create `templates/dashboard/articles/delete_confirm.html`
    - Style with Tailwind CSS for RTL layout
    - _Requirements: 2, 19_

  - [x] 6.9 Create article public views and templates
    - Implement `ArticleListView` for public site with pagination
    - Implement `ArticleDetailView` with select_related optimization
    - Implement `CategoryArticleListView` for category pages
    - Implement `TagArticleListView` for tag pages
    - Create `templates/articles/list.html` with RTL layout
    - Create `templates/articles/detail.html` rendering sanitized HTML content
    - Create `templates/articles/category.html` and `templates/articles/tag.html`
    - Add lazy loading for images
    - _Requirements: 9, 17, 19_

  - [x] 6.10 Register article models in Django Admin (emergency use)
    - Create `apps/articles/admin.py`
    - Register Article, Category, Tag models
    - Add basic list_display, search_fields, and filters
    - _Requirements: 2_


- [ ] 7. Phase 7: Lead Generation and SEO Completion
  - [x] 7.1 Create lead model
    - Create `apps/leads/` Django app
    - Create `LeadType` choices: REGISTRATION, CONTACT
    - Implement `Lead` model inheriting from `TimestampedModel`
    - Add fields: lead_type, name, email, phone, message
    - Add tracking fields: source_page, referrer
    - Add UTM parameter fields: utm_source, utm_medium, utm_campaign, utm_term, utm_content
    - Add status fields: is_read, notes
    - Add database indexes for created_at, lead_type, is_read
    - _Requirements: 5, 23_

  - [x] 7.2 Create lead form with spam protection
    - Create `apps/leads/forms.py`
    - Implement `LeadForm` with all user-facing fields
    - Add honeypot field for spam protection
    - Add form validation for email and phone
    - Add Arabic labels and help text
    - _Requirements: 5, 18_

  - [x] 7.3 Create lead submission view
    - Implement `LeadSubmitView` handling form submission
    - Extract UTM parameters from request
    - Extract source_page and referrer from request
    - Validate CSRF token
    - Save lead to database
    - Redirect to thank you page
    - _Requirements: 5, 18_

  - [x] 7.4 Create lead email notification signal
    - Create `apps/leads/signals.py`
    - Implement post_save signal for Lead model
    - Send email notification to administrators on new lead
    - Include lead details in email
    - Handle email sending errors gracefully
    - _Requirements: 5_

  - [x] 7.5 Create lead management dashboard views
    - Implement `LeadListView` with filters: type, date range, search, read status
    - Implement `LeadDetailView` marking lead as read on view
    - Implement `LeadExportView` exporting filtered leads to CSV
    - Add pagination for lead list
    - Add Arabic success/error messages
    - _Requirements: 2, 23_

  - [x] 7.6 Create lead management dashboard templates
    - Create `templates/dashboard/leads/list.html` with filters and pagination
    - Create `templates/dashboard/leads/detail.html` showing all lead information
    - Add export button linking to CSV export
    - Style with Tailwind CSS for RTL layout
    - _Requirements: 2, 23_

  - [x] 7.7 Create lead form component for public site
    - Create `templates/components/lead_form.html` reusable component
    - Add honeypot field (hidden)
    - Add CSRF token
    - Style with Tailwind CSS for RTL layout
    - Add client-side validation using Alpine.js
    - _Requirements: 5, 19_

  - [x] 7.8 Register lead models in Django Admin (emergency use)
    - Create `apps/leads/admin.py`
    - Register Lead model
    - Add basic list_display, search_fields, and filters
    - _Requirements: 2_

  - [x] 7.9 Complete SEO sitemap generation
    - Update `apps/seo/sitemaps.py` (created in Phase 1)
    - Implement sitemaps for: University, Institute, Major, Article
    - Filter by publish_status and sitemap_include
    - Configure sitemap URL in root URLconf
    - _Requirements: 10_

  - [x] 7.10 Create SEO template tags
    - Create `apps/seo/templatetags/seo_tags.py`
    - Implement `render_meta_tags` template tag
    - Implement `render_og_tags` template tag
    - Implement `render_twitter_card_tags` template tag
    - Implement `render_canonical_tag` template tag
    - _Requirements: 10_

  - [x] 7.11 Create SEO schema markup generation
    - Update `apps/seo/schema.py` (created in Phase 1)
    - Implement `generate_organization_schema()` function
    - Implement `generate_article_schema()` function
    - Implement `generate_faq_schema()` function
    - Return JSON-LD formatted schema
    - _Requirements: 10_

  - [x] 7.12 Create breadcrumb template tag
    - Create `apps/seo/templatetags/breadcrumbs.py`
    - Implement `render_breadcrumbs` template tag
    - Generate breadcrumb navigation based on current page
    - Include schema markup for breadcrumbs
    - Style with Tailwind CSS for RTL layout
    - _Requirements: 10_


- [ ] 8. Phase 8: Search, Frontend, RTL, Performance, and Deployment
  - [x] 8.1 Create search functionality
    - Create `apps/search/` Django app
    - Create `apps/search/forms.py` with `SearchForm`
    - Create `apps/search/utils.py` with search query builder using Django ORM Q objects
    - Implement `SearchView` searching across University, Institute, Major, Article
    - Search in fields: name/title, slug, description, category
    - Create `templates/search/results.html` with pagination
    - Add Arabic labels and messages
    - _Requirements: 13_

  - [x] 8.2 Create base public template with RTL layout
    - Create `templates/base.html` with RTL direction
    - Include SEO meta tags using template tags
    - Include schema markup
    - Include Tailwind CSS with RTL configuration
    - Include Alpine.js for interactive components
    - Add Google Analytics placeholder (if needed)
    - _Requirements: 1, 10, 19_

  - [x] 8.3 Create public header and footer components
    - Create `templates/components/header.html` with navigation
    - Create `templates/components/footer.html` with links
    - Add mobile-responsive navigation menu using Alpine.js
    - Style with Tailwind CSS for RTL layout
    - Add search form in header
    - _Requirements: 1, 19_

  - [x] 8.4 Create homepage view and template
    - Implement `HomeView` in `apps/core/views.py`
    - Fetch featured content: universities, institutes, majors, articles
    - Create `templates/home.html` with hero section and content sections
    - Add lead form component
    - Style with Tailwind CSS for RTL layout
    - _Requirements: 1, 19_

  - [x] 8.5 Implement advanced image optimization
    - Update `apps/core/utils.py` image processing utilities (basic validation already done in Phase 1)
    - Implement advanced image compression
    - Generate WebP versions of images
    - Serve WebP with fallback to original format
    - _Requirements: 16_

  - [x] 8.6 Implement lazy loading for images
    - Add `loading="lazy"` attribute to all image tags in templates
    - Implement intersection observer for below-fold images
    - Add placeholder images for lazy-loaded content
    - _Requirements: 16, 17_

  - [x] 8.7 Optimize database queries
    - Add `select_related()` for ForeignKey relationships in all views
    - Add `prefetch_related()` for ManyToMany relationships in all views
    - Review and optimize N+1 query problems
    - Add database indexes where needed
    - _Requirements: 17_

  - [x] 8.8 Implement pagination for all list views
    - Add pagination to all public list views (20 items per page)
    - Add pagination to all dashboard list views (20-50 items per page)
    - Create `templates/components/pagination.html` reusable component
    - Style pagination with Tailwind CSS for RTL layout
    - _Requirements: 17_

  - [x] 8.9 Minify CSS and JavaScript for production
    - Configure CSS minification in Tailwind build process
    - Configure JavaScript minification
    - Set up collectstatic command for production
    - Configure static file caching headers
    - _Requirements: 17, 20_

  - [x] 8.10 Configure file-based caching
    - Configure Django file-based cache in settings
    - Add cache configuration for production environment
    - Document optional Redis configuration
    - _Requirements: 17, 20_

  - [x] 8.11 Implement security hardening
    - Set DEBUG=False in production settings
    - Configure ALLOWED_HOSTS
    - Set SECURE_SSL_REDIRECT=True
    - Set SESSION_COOKIE_SECURE=True
    - Set CSRF_COOKIE_SECURE=True
    - Set SECURE_HSTS_SECONDS
    - Configure SECURE_CONTENT_TYPE_NOSNIFF
    - Configure X_FRAME_OPTIONS
    - _Requirements: 18, 20_

  - [x] 8.12 Test cPanel deployment
    - Test passenger_wsgi.py configuration
    - Test static file serving
    - Test media file uploads and serving
    - Test MySQL/MariaDB connection
    - Test file-based caching
    - Verify SSL certificate configuration
    - _Requirements: 20_

  - [x] 8.13 Create deployment documentation
    - Document cPanel deployment steps
    - Document environment variable configuration
    - Document database setup and migration
    - Document static file collection
    - Document backup procedures
    - Create README.md with project overview
    - _Requirements: 20_

  - [x] 8.14 Final testing and quality assurance
    - Test all CRUD operations in Custom Dashboard
    - Test all public pages for RTL layout correctness
    - Test lead form submission and email notifications
    - Test redirect functionality
    - Test search functionality
    - Test SEO meta tags and schema markup
    - Test mobile responsiveness on various devices
    - Test image lazy loading and optimization
    - Verify all Arabic text displays correctly
    - _Requirements: 1, 19_


## Notes

- All tasks reference specific requirements for traceability
- The platform uses Python with Django framework
- Custom Dashboard is the primary admin interface (Django Admin for emergency use only)
- **Custom HTML Editor V1 Scope**: BASIC editor with Bold, Italic, Headers (H2-H4), Lists (UL/OL), Links, Images ONLY. Video embeds, tables, and CTA blocks are future enhancements.
- Universities, Institutes, and Majors use Structured Template Editors with Simple Rich Text Widget
- **registration_section field**: CRITICAL - Must be explicitly added to both University and Institute models, forms (with SimpleRichTextWidget), and templates
- Arabic RTL layout is native throughout the platform
- Security measures (CSRF, XSS protection, input sanitization) are applied across all features
- **Image Optimization**: Basic validation and resize in Phase 1 (max size, basic resize on upload), advanced optimization (WebP, compression) in Phase 8
- **User Management**: Moved to Phase 2 for early access (Super Admin can create users right after dashboard setup)
- **Redirects**: Moved to Phase 2 (right after slug system is established in content models) - critical for SEO preservation
- **SEO**: Base structure and sitemap foundation in Phase 1, completion in Phase 7
- **Phase 7 is lighter**: Only Leads and SEO completion (Search moved to Phase 8)
- **Search**: Moved to Phase 8 for cleaner phase organization
- Performance optimization focuses on: image optimization, query optimization, pagination, lazy loading, CSS/JS minification
- cPanel deployment compatibility is maintained throughout all phases
- Each phase builds incrementally on previous phases
- Testing and validation occur at the end of each phase

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.3"] },
    { "id": 1, "tasks": ["1.2", "1.4", "1.5", "1.6"] },
    { "id": 2, "tasks": ["2.1", "2.2"] },
    { "id": 3, "tasks": ["2.3", "2.4", "2.5"] },
    { "id": 4, "tasks": ["2.6", "2.8"] },
    { "id": 5, "tasks": ["2.7", "2.9"] },
    { "id": 6, "tasks": ["2.10", "2.11"] },
    { "id": 7, "tasks": ["3.1", "3.2", "3.3", "3.4"] },
    { "id": 8, "tasks": ["3.5", "3.6", "3.7"] },
    { "id": 9, "tasks": ["3.8", "3.9", "3.10"] },
    { "id": 10, "tasks": ["4.1", "4.2"] },
    { "id": 11, "tasks": ["4.3", "4.4"] },
    { "id": 12, "tasks": ["4.5", "4.6", "4.7"] },
    { "id": 13, "tasks": ["5.1", "5.2"] },
    { "id": 14, "tasks": ["5.3", "5.4"] },
    { "id": 15, "tasks": ["5.5", "5.6", "5.7"] },
    { "id": 16, "tasks": ["6.1", "6.2"] },
    { "id": 17, "tasks": ["6.3", "6.4"] },
    { "id": 18, "tasks": ["6.5", "6.6", "6.7"] },
    { "id": 19, "tasks": ["6.8", "6.9", "6.10"] },
    { "id": 20, "tasks": ["7.1", "7.2"] },
    { "id": 21, "tasks": ["7.3", "7.4", "7.9"] },
    { "id": 22, "tasks": ["7.5", "7.6", "7.7", "7.10", "7.11"] },
    { "id": 23, "tasks": ["7.8", "7.12"] },
    { "id": 24, "tasks": ["8.1", "8.2"] },
    { "id": 25, "tasks": ["8.3", "8.4", "8.5"] },
    { "id": 26, "tasks": ["8.6", "8.7", "8.8"] },
    { "id": 27, "tasks": ["8.9", "8.10", "8.11"] },
    { "id": 28, "tasks": ["8.12", "8.13"] },
    { "id": 29, "tasks": ["8.14"] }
  ]
}
```
