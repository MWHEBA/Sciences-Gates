import json
from pathlib import Path
from django.test import TestCase
from django.core.management import call_command
from django.conf import settings
from apps.articles.models import Article
from apps.redirects.models import Redirect


class SlugOptimizationCommandTests(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title="اختبار مقال الدراسة في ماليزيا 2026 الدليل الشامل والكامل للطلاب العرب الراغبين في الالتحاق بالجامعات",
            slug="اختبار-مقال-الدراسة-في-ماليزيا-2026-الدليل-الشامل-والكامل-للطلاب-العرب-الراغبين-في-الالتحاق-بالجامعات",
            content="محتوى تجريبي",
            publish_status='published'
        )
        self.test_json = Path(settings.BASE_DIR) / 'test_slug_audit.json'

    def tearDown(self):
        if self.test_json.exists():
            self.test_json.unlink()

    def test_dry_run_command_generates_json(self):
        call_command('suggest_slug_optimizations', '--dry-run', '--file=test_slug_audit.json')
        self.assertTrue(self.test_json.exists())
        
        with open(self.test_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertGreater(len(data), 0)
            self.assertEqual(data[0]['model'], 'Article')
            self.assertNotIn('2026', data[0]['suggested_slug'])

    def test_apply_command_registers_301_redirect(self):
        old_url = self.article.get_absolute_url()
        call_command('suggest_slug_optimizations', '--dry-run', '--file=test_slug_audit.json')
        
        with open(self.test_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        data[0]['approved'] = True
        with open(self.test_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        call_command('suggest_slug_optimizations', '--apply', '--file=test_slug_audit.json')
        
        self.article.refresh_from_db()
        self.assertNotIn('2026', self.article.slug)
        
        # Verify 301 Redirect was registered
        redirect_exists = Redirect.objects.filter(old_url=Redirect.normalize_path(old_url)).exists()
        self.assertTrue(redirect_exists)
