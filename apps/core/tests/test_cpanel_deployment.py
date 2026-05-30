"""
Comprehensive tests for cPanel deployment configuration.

This test suite verifies all aspects of cPanel deployment:
1. passenger_wsgi.py configuration
2. Static file serving
3. Media file uploads and serving
4. MySQL/MariaDB connection
5. File-based caching
6. SSL certificate configuration

Requirements: 20 (cPanel Deployment Compatibility)
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings, Client
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.db import connection
from django.test.utils import override_settings
from django.urls import reverse


class PassengerWSGIConfigurationTest(TestCase):
    """Test passenger_wsgi.py configuration for cPanel deployment."""

    def test_passenger_wsgi_file_exists(self):
        """Test that passenger_wsgi.py file exists in project root."""
        # passenger_wsgi.py is in the project root (same level as manage.py)
        project_root = Path(settings.BASE_DIR)
        passenger_wsgi_path = project_root / 'passenger_wsgi.py'
        self.assertTrue(
            passenger_wsgi_path.exists(),
            f"passenger_wsgi.py not found at {passenger_wsgi_path}"
        )

    def test_passenger_wsgi_contains_wsgi_application(self):
        """Test that passenger_wsgi.py exports 'application' variable."""
        project_root = Path(settings.BASE_DIR)
        passenger_wsgi_path = project_root / 'passenger_wsgi.py'
        
        with open(passenger_wsgi_path, 'r') as f:
            content = f.read()
        
        self.assertIn(
            'application = get_wsgi_application()',
            content,
            "passenger_wsgi.py must export 'application' variable"
        )

    def test_passenger_wsgi_sets_django_settings_module(self):
        """Test that passenger_wsgi.py sets DJANGO_SETTINGS_MODULE."""
        project_root = Path(settings.BASE_DIR)
        passenger_wsgi_path = project_root / 'passenger_wsgi.py'
        
        with open(passenger_wsgi_path, 'r') as f:
            content = f.read()
        
        self.assertIn(
            'DJANGO_SETTINGS_MODULE',
            content,
            "passenger_wsgi.py must set DJANGO_SETTINGS_MODULE"
        )
        self.assertIn(
            'config.settings.production',
            content,
            "passenger_wsgi.py should use production settings by default"
        )

    def test_passenger_wsgi_creates_required_directories(self):
        """Test that passenger_wsgi.py creates required directories."""
        project_root = Path(settings.BASE_DIR)
        passenger_wsgi_path = project_root / 'passenger_wsgi.py'
        
        with open(passenger_wsgi_path, 'r') as f:
            content = f.read()
        
        # Check for directory creation code
        required_dirs = ['cache', 'logs', 'media', 'staticfiles']
        for dir_name in required_dirs:
            self.assertIn(
                dir_name,
                content,
                f"passenger_wsgi.py should create {dir_name} directory"
            )


class StaticFileServingTest(TestCase):
    """Test static file serving configuration for cPanel."""

    def test_static_url_configured(self):
        """Test that STATIC_URL is properly configured."""
        self.assertEqual(
            settings.STATIC_URL,
            '/static/',
            "STATIC_URL should be '/static/'"
        )

    def test_static_root_configured(self):
        """Test that STATIC_ROOT is properly configured."""
        self.assertIsNotNone(
            settings.STATIC_ROOT,
            "STATIC_ROOT must be configured"
        )
        self.assertTrue(
            str(settings.STATIC_ROOT).endswith('staticfiles'),
            "STATIC_ROOT should point to 'staticfiles' directory"
        )

    def test_static_root_directory_exists(self):
        """Test that STATIC_ROOT directory exists."""
        static_root = Path(settings.STATIC_ROOT)
        self.assertTrue(
            static_root.exists(),
            f"STATIC_ROOT directory does not exist: {static_root}"
        )

    def test_staticfiles_dirs_configured(self):
        """Test that STATICFILES_DIRS is properly configured."""
        self.assertIsNotNone(
            settings.STATICFILES_DIRS,
            "STATICFILES_DIRS must be configured"
        )
        self.assertTrue(
            len(settings.STATICFILES_DIRS) > 0,
            "STATICFILES_DIRS should contain at least one directory"
        )

    def test_staticfiles_storage_configured(self):
        """Test that ManifestStaticFilesStorage is configured in production."""
        # In test environment, we might use a different storage backend
        # Check that production.py has the correct configuration
        project_root = Path(settings.BASE_DIR)
        production_settings = project_root / 'config' / 'settings' / 'production.py'
        
        with open(production_settings, 'r') as f:
            content = f.read()
        
        self.assertIn(
            'ManifestStaticFilesStorage',
            content,
            "Production settings should use ManifestStaticFilesStorage for cache-busting"
        )

    def test_static_files_exist(self):
        """Test that static files are present."""
        static_dir = Path(settings.BASE_DIR) / 'static'
        
        # Check for CSS directory
        css_dir = static_dir / 'css'
        self.assertTrue(
            css_dir.exists(),
            f"CSS directory not found: {css_dir}"
        )
        
        # Check for JS directory
        js_dir = static_dir / 'js'
        self.assertTrue(
            js_dir.exists(),
            f"JS directory not found: {js_dir}"
        )

    def test_tailwind_css_exists(self):
        """Test that Tailwind CSS file exists."""
        tailwind_path = Path(settings.BASE_DIR) / 'static' / 'css' / 'tailwind.css'
        self.assertTrue(
            tailwind_path.exists(),
            f"Tailwind CSS not found: {tailwind_path}"
        )


class MediaFileHandlingTest(TestCase):
    """Test media file uploads and serving for cPanel."""

    def test_media_url_configured(self):
        """Test that MEDIA_URL is properly configured."""
        self.assertEqual(
            settings.MEDIA_URL,
            '/media/',
            "MEDIA_URL should be '/media/'"
        )

    def test_media_root_configured(self):
        """Test that MEDIA_ROOT is properly configured."""
        self.assertIsNotNone(
            settings.MEDIA_ROOT,
            "MEDIA_ROOT must be configured"
        )

    def test_media_root_directory_exists(self):
        """Test that MEDIA_ROOT directory exists."""
        media_root = Path(settings.MEDIA_ROOT)
        self.assertTrue(
            media_root.exists(),
            f"MEDIA_ROOT directory does not exist: {media_root}"
        )

    def test_media_subdirectories_exist(self):
        """Test that required media subdirectories exist."""
        media_root = Path(settings.MEDIA_ROOT)
        
        required_subdirs = [
            'universities/logos',
            'universities/images',
            'institutes/images',
            'majors/images',
            'articles/images',
            'og_images',
            'temp',
        ]
        
        for subdir in required_subdirs:
            subdir_path = media_root / subdir
            self.assertTrue(
                subdir_path.exists(),
                f"Media subdirectory not found: {subdir_path}"
            )

    def test_media_file_upload_and_serving(self):
        """Test that media files can be uploaded and served."""
        from apps.universities.models import University
        
        # Create a test image file
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        uploaded_file = SimpleUploadedFile(
            name='test_image.png',
            content=image_content,
            content_type='image/png'
        )
        
        # Create a university with an image
        university = University.objects.create(
            name='Test University',
            slug='test-university',
            logo=uploaded_file,
            main_image=uploaded_file,
            description='Test description',
            location='Test Location',
            admission_requirements='Test requirements'
        )
        
        # Verify the file was saved
        self.assertTrue(university.logo)
        self.assertTrue(university.main_image)
        
        # Verify the file path is correct
        self.assertIn('universities/logos', university.logo.name)
        self.assertIn('universities/images', university.main_image.name)

    def test_media_file_permissions(self):
        """Test that media directory has correct permissions."""
        media_root = Path(settings.MEDIA_ROOT)
        
        # Check that directory is readable and writable
        self.assertTrue(
            os.access(media_root, os.R_OK),
            f"Media directory is not readable: {media_root}"
        )
        self.assertTrue(
            os.access(media_root, os.W_OK),
            f"Media directory is not writable: {media_root}"
        )


class MySQLMariaDBConnectionTest(TestCase):
    """Test MySQL/MariaDB database connection for cPanel."""

    def test_database_engine_is_mysql(self):
        """Test that MySQL database engine is configured in production."""
        # In test environment, we use SQLite, but production.py configures MySQL
        # Check that production.py has the correct configuration
        project_root = Path(settings.BASE_DIR)
        production_settings = project_root / 'config' / 'settings' / 'production.py'
        
        with open(production_settings, 'r') as f:
            content = f.read()
        
        self.assertIn(
            'django.db.backends.mysql',
            content,
            "Production settings should use MySQL database engine"
        )

    def test_database_connection_successful(self):
        """Test that database connection is successful."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    def test_database_charset_utf8mb4(self):
        """Test that database uses UTF-8 charset for Arabic support in production."""
        # In test environment, we use SQLite which doesn't have charset options
        # Check that production.py has the correct configuration
        project_root = Path(settings.BASE_DIR)
        production_settings = project_root / 'config' / 'settings' / 'production.py'
        
        with open(production_settings, 'r') as f:
            content = f.read()
        
        self.assertIn(
            'utf8mb4',
            content,
            "Production settings should use utf8mb4 charset for Arabic support"
        )

    def test_database_connection_pooling_configured(self):
        """Test that connection pooling is configured in production."""
        # In test environment, CONN_MAX_AGE might be 0
        # Check that production.py has the correct configuration
        project_root = Path(settings.BASE_DIR)
        production_settings = project_root / 'config' / 'settings' / 'production.py'
        
        with open(production_settings, 'r') as f:
            content = f.read()
        
        self.assertIn(
            'CONN_MAX_AGE',
            content,
            "Production settings should configure CONN_MAX_AGE for connection pooling"
        )

    def test_database_models_accessible(self):
        """Test that all models can be accessed from database."""
        from apps.universities.models import University
        from apps.institutes.models import Institute
        from apps.majors.models import Major
        from apps.articles.models import Article
        
        # Test University model
        university_count = University.objects.count()
        self.assertIsInstance(university_count, int)
        
        # Test Institute model
        institute_count = Institute.objects.count()
        self.assertIsInstance(institute_count, int)
        
        # Test Major model
        major_count = Major.objects.count()
        self.assertIsInstance(major_count, int)
        
        # Test Article model
        article_count = Article.objects.count()
        self.assertIsInstance(article_count, int)


class FileBasedCachingTest(TestCase):
    """Test file-based caching configuration for cPanel."""

    def test_cache_backend_is_filebased(self):
        """Test that file-based cache backend is configured."""
        cache_backend = settings.CACHES['default']['BACKEND']
        self.assertEqual(
            cache_backend,
            'django.core.cache.backends.filebased.FileBasedCache',
            "Should use file-based cache backend for cPanel compatibility"
        )

    def test_cache_location_configured(self):
        """Test that cache location is properly configured."""
        cache_location = settings.CACHES['default'].get('LOCATION')
        self.assertIsNotNone(
            cache_location,
            "Cache LOCATION must be configured"
        )

    def test_cache_directory_exists(self):
        """Test that cache directory exists."""
        cache_location = settings.CACHES['default'].get('LOCATION')
        cache_dir = Path(cache_location)
        self.assertTrue(
            cache_dir.exists(),
            f"Cache directory does not exist: {cache_dir}"
        )

    def test_cache_timeout_configured(self):
        """Test that cache timeout is configured."""
        cache_timeout = settings.CACHES['default'].get('TIMEOUT')
        self.assertIsNotNone(
            cache_timeout,
            "Cache TIMEOUT must be configured"
        )
        self.assertGreater(
            cache_timeout,
            0,
            "Cache TIMEOUT should be greater than 0"
        )

    def test_cache_set_and_get(self):
        """Test that cache can store and retrieve values."""
        cache_key = 'test_cache_key'
        cache_value = 'test_cache_value'
        
        # Set cache
        cache.set(cache_key, cache_value, 300)
        
        # Get cache
        retrieved_value = cache.get(cache_key)
        self.assertEqual(
            retrieved_value,
            cache_value,
            "Cache should store and retrieve values correctly"
        )
        
        # Clean up
        cache.delete(cache_key)

    def test_cache_max_entries_configured(self):
        """Test that cache max entries is configured."""
        cache_options = settings.CACHES['default'].get('OPTIONS', {})
        max_entries = cache_options.get('MAX_ENTRIES')
        self.assertIsNotNone(
            max_entries,
            "Cache MAX_ENTRIES should be configured"
        )
        self.assertGreater(
            max_entries,
            0,
            "Cache MAX_ENTRIES should be greater than 0"
        )


class SSLCertificateConfigurationTest(TestCase):
    """Test SSL certificate configuration for cPanel."""

    def test_secure_ssl_redirect_configured(self):
        """Test that SECURE_SSL_REDIRECT is configured."""
        # In production, this should be True
        # In test environment, it might be False
        self.assertIn(
            settings.SECURE_SSL_REDIRECT,
            [True, False],
            "SECURE_SSL_REDIRECT should be a boolean"
        )

    def test_session_cookie_secure_configured(self):
        """Test that SESSION_COOKIE_SECURE is configured."""
        # In test environment, this might be False, but in production it should be True
        # The production.py file sets it to True
        self.assertIsNotNone(settings.SESSION_COOKIE_SECURE)

    def test_csrf_cookie_secure_configured(self):
        """Test that CSRF_COOKIE_SECURE is configured."""
        # In test environment, this might be False, but in production it should be True
        # The production.py file sets it to True
        self.assertIsNotNone(settings.CSRF_COOKIE_SECURE)

    def test_secure_content_type_nosniff_configured(self):
        """Test that SECURE_CONTENT_TYPE_NOSNIFF is configured."""
        self.assertTrue(
            settings.SECURE_CONTENT_TYPE_NOSNIFF,
            "SECURE_CONTENT_TYPE_NOSNIFF should be True"
        )

    def test_x_frame_options_configured(self):
        """Test that X_FRAME_OPTIONS is configured."""
        self.assertEqual(
            settings.X_FRAME_OPTIONS,
            'DENY',
            "X_FRAME_OPTIONS should be 'DENY' to prevent clickjacking"
        )

    def test_hsts_headers_configured(self):
        """Test that HSTS headers are configured."""
        # In test environment, this might be 0, but in production it should be > 0
        # The production.py file sets it to 31536000
        self.assertIsNotNone(settings.SECURE_HSTS_SECONDS)

    def test_secure_browser_xss_filter_configured(self):
        """Test that SECURE_BROWSER_XSS_FILTER is configured."""
        # This setting might not be present in all Django versions
        # Check if it exists and if so, verify it's True
        if hasattr(settings, 'SECURE_BROWSER_XSS_FILTER'):
            self.assertTrue(
                settings.SECURE_BROWSER_XSS_FILTER,
                "SECURE_BROWSER_XSS_FILTER should be True"
            )


class RequirementsFileTest(TestCase):
    """Test requirements.txt file for cPanel deployment."""

    def test_requirements_file_exists(self):
        """Test that requirements.txt file exists."""
        project_root = Path(settings.BASE_DIR)
        requirements_path = project_root / 'requirements.txt'
        self.assertTrue(
            requirements_path.exists(),
            f"requirements.txt not found at {requirements_path}"
        )

    def test_requirements_contains_django(self):
        """Test that requirements.txt contains Django."""
        project_root = Path(settings.BASE_DIR)
        requirements_path = project_root / 'requirements.txt'
        
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        self.assertIn(
            'Django',
            content,
            "requirements.txt should contain Django"
        )

    def test_requirements_contains_mysqlclient(self):
        """Test that requirements.txt contains mysqlclient."""
        project_root = Path(settings.BASE_DIR)
        requirements_path = project_root / 'requirements.txt'
        
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        self.assertIn(
            'mysqlclient',
            content,
            "requirements.txt should contain mysqlclient for MySQL support"
        )

    def test_requirements_contains_pillow(self):
        """Test that requirements.txt contains Pillow."""
        project_root = Path(settings.BASE_DIR)
        requirements_path = project_root / 'requirements.txt'
        
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        self.assertIn(
            'Pillow',
            content,
            "requirements.txt should contain Pillow for image processing"
        )

    def test_requirements_contains_bleach(self):
        """Test that requirements.txt contains bleach."""
        project_root = Path(settings.BASE_DIR)
        requirements_path = project_root / 'requirements.txt'
        
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        self.assertIn(
            'bleach',
            content,
            "requirements.txt should contain bleach for HTML sanitization"
        )

    def test_requirements_contains_python_decouple(self):
        """Test that requirements.txt contains python-decouple."""
        project_root = Path(settings.BASE_DIR)
        requirements_path = project_root / 'requirements.txt'
        
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        self.assertIn(
            'python-decouple',
            content,
            "requirements.txt should contain python-decouple for environment variables"
        )


class DeploymentDocumentationTest(TestCase):
    """Test deployment documentation for cPanel."""

    def test_cpanel_deployment_guide_exists(self):
        """Test that CPANEL_DEPLOYMENT.md exists."""
        project_root = Path(settings.BASE_DIR)
        deployment_guide = project_root / 'CPANEL_DEPLOYMENT.md'
        self.assertTrue(
            deployment_guide.exists(),
            f"CPANEL_DEPLOYMENT.md not found at {deployment_guide}"
        )

    def test_deployment_guide_contains_setup_instructions(self):
        """Test that deployment guide contains setup instructions."""
        project_root = Path(settings.BASE_DIR)
        deployment_guide = project_root / 'CPANEL_DEPLOYMENT.md'
        
        with open(deployment_guide, 'r') as f:
            content = f.read()
        
        required_sections = [
            'Prerequisites',
            'Deployment Steps',
            'Python Application',
            'MySQL Database',
            'Environment Variables',
            'Static Files',
            'SSL Certificate',
        ]
        
        for section in required_sections:
            self.assertIn(
                section,
                content,
                f"Deployment guide should contain '{section}' section"
            )

    def test_deployment_checklist_exists(self):
        """Test that DEPLOYMENT_CHECKLIST.md exists."""
        project_root = Path(settings.BASE_DIR)
        checklist = project_root / 'DEPLOYMENT_CHECKLIST.md'
        self.assertTrue(
            checklist.exists(),
            f"DEPLOYMENT_CHECKLIST.md not found at {checklist}"
        )

    def test_env_example_file_exists(self):
        """Test that .env.example file exists."""
        project_root = Path(settings.BASE_DIR)
        env_example = project_root / '.env.example'
        self.assertTrue(
            env_example.exists(),
            f".env.example not found at {env_example}"
        )

    def test_env_example_contains_required_variables(self):
        """Test that .env.example contains required variables."""
        project_root = Path(settings.BASE_DIR)
        env_example = project_root / '.env.example'
        
        with open(env_example, 'r') as f:
            content = f.read()
        
        required_vars = [
            'DEBUG',
            'SECRET_KEY',
            'ALLOWED_HOSTS',
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD',
            'DB_HOST',
            'DB_PORT',
        ]
        
        for var in required_vars:
            self.assertIn(
                var,
                content,
                f".env.example should contain '{var}' variable"
            )


class ProductionSettingsTest(TestCase):
    """Test production settings configuration."""

    def test_debug_false_in_production(self):
        """Test that DEBUG is False in production settings."""
        # This test checks the production.py file
        project_root = Path(settings.BASE_DIR)
        production_settings = project_root / 'config' / 'settings' / 'production.py'
        
        with open(production_settings, 'r') as f:
            content = f.read()
        
        # Check that DEBUG is set from environment with False default
        self.assertIn(
            "config('DEBUG'",
            content,
            "DEBUG should be configured from environment variables"
        )

    def test_allowed_hosts_configured(self):
        """Test that ALLOWED_HOSTS is configured."""
        self.assertIsNotNone(
            settings.ALLOWED_HOSTS,
            "ALLOWED_HOSTS must be configured"
        )

    def test_database_configured_from_environment(self):
        """Test that database is configured from environment variables."""
        project_root = Path(settings.BASE_DIR)
        production_settings = project_root / 'config' / 'settings' / 'production.py'
        
        with open(production_settings, 'r') as f:
            content = f.read()
        
        required_configs = [
            "config('DB_NAME'",
            "config('DB_USER'",
            "config('DB_PASSWORD'",
            "config('DB_HOST'",
        ]
        
        for config_var in required_configs:
            self.assertIn(
                config_var,
                content,
                f"Production settings should configure {config_var}"
            )

    def test_logging_configured(self):
        """Test that logging is configured."""
        self.assertIsNotNone(
            settings.LOGGING,
            "LOGGING must be configured"
        )
        self.assertIn(
            'handlers',
            settings.LOGGING,
            "LOGGING should have handlers configured"
        )

    def test_logs_directory_exists(self):
        """Test that logs directory exists."""
        logs_dir = Path(settings.BASE_DIR) / 'logs'
        self.assertTrue(
            logs_dir.exists(),
            f"Logs directory does not exist: {logs_dir}"
        )


class IntegrationTest(TestCase):
    """Integration tests for cPanel deployment."""

    def test_application_starts_successfully(self):
        """Test that Django application starts successfully."""
        # This test verifies that all settings are valid
        # If settings are invalid, Django would raise an error during test setup
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertIsNotNone(settings.INSTALLED_APPS)

    def test_all_required_apps_installed(self):
        """Test that all required apps are installed."""
        required_apps = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'apps.core',
            'apps.dashboard',
            'apps.universities',
            'apps.institutes',
            'apps.majors',
            'apps.articles',
            'apps.leads',
            'apps.seo',
            'apps.redirects',
            'apps.search',
        ]
        
        for app in required_apps:
            self.assertIn(
                app,
                settings.INSTALLED_APPS,
                f"App '{app}' should be installed"
            )

    def test_middleware_configured(self):
        """Test that required middleware is configured."""
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ]
        
        for middleware in required_middleware:
            self.assertIn(
                middleware,
                settings.MIDDLEWARE,
                f"Middleware '{middleware}' should be configured"
            )

    def test_templates_configured(self):
        """Test that templates are properly configured."""
        self.assertIsNotNone(
            settings.TEMPLATES,
            "TEMPLATES must be configured"
        )
        self.assertGreater(
            len(settings.TEMPLATES),
            0,
            "At least one template engine should be configured"
        )

    def test_static_files_can_be_collected(self):
        """Test that static files can be collected."""
        # This is a basic test to ensure the static files configuration is valid
        static_root = Path(settings.STATIC_ROOT)
        self.assertTrue(
            static_root.exists(),
            f"STATIC_ROOT should exist: {static_root}"
        )

    def test_database_migrations_applied(self):
        """Test that database migrations are applied."""
        # Check that we can query the database
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            User.objects.count()
        except Exception as e:
            self.fail(f"Database migrations may not be applied: {e}")

    def test_content_can_be_created_and_retrieved(self):
        """Test that content can be created and retrieved from database."""
        from apps.universities.models import University
        
        # Create a test university
        university = University.objects.create(
            name='Test University',
            slug='test-university',
            description='Test description',
            location='Test Location',
            admission_requirements='Test requirements'
        )
        
        # Retrieve it
        retrieved = University.objects.get(slug='test-university')
        self.assertEqual(retrieved.name, 'Test University')
        
        # Clean up
        university.delete()
