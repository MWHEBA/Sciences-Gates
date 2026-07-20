import json
import logging
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.template import Template, Context
from django.db.utils import OperationalError, ProgrammingError
from apps.core.models import SiteSettings

logger = logging.getLogger(__name__)


class MaintenanceModeMiddleware:
    """
    Middleware that intercepts requests and displays a maintenance page 
    if maintenance mode is enabled in SiteSettings.
    Uses a local JSON cache to prevent database lookups on every request,
    and renders the page without context processors to prevent DB hits.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache_file = settings.BASE_DIR / 'cache' / 'maintenance_state.json'

    def __call__(self, request):
        state = self.get_maintenance_state(request)
        if not state or not state.get('maintenance_mode', False):
            return self.get_response(request)

        # 1. Path Exclusions (Normalized to handle trailing slashes)
        path = request.path.rstrip('/')
        admin_prefix = f"/{settings.ADMIN_URL.strip('/')}"
        static_prefix = settings.STATIC_URL.rstrip('/')
        media_prefix = settings.MEDIA_URL.rstrip('/')
        
        excluded_prefixes = [
            admin_prefix,
            f"/{settings.DASHBOARD_URL.strip('/')}",
            static_prefix,
            media_prefix,
            '/importer',
        ]
        
        if any(path == prefix or path.startswith(prefix + '/') for prefix in excluded_prefixes):
            return self.get_response(request)

        # 2. Staff Bypass (requires database session & auth)
        if state.get('maintenance_bypass_staff', True) and request.user.is_authenticated and request.user.is_staff:
            return self.get_response(request)

        # 3. IP Whitelist Bypass
        bypass_ips_raw = state.get('maintenance_bypass_ips', '')
        if bypass_ips_raw:
            client_ip = self.get_client_ip(request)
            allowed_ips = [ip.strip() for ip in bypass_ips_raw.replace('\r', '').split('\n') if ip.strip()]
            allowed_ips.extend([ip.strip() for ip in bypass_ips_raw.split(',') if ip.strip()])
            if client_ip in allowed_ips:
                return self.get_response(request)

        # 4. Render using Django Template without Context Processors
        return self.render_maintenance_response(state)

    def get_maintenance_state(self, request=None):
        """Reads maintenance config from local JSON file; regenerates from DB if missing."""
        from django.conf import settings
        if getattr(settings, 'TESTING', False) or 'test' in sys.argv or 'pytest' in sys.modules:
            try:
                db_settings = SiteSettings.get_settings()
                # Cache on request to avoid duplicate DB hit from site_settings_context
                if request is not None:
                    request._site_settings = db_settings
                return {
                    'maintenance_mode': db_settings.maintenance_mode,
                    'maintenance_bypass_staff': db_settings.maintenance_bypass_staff,
                    'maintenance_bypass_ips': db_settings.maintenance_bypass_ips,
                    'maintenance_title': db_settings.maintenance_title,
                    'maintenance_message': db_settings.maintenance_message,
                    'maintenance_estimated_end': db_settings.maintenance_estimated_end.isoformat() if db_settings.maintenance_estimated_end else None,
                    'whatsapp': db_settings.whatsapp,
                    'email': db_settings.email,
                    'phone': db_settings.phone,
                }
            except Exception:
                return None

        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Regenerate if file missing
            db_settings = SiteSettings.get_settings()
            db_settings.update_maintenance_cache()
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except (OperationalError, ProgrammingError, AttributeError):
            # Safe fallback if tables don't exist yet (e.g. during migration)
            return None
        except Exception as e:
            logger.error(f"Error reading maintenance state: {e}")
            return None

    def render_maintenance_response(self, state):
        """Renders maintenance page using raw Django Context to bypass context processors."""
        try:
            template_path = settings.BASE_DIR / 'templates' / 'maintenance.html'
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            else:
                # Minimum Inline Fallback if template is deleted
                template_content = "<html><body><h1>Site Under Maintenance</h1><p>{{ message }}</p></body></html>"
            whatsapp_num = state.get('whatsapp')
            cleaned_whatsapp = ""
            if whatsapp_num:
                import re
                cleaned_whatsapp = re.sub(r'\D', '', whatsapp_num)
                if cleaned_whatsapp.startswith('00'):
                    cleaned_whatsapp = cleaned_whatsapp[2:]
                if cleaned_whatsapp.startswith('2001'):
                    cleaned_whatsapp = '20' + cleaned_whatsapp[3:]
                elif cleaned_whatsapp.startswith('96605'):
                    cleaned_whatsapp = '966' + cleaned_whatsapp[4:]
                elif cleaned_whatsapp.startswith('6001'):
                    cleaned_whatsapp = '60' + cleaned_whatsapp[3:]

            context_data = {
                'title': state.get('maintenance_title', 'صيانة مجدولة'),
                'message': state.get('maintenance_message', 'الموقع قيد الصيانة حالياً. سنعود قريباً.'),
                'whatsapp': cleaned_whatsapp,
                'email': state.get('email'),
                'phone': state.get('phone'),
                'estimated_end': state.get('maintenance_estimated_end'),
            }

            # Parse estimated end time to calculate remaining seconds for JS countdown
            est_end_str = state.get('maintenance_estimated_end')
            if est_end_str:
                from django.utils.dateparse import parse_datetime
                est_end = parse_datetime(est_end_str)
                if est_end and est_end > timezone.now():
                    context_data['remaining_seconds'] = int((est_end - timezone.now()).total_seconds())

            # Rendering WITHOUT RequestContext to bypass context processors
            template = Template(template_content)
            html_content = template.render(Context(context_data))
            
            response = HttpResponse(html_content, status=503, content_type='text/html; charset=utf-8')
            
            # Set SEO Retry-After Header
            if 'remaining_seconds' in context_data:
                response['Retry-After'] = str(context_data['remaining_seconds'])
            else:
                response['Retry-After'] = '3600'  # 1 hour default
                
            return response
        except Exception as e:
            logger.error(f"Failed rendering maintenance response: {e}")
            return HttpResponse("الموقع قيد الصيانة حالياً. سنعود قريباً.", status=503, content_type='text/plain; charset=utf-8')

    def get_client_ip(self, request):
        # Support Cloudflare connecting IP header first
        cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_ip:
            return cf_ip.strip()
            
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
