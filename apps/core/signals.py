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
    if not created and not kwargs.get('update_fields'):
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
