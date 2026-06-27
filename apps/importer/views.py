import re
import os
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from apps.dashboard.mixins import ContentAdminRequiredMixin
from apps.core.models import MediaFile
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article
from .services.wp_client import WPImporterClient, WPImporterError, WPNotFoundError, WPAuthError, WPConnectionError
from .services.image_downloader import download_and_optimize_image
from .services.content_mapper import ContentMapper


class ImportPageView(ContentAdminRequiredMixin, View):
    """
    Renders the import URL input form and list of imported links.
    صفحة استيراد المحتوى من الموقع القديم وقائمة الروابط المستوردة.
    """
    template_name = 'dashboard/import/index.html'

    def _parse_imported_links(self):
        sections = {
            'universities': [],
            'institutes': [],
            'articles': [],
            'majors': []
        }
        
        md_path = settings.BASE_DIR / 'imported_links_summary.md'
        if not os.path.exists(md_path):
            return sections
            
        current_section = None
        
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Detect section
                    if line.startswith('## '):
                        if 'الجامعات' in line or 'Universities' in line:
                            current_section = 'universities'
                        elif 'المعاهد' in line or 'Institutes' in line:
                            current_section = 'institutes'
                        elif 'المقالات' in line or 'Articles' in line:
                            current_section = 'articles'
                        elif 'التخصصات' in line or 'Majors' in line:
                            current_section = 'majors'
                        else:
                            current_section = None
                        continue
                        
                    if not current_section:
                        continue
                        
                    # Parse table row
                    if line.startswith('|') and not line.startswith('|-') and not 'الرقم' in line and '---' not in line:
                        temp_line = line.replace(r'\|', ' - ')
                        parts = [p.strip() for p in temp_line.split('|')]
                        
                        if parts and parts[0] == '':
                            parts = parts[1:]
                        if parts and parts[-1] == '':
                            parts = parts[:-1]
                            
                        if len(parts) >= 3:
                            number = parts[0]
                            title = parts[1]
                            
                            if current_section == 'universities' and len(parts) >= 5:
                                category = parts[2]
                                link_part = parts[3]
                                slug_part = parts[4]
                            else:
                                category = ''
                                link_part = parts[2]
                                slug_part = parts[3] if len(parts) > 3 else ''
                                
                            # Extract URL from markdown link [Text](URL)
                            url_match = re.search(r'\((https?://[^\)]+)\)', link_part)
                            url = url_match.group(1) if url_match else link_part
                            
                            slug = slug_part.replace('`', '').strip()
                            
                            sections[current_section].append({
                                'number': number,
                                'title': title,
                                'category': category,
                                'url': url,
                                'slug': slug
                            })
        except Exception:
            pass
            
        return sections

    def get(self, request):
        sections = self._parse_imported_links()
        
        # Check database existence for each item
        existing_universities = set(University.objects.values_list('slug', flat=True))
        existing_institutes = set(Institute.objects.values_list('slug', flat=True))
        existing_majors = set(Major.objects.values_list('slug', flat=True))
        existing_articles = set(Article.objects.values_list('slug', flat=True))
        
        for item in sections['universities']:
            item['imported'] = item['slug'] in existing_universities
            
        for item in sections['institutes']:
            item['imported'] = item['slug'] in existing_institutes
            
        for item in sections['majors']:
            item['imported'] = item['slug'] in existing_majors
            
        for item in sections['articles']:
            item['imported'] = item['slug'] in existing_articles
            
        # Get count summaries
        counts = {
            'universities': len(sections['universities']),
            'institutes': len(sections['institutes']),
            'majors': len(sections['majors']),
            'articles': len(sections['articles']),
            'total': sum(len(v) for v in sections.values())
        }
            
        context = {
            'page_title': 'استيراد المحتوى من WordPress',
            'sections': sections,
            'counts': counts,
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
        if content_type_override in ['university', 'institute', 'major', 'article']:
            wp_data['content_type'] = content_type_override

        # 2. Resolve image source types based on content type
        content_type = wp_data.get('content_type', 'university')
        
        main_image_source = MediaFile.SourceType.UNIVERSITY_IMAGE
        if content_type == 'institute':
            main_image_source = MediaFile.SourceType.INSTITUTE_IMAGE
        elif content_type == 'major':
            main_image_source = MediaFile.SourceType.MAJOR_IMAGE
        elif content_type == 'article':
            main_image_source = MediaFile.SourceType.ARTICLE_IMAGE

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
            if warning:
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
            if warning:
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
            if warning:
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


class ImportBulkSaveAPIView(ContentAdminRequiredMixin, View):
    """
    Handles sequential bulk saving of imported content from WP.
    يستدعي الووردبريس ويجلب البيانات ويحمل الصور ويحفظ مباشرة بقاعدة البيانات عبر الفورمز.
    """
    def post(self, request):
        url = request.POST.get('url', '').strip()
        if not url:
            return JsonResponse({'success': False, 'error': 'الرجاء إدخال الرابط.'}, status=400)

        # Extract slug from URL
        try:
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
        if content_type_override in ['university', 'institute', 'major', 'article']:
            wp_data['content_type'] = content_type_override

        content_type = wp_data.get('content_type', 'university')

        # 2. Resolve image source types
        main_image_source = MediaFile.SourceType.UNIVERSITY_IMAGE
        if content_type == 'institute':
            main_image_source = MediaFile.SourceType.INSTITUTE_IMAGE
        elif content_type == 'major':
            main_image_source = MediaFile.SourceType.MAJOR_IMAGE
        elif content_type == 'article':
            main_image_source = MediaFile.SourceType.ARTICLE_IMAGE

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
            if warning:
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
            if warning:
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
            if warning:
                image_warnings.append(warning)

        # 4. Map content schema
        mapper = ContentMapper()
        mapped_data = mapper.map_data(wp_data, downloaded_images, image_warnings)

        # 5. Save content using bulk_saver
        from .services.bulk_saver import save_imported_content
        try:
            saved_obj, action_type = save_imported_content(content_type, mapped_data, request.user)
            name = getattr(saved_obj, 'name', getattr(saved_obj, 'title', slug))
            return JsonResponse({
                'success': True,
                'content_type': content_type,
                'name': name,
                'id': saved_obj.id,
                'action': action_type,
                'image_warnings': image_warnings
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error bulk saving imported content: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f"فشل الحفظ في قاعدة البيانات: {str(e)}"
            }, status=400)

