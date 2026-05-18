# Requirements Document

## Introduction

Science Gates (بوابات العلوم للدراسة في ماليزيا) is a professional educational content platform focused on Malaysian universities, institutes, study majors, and educational articles. The platform serves as a structured SEO-optimized website built with Django, MySQL, Django Templates, Tailwind CSS, and Alpine.js, designed for cPanel deployment. Version 1 will be Arabic-only with RTL support, with architecture designed to support future multilingual expansion without rebuilding. The system provides comprehensive SEO capabilities, lead generation, and content management through a professional Custom Dashboard across four core content types: Universities, Institutes, Majors, and Articles.

## Glossary

- **Platform**: The Science Gates web application system
- **Content_Admin**: Administrative user responsible for managing educational content
- **SEO_System**: The subsystem responsible for search engine optimization features
- **Lead_Form**: User-facing form for registration or contact requests
- **Content_Type**: One of the four core entities (University, Institute, Major, Article)
- **Custom_Dashboard**: Professional custom-built admin interface for all content and lead management
- **Custom_HTML_Editor**: Custom-built HTML editor integrated into Custom_Dashboard for article content
- **Redirect_Manager**: System component managing 301 redirects for URL preservation
- **Faculty**: Academic division within a university containing programs
- **Program**: Educational offering within a faculty with duration and fees
- **Course**: Educational offering within an institute
- **Dynamic_Table**: Structured data table with configurable rows and columns
- **SEO_Fields**: Collection of metadata fields for search engine optimization
- **Django_Admin**: Django's built-in admin interface available for emergency or technical use only
- **Publish_Status**: Binary state indicating whether content is visible to public users (Published or Unpublished)
- **Slug**: URL-friendly identifier supporting Arabic characters for content routing

---

## Requirements

### Requirement 1: Arabic RTL Language Support

**User Story:** As a visitor, I want to view the website in Arabic with proper RTL layout, so that I can consume content naturally in my native language.

#### Acceptance Criteria

1. THE Platform SHALL display all content in Arabic language
2. THE Platform SHALL apply RTL (right-to-left) text direction throughout the interface
3. THE Platform SHALL apply correct text alignment for Arabic RTL content
4. THE Platform SHALL render tables, lists, forms, and accordions with correct RTL directionality
5. THE Platform SHALL maintain RTL layout correctness on all device sizes
6. THE Platform SHALL be architecturally prepared for future multilingual expansion without requiring structural changes

### Requirement 2: Custom Dashboard Content Management

**User Story:** As a Content_Admin, I want to manage all content through a professional custom-built dashboard in Arabic, so that I can use an intuitive, organized, and purpose-built administration system.

#### Acceptance Criteria

1. THE Platform SHALL provide a Custom_Dashboard as the primary interface for all content and lead management
2. THE Custom_Dashboard SHALL be built specifically for the Platform (not Django_Admin)
3. THE Custom_Dashboard SHALL provide Arabic RTL interface throughout
4. THE Custom_Dashboard SHALL provide interfaces for managing University, Institute, Major, and Article content
5. THE Custom_Dashboard SHALL provide interfaces for managing Faculty, Program, Course, and FAQ entities
6. THE Custom_Dashboard SHALL provide interfaces for managing categories, tags, and redirects
7. THE Custom_Dashboard SHALL provide interfaces for managing leads with filtering and export capabilities
8. THE Custom_Dashboard SHALL provide interfaces for managing SEO_Fields for all content types
9. THE Custom_Dashboard SHALL provide interfaces for managing user accounts and role assignments
10. THE Custom_Dashboard SHALL provide organized navigation and intuitive user experience
11. THE Platform SHALL maintain Django_Admin for emergency or technical use only
12. THE Custom_Dashboard SHALL support inline editing for related entities (e.g., Faculty within University)

### Requirement 3: Custom HTML Editor Integration for Articles

**User Story:** As a Content_Admin, I want to create and edit article and news content using a flexible custom-built HTML editor within the dashboard, so that I can format content safely without relying on third-party editors.

#### Acceptance Criteria

1. THE Platform SHALL provide a Custom_HTML_Editor built specifically for the Custom_Dashboard
2. THE Platform SHALL NOT use CKEditor, TinyMCE, or other third-party WYSIWYG editors
3. THE Custom_HTML_Editor SHALL be used ONLY for Article and News Content_Type entities
4. THE Custom_HTML_Editor SHALL support headings (H1-H6)
5. THE Custom_HTML_Editor SHALL support paragraphs with text formatting (bold, italic, underline)
6. THE Custom_HTML_Editor SHALL support image insertion with alt text
7. THE Custom_HTML_Editor SHALL support video embedding
8. THE Custom_HTML_Editor SHALL support table creation and editing
9. THE Custom_HTML_Editor SHALL support internal and external link insertion
10. THE Custom_HTML_Editor SHALL support button and CTA block insertion
11. THE Custom_HTML_Editor SHALL support safe HTML blocks for controlled rich content
12. THE Custom_HTML_Editor SHALL support Arabic RTL text entry and editing
13. THE Custom_HTML_Editor SHALL prevent insertion of unsafe scripts and malicious code
14. THE Platform SHALL sanitize HTML output from Custom_HTML_Editor before saving to database or rendering to public
15. THE Custom_HTML_Editor SHALL provide a preview mode showing how content will appear on the public site

### Requirement 4: Structured Template Editors for Content Types

**User Story:** As a Content_Admin, I want to manage Universities, Institutes, and Majors through structured template editors with predefined sections and fields, so that content is consistent, SEO-optimized, design-safe, and easy to manage.

#### Acceptance Criteria

1. THE Platform SHALL provide Structured Template Editors for University, Institute, and Major content types
2. THE Platform SHALL NOT use free-form HTML editors or block editors for University, Institute, and Major content
3. THE Structured Template Editor for University SHALL provide organized sections:
   - Basic information fields: name, slug, logo, main image, location, video URL
   - Rich text fields with simple formatting: description, admission requirements, registration section
   - Structured data management: Faculties (managed separately), Programs (within Faculty), FAQ (inline formset)
   - SEO fields section
4. THE Structured Template Editor for Institute SHALL provide organized sections:
   - Basic information fields: name, slug, main image
   - Rich text fields with simple formatting: description, registration requirements, registration section
   - Structured data management: Courses (inline formset)
   - SEO fields section
5. THE Structured Template Editor for Major SHALL provide organized sections:
   - Basic information fields: name, slug, main image
   - Rich text fields with simple formatting: description, why study this major, how to apply
   - Quick information fields: study duration, tuition fees, study language, practical training, career opportunities
   - Structured data management: Subjects table, Salary table, Countries table (inline formsets)
   - University relationships: best universities, cheap universities (many-to-many selection)
   - SEO fields section
6. THE Rich text fields within Structured Template Editors SHALL use simple, safe HTML formatting only (bold, italic, headings H2-H4, lists, links)
7. THE Rich text fields within Structured Template Editors SHALL NOT provide full block editor capabilities or complex formatting options
8. THE Platform SHALL sanitize all rich text field output to prevent XSS attacks
9. THE Structured Template Editors SHALL ensure consistent page structure across all content of the same type
10. THE Structured Template Editors SHALL prevent design breakage by limiting formatting options to predefined safe elements
11. THE Structured Template Editors SHALL organize fields into logical sections with clear labels in Arabic
12. THE Structured Template Editors SHALL validate required fields before allowing content save

### Requirement 5: Lead Form Submission and Storage

**User Story:** As a visitor, I want to submit registration or contact requests, so that I can inquire about educational opportunities.

#### Acceptance Criteria

1. THE Platform SHALL provide two Lead_Form types: Registration Request and Contact Request
2. WHEN a user submits a Lead_Form, THE Platform SHALL store the submission in the database
3. WHEN a user submits a Lead_Form, THE Platform SHALL record the source page URL
4. WHEN a user submits a Lead_Form, THE Platform SHALL record the submission timestamp
5. WHEN a user submits a Lead_Form, THE Platform SHALL record the HTTP referrer if available
6. WHEN a user submits a Lead_Form, THE Platform SHALL record UTM parameters if present in the URL
7. THE Platform SHALL send email notifications to administrators when a Lead_Form is submitted
8. THE Platform SHALL display submitted leads in Custom_Dashboard
9. THE Platform SHALL protect Lead_Form submissions with anti-spam measures (honeypot or reCAPTCHA)
10. THE Platform SHALL apply CSRF protection to all Lead_Form submissions

### Requirement 6: University Content Structure

**User Story:** As a Content_Admin, I want to create structured university pages with faculties and programs, so that visitors can explore educational offerings.

#### Acceptance Criteria

1. THE Platform SHALL support University Content_Type with name, slug, logo, main image, description, location, video URL, admission requirements, and SEO_Fields
2. THE Platform SHALL allow each University to contain multiple Faculty entities
3. THE Platform SHALL allow each Faculty to contain multiple Program entities
4. THE Platform SHALL store Faculty with name and sort order
5. THE Platform SHALL store Program with name, duration, tuition fees, and sort order
6. THE Platform SHALL allow each University to contain multiple FAQ entries with question, answer, and sort order
7. THE Platform SHALL display University content in the template order: name, logo, main image, description, location, video, admission requirements, registration section, faculties and programs, FAQ, registration steps
8. THE Platform SHALL support accordion UI for FAQ sections using Alpine.js
9. THE Platform SHALL apply SEO_Fields to University pages

### Requirement 7: Institute Content Structure

**User Story:** As a Content_Admin, I want to create structured institute pages with courses, so that visitors can explore vocational and training programs.

#### Acceptance Criteria

1. THE Platform SHALL support Institute Content_Type with name, slug, main image, description, registration requirements, and SEO_Fields
2. THE Platform SHALL allow each Institute to contain multiple Course entities
3. THE Platform SHALL store Course with name, duration, fees, description, and notes
4. THE Platform SHALL display Institute content in the template order: name, image, description, registration requirements, courses, registration section
5. THE Platform SHALL apply SEO_Fields to Institute pages

### Requirement 8: Major Content Structure with Dynamic Tables

**User Story:** As a Content_Admin, I want to create major pages with structured information and dynamic tables, so that visitors can understand study programs comprehensively.

#### Acceptance Criteria

1. THE Platform SHALL support Major Content_Type with name, slug, main image, description, study duration, and SEO_Fields
2. THE Platform SHALL support quick information fields: study duration, tuition fees, study language, practical training, career opportunities
3. THE Platform SHALL support a Subjects Dynamic_Table with columns: Academic Year, Subjects
4. THE Platform SHALL support a Salary Dynamic_Table with columns: Job Title, Average Monthly Salary
5. THE Platform SHALL support a Countries Dynamic_Table with columns: Destination, Study Duration, Annual Fees, Living Cost
6. THE Platform SHALL allow linking Majors to related University entities (best universities)
7. THE Platform SHALL allow linking Majors to related University entities (cheap universities)
8. THE Platform SHALL display Major content in the template order: name, image, description, quick information, why study this major, study duration, best universities, cheap universities, subjects table, career & salary table, countries table, how to apply
9. THE Platform SHALL apply SEO_Fields to Major pages

### Requirement 9: Article and News System

**User Story:** As a Content_Admin, I want to create flexible articles with categories and tags, so that I can publish educational news and content.

#### Acceptance Criteria

1. THE Platform SHALL support Article Content_Type with title, slug, featured image, category, tags, author, publish date, Rich_Editor content, and SEO_Fields
2. THE Platform SHALL support multiple categories for organizing articles
3. THE Platform SHALL support multiple tags for article classification
4. THE Platform SHALL allow articles to link to related University, Institute, and Major entities
5. THE Platform SHALL display article content rendered from Rich_Editor output
6. THE Platform SHALL apply SEO_Fields to Article pages
7. THE Platform SHALL sanitize article HTML content to prevent XSS attacks

### Requirement 10: SEO System Implementation

**User Story:** As a Content_Admin, I want comprehensive SEO features for all content types manageable through the custom dashboard, so that the platform ranks well in search engines.

#### Acceptance Criteria

1. THE SEO_System SHALL provide SEO_Fields: meta title, meta description, focus keyword, slug, canonical URL, Open Graph title, Open Graph description, Open Graph image, robots settings, sitemap inclusion
2. THE SEO_System SHALL make SEO_Fields editable through Custom_Dashboard for all content types
3. THE SEO_System SHALL generate an XML sitemap including all published content
4. THE SEO_System SHALL generate a robots.txt file
5. THE SEO_System SHALL render breadcrumb navigation on content pages
6. THE SEO_System SHALL render Organization Schema markup
7. THE SEO_System SHALL render Article Schema markup for article pages
8. THE SEO_System SHALL render FAQ Schema markup where applicable
9. THE SEO_System SHALL render canonical link tags on all content pages
10. THE SEO_System SHALL render Open Graph meta tags on all content pages
11. THE SEO_System SHALL render Twitter Card meta tags on all content pages
12. THE SEO_System SHALL apply SEO_Fields to University, Institute, Major, and Article Content_Type entities

### Requirement 11: URL Slug Management with Arabic Support

**User Story:** As a Content_Admin, I want to manage URL slugs for all content with Arabic support and automatic redirect creation, so that I can maintain SEO-friendly URLs while preserving old links.

#### Acceptance Criteria

1. THE Platform SHALL support Arabic characters in URL slugs for all Content_Type entities
2. THE Platform SHALL allow Content_Admin to manually edit slug values through Custom_Dashboard
3. THE Platform SHALL provide automatic slug generation from content title/name when creating new content
4. THE Platform SHALL prevent duplicate slug values within each Content_Type
5. THE Platform SHALL preserve existing URLs where possible to minimize redirect necessity
6. WHEN a Content_Admin changes the slug of published content, THE Platform SHALL display a warning in Custom_Dashboard
7. WHEN a Content_Admin changes the slug of published content, THE Platform SHALL offer to automatically create a 301 redirect from old slug to new slug
8. THE Platform SHALL validate slug format to ensure URL compatibility
9. THE Platform SHALL transliterate or sanitize slug input to ensure web server compatibility while preserving Arabic characters

### Requirement 12: URL Redirect Management

**User Story:** As a Content_Admin, I want to manage 301 redirects for changed URLs, so that old links continue to work and SEO value is preserved.

#### Acceptance Criteria

1. THE Platform SHALL provide a Redirect_Manager in Custom_Dashboard
2. THE Redirect_Manager SHALL store redirects with old URL, new URL, active status, and notes
3. WHEN a user requests a URL matching an active redirect old URL, THE Platform SHALL respond with HTTP 301 status and redirect to the new URL
4. THE Redirect_Manager SHALL allow Content_Admin to create, edit, and deactivate redirects through Custom_Dashboard
5. THE Platform SHALL preserve existing URLs where possible to minimize redirect necessity

### Requirement 13: Simple Search Functionality

**User Story:** As a visitor, I want to search for universities, institutes, majors, and articles in Arabic, so that I can quickly find relevant information.

#### Acceptance Criteria

1. THE Platform SHALL provide a search interface accessible from all pages
2. WHEN a user submits a search query, THE Platform SHALL search across University, Institute, Major, and Article Content_Type entities using Django ORM
3. THE Platform SHALL match search queries against title, slug, description, and category fields
4. THE Platform SHALL display search results with title, excerpt, and link to full content
5. THE Platform SHALL paginate search results when result count exceeds 20 items
6. THE Platform SHALL support Arabic search queries
7. THE Platform SHALL NOT use Elasticsearch, Meilisearch, or other advanced search infrastructure in Version 1

### Requirement 14: Simple Content Publishing Control

**User Story:** As a Content_Admin, I want to control whether content is visible to the public using a simple two-state system, so that I can prepare content before publishing without complex workflows.

#### Acceptance Criteria

1. THE Platform SHALL provide Publish_Status field for all Content_Type entities with exactly two states: Published and Unpublished
2. THE Platform SHALL NOT implement Draft, Review, Approval, or other complex editorial workflow states
3. WHEN content Publish_Status is Unpublished, THE Platform SHALL exclude it from public-facing pages
4. WHEN content Publish_Status is Unpublished, THE Platform SHALL exclude it from search results
5. WHEN content Publish_Status is Unpublished, THE Platform SHALL exclude it from sitemaps
6. WHEN content Publish_Status is Published, THE Platform SHALL include it in public-facing pages, search results, and sitemaps
7. THE Platform SHALL display Publish_Status in Custom_Dashboard for all content

### Requirement 15: Simple User Role Management

**User Story:** As a system administrator, I want to assign simple permission levels to users through the custom dashboard, so that content management is properly controlled without enterprise-level complexity.

#### Acceptance Criteria

1. THE Platform SHALL support three user roles: Super Admin, Content Admin, and SEO Admin
2. THE Platform SHALL NOT implement complex enterprise permission systems or approval workflows
3. THE Platform SHALL grant Super Admin full access to all Custom_Dashboard features
4. THE Platform SHALL grant Content Admin access to create, edit, and delete content entities through Custom_Dashboard
5. THE Platform SHALL grant SEO Admin access to edit SEO_Fields for all content through Custom_Dashboard
6. THE Platform SHALL restrict access to Custom_Dashboard based on user role
7. THE Platform SHALL require authentication for all Custom_Dashboard access
8. THE Platform SHALL provide user management interface in Custom_Dashboard for Super Admin
9. THE Platform SHALL maintain Django_Admin access for emergency or technical use only

### Requirement 16: Image Handling and Optimization

**User Story:** As a Content_Admin, I want uploaded images to be automatically optimized, so that page load times remain fast.

#### Acceptance Criteria

1. WHEN a Content_Admin uploads an image, THE Platform SHALL enforce a maximum file size limit
2. WHEN an uploaded image exceeds maximum dimensions, THE Platform SHALL automatically resize it
3. THE Platform SHALL compress uploaded images to reduce file size
4. WHERE WebP format is supported by the browser, THE Platform SHALL serve images in WebP format
5. THE Platform SHALL require alt text for all uploaded images
6. THE Platform SHALL store uploaded images in the media directory
7. THE Platform SHALL implement lazy loading for images on content pages

### Requirement 17: Performance Optimization Without Complex Caching

**User Story:** As a visitor, I want pages to load quickly through basic optimization techniques, so that I can access information without delay.

#### Acceptance Criteria

1. THE Platform SHALL paginate content lists when item count exceeds 20
2. THE Platform SHALL implement lazy loading for images below the fold
3. THE Platform SHALL minify CSS and JavaScript assets in production
4. THE Platform SHALL optimize database queries to avoid N+1 query problems using select_related and prefetch_related
5. THE Platform SHALL NOT require Redis or complex caching infrastructure in Version 1
6. WHERE basic caching is needed, THE Platform MAY use Django file-based cache or database cache
7. WHERE Redis is available in the hosting environment, THE Platform MAY optionally use Redis for caching
8. THE Platform SHALL serve static assets from the static directory with appropriate cache headers
9. THE Platform SHALL focus performance optimization on: image optimization, CSS/JS minification, pagination, query optimization, and lazy loading

### Requirement 18: Security Implementation

**User Story:** As a system administrator, I want the platform to be secure against common web vulnerabilities, so that user data and content are protected.

#### Acceptance Criteria

1. THE Platform SHALL apply CSRF protection to all form submissions
2. THE Platform SHALL sanitize all Custom_HTML_Editor output to prevent XSS attacks
3. THE Platform SHALL use parameterized database queries to prevent SQL injection
4. THE Platform SHALL enforce strong password requirements for Custom_Dashboard users
5. THE Platform SHALL disable debug mode in production environment
6. THE Platform SHALL use secure cookies with HttpOnly and Secure flags in production
7. THE Platform SHALL rate-limit Lead_Form submissions to prevent abuse
8. THE Platform SHALL validate and sanitize all user input before processing
9. THE Platform SHALL protect Custom_Dashboard with authentication and role-based access control

### Requirement 19: Mobile Responsiveness with RTL Support

**User Story:** As a mobile visitor, I want the Arabic website to display correctly on my device, so that I can access content on any screen size with proper RTL layout.

#### Acceptance Criteria

1. THE Platform SHALL render all pages responsively using mobile-first design principles
2. THE Platform SHALL ensure all interactive elements are touch-friendly on mobile devices
3. THE Platform SHALL render tables responsively with horizontal scrolling or stacking on small screens
4. THE Platform SHALL render navigation menus appropriately for mobile devices using Alpine.js
5. THE Platform SHALL maintain RTL layout correctness on mobile devices for Arabic content
6. THE Platform SHALL optimize images for mobile viewport sizes
7. THE Platform SHALL ensure forms, accordions, and interactive components work correctly on mobile with RTL layout
8. THE Custom_Dashboard SHALL be responsive and usable on tablet devices

### Requirement 20: cPanel Deployment Compatibility

**User Story:** As a system administrator, I want to deploy the platform on cPanel hosting, so that I can use affordable shared hosting infrastructure.

#### Acceptance Criteria

1. THE Platform SHALL include a passenger_wsgi.py file for cPanel Python App deployment
2. THE Platform SHALL use MySQL or MariaDB as the database backend
3. THE Platform SHALL store media files in a local media directory accessible via cPanel
4. THE Platform SHALL use file-based caching or database caching compatible with cPanel environments
5. THE Platform SHALL provide a requirements.txt file listing all Python dependencies
6. THE Platform SHALL support SSL certificate configuration via cPanel
7. THE Platform SHALL use Django's collectstatic command for static file management compatible with cPanel

### Requirement 21: Incremental Development Phases

**User Story:** As a project stakeholder, I want the platform built in incremental phases, so that progress can be validated and adjusted throughout development.

#### Acceptance Criteria

1. THE Platform SHALL be developed across 8 sequential phases: Foundation, Universities, Institutes, Majors, Articles, SEO/Search/Redirects, Frontend/RTL/Performance, Deployment
2. WHEN Phase 1 is complete, THE Platform SHALL have working Django project, MySQL connection, Custom_Dashboard foundation, and cPanel-compatible structure
3. WHEN Phase 2 is complete, THE Platform SHALL have complete University system with Faculty, Program, and FAQ functionality
4. WHEN Phase 3 is complete, THE Platform SHALL have complete Institute system with Course functionality
5. WHEN Phase 4 is complete, THE Platform SHALL have complete Major system with Dynamic_Table functionality
6. WHEN Phase 5 is complete, THE Platform SHALL have complete Article system with Custom_HTML_Editor and categorization
7. WHEN Phase 6 is complete, THE Platform SHALL have complete SEO_System, search functionality, and Redirect_Manager
8. WHEN Phase 7 is complete, THE Platform SHALL have responsive frontend with RTL support and performance optimizations
9. WHEN Phase 8 is complete, THE Platform SHALL be deployed to production with SSL, backups, and security hardening

### Requirement 22: Content Relationships and Internal Linking

**User Story:** As a visitor, I want to discover related content across different content types, so that I can explore connected educational information.

#### Acceptance Criteria

1. THE Platform SHALL allow University entities to link to related Major entities
2. THE Platform SHALL allow University entities to link to related Article entities
3. THE Platform SHALL allow Institute entities to link to related Article entities
4. THE Platform SHALL allow Major entities to link to related University entities (best universities)
5. THE Platform SHALL allow Major entities to link to related University entities (cheap universities)
6. THE Platform SHALL allow Major entities to link to related Article entities
7. THE Platform SHALL allow Article entities to link to related University, Institute, and Major entities
8. THE Platform SHALL display related content links on content detail pages
9. THE Platform SHALL generate internal links using correct slugs and URL patterns

### Requirement 23: Simple Lead Management and Statistics

**User Story:** As a Content_Admin, I want to view submitted leads and basic statistics in the custom dashboard, so that I can follow up on inquiries without complex analytics dashboards.

#### Acceptance Criteria

1. THE Custom_Dashboard SHALL display all submitted Lead_Form entries
2. THE Custom_Dashboard SHALL display lead submission details: name, email, phone, message, source page, timestamp, referrer, UTM parameters
3. THE Custom_Dashboard SHALL allow filtering leads by form type (Registration Request or Contact Request)
4. THE Custom_Dashboard SHALL allow filtering leads by submission date range
5. THE Custom_Dashboard SHALL allow searching leads by name, email, or phone
6. THE Custom_Dashboard SHALL allow exporting leads to CSV format
7. THE Custom_Dashboard SHALL display three simple statistics: total lead count, lead count by form type, and lead count for current month
8. THE Platform SHALL NOT implement complex analytics dashboards, charts, or advanced reporting in Version 1

---

## Implementation Notes

- All requirements follow EARS patterns for clarity and testability
- Requirements are solution-free, focusing on what the system shall do rather than how
- Technical implementation details are deferred to the design phase
- Requirements support incremental development across 8 phases
- All content types share common SEO, publishing, and relationship capabilities
- Security and performance requirements apply globally across all features
- Version 1 is Arabic-only with architecture prepared for future multilingual expansion
- Custom Dashboard is the primary interface for all content and lead management
- Django Admin is maintained for emergency or technical use only (not primary interface)
- **Content Editing Approach:**
  - **Universities, Institutes, and Majors use Structured Template Editors** with predefined sections and fields
  - **Only Articles use the flexible Custom HTML Editor** for free-form content creation
  - Rich text fields in structured templates use simple, safe HTML formatting only (bold, italic, headings, lists, links)
  - This approach ensures content consistency, SEO optimization, design safety, and ease of use
  - Structured templates prevent design breakage and maintain uniform page structure
- Custom HTML Editor is built specifically for the platform (no CKEditor or TinyMCE)
- URL slugs support Arabic characters with automatic redirect creation on slug changes
- Redis is optional and not required; file-based or database caching is the baseline
- No complex caching infrastructure in Version 1; focus on image optimization, CSS/JS minification, pagination, query optimization
- Search uses Django ORM only (no Elasticsearch or advanced search infrastructure)
- Publishing workflow is simple: Published/Unpublished only (no complex editorial workflows)
- Lead statistics are basic: total count, count by type, and current month count (no complex analytics)
- User roles (Super Admin, Content Admin, SEO Admin) work within Custom Dashboard
- Technology stack is fixed: Django + MySQL/MariaDB + Django Templates + Tailwind CSS + Alpine.js + cPanel
- No overengineering: the platform is sized appropriately for ~200 articles and moderate content volume
- No Wagtail, no React, no complex workflows
