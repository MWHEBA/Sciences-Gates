import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.core.models import UserProfile, UserRole
from apps.redirects.models import Redirect

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestRedirectLoopsPrevention:
    """Automated verification for redirect loop prevention and authentication hardening."""

    def test_anonymous_user_can_access_login_page(self, client):
        """Anonymous user gets 200 OK on login page with next param without any redirect loop."""
        url = f"{reverse('dashboard:login')}?next=/sg/"
        response = client.get(url)
        assert response.status_code == 200
        assert 'dashboard/login.html' in [t.name for t in response.templates]

    def test_staff_user_without_profile_login_page_no_loop(self, client):
        """
        Staff user without a UserProfile accessing login page gets session cleared
        and receives 200 OK (login form) rather than bouncing to /sg/ in a loop.
        """
        user = User.objects.create_user(username='orphan_staff', password='Password123', is_staff=True)
        # Ensure no UserProfile exists
        UserProfile.objects.filter(user=user).delete()

        client.login(username='orphan_staff', password='Password123')
        
        # When accessing /sg/login/?next=/sg/
        url = f"{reverse('dashboard:login')}?next=/sg/"
        response = client.get(url)
        # Must return 200 OK (login form), session flushed, no loop
        assert response.status_code == 200
        assert 'dashboard/login.html' in [t.name for t in response.templates]

    def test_staff_user_without_profile_accessing_dashboard_follow_redirects(self, client):
        """
        Staff user without a UserProfile accessing /sg/ with follow=True lands on login page cleanly.
        """
        user = User.objects.create_user(username='orphan_staff_dash', password='Password123', is_staff=True)
        UserProfile.objects.filter(user=user).delete()

        client.login(username='orphan_staff_dash', password='Password123')
        
        response = client.get(reverse('dashboard:home'), follow=True)
        # Should cleanly land on login page with 200 OK without redirect cycle
        assert response.status_code == 200
        assert len(response.redirect_chain) <= 2
        assert 'dashboard/login.html' in [t.name for t in response.templates]

    def test_login_post_auto_heals_missing_profile(self, client):
        """
        Staff user logging in via POST automatically gets a UserProfile created and accesses dashboard.
        """
        user = User.objects.create_user(username='auto_heal_staff', password='Password123', is_staff=True)
        UserProfile.objects.filter(user=user).delete()
        assert not UserProfile.objects.filter(user=user).exists()

        url = reverse('dashboard:login')
        response = client.post(url, {'username': 'auto_heal_staff', 'password': 'Password123'}, follow=True)
        
        assert response.status_code == 200
        # Profile was auto-healed
        assert UserProfile.objects.filter(user=user).exists()
        assert 'dashboard/home.html' in [t.name for t in response.templates]

    def test_role_mismatch_redirects_to_home_not_login(self, client):
        """
        An authenticated SEO Admin accessing Content Admin page is redirected to dashboard:home,
        NEVER to dashboard:login (preventing Role Mismatch Loops).
        """
        seo_user = User.objects.create_user(username='seo_user', password='Password123', is_staff=True)
        profile, _ = UserProfile.objects.get_or_create(user=seo_user)
        profile.role = UserRole.SEO_ADMIN
        profile.save()

        client.login(username='seo_user', password='Password123')

        # SEO admin accessing university list (Content Admin only)
        response = client.get(reverse('dashboard:university_list'))
        assert response.status_code == 302
        assert response.url == reverse('dashboard:home')
        assert 'login' not in response.url

    def test_redirect_middleware_ignores_dashboard_paths(self, client):
        """
        RedirectMiddleware must not redirect /sg/ or /sg/login/ even if a database redirect exists.
        """
        Redirect.objects.create(
            old_url='/sg/login/',
            new_url='/somewhere-else/',
            is_active=True
        )
        Redirect.objects.create(
            old_url='/sg/',
            new_url='/somewhere-else/',
            is_active=True
        )

        login_url = reverse('dashboard:login')
        response = client.get(login_url)
        # Should NOT be 301 redirected to /somewhere-else/
        assert response.status_code == 200
        assert 'dashboard/login.html' in [t.name for t in response.templates]

    def test_unauthenticated_api_request_returns_401_json(self, client):
        """
        Unauthenticated AJAX / API requests return 401 JSON rather than 302 HTML redirect.
        """
        api_url = reverse('dashboard:api_tags_create')
        response = client.post(api_url, {'name': 'New Tag'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert response.status_code == 401
        assert response.json().get('authenticated') is False

    def test_sanitizes_self_referencing_next_param(self, client):
        """
        Login view strips next param if it points back to login view or contains loops.
        """
        user = User.objects.create_user(username='clean_staff', password='Password123', is_staff=True)
        UserProfile.objects.get_or_create(user=user)

        login_url = reverse('dashboard:login')
        # Attempting self-referencing next parameter
        response = client.post(f"{login_url}?next={login_url}", {
            'username': 'clean_staff',
            'password': 'Password123'
        })
        # Should redirect to dashboard:home instead of login
        assert response.status_code == 302
        assert response.url == reverse('dashboard:home')
