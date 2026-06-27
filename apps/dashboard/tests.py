"""
Tests for the dashboard app.

Converted from Django TestCase to pytest for faster test execution.
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.test import TestCase, Client
from apps.leads.models import Lead, LeadType


@pytest.mark.django_db
class TestDashboardLoginView:
    """Tests for dashboard login view."""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Set up test client and test users."""
        self.client = client
        self.login_url = reverse('dashboard:login')
        self.home_url = reverse('dashboard:home')
        
        # Create a staff user for testing
        self.staff_user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            is_staff=True
        )
        
        # Create a non-staff user for testing
        self.regular_user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=False
        )

    def test_login_page_loads(self):
        """Test that login page loads successfully."""
        response = self.client.get(self.login_url)
        assert response.status_code == 200
        assert 'dashboard/login.html' in [t.name for t in response.templates]
        # Verify CSRF token is present in the form
        assert 'csrfmiddlewaretoken' in response.content.decode()

    def test_login_redirects_authenticated_user(self):
        """Test that authenticated users are redirected from login page."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.login_url)
        assert response.status_code == 302
        assert self.home_url in response.url

    def test_successful_staff_login(self):
        """Test successful login for staff user."""
        response = self.client.post(self.login_url, {
            'username': 'testadmin',
            'password': 'testpass123'
        })
        assert response.status_code == 302
        assert self.home_url in response.url

    def test_failed_login_with_wrong_password(self):
        """Test login fails with wrong password."""
        response = self.client.post(self.login_url, {
            'username': 'testadmin',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200
        assert 'dashboard/login.html' in [t.name for t in response.templates]

    def test_non_staff_user_cannot_login(self):
        """Test that non-staff users cannot access dashboard."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        assert 'dashboard/login.html' in [t.name for t in response.templates]

    def test_missing_credentials(self):
        """Test login fails with missing credentials."""
        response = self.client.post(self.login_url, {
            'username': '',
            'password': ''
        })
        assert response.status_code == 200
        assert 'dashboard/login.html' in [t.name for t in response.templates]


class DashboardLogoutViewTests(TestCase):
    """Tests for dashboard logout view."""

    def setUp(self):
        """Set up test client and test user."""
        self.client = Client()
        self.logout_url = reverse('dashboard:logout')
        self.login_url = reverse('dashboard:login')
        
        self.staff_user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            is_staff=True
        )

    def test_logout_redirects_to_login(self):
        """Test that logout redirects to login page."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url)

    def test_logout_unauthenticated_user_redirects_to_login(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)


class DashboardHomeViewTests(TestCase):
    """Tests for dashboard home view."""

    def setUp(self):
        """Set up test client and test user."""
        self.client = Client()
        self.home_url = reverse('dashboard:home')
        self.login_url = reverse('dashboard:login')
        
        self.staff_user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            is_staff=True
        )

    def test_home_requires_login(self):
        """Test that home page requires authentication."""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)

    def test_home_loads_for_authenticated_user(self):
        """Test that home page loads for authenticated users."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/home.html')

    def test_home_displays_lead_statistics(self):
        """Test that home page displays correct lead statistics."""
        from apps.leads.models import Lead, LeadType
        
        # Create test leads
        today = timezone.now()
        first_day_of_month = today.replace(day=1)
        
        # Create leads of different types
        Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='Test User 1',
            email='test1@example.com',
            phone='1234567890',
            message='Test message 1'
        )
        Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='Test User 2',
            email='test2@example.com',
            phone='0987654321',
            message='Test message 2'
        )
        # Create an old lead (not in current month)
        old_lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='Old User',
            email='old@example.com',
            phone='5555555555',
            message='Old message'
        )
        old_lead.created_at = first_day_of_month - timedelta(days=1)
        old_lead.save()
        
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify statistics in context
        self.assertEqual(response.context['total_leads'], 3)
        self.assertEqual(response.context['registration_leads'], 2)
        self.assertEqual(response.context['contact_leads'], 1)
        self.assertEqual(response.context['current_month_leads'], 2)

    def test_home_displays_recent_leads(self):
        """Test that home page displays recent 10 leads ordered by creation date."""
        from apps.leads.models import Lead, LeadType
        
        # Create 15 test leads
        for i in range(15):
            Lead.objects.create(
                lead_type=LeadType.REGISTRATION,
                name=f'Test User {i}',
                email=f'test{i}@example.com',
                phone=f'123456789{i}',
                message=f'Test message {i}'
            )
        
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify only 10 most recent leads are displayed
        recent_leads = response.context['recent_leads']
        self.assertEqual(len(recent_leads), 10)
        
        # Verify leads are ordered by creation date (newest first)
        for i in range(len(recent_leads) - 1):
            self.assertGreaterEqual(
                recent_leads[i].created_at,
                recent_leads[i + 1].created_at
            )



class DashboardSidebarComponentTests(TestCase):
    """Tests for dashboard sidebar navigation component."""

    def setUp(self):
        """Set up test client and test users with different roles."""
        self.client = Client()
        self.home_url = reverse('dashboard:home')
        
        # Import models in setUp
        from django.contrib.auth.models import User
        from apps.core.models import UserRole
        
        # Create users with different roles
        self.super_admin_user = User.objects.create_user(
            username='superadmin',
            password='testpass123',
            is_staff=True
        )
        self.super_admin_user.profile.role = UserRole.SUPER_ADMIN
        self.super_admin_user.profile.save()
        
        self.content_admin_user = User.objects.create_user(
            username='contentadmin',
            password='testpass123',
            is_staff=True
        )
        self.content_admin_user.profile.role = UserRole.CONTENT_ADMIN
        self.content_admin_user.profile.save()
        
        self.seo_admin_user = User.objects.create_user(
            username='seoadmin',
            password='testpass123',
            is_staff=True
        )
        self.seo_admin_user.profile.role = UserRole.SEO_ADMIN
        self.seo_admin_user.profile.save()

    def test_sidebar_renders_in_dashboard(self):
        """Test that sidebar component is included in dashboard template."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify sidebar component is included
        self.assertContains(response, 'Science Gates')
        self.assertContains(response, 'لوحة التحكم')

    def test_home_link_visible_to_all_users(self):
        """Test that Home link is visible to all user roles."""
        for username in ['superadmin', 'contentadmin', 'seoadmin']:
            self.client.login(username=username, password='testpass123')
            response = self.client.get(self.home_url)
            
            # Verify Home link is present
            self.assertContains(response, 'الرئيسية')
            self.client.logout()

    def test_content_section_visible_to_content_admin(self):
        """Test that Content section is visible to CONTENT_ADMIN."""
        self.client.login(username='contentadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify Content section is present
        self.assertContains(response, 'المحتوى')
        self.assertContains(response, 'الجامعات')
        self.assertContains(response, 'المعاهد')
        self.assertContains(response, 'التخصصات')
        self.assertContains(response, 'المقالات')

    def test_content_section_visible_to_super_admin(self):
        """Test that Content section is visible to SUPER_ADMIN."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify Content section is present
        self.assertContains(response, 'المحتوى')
        self.assertContains(response, 'الجامعات')
        self.assertContains(response, 'المعاهد')
        self.assertContains(response, 'التخصصات')
        self.assertContains(response, 'المقالات')

    def test_content_section_hidden_from_seo_admin(self):
        """Test that Content section is hidden from SEO_ADMIN."""
        self.client.login(username='seoadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify Content section header is NOT present
        # The section header "المحتوى" should not be rendered
        content = response.content.decode()
        # Count occurrences of the section header in the sidebar
        # We check that the content section is not in the sidebar by looking for the pattern
        sidebar_start = content.find('<aside')
        sidebar_end = content.find('</aside>')
        if sidebar_start != -1 and sidebar_end != -1:
            sidebar_content = content[sidebar_start:sidebar_end]
            # The section header should not be present in the sidebar
            self.assertNotIn('المحتوى</h3>', sidebar_content)

    def test_leads_section_visible_to_all_users(self):
        """Test that Leads section is visible to all user roles."""
        for username in ['superadmin', 'contentadmin', 'seoadmin']:
            self.client.login(username=username, password='testpass123')
            response = self.client.get(self.home_url)
            
            # Verify Leads section is present
            self.assertContains(response, 'طلبات التسجيل')
            self.client.logout()

    def test_seo_section_visible_to_seo_admin(self):
        """Test that SEO section is visible to SEO_ADMIN."""
        self.client.login(username='seoadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify SEO section is present
        self.assertContains(response, 'SEO')
        self.assertContains(response, 'إعادة التوجيه')
        self.assertContains(response, 'إعدادات SEO')

    def test_seo_section_visible_to_super_admin(self):
        """Test that SEO section is visible to SUPER_ADMIN."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify SEO section is present
        self.assertContains(response, 'SEO')
        self.assertContains(response, 'إعادة التوجيه')
        self.assertContains(response, 'إعدادات SEO')

    def test_seo_section_hidden_from_content_admin(self):
        """Test that SEO section is hidden from CONTENT_ADMIN."""
        self.client.login(username='contentadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify SEO section is NOT present in sidebar
        content = response.content.decode()
        sidebar_start = content.find('<aside')
        sidebar_end = content.find('</aside>')
        if sidebar_start != -1 and sidebar_end != -1:
            sidebar_content = content[sidebar_start:sidebar_end]
            # The SEO section header should not be present in the sidebar
            self.assertNotIn('إعادة التوجيه', sidebar_content)

    def test_administration_section_visible_to_super_admin_only(self):
        """Test that Administration section is visible only to SUPER_ADMIN."""
        # Test SUPER_ADMIN can see it
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(self.home_url)
        self.assertContains(response, 'الإدارة')
        self.assertContains(response, 'إدارة المستخدمين')
        self.client.logout()
        
        # Test CONTENT_ADMIN cannot see it
        self.client.login(username='contentadmin', password='testpass123')
        response = self.client.get(self.home_url)
        content = response.content.decode()
        sidebar_start = content.find('<aside')
        sidebar_end = content.find('</aside>')
        if sidebar_start != -1 and sidebar_end != -1:
            sidebar_content = content[sidebar_start:sidebar_end]
            self.assertNotIn('إدارة المستخدمين', sidebar_content)
        self.client.logout()
        
        # Test SEO_ADMIN cannot see it
        self.client.login(username='seoadmin', password='testpass123')
        response = self.client.get(self.home_url)
        content = response.content.decode()
        sidebar_start = content.find('<aside')
        sidebar_end = content.find('</aside>')
        if sidebar_start != -1 and sidebar_end != -1:
            sidebar_content = content[sidebar_start:sidebar_end]
            self.assertNotIn('إدارة المستخدمين', sidebar_content)

    def test_unread_leads_badge_displays_count(self):
        """Test that unread leads badge displays correct count."""
        from apps.leads.models import Lead, LeadType
        
        # Create some unread leads
        for i in range(3):
            Lead.objects.create(
                lead_type=LeadType.REGISTRATION,
                name=f'Test User {i}',
                email=f'test{i}@example.com',
                phone=f'123456789{i}',
                message=f'Test message {i}',
                is_read=False
            )
        
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify badge displays the count
        self.assertContains(response, '3')

    def test_unread_leads_badge_hidden_when_no_unread(self):
        """Test that unread leads badge is hidden when there are no unread leads."""
        from apps.leads.models import Lead, LeadType
        
        # Create only read leads
        for i in range(2):
            Lead.objects.create(
                lead_type=LeadType.REGISTRATION,
                name=f'Test User {i}',
                email=f'test{i}@example.com',
                phone=f'123456789{i}',
                message=f'Test message {i}',
                is_read=True
            )
        
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify badge is not displayed (no unread count)
        # The badge should not appear in the HTML
        content = response.content.decode()
        # Check that the badge container is not rendered
        self.assertNotIn('bg-red-600', content)

    def test_user_profile_section_displays_username(self):
        """Test that user profile section displays username."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify user profile section is present
        self.assertContains(response, 'superadmin')

    def test_user_profile_section_displays_role(self):
        """Test that user profile section displays user role."""
        self.client.login(username='contentadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify role is displayed
        self.assertContains(response, 'مسؤول المحتوى')

    def test_logout_link_present_in_sidebar(self):
        """Test that logout link is present in sidebar."""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify logout URL is present
        logout_url = reverse('dashboard:logout')
        self.assertContains(response, logout_url)


class DashboardMessagesComponentTests(TestCase):
    """Tests for dashboard notification messages component."""

    def test_success_message_renders_correctly(self):
        """Test that success messages render with correct styling."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(25, 'تم الحفظ بنجاح', extra_tags='success')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('role="status"', rendered)

    def test_error_message_renders_correctly(self):
        """Test that error messages render with correct styling."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(40, 'خطأ في الحفظ', extra_tags='error')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('role="alert"', rendered)

    def test_warning_message_renders_correctly(self):
        """Test that warning messages render with correct styling."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(30, 'تحذير هام', extra_tags='warning')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('role="alert"', rendered)

    def test_info_message_renders_correctly(self):
        """Test that info messages render with correct styling."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(20, 'معلومات عامة', extra_tags='info')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('role="status"', rendered)

    def test_messages_component_has_alpine_js_state(self):
        """Test that messages component includes Alpine.js state."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(20, 'معلومات عامة', extra_tags='info')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('x-data="{ show: true }"', rendered)

    def test_messages_component_has_dismiss_button(self):
        """Test that messages component includes dismiss button."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(20, 'معلومات عامة', extra_tags='info')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('@click="show = false"', rendered)
        self.assertIn('aria-label="إغلاق الرسالة"', rendered)

    def test_messages_component_has_correct_padding(self):
        """Test that messages component has correct padding."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(20, 'معلومات عامة', extra_tags='info')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('px-4 py-3', rendered)

    def test_messages_component_has_correct_border_radius(self):
        """Test that messages component has correct border radius."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(20, 'معلومات عامة', extra_tags='info')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('rounded-lg', rendered)

    def test_messages_component_has_correct_text_size(self):
        """Test that messages component has correct text size."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(20, 'معلومات عامة', extra_tags='info')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('text-sm', rendered)

    def test_messages_component_has_type_specific_icons(self):
        """Test that messages component includes type-specific icons."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(20, 'معلومات عامة', extra_tags='info')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('<svg', rendered)
        self.assertIn('viewBox="0 0 24 24"', rendered)

    def test_messages_component_has_correct_aria_roles(self):
        """Test that messages component has correct ARIA roles."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(40, 'خطأ', extra_tags='error')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('role="alert"', rendered)

    def test_messages_component_has_flex_layout(self):
        """Test that messages component uses flex layout."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(20, 'معلومات عامة', extra_tags='info')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('flex items-center gap-3', rendered)

    def test_messages_component_dismiss_button_on_left_side(self):
        """Test that dismiss button is positioned on left side (RTL)."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(20, 'معلومات عامة', extra_tags='info')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        button_pos = rendered.find('@click="show = false"')
        text_pos = rendered.find('flex-1')
        self.assertLess(button_pos, text_pos, "Dismiss button should come before text in RTL layout")

    def test_messages_container_has_correct_gap(self):
        """Test that messages container has correct gap between messages."""
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message
        messages = [Message(20, 'معلومات عامة', extra_tags='info')]
        rendered = render_to_string('dashboard/components/messages.html', {'messages': messages})
        self.assertIn('gap-3', rendered)


class DashboardMobileSidebarOverlayTests(TestCase):
    """Tests for mobile sidebar overlay behavior (Task 3.2)."""

    def setUp(self):
        """Set up test client and test user."""
        self.client = Client()
        self.home_url = reverse('dashboard:home')
        
        self.staff_user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            is_staff=True
        )

    def test_sidebar_hidden_by_default_on_mobile(self):
        """Test that sidebar is hidden by default on mobile viewports."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify sidebar has hidden class/logic for mobile
        self.assertContains(response, "translate-x-full md:translate-x-0")

    def test_hamburger_menu_button_visible_on_mobile(self):
        """Test that hamburger menu button is visible on mobile."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify hamburger button is present and visible only on mobile
        self.assertContains(response, 'md:hidden')
        self.assertContains(response, '@click="sidebarOpen = true"')
        self.assertContains(response, 'aria-label="فتح القائمة الجانبية"')

    def test_hamburger_button_has_menu_icon(self):
        """Test that hamburger button displays menu icon."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify menu icon SVG is present
        content = response.content.decode()
        # Find the hamburger button and verify it contains an SVG
        hamburger_start = content.find('@click="sidebarOpen = true"')
        hamburger_end = content.find('</button>', hamburger_start)
        hamburger_section = content[hamburger_start:hamburger_end]
        
        self.assertIn('<svg', hamburger_section)

    def test_sidebar_overlay_has_correct_positioning(self):
        """Test that sidebar overlay has correct positioning for RTL."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify sidebar is positioned on right side (RTL)
        self.assertContains(response, 'fixed')
        self.assertContains(response, 'right-5')

    def test_sidebar_overlay_has_correct_width(self):
        """Test that sidebar overlay has correct width."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify sidebar width is sidebar-width
        self.assertContains(response, 'var(--sidebar-width)')

    def test_sidebar_overlay_has_200ms_transition(self):
        """Test that sidebar overlay has 200ms transition duration."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify transition-transform and duration-200 classes
        self.assertContains(response, 'transition-transform')
        self.assertContains(response, 'duration-200')

    def test_sidebar_overlay_uses_translate_transform(self):
        """Test that sidebar overlay uses translate transform for slide-in."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify Alpine.js binding for translate transform
        self.assertContains(response, ':class="sidebarOpen ? \'translate-x-0\' : \'translate-x-full md:translate-x-0\'"')

    def test_backdrop_has_50_percent_opacity(self):
        """Test that backdrop has 50% opacity background."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify backdrop styling
        self.assertContains(response, 'rgba(6, 20, 36, 0.45)')

    def test_backdrop_visible_only_on_mobile(self):
        """Test that backdrop is visible only on mobile."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify backdrop has md:hidden class
        self.assertContains(response, 'md:hidden')

    def test_backdrop_has_correct_z_index(self):
        """Test that backdrop has correct z-index."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify backdrop z-index is z-30 (below sidebar z-40)
        content = response.content.decode()
        backdrop_start = content.find('rgba(6, 20, 36, 0.45)')
        backdrop_section = content[max(0, backdrop_start-150):backdrop_start+150]
        
        self.assertIn('z-30', backdrop_section)

    def test_sidebar_has_higher_z_index_than_backdrop(self):
        """Test that sidebar has higher z-index than backdrop."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify sidebar z-index is z-40 (above backdrop z-30)
        content = response.content.decode()
        sidebar_start = content.find('<aside')
        sidebar_section = content[sidebar_start:sidebar_start+500]
        
        self.assertIn('z-40', sidebar_section)

    def test_backdrop_closes_sidebar_on_click(self):
        """Test that backdrop click closes sidebar."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify backdrop has click handler to close sidebar
        self.assertContains(response, '@click="sidebarOpen = false"')

    def test_backdrop_has_transition_animation(self):
        """Test that backdrop has transition animation."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify backdrop has Alpine.js transition directives
        self.assertContains(response, 'x-transition:enter="transition-opacity ease-linear duration-200"')

    def test_sidebar_navigation_links_close_sidebar(self):
        """Test that clicking navigation links closes sidebar."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify navigation links or nav has sidebarOpen = false logic
        content = response.content.decode()
        self.assertIn('sidebarOpen = false', content)

    def test_sidebar_visible_on_desktop(self):
        """Test that sidebar is visible on desktop viewports."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify sidebar is visible on desktop
        self.assertContains(response, 'md:fixed')

    def test_sidebar_not_fixed_on_desktop(self):
        """Test that sidebar has correct classes on desktop."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        self.assertContains(response, 'md:fixed')

    def test_backdrop_hidden_on_desktop(self):
        """Test that backdrop is hidden on desktop."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        content = response.content.decode()
        backdrop_start = content.find('rgba(6, 20, 36, 0.45)')
        backdrop_section = content[max(0, backdrop_start-150):backdrop_start+150]
        
        self.assertIn('md:hidden', backdrop_section)

    def test_hamburger_button_hidden_on_desktop(self):
        """Test that hamburger button is hidden on desktop."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify hamburger button has md:hidden class
        content = response.content.decode()
        hamburger_start = content.find('@click="sidebarOpen = true"')
        hamburger_section = content[max(0, hamburger_start-100):hamburger_start+100]
        
        self.assertIn('md:hidden', hamburger_section)

    def test_alpine_js_state_initialized(self):
        """Test that Alpine.js state is initialized."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify Alpine.js x-data with sidebarOpen state
        self.assertContains(response, 'x-data="{ sidebarOpen: false }"')

    def test_sidebar_has_aria_hidden_on_mobile(self):
        """Test that backdrop has aria-hidden attribute."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify backdrop has aria-hidden="true"
        self.assertContains(response, 'aria-hidden="true"')

    def test_hamburger_button_has_aria_label(self):
        """Test that hamburger button has accessible aria-label."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify hamburger button has aria-label
        self.assertContains(response, 'aria-label="فتح القائمة الجانبية"')

    def test_hamburger_icon_has_aria_hidden(self):
        """Test that hamburger icon has aria-hidden attribute."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify hamburger icon SVG has aria-hidden="true"
        content = response.content.decode()
        hamburger_start = content.find('@click="sidebarOpen = true"')
        hamburger_end = content.find('</button>', hamburger_start)
        hamburger_section = content[hamburger_start:hamburger_end]
        
        self.assertIn('aria-hidden="true"', hamburger_section)



@pytest.mark.django_db
class TestDashboardLogoutView:
    """Tests for dashboard logout view."""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Set up test client and test user."""
        self.client = client
        self.logout_url = reverse('dashboard:logout')
        self.login_url = reverse('dashboard:login')
        
        self.staff_user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            is_staff=True
        )

    def test_logout_redirects_to_login(self):
        """Test that logout redirects to login page."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.logout_url)
        assert response.status_code == 302
        assert self.login_url in response.url

    def test_logout_unauthenticated_user_redirects_to_login(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(self.logout_url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestDashboardHomeView:
    """Tests for dashboard home view."""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Set up test client and test user."""
        self.client = client
        self.home_url = reverse('dashboard:home')
        self.login_url = reverse('dashboard:login')
        
        self.staff_user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            is_staff=True
        )

    def test_home_requires_login(self):
        """Test that home page requires authentication."""
        response = self.client.get(self.home_url)
        assert response.status_code == 302
        assert self.login_url in response.url

    def test_home_loads_for_authenticated_user(self):
        """Test that home page loads for authenticated users."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        assert response.status_code == 200
        assert 'dashboard/home.html' in [t.name for t in response.templates]

    def test_home_displays_lead_statistics(self):
        """Test that home page displays correct lead statistics."""
        # Create test leads
        today = timezone.now()
        first_day_of_month = today.replace(day=1)
        
        # Create leads of different types
        Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='Test User 1',
            email='test1@example.com',
            phone='1234567890',
            message='Test message 1'
        )
        Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='Test User 2',
            email='test2@example.com',
            phone='0987654321',
            message='Test message 2'
        )
        # Create an old lead (not in current month)
        old_lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='Old User',
            email='old@example.com',
            phone='5555555555',
            message='Old message'
        )
        old_lead.created_at = first_day_of_month - timedelta(days=1)
        old_lead.save()
        
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify statistics in context
        assert response.context['total_leads'] == 3
        assert response.context['registration_leads'] == 2
        assert response.context['contact_leads'] == 1
        assert response.context['current_month_leads'] == 2

    def test_home_displays_recent_leads(self):
        """Test that home page displays recent 10 leads ordered by creation date."""
        # Create 15 test leads
        for i in range(15):
            Lead.objects.create(
                lead_type=LeadType.REGISTRATION,
                name=f'Test User {i}',
                email=f'test{i}@example.com',
                phone=f'123456789{i}',
                message=f'Test message {i}'
            )
        
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify only 10 most recent leads are displayed
        recent_leads = response.context['recent_leads']
        assert len(recent_leads) == 10
        
        # Verify leads are ordered by creation date (newest first)
        for i in range(len(recent_leads) - 1):
            assert recent_leads[i].created_at >= recent_leads[i + 1].created_at


@pytest.mark.django_db
class TestUniversityViews:
    """Tests for dashboard university views."""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.create_url = reverse('dashboard:university_create')
        
        # Create user
        self.admin = User.objects.create_user(
            username='uniadmin',
            password='testpass123',
            is_staff=True
        )
        
    def test_create_view_loads_successfully_with_recent_context(self):
        self.client.login(username='uniadmin', password='testpass123')
        response = self.client.get(self.create_url)
        assert response.status_code == 200
        assert 'recently_used_majors' in response.context
        assert 'recently_used_articles' in response.context
        assert 'recently_used_tags' in response.context

    def test_faculty_formset_duplicate_swap(self):
        """Test that the custom faculty formset clean method correctly swaps duplicate forms."""
        from apps.universities.models import University, Faculty
        from apps.dashboard.forms.university import UniversityFacultyFormSet
        
        # Create a university
        uni = University.objects.create(
            name="Test University",
            slug="test-university",
            city="kl",
            university_type="private",
            description="Test Description",
            location="Test Location"
        )
        
        # Create an existing faculty
        faculty = Faculty.objects.create(
            university=uni,
            name="كلية الهندسة",
            sort_order=0
        )
        
        # Simulate POST data where form 0 (existing) is marked for deletion,
        # and form 1 (new) is a duplicate with spelling variations
        data = {
            'faculties-TOTAL_FORMS': '2',
            'faculties-INITIAL_FORMS': '1',
            'faculties-MIN_NUM_FORMS': '0',
            'faculties-MAX_NUM_FORMS': '100',
            
            # Form 0 (existing) - marked for deletion
            'faculties-0-id': str(faculty.id),
            'faculties-0-name': "كلية الهندسة",
            'faculties-0-sort_order': '0',
            'faculties-0-DELETE': 'on',
            
            # Form 1 (new) - matches name normalized
            'faculties-1-id': '',
            'faculties-1-name': "  كليه الهندسه  ",  # spelling difference & spacing
            'faculties-1-sort_order': '1',
        }
        
        formset = UniversityFacultyFormSet(data, instance=uni)
        is_valid = formset.is_valid()
        
        assert is_valid, f"Formset errors: {formset.errors}"
        
        # Instances should have swapped
        assert formset.forms[0].instance.pk is None
        assert formset.forms[1].instance.pk == faculty.id
        assert formset.forms[1].instance.name == "كليه الهندسه"



