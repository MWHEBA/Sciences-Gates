import logging
import sys
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.articles.models import Article
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.importer.services.wp_client import WPImporterClient, WPImporterError
from apps.importer.services.bulk_saver import parse_wp_datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Sync original creation dates from the legacy WordPress site for all imported articles, universities, institutes, and majors."

    def write_safe(self, text, style_func=None):
        encoding = sys.stdout.encoding or 'utf-8'
        # Encode to console encoding, replacing unmappable chars, then decode back
        safe_text = text.encode(encoding, 'replace').decode(encoding)
        if style_func:
            self.stdout.write(style_func(safe_text))
        else:
            self.stdout.write(safe_text)

    def handle(self, *args, **options):
        client = WPImporterClient()

        # Define targets to sync
        targets = [
            (Article, "publish_date"),
            (University, "created_at"),
            (Institute, "created_at"),
            (Major, "created_at"),
        ]

        total_synced = 0
        total_failed = 0

        for model, date_field in targets:
            model_name = model.__name__
            self.write_safe(f"=== Starting sync for {model_name} ===", self.style.HTTP_INFO)
            
            items = model.objects.all()
            count = items.count()
            self.write_safe(f"Found {count} {model_name} items in database.\n")

            for item in items:
                slug = item.slug
                if not slug:
                    self.write_safe(f"Skipping {model_name} ID={item.id} because slug is empty.\n", self.style.WARNING)
                    continue

                try:
                    wp_data = client.fetch(slug)
                    created_at_str = wp_data.get('created_at')
                    
                    if not created_at_str:
                        self.write_safe(f"No created_at date found in WP response for {model_name}: {slug}\n", self.style.WARNING)
                        total_failed += 1
                        continue

                    dt = parse_wp_datetime(created_at_str)
                    if not dt:
                        self.write_safe(f"Invalid date format '{created_at_str}' for {model_name}: {slug}\n", self.style.WARNING)
                        total_failed += 1
                        continue

                    # Update the date field
                    if date_field == 'publish_date' and hasattr(item, 'publish_date'):
                        item.publish_date = dt
                        item.save(update_fields=['publish_date'])
                    else:
                        model.objects.filter(pk=item.pk).update(created_at=dt)

                    self.write_safe(f"Synced {model_name} '{slug}' -> {dt}\n", self.style.SUCCESS)
                    total_synced += 1

                except WPImporterError as e:
                    self.write_safe(f"Error fetching {model_name} '{slug}': {e}\n", self.style.ERROR)
                    total_failed += 1
                except Exception as e:
                    self.write_safe(f"Unexpected error for {model_name} '{slug}': {e}\n", self.style.ERROR)
                    total_failed += 1

        self.write_safe(f"=== Sync Completed: {total_synced} synced successfully, {total_failed} failed ===\n", self.style.SUCCESS)
