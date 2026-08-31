import logging
import threading
import datetime
import urllib.parse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.models import User

from .models import Lead
from apps.core.models import SiteSettings

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Lead)
def send_lead_notification_email(sender, instance, created, **kwargs):
    """
    Send HTML email notification to administrators and a confirmation email to applicant when a new lead is created.
    Filters recipients based on user preferences in UserProfile for admin notifications.
    """
    # Only send email for newly created leads
    if not created:
        return
    
    # ----------------------------------------------------
    # 1. Admin Email Notification
    # ----------------------------------------------------
    admin_email_msg = None
    recipient_list = []
    try:
        # Filter recipients based on lead type and admin preferences
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
                
        if recipient_list:
            # Prepare email context
            context = {
                'lead': instance,
                'lead_type_display': instance.get_lead_type_display(),
                'site_name': settings.SITE_NAME,
                'site_url': settings.SITE_URL,
                'current_year': datetime.datetime.now().year,
            }
            
            # Build email subject in Arabic
            raw_name = str(instance.name or '')
            sanitized_name = raw_name.replace('\n', ' ').replace('\r', ' ')
            subject = f'رسالة جديدة من {sanitized_name} - {instance.get_lead_type_display()}'
            
            # Render HTML and Plain Text templates
            html_body = render_to_string('leads/emails/lead_notification_admin.html', context)
            plain_text_body = render_to_string('leads/emails/lead_notification_admin.txt', context)
            
            # Build Email Message with reply_to
            reply_to_list = [instance.email.strip()] if (instance.email and instance.email.strip()) else None
            admin_email_msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
                reply_to=reply_to_list
            )
            admin_email_msg.attach_alternative(html_body, "text/html")
        else:
            logger.warning(
                f'Lead notification email not sent: No recipients found (staff users or ADMIN_EMAIL). '
                f'Lead ID: {instance.id}, Name: {instance.name}'
            )
    except Exception as e:
        logger.error(
            f'Failed to initialize lead admin notification email. '
            f'Lead ID: {instance.id}, Name: {instance.name}, '
            f'Error: {str(e)}',
            exc_info=True
        )

    # ----------------------------------------------------
    # 2. Applicant Confirmation Email (to instance.email)
    # ----------------------------------------------------
    user_email_msg = None
    user_recipient = None
    if instance.email and instance.email.strip():
        try:
            site_settings = SiteSettings.get_settings()
            whatsapp_clean = site_settings.whatsapp_primary_clean or '60182638888'

            lead_type_str = 'طلب تسجيل' if instance.lead_type == 'registration' else 'استفسار'
            if instance.institution_name and instance.name:
                whatsapp_prefilled_text = f"مرحباً شركة بوابات العلوم، قمت بالتقديم عبر الموقع لـ ({lead_type_str} في {instance.institution_name}) باسم: {instance.name}، وأود المتابعة معكم."
            elif instance.institution_name:
                whatsapp_prefilled_text = f"مرحباً شركة بوابات العلوم، قمت بالتقديم عبر الموقع لـ ({lead_type_str} في {instance.institution_name})، وأود المتابعة معكم."
            elif instance.name:
                whatsapp_prefilled_text = f"مرحباً شركة بوابات العلوم، قمت بالتقديم عبر الموقع لـ ({lead_type_str}) باسم: {instance.name}، وأود المتابعة معكم."
            else:
                whatsapp_prefilled_text = f"مرحباً شركة بوابات العلوم، قمت بالتقديم عبر الموقع لـ ({lead_type_str}) وأود المتابعة معكم لسرعة الإجراءات."
            whatsapp_prefilled_encoded = urllib.parse.quote(whatsapp_prefilled_text)

            user_context = {
                'lead': instance,
                'lead_type_display': instance.get_lead_type_display(),
                'site_name': settings.SITE_NAME,
                'site_url': settings.SITE_URL,
                'current_year': datetime.datetime.now().year,
                'whatsapp_clean': whatsapp_clean,
                'whatsapp_prefilled_encoded': whatsapp_prefilled_encoded,
            }

            if instance.lead_type == 'registration':
                user_subject = f"تم استلام طلب التسجيل بنجاح - {settings.SITE_NAME}"
            else:
                user_subject = f"تم استلام استفسارك بنجاح - {settings.SITE_NAME}"

            user_html_body = render_to_string('leads/emails/lead_confirmation_user.html', user_context)
            user_plain_text_body = render_to_string('leads/emails/lead_confirmation_user.txt', user_context)

            user_recipient = instance.email.strip()
            user_email_msg = EmailMultiAlternatives(
                subject=user_subject,
                body=user_plain_text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_recipient]
            )
            user_email_msg.attach_alternative(user_html_body, "text/html")
        except Exception as e:
            logger.error(
                f'Failed to initialize lead applicant confirmation email. '
                f'Lead ID: {instance.id}, Email: {instance.email}, '
                f'Error: {str(e)}',
                exc_info=True
            )

    # ----------------------------------------------------
    # 3. Dispatch Emails Asynchronously in Background Thread
    # ----------------------------------------------------
    def _send_emails_async():
        if admin_email_msg:
            try:
                admin_email_msg.send(fail_silently=False)
                logger.info(
                    f'Lead admin notification email sent successfully. '
                    f'Lead ID: {instance.id}, Name: {instance.name}'
                )
            except Exception as e:
                logger.error(
                    f'Failed to send lead admin notification email. '
                    f'Lead ID: {instance.id}, Name: {instance.name}, '
                    f'Error: {str(e)}',
                    exc_info=True
                )

        if user_email_msg:
            try:
                user_email_msg.send(fail_silently=False)
                logger.info(
                    f'Lead user confirmation email sent successfully. '
                    f'Lead ID: {instance.id}, Recipient: {user_recipient}'
                )
            except Exception as e:
                logger.error(
                    f'Failed to send lead applicant confirmation email. '
                    f'Lead ID: {instance.id}, Recipient: {user_recipient}, '
                    f'Error: {str(e)}',
                    exc_info=True
                )

    # In testing mode (e.g. pytest / unittest checking mail.outbox), send synchronously
    import sys
    is_testing = getattr(settings, 'TESTING', False) or 'test' in sys.argv or 'pytest' in sys.modules
    if is_testing:
        _send_emails_async()
    else:
        email_thread = threading.Thread(target=_send_emails_async, daemon=True)
        email_thread.start()





