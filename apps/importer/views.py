import re
import os
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

logger = logging.getLogger(__name__)
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
from .services.gemini_service import GeminiService

def update_env_file(key, value):
    env_path = os.path.join(settings.BASE_DIR, '.env')
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        replaced = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                replaced = True
            else:
                new_lines.append(line)
        if not replaced:
            new_lines.append(f"\n{key}={value}\n")
            
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    except Exception:
        pass



class ImportPageView(ContentAdminRequiredMixin, View):
    """
    Renders the import URL input form and list of imported links.
    صفحة استيراد المحتوى من الموقع القديم وقائمة الروابط المستوردة.
    """
    template_name = 'dashboard/import/index.html'

    def _parse_imported_links(self):
        sections = {
            'articles': [],
            'majors': []
        }
        
        md_path = settings.BASE_DIR / 'imported_links_summary.md'
        if not os.path.exists(md_path):
            return sections
            
        current_section = None
        
        try:
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(md_path, 'r', encoding='windows-1256') as f:
                    content = f.read()
            
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                    
                # Detect section
                if line.startswith('## '):
                    if 'المقالات' in line or 'Articles' in line:
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
                        number = parts[0].strip()
                        if not number.isdigit():
                            continue
                        title = parts[1]
                        
                        if current_section == 'majors' and len(parts) >= 5:
                            title = " - ".join(parts[1:-3]).strip()
                            category = ''
                            link_part = parts[-3]
                            slug_part = parts[-2]
                            # تنظيف وتجهيز رابط المنافس
                            competitor_url = parts[-1].replace('`', '').strip()
                            comp_match = re.search(r'\((https?://[^\)]+)\)', competitor_url)
                            if comp_match:
                                competitor_url = comp_match.group(1)
                        else:
                            title = " - ".join(parts[1:-2]).strip() if len(parts) >= 3 else parts[1]
                            category = ''
                            link_part = parts[-2] if len(parts) >= 3 else parts[1]
                            slug_part = parts[-1] if len(parts) >= 4 else ''
                            competitor_url = ''
                            
                        # Extract URL from markdown link [Text](URL)
                        url_match = re.search(r'\((https?://[^\)]+)\)', link_part)
                        url = url_match.group(1) if url_match else link_part
                        
                        slug = slug_part.replace('`', '').strip()
                        
                        sections[current_section].append({
                            'number': number,
                            'title': title,
                            'category': category,
                            'url': url,
                            'slug': slug,
                            'competitor_url': competitor_url
                        })
        except Exception:
            pass
            
        return sections

    def get(self, request):
        sections = self._parse_imported_links()
        
        # Check database existence for each item
        existing_majors = set(Major.objects.values_list('slug', flat=True))
        existing_articles = set(Article.objects.values_list('slug', flat=True))
        
        for item in sections['majors']:
            item['imported'] = item['slug'] in existing_majors
            
        for item in sections['articles']:
            item['imported'] = item['slug'] in existing_articles
            
        # Sort so that non-imported items (False) come first, and imported items (True) go to the bottom
        sections['majors'].sort(key=lambda x: x.get('imported', False))
        sections['articles'].sort(key=lambda x: x.get('imported', False))
            
        # Get count summaries
        counts = {
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


import threading
import json
from django.db import close_old_connections
from django.contrib.auth.models import User
from apps.importer.models import ImportJob

def run_in_background(target, *args, **kwargs):
    thread = threading.Thread(target=target, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()

def import_fetch_worker(job_id, url, competitor_url, content_type_override, user_id, lazy_images=False):
    try:
        user = User.objects.get(pk=user_id) if user_id else None
        job = ImportJob.objects.get(id=job_id)
        job.status = 'PROCESSING'
        job.progress = 10
        job.status_message = 'جاري استيراد وتجهيز البيانات والبرومبت...'
        job.save()

        # Extract slug from URL
        url_clean = url.split('?')[0].rstrip('/')
        slug = url_clean.split('/')[-1]
        import urllib.parse
        slug = urllib.parse.unquote(slug)

        job.progress = 20
        job.status_message = 'جاري استيراد وتجهيز البيانات والبرومبت...'
        job.save()

        # 1. Fetch content from WP
        client = WPImporterClient()
        wp_data = client.fetch(slug)

        if content_type_override in ['university', 'institute', 'major', 'article']:
            wp_data['content_type'] = content_type_override

        content_type = wp_data.get('content_type', 'university')

        job.progress = 40
        job.status_message = 'جاري استيراد وتجهيز البيانات والبرومبت...'
        job.save()

        # 2. Resolve image source types
        main_image_source = MediaFile.SourceType.UNIVERSITY_IMAGE
        logo_source = MediaFile.SourceType.UNIVERSITY_LOGO
        if content_type == 'institute':
            main_image_source = MediaFile.SourceType.INSTITUTE_IMAGE
            logo_source = MediaFile.SourceType.INSTITUTE_LOGO
        elif content_type == 'major':
            main_image_source = MediaFile.SourceType.MAJOR_IMAGE
        elif content_type == 'article':
            main_image_source = MediaFile.SourceType.ARTICLE_IMAGE

        # 3. Download images and get competitor content in parallel
        job.progress = 50
        job.status_message = 'جاري استيراد الصور وجلب بيانات المنافس بالتوازي...'
        job.save()

        images_to_download = wp_data.get('images', {})
        downloaded_images = {}
        image_warnings = []
        competitor_html = None
        comp_url = competitor_url
        if not comp_url and content_type == 'major':
            try:
                from apps.majors.models import Major
                existing_major = Major.objects.filter(slug=slug).first()
                if existing_major and existing_major.competitor_url:
                    comp_url = existing_major.competitor_url
            except Exception:
                pass

        from concurrent.futures import ThreadPoolExecutor

        def download_logo_task():
            from django.db import close_old_connections
            close_old_connections()
            try:
                logo_data = images_to_download.get('logo', {})
                if logo_data and logo_data.get('url'):
                    media_file, warning = download_and_optimize_image(
                        url=logo_data['url'],
                        alt_text=logo_data.get('alt', ''),
                        caption=logo_data.get('caption', ''),
                        description=logo_data.get('description', ''),
                        title=logo_data.get('title', ''),
                        source_type=logo_source,
                        user=user,
                        skip_if_exists=True
                    )
                    return ('logo', media_file, warning)
            except Exception as e:
                return ('logo', None, f"فشل تحميل شعار الجامعة: {str(e)}")
            finally:
                close_old_connections()
            return None

        def download_main_image_task():
            from django.db import close_old_connections
            close_old_connections()
            try:
                main_img_data = images_to_download.get('main_image', {})
                if main_img_data and main_img_data.get('url'):
                    media_file, warning = download_and_optimize_image(
                        url=main_img_data['url'],
                        alt_text=main_img_data.get('alt', ''),
                        caption=main_img_data.get('caption', ''),
                        description=main_img_data.get('description', ''),
                        title=main_img_data.get('title', ''),
                        source_type=main_image_source,
                        user=user,
                        skip_if_exists=True
                    )
                    return ('main_image', media_file, warning)
            except Exception as e:
                return ('main_image', None, f"فشل تحميل الصورة الرئيسية: {str(e)}")
            finally:
                close_old_connections()
            return None

        def download_og_image_task():
            from django.db import close_old_connections
            close_old_connections()
            try:
                og_img_data = images_to_download.get('og_image', {})
                if og_img_data and og_img_data.get('url'):
                    media_file, warning = download_and_optimize_image(
                        url=og_img_data['url'],
                        alt_text=og_img_data.get('alt', ''),
                        caption=og_img_data.get('caption', ''),
                        description=og_img_data.get('description', ''),
                        title=og_img_data.get('title', ''),
                        source_type=MediaFile.SourceType.EDITOR,
                        user=user,
                        skip_if_exists=True
                    )
                    return ('og_image', media_file, warning)
            except Exception as e:
                return ('og_image', None, f"فشل تحميل صورة شبكات التواصل: {str(e)}")
            finally:
                close_old_connections()
            return None

        def competitor_task():
            if content_type != 'major':
                return None
            from django.db import close_old_connections
            close_old_connections()
            try:
                cleaned_name = ContentMapper()._clean_importer_name(wp_data.get('name', ''))
                gemini = GeminiService()
                
                local_comp_url = comp_url
                local_warnings = []
                if not local_comp_url:
                    local_comp_url = gemini.search_competitor(cleaned_name)
                    if local_comp_url:
                        local_warnings.append(f"تم العثور على التخصص المطابق عند المنافس ودمجه تلقائياً: {local_comp_url}")
                else:
                    local_warnings.append(f"تم دمج محتوى المنافس من الرابط المدخل: {local_comp_url}")
                
                local_html = None
                if local_comp_url:
                    local_html = gemini.fetch_competitor_content(local_comp_url)
                
                return ('competitor', local_html, local_comp_url, local_warnings)
            except Exception as e:
                return ('competitor_error', str(e))
            finally:
                close_old_connections()

        # Execute parallel tasks
        if lazy_images:
            tasks = [competitor_task]
        else:
            tasks = [download_logo_task, download_main_image_task, download_og_image_task, competitor_task]

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(t) for t in tasks]
            for future in futures:
                res = future.result()
                if not res:
                    continue
                if res[0] in ('logo', 'main_image', 'og_image'):
                    _, media_file, warning = res
                    if media_file:
                        downloaded_images[res[0]] = media_file
                    if warning:
                        image_warnings.append(warning)
                elif res[0] == 'competitor':
                    _, competitor_html, comp_url, local_warnings = res
                    image_warnings.extend(local_warnings)
                elif res[0] == 'competitor_error':
                    image_warnings.append(f"فشل جلب بيانات المنافس: {res[1]}")

        job.progress = 85
        job.status_message = 'جاري دمج وتنسيق البيانات وتوليد البرومبت...'
        job.save()

        # 4. Map content schema
        mapper = ContentMapper()
        mapped_data = mapper.map_data(wp_data, downloaded_images, image_warnings)

        if lazy_images:
            mapped_data['images_to_download'] = wp_data.get('images', {})

        if content_type == 'major':
            if comp_url:
                mapped_data['competitor_url'] = comp_url
                mapped_data['form_initial']['competitor_url'] = comp_url
            
            gemini = GeminiService()
            # Always compile the prompt and save it in mapped_data
            compiled_prompt = gemini.build_prompt(mapped_data, competitor_html)
            mapped_data['compiled_prompt'] = compiled_prompt

        job.progress = 100
        job.status = 'SUCCESS'
        job.status_message = 'تم استخراج البيانات وتجهيز البرومبت بنجاح! 🚀'
        job.result_url = mapped_data.get('redirect_url', '')
        job.result_data = json.dumps({
            'success': True,
            'content_type': content_type,
            'mapped_data': mapped_data,
            'redirect_url': mapped_data.get('redirect_url', '')
        }, ensure_ascii=False)
        job.save()

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in import_fetch_worker: {e}\n{tb}")
        try:
            job = ImportJob.objects.get(id=job_id)
            job.status = 'FAILED'
            job.progress = 100
            job.status_message = 'فشلت عملية جلب وصياغة البيانات.'
            job.error_message = str(e)
            # Store partial result data containing mapped_data (and thus compiled_prompt) if available
            job.result_data = json.dumps({
                'success': False,
                'error': str(e),
                'content_type': content_type if 'content_type' in locals() else 'major',
                'mapped_data': mapped_data if 'mapped_data' in locals() else None,
            }, ensure_ascii=False)
            job.save()
        except Exception:
            pass
    finally:
        close_old_connections()

def import_bulk_save_worker(job_id, url, competitor_url, content_type_override, user_id):
    from .services.bulk_saver import save_imported_content
    try:
        user = User.objects.get(pk=user_id) if user_id else None
        job = ImportJob.objects.get(id=job_id)
        job.status = 'PROCESSING'
        job.progress = 10
        job.status_message = 'جاري استخراج الرمز التعريفي وجلب البيانات...'
        job.save()

        # Extract slug from URL
        url_clean = url.split('?')[0].rstrip('/')
        slug = url_clean.split('/')[-1]
        import urllib.parse
        slug = urllib.parse.unquote(slug)

        job.progress = 20
        job.status_message = 'جاري الاتصال بالموقع القديم وجلب المقال...'
        job.save()

        # 1. Fetch content from WP
        client = WPImporterClient()
        wp_data = client.fetch(slug)

        if content_type_override in ['university', 'institute', 'major', 'article']:
            wp_data['content_type'] = content_type_override

        content_type = wp_data.get('content_type', 'university')

        job.progress = 40
        job.status_message = 'تم جلب البيانات بنجاح، جاري تحميل وتحسين الصور...'
        job.save()

        # 2. Resolve image source types
        main_image_source = MediaFile.SourceType.UNIVERSITY_IMAGE
        logo_source = MediaFile.SourceType.UNIVERSITY_LOGO
        if content_type == 'institute':
            main_image_source = MediaFile.SourceType.INSTITUTE_IMAGE
            logo_source = MediaFile.SourceType.INSTITUTE_LOGO
        elif content_type == 'major':
            main_image_source = MediaFile.SourceType.MAJOR_IMAGE
        elif content_type == 'article':
            main_image_source = MediaFile.SourceType.ARTICLE_IMAGE

        # 3. Download images and get competitor content in parallel
        job.progress = 50
        job.status_message = 'جاري استيراد الصور وجلب بيانات المنافس بالتوازي...'
        job.save()

        images_to_download = wp_data.get('images', {})
        downloaded_images = {}
        image_warnings = []
        competitor_html = None
        comp_url = competitor_url
        if not comp_url and content_type == 'major':
            try:
                from apps.majors.models import Major
                existing_major = Major.objects.filter(slug=slug).first()
                if existing_major and existing_major.competitor_url:
                    comp_url = existing_major.competitor_url
            except Exception:
                pass

        from concurrent.futures import ThreadPoolExecutor

        def download_logo_task():
            from django.db import close_old_connections
            close_old_connections()
            try:
                logo_data = images_to_download.get('logo', {})
                if logo_data and logo_data.get('url'):
                    media_file, warning = download_and_optimize_image(
                        url=logo_data['url'],
                        alt_text=logo_data.get('alt', ''),
                        caption=logo_data.get('caption', ''),
                        description=logo_data.get('description', ''),
                        title=logo_data.get('title', ''),
                        source_type=logo_source,
                        user=user,
                        skip_if_exists=True
                    )
                    return ('logo', media_file, warning)
            except Exception as e:
                return ('logo', None, f"فشل تحميل شعار الجامعة: {str(e)}")
            finally:
                close_old_connections()
            return None

        def download_main_image_task():
            from django.db import close_old_connections
            close_old_connections()
            try:
                main_img_data = images_to_download.get('main_image', {})
                if main_img_data and main_img_data.get('url'):
                    media_file, warning = download_and_optimize_image(
                        url=main_img_data['url'],
                        alt_text=main_img_data.get('alt', ''),
                        caption=main_img_data.get('caption', ''),
                        description=main_img_data.get('description', ''),
                        title=main_img_data.get('title', ''),
                        source_type=main_image_source,
                        user=user,
                        skip_if_exists=True
                    )
                    return ('main_image', media_file, warning)
            except Exception as e:
                return ('main_image', None, f"فشل تحميل الصورة الرئيسية: {str(e)}")
            finally:
                close_old_connections()
            return None

        def download_og_image_task():
            from django.db import close_old_connections
            close_old_connections()
            try:
                og_img_data = images_to_download.get('og_image', {})
                if og_img_data and og_img_data.get('url'):
                    media_file, warning = download_and_optimize_image(
                        url=og_img_data['url'],
                        alt_text=og_img_data.get('alt', ''),
                        caption=og_img_data.get('caption', ''),
                        description=og_img_data.get('description', ''),
                        title=og_img_data.get('title', ''),
                        source_type=MediaFile.SourceType.EDITOR,
                        user=user,
                        skip_if_exists=True
                    )
                    return ('og_image', media_file, warning)
            except Exception as e:
                return ('og_image', None, f"فشل تحميل صورة شبكات التواصل: {str(e)}")
            finally:
                close_old_connections()
            return None

        def competitor_task():
            if content_type != 'major':
                return None
            from django.db import close_old_connections
            close_old_connections()
            try:
                cleaned_name = ContentMapper()._clean_importer_name(wp_data.get('name', ''))
                gemini = GeminiService()
                
                local_comp_url = comp_url
                local_warnings = []
                if not local_comp_url:
                    local_comp_url = gemini.search_competitor(cleaned_name)
                    if local_comp_url:
                        local_warnings.append(f"تم العثور على التخصص المطابق عند المنافس ودمجه تلقائياً: {local_comp_url}")
                else:
                    local_warnings.append(f"تم دمج محتوى المنافس من الرابط المدخل: {local_comp_url}")
                
                local_html = None
                if local_comp_url:
                    local_html = gemini.fetch_competitor_content(local_comp_url)
                
                return ('competitor', local_html, local_comp_url, local_warnings)
            except Exception as e:
                return ('competitor_error', str(e))
            finally:
                close_old_connections()

        # Execute parallel tasks
        tasks = [download_logo_task, download_main_image_task, download_og_image_task, competitor_task]
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(t) for t in tasks]
            for future in futures:
                res = future.result()
                if not res:
                    continue
                if res[0] in ('logo', 'main_image', 'og_image'):
                    _, media_file, warning = res
                    if media_file:
                        downloaded_images[res[0]] = media_file
                    if warning:
                        image_warnings.append(warning)
                elif res[0] == 'competitor':
                    _, competitor_html, comp_url, local_warnings = res
                    image_warnings.extend(local_warnings)
                elif res[0] == 'competitor_error':
                    image_warnings.append(f"فشل جلب بيانات المنافس: {res[1]}")

        job.progress = 80
        job.status_message = 'جاري دمج وتنسيق البيانات وتوليد البرومبت...'
        job.save()

        # 4. Map content schema
        mapper = ContentMapper()
        mapped_data = mapper.map_data(wp_data, downloaded_images, image_warnings)

        if content_type == 'major':
            if comp_url:
                mapped_data['competitor_url'] = comp_url
                mapped_data['form_initial']['competitor_url'] = comp_url
            
            gemini = GeminiService()
            # Always compile the prompt and save it in mapped_data
            compiled_prompt = gemini.build_prompt(mapped_data, competitor_html)
            mapped_data['compiled_prompt'] = compiled_prompt
            # Force Draft status
            mapped_data['form_initial']['publish_status'] = 'unpublished'

        job.progress = 88
        job.status_message = 'جاري حفظ البيانات مباشرة في قاعدة البيانات كـ مسودة...'
        job.save()

        # 5. Save content using bulk_saver
        saved_obj, action_type = save_imported_content(content_type, mapped_data, user)
        name = getattr(saved_obj, 'name', getattr(saved_obj, 'title', slug))

        job.progress = 100
        job.status = 'SUCCESS'
        job.status_message = 'تم الاستيراد والحفظ بنجاح!'
        job.result_data = json.dumps({
            'success': True,
            'content_type': content_type,
            'name': name,
            'id': saved_obj.id,
            'action': action_type,
            'image_warnings': image_warnings
        }, ensure_ascii=False)
        job.save()

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in import_bulk_save_worker: {e}\n{tb}")
        try:
            job = ImportJob.objects.get(id=job_id)
            job.status = 'FAILED'
            job.progress = 100
            job.status_message = 'فشلت عملية استيراد وحفظ المقال.'
            job.error_message = str(e)
            # Store partial result data containing mapped_data (and thus compiled_prompt) if available
            job.result_data = json.dumps({
                'success': False,
                'error': str(e),
                'content_type': content_type if 'content_type' in locals() else 'major',
                'mapped_data': mapped_data if 'mapped_data' in locals() else None,
            }, ensure_ascii=False)
            job.save()
        except Exception:
            pass
    finally:
        close_old_connections()


class ImportFetchView(ContentAdminRequiredMixin, View):
    """
    Handles starting the asynchronous WordPress import and rewrite task.
    """
    def post(self, request):
        url = request.POST.get('url', '').strip()
        competitor_url = request.POST.get('competitor_url', '').strip()
        if not url:
            return JsonResponse({'success': False, 'error': 'الرجاء إدخال الرابط.'}, status=400)

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

        # Create job tracker
        job = ImportJob.objects.create(
            url=url,
            content_type=content_type_override,
            status='PENDING',
            progress=0,
            status_message='بدء عملية جلب وصياغة البيانات...'
        )

        lazy_images = request.POST.get('lazy_images', '').lower() == 'true'

        run_in_background(
            import_fetch_worker,
            job_id=job.id,
            url=url,
            competitor_url=competitor_url,
            content_type_override=content_type_override,
            user_id=request.user.id if request.user else None,
            lazy_images=lazy_images
        )

        return JsonResponse({
            'success': True,
            'job_id': str(job.id)
        })


class ImportBulkSaveAPIView(ContentAdminRequiredMixin, View):
    """
    Handles starting the asynchronous WordPress import and direct save task.
    """
    def post(self, request):
        url = request.POST.get('url', '').strip()
        competitor_url = request.POST.get('competitor_url', '').strip()
        if not url:
            return JsonResponse({'success': False, 'error': 'الرجاء إدخال الرابط.'}, status=400)

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

        # Create job tracker
        job = ImportJob.objects.create(
            url=url,
            content_type=content_type_override,
            status='PENDING',
            progress=0,
            status_message='بدء عملية استيراد وحفظ المقال...'
        )

        run_in_background(
            import_bulk_save_worker,
            job_id=job.id,
            url=url,
            competitor_url=competitor_url,
            content_type_override=content_type_override,
            user_id=request.user.id if request.user else None
        )

        return JsonResponse({
            'success': True,
            'job_id': str(job.id)
        })


class ImportJobStatusView(ContentAdminRequiredMixin, View):
    """
    Returns progress and results of a background import task.
    """
    def get(self, request, job_id):
        try:
            job = ImportJob.objects.get(id=job_id)
            response_data = {
                'success': True,
                'status': job.status,
                'progress': job.progress,
                'status_message': job.status_message,
                'result_url': job.result_url,
                'error_message': job.error_message,
            }
            if job.status == 'SUCCESS' and job.result_data:
                response_data['result_data'] = json.loads(job.result_data)
            return JsonResponse(response_data)
        except ImportJob.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'العملية غير موجودة.'}, status=404)


class ImportSaveDraftView(ContentAdminRequiredMixin, View):
    """
    Saves the imported content as a draft after resolving lazy image downloads.
    """
    def post(self, request):
        try:
            body = json.loads(request.body)
            mapped_data = body.get('mapped_data')
            content_type = body.get('content_type', 'major')
        except Exception:
            return JsonResponse({'success': False, 'error': 'بيانات غير صالحة.'}, status=400)

        if not mapped_data:
            return JsonResponse({'success': False, 'error': 'البيانات فارغة.'}, status=400)

        images_to_download = mapped_data.get('images_to_download', {})
        downloaded_images = {}
        image_warnings = []

        # Resolve image source types
        main_image_source = MediaFile.SourceType.UNIVERSITY_IMAGE
        logo_source = MediaFile.SourceType.UNIVERSITY_LOGO
        if content_type == 'institute':
            main_image_source = MediaFile.SourceType.INSTITUTE_IMAGE
            logo_source = MediaFile.SourceType.INSTITUTE_LOGO
        elif content_type == 'major':
            main_image_source = MediaFile.SourceType.MAJOR_IMAGE
        elif content_type == 'article':
            main_image_source = MediaFile.SourceType.ARTICLE_IMAGE

        # 1. Download and optimize images synchronously before saving
        # Download logo
        logo_data = images_to_download.get('logo', {})
        if logo_data and logo_data.get('url'):
            try:
                media_file, warning = download_and_optimize_image(
                    url=logo_data['url'],
                    alt_text=logo_data.get('alt', ''),
                    caption=logo_data.get('caption', ''),
                    description=logo_data.get('description', ''),
                    title=logo_data.get('title', ''),
                    source_type=logo_source,
                    user=request.user,
                    skip_if_exists=True
                )
                if media_file:
                    downloaded_images['logo'] = media_file
                if warning:
                    image_warnings.append(warning)
            except Exception as e:
                image_warnings.append(f"فشل تحميل شعار الجامعة: {str(e)}")

        # Download main image
        main_img_data = images_to_download.get('main_image', {})
        if main_img_data and main_img_data.get('url'):
            try:
                media_file, warning = download_and_optimize_image(
                    url=main_img_data['url'],
                    alt_text=main_img_data.get('alt', ''),
                    caption=main_img_data.get('caption', ''),
                    description=main_img_data.get('description', ''),
                    title=main_img_data.get('title', ''),
                    source_type=main_image_source,
                    user=request.user,
                    skip_if_exists=True
                )
                if media_file:
                    downloaded_images['main_image'] = media_file
                if warning:
                    image_warnings.append(warning)
            except Exception as e:
                image_warnings.append(f"فشل تحميل الصورة الرئيسية: {str(e)}")

        # Download og image
        og_img_data = images_to_download.get('og_image', {})
        if og_img_data and og_img_data.get('url'):
            try:
                media_file, warning = download_and_optimize_image(
                    url=og_img_data['url'],
                    alt_text=og_img_data.get('alt', ''),
                    caption=og_img_data.get('caption', ''),
                    description=og_img_data.get('description', ''),
                    title=og_img_data.get('title', ''),
                    source_type=MediaFile.SourceType.EDITOR,
                    user=request.user,
                    skip_if_exists=True
                )
                if media_file:
                    downloaded_images['og_image'] = media_file
                if warning:
                    image_warnings.append(warning)
            except Exception as e:
                image_warnings.append(f"فشل تحميل صورة شبكات التواصل: {str(e)}")

        # Update image_paths in mapped_data
        if 'image_paths' not in mapped_data:
            mapped_data['image_paths'] = {}
        for img_type, media_file in downloaded_images.items():
            if media_file:
                mapped_data['image_paths'][img_type] = '/media/' + media_file.file.name

        # 2. Force Draft Status
        if 'form_initial' not in mapped_data:
            mapped_data['form_initial'] = {}
        mapped_data['form_initial']['publish_status'] = 'unpublished'

        # 3. Save imported content using bulk_saver
        try:
            from .services.bulk_saver import save_imported_content
            saved_obj, action_type = save_imported_content(content_type, mapped_data, request.user)
            name = getattr(saved_obj, 'name', getattr(saved_obj, 'title', ''))
            return JsonResponse({
                'success': True,
                'id': saved_obj.id,
                'name': name,
                'action': action_type,
                'image_warnings': image_warnings
            })
        except Exception as e:
            import traceback
            logger.error(f"Error in ImportSaveDraftView: {e}\n{traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

