from django.db.models.signals import pre_save
from django.dispatch import receiver
import logging

from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article
from apps.redirects.models import Redirect

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=University)
@receiver(pre_save, sender=Institute)
@receiver(pre_save, sender=Major)
@receiver(pre_save, sender=Article)
def pre_save_content_redirect(sender, instance, **kwargs):
    """
    Automates 301 redirect generation when a published item's slug is changed.
    Triggers for University, Institute, Major, and Article models.
    """
    if not instance.pk:
        return
        
    try:
        # Get the original instance from the database
        old_instance = sender.objects.filter(pk=instance.pk).first()
        if not old_instance:
            return
            
        # Only track if the item is published
        # Article uses publish_status, others use publish_status too (from PublishableModel)
        is_published = getattr(old_instance, 'publish_status', '') == 'published'
        
        # Check if the slug has changed
        if old_instance.slug != instance.slug and is_published:
            # Determine path prefix
            prefix = ''
            if sender == University:
                prefix = '/universities/'
            elif sender == Institute:
                prefix = '/institutes/'
            elif sender == Major:
                prefix = '/majors/'
            elif sender == Article:
                prefix = '/articles/'
                
            if not prefix:
                return
                
            old_url = Redirect.normalize_path(f'{prefix}{old_instance.slug}/')
            new_url = Redirect.normalize_path(f'{prefix}{instance.slug}/')
            
            if old_url == new_url:
                return
                
            # Loop protection: If a redirect from new_url to old_url exists, delete it
            Redirect.objects.filter(old_url=new_url, new_url=old_url).delete()
            
            # Chain protection: Update existing redirects pointing to the old URL to point to the new URL
            Redirect.objects.filter(new_url=old_url).update(new_url=new_url)
            
            # Create or update the redirect record
            # We use update_or_create to make it idempotent
            redirect_obj, created = Redirect.objects.update_or_create(
                old_url=old_url,
                defaults={
                    'new_url': new_url,
                    'is_active': True,
                    'notes': f"توجيه تلقائي لتغير رابط {instance._meta.verbose_name}: {getattr(instance, 'name', '') or getattr(instance, 'title', '')}"
                }
            )
            
            if created:
                logger.info("Auto-created 301 redirect: %s -> %s", old_url, new_url)
            else:
                logger.info("Updated existing 301 redirect: %s -> %s", old_url, new_url)
                
    except Exception as exc:
        # Prevent database save from crashing if anything goes wrong during redirect generation
        logger.error("Error generating automatic redirect: %s", exc)
