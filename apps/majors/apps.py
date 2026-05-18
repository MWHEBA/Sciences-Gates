from django.apps import AppConfig


class MajorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.majors'
    verbose_name = 'التخصصات'

    def ready(self):
        """Register signal handlers for image optimization."""
        from django.db.models.signals import post_save
        from apps.core.signals import create_webp_signal_handler
        from .models import Major
        
        # Generate WebP versions for major images
        handler = create_webp_signal_handler(Major, 'main_image')
        post_save.connect(handler, sender=Major)
