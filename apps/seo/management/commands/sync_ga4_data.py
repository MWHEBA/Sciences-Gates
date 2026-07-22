import logging
from django.core.management.base import BaseCommand
from apps.core.models import SiteSettings, GA4CachedReport
from apps.seo.services.ga4_client import GA4Client, GA4APIError

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync Google Analytics 4 reporting data to local database cache.'

    def handle(self, *args, **options):
        self.stdout.write("Starting GA4 data synchronization...")
        
        try:
            site_settings = SiteSettings.get_settings()
        except Exception as exc:
            self.stderr.write(f"Error fetching site settings: {exc}")
            return

        property_id = site_settings.ga4_property_id
        if not property_id:
            self.stdout.write(self.style.WARNING("GA4 Property ID is not configured. Skipping synchronization."))
            return

        client = GA4Client()
        if not client.is_configured():
            self.stdout.write(self.style.WARNING("Google Service Account is not configured in settings. Skipping."))
            return

        periods = [7, 14, 28, 90]
        success_count = 0

        for days in periods:
            self.stdout.write(f"Syncing GA4 data for past {days} days...")
            try:
                data = client.fetch_all_reports(property_id, days)
                
                # Save to database
                report, created = GA4CachedReport.objects.update_or_create(
                    days=days,
                    defaults={
                        'payload': data
                    }
                )
                self.stdout.write(self.style.SUCCESS(f"Successfully synced {days} days report."))
                success_count += 1
            except GA4APIError as exc:
                self.stderr.write(f"Error syncing {days} days: {exc}")
                logger.error("GA4 sync failed for days %s: %s", days, exc)
            except Exception as exc:
                self.stderr.write(f"Unexpected error for {days} days: {exc}")
                logger.error("GA4 sync unexpected failure for days %s: %s", days, exc, exc_info=True)

        if success_count == len(periods):
            self.stdout.write(self.style.SUCCESS("All GA4 periods synced successfully!"))
        else:
            self.stdout.write(self.style.WARNING(f"Sync complete. Successful periods: {success_count}/{len(periods)}"))
