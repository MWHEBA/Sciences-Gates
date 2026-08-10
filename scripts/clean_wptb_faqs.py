#!/usr/bin/env python
"""
Migration & Audit Script for cleaning WPTB shortcodes from ArticleFAQ and Article content.
Logs old content, timestamp, and new sanitized content.
"""
import os
import sys
import django
from datetime import datetime

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.articles.models import Article, ArticleFAQ

def run_wptb_faq_migration():
    print("=" * 80)
    print(f"STARTING WPTB & FAQ MIGRATION AUDIT AT {datetime.now().isoformat()}")
    print("=" * 80)

    # 1. Audit ArticleFAQ records containing [wptb
    faq_matches = ArticleFAQ.objects.filter(answer__icontains="[wptb")
    print(f"Found {faq_matches.count()} ArticleFAQ records containing [wptb shortcode.")

    for faq in list(faq_matches):
        print(f"\n--- FAQ ID: {faq.id} (Article: {faq.article.title}) ---")
        print(f"OLD ANSWER:\n{faq.answer}")
        
        # Sanitize: if [wptb id=14730] in answer, replace or clean
        import re
        sanitized = re.sub(r'\[wptb[^\]]*\]', '', faq.answer).strip()
        if not sanitized or len(sanitized) < 10:
            print("Action: Deleting empty/broken FAQ record.")
            faq.delete()
        else:
            print(f"NEW SANITIZED ANSWER:\n{sanitized}")
            faq.answer = sanitized
            faq.save()

    # 2. Audit Article content containing [wptb
    art_matches = Article.objects.filter(content__icontains="[wptb")
    print(f"\nFound {art_matches.count()} Article records containing [wptb shortcode in main content.")

    for art in list(art_matches):
        print(f"\n--- ARTICLE ID: {art.id} ({art.title}) ---")
        import re
        sanitized = re.sub(r'\[wptb[^\]]*\]', '', art.content).strip()
        art.content = sanitized
        art.save()
        print(f"Cleaned [wptb] shortcode from Article ID {art.id}.")

    print("=" * 80)
    print("MIGRATION & AUDIT COMPLETED SUCCESSFULLY.")
    print("=" * 80)

if __name__ == "__main__":
    run_wptb_faq_migration()
