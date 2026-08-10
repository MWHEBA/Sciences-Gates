"""
Signal handlers for core app.
Handles automatic image optimization and WebP generation on upload.
"""
import os
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from .utils import process_image_with_webp

logger = logging.getLogger(__name__)


def generate_webp_for_image_field(sender, instance, created, field_name, **kwargs):
    """
    Generic signal handler to generate WebP versions for image fields.
    
    This handler is called after an image is uploaded and saved.
    It generates a WebP version of the image for modern browsers.
    
    Args:
        sender: Model class
        instance: Model instance
        created: Boolean indicating if this is a new instance
        field_name: Name of the ImageField to process
        **kwargs: Additional signal arguments
    """
    # Only process on creation or update
    if not created and kwargs.get('update_fields') is not None and field_name not in kwargs.get('update_fields'):
        return
    
    try:
        # Get the image field
        image_field = getattr(instance, field_name, None)
        if not image_field or not image_field.name:
            return
        
        # Get the full file path
        image_path = image_field.path
        
        # Check if WebP version already exists
        webp_path = os.path.splitext(image_path)[0] + '.webp'
        if os.path.exists(webp_path):
            return
        
        # Generate WebP version
        with open(image_path, 'rb') as f:
            from django.core.files.uploadedfile import InMemoryUploadedFile
            
            # Create an in-memory file object
            uploaded_file = InMemoryUploadedFile(
                f,
                field_name,
                image_field.name,
                'image/jpeg',
                os.path.getsize(image_path),
                None
            )
            
            # Process image and generate WebP
            result = process_image_with_webp(uploaded_file)
            
            if result['webp']:
                # Save WebP version
                with open(webp_path, 'wb') as webp_file:
                    webp_file.write(result['webp'].read())
                
                logger.info(f'Generated WebP version: {webp_path}')
    
    except Exception as e:
        logger.error(f'Error generating WebP for {field_name}: {str(e)}')


def create_webp_signal_handler(model_class, field_name):
    """
    Factory function to create a signal handler for a specific model and field.
    
    Usage:
        from django.apps import AppConfig
        from .signals import create_webp_signal_handler
        
        class UniversitiesConfig(AppConfig):
            default_auto_field = 'django.db.models.BigAutoField'
            name = 'apps.universities'
            
            def ready(self):
                from .models import University
                from django.db.models.signals import post_save
                
                handler = create_webp_signal_handler(University, 'main_image')
                post_save.connect(handler, sender=University)
    
    Args:
        model_class: Django model class
        field_name: Name of the ImageField
        
    Returns:
        function: Signal handler function
    """
    def handler(sender, instance, created, **kwargs):
        generate_webp_for_image_field(sender, instance, created, field_name, **kwargs)
    
    return handler


def sync_media_file(instance, field_name, alt_field_name, source_type):
    """Sync model image field to MediaFile model."""
    from apps.core.models import MediaFile
    from django.contrib.contenttypes.models import ContentType
    
    image_file = getattr(instance, field_name, None)
    if not image_file or not image_file.name:
        # If the image was cleared/deleted, delete the corresponding MediaFile
        MediaFile.objects.filter(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.pk,
            source_type=source_type
        ).delete()
        return

    alt_text = getattr(instance, alt_field_name, '')
    
    # Check if a MediaFile already exists
    media_file = MediaFile.objects.filter(
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.pk,
        source_type=source_type
    ).first()

    if not media_file:
        # التحقق مما إذا كان المستورد قد أنشأ كائناً بالفعل لنفس الملف على القرص
        media_file = MediaFile.objects.filter(file=image_file.name).first()

    try:
        width = image_file.width
        height = image_file.height
        file_size = image_file.size
    except Exception:
        width, height, file_size = None, None, 0

    if media_file:
        # Check if the image file has changed (i.e. replaced with a new file)
        image_changed = media_file.file.name != image_file.name
        
        if image_changed:
            # If the image was replaced, clear the alt text
            alt_text = ''
            # Update the instance field in the DB directly without triggering signals
            type(instance).objects.filter(pk=instance.pk).update(**{alt_field_name: ''})
        else:
            # If the image did NOT change, but the incoming alt_text is empty and media_file has one,
            # it means the model was saved without the alt text in the form, so preserve it.
            if not alt_text and media_file.alt_text:
                alt_text = media_file.alt_text
                # Sync it back to the instance DB field
                type(instance).objects.filter(pk=instance.pk).update(**{alt_field_name: alt_text})

        media_file.alt_text = alt_text
        media_file.width = width
        media_file.height = height
        media_file.file_size = file_size
        media_file.content_type = ContentType.objects.get_for_model(instance)
        media_file.object_id = instance.pk
        media_file.source_type = source_type
        if image_changed:
            media_file.file = image_file
            media_file.original_filename = os.path.basename(image_file.name)
        media_file.save()
    else:
        MediaFile.objects.create(
            file=image_file,
            original_filename=os.path.basename(image_file.name),
            file_size=file_size,
            width=width,
            height=height,
            alt_text=alt_text,
            source_type=source_type,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.pk
        )


def delete_entity_media_files(sender, instance, **kwargs):
    """Delete corresponding MediaFile entries, physical files, and related attachments when model instance is deleted."""
    from apps.core.models import MediaFile
    from django.contrib.contenttypes.models import ContentType
    import os
    
    # 1. Clean up related attachments (if any) to delete their physical files
    if hasattr(instance, 'attachments'):
        try:
            for attachment in instance.attachments.all():
                if attachment.file:
                    try:
                        if os.path.exists(attachment.file.path):
                            os.remove(attachment.file.path)
                    except Exception as e:
                        logger.warning(f"Error deleting physical file for attachment {attachment.pk}: {e}")
        except Exception as e:
            logger.warning(f"Error accessing attachments for {instance}: {e}")

    # 2. Clean up associated MediaFiles (including logos, main images, and editor uploads) and their physical files
    try:
        content_type = ContentType.objects.get_for_model(instance)
        media_files = MediaFile.objects.filter(
            content_type=content_type,
            object_id=instance.pk
        )
        for media in media_files:
            try:
                if media.file:
                    # Delete main file on disk
                    if os.path.exists(media.file.path):
                        os.remove(media.file.path)
                    # Delete WebP version of the image if it exists
                    webp_path = os.path.splitext(media.file.path)[0] + '.webp'
                    if os.path.exists(webp_path):
                        os.remove(webp_path)
            except Exception as e:
                logger.warning(f"Error deleting physical file for MediaFile {media.pk}: {e}")
        media_files.delete()
    except Exception as e:
        logger.warning(f"Error cleaning up MediaFiles for {instance}: {e}")


def sync_university_media(sender, instance, **kwargs):
    from apps.core.models import MediaFile
    sync_media_file(instance, 'logo', 'logo_alt', MediaFile.SourceType.UNIVERSITY_LOGO)
    sync_media_file(instance, 'main_image', 'main_image_alt', MediaFile.SourceType.UNIVERSITY_IMAGE)


def sync_institute_media(sender, instance, **kwargs):
    from apps.core.models import MediaFile
    sync_media_file(instance, 'logo', 'logo_alt', MediaFile.SourceType.INSTITUTE_LOGO)
    sync_media_file(instance, 'main_image', 'main_image_alt', MediaFile.SourceType.INSTITUTE_IMAGE)


def sync_major_media(sender, instance, **kwargs):
    from apps.core.models import MediaFile
    sync_media_file(instance, 'main_image', 'main_image_alt', MediaFile.SourceType.MAJOR_IMAGE)


def sync_article_media(sender, instance, **kwargs):
    from apps.core.models import MediaFile
    sync_media_file(instance, 'featured_image', 'featured_image_alt', MediaFile.SourceType.ARTICLE_IMAGE)


def invalidate_mega_menu_cache(sender, instance, **kwargs):
    """Clear the mega menu cache when universities or institutes change."""
    from django.core.cache import cache
    try:
        cache.delete('mega_menu_data')
        logger.info('Mega menu cache invalidated due to save/delete of university/institute.')
    except OSError as e:
        # Gracefully handle Windows file locks (PermissionError/WinError 32) during test runs
        logger.warning(f'Could not delete mega menu cache file due to OS lock: {e}')
    except Exception as e:
        logger.error(f'Error invalidating mega menu cache: {e}')

def invalidate_sitemap_cache_signal(sender, instance, **kwargs):
    """Clear the sitemap cache when content models change."""
    from apps.seo.sitemaps import clear_sitemap_cache
    try:
        clear_sitemap_cache()
        logger.info('Sitemap cache invalidated due to save/delete of content entity.')
    except Exception as e:
        logger.error(f'Error invalidating sitemap cache: {e}')


def connect_media_signals():
    """Connect all media synchronization signals and cache invalidations."""
    from django.db.models.signals import post_save, post_delete, pre_delete
    from apps.universities.models import University
    from apps.institutes.models import Institute
    from apps.majors.models import Major
    from apps.majors.models import MajorCategory
    from apps.articles.models import Article

    post_save.connect(sync_university_media, sender=University)
    pre_delete.connect(delete_entity_media_files, sender=University)

    post_save.connect(sync_institute_media, sender=Institute)
    pre_delete.connect(delete_entity_media_files, sender=Institute)

    post_save.connect(sync_major_media, sender=Major)
    pre_delete.connect(delete_entity_media_files, sender=Major)

    post_save.connect(sync_article_media, sender=Article)
    pre_delete.connect(delete_entity_media_files, sender=Article)

    # Invalidate Mega Menu Cache
    post_save.connect(invalidate_mega_menu_cache, sender=University)
    post_delete.connect(invalidate_mega_menu_cache, sender=University)
    post_save.connect(invalidate_mega_menu_cache, sender=Institute)
    post_delete.connect(invalidate_mega_menu_cache, sender=Institute)
    post_save.connect(invalidate_mega_menu_cache, sender=MajorCategory)
    post_delete.connect(invalidate_mega_menu_cache, sender=MajorCategory)
    post_save.connect(invalidate_mega_menu_cache, sender=Major)
    post_delete.connect(invalidate_mega_menu_cache, sender=Major)

    # Invalidate Sitemap Cache
    for model_cls in [University, Institute, Major, MajorCategory, Article]:
        post_save.connect(invalidate_sitemap_cache_signal, sender=model_cls)
        post_delete.connect(invalidate_sitemap_cache_signal, sender=model_cls)


# Connect signals automatically on import
connect_media_signals()
