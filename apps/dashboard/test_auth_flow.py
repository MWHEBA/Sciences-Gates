import pytest
from django.urls import reverse
from django.core import mail
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


@pytest.mark.django_db
def test_password_reset_page_accessible(client):
    """
    Test that the password reset request page is accessible (200 OK)
    and uses the correct template.
    """
    url = reverse('dashboard:password_reset')
    response = client.get(url)
    assert response.status_code == 200
    assert 'dashboard/auth/password_reset_form.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_password_reset_post_invalid_email(client):
    """
    Test that posting an unregistered email redirects to the done page,
    but does NOT send any email (security measure against user enumeration and spam).
    """
    url = reverse('dashboard:password_reset')
    response = client.post(url, {'email': 'nonexistent@example.com'})
    
    # Standard security practice redirects to done page anyway
    assert response.status_code == 302
    assert response.url == reverse('dashboard:password_reset_done')
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_post_non_staff_email(client, regular_user):
    """
    Test that posting a regular (non-staff) user's email redirects to the done page,
    but does NOT send any email (our custom form restriction).
    """
    assert regular_user.is_staff is False
    
    url = reverse('dashboard:password_reset')
    response = client.post(url, {'email': regular_user.email})
    
    # Should redirect but no email should be sent for non-staff users
    assert response.status_code == 302
    assert response.url == reverse('dashboard:password_reset_done')
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_post_staff_email(client, staff_user):
    """
    Test that posting a staff user's email redirects to the done page,
    and sends the styled password reset email.
    """
    assert staff_user.is_staff is True
    
    url = reverse('dashboard:password_reset')
    response = client.post(url, {'email': staff_user.email})
    
    assert response.status_code == 302
    assert response.url == reverse('dashboard:password_reset_done')
    
    # One email should be sent
    assert len(mail.outbox) == 1
    sent_mail = mail.outbox[0]
    
    assert sent_mail.to == [staff_user.email]
    assert "طلب استعادة كلمة المرور" in sent_mail.subject
    
    # Verify link components exist in both HTML and plain text parts
    uidb64 = urlsafe_base64_encode(force_bytes(staff_user.pk))
    token = default_token_generator.make_token(staff_user)
    
    confirm_url_part = f"/password-reset/confirm/{uidb64}/{token}/"
    assert confirm_url_part in sent_mail.body
    
    # Check that HTML alternative exists and has the link too
    assert len(sent_mail.alternatives) == 1
    html_content, content_type = sent_mail.alternatives[0]
    assert content_type == 'text/html'
    assert confirm_url_part in html_content
    # Check that branded color is used in HTML email
    assert "#C8A041" in html_content


@pytest.mark.django_db
def test_password_reset_confirm_invalid_token(client, staff_user):
    """
    Test that the confirm view displays an invalid link message
    when an incorrect token is provided.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(staff_user.pk))
    invalid_url = reverse('dashboard:password_reset_confirm', kwargs={
        'uidb64': uidb64,
        'token': 'invalid-token-value'
    })
    
    response = client.get(invalid_url)
    assert response.status_code == 200
    assert 'dashboard/auth/password_reset_confirm.html' in [t.name for t in response.templates]
    assert response.context['validlink'] is False


@pytest.mark.django_db
def test_password_reset_confirm_valid_token_and_reset(client, staff_user):
    """
    Test the full reset flow: generating a valid token, confirming it,
    posting a new password, and verifying it successfully updates in the database.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(staff_user.pk))
    token = default_token_generator.make_token(staff_user)
    
    confirm_url = reverse('dashboard:password_reset_confirm', kwargs={
        'uidb64': uidb64,
        'token': token
    })
    
    # 1. Access confirm page with valid link (Django redirects to set-password/ internally for security)
    response = client.get(confirm_url, follow=True)
    assert response.status_code == 200
    assert response.context['validlink'] is True
    
    # 2. Submit new password to the redirected URL
    redirected_url = response.request['PATH_INFO']
    new_password = 'NewSecurePassword123!'
    response = client.post(redirected_url, {
        'new_password1': new_password,
        'new_password2': new_password
    })
    
    # Should redirect to complete page
    assert response.status_code == 302
    assert response.url == reverse('dashboard:password_reset_complete')
    
    # 3. Check password updated successfully
    staff_user.refresh_from_db()
    assert staff_user.check_password(new_password) is True
