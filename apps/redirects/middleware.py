"""
Middleware for handling URL redirects.
"""
import posixpath
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin
from .models import Redirect


class RedirectMiddleware(MiddlewareMixin):
    """
    Middleware to handle 301 redirects for changed URLs.
    Checks if the requested path matches an active redirect and returns a 301 response.
    """

    def process_request(self, request):
        """
        Process incoming request to check for active redirects.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponsePermanentRedirect if a matching redirect is found, None otherwise
        """
        # Normalize request path to eliminate double slashes and dot segments
        raw_path = request.path or '/'
        normalized_path = posixpath.normpath(raw_path)
        if raw_path.endswith('/') and not normalized_path.endswith('/'):
            normalized_path += '/'

        # Exclude administrative, internal API, and media/static prefixes from DB redirects
        dashboard_prefix = f"/{getattr(settings, 'DASHBOARD_URL', 'sg/').strip('/')}"
        admin_prefix = f"/{getattr(settings, 'ADMIN_URL', 'mw-admin/').strip('/')}"
        static_prefix = getattr(settings, 'STATIC_URL', '/static/').rstrip('/')
        media_prefix = getattr(settings, 'MEDIA_URL', '/media/').rstrip('/')

        excluded_prefixes = [
            dashboard_prefix,
            admin_prefix,
            static_prefix,
            media_prefix,
            '/importer',
            '/api',
        ]

        normalized_clean = normalized_path.rstrip('/')
        if any(normalized_clean == prefix or normalized_path.startswith(f"{prefix}/") for prefix in excluded_prefixes if prefix):
            return None

        # Get the request path (without query string)
        request_path = normalized_path
        
        # Check both the path as requested, and with/without trailing slash + URL unquoted variants
        import urllib.parse
        base_paths = [request_path, urllib.parse.unquote(request_path)]
        paths_to_check = set()
        for p in base_paths:
            paths_to_check.add(p)
            if p.endswith('/'):
                paths_to_check.add(p[:-1])
            else:
                paths_to_check.add(p + '/')
            
        from django.core.cache import cache
        redirects_map = cache.get('active_redirects_dict')
        if redirects_map is None:
            redirects_map = {
                r['old_url']: (r['id'], r['new_url'])
                for r in Redirect.objects.filter(is_active=True).values('id', 'old_url', 'new_url')
            }
            cache.set('active_redirects_dict', redirects_map, 300)

        for path in paths_to_check:
            if path in redirects_map:
                red_id, new_url = redirects_map[path]
                from django.db.models import F
                Redirect.objects.filter(id=red_id).update(hit_count=F('hit_count') + 1)
                return HttpResponsePermanentRedirect(new_url)
        
        # No redirect found, continue with normal request processing
        return None
