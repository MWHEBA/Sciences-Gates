import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from apps.core.models import UserProfile, UserRole


@pytest.mark.django_db
class TestUserModalViews:
    """Tests for user management modal views and AJAX APIs."""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Set up test client and user fixtures."""
        self.client = client
        self.list_url = reverse('dashboard:user_list')
        self.create_url = reverse('dashboard:user_create')
        
        # Create a super admin user to pass SuperAdminRequiredMixin
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            password='adminpass123',
            is_staff=True
        )
        self.super_admin.profile.role = UserRole.SUPER_ADMIN
        self.super_admin.profile.save()
        
        # Create another staff user
        self.staff_user = User.objects.create_user(
            username='staffone',
            email='staffone@example.com',
            password='staffpass123',
            is_staff=True
        )
        self.staff_user.profile.role = UserRole.CONTENT_ADMIN
        self.staff_user.profile.save()

        # Log in as super admin by default
        self.client.login(username='superadmin', password='adminpass123')

    def test_user_list_search_filter(self):
        """Test search and role filtering in UserListView."""
        # 1. Without filters, both users are returned
        response = self.client.get(self.list_url)
        assert response.status_code == 200
        users = list(response.context['users'])
        assert self.super_admin in users
        assert self.staff_user in users

        # 2. Search query matches staffone
        response = self.client.get(self.list_url, {'search': 'staffone'})
        assert response.status_code == 200
        users = list(response.context['users'])
        assert self.staff_user in users
        assert self.super_admin not in users

        # 3. Search query matches email
        response = self.client.get(self.list_url, {'search': 'super@'})
        assert response.status_code == 200
        users = list(response.context['users'])
        assert self.super_admin in users
        assert self.staff_user not in users

        # 4. Role filter matches content_admin
        response = self.client.get(self.list_url, {'role': 'content_admin'})
        assert response.status_code == 200
        users = list(response.context['users'])
        assert self.staff_user in users
        assert self.super_admin not in users

    def test_user_create_get_redirects(self):
        """Test that direct GET request to user_create redirects to user_list."""
        response = self.client.get(self.create_url)
        assert response.status_code == 302
        assert response.url == self.list_url

    def test_user_create_ajax_success(self):
        """Test successful user creation via AJAX POST."""
        post_data = {
            'create-username': 'newuser',
            'create-email': 'newuser@example.com',
            'create-first_name': 'New',
            'create-last_name': 'User',
            'create-password': 'SecurePass123',
            'create-password_confirm': 'SecurePass123',
            'create-role': 'seo_admin'
        }
        response = self.client.post(
            self.create_url,
            post_data,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'SecurePass123' not in str(data)  # Ensure password is not returned
        
        # Verify user was created in database
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        assert user.is_staff is True
        assert user.profile.role == UserRole.SEO_ADMIN
        assert user.check_password('SecurePass123') is True

    def test_user_create_ajax_validation_error(self):
        """Test validation error in AJAX user creation (e.g. duplicate username)."""
        post_data = {
            'create-username': 'staffone',  # already exists
            'create-email': 'different@example.com',
            'create-password': 'SecurePass123',
            'create-password_confirm': 'SecurePass123',
            'create-role': 'seo_admin'
        }
        response = self.client.post(
            self.create_url,
            post_data,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 400
        data = response.json()
        assert data['status'] == 'error'
        assert 'username' in data['errors']

    def test_user_update_get_ajax_data(self):
        """Test that GET request with AJAX on user_edit returns user details in JSON."""
        edit_url = reverse('dashboard:user_edit', args=[self.staff_user.pk])
        response = self.client.get(
            edit_url,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['username'] == 'staffone'
        assert data['email'] == 'staffone@example.com'
        assert data['first_name'] == ''
        assert data['role'] == UserRole.CONTENT_ADMIN

    def test_user_update_get_redirects(self):
        """Test that direct GET request to user_edit redirects to user_list."""
        edit_url = reverse('dashboard:user_edit', args=[self.staff_user.pk])
        response = self.client.get(edit_url)
        assert response.status_code == 302
        assert response.url == self.list_url

    def test_user_update_ajax_success_without_password(self):
        """Test updating user details via AJAX POST without changing the password."""
        edit_url = reverse('dashboard:user_edit', args=[self.staff_user.pk])
        post_data = {
            'edit-email': 'updated@example.com',
            'edit-first_name': 'Updated',
            'edit-last_name': 'Name',
            'edit-role': 'seo_admin',
            'edit-password': '',
            'edit-password_confirm': ''
        }
        response = self.client.post(
            edit_url,
            post_data,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        
        # Verify in DB
        user = User.objects.get(pk=self.staff_user.pk)
        assert user.email == 'updated@example.com'
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'
        assert user.profile.role == UserRole.SEO_ADMIN
        # Password should still be original
        assert user.check_password('staffpass123') is True

    def test_user_update_ajax_success_with_password(self):
        """Test updating user details and password via AJAX POST."""
        edit_url = reverse('dashboard:user_edit', args=[self.staff_user.pk])
        post_data = {
            'edit-email': 'staffone@example.com',
            'edit-first_name': '',
            'edit-last_name': '',
            'edit-role': 'content_admin',
            'edit-password': 'NewSuperSecurePassword1!',
            'edit-password_confirm': 'NewSuperSecurePassword1!'
        }
        response = self.client.post(
            edit_url,
            post_data,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        
        # Verify password is updated in DB
        user = User.objects.get(pk=self.staff_user.pk)
        assert user.check_password('NewSuperSecurePassword1!') is True
        assert user.check_password('staffpass123') is False

    def test_user_update_ajax_password_mismatch(self):
        """Test validation error when new password fields do not match."""
        edit_url = reverse('dashboard:user_edit', args=[self.staff_user.pk])
        post_data = {
            'edit-email': 'staffone@example.com',
            'edit-first_name': '',
            'edit-last_name': '',
            'edit-role': 'content_admin',
            'edit-password': 'NewSuperSecurePassword1!',
            'edit-password_confirm': 'WrongConfirmation'
        }
        response = self.client.post(
            edit_url,
            post_data,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 400
        data = response.json()
        assert data['status'] == 'error'
        # Django validation errors for non-field error are keyed as __all__
        assert '__all__' in data['errors']
        assert 'كلمات المرور غير متطابقة' in data['errors']['__all__']

    def test_user_delete_get_ajax_data(self):
        """Test that GET request with AJAX on user_delete returns user details."""
        delete_url = reverse('dashboard:user_delete', args=[self.staff_user.pk])
        response = self.client.get(
            delete_url,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['username'] == 'staffone'

    def test_user_delete_ajax_success(self):
        """Test successful user deletion via AJAX POST/DELETE request."""
        delete_url = reverse('dashboard:user_delete', args=[self.staff_user.pk])
        response = self.client.post(
            delete_url,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        
        # Verify user is deleted from DB
        assert not User.objects.filter(pk=self.staff_user.pk).exists()
