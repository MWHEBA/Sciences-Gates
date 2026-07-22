from django.apps import AppConfig


class RedirectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.redirects'
    verbose_name = 'إعادات التوجيه'

    def ready(self):
        import apps.redirects.signals
