from django.core.management.base import BaseCommand
from apps.articles.models import Article
import re


CLEAN_TUITION_HTML_TABLE = """
<div class="my-8 overflow-x-auto border border-gray-200 rounded-xl shadow-sm bg-white">
    <table class="w-full text-right text-sm border-collapse">
        <thead>
            <tr class="bg-gray-100 border-b border-gray-200 text-gray-900 font-bold">
                <th class="p-4 border-l">الجامعة الماليزية</th>
                <th class="p-4 border-l">نوع الجامعة</th>
                <th class="p-4 border-l">متوسط المصاريف السنوية (USD)</th>
                <th class="p-4">أبرز التخصصات المتاحة</th>
            </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 text-gray-800">
            <tr class="hover:bg-gray-50">
                <td class="p-4 border-l font-semibold">جامعة UKM (Universiti Kebangsaan Malaysia)</td>
                <td class="p-4 border-l"><span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">حكومية</span></td>
                <td class="p-4 border-l">$3,200 - $4,800</td>
                <td class="p-4">علوم الحاسوب، الهندسة، الطب</td>
            </tr>
            <tr class="hover:bg-gray-50">
                <td class="p-4 border-l font-semibold">جامعة UPM (Universiti Putra Malaysia)</td>
                <td class="p-4 border-l"><span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">حكومية</span></td>
                <td class="p-4 border-l">$3,000 - $4,500</td>
                <td class="p-4">العلوم الزراعية، التقنية، إدارة الأعمال</td>
            </tr>
            <tr class="hover:bg-gray-50">
                <td class="p-4 border-l font-semibold">جامعة APU (Asia Pacific University)</td>
                <td class="p-4 border-l"><span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">خاصة رائدة</span></td>
                <td class="p-4 border-l">$5,500 - $7,200</td>
                <td class="p-4">الذكاء الاصطناعي، الأمن السيبراني، التكنولوجيا</td>
            </tr>
            <tr class="hover:bg-gray-50">
                <td class="p-4 border-l font-semibold">جامعة INTI International University</td>
                <td class="p-4 border-l"><span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">خاصة دولية</span></td>
                <td class="p-4 border-l">$4,800 - $6,500</td>
                <td class="p-4">إدارة الأعمال، التمريض، التصميم</td>
            </tr>
        </tbody>
    </table>
</div>
"""


class Command(BaseCommand):
    help = 'Clean leftover WordPress shortcodes and convert [wptb] tables to clean responsive HTML tables.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Scan and report changes without saving.')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        articles = Article.objects.filter(publish_status='published')
        updated_count = 0

        self.stdout.write(self.style.MIGRATE_HEADING("=== Content QA & Shortcode Conversion ==="))

        for article in articles:
            content = article.content or ''
            if '[wptb' in content:
                # Replace wptb shortcode with clean responsive HTML table
                new_content = re.sub(r'\[wptb\s+id=\d+\]', CLEAN_TUITION_HTML_TABLE, content)
                
                if new_content != content:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"Article ID {article.id} | Slug: {article.slug} -> Replaced [wptb] shortcode with clean HTML table."))
                    
                    if not dry_run:
                        article.content = new_content
                        article.save()

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry run complete: {updated_count} article(s) would be updated."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Content QA complete: Successfully cleaned {updated_count} article(s)."))
