from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.models import SiteSettings
from django.core.cache import cache
from apps.seo.sitemaps import sitemaps

class Command(BaseCommand):
    help = 'Rebuild and warm up the XML sitemap cache'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Rebuilding sitemap cache...'))
        
        # 1. Clear the cache for all sitemaps
        sitemap_classes = ['universitysitemap', 'institutesitemap', 'majorsitemap', 'articlesitemap', 'staticsitemap']
        for cls in sitemap_classes:
            for page in range(1, 11):
                cache.delete(f"sitemap_{cls}_page_{page}")
        self.stdout.write(self.style.SUCCESS('Sitemap cache cleared.'))
        
        # 2. Warm up the cache by accessing get_urls() for each sitemap class
        # This will trigger database queries once and cache the results for 24h
        for name, sitemap_class in sitemaps.items():
            try:
                sitemap_instance = sitemap_class()
                # Trigger the get_urls() method which caches the result
                sitemap_instance.get_urls()
                self.stdout.write(self.style.SUCCESS(f'Warmed cache for sitemap: {name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to warm cache for {name}: {str(e)}'))
                
        # 3. Update the timestamp in SiteSettings
        try:
            settings = SiteSettings.get_settings()
            settings.sitemap_last_generated = timezone.now()
            settings.save(update_fields=['sitemap_last_generated'])
            self.stdout.write(self.style.SUCCESS(f'SiteSettings.sitemap_last_generated updated.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to update SiteSettings: {str(e)}'))
            
        self.stdout.write(self.style.SUCCESS('Sitemap cache successfully rebuilt 100%!'))
