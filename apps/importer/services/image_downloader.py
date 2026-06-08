import io
import os
import hashlib
import requests
from PIL import Image
from datetime import datetime
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from apps.core.models import MediaFile

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

def download_and_optimize_image(url, alt_text, caption='', description='', source_type=None, user=None):
    """
    Downloads an image from a URL, validates it, optimizes/converts it to WebP
    (if PNG or JPEG), creates a MediaFile instance, and saves it.
    
    يفحص أولاً إذا كانت الصورة موجودة مسبقاً باستخدام hash من الـ URL
    عشان نمنع تكرار الصور في إدارة الوسائط.
    
    Args:
        url: Image URL to download
        alt_text: Alt text for SEO (required)
        caption: Caption text visible to users (optional)
        description: Internal description for media library (optional)
        source_type: MediaFile.SourceType value
        user: Django User instance
    
    Returns:
        (media_file_instance, None) if successful.
        (None, warning_message) if it failed or was skipped.
    """
    if not url:
        return None, "رابط الصورة فارغ."

    try:
        # ============================================================
        # Step 1: Check if image already exists using URL hash
        # ============================================================
        # نحسب hash من الـ URL عشان نفحص إذا كانت الصورة موجودة مسبقاً
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        url_marker = f"[WP_URL_HASH:{url_hash}]"
        
        # نبحث في description field عن أي صورة محفوظة بنفس الـ URL
        existing_media = MediaFile.objects.filter(
            description__contains=url_marker
        ).first()
        
        if existing_media:
            # ============================================================
            # الصورة موجودة مسبقاً - نتأكد من تحديث البيانات الوصفية
            # ============================================================
            updated = False
            
            # Update alt_text if provided and different
            if alt_text and alt_text.strip() and alt_text.strip() != existing_media.alt_text:
                existing_media.alt_text = alt_text.strip()
                updated = True
            
            # Update caption if provided and different
            if caption and caption.strip() and caption.strip() != existing_media.caption:
                existing_media.caption = caption.strip()
                updated = True
            
            # Update title if not already set or if we want to update it
            # (title is auto-generated from filename, so we only update if explicitly provided)
            
            # Update description - but preserve the URL hash marker
            if description and description.strip():
                # Check if new description is different (excluding the hash marker)
                url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
                url_marker = f"[WP_URL_HASH:{url_hash}]"
                
                existing_desc_without_marker = existing_media.description.replace(url_marker, '').strip()
                new_desc = description.strip()
                
                if new_desc != existing_desc_without_marker:
                    # Preserve the hash marker in the updated description
                    if url_marker not in new_desc:
                        existing_media.description = f"{new_desc}\n{url_marker}".strip()
                    else:
                        existing_media.description = new_desc
                    updated = True
            
            # Save only if something changed
            if updated:
                existing_media.save()
            
            return existing_media, None
        
        # ============================================================
        # Step 2: Download image (only if not exists)
        # ============================================================
        # 1. Download image with a timeout
        resp = requests.get(url, timeout=15, stream=True)
        if not resp.ok:
            return None, f"فشل تحميل الصورة ({resp.status_code}): {url}"

        content_type = resp.headers.get('Content-Type', '')
        if 'image' not in content_type:
            return None, f"الرابط لا يشير إلى صورة صالحة (Content-Type: {content_type}): {url}"

        # 2. Stream content to check size limit
        content = b''
        for chunk in resp.iter_content(8192):
            content += chunk
            if len(content) > MAX_IMAGE_SIZE_BYTES:
                return None, f"الصورة تتجاوز الحد الأقصى للحجم (5MB): {url}"

        # 3. Open image with Pillow to validate and optimize
        try:
            img = Image.open(io.BytesIO(content))
            # Keep original format for verification
            img_format = img.format
            img.verify()
            
            # Re-open because verify() closes the stream or limits operations
            img = Image.open(io.BytesIO(content))
        except Exception as e:
            return None, f"الملف الذي تم تحميله ليس صورة صالحة أو أنه تالف: {url}"

        # 4. Optimize image (convert PNG/JPEG to WebP, resize if too large)
        max_width = 1200
        max_height = 1200
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        original_ext = os.path.splitext(url.split('?')[0])[1].lower()
        if not original_ext:
            original_ext = '.jpg'

        # Convert to WebP for JPEG/PNG
        is_convertible = img_format in ('JPEG', 'PNG')
        output_format = 'WEBP' if is_convertible else img_format
        output_ext = '.webp' if is_convertible else original_ext

        # Prepare output buffer
        output = io.BytesIO()
        
        # Mode conversion for non-transparency formats if saving to JPEG,
        # but for WebP we can retain alpha channels (mode RGBA) or convert.
        if output_format == 'WEBP':
            # Save as WebP
            img.save(output, format='WEBP', quality=80)
        else:
            # Fallback to saving in its original format
            img.save(output, format=img_format)

        output.seek(0)
        file_data = output.getvalue()
        file_size = len(file_data)

        # 5. Generate a clean, unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.basename(url.split('?')[0])
        clean_basename = "".join(c for c in os.path.splitext(base_name)[0] if c.isalnum() or c in ('-', '_'))
        if not clean_basename:
            clean_basename = "wp_imported"
        filename = f"{timestamp}_{clean_basename}{output_ext}"

        # 6. Map target MediaFile SourceType
        # Mapping wp plugin images format to MediaFile SourceType choices
        # choices are: university_logo, university_image, institute_image, major_image, editor
        source_mapping = {
            'logo': MediaFile.SourceType.UNIVERSITY_LOGO,
            'main_image': {
                'university': MediaFile.SourceType.UNIVERSITY_IMAGE,
                'institute': MediaFile.SourceType.INSTITUTE_IMAGE,
                'major': MediaFile.SourceType.MAJOR_IMAGE,
            },
            'og_image': MediaFile.SourceType.EDITOR,  # Fallback for og images to editor type
        }

        # Determine proper source type
        mapped_source_type = MediaFile.SourceType.EDITOR
        if source_type == 'logo':
            mapped_source_type = MediaFile.SourceType.UNIVERSITY_LOGO
        elif source_type == 'main_image':
            # Will be resolved in content_mapper depending on actual content type,
            # or passed directly as resolved type.
            mapped_source_type = MediaFile.SourceType.UNIVERSITY_IMAGE
        elif source_type in (MediaFile.SourceType.UNIVERSITY_IMAGE, MediaFile.SourceType.INSTITUTE_IMAGE, MediaFile.SourceType.MAJOR_IMAGE):
            mapped_source_type = source_type

        # 7. Create and save MediaFile
        # ============================================================
        # نضيف URL hash marker في الـ description عشان نقدر نفحص بيه في المستقبل
        # ============================================================
        final_description = description or ''
        if url_marker not in final_description:
            final_description = f"{final_description}\n{url_marker}".strip()
        
        media_file = MediaFile(
            original_filename=base_name,
            file_size=file_size,
            width=img.width,
            height=img.height,
            alt_text=alt_text or '',
            caption=caption or '',
            title=clean_basename,
            description=final_description,
            source_type=mapped_source_type,
            uploaded_by=user if user and user.is_authenticated else None
        )
        
        # Django's FileField save() saves the file and saves the model
        media_file.file.save(filename, ContentFile(file_data), save=True)

        return media_file, None

    except Exception as e:
        return None, f"خطأ غير متوقع أثناء تحميل الصورة {url}: {str(e)}"
