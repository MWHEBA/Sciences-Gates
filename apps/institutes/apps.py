from django.apps import AppConfig


class InstitutesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.institutes'
    verbose_name = 'المعاهد'

    def ready(self):
        """Register signal handlers for image optimization."""
        from django.db.models.signals import post_save
        from apps.core.signals import create_webp_signal_handler
        from .models import Institute
        
        # Generate WebP versions for institute images
        handler = create_webp_signal_handler(Institute, 'main_image')
        post_save.connect(handler, sender=Institute)
