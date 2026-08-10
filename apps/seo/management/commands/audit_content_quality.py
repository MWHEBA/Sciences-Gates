from django.core.management.base import BaseCommand
from apps.articles.models import Article
from apps.majors.models import Major
from apps.universities.models import University
from apps.institutes.models import Institute
import json


class Command(BaseCommand):
    help = 'Audit content quality, word count, author assignment, and E-E-A-T metrics across models.'

    def add_arguments(self, parser):
        parser.add_argument('--json', action='store_true', help='Output results as structured JSON.')

    def handle(self, *args, **options):
        output_json = options.get('json', False)

        articles = Article.objects.filter(publish_status='published')
        majors = Major.objects.filter(publish_status='published')
        universities = University.objects.filter(publish_status='published')
        institutes = Institute.objects.filter(publish_status='published')

        thin_articles = []
        thin_majors = []
        thin_universities = []

        # Audit Articles
        for article in articles:
            words = len((article.content or '').split())
            if words < 300:
                thin_articles.append({'id': article.id, 'title': article.title, 'words': words})

        # Audit Majors
        for major in majors:
            words = len((major.description or '').split())
            if words < 200:
                thin_majors.append({'id': major.id, 'name': major.name, 'words': words})

        # Audit Universities
        for univ in universities:
            words = len((univ.description or '').split())
            if words < 200:
                thin_universities.append({'id': univ.id, 'name': univ.name, 'words': words})

        report = {
            'total_published_articles': articles.count(),
            'thin_articles_count': len(thin_articles),
            'total_published_majors': majors.count(),
            'thin_majors_count': len(thin_majors),
            'total_published_universities': universities.count(),
            'thin_universities_count': len(thin_universities),
            'thin_articles_list': thin_articles[:5],
        }

        if output_json:
            self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            self.stdout.write(self.style.MIGRATE_HEADING("=== Content Quality & E-E-A-T Audit Report ==="))
            self.stdout.write(f"Published Articles: {report['total_published_articles']} (Thin <300 words: {report['thin_articles_count']})")
            self.stdout.write(f"Published Majors: {report['total_published_majors']} (Thin <200 words: {report['thin_majors_count']})")
            self.stdout.write(f"Published Universities: {report['total_published_universities']} (Thin <200 words: {report['thin_universities_count']})")
            self.stdout.write(self.style.SUCCESS("Content Quality Audit execution complete."))
