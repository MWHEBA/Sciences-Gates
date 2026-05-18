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
        
        # Try to find an active redirect matching the old URL
        redirect = Redirect.objects.filter(
            old_url=request_path,
            is_active=True
        ).first()
        
        if redirect:
            # Increment hit count
            redirect.increment_hit_count()
            
            # Return 301 permanent redirect
            return HttpResponsePermanentRedirect(redirect.new_url)
        
        # No redirect found, continue with normal request processing
        return None
