import re
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from apps.dashboard.mixins import ContentAdminRequiredMixin
from apps.core.models import MediaFile
from .services.wp_client import WPImporterClient, WPImporterError, WPNotFoundError, WPAuthError, WPConnectionError
from .services.image_downloader import download_and_optimize_image
from .services.content_mapper import ContentMapper


class ImportPageView(ContentAdminRequiredMixin, View):
    """
    Renders the import URL input form.
    صفحة استيراد المحتوى من الموقع القديم.
    """
    template_name = 'dashboard/import/index.html'

    def get(self, request):
        context = {
            'page_title': 'استيراد المحتوى من WordPress',
        }
        return render(request, self.template_name, context)


class ImportFetchView(ContentAdminRequiredMixin, View):
    """
    Handles fetching content from the WordPress API and downloading files.
    يستدعي موقع ووردبريس ويقوم بتحميل الصور وتحويل البيانات.
    """

    def post(self, request):
        url = request.POST.get('url', '').strip()
        if not url:
            return JsonResponse({'success': False, 'error': 'الرجاء إدخال الرابط.'}, status=400)

        # Extract slug from URL
        try:
            # Strip query params
            url_clean = url.split('?')[0].rstrip('/')
            if not url_clean:
                raise ValueError()
            slug = url_clean.split('/')[-1]
            if not slug:
                raise ValueError()
            import urllib.parse
            slug = urllib.parse.unquote(slug)
        except Exception:
            return JsonResponse({'success': False, 'error': 'الرابط المدخل غير صالح.'}, status=400)

        content_type_override = request.POST.get('content_type_override', 'auto').strip()

        # 1. Fetch content from WP
        client = WPImporterClient()
        try:
            wp_data = client.fetch(slug)
        except WPNotFoundError:
            return JsonResponse({'success': False, 'error': 'المقال غير موجود في الموقع القديم.'}, status=404)
        except WPAuthError:
            return JsonResponse({'success': False, 'error': 'مفتاح الاتصال (SECRET_KEY) غير صحيح. يرجى مراجعة إعدادات السيرفر.'}, status=502)
        except WPConnectionError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=503)
        except WPImporterError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

        # Apply manual type override if requested
        if content_type_override in ['university', 'institute', 'major']:
            wp_data['content_type'] = content_type_override

        # 2. Resolve image source types based on content type
        content_type = wp_data.get('content_type', 'university')
        
        main_image_source = MediaFile.SourceType.UNIVERSITY_IMAGE
        if content_type == 'institute':
            main_image_source = MediaFile.SourceType.INSTITUTE_IMAGE
        elif content_type == 'major':
            main_image_source = MediaFile.SourceType.MAJOR_IMAGE

        # 3. Download images (partial success)
        images_to_download = wp_data.get('images', {})
        downloaded_images = {}
        image_warnings = []

        # Download Logo
        logo_data = images_to_download.get('logo', {})
        if logo_data and logo_data.get('url'):
            media_file, warning = download_and_optimize_image(
                url=logo_data['url'],
                alt_text=logo_data.get('alt', ''),
                caption=logo_data.get('caption', ''),
                description=logo_data.get('description', ''),
                title=logo_data.get('title', ''),
                source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
                user=request.user
            )
            if media_file:
                downloaded_images['logo'] = media_file
            else:
                image_warnings.append(warning)

        # Download Main Image
        main_img_data = images_to_download.get('main_image', {})
        if main_img_data and main_img_data.get('url'):
            media_file, warning = download_and_optimize_image(
                url=main_img_data['url'],
                alt_text=main_img_data.get('alt', ''),
                caption=main_img_data.get('caption', ''),
                description=main_img_data.get('description', ''),
                title=main_img_data.get('title', ''),
                source_type=main_image_source,
                user=request.user
            )
            if media_file:
                downloaded_images['main_image'] = media_file
            else:
                image_warnings.append(warning)

        # Download OG Image
        og_img_data = images_to_download.get('og_image', {})
        if og_img_data and og_img_data.get('url'):
            media_file, warning = download_and_optimize_image(
                url=og_img_data['url'],
                alt_text=og_img_data.get('alt', ''),
                caption=og_img_data.get('caption', ''),
                description=og_img_data.get('description', ''),
                title=og_img_data.get('title', ''),
                source_type=MediaFile.SourceType.EDITOR,
                user=request.user
            )
            if media_file:
                downloaded_images['og_image'] = media_file
            else:
                image_warnings.append(warning)

        # 4. Map content schema
        mapper = ContentMapper()
        mapped_data = mapper.map_data(wp_data, downloaded_images, image_warnings)

        return JsonResponse({
            'success': True,
            'content_type': content_type,
            'mapped_data': mapped_data,
            'redirect_url': mapped_data['redirect_url']
        })
