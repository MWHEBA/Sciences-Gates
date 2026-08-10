from django.core.management.base import BaseCommand
from apps.articles.models import Article
import re


class Command(BaseCommand):
    help = 'Scan all published articles for leftover WordPress shortcodes (e.g. [wptb], [gallery]).'

    def handle(self, *args, **options):
        articles = Article.objects.filter(publish_status='published')
        shortcode_pattern = re.compile(r'\[([a-zA-Z0-9_\-]+)[^\]]*\]')
        found_count = 0

        self.stdout.write(self.style.MIGRATE_HEADING("=== WordPress Shortcodes Scan Report ==="))

        for article in articles:
            matches = shortcode_pattern.findall(article.content or '')
            if matches:
                found_count += 1
                unique_matches = set(matches)
                self.stdout.write(
                    self.style.WARNING(f"Article ID {article.id} | Slug: {article.slug} | Shortcodes: {', '.join(unique_matches)}")
                )

        if found_count == 0:
            self.stdout.write(self.style.SUCCESS("No leftover shortcodes found in published articles."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Scan complete: Found shortcodes in {found_count} article(s)."))
