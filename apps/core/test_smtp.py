import pytest
from django.conf import settings
from apps.core.utils import SMTPCryptography
from apps.core.models import SiteSettings
from apps.core.email_backends import DynamicEmailBackend
from django.core.mail import EmailMessage

@pytest.mark.django_db
def test_smtp_cryptography():
    original_password = "mySecretGoogleWorkspacePassword123!"
    
    # Test Encryption
    encrypted = SMTPCryptography.encrypt(original_password)
    assert encrypted != original_password
    assert len(encrypted) > 0
    
    # Test Decryption
    decrypted = SMTPCryptography.decrypt(encrypted)
    assert decrypted == original_password


@pytest.mark.django_db
def test_dynamic_email_backend_fallbacks(settings):
    # Set default static setting
    settings.EMAIL_HOST = 'static.smtp.com'
    settings.EMAIL_PORT = 123
    
    # Instantiate backend with dynamic disabled
    site_settings = SiteSettings.get_settings()
    site_settings.email_smtp_use_dynamic = False
    site_settings.save()
    
    backend = DynamicEmailBackend()
    assert backend.host == 'static.smtp.com'
    assert backend.port == 123


@pytest.mark.django_db
def test_dynamic_email_backend_active(settings):
    settings.EMAIL_HOST = 'static.smtp.com'
    
    # Enable dynamic SMTP and save settings
    site_settings = SiteSettings.get_settings()
    site_settings.email_smtp_use_dynamic = True
    site_settings.email_smtp_host = 'dynamic.smtp.com'
    site_settings.email_smtp_port = 456
    site_settings.email_smtp_user = 'user@dynamic.com'
    site_settings.email_smtp_password = SMTPCryptography.encrypt('pass123')
    site_settings.email_from_address = 'from@dynamic.com'
    site_settings.save()
    
    backend = DynamicEmailBackend()
    assert backend.host == 'dynamic.smtp.com'
    assert backend.port == 456
    assert backend.username == 'user@dynamic.com'
    assert backend.password == 'pass123'
    
    # Test from_email rewrite
    msg = EmailMessage(
        subject='Test',
        body='Body',
        from_email='webmaster@localhost',
        to=['to@test.com']
    )
    
    from unittest.mock import patch
    with patch('django.core.mail.backends.smtp.EmailBackend.send_messages', return_value=1):
        backend.send_messages([msg])
    assert msg.from_email == 'شركة بوابات العلوم <from@dynamic.com>'
