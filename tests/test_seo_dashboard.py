import pytest
from unittest.mock import MagicMock, patch
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from apps.core.models import UserRole
from apps.seo.services.gsc_client import GSCClient, GSCAPIError
from apps.redirects.models import Redirect
from apps.seo.models import Page404Log

@pytest.fixture
def seo_admin_user():
    user = User.objects.create_user(
        username='seoadmin',
        email='seoadmin@test.com',
        password='password',
        is_staff=True
    )
    profile = user.profile
    profile.role = UserRole.SEO_ADMIN
    profile.save()
    return user

@pytest.mark.django_db
class TestSearchConsoleDashboard:

    @patch('apps.seo.services.gsc_client.GSCClient.is_connected')
    @patch('apps.seo.services.gsc_client.GSCClient.get_summary')
    @patch('apps.seo.services.gsc_client.GSCClient.get_bracketted_pages')
    @patch('apps.seo.services.gsc_client.GSCClient.get_top_queries')
    def test_search_console_view_success(
        self, mock_top_queries, mock_brackets, mock_summary, mock_connected,
        client, seo_admin_user
    ):
        mock_connected.return_value = True
        mock_summary.return_value = {"total_clicks": 100, "total_impressions": 1000, "avg_ctr": 10.0, "avg_position": 1.2, "days": 28, "is_stale": False}
        mock_brackets.return_value = {"winners": [], "quick_wins": [], "growth": [], "low_visibility": [], "weak": [], "broken": [], "is_stale": False}
        mock_top_queries.return_value = {"queries": [], "is_stale": False}

        client.force_login(seo_admin_user)
        url = reverse('dashboard:search_console')
        response = client.get(url)

        assert response.status_code == 200
        mock_connected.assert_called_once()
        mock_summary.assert_called_once_with(28)
        mock_brackets.assert_called_once_with(28)
        assert "gsc_connected" in response.context
        assert response.context["gsc_connected"] is True
        assert response.context["gsc_data_stale"] is False

    @patch('apps.seo.services.gsc_client.GSCClient.is_connected')
    @patch('apps.seo.services.gsc_client.GSCClient.get_summary')
    def test_search_console_view_exception_handling(self, mock_summary, mock_connected, client, seo_admin_user):
        mock_connected.return_value = True
        mock_summary.side_effect = Exception("API connection failed")

        client.force_login(seo_admin_user)
        url = reverse('dashboard:search_console')
        
        response = client.get(url)
        assert response.status_code == 200
        assert "gsc_error" in response.context
        assert "API connection failed" in response.context["gsc_error"]

    @patch('apps.seo.services.gsc_client.GSCClient.is_connected')
    @patch('apps.seo.services.gsc_client.GSCClient.get_cannibalized_keywords')
    def test_cannibalization_api_view(self, mock_cannibal, mock_connected, client, seo_admin_user):
        mock_connected.return_value = True
        mock_cannibal.return_value = {"keywords": [{"query": "test query", "pages": []}], "is_stale": False}

        client.force_login(seo_admin_user)
        url = reverse('dashboard:search_console_cannibalization_api')
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "keywords" in data
        assert len(data["keywords"]) == 1
        assert data["keywords"][0]["query"] == "test query"

    @patch('apps.seo.services.gsc_client.GSCClient._query')
    def test_gsc_client_decision_tree_brackets(self, mock_query):
        mock_query.side_effect = [
            [
                {"keys": ["https://sciencesgates.com/page-winner"], "clicks": 10, "impressions": 100, "position": 2.1, "ctr": 0.1},
                {"keys": ["https://sciencesgates.com/page-qw"], "clicks": 5, "impressions": 50, "position": 8.5, "ctr": 0.1},
                {"keys": ["https://sciencesgates.com/page-growth"], "clicks": 2, "impressions": 25, "position": 18.0, "ctr": 0.08},
                {"keys": ["https://sciencesgates.com/page-low"], "clicks": 1, "impressions": 20, "position": 35.2, "ctr": 0.05},
                {"keys": ["https://sciencesgates.com/page-weak"], "clicks": 0, "impressions": 5, "position": 12.0, "ctr": 0.0},
            ],
            [],
            []
        ]

        gsc = GSCClient()
        cache.clear()
        
        brackets = gsc.get_bracketted_pages(days=28)
        
        assert len(brackets["winners"]) == 1
        assert brackets["winners"][0]["path"] == "/page-winner"
        assert len(brackets["quick_wins"]) == 1
        assert brackets["quick_wins"][0]["path"] == "/page-qw"
        assert len(brackets["growth"]) == 1
        assert brackets["growth"][0]["path"] == "/page-growth"
        assert len(brackets["low_visibility"]) == 1
        assert brackets["low_visibility"][0]["path"] == "/page-low"
        assert len(brackets["weak"]) == 1
        assert brackets["weak"][0]["path"] == "/page-weak"
        assert brackets["is_stale"] is False

    @patch('apps.seo.services.gsc_client.GSCClient._query')
    def test_gsc_client_in_memory_broken_detection(self, mock_query):
        # We mock a GSC result returning a path starting with '/articles/'
        # but resolved to type='page' which indicates the Article was not found (404)
        mock_query.side_effect = [
            [
                {"keys": ["https://sciencesgates.com/articles/deleted-article/"], "clicks": 5, "impressions": 50, "position": 1.2, "ctr": 0.1},
            ],
            [],
            []
        ]

        gsc = GSCClient()
        cache.clear()
        brackets = gsc.get_bracketted_pages(days=28)
        
        assert len(brackets["winners"]) == 0
        assert len(brackets["broken"]) == 1
        assert brackets["broken"][0]["path"] == "/articles/deleted-article/"
        assert brackets["broken"][0]["is_gsc_error"] is True

    def test_redirect_url_normalization_rules(self):
        # Verify all rules specified by the user
        assert Redirect.normalize_path("https://sciencesgates.com/ijcmit/") == "/ijcmit/"
        assert Redirect.normalize_path("sciencesgates.com/ijcmit/") == "/ijcmit/"
        assert Redirect.normalize_path("/ijcmit/") == "/ijcmit/"
        assert Redirect.normalize_path("ijcmit/") == "/ijcmit/"
        assert Redirect.normalize_path("https://sciencesgates.com/path?query=val") == "/path?query=val"

    def test_redirect_create_ajax_api(self, client, seo_admin_user):
        # Create a Page404Log entry first
        log = Page404Log.objects.create(path="/ijcmit/", hits=5)
        
        client.force_login(seo_admin_user)
        url = reverse('dashboard:search_console_redirect_create_api')
        
        response = client.post(
            url, 
            data={"old_url": "https://sciencesgates.com/ijcmit/", "new_url": "/new-path/"},
            content_type="application/json"
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify Redirect model was created and normalized
        redirect_exists = Redirect.objects.filter(old_url="/ijcmit/", new_url="/new-path/").exists()
        assert redirect_exists is True
        
        # Verify Page404Log database record was deleted (all slash variations)
        assert Page404Log.objects.filter(path="/ijcmit/").exists() is False
        assert Page404Log.objects.filter(path="/ijcmit").exists() is False

    def test_ignore_404_ajax_api(self, client, seo_admin_user):
        # Create a Page404Log entry first
        log = Page404Log.objects.create(path="/broken-path/", hits=5)
        
        client.force_login(seo_admin_user)
        url = reverse('dashboard:search_console_404_ignore_api')
        
        response = client.post(
            url, 
            data={"path": "/broken-path/"},
            content_type="application/json"
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify the Page404Log record was marked as ignored
        log.refresh_from_db()
        assert log.is_ignored is True

    def test_redirects_list_view_context(self, client, seo_admin_user):
        client.force_login(seo_admin_user)
        url = reverse('dashboard:redirect_list')
        response = client.get(url)
        
        assert response.status_code == 200
        # Verify list context fixes (broken table fixes)
        assert "columns" in response.context
        assert len(response.context["columns"]) == 5
        keys = [col['key'] for col in response.context["columns"]]
        assert "is_active_label" in keys
        assert "is_active" not in keys
        assert response.context["edit_url_name"] == "dashboard:redirect_edit"
        assert response.context["delete_url_name"] == "dashboard:redirect_delete"

    @patch('apps.seo.services.gsc_client.GSCClient.is_connected')
    @patch('apps.seo.services.gsc_client.GSCClient.get_summary')
    @patch('apps.seo.services.gsc_client.GSCClient.get_bracketted_pages')
    @patch('apps.seo.services.gsc_client.GSCClient.get_top_queries')
    def test_search_console_view_404_limit_and_total_count(
        self, mock_top_queries, mock_brackets, mock_summary, mock_connected,
        client, seo_admin_user
    ):
        mock_connected.return_value = True
        mock_summary.return_value = {"total_clicks": 10, "total_impressions": 100, "avg_ctr": 10.0, "avg_position": 1.0, "days": 28, "is_stale": False}
        mock_brackets.return_value = {"winners": [], "quick_wins": [], "growth": [], "low_visibility": [], "weak": [], "broken": [], "is_stale": False}
        mock_top_queries.return_value = {"queries": [], "is_stale": False}

        # Create 60 Page404Log items with hits >= 10
        for i in range(60):
            Page404Log.objects.create(path=f"/broken-page-{i}/", hits=i + 10)

        client.force_login(seo_admin_user)
        url = reverse('dashboard:search_console')
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["total_broken_count"] == 60
        assert len(response.context["bracketted_pages"]["broken"]) == 50
        # Assert highest hits comes first
        assert response.context["bracketted_pages"]["broken"][0]["clicks"] == 69

    @patch('apps.seo.services.gsc_client.GSCClient.is_connected')
    @patch('apps.seo.services.gsc_client.GSCClient.get_summary')
    @patch('apps.seo.services.gsc_client.GSCClient.get_bracketted_pages')
    @patch('apps.seo.services.gsc_client.GSCClient.get_top_queries')
    def test_search_console_view_404_date_range_filter(
        self, mock_top_queries, mock_brackets, mock_summary, mock_connected,
        client, seo_admin_user
    ):
        from django.utils import timezone
        from datetime import timedelta

        mock_connected.return_value = True
        mock_summary.return_value = {"total_clicks": 0, "total_impressions": 0, "avg_ctr": 0, "avg_position": 0, "days": 7, "is_stale": False}
        mock_brackets.return_value = {"winners": [], "quick_wins": [], "growth": [], "low_visibility": [], "weak": [], "broken": [], "is_stale": False}
        mock_top_queries.return_value = {"queries": [], "is_stale": False}

        recent_date = (timezone.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        old_date = (timezone.now() - timedelta(days=20)).strftime('%Y-%m-%d')

        # Create 1 recent 404 (2 days ago) and 1 old 404 (20 days ago), both hits >= 10
        recent = Page404Log.objects.create(path="/recent-404/", hits=15, daily_hits={recent_date: 15})
        old = Page404Log.objects.create(path="/old-404/", hits=12, daily_hits={old_date: 12})
        Page404Log.objects.filter(pk=old.pk).update(last_hit=timezone.now() - timedelta(days=20))

        client.force_login(seo_admin_user)
        
        # When querying with days=7, only recent should appear
        resp_7 = client.get(reverse('dashboard:search_console') + "?days=7")
        assert resp_7.status_code == 200
        assert resp_7.context["total_broken_count"] == 1
        assert resp_7.context["bracketted_pages"]["broken"][0]["path"] == "/recent-404/"
        assert resp_7.context["bracketted_pages"]["broken"][0]["clicks"] == 15

        # When querying with days=28, both should appear, sorted descending (15, 12)
        mock_summary.return_value["days"] = 28
        resp_28 = client.get(reverse('dashboard:search_console') + "?days=28")
        assert resp_28.status_code == 200
        assert resp_28.context["total_broken_count"] == 2
        assert resp_28.context["bracketted_pages"]["broken"][0]["clicks"] == 15
        assert resp_28.context["bracketted_pages"]["broken"][1]["clicks"] == 12

    @patch('apps.seo.services.gsc_client.GSCClient.is_connected')
    @patch('apps.seo.services.gsc_client.GSCClient.get_summary')
    @patch('apps.seo.services.gsc_client.GSCClient.get_bracketted_pages')
    @patch('apps.seo.services.gsc_client.GSCClient.get_top_queries')
    def test_search_console_view_404_min_10_hits_filter(
        self, mock_top_queries, mock_brackets, mock_summary, mock_connected,
        client, seo_admin_user
    ):
        from django.utils import timezone
        today_str = timezone.now().strftime('%Y-%m-%d')

        mock_connected.return_value = True
        mock_summary.return_value = {"total_clicks": 0, "total_impressions": 0, "avg_ctr": 0, "avg_position": 0, "days": 28, "is_stale": False}
        mock_brackets.return_value = {"winners": [], "quick_wins": [], "growth": [], "low_visibility": [], "weak": [], "broken": [], "is_stale": False}
        mock_top_queries.return_value = {"queries": [], "is_stale": False}

        # Page with 10 hits (should qualify)
        Page404Log.objects.create(path="/qualified-404/", hits=10, daily_hits={today_str: 10})
        # Page with 9 hits (should be excluded)
        Page404Log.objects.create(path="/low-hits-404/", hits=9, daily_hits={today_str: 9})

        client.force_login(seo_admin_user)
        resp = client.get(reverse('dashboard:search_console'))
        assert resp.status_code == 200
        assert resp.context["total_broken_count"] == 1
        assert resp.context["bracketted_pages"]["broken"][0]["path"] == "/qualified-404/"
        assert resp.context["bracketted_pages"]["broken"][0]["clicks"] == 10

    @patch('apps.seo.services.gsc_client.GSCClient.is_connected')
    @patch('apps.seo.services.gsc_client.GSCClient.get_summary')
    @patch('apps.seo.services.gsc_client.GSCClient.get_bracketted_pages')
    @patch('apps.seo.services.gsc_client.GSCClient.get_top_queries')
    def test_search_console_view_404_sorted_descending(
        self, mock_top_queries, mock_brackets, mock_summary, mock_connected,
        client, seo_admin_user
    ):
        from django.utils import timezone
        today_str = timezone.now().strftime('%Y-%m-%d')

        mock_connected.return_value = True
        mock_summary.return_value = {"total_clicks": 0, "total_impressions": 0, "avg_ctr": 0, "avg_position": 0, "days": 7, "is_stale": False}
        mock_brackets.return_value = {"winners": [], "quick_wins": [], "growth": [], "low_visibility": [], "weak": [], "broken": [], "is_stale": False}
        mock_top_queries.return_value = {"queries": [], "is_stale": False}

        Page404Log.objects.create(path="/medium-404/", hits=20, daily_hits={today_str: 20})
        Page404Log.objects.create(path="/highest-404/", hits=50, daily_hits={today_str: 50})
        Page404Log.objects.create(path="/lowest-404/", hits=10, daily_hits={today_str: 10})

        client.force_login(seo_admin_user)
        resp = client.get(reverse('dashboard:search_console') + "?days=7")
        assert resp.status_code == 200
        broken = resp.context["bracketted_pages"]["broken"]
        assert len(broken) == 3
        # Assert strict descending order (50, 20, 10)
        assert broken[0]["path"] == "/highest-404/"
        assert broken[0]["clicks"] == 50
        assert broken[1]["path"] == "/medium-404/"
        assert broken[1]["clicks"] == 20
        assert broken[2]["path"] == "/lowest-404/"
        assert broken[2]["clicks"] == 10
