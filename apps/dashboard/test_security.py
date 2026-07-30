import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

User = get_user_model()

@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()

@pytest.mark.django_db
class TestDashboardSecurity:
    """Automated security verification tests."""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        # Staff user
        self.staff_user = User.objects.create_user(
            username='staff_user',
            email='staff@example.com',
            password='Password123',
            is_staff=True
        )
        # Profile is required by DashboardMixin
        from apps.core.models import UserProfile
        UserProfile.objects.get_or_create(user=self.staff_user, defaults={'full_name': 'Staff Member'})

        # Non-staff user
        self.non_staff_user = User.objects.create_user(
            username='regular_user',
            email='regular@example.com',
            password='Password123',
            is_staff=False
        )
        UserProfile.objects.get_or_create(user=self.non_staff_user, defaults={'full_name': 'Regular Member'})

    def test_dashboard_home_access_control(self):
        """Verify non-staff user cannot access dashboard home."""
        # 1. Anonymous user redirected
        response = self.client.get(reverse('dashboard:home'))
        assert response.status_code == 302
        assert 'login' in response.url

        # 2. Non-staff user logged in -> redirected with error
        self.client.login(username='regular_user', password='Password123')
        response = self.client.get(reverse('dashboard:home'))
        assert response.status_code == 302
        assert 'login' in response.url

        # 3. Staff user logged in -> success
        self.client.login(username='staff_user', password='Password123')
        response = self.client.get(reverse('dashboard:home'))
        assert response.status_code == 200

    def test_editor_image_upload_access_control(self):
        """Verify non-staff user cannot upload images."""
        url = reverse('dashboard:editor_upload_image')
        # 1. Anonymous user redirected
        response = self.client.post(url)
        assert response.status_code == 302

        # 2. Non-staff user redirected
        self.client.login(username='regular_user', password='Password123')
        response = self.client.post(url)
        assert response.status_code == 302

    def test_login_brute_force_lockout(self):
        """Verify IP lockout after 5 consecutive failed login attempts."""
        url = reverse('dashboard:login')
        
        # 4 failed attempts should not lock out yet
        for i in range(4):
            response = self.client.post(url, {'username': 'staff_user', 'password': 'WrongPassword'})
            assert response.status_code == 200
            assert 'اسم المستخدم أو كلمة المرور غير صحيحة' in response.content.decode('utf-8')

        # 5th failed attempt triggers lockout
        response = self.client.post(url, {'username': 'staff_user', 'password': 'WrongPassword'})
        assert response.status_code == 200
        assert 'تم قفل محاولات تسجيل الدخول مؤقتاً' in response.content.decode('utf-8')

        # 6th attempt (even correct password) is blocked immediately due to active lockout
        response = self.client.post(url, {'username': 'staff_user', 'password': 'Password123'})
        assert response.status_code == 200
        assert 'تم قفل محاولات تسجيل الدخول مؤقتاً' in response.content.decode('utf-8')

    @override_settings(TESTING=False)
    def test_rate_limiting_lead_submission(self):
        """Verify rate limiting on lead submission (3 submissions per hour)."""
        url = reverse('leads:submit')
        
        # Mock sys.argv to bypass Turnstile during form submissions
        with patch('sys.argv', ['pytest']):
            # 3 submissions should be registered
            for _ in range(3):
                response = self.client.post(url, {
                    'name': 'Spam Bot',
                    'email': 'spam@bot.com',
                    'phone_number': '123456789',
                    'country_code': '+966',
                    'phone': '+966123456789',
                    'nationality': 'مصري',
                })
                assert 'تم تجاوز الحد الأقصى' not in response.content.decode('utf-8')

            # 4th submission is rate limited
            response = self.client.post(url, {
                'name': 'Spam Bot',
                'email': 'spam@bot.com',
                'phone_number': '123456789',
                'country_code': '+966',
                'phone': '+966123456789',
                'nationality': 'مصري',
            })
            assert response.status_code == 200
            assert 'تم تجاوز الحد الأقصى' in response.content.decode('utf-8')

    def test_image_exif_stripping(self):
        """Verify that uploaded images have their EXIF metadata stripped."""
        img_io = BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        
        exif_data = image.getexif()
        exif_data[271] = "Test Camera Maker"
        exif_data[272] = "Test Camera Model"
        
        image.save(img_io, format='JPEG', exif=exif_data)
        img_file = SimpleUploadedFile("exif_test.jpg", img_io.getvalue(), content_type="image/jpeg")

        self.client.login(username='staff_user', password='Password123')
        url = reverse('dashboard:editor_upload_image')
        
        with patch('django.core.files.storage.default_storage.save') as mock_storage_save:
            mock_storage_save.return_value = 'exif_test.jpg'
            # Mock the MediaFile creation since database fields are checked
            with patch('apps.core.models.MediaFile.objects.create') as mock_db_create:
                response = self.client.post(url, {'image': img_file})
                assert response.status_code == 200
                
                args, kwargs = mock_storage_save.call_args
                saved_content = args[1].read()
                
                saved_image = Image.open(BytesIO(saved_content))
                exif_after = saved_image.getexif()
                assert len(exif_after) == 0

    def test_turnstile_backend_validation(self):
        """Verify Turnstile verification blocks invalid submissions."""
        from django.conf import settings
        from django.test import override_settings
        from apps.leads.forms import ContactLeadForm
        
        with override_settings(TESTING=False):
            with patch.object(settings, 'TURNSTILE_SECRET_KEY', 'dummy-secret-key'):
                with patch('sys.argv', ['manage.py', 'runserver']):
                    # 1. Post without turnstile token
                    form_data = {
                        'lead_type': 'contact',
                        'name': 'Test User',
                        'email': 'student@example.com',
                        'phone_number': '123456789',
                        'country_code': '+966',
                        'phone': '+966123456789',
                        'nationality': 'مصري',
                    }
                    form = ContactLeadForm(data=form_data)
                    assert not form.is_valid()
                    assert 'يرجى التحقق من اختبار الأمان (Turnstile).' in form.errors['__all__'][0]

                    # 2. Mock Cloudflare verification returning failure
                    with patch('requests.post') as mock_post:
                        mock_resp = MagicMock()
                        mock_resp.json.return_value = {'success': False}
                        mock_post.return_value = mock_resp
                        
                        form_data['cf-turnstile-response'] = 'invalid-token'
                        form = ContactLeadForm(data=form_data)
                        assert not form.is_valid()
                        assert 'فشل التحقق من اختبار الأمان (Turnstile).' in form.errors['__all__'][0]

                    # 3. Mock Cloudflare verification returning success
                    with patch('requests.post') as mock_post:
                        mock_resp = MagicMock()
                        mock_resp.json.return_value = {'success': True}
                        mock_post.return_value = mock_resp
                        
                        form_data['cf-turnstile-response'] = 'valid-token'
                        form = ContactLeadForm(data=form_data)
                        assert form.is_valid()

    def test_super_admin_self_deletion_prevention(self):
        """Verify that a Super Admin cannot delete their own account."""
        from apps.core.models import UserRole
        
        # 1. Create a Super Admin user
        super_admin = User.objects.create_user(
            username='super_admin_user',
            email='superadmin@example.com',
            password='Password123',
            is_staff=True
        )
        profile = super_admin.profile
        profile.role = UserRole.SUPER_ADMIN
        profile.save()
        
        # Log in as the Super Admin
        self.client.login(username='super_admin_user', password='Password123')
        
        # 2. Try to get the delete confirmation (GET) -> should redirect (cannot delete self)
        url = reverse('dashboard:user_delete', kwargs={'pk': super_admin.pk})
        response = self.client.get(url)
        assert response.status_code == 302  # redirects with error
        
        # Try GET via AJAX -> should fail
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert response.status_code == 400
        
        # 3. Try to POST delete request -> should fail and not delete
        response = self.client.post(url)
        assert response.status_code == 302
        
        # Check that user still exists in the database
        assert User.objects.filter(pk=super_admin.pk).exists()
