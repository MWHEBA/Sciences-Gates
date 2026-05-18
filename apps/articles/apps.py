from django.apps import AppConfig


class ArticlesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.articles'
    verbose_name = 'المقالات'

    def ready(self):
        """Register signal handlers for image optimization."""
        from django.db.models.signals import post_save
        from apps.core.signals import create_webp_signal_handler
        from .models import Article
        
        # Generate WebP versions for article images
        handler = create_webp_signal_handler(Article, 'featured_image')
        post_save.connect(handler, sender=Article)
