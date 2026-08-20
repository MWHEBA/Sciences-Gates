import pytest
import json
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
from apps.core.models import ContentLock
from apps.universities.models import University

@pytest.fixture
def test_user(db):
    return User.objects.create_user(username='admin1', email='admin1@test.com', password='password')

@pytest.fixture
def other_user(db):
    return User.objects.create_user(username='admin2', email='admin2@test.com', password='password')

@pytest.fixture
def university(db):
    return University.objects.create(
        name='Test University',
        slug='test-university',
        university_type='private',
        state='kl',
        city='kl',
        logo='test.png',
        main_image='test.png',
        description='Test description',
        location='Kuala Lumpur',
    )

@pytest.mark.django_db
class TestContentLocking:
    
    def test_acquire_lock_success(self, client, test_user, university):
        client.force_login(test_user)
        url = reverse('dashboard:api_locks')
        
        response = client.post(
            url,
            data=json.dumps({
                'action': 'acquire',
                'model': 'university',
                'object_id': university.id,
                'client_token': 'token_123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['locked'] is True
        assert data['owned'] is True
        
        # Verify db entry
        lock = ContentLock.objects.get(object_id=university.id)
        assert lock.user == test_user
        assert lock.client_token == 'token_123'

    def test_acquire_lock_already_locked_by_other(self, client, test_user, other_user, university):
        # Create lock for other_user
        ct = ContentType.objects.get_for_model(University)
        ContentLock.objects.create(
            content_type=ct,
            object_id=university.id,
            user=other_user,
            client_token='other_token',
            expires_at=timezone.now() + timedelta(minutes=2)
        )
        
        client.force_login(test_user)
        url = reverse('dashboard:api_locks')
        
        response = client.post(
            url,
            data=json.dumps({
                'action': 'acquire',
                'model': 'university',
                'object_id': university.id,
                'client_token': 'my_token'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'locked'
        assert data['locked_by'] == (other_user.get_full_name() or other_user.username)
        assert data['is_same_user'] is False

    def test_multi_tab_same_user_collision(self, client, test_user, university):
        # User has lock in Tab 1
        ct = ContentType.objects.get_for_model(University)
        ContentLock.objects.create(
            content_type=ct,
            object_id=university.id,
            user=test_user,
            client_token='tab_1_token',
            expires_at=timezone.now() + timedelta(minutes=2)
        )
        
        client.force_login(test_user)
        url = reverse('dashboard:api_locks')
        
        # Try to acquire from Tab 2
        response = client.post(
            url,
            data=json.dumps({
                'action': 'acquire',
                'model': 'university',
                'object_id': university.id,
                'client_token': 'tab_2_token'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'locked'
        assert data['is_same_user'] is True

    def test_refresh_lock_success(self, client, test_user, university):
        ct = ContentType.objects.get_for_model(University)
        lock = ContentLock.objects.create(
            content_type=ct,
            object_id=university.id,
            user=test_user,
            client_token='token_123',
            expires_at=timezone.now() + timedelta(seconds=10)
        )
        
        client.force_login(test_user)
        url = reverse('dashboard:api_locks')
        
        response = client.post(
            url,
            data=json.dumps({
                'action': 'refresh',
                'model': 'university',
                'object_id': university.id,
                'client_token': 'token_123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['refreshed'] is True
        
        # Check that expiration is extended
        lock.refresh_from_db()
        assert lock.expires_at > timezone.now() + timedelta(seconds=60)

    def test_release_lock_success(self, client, test_user, university):
        ct = ContentType.objects.get_for_model(University)
        ContentLock.objects.create(
            content_type=ct,
            object_id=university.id,
            user=test_user,
            client_token='token_123',
            expires_at=timezone.now() + timedelta(minutes=2)
        )
        
        client.force_login(test_user)
        url = reverse('dashboard:api_locks')
        
        response = client.post(
            url,
            data=json.dumps({
                'action': 'release',
                'model': 'university',
                'object_id': university.id,
                'client_token': 'token_123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        assert response.json()['status'] == 'success'
        assert ContentLock.objects.filter(object_id=university.id).exists() is False

    def test_post_mixin_re_renders_form(self, client, test_user, other_user, university):
        # Create lock for other_user
        ct = ContentType.objects.get_for_model(University)
        ContentLock.objects.create(
            content_type=ct,
            object_id=university.id,
            user=other_user,
            client_token='other_token',
            expires_at=timezone.now() + timedelta(minutes=2)
        )
        
        # Login as test_user (with content admin access)
        test_user.is_staff = True
        test_user.save()
        
        profile = test_user.profile
        profile.role = 'content_admin'
        profile.save()
        
        client.force_login(test_user)
        
        # Try to post university edit
        url = reverse('dashboard:university_edit', args=[university.id])
        response = client.post(url, data={
            'name': 'Updated University Name',
            'slug': 'test-university',
            'university_type': 'private',
            'state': 'kuala_lumpur',
            'city': 'kuala_lumpur'
        })
        
        # Verify it re-renders the form (returns 200) instead of redirecting
        assert response.status_code == 200
        assert 'لا يمكن حفظ التغييرات' in response.content.decode('utf-8')
        
        # Verify the database entry was NOT updated
        university.refresh_from_db()
        assert university.name == 'Test University'

    def test_force_takeover_success_higher_role(self, client, test_user, other_user, university):
        # other_user (Content Admin) has lock
        other_user.is_staff = True
        other_user.save()
        other_user.profile.role = 'content_admin'
        other_user.profile.save()
        
        ct = ContentType.objects.get_for_model(University)
        ContentLock.objects.create(
            content_type=ct,
            object_id=university.id,
            user=other_user,
            client_token='other_token',
            expires_at=timezone.now() + timedelta(minutes=2)
        )
        
        # test_user (Super Admin) wants to kick other_user
        test_user.is_staff = True
        test_user.save()
        test_user.profile.role = 'super_admin'
        test_user.profile.save()
        
        client.force_login(test_user)
        url = reverse('dashboard:api_locks')
        
        response = client.post(
            url,
            data=json.dumps({
                'action': 'acquire',
                'model': 'university',
                'object_id': university.id,
                'client_token': 'super_token',
                'force': True
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['kicked_previous'] is True
        
        # Verify lock was updated
        lock = ContentLock.objects.get(object_id=university.id)
        assert lock.user == test_user
        assert lock.client_token == 'super_token'

    def test_force_takeover_failure_lower_role(self, client, test_user, other_user, university):
        # other_user (Super Admin) has lock
        other_user.is_staff = True
        other_user.save()
        other_user.profile.role = 'super_admin'
        other_user.profile.save()
        
        ct = ContentType.objects.get_for_model(University)
        ContentLock.objects.create(
            content_type=ct,
            object_id=university.id,
            user=other_user,
            client_token='super_token',
            expires_at=timezone.now() + timedelta(minutes=2)
        )
        
        # test_user (Content Admin) tries to kick other_user
        test_user.is_staff = True
        test_user.save()
        test_user.profile.role = 'content_admin'
        test_user.profile.save()
        
        client.force_login(test_user)
        url = reverse('dashboard:api_locks')
        
        response = client.post(
            url,
            data=json.dumps({
                'action': 'acquire',
                'model': 'university',
                'object_id': university.id,
                'client_token': 'my_token',
                'force': True
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data['status'] == 'insufficient_privileges'

    def test_heartbeat_kicked_state(self, client, test_user, other_user, university):
        # test_user has lock in Tab 1
        ct = ContentType.objects.get_for_model(University)
        lock = ContentLock.objects.create(
            content_type=ct,
            object_id=university.id,
            user=test_user,
            client_token='tab_1_token',
            expires_at=timezone.now() + timedelta(minutes=2)
        )
        
        # other_user (Super Admin) takes over lock
        other_user.is_staff = True
        other_user.save()
        other_user.profile.role = 'super_admin'
        other_user.profile.save()
        
        lock.user = other_user
        lock.client_token = 'other_token'
        lock.save()
        
        # test_user sends heartbeat check from Tab 1
        client.force_login(test_user)
        url = reverse('dashboard:api_locks')
        
        response = client.post(
            url,
            data=json.dumps({
                'action': 'refresh',
                'model': 'university',
                'object_id': university.id,
                'client_token': 'tab_1_token'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'kicked'
        assert data['locked_by'] == (other_user.get_full_name() or other_user.username)

