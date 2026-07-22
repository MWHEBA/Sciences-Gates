import logging
from django.db import transaction
from .models import Page404Log

logger = logging.getLogger(__name__)


class Page404TrackingMiddleware:
    """
    Middleware to log 404 responses to the database.
    يتتبع محاولات دخول الصفحات التي تعطي خطأ 404 بدقة متناهية.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code == 404:
            path = request.path
            path_lower = path.lower()

            # Ignore typical static files, media files, and system requests to reduce noise
            ignored_prefixes = ['/static/', '/media/', '/apple-touch-icon', '/favicon.ico']
            ignored_extensions = (
                '.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js', '.ico',
                '.txt', '.xml', '.map', '.woff', '.woff2', '.ttf', '.eot', '.webmanifest'
            )

            if any(path_lower.startswith(prefix) for prefix in ignored_prefixes):
                return response
            if path_lower.endswith(ignored_extensions):
                return response

            # Log the 404 occurrence
            self.log_404(request, path)

        return response

    def log_404(self, request, path):
        referer = request.META.get('HTTP_REFERER', 'direct')
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')

        try:
            with transaction.atomic():
                log, created = Page404Log.objects.select_for_update().get_or_create(path=path)
                if log.is_ignored:
                    return
                log.hits += 1

                # Update referrers dictionary
                ref_dict = log.referrers or {}
                ref_dict[referer] = ref_dict.get(referer, 0) + 1
                log.referrers = ref_dict

                # Update user agents dictionary (truncated to avoid bloating JSON)
                ua_dict = log.user_agents or {}
                ua_short = user_agent[:150]
                ua_dict[ua_short] = ua_dict.get(ua_short, 0) + 1
                log.user_agents = ua_dict

                log.save()
        except Exception as exc:
            logger.warning("Page404TrackingMiddleware: Failed to log 404 for path %s: %s", path, exc)
