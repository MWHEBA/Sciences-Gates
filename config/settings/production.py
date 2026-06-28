"""
Production settings for science_gates project.
Optimized for cPanel deployment with MySQL/MariaDB database.

This configuration is designed for cPanel shared hosting environments with:
- Passenger WSGI application server
- MySQL/MariaDB database
- File-based caching (compatible with cPanel)
- Static file serving through cPanel's web server
- Media file storage in local directories
"""
from .base import *
from decouple import config, Csv
from pathlib import Path

DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='science.mwheba.co.uk,localhost,127.0.0.1', cast=Csv())
if 'science.mwheba.co.uk' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('science.mwheba.co.uk')

# Production database configuration
# Support both SQLite and MySQL dynamically based on DB_ENGINE (defaults to sqlite)
db_engine = config('DB_ENGINE', default='django.db.backends.sqlite3')

if 'sqlite' in db_engine:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / config('DB_NAME', default='db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': db_engine,
            'NAME': config('DB_NAME', default='science_gates'),
            'USER': config('DB_USER', default='root'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'autocommit': True,
            },
            'CONN_MAX_AGE': 600,  # Connection pooling for better performance
        }
    }

# ============================================================================
# STATIC FILES CONFIGURATION FOR cPANEL
# ============================================================================
# For cPanel deployment:
# 1. Run 'python manage.py collectstatic' to gather all static files
# 2. Configure cPanel to serve static files from STATIC_ROOT directory
# 3. Point web server to serve /static/ URL from STATIC_ROOT path
#
# Static files include:
# - CSS (Tailwind CSS compiled output - minified)
# - JavaScript (Alpine.js, custom scripts - minified)
# - Images (logos, placeholders)
# - Fonts (if any)
#
# MINIFICATION PROCESS:
# Before running collectstatic in production:
# 1. Run 'npm run build' to minify CSS and JavaScript
# 2. This generates:
#    - static/css/tailwind.min.css (from Tailwind build process)
#    - static/js/*.min.js files (from Node.js minification script)
# 3. Then run 'python manage.py collectstatic --noinput'
# 4. Django will copy all files to STATIC_ROOT with cache-busting hashes
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Ensure static files directory exists
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# Additional static files directories to collect from
STATICFILES_DIRS = [BASE_DIR / 'static']

# Storage Configurations (Django 4.2+)
# Uses a custom SafeManifestStaticFilesStorage which prevents crashes if a file is missing in the manifest,
# falling back gracefully to the original file path.
STORAGES = {
    "default": {
        "BACKEND": "apps.core.storage.SafeFileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "apps.core.storage.SafeManifestStaticFilesStorage",
    },
}


# ============================================================================
# STATIC FILE CACHING HEADERS
# ============================================================================
# Configure HTTP caching headers for static files
# These headers tell browsers and CDNs how long to cache static assets
#
# Strategy:
# - Minified files with content hashes can be cached for 1 year (31536000 seconds)
# - Browser will use cached version unless content changes (hash changes)
# - If content changes, new hash is generated, forcing browser to fetch new version
#
# Implementation:
# Configure your web server (Apache/Nginx) to set these headers:
#
# For Apache (.htaccess in staticfiles directory):
#   <FilesMatch "\.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$">
#     Header set Cache-Control "public, max-age=31536000, immutable"
#   </FilesMatch>
#
# For Nginx (in server block):
#   location /static/ {
#     expires 1y;
#     add_header Cache-Control "public, immutable";
#   }
#
# For cPanel with Apache:
# 1. Create .htaccess file in staticfiles directory
# 2. Add cache headers for static file extensions
# 3. Restart Apache through cPanel
#
# Django Configuration:
# Set these environment variables or configure in .env:
STATIC_FILE_CACHE_MAX_AGE = config('STATIC_FILE_CACHE_MAX_AGE', default=31536000, cast=int)  # 1 year

# Additional security headers for static files
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# ============================================================================
# MEDIA FILES CONFIGURATION FOR cPANEL
# ============================================================================
# Media files (user uploads) are stored in local directory
# Configure cPanel to serve /media/ URL from MEDIA_ROOT path
#
# Media files include:
# - University logos and images
# - Institute images
# - Major images
# - Article featured images
# - Open Graph images
# - User-uploaded content
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Ensure media directory exists
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# Create subdirectories for organized media storage
media_subdirs = [
    'universities/logos',
    'universities/images',
    'institutes/images',
    'majors/images',
    'articles/images',
    'og_images',
    'temp',
]

for subdir in media_subdirs:
    (MEDIA_ROOT / subdir).mkdir(parents=True, exist_ok=True)

# ============================================================================
# CACHING CONFIGURATION FOR cPANEL
# ============================================================================
# File-based caching is compatible with cPanel shared hosting
# No Redis or Memcached required (though they can be used if available)
#
# Caching Strategy:
# - Default: File-based cache (compatible with all cPanel environments)
# - Optional: Redis cache (if available on your cPanel server)
# - Cache timeout: 300 seconds (5 minutes) by default
# - Max entries: 1000 items
#
# Cache is used for:
# - Query result caching (via django-cachalot)
# - Session storage (optional)
# - Template fragment caching
# - View caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(BASE_DIR / 'cache'),
        'TIMEOUT': 300,  # 5 minutes default cache timeout
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Ensure cache directory exists
cache_dir = BASE_DIR / 'cache'
cache_dir.mkdir(parents=True, exist_ok=True)

# Optional: Use Redis if available on cPanel server
# Uncomment and configure if Redis is available:
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }

# ============================================================================
# SECURITY SETTINGS FOR PRODUCTION
# ============================================================================
# DEBUG MODE - MUST BE FALSE IN PRODUCTION
# Setting DEBUG=True in production exposes sensitive information and is a security risk
# DEBUG is already configured at the top of this file from environment variables
# with a default of False for safety

# SSL/TLS CONFIGURATION
# SECURE_SSL_REDIRECT: Redirect all HTTP requests to HTTPS
# Set to False during initial setup/testing, then enable for production
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)

# SECURE COOKIES
# SESSION_COOKIE_SECURE: Only send session cookie over HTTPS
# CSRF_COOKIE_SECURE: Only send CSRF cookie over HTTPS
# These prevent cookie interception over unencrypted connections
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# SECURE_CONTENT_TYPE_NOSNIFF
# Prevents browsers from MIME-sniffing a response away from the declared Content-Type
# Protects against content-type based attacks
SECURE_CONTENT_TYPE_NOSNIFF = True

# X_FRAME_OPTIONS
# Prevents clickjacking attacks by controlling whether the site can be framed
# DENY: Page cannot be displayed in a frame
# SAMEORIGIN: Page can only be displayed in a frame on the same origin
X_FRAME_OPTIONS = 'DENY'

# HSTS (HTTP Strict Transport Security)
# Tells browsers to always use HTTPS for this domain
# SECURE_HSTS_SECONDS: How long (in seconds) the browser should remember to use HTTPS
# Set to 31536000 (1 year) after testing SSL configuration
# Start with lower value (e.g., 3600 = 1 hour) during testing
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# XSS PROTECTION
# SECURE_BROWSER_XSS_FILTER: Enable browser XSS filtering
SECURE_BROWSER_XSS_FILTER = True

# Content Security Policy
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", "'unsafe-inline'"),  # Alpine.js requires unsafe-inline
    'style-src': ("'self'", "'unsafe-inline'"),   # Tailwind requires unsafe-inline
    'img-src': ("'self'", 'data:', 'https:'),
    'font-src': ("'self'",),
    'connect-src': ("'self'",),
}

# ============================================================================
# LOGGING CONFIGURATION FOR cPANEL
# ============================================================================
# Logs are written to local files in the logs directory
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': str(BASE_DIR / 'logs' / 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'django': {
        'handlers': ['file'],
        'level': 'INFO',
        'propagate': False,
    },
}

# Ensure logs directory exists
logs_dir = BASE_DIR / 'logs'
logs_dir.mkdir(parents=True, exist_ok=True)

# ============================================================================
# PERFORMANCE OPTIMIZATION FOR cPANEL
# ============================================================================
# Database connection pooling
CONN_MAX_AGE = 600

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ============================================================================
# EMAIL CONFIGURATION FOR cPANEL
# ============================================================================
# Configure email for lead notifications
# Update these values in .env file for your cPanel hosting
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@example.com')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin@example.com')
