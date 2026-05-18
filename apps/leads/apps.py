from django.apps import AppConfig


class LeadsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.leads'
    verbose_name = 'العملاء المحتملون'
    
    def ready(self):
        """Register signal handlers when app is ready."""
        import apps.leads.signals  # noqa
