"""
Tests for Redirect model and middleware.
"""
from django.test import TestCase, RequestFactory
from django.http import HttpResponsePermanentRedirect


class RedirectModelTests(TestCase):
    """Tests for the Redirect model."""

    def setUp(self):
        """Set up test data."""
        from .models import Redirect
        
        self.redirect = Redirect.objects.create(
            old_url='/old-university/engineering',
            new_url='/universities/engineering',
            is_active=True,
            notes='University slug changed'
        )

    def test_redirect_creation(self):
        """Test that a redirect can be created."""
        self.assertEqual(self.redirect.old_url, '/old-university/engineering')
        self.assertEqual(self.redirect.new_url, '/universities/engineering')
        self.assertTrue(self.redirect.is_active)
        self.assertEqual(self.redirect.hit_count, 0)

    def test_redirect_string_representation(self):
        """Test the string representation of a redirect."""
        expected = '/old-university/engineering → /universities/engineering'
        self.assertEqual(str(self.redirect), expected)

    def test_increment_hit_count(self):
        """Test that hit count increments correctly."""
        self.assertEqual(self.redirect.hit_count, 0)
        self.redirect.increment_hit_count()
        self.redirect.refresh_from_db()
        self.assertEqual(self.redirect.hit_count, 1)
        
        self.redirect.increment_hit_count()
        self.redirect.refresh_from_db()
        self.assertEqual(self.redirect.hit_count, 2)

    def test_inactive_redirect(self):
        """Test that inactive redirects are stored correctly."""
        inactive_redirect = Redirect.objects.create(
            old_url='/old-path',
            new_url='/new-path',
            is_active=False
        )
        self.assertFalse(inactive_redirect.is_active)

    def test_redirect_with_notes(self):
        """Test that notes are stored correctly."""
        redirect_with_notes = Redirect.objects.create(
            old_url='/old',
            new_url='/new',
            notes='This is a test redirect'
        )
        self.assertEqual(redirect_with_notes.notes, 'This is a test redirect')

    def test_redirect_timestamps(self):
        """Test that timestamps are set correctly."""
        self.assertIsNotNone(self.redirect.created_at)
        self.assertIsNotNone(self.redirect.updated_at)


class RedirectMiddlewareTests(TestCase):
    """Tests for the RedirectMiddleware."""

    def setUp(self):
        """Set up test data and middleware."""
        from .models import Redirect
        from .middleware import RedirectMiddleware
        
        self.factory = RequestFactory()
        self.middleware = RedirectMiddleware(lambda r: None)
        
        # Create test redirects
        self.active_redirect = Redirect.objects.create(
            old_url='/old-university',
            new_url='/universities/new-university',
            is_active=True
        )
        
        self.inactive_redirect = Redirect.objects.create(
            old_url='/inactive-path',
            new_url='/new-path',
            is_active=False
        )

    def test_middleware_redirects_active_url(self):
        """Test that middleware redirects active URLs."""
        request = self.factory.get('/old-university')
        response = self.middleware.process_request(request)
        
        self.assertIsNotNone(response)
        self.assertIsInstance(response, HttpResponsePermanentRedirect)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, '/universities/new-university')

    def test_middleware_increments_hit_count(self):
        """Test that middleware increments hit count on redirect."""
        self.assertEqual(self.active_redirect.hit_count, 0)
        
        request = self.factory.get('/old-university')
        self.middleware.process_request(request)
        
        self.active_redirect.refresh_from_db()
        self.assertEqual(self.active_redirect.hit_count, 1)

    def test_middleware_ignores_inactive_redirects(self):
        """Test that middleware ignores inactive redirects."""
        request = self.factory.get('/inactive-path')
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)
        self.inactive_redirect.refresh_from_db()
        self.assertEqual(self.inactive_redirect.hit_count, 0)

    def test_middleware_returns_none_for_non_matching_url(self):
        """Test that middleware returns None for non-matching URLs."""
        request = self.factory.get('/non-existent-path')
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)

    def test_middleware_with_query_string(self):
        """Test that middleware matches path without query string."""
        request = self.factory.get('/old-university?param=value')
        response = self.middleware.process_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 301)

    def test_multiple_redirects_same_old_url(self):
        """Test behavior when multiple redirects have the same old_url."""
        # Create another active redirect with same old_url
        Redirect.objects.create(
            old_url='/old-university',
            new_url='/different-new-url',
            is_active=True
        )
        
        request = self.factory.get('/old-university')
        # Should get one of them (first in database order)
        response = self.middleware.process_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 301)
