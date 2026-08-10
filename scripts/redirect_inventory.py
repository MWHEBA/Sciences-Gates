"""
Redirect and Legacy URL Inventory Script for Sciences Gates
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
import django
django.setup()

from django.test import Client
from apps.articles.models import Article

def inventory_redirects():
    client = Client()
    print("=" * 80)
    print("REDIRECT & LEGACY URL INVENTORY AUDIT")
    print("=" * 80)

    test_paths = [
        '/contact/',
        '/indexnow.txt',
        '/c7a8b9f0e1d2c3b4a5f6e7d8c9b0a1f2.txt',
        '/sitemap.xml',
        '/robots.txt',
    ]

    # Add sample legacy article slugs
    legacy_articles = Article.objects.filter(is_legacy=True)[:5]
    for art in legacy_articles:
        test_paths.append(f'/{art.slug}/')

    for path in test_paths:
        res = client.get(path, follow=False)
        target = res.get('Location', '') if res.status_code in [301, 302, 307, 308] else 'Direct Page'
        print(f"Path: {path:<40} | Status: {res.status_code} | Destination: {target}")

    print("=" * 80)

if __name__ == '__main__':
    inventory_redirects()
