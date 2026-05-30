"""
Tests for the Delete Confirmation template (task 18.1).

Tests verify:
- Template extends base.html
- Item name displays in bold within warning message
- Item name is truncated at 100 characters with ellipsis
- Permanent deletion warning message is displayed
- Danger confirm button is present
- Secondary cancel button is present and links to list page
- Card container uses p-6 padding and max-w-lg width
- No JavaScript modal dialogs (dedicated page only)
- CSS variable usage for colors
- Proper accessibility attributes

Validates: Requirements 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7
"""
from django.test import TestCase, RequestFactory
from django.template.loader import render_to_string


class DeleteConfirmationTemplateTest(TestCase):
    """Test the delete confirmation template."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        
        # Create user with profile to satisfy sidebar layout inside base.html
        from django.contrib.auth.models import User
        from apps.core.models import UserProfile, UserRole
        self.user = User.objects.create_user(
            username='admin_test',
            email='admin_test@example.com',
            password='password123'
        )
        self.request.user = self.user
        profile = self.user.profile
        profile.role = UserRole.SUPER_ADMIN
        profile.save()

    def _render(self, context):
        return render_to_string('dashboard/delete_confirm.html', context, request=self.request)
    
    def test_template_extends_base(self):
        """Test that delete_confirm.html extends base.html."""
        # Render the template with minimal context
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check that base template elements are present
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('dir="rtl"', html)
        self.assertIn('lang="ar"', html)
    
    def test_item_name_displays_in_bold(self):
        """Test that item name displays in bold within warning message."""
        context = {
            'item_name': 'Test Item Name',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for bold tag around item name
        self.assertIn('<strong', html)
        self.assertIn('Test Item Name', html)
    
    def test_item_name_truncated_at_100_chars(self):
        """Test that item name is truncated at 100 characters with ellipsis."""
        # Create a name longer than 100 characters
        long_name = 'A' * 150
        context = {
            'item_name': long_name,
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check that the name is truncated (Django's truncatechars adds ellipsis)
        # The output should contain the truncated version, not the full 150 chars
        self.assertNotIn('A' * 100, html)  # Full 100 A's should not be present
        self.assertTrue('…' in html or '...' in html)  # Ellipsis should be present
    
    def test_permanent_deletion_warning_displayed(self):
        """Test that permanent deletion warning message is displayed."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for warning message
        self.assertIn('تحذير', html)  # Arabic for "Warning"
        self.assertIn('لا يمكن التراجع', html)  # "Cannot be undone"
        self.assertIn('حذف البيانات بشكل دائم', html)  # "Delete data permanently"
    
    def test_danger_confirm_button_present(self):
        """Test that danger confirm button is present."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for delete button
        self.assertIn('type="submit"', html)
        self.assertIn('حذف نهائياً', html)  # Arabic for "Delete Permanently"
        self.assertIn('method="post"', html)
    
    def test_secondary_cancel_button_present(self):
        """Test that secondary cancel button is present and links to list page."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for cancel button
        self.assertIn('إلغاء', html)  # Arabic for "Cancel"
        self.assertIn('/dashboard/items/', html)  # Cancel URL should be present
    
    def test_card_container_styling(self):
        """Test that card container uses p-6 padding and max-w-lg width."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for card styling classes
        self.assertIn('p-6', html)  # Padding
        self.assertIn('max-w-lg', html)  # Max width
        self.assertIn('bg-white', html)  # White background
        self.assertIn('rounded-lg', html)  # Rounded corners
        self.assertIn('shadow-sm', html)  # Shadow
    
    def test_no_javascript_modal_dialogs(self):
        """Test that no JavaScript modal dialogs are used."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check that no modal-related JavaScript is present
        self.assertNotIn('modal', html.lower())
        self.assertNotIn('dialog', html.lower())
        self.assertNotIn('confirm(', html)  # No JavaScript confirm dialogs
    
    def test_css_variable_usage(self):
        """Test that CSS variables are used for colors."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for CSS variable usage
        self.assertIn('var(--danger)', html)
        self.assertIn('var(--border)', html)
        self.assertIn('var(--text-primary)', html)
        self.assertIn('var(--text-secondary)', html)
        self.assertIn('var(--bg-light)', html)
    
    def test_no_hardcoded_colors(self):
        """Test that no hardcoded hex or rgb colors are used (except for rgba fallback)."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check that no hardcoded hex colors are present (except in SVG)
        # Allow rgba for semi-transparent backgrounds as fallback
        clean_html = html.replace('viewBox', '').replace('href="#"', '').replace("href='#'", '')
        self.assertNotIn('#', clean_html)
    
    def test_icon_accessibility(self):
        """Test that icon has proper accessibility attributes."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for aria-hidden on decorative icon
        self.assertIn('aria-hidden="true"', html)
    
    def test_form_csrf_token(self):
        """Test that CSRF token is present in delete form."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for CSRF token
        self.assertIn('csrfmiddlewaretoken', html)
    
    def test_delete_form_action_url(self):
        """Test that delete form has correct action URL."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for form action
        self.assertIn('action="/dashboard/items/1/delete/"', html)
    
    def test_centered_layout(self):
        """Test that card is centered horizontally."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for centering classes
        self.assertIn('flex justify-center', html)
    
    def test_button_styling_classes(self):
        """Test that buttons have proper styling classes."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for button styling
        self.assertIn('rounded-lg', html)
        self.assertIn('font-medium', html)
        self.assertIn('transition-colors', html)
        self.assertIn('duration-200', html)
        self.assertIn('cursor-pointer', html)
    
    def test_rtl_layout(self):
        """Test that template supports RTL layout."""
        context = {
            'item_name': 'Test Item',
            'cancel_url': '/dashboard/items/',
            'delete_url': '/dashboard/items/1/delete/',
        }
        html = self._render(context)
        
        # Check for RTL attributes
        self.assertIn('dir="rtl"', html)
        self.assertIn('lang="ar"', html)
