"""
Middleware for handling URL redirects.
"""
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
        # Get the request path (without query string)
        request_path = request.path
        
        # Check both the path as requested, and with/without trailing slash
        paths_to_check = [request_path]
        if request_path.endswith('/'):
            paths_to_check.append(request_path[:-1])
        else:
            paths_to_check.append(request_path + '/')
            
        # Try to find an active redirect matching the old URL
        redirect = Redirect.objects.filter(
            old_url__in=paths_to_check,
            is_active=True
        ).first()
        
        if redirect:
            # Perform atomic update on database without model save lifecycle overhead
            from django.db.models import F
            Redirect.objects.filter(id=redirect.id).update(hit_count=F('hit_count') + 1)
            
            # Return 301 permanent redirect
            return HttpResponsePermanentRedirect(redirect.new_url)
        
        # No redirect found, continue with normal request processing
        return None
