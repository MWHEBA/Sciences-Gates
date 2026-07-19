import logging
import threading
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.models import User

from .models import Lead

logger = logging.getLogger(__name__)


def _send_email_async(email_msg, lead_id, lead_name, recipients):
    """Helper function to send email in a background thread."""
    try:
        email_msg.send(fail_silently=False)
        logger.info(
            f'Lead notification email sent successfully in background. '
            f'Lead ID: {lead_id}, Name: {lead_name}, '
            f'Recipients: {", ".join(recipients)}'
        )
    except Exception as e:
        logger.error(
            f'Failed to send lead notification email in background thread. '
            f'Lead ID: {lead_id}, Name: {lead_name}, '
            f'Error: {str(e)}',
            exc_info=True
        )


@receiver(post_save, sender=Lead)
def send_lead_notification_email(sender, instance, created, **kwargs):
    """
    Send HTML email notification to administrators when a new lead is created.
    Filters recipients based on user preferences in UserProfile.
    """
    # Only send email for newly created leads
    if not created:
        return
    
    try:
        # 1. Filter recipients based on lead type and admin preferences
        recipients = []
        if instance.lead_type == 'registration':
            # Staff users who enabled registration emails
            staff_users = User.objects.filter(
                is_staff=True,
                is_active=True,
                profile__receive_registration_emails=True
            ).select_related('profile')
        else:
            # Staff users who enabled inquiry emails
            staff_users = User.objects.filter(
                is_staff=True,
                is_active=True,
                profile__receive_inquiry_emails=True
            ).select_related('profile')
            
        recipient_list = [user.email for user in staff_users if user.email]
        
        # Fallback to settings.ADMIN_EMAIL if no staff emails are configured/enabled
        if not recipient_list:
            admin_email = settings.ADMIN_EMAIL
            if isinstance(admin_email, str):
                recipient_list = [admin_email]
            else:
                recipient_list = list(admin_email) if admin_email else []
                
        # If still no recipient, log warning and return
        if not recipient_list:
            logger.warning(
                f'Lead notification email not sent: No recipients found (staff users or ADMIN_EMAIL). '
                f'Lead ID: {instance.id}, Name: {instance.name}'
            )
            return
            
        # 2. Prepare email context
        context = {
            'lead': instance,
            'lead_type_display': instance.get_lead_type_display(),
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
            'current_year': datetime.datetime.now().year,
        }
        
        # 3. Build email subject in Arabic
        sanitized_name = instance.name.replace('\n', ' ').replace('\r', ' ')
        subject = f'رسالة جديدة من {sanitized_name} - {instance.get_lead_type_display()}'
        
        # 4. Render HTML and Plain Text templates
        html_body = render_to_string('leads/emails/lead_notification_admin.html', context)
        plain_text_body = render_to_string('leads/emails/lead_notification_admin.txt', context)
        
        # 5. Build Email Message with reply_to
        reply_to_list = [instance.email] if instance.email else None
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
            reply_to=reply_to_list
        )
        email.attach_alternative(html_body, "text/html")
        
        # 6. Dispatch email: synchronously if testing, in background thread otherwise
        is_testing = getattr(settings, 'TESTING', False) or settings.EMAIL_BACKEND == 'django.core.mail.backends.locmem.EmailBackend'
        if is_testing:
            email.send(fail_silently=False)
            logger.info(
                f'Lead notification email sent synchronously for testing. '
                f'Lead ID: {instance.id}, Name: {instance.name}'
            )
        else:
            thread = threading.Thread(
                target=_send_email_async,
                args=(email, instance.id, instance.name, recipient_list)
            )
            thread.daemon = True
            thread.start()
        
    except Exception as e:
        logger.error(
            f'Failed to initialize lead notification email sending. '
            f'Lead ID: {instance.id}, Name: {instance.name}, '
            f'Error: {str(e)}',
            exc_info=True
        )

