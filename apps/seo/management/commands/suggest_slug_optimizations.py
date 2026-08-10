import json
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article
from apps.redirects.models import Redirect


def clean_slug(slug):
    """
    Shorten bloated slugs and strip obsolete year tokens.
    """
    if not slug:
        return slug
        
    # Remove year tokens (2024, 2025, 2026, 2027)
    cleaned = re.sub(r'-(202[0-9])', '', slug)
    cleaned = re.sub(r'(202[0-9])-?', '', cleaned)
    
    # If slug is still too long, clean up redundant filler phrases
    if len(cleaned) > 90:
        cleaned = cleaned.replace('-في-ماليزيا', '')
        cleaned = cleaned.replace('الدراسة-في-ماليزيا-', '')
        cleaned = cleaned.replace('دليل-جامعة-', '')
        cleaned = cleaned.replace('دليل-', '')
        
    return cleaned.strip('-')


class Command(BaseCommand):
    help = "Suggest and apply URL slug optimizations with 301 redirect audit logging."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=True,
            help='Generate audit JSON file with suggested slug optimizations without saving to DB.'
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Apply approved slug changes from approved JSON file.'
        )
        parser.add_argument(
            '--file',
            type=str,
            default='slug_audit_metadata.json',
            help='Path to the JSON audit file.'
        )

    def handle(self, *args, **options):
        file_path = Path(settings.BASE_DIR) / options['file']
        
        if options['apply']:
            if not file_path.exists():
                self.stderr.write(self.style.ERROR(f"Approved file not found: {file_path}"))
                return
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            applied_count = 0
            for item in data:
                if not item.get('approved', False):
                    continue
                    
                model_name = item['model']
                pk = item['pk']
                old_url = item['old_url']
                new_slug = item['suggested_slug']
                
                model_map = {
                    'University': University,
                    'Institute': Institute,
                    'Major': Major,
                    'Article': Article
                }
                model_cls = model_map.get(model_name)
                if not model_cls:
                    continue
                    
                try:
                    obj = model_cls.objects.get(pk=pk)
                    obj.slug = new_slug
                    obj.save(update_fields=['slug'])
                    
                    new_url = obj.get_absolute_url()
                    
                    # Create or update 301 Permanent Redirect
                    Redirect.objects.update_or_create(
                        old_url=Redirect.normalize_path(old_url),
                        defaults={
                            'new_url': Redirect.normalize_path(new_url),
                            'is_active': True,
                            'notes': f'SEO Slug Optimization Migration: {old_url} -> {new_url}'
                        }
                    )
                    applied_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated {model_name} #{pk}: {old_url} -> {new_url} (301 Redirect registered)"))
                except model_cls.DoesNotExist:
                    self.stderr.write(self.style.WARNING(f"Object {model_name} #{pk} not found."))
                    
            self.stdout.write(self.style.SUCCESS(f"Successfully applied {applied_count} slug optimizations with 301 redirects."))
            return

        # Dry-run mode: scan models and output suggestions
        suggestions = []
        models = [
            (University, 'University', '/universities/'),
            (Institute, 'Institute', '/institutes/'),
            (Major, 'Major', '/majors/'),
            (Article, 'Article', '/articles/'),
        ]
        
        for model_cls, model_name, prefix in models:
            for obj in model_cls.objects.all():
                old_slug = getattr(obj, 'slug', '')
                if not old_slug:
                    continue
                    
                suggested_slug = clean_slug(old_slug)
                
                # Flag if slug exceeds 100 chars or contains '2026' or changed
                if len(old_slug) > 100 or '2026' in old_slug or suggested_slug != old_slug:
                    old_url = getattr(obj, 'get_absolute_url', lambda: f"{prefix}{old_slug}/")()
                    suggestions.append({
                        'model': model_name,
                        'pk': obj.pk,
                        'title': getattr(obj, 'name', getattr(obj, 'title', '')),
                        'old_slug': old_slug,
                        'old_slug_length': len(old_slug),
                        'old_url': old_url,
                        'suggested_slug': suggested_slug,
                        'suggested_slug_length': len(suggested_slug),
                        'approved': False
                    })
                    
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(suggestions, f, ensure_ascii=False, indent=2)
            
        self.stdout.write(self.style.SUCCESS(
            f"Generated {len(suggestions)} slug optimization suggestions in dry-run mode -> {file_path}.\n"
            "To apply changes: Set 'approved': true on desired items in JSON, then run:\n"
            "python manage.py suggest_slug_optimizations --apply"
        ))
