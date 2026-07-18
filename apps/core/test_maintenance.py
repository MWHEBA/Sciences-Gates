from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from apps.core.models import SiteSettings


class MaintenanceModeTestCase(TestCase):
    def setUp(self):
        self.settings_obj = SiteSettings.get_settings()
        self.settings_obj.maintenance_mode = False
        self.settings_obj.maintenance_title = "صيانة"
        self.settings_obj.maintenance_message = "رسالة صيانة"
        self.settings_obj.maintenance_bypass_ips = ""
        self.settings_obj.maintenance_bypass_staff = True
        self.settings_obj.save()

        # Admin user
        self.staff_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123',
            is_staff=True
        )
        # Normal user
        self.normal_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password123',
            is_staff=False
        )

    def tearDown(self):
        self.settings_obj.maintenance_mode = False
        self.settings_obj.save()

    def test_maintenance_disabled_by_default(self):
        """Test that the home page and public pages load normally when maintenance is disabled."""
        response = self.client.get(reverse('about_us'))
        self.assertEqual(response.status_code, 200)

    def test_maintenance_enabled_blocks_public(self):
        """Test that enabling maintenance blocks anonymous public access with a 503 status code."""
        self.settings_obj.maintenance_mode = True
        self.settings_obj.save()

        response = self.client.get(reverse('about_us'))
        self.assertEqual(response.status_code, 503)
        self.assertIn('Retry-After', response)
        self.assertIn("صيانة", response.content.decode('utf-8'))

    def test_maintenance_excluded_paths(self):
        """Test that admin and dashboard paths bypass maintenance mode."""
        from django.conf import settings
        self.settings_obj.maintenance_mode = True
        self.settings_obj.save()

        # Try to access admin URL prefix
        admin_path = f"/{settings.ADMIN_URL.strip('/')}/"
        response = self.client.get(admin_path)
        self.assertNotEqual(response.status_code, 503)

        response = self.client.get(admin_path.rstrip('/'))
        self.assertNotEqual(response.status_code, 503)

        # Try to access dashboard URL prefix
        dash_path = f"/{settings.DASHBOARD_URL.strip('/')}/"
        response = self.client.get(dash_path)
        self.assertNotEqual(response.status_code, 503)

        response = self.client.get(dash_path.rstrip('/'))
        self.assertNotEqual(response.status_code, 503)

    def test_staff_bypass(self):
        """Test that authenticated staff users bypass maintenance mode."""
        self.settings_obj.maintenance_mode = True
        self.settings_obj.maintenance_bypass_staff = True
        self.settings_obj.save()

        # Log in normal user
        self.client.login(username='user', password='password123')
        response = self.client.get(reverse('about_us'))
        self.assertEqual(response.status_code, 503)

        # Log in staff user
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('about_us'))
        self.assertEqual(response.status_code, 200)

    def test_ip_bypass(self):
        """Test that whitelisted IPs bypass maintenance mode."""
        self.settings_obj.maintenance_mode = True
        self.settings_obj.maintenance_bypass_ips = "192.168.1.100, 127.0.0.1"
        self.settings_obj.save()

        # Non-whitelisted request
        response = self.client.get(reverse('about_us'), REMOTE_ADDR='1.1.1.1')
        self.assertEqual(response.status_code, 503)

        # Whitelisted request
        response = self.client.get(reverse('about_us'), REMOTE_ADDR='192.168.1.100')
        self.assertEqual(response.status_code, 200)

        # Whitelisted Cloudflare request
        response = self.client.get(reverse('about_us'), REMOTE_ADDR='1.1.1.1', HTTP_CF_CONNECTING_IP='127.0.0.1')
        self.assertEqual(response.status_code, 200)
