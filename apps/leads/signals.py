"""
Signal handlers for Lead model.
Sends email notifications to administrators when a new lead is submitted.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import Lead

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Lead)
def send_lead_notification_email(sender, instance, created, **kwargs):
    """
    Send email notification to administrators when a new lead is created.
    
    Args:
        sender: The model class (Lead)
        instance: The Lead instance that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    # Only send email for newly created leads
    if not created:
        return
    
    try:
        # Prepare email context
        context = {
            'lead': instance,
            'lead_type_display': instance.get_lead_type_display(),
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
        }
        
        # Build email subject in Arabic (sanitize to remove newlines)
        sanitized_name = instance.name.replace('\n', ' ').replace('\r', ' ')
        subject = f'رسالة جديدة من {sanitized_name} - {instance.get_lead_type_display()}'
        
        # Build plain text email body
        plain_text_body = f"""
بوابات العلوم للدراسة في ماليزيا

تم استقبال رسالة جديدة:

الاسم: {instance.name}
البريد الإلكتروني: {instance.email}
رقم الهاتف: {instance.phone}
نوع الرسالة: {instance.get_lead_type_display()}
صفحة المصدر: {instance.source_page or 'غير محدد'}
الرسالة:
{instance.message}

---
معلومات التتبع:
المرجع: {instance.referrer or 'غير محدد'}
UTM Source: {instance.utm_source or 'غير محدد'}
UTM Medium: {instance.utm_medium or 'غير محدد'}
UTM Campaign: {instance.utm_campaign or 'غير محدد'}
UTM Term: {instance.utm_term or 'غير محدد'}
UTM Content: {instance.utm_content or 'غير محدد'}
وقت الإرسال: {instance.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Get admin email(s)
        admin_email = settings.ADMIN_EMAIL
        if isinstance(admin_email, str):
            recipient_list = [admin_email]
        else:
            recipient_list = list(admin_email) if admin_email else []
        
        # If no admin email configured, log warning and return
        if not recipient_list:
            logger.warning(
                f'Lead notification email not sent: ADMIN_EMAIL not configured. '
                f'Lead ID: {instance.id}, Name: {instance.name}'
            )
            return
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        logger.info(
            f'Lead notification email sent successfully. '
            f'Lead ID: {instance.id}, Name: {instance.name}, '
            f'Recipients: {", ".join(recipient_list)}'
        )
        
    except Exception as e:
        # Log error but don't crash the application
        logger.error(
            f'Failed to send lead notification email. '
            f'Lead ID: {instance.id}, Name: {instance.name}, '
            f'Error: {str(e)}',
            exc_info=True
        )
