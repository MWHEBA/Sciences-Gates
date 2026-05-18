# Science Gates - Study in Malaysia Platform

A comprehensive Django-based platform for studying in Malaysia. Built with Django 4.2.11 LTS, MySQL/MariaDB, and full Arabic/RTL support.

**Status**: ✅ Phase 1 Complete | Ready for Phase 2 Development

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Setup Instructions](#setup-instructions)
- [Deployment](#deployment)
- [Architecture](#architecture)
- [Phase 1 Completion](#phase-1-completion)
- [Phase 2 Roadmap](#phase-2-roadmap)
- [Development Checklist](#development-checklist)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MySQL/MariaDB 5.7+
- Git

### 1. Clone & Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 4. Create Database
```sql
CREATE DATABASE science_gates CHARACTER SET utf8mb4;
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Start Development Server
```bash
python manage.py runserver
```

### 8. Access Admin
- URL: http://localhost:8000/admin/
- Username & Password: (created in step 6)

---

## 📁 Project Structure

```
science_gates/
├── config/                          # Django configuration
│   ├── settings/
│   │   ├── base.py                 # Common settings
│   │   ├── local.py                # Development settings
│   │   ├── production.py           # Production settings
│   │   └── __init__.py
│   ├── urls.py                     # URL routing
│   ├── wsgi.py                     # WSGI application
│   ├── asgi.py                     # ASGI application
│   └── __init__.py
│
├── apps/                            # 9 Django Applications
│   ├── core/                        # Abstract base models
│   │   ├── models.py               # TimeStamped, Slug, Publishable, Sortable
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── tests.py
│   │   ├── apps.py
│   │   └── __init__.py
│   │
│   ├── seo/                         # SEO functionality
│   │   ├── models.py               # SEO model with 10 fields
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── tests.py
│   │   ├── apps.py
│   │   └── __init__.py
│   │
│   ├── universities/                # Universities management
│   ├── institutes/                  # Institutes management
│   ├── majors/                      # Majors/specializations
│   ├── articles/                    # Blog/articles
│   ├── leads/                       # Lead capture
│   ├── search/                      # Search functionality
│   ├── redirects/                   # URL redirects
│   └── __init__.py
│
├── templates/                       # RTL-ready templates
│   ├── base.html
│   └── partials/
│
├── static/                          # Static files
│   ├── css/
│   │   └── main.css                # RTL support
│   ├── js/
│   │   └── main.js
│   └── images/
│
├── media/                           # User-uploaded files
│
├── manage.py                        # Django management script
├── passenger_wsgi.py                # cPanel Passenger WSGI entry point
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── setup.bat                        # Windows setup script
├── setup.sh                         # macOS/Linux setup script
└── README.md                        # This file
```

---

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Django | 4.2.11 LTS |
| Database | MySQL/MariaDB | 5.7+ |
| Python | Python | 3.9+ |
| CSS Framework | Tailwind CSS | 3.x |
| RTL Support | tailwindcss-rtl | 0.9.0 |
| Image Processing | Pillow | 10.2.0 |
| Environment | python-decouple | 3.8 |
| Database Driver | mysqlclient | 2.2.0 |
| Build Tool | PostCSS | 8.x |
| Autoprefixer | Autoprefixer | 10.x |

---

## 📦 Setup Instructions

### Development Setup

#### 1. Virtual Environment
```bash
# Create
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Environment Configuration
```bash
# Copy template
cp .env.example .env

# Edit .env with your settings
# Required variables:
# - SECRET_KEY
# - DEBUG
# - ALLOWED_HOSTS
# - DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
```

#### 4. Database Setup
```bash
# Create database
mysql -u root -p
CREATE DATABASE science_gates CHARACTER SET utf8mb4;
EXIT;

# Run migrations
python manage.py migrate
```

#### 5. Create Superuser
```bash
python manage.py createsuperuser
```

#### 6. Run Development Server
```bash
python manage.py runserver
```

### Production Deployment

#### cPanel Deployment
1. Upload project to cPanel public_html or subdirectory
2. Create Python app in cPanel (Python 3.9+)
3. Set WSGI entry point to `passenger_wsgi.py`
4. Configure environment variables in cPanel
5. SSH into server and run migrations:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

#### Other Servers (Gunicorn/uWSGI)
```bash
# Gunicorn
gunicorn config.wsgi:application

# uWSGI
uwsgi --http :8000 --wsgi-file config/wsgi.py --master --processes 4
```

### Tailwind CSS Setup

#### Install Dependencies
```bash
npm install
```

#### Build CSS
```bash
# One-time build
npm run build:css

# Watch for changes during development
npm run watch:css

# Build for production
npm run build
```

#### CSS Files
- **Source**: `static/css/tailwind.css` - Tailwind directives and custom RTL utilities
- **Compiled**: `static/css/tailwind.min.css` - Minified production CSS
- **Configuration**: `tailwind.config.js` - Tailwind configuration with RTL plugin
- **PostCSS**: `postcss.config.js` - PostCSS configuration

#### RTL Support
- Full RTL (right-to-left) support via `tailwindcss-rtl` plugin
- Custom RTL utilities for margins, padding, positioning
- RTL-aware component classes
- All templates use `dir="rtl"` and `lang="ar"`

#### Development Workflow
```bash
# Terminal 1: Django development server
python manage.py runserver

# Terminal 2: Watch Tailwind CSS changes
npm run watch:css
```

#### Production Build
```bash
# Build minified CSS
npm run build:css

# Collect static files
python manage.py collectstatic --noinput
```

---

## 🚀 Deployment

### Quick Deployment Summary

The Science Gates platform is designed for easy deployment on cPanel hosting. For comprehensive deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### cPanel Deployment (Quick Steps)

1. **Upload Files**: Upload project to cPanel public_html
2. **Create Python App**: Use cPanel's "Setup Python App" with Python 3.9+
3. **Configure Environment**: Create `.env` file with production settings
4. **Setup Database**: Create MySQL database and user
5. **Run Migrations**: Execute `python manage.py migrate`
6. **Collect Static Files**: Run `python manage.py collectstatic --noinput`
7. **Configure SSL**: Enable SSL certificate via cPanel AutoSSL
8. **Restart Application**: Restart Python app in cPanel

### Environment Configuration

Create `.env` file with required variables:

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_ENGINE=django.db.backends.mysql
DB_NAME=science_gates_db
DB_USER=science_gates_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Database Setup

```bash
# Create database
mysql -u root -p
CREATE DATABASE science_gates CHARACTER SET utf8mb4;
CREATE USER 'science_gates_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON science_gates.* TO 'science_gates_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Run migrations
python manage.py migrate
```

### Static Files Collection

```bash
# Build CSS
npm run build:css

# Collect static files
python manage.py collectstatic --noinput
```

### Backup Procedures

```bash
# Database backup
mysqldump -u science_gates_user -p science_gates > backup.sql

# Scheduled backup (cron job)
0 2 * * * mysqldump -u science_gates_user -p'password' science_gates | gzip > /home/user/backups/db_$(date +\%Y\%m\%d).sql.gz

# Media files backup
tar -czf media_backup.tar.gz media/
```

### Post-Deployment Verification

- [ ] Application loads at https://yourdomain.com
- [ ] Django admin accessible at https://yourdomain.com/admin/
- [ ] Static files loading (CSS, JS)
- [ ] Media files uploading and serving
- [ ] SSL certificate valid
- [ ] Database connected
- [ ] Email notifications working
- [ ] Logs accessible

### Comprehensive Deployment Guide

For detailed deployment instructions including:
- Pre-deployment checklist
- Step-by-step cPanel setup
- Environment variable configuration
- Database setup and migration
- Static file collection
- Backup procedures
- Security hardening
- Troubleshooting

See **[DEPLOYMENT.md](DEPLOYMENT.md)**

---

## 🏗️ Architecture

### Settings Structure

**base.py** - Common settings for all environments
- Database configuration
- Installed apps
- Middleware
- Static/media files
- Internationalization (Arabic, Malaysia timezone)
- Security settings

**local.py** - Development settings
- DEBUG = True
- Local database configuration
- No SSL enforcement
- Console logging

**production.py** - Production settings
- DEBUG = False
- Security hardening
- SSL/TLS enforcement
- Secure cookies
- Content Security Policy

### Abstract Models (apps/core/models.py)

#### TimeStampedModel
```python
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)
```

#### SlugModel
```python
- slug: SlugField (unique, max_length=255)
```

#### PublishableModel
```python
- is_published: BooleanField (default=False)
```

#### SortableModel
```python
- sort_order: PositiveIntegerField (default=0)
```

### SEO Model (apps/seo/models.py)

10 comprehensive SEO fields:
- `meta_title` - Page title for search engines (60 chars)
- `meta_description` - Page description (160 chars)
- `focus_keyword` - Primary keyword for optimization
- `canonical_url` - Prevent duplicate content issues
- `og_title` - Open Graph title for social sharing
- `og_description` - Open Graph description
- `og_image` - Open Graph image
- `robots_index` - Allow/disallow indexing
- `robots_follow` - Allow/disallow link following
- `sitemap_include` - Include in XML sitemap

### Database Configuration

- **Engine**: MySQL/MariaDB with UTF-8MB4 support
- **Charset**: utf8mb4 for full Unicode support (Arabic, emojis, etc.)
- **Strict Mode**: Enabled for data integrity
- **Connection**: Configured via environment variables

### Internationalization

- **Language**: Arabic (ar)
- **Timezone**: Asia/Kuala_Lumpur (Malaysia)
- **RTL Support**: Full right-to-left support in templates and CSS
- **Database**: UTF-8MB4 for full Unicode support
- **Admin**: All labels in Arabic

### Security Features

**Development (local.py)**
- DEBUG = True (for development only)
- Local database configuration
- No SSL enforcement

**Production (production.py)**
- DEBUG = False
- SECURE_SSL_REDIRECT = True
- SESSION_COOKIE_SECURE = True
- CSRF_COOKIE_SECURE = True
- SECURE_BROWSER_XSS_FILTER = True
- Content Security Policy enabled
- Environment-based configuration

---

## ✅ Phase 1 Completion

### What Was Built

#### Core Infrastructure
- ✅ Django 4.2.11 LTS project structure
- ✅ Modular settings (base, local, production)
- ✅ Environment variable configuration (python-decouple)
- ✅ MySQL/MariaDB database setup with UTF-8MB4
- ✅ Static files configuration (CSS, JS, images)
- ✅ Media files configuration (user uploads)
- ✅ RTL-ready templates with Arabic support
- ✅ Django Admin setup with Arabic labels

#### Applications (9 Apps)
1. ✅ **core** - Abstract base models
2. ✅ **seo** - SEO functionality
3. ✅ **universities** - Universities management
4. ✅ **institutes** - Institutes management
5. ✅ **majors** - Majors/specializations
6. ✅ **articles** - Blog/articles
7. ✅ **leads** - Lead capture
8. ✅ **search** - Search functionality
9. ✅ **redirects** - URL redirects

#### Abstract Models
- ✅ **TimeStampedModel** - created_at, updated_at
- ✅ **SlugModel** - URL-friendly slug field
- ✅ **PublishableModel** - is_published status
- ✅ **SortableModel** - sort_order field
- ✅ **SEOModel** - 10 SEO fields

#### Deployment Ready
- ✅ **passenger_wsgi.py** - cPanel Passenger WSGI entry point
- ✅ **requirements.txt** - All dependencies listed
- ✅ **.env.example** - Environment variables template
- ✅ **setup.bat** - Windows setup script
- ✅ **setup.sh** - macOS/Linux setup script

### Acceptance Criteria - All Met ✅

- [x] Project runs locally
- [x] MySQL connection works
- [x] Django Admin opens
- [x] Static/media settings are correct
- [x] Base models exist (TimeStamped, Slug, Publishable, Sortable)
- [x] SEO abstract model exists with 10 fields
- [x] cPanel passenger_wsgi.py exists
- [x] Project structure is clean and modular
- [x] All 9 apps registered correctly
- [x] Environment variables configured
- [x] RTL support implemented
- [x] Documentation complete

### Deliverables Summary

- Total Files Created: 82
- Total Directories: 18
- Total Lines of Code: 1000+

---

## 🚀 Phase 2 Roadmap

### ✅ COMPLETED TASKS

#### Models Implementation
- [x] **University Model** - Complete with all fields
  - name, slug, logo, main_image, description, location, video_url
  - admission_requirements, registration_section
  - SEO fields, timestamps, publish status
  
- [x] **Faculty Model** - Complete
  - name, university (ForeignKey), sort_order
  - Timestamps, publish status
  
- [x] **Program Model** - Complete
  - program_name, faculty (ForeignKey), duration, tuition_fees
  - sort_order, timestamps, publish status
  
- [x] **FAQ Model** - Complete
  - question, answer, university (ForeignKey), sort_order
  - Timestamps, publish status
  
- [x] **Institute Model** - Complete
  - name, slug, main_image, description, registration_requirements
  - registration_section, SEO fields, timestamps, publish status
  
- [x] **Course Model** - Complete
  - course_name, institute (ForeignKey), duration, fees
  - description, notes, sort_order, timestamps, publish status
  
- [x] **Major Model** - Complete
  - name, slug, main_image, description, quick_info
  - why_study, study_duration, best_universities, cheap_universities
  - SEO fields, timestamps, publish status
  
- [x] **MajorSubject Model** - Complete
  - major (ForeignKey), academic_year, subjects
  - sort_order, timestamps
  
- [x] **MajorSalary Model** - Complete
  - major (ForeignKey), job_title, average_salary
  - sort_order, timestamps
  
- [x] **MajorCountry Model** - Complete
  - major (ForeignKey), destination, duration, annual_fees, living_cost
  - sort_order, timestamps
  
- [x] **Article Model** - Complete
  - title, slug, featured_image, category, tags
  - author, publish_date, content (HTML editor)
  - SEO fields, timestamps, publish status
  
- [x] **Category Model** - Complete
  - name, slug, description, timestamps
  
- [x] **Tag Model** - Complete
  - name, slug, timestamps
  
- [x] **Lead Model** - Complete
  - name, email, phone, message, source_page
  - timestamp, referrer, utm_parameters, status
  
- [x] **Redirect Model** - Complete
  - old_url, new_url, status_code, notes
  - is_active, created_at, updated_at

#### Admin Customization
- [x] University Admin - list_display, list_filter, search_fields, prepopulated_fields
- [x] Faculty Admin - Inline in University
- [x] Program Admin - Inline in Faculty
- [x] FAQ Admin - Inline in University
- [x] Institute Admin - list_display, list_filter, search_fields
- [x] Course Admin - Inline in Institute
- [x] Major Admin - list_display, list_filter, search_fields
- [x] MajorSubject Admin - Inline in Major
- [x] MajorSalary Admin - Inline in Major
- [x] MajorCountry Admin - Inline in Major
- [x] Article Admin - list_display, list_filter, search_fields, rich editor
- [x] Category Admin - list_display, search_fields
- [x] Tag Admin - list_display, search_fields
- [x] Lead Admin - list_display, list_filter, readonly_fields
- [x] Redirect Admin - list_display, list_filter, search_fields

#### Frontend Development
- [x] University list view and template
- [x] University detail view and template
- [x] Institute list view and template
- [x] Institute detail view and template
- [x] Major list view and template
- [x] Major detail view and template
- [x] Article list view and template
- [x] Article detail view and template
- [x] Article category view and template
- [x] Article tag view and template
- [x] Lead form view and template
- [x] Lead thank you template
- [x] Search results view and template
- [x] Pagination component
- [x] Breadcrumbs component
- [x] Header component
- [x] Footer component
- [x] Lead form component

#### Additional Features
- [x] Search functionality (universities, institutes, majors, articles)
- [x] Lead capture forms with anti-spam
- [x] URL redirects (301 redirects)
- [x] Pagination
- [x] Filtering and sorting
- [x] RTL support in all templates
- [x] SEO integration (meta tags, Open Graph, schema)
- [x] Sitemap generation
- [x] Robots.txt
- [x] Breadcrumbs
- [x] Related content linking
- [x] Image optimization and lazy loading
- [x] HTML editor for articles
- [x] Dashboard for content management

---

### ⏳ REMAINING TASKS (Phase 2 & Beyond)

#### Frontend Polish & Performance
- [ ] Mobile responsiveness optimization
- [ ] RTL edge cases testing and fixes
- [ ] Performance optimization (query optimization, caching)
- [ ] Image compression and WebP conversion
- [ ] CSS minification and optimization
- [ ] JavaScript minification and optimization
- [ ] Lazy loading implementation for images
- [ ] Pagination optimization

#### SEO & Search
- [ ] XML Sitemap generation and testing
- [ ] Robots.txt configuration
- [ ] Schema markup (Organization, Article, FAQ)
- [ ] Breadcrumb schema
- [ ] Open Graph tags verification
- [ ] Twitter card tags
- [ ] Canonical URL implementation
- [ ] Search engine indexing verification

#### Security & Validation
- [ ] Form validation (client-side and server-side)
- [ ] CSRF protection verification
- [ ] XSS prevention (HTML sanitization)
- [ ] SQL injection prevention
- [ ] Rate limiting for forms
- [ ] reCAPTCHA or honeypot implementation
- [ ] Admin security hardening
- [ ] SSL/TLS configuration

#### Testing & QA
- [ ] Unit tests for models
- [ ] Integration tests for views
- [ ] Form validation tests
- [ ] Search functionality tests
- [ ] Redirect tests
- [ ] Mobile responsiveness testing
- [ ] RTL testing
- [ ] Cross-browser testing
- [ ] Performance testing
- [ ] Security testing

#### Deployment & DevOps
- [ ] cPanel deployment setup
- [ ] Database backup procedures
- [ ] Media files backup
- [ ] SSL certificate configuration
- [ ] Static files collection
- [ ] Environment variables setup
- [ ] Logging configuration
- [ ] Monitoring setup
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring

#### Documentation
- [ ] API documentation (if needed)
- [ ] Admin user guide
- [ ] Content management guide
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Architecture documentation
- [ ] Database schema documentation

#### Content Management
- [ ] Bulk import tools for universities/institutes
- [ ] Content migration from old website
- [ ] URL redirect mapping
- [ ] Image upload and optimization
- [ ] Content versioning
- [ ] Content scheduling
- [ ] Content approval workflow (optional)

#### Analytics & Reporting
- [ ] Google Analytics integration
- [ ] Lead tracking and reporting
- [ ] Traffic analytics
- [ ] Search analytics
- [ ] User behavior tracking
- [ ] Conversion tracking

#### Advanced Features (Phase 3+)
- [ ] User registration and profiles
- [ ] Wishlist/favorites functionality
- [ ] User reviews and ratings
- [ ] Email notifications
- [ ] WhatsApp integration
- [ ] API endpoints for mobile app
- [ ] Multi-language support (if needed)
- [ ] Advanced search filters
- [ ] Comparison tools (universities, majors)
- [ ] Chatbot integration

---

## 📝 Development Checklist

### Pre-Development Setup

#### Environment Setup
- [ ] Python 3.9+ installed
- [ ] MySQL/MariaDB installed and running
- [ ] Git installed
- [ ] Code editor/IDE installed

#### Project Setup
- [ ] Clone/download project
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env`
- [ ] Configure `.env` with database credentials
- [ ] Create MySQL database: `CREATE DATABASE science_gates CHARACTER SET utf8mb4;`
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Verify admin access: `python manage.py runserver` → http://localhost:8000/admin/

### Daily Development Workflow

#### Start of Day
```bash
git pull
source venv/bin/activate  # or venv\Scripts\activate on Windows
python manage.py migrate
python manage.py runserver
```

#### During Development
- Write code following project conventions
- Test changes locally
- Run linting: `flake8 apps/`
- Run tests: `python manage.py test`
- Commit changes regularly: `git commit -m "message"`

#### End of Day
```bash
python manage.py test
flake8 apps/
git push
```

### Common Commands

```bash
# Virtual Environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Dependencies
pip install -r requirements.txt
pip freeze > requirements.txt

# Migrations
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Testing
python manage.py test
python manage.py test apps.app_name
python manage.py test apps.app_name.tests.TestClass

# Development
python manage.py runserver
python manage.py shell
python manage.py createsuperuser

# Static Files
python manage.py collectstatic --noinput

# Code Quality
flake8 apps/
black apps/
mypy apps/

# Git
git status
git add .
git commit -m "message"
git push
git pull
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named 'django'" | Activate venv and run `pip install -r requirements.txt` |
| "Can't connect to MySQL" | Check MySQL is running, verify credentials in .env |
| "Migration conflicts" | Run `python manage.py makemigrations --merge` |
| "Static files not loading" | Run `python manage.py collectstatic --noinput` |
| "Permission denied" | Check file permissions, use `chmod +x` on scripts |
| "Port 8000 already in use" | Use `python manage.py runserver 8001` |
| "ModuleNotFoundError" | Ensure virtual environment is activated |
| "Database doesn't exist" | Create database: `CREATE DATABASE science_gates CHARACTER SET utf8mb4;` |

---

## 📚 Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **MySQL Documentation**: https://dev.mysql.com/doc/
- **Python Documentation**: https://docs.python.org/
- **Git Documentation**: https://git-scm.com/doc
- **python-decouple**: https://github.com/henriquebastos/python-decouple
- **Pillow**: https://pillow.readthedocs.io/

---

## 📞 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review Django documentation
3. Check MySQL documentation
4. Review project structure and architecture sections

---

## 📄 License

This project is part of the Science Gates platform.

---

## 📅 Project Timeline

- **Phase 1**: ✅ Complete (May 17, 2026)
  - Foundation infrastructure
  - Abstract models
  - Settings configuration
  - Deployment setup

- **Phase 2**: 🚀 In Progress
  - Model implementation
  - Admin customization
  - Frontend development
  - Search functionality

---

**Last Updated**: May 17, 2026
**Status**: ✅ Phase 1 Complete | Ready for Phase 2
**Framework**: Django 4.2.11 LTS
**Database**: MySQL/MariaDB with UTF-8MB4
**Language**: Arabic (ar)
**Timezone**: Asia/Kuala_Lumpur
