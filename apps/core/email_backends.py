import json
import logging
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
from apps.core.utils import SMTPCryptography

logger = logging.getLogger(__name__)


class DynamicEmailBackend(EmailBackend):
    """
    Custom SMTP Email Backend that dynamically loads settings from a cached JSON file or the database.
    This avoids database queries on every email dispatch, and supports encrypted passwords.
    """
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, use_ssl=None, timeout=None, ssl_keyfile=None,
                 ssl_certfile=None, **kwargs):
        
        smtp_config = None
        
        # 1. Try to read from cache file to avoid DB queries
        cache_file = settings.BASE_DIR / 'cache' / 'smtp_config.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    smtp_config = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read SMTP config from cache file: {e}")

        # 2. Try to read from database if cache file is missing or invalid
        if not smtp_config:
            try:
                from apps.core.models import SiteSettings
                site_settings = SiteSettings.get_settings()
                # Regenerate config cache file
                site_settings.update_smtp_cache()
                smtp_config = {
                    'email_smtp_use_dynamic': site_settings.email_smtp_use_dynamic,
                    'email_smtp_host': site_settings.email_smtp_host,
                    'email_smtp_port': site_settings.email_smtp_port,
                    'email_smtp_user': site_settings.email_smtp_user,
                    'email_smtp_password': site_settings.email_smtp_password,
                    'email_smtp_use_tls': site_settings.email_smtp_use_tls,
                    'email_smtp_use_ssl': site_settings.email_smtp_use_ssl,
                    'email_from_address': site_settings.email_from_address,
                }
            except Exception as e:
                logger.warning(f"Failed to read SMTP config from database: {e}")

        # 3. Apply configurations if dynamic is enabled
        if smtp_config and smtp_config.get('email_smtp_use_dynamic'):
            try:
                # Decrypt password
                encrypted_password = smtp_config.get('email_smtp_password', '')
                decrypted_password = SMTPCryptography.decrypt(encrypted_password)
                
                host = host or smtp_config.get('email_smtp_host') or settings.EMAIL_HOST
                port = port or smtp_config.get('email_smtp_port') or settings.EMAIL_PORT
                username = username or smtp_config.get('email_smtp_user') or settings.EMAIL_HOST_USER
                password = password or decrypted_password or settings.EMAIL_HOST_PASSWORD
                
                # Check for TLS
                use_tls_val = smtp_config.get('email_smtp_use_tls')
                if use_tls_val is not None:
                    use_tls = use_tls if use_tls is not None else use_tls_val
                else:
                    use_tls = use_tls if use_tls is not None else settings.EMAIL_USE_TLS
                
                # Check for SSL
                use_ssl_val = smtp_config.get('email_smtp_use_ssl')
                if use_ssl_val is not None:
                    use_ssl = use_ssl if use_ssl is not None else use_ssl_val
                else:
                    use_ssl = use_ssl if use_ssl is not None else getattr(settings, 'EMAIL_USE_SSL', False)
                    
            except Exception as e:
                logger.error(f"Error applying dynamic SMTP configuration: {e}")

        # Initialize base SMTP backend
        super().__init__(
            host=host, port=port, username=username, password=password,
            use_tls=use_tls, use_ssl=use_ssl, timeout=timeout,
            ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile, **kwargs
        )

    def send_messages(self, email_messages):
        """Override to dynamically rewrite the from_email address if configured."""
        try:
            from_email_addr = None
            
            # Read from cache file
            cache_file = settings.BASE_DIR / 'cache' / 'smtp_config.json'
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        smtp_config = json.load(f)
                        if smtp_config.get('email_smtp_use_dynamic'):
                            from_email_addr = smtp_config.get('email_from_address')
                except Exception:
                    pass
            
            # Fallback to database
            if not from_email_addr:
                try:
                    from apps.core.models import SiteSettings
                    site_settings = SiteSettings.get_settings()
                    if site_settings.email_smtp_use_dynamic:
                        from_email_addr = site_settings.email_from_address
                except Exception:
                    pass

            # Apply the from_email if configured
            if from_email_addr:
                formatted_from = from_email_addr
                if '<' not in from_email_addr:
                    formatted_from = f"شركة بوابات العلوم <{from_email_addr}>"
                
                for message in email_messages:
                    if not message.from_email or message.from_email == settings.DEFAULT_FROM_EMAIL or message.from_email == 'webmaster@localhost':
                        message.from_email = formatted_from
                    elif '<' not in message.from_email:
                        message.from_email = f"شركة بوابات العلوم <{message.from_email}>"
        except Exception as e:
            logger.warning(f"Error modifying message from_email: {e}")

        return super().send_messages(email_messages)
