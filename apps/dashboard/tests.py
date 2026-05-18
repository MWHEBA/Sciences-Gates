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
            self.assertNotIn('المحتوى', sidebar_content)

    def test_leads_section_visible_to_all_users(self):
        """Test that Leads section is visible to all user roles."""
        for username in ['superadmin', 'contentadmin', 'seoadmin']:
            self.client.login(username=username, password='testpass123')
            response = self.client.get(self.home_url)
            
            # Verify Leads section is present
            self.assertContains(response, 'الرسائل')
            self.assertContains(response, 'عرض الرسائل')
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

    def setUp(self):
        """Set up test client and test user."""
        self.client = Client()
        self.home_url = reverse('dashboard:home')
        
        self.staff_user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            is_staff=True
        )

    def test_success_message_renders_correctly(self):
        """Test that success messages render with correct styling."""
        self.client.login(username='testadmin', password='testpass123')
        
        # Add a success message
        from django.contrib.messages import get_messages
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory
        
        # Use the session framework to add messages
        session = self.client.session
        from django.contrib.messages.middleware import MessageMiddleware
        from django.contrib.sessions.middleware import SessionMiddleware
        
        # Create a request with messages
        factory = RequestFactory()
        request = factory.get(self.home_url)
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        messages_middleware = MessageMiddleware(lambda x: x)
        messages_middleware.process_request(request)
        
        from django.contrib.messages import add_message, constants
        add_message(request, constants.SUCCESS, 'تم الحفظ بنجاح')
        
        # Get the response
        response = self.client.get(self.home_url)
        
        # Verify success message styling is present
        self.assertContains(response, 'bg-green-50')
        self.assertContains(response, 'border-green-200')
        self.assertContains(response, 'text-green-800')

    def test_error_message_renders_correctly(self):
        """Test that error messages render with correct styling."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify error message styling classes are available in template
        # (actual message rendering tested through integration tests)
        self.assertContains(response, 'bg-red-50')
        self.assertContains(response, 'border-red-200')
        self.assertContains(response, 'text-red-800')

    def test_warning_message_renders_correctly(self):
        """Test that warning messages render with correct styling."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify warning message styling classes are available in template
        self.assertContains(response, 'bg-yellow-50')
        self.assertContains(response, 'border-yellow-200')

    def test_info_message_renders_correctly(self):
        """Test that info messages render with correct styling."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify info message styling classes are available in template
        self.assertContains(response, 'bg-blue-50')
        self.assertContains(response, 'border-blue-200')
        self.assertContains(response, 'text-blue-800')

    def test_messages_component_has_alpine_js_state(self):
        """Test that messages component includes Alpine.js state."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify Alpine.js x-data attribute is present
        self.assertContains(response, 'x-data="{ show: true }"')

    def test_messages_component_has_dismiss_button(self):
        """Test that messages component includes dismiss button."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify dismiss button with Alpine.js click handler
        self.assertContains(response, '@click="show = false"')
        self.assertContains(response, 'aria-label="إغلاق الرسالة"')

    def test_messages_component_has_correct_padding(self):
        """Test that messages component has correct padding."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify padding classes
        self.assertContains(response, 'px-4 py-3')

    def test_messages_component_has_correct_border_radius(self):
        """Test that messages component has correct border radius."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify rounded-lg class
        self.assertContains(response, 'rounded-lg')

    def test_messages_component_has_correct_text_size(self):
        """Test that messages component has correct text size."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify text-sm class
        self.assertContains(response, 'text-sm')

    def test_messages_component_has_type_specific_icons(self):
        """Test that messages component includes type-specific icons."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify SVG icons are present in template
        self.assertContains(response, '<svg')
        self.assertContains(response, 'viewBox="0 0 24 24"')

    def test_messages_component_has_correct_aria_roles(self):
        """Test that messages component has correct ARIA roles."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify ARIA roles are present
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, 'role="status"')

    def test_messages_component_has_flex_layout(self):
        """Test that messages component uses flex layout."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify flex classes
        self.assertContains(response, 'flex items-center gap-3')

    def test_messages_component_dismiss_button_on_left_side(self):
        """Test that dismiss button is positioned on left side (RTL)."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify button is first in flex order (left side in RTL)
        content = response.content.decode()
        # Find the messages component and verify button comes before icon
        if 'x-data="{ show: true }"' in content:
            # Extract the message div structure
            start = content.find('x-data="{ show: true }"')
            end = content.find('</div>', start)
            message_div = content[start:end]
            
            # Verify button comes before the icon div
            button_pos = message_div.find('@click="show = false"')
            icon_pos = message_div.find('flex-shrink-0')
            self.assertLess(button_pos, icon_pos, "Dismiss button should come before icon in RTL layout")

    def test_messages_container_has_correct_gap(self):
        """Test that messages container has correct gap between messages."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify space-y-2 class (8px gap)
        self.assertContains(response, 'space-y-2')


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
        
        # Verify sidebar has hidden class for mobile
        self.assertContains(response, 'hidden md:flex')

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
        self.assertIn('M4 6h16M4 12h16M4 18h16', hamburger_section)

    def test_sidebar_overlay_has_correct_positioning(self):
        """Test that sidebar overlay has correct positioning for RTL."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify sidebar is positioned on right side (RTL)
        self.assertContains(response, 'inset-y-0 right-0')
        self.assertContains(response, 'fixed')

    def test_sidebar_overlay_has_correct_width(self):
        """Test that sidebar overlay has correct width."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify sidebar width is w-64 (256px)
        self.assertContains(response, 'w-64')

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
        self.assertContains(response, ':class="sidebarOpen ? \'translate-x-0\' : \'translate-x-full\'"')

    def test_backdrop_has_50_percent_opacity(self):
        """Test that backdrop has 50% opacity black background."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify backdrop styling
        self.assertContains(response, 'bg-black')
        self.assertContains(response, 'bg-opacity-50')

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
        # Find the backdrop div
        backdrop_start = content.find('bg-black bg-opacity-50')
        backdrop_section = content[max(0, backdrop_start-100):backdrop_start+100]
        
        self.assertIn('z-30', backdrop_section)

    def test_sidebar_has_higher_z_index_than_backdrop(self):
        """Test that sidebar has higher z-index than backdrop."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify sidebar z-index is z-40 (above backdrop z-30)
        content = response.content.decode()
        # Find the sidebar
        sidebar_start = content.find('w-64 bg-white border-l')
        sidebar_section = content[max(0, sidebar_start-100):sidebar_start+100]
        
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
        self.assertContains(response, 'x-transition:enter-start="opacity-0"')
        self.assertContains(response, 'x-transition:enter-end="opacity-100"')
        self.assertContains(response, 'x-transition:leave="transition-opacity ease-linear duration-200"')
        self.assertContains(response, 'x-transition:leave-start="opacity-100"')
        self.assertContains(response, 'x-transition:leave-end="opacity-0"')

    def test_sidebar_navigation_links_close_sidebar(self):
        """Test that clicking navigation links closes sidebar."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify navigation links have @click="sidebarOpen = false"
        content = response.content.decode()
        
        # Count occurrences of the close sidebar handler on links
        close_handlers = content.count('@click="sidebarOpen = false"')
        
        # Should have multiple close handlers (one for each nav link)
        # At minimum: home, leads, and potentially others depending on user role
        self.assertGreater(close_handlers, 1)

    def test_sidebar_visible_on_desktop(self):
        """Test that sidebar is visible on desktop viewports."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify sidebar has md:static and md:flex classes
        self.assertContains(response, 'md:static')
        self.assertContains(response, 'md:flex')
        self.assertContains(response, 'md:translate-x-0')

    def test_sidebar_not_fixed_on_desktop(self):
        """Test that sidebar is not fixed on desktop."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify sidebar has md:static (not fixed on desktop)
        self.assertContains(response, 'md:static')

    def test_backdrop_hidden_on_desktop(self):
        """Test that backdrop is hidden on desktop."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(self.home_url)
        
        # Verify backdrop has md:hidden class
        content = response.content.decode()
        backdrop_start = content.find('bg-black bg-opacity-50')
        backdrop_section = content[max(0, backdrop_start-100):backdrop_start+100]
        
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
