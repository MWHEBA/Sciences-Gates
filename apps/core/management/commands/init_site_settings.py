"""
Management command to initialize SiteSettings with default values.
"""
from django.core.management.base import BaseCommand
from apps.core.models import SiteSettings


class Command(BaseCommand):
    help = 'Initialize SiteSettings with default values'

    def handle(self, *args, **options):
        """Initialize or update SiteSettings."""
        settings, created = SiteSettings.objects.get_or_create(pk=1)
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✓ SiteSettings created successfully')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠ SiteSettings already exists, skipping creation')
            )
        
        # Display current settings
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Current SiteSettings:')
        self.stdout.write('='*60)
        self.stdout.write(f'Site Name: {settings.site_name}')
        self.stdout.write(f'Registration Steps Title: {settings.registration_steps_title}')
        self.stdout.write(f'Registration Steps Content: {settings.registration_steps_content[:100] if settings.registration_steps_content else "Empty"}...')
        self.stdout.write(f'Phone: {settings.phone or "Not set"}')
        self.stdout.write(f'Email: {settings.email or "Not set"}')
        self.stdout.write(f'WhatsApp: {settings.whatsapp or "Not set"}')
        self.stdout.write('='*60 + '\n')
        
        self.stdout.write(
            self.style.SUCCESS('✓ You can now edit these settings in the Django admin panel')
        )
