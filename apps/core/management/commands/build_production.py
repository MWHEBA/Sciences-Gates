"""
Django management command for production build process.

This command automates the complete production build process:
1. Minifies CSS and JavaScript
2. Collects static files
3. Verifies deployment readiness

Usage:
    python manage.py build_production
    python manage.py build_production --skip-minify
    python manage.py build_production --skip-collect
"""

import os
import subprocess
import sys
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = 'Build production assets: minify CSS/JS and collect static files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-minify',
            action='store_true',
            help='Skip CSS and JavaScript minification',
        )
        parser.add_argument(
            '--skip-collect',
            action='store_true',
            help='Skip static file collection',
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Do not prompt for user input',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('PRODUCTION BUILD PROCESS'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Check if we're in production mode
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING(
                'WARNING: DEBUG is True. This should be False in production.'
            ))
            self.stdout.write(self.style.WARNING(
                'Set DEBUG=False in your .env file before deploying.'
            ))
            self.stdout.write('')

        # Step 1: Minify CSS and JavaScript
        if not options['skip_minify']:
            self.stdout.write(self.style.SUCCESS('Step 1: Minifying CSS and JavaScript...'))
            try:
                self._minify_assets()
                self.stdout.write(self.style.SUCCESS('[OK] Minification complete'))
            except Exception as e:
                raise CommandError(f'Minification failed: {str(e)}')
            self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING('[SKIP] Skipping minification'))
            self.stdout.write('')

        # Step 2: Collect static files
        if not options['skip_collect']:
            self.stdout.write(self.style.SUCCESS('Step 2: Collecting static files...'))
            try:
                call_command(
                    'collectstatic',
                    no_input=options['noinput'],
                    verbosity=1,
                )
                self.stdout.write(self.style.SUCCESS('[OK] Static files collected'))
            except Exception as e:
                raise CommandError(f'Static file collection failed: {str(e)}')
            self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING('[SKIP] Skipping static file collection'))
            self.stdout.write('')

        # Step 3: Verify deployment readiness
        self.stdout.write(self.style.SUCCESS('Step 3: Verifying deployment readiness...'))
        self._verify_deployment()
        self.stdout.write('')

        # Summary
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('BUILD COMPLETE'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Next steps:'))
        self.stdout.write('1. Verify all static files are in: ' + str(settings.STATIC_ROOT))
        self.stdout.write('2. Check that minified files exist (.min.css, .min.js)')
        self.stdout.write('3. Verify staticfiles.json manifest file exists')
        self.stdout.write('4. Configure web server to serve static files from STATIC_ROOT')
        self.stdout.write('5. Ensure .htaccess is in place for caching headers')
        self.stdout.write('6. Restart your application (through cPanel or SSH)')
        self.stdout.write('')

    def _minify_assets(self):
        """Minify CSS and JavaScript files."""
        base_dir = Path(settings.BASE_DIR)
        
        # Check if npm is available
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, check=True, shell=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.stdout.write(self.style.WARNING(
                'WARNING: npm is not installed or not in PATH. '
                'Skipping minification. You can run minification manually:'
            ))
            self.stdout.write('  npm run build')
            return

        # Run npm build command
        self.stdout.write('  - Running npm build...')
        try:
            result = subprocess.run(
                'npm run build',
                cwd=str(base_dir),
                capture_output=True,
                text=True,
                check=True,
                shell=True,
            )
            if result.stdout:
                self.stdout.write(result.stdout)
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'npm build failed: {e.stderr}'))
            raise CommandError('npm build failed')

        # Verify minified files exist
        self.stdout.write('  - Verifying minified files...')
        css_minified = base_dir / 'static' / 'css' / 'tailwind.min.css'
        if not css_minified.exists():
            raise CommandError(f'Minified CSS not found: {css_minified}')
        self.stdout.write(f'    [OK] {css_minified.name} ({css_minified.stat().st_size} bytes)')

        # Check for minified JS files
        js_dir = base_dir / 'static' / 'js'
        minified_js_files = list(js_dir.glob('*.min.js'))
        if minified_js_files:
            for js_file in minified_js_files:
                self.stdout.write(f'    [OK] {js_file.name} ({js_file.stat().st_size} bytes)')
        else:
            self.stdout.write(self.style.WARNING('    [SKIP] No minified JS files found'))

    def _verify_deployment(self):
        """Verify deployment readiness."""
        base_dir = Path(settings.BASE_DIR)
        issues = []

        # Check STATIC_ROOT exists
        static_root = Path(settings.STATIC_ROOT)
        if not static_root.exists():
            issues.append(f'STATIC_ROOT does not exist: {static_root}')
        else:
            self.stdout.write(f'  [OK] STATIC_ROOT exists: {static_root}')

        # Check staticfiles.json manifest
        manifest_file = static_root / 'staticfiles.json'
        if manifest_file.exists():
            self.stdout.write(f'  [OK] Manifest file exists: {manifest_file.name}')
        else:
            issues.append(f'Manifest file not found: {manifest_file}')

        # Check .htaccess for caching headers
        htaccess_file = static_root / '.htaccess'
        if htaccess_file.exists():
            self.stdout.write(f'  [OK] .htaccess file exists for caching headers')
        else:
            self.stdout.write(self.style.WARNING(
                f'  [WARN] .htaccess file not found. '
                'Caching headers may not be configured.'
            ))

        # Check DEBUG setting
        if settings.DEBUG:
            issues.append('DEBUG is True. Set DEBUG=False in production.')
        else:
            self.stdout.write('  [OK] DEBUG is False')

        # Check ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
            issues.append('ALLOWED_HOSTS is not properly configured')
        else:
            self.stdout.write(f'  [OK] ALLOWED_HOSTS configured: {settings.ALLOWED_HOSTS}')

        # Check SECURE_SSL_REDIRECT
        if not settings.SECURE_SSL_REDIRECT:
            self.stdout.write(self.style.WARNING(
                '  [WARN] SECURE_SSL_REDIRECT is False. '
                'Consider enabling SSL redirect in production.'
            ))
        else:
            self.stdout.write('  [OK] SECURE_SSL_REDIRECT is True')

        # Report issues
        if issues:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('ISSUES FOUND:'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'  [ERROR] {issue}'))
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'Please fix these issues before deploying to production.'
            ))
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('[OK] All deployment checks passed'))
