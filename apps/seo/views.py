"""
SEO views for robots.txt and other SEO-related endpoints.
"""
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings


@require_http_methods(["GET"])
def robots_txt(request):
    """
    Generate robots.txt file for search engine crawlers.
    
    Returns a text/plain response with robots.txt directives.
    """
    robots_content = """# Science Gates Platform - robots.txt
# Generated for search engine optimization

User-agent: *
Allow: /
Disallow: /admin/
Disallow: /dashboard/
Disallow: /api/
Disallow: /static/
Disallow: /media/
Disallow: /*.json$
Disallow: /?*
Disallow: /*?*

# Specific rules for search engines
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

# Crawl delay (in seconds)
Crawl-delay: 1

# Sitemap location
Sitemap: {sitemap_url}
""".format(
        sitemap_url=request.build_absolute_uri('/sitemap.xml')
    )
    
    return HttpResponse(robots_content, content_type='text/plain')
