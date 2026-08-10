"""
WPTB Shortcode & HTML Cleanup Pipeline with Content Integrity Report
"""
import os
import sys
import re
from bs4 import BeautifulSoup

# Setup Django Environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
import django
django.setup()

from apps.articles.models import Article

def get_content_metrics(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    words = len(text.split())
    tables = len(soup.find_all('table'))
    images = len(soup.find_all('img'))
    links = len([a for a in soup.find_all('a', href=True) if a['href'].startswith('/') or 'sciencesgates.com' in a['href']])
    return {
        'word_count': words,
        'table_count': tables,
        'image_count': images,
        'internal_links_count': links,
    }

def clean_wptb_html(content):
    if not content:
        return content

    # Remove raw [wptb id=...] shortcodes if present standalone
    content = re.sub(r'\[wptb\s+id=\d+[^\]]*\]', '', content, flags=re.IGNORECASE)

    soup = BeautifulSoup(content, 'html.parser')

    # Strip wptb-specific classes from elements while keeping structure
    for el in soup.find_all(True):
        if 'class' in el.attrs:
            classes = el['class']
            # Filter out classes starting with wptb-
            new_classes = [c for c in classes if not c.startswith('wptb-') and not c.startswith('edit-active')]
            if new_classes:
                el['class'] = new_classes
            else:
                del el['class']
        
        # Clean inline styles that conflict with theme
        if 'style' in el.attrs and 'wptb' in str(el.attrs.get('style', '')):
            del el['style']

    # Ensure tables have clean modern classes
    for table in soup.find_all('table'):
        table['class'] = ['article-table', 'w-full', 'text-right', 'border-collapse', 'my-6']

    return str(soup)

def run_pipeline():
    print("=" * 80)
    print("STARTING WPTB CLEANUP & CONTENT INTEGRITY PIPELINE")
    print("=" * 80)

    target_articles = Article.objects.filter(content__icontains='wptb')
    total_count = target_articles.count()
    print(f"Found {total_count} articles containing WPTB artifacts.")

    report = []
    
    for article in target_articles:
        metrics_before = get_content_metrics(article.content)
        
        cleaned_content = clean_wptb_html(article.content)
        
        metrics_after = get_content_metrics(cleaned_content)
        
        # Save updated content
        article.content = cleaned_content
        article.save(update_fields=['content'])

        report_entry = {
            'id': article.id,
            'slug': article.slug,
            'title': article.title,
            'before': metrics_before,
            'after': metrics_after,
        }
        report.append(report_entry)

    print("\n--- CONTENT INTEGRITY REPORT ---")
    for item in report:
        print(f"Article [{item['id']}] '{item['slug']}':")
        print(f"  Words : {item['before']['word_count']} -> {item['after']['word_count']}")
        print(f"  Tables: {item['before']['table_count']} -> {item['after']['table_count']}")
        print(f"  Images: {item['before']['image_count']} -> {item['after']['image_count']}")
        print(f"  Links : {item['before']['internal_links_count']} -> {item['after']['internal_links_count']}")

    remaining_wptb = Article.objects.filter(content__icontains='wptb').count()
    print("=" * 80)
    print(f"PIPELINE COMPLETE. Remaining WPTB matches in DB: {remaining_wptb}")
    print("=" * 80)

    assert remaining_wptb == 0, "Pipeline failed: WPTB artifacts still remain in DB!"

if __name__ == '__main__':
    run_pipeline()
