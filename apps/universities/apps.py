from django.apps import AppConfig


class UniversitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.universities'
    verbose_name = 'الجامعات'

    def ready(self):
        """Register signal handlers for image optimization."""
        from django.db.models.signals import post_save
        from apps.core.signals import create_webp_signal_handler
        from .models import University
        
        # Generate WebP versions for university images
        handler = create_webp_signal_handler(University, 'main_image')
        post_save.connect(handler, sender=University)
        
        handler_logo = create_webp_signal_handler(University, 'logo')
        post_save.connect(handler_logo, sender=University)
