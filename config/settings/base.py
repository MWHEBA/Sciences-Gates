"""
Base Django settings for science_gates project.
Shared configuration for all environments (local, production).
Environment-specific overrides are in local.py and production.py
"""
import os
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
def _safe_bool_env(name: str, default: bool) -> bool:
    """
    Parse boolean-like env vars with a safe fallback.
    """
    value = config(name, default=str(default))
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {'1', 'true', 't', 'yes', 'y', 'on', 'debug', 'dev'}:
        return True
    if normalized in {'0', 'false', 'f', 'no', 'n', 'off', 'release', 'prod', 'production'}:
        return False
    return default


DEBUG = _safe_bool_env('DEBUG', True)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    
    # Local apps
    'apps.core',
    'apps.seo',
    'apps.dashboard',
    'apps.universities',
    'apps.institutes',
    'apps.majors',
    'apps.articles',
    'apps.html_editor',
    'apps.leads',
    'apps.search',
    'apps.redirects',
    'apps.importer',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.MaintenanceModeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.redirects.middleware.RedirectMiddleware',
    'apps.seo.middleware.Page404TrackingMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.dashboard_context',
                'apps.core.context_processors.site_settings_context',
                'apps.core.context_processors.phone_countries_context',
                'apps.core.context_processors.mega_menu_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Kuala_Lumpur'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Admin site configuration
ADMIN_URL = 'mw-admin/'
DASHBOARD_URL = 'sg/'

# Django Sites Framework
SITE_ID = 1

# Caching Configuration
CACHES = {
    'default': {
        'BACKEND': config('CACHE_BACKEND', default='django.core.cache.backends.filebased.FileBasedCache'),
        'LOCATION': config('CACHE_LOCATION', default=str(BASE_DIR / 'cache')),
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Email Configuration for Lead Notifications
EMAIL_BACKEND = config('EMAIL_BACKEND', default='apps.core.email_backends.DynamicEmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER', default='noreply@example.com')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin@example.com')

# Image Upload Settings
MAX_UPLOAD_SIZE = config('MAX_UPLOAD_SIZE', default=5242880, cast=int)  # 5MB
MAX_IMAGE_WIDTH = config('MAX_IMAGE_WIDTH', default=1920, cast=int)

# Site Configuration
SITE_NAME = config('SITE_NAME', default='بوابات العلوم للدراسة في ماليزيا')
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Security Settings
SECURE_HSTS_SECONDS = 0  # Set to 31536000 in production
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'



# Google Analytics & Search Console Settings
GA4_MEASUREMENT_ID = config('GA4_MEASUREMENT_ID', default='')
GOOGLE_SITE_VERIFICATION = config('GOOGLE_SITE_VERIFICATION', default='')

GOOGLE_SERVICE_ACCOUNT_JSON = config('GOOGLE_SERVICE_ACCOUNT_JSON', default='')
if GOOGLE_SERVICE_ACCOUNT_JSON and not os.path.isabs(GOOGLE_SERVICE_ACCOUNT_JSON):
    GOOGLE_SERVICE_ACCOUNT_JSON = os.path.join(BASE_DIR, GOOGLE_SERVICE_ACCOUNT_JSON)

# Load GSC credentials dict from JSON string env var if available
import json
GSC_CREDENTIALS_DICT = None
gsc_credentials_raw = config('GOOGLE_SERVICE_ACCOUNT_JSON_STRING', default='')
if gsc_credentials_raw:
    try:
        GSC_CREDENTIALS_DICT = json.loads(gsc_credentials_raw)
    except Exception:
        pass

GSC_SITE_URL = config('GSC_SITE_URL', default='https://sciencesgates.com/')

# Increase maximum number of GET/POST fields for large forms (e.g. university form with many nested programs)
DATA_UPLOAD_MAX_NUMBER_FIELDS = config('DATA_UPLOAD_MAX_NUMBER_FIELDS', default=10000, cast=int)

# Storage Configurations (Django 4.2+)
STORAGES = {
    "default": {
        "BACKEND": "apps.core.storage.SafeFileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Cloudflare Turnstile Settings
TURNSTILE_SITE_KEY = config('TURNSTILE_SITE_KEY', default='')
TURNSTILE_SECRET_KEY = config('TURNSTILE_SECRET_KEY', default='')

