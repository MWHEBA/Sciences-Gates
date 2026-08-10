"""
Automated Local SEO Audit Script for Sciences Gates
"""
import os
import sys
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
import django
django.setup()

from django.test import Client

def audit_url(client, path):
    response = client.get(path)
    if response.status_code != 200:
        return {'path': path, 'status': response.status_code, 'errors': ['Non-200 status code']}

    html = response.content.decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    issues = []

    # Title check
    title = soup.find('title')
    if not title or not title.string.strip():
        issues.append('Missing or empty <title>')

    # Meta description check
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if not meta_desc or not meta_desc.get('content', '').strip():
        issues.append('Missing or empty <meta name="description">')

    # Canonical check
    canonical = soup.find('link', attrs={'rel': 'canonical'})
    if not canonical or not canonical.get('href', '').strip():
        issues.append('Missing <link rel="canonical">')

    # Heading check
    h1_tags = soup.find_all('h1')
    if len(h1_tags) == 0:
        issues.append('Missing <h1> tag')
    elif len(h1_tags) > 1:
        issues.append(f'Multiple <h1> tags found ({len(h1_tags)})')

    # Images width/height check
    images_without_dims = [img.get('src') for img in soup.find_all('img') if not (img.get('width') and img.get('height'))]
    
    # JSON-LD Schema check
    json_ld_blocks = soup.find_all('script', type='application/ld+json')
    if not json_ld_blocks:
        issues.append('No JSON-LD schema blocks found')

    return {
        'path': path,
        'status': 200,
        'h1': h1_tags[0].get_text(strip=True) if h1_tags else None,
        'json_ld_count': len(json_ld_blocks),
        'images_without_dims_count': len(images_without_dims),
        'issues': issues,
    }

def run_audit():
    client = Client()
    paths = ['/', '/about-us/', '/contact/', '/universities/', '/articles/', '/indexnow.txt', '/sitemap.xml']
    
    print("=" * 80)
    print("SEO & INFRASTRUCTURE INTEGRITY AUDIT")
    print("=" * 80)

    for path in paths:
        res = audit_url(client, path)
        status_symbol = "[PASS]" if not res.get('issues') and res['status'] == 200 else "[WARN]"
        print(f"{status_symbol} Path: {res['path']} | Status: {res['status']} | JSON-LD: {res.get('json_ld_count', 0)} blocks | Issues: {len(res.get('issues', []))}")
        for issue in res.get('issues', []):
            print(f"    - {issue}")
    print("=" * 80)

if __name__ == '__main__':
    run_audit()
