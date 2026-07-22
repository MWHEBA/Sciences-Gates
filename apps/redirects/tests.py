"""
Tests for Redirect model and middleware.
"""
from django.test import TestCase, RequestFactory
from django.http import HttpResponsePermanentRedirect
from apps.redirects.models import Redirect


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

    def test_middleware_redirects_with_and_without_trailing_slash(self):
        """Test that middleware matches path with or without trailing slash."""
        # 1. Test slushed request for unslushed old_url
        request_with_slash = self.factory.get('/old-university/')
        response = self.middleware.process_request(request_with_slash)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, '/universities/new-university')

        # 2. Create slushed old_url and test unslushed request
        from .models import Redirect
        Redirect.objects.create(
            old_url='/slashed-path/',
            new_url='/target-path',
            is_active=True
        )
        request_without_slash = self.factory.get('/slashed-path')
        response = self.middleware.process_request(request_without_slash)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, '/target-path')

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


import pytest
from apps.universities.models import University
from apps.articles.models import Article

@pytest.mark.django_db
class TestAutomaticRedirectSignals:
    """Test automatic redirect creation via Django signals."""

    def test_auto_redirect_on_published_slug_change(self):
        """Test that changing slug of a published item automatically creates a Redirect."""
        # 1. Create a published university
        uni = University.objects.create(
            name="الجامعة الوطنية",
            slug="national-uni",
            publish_status="published"
        )
        # Verify no redirect exists yet
        assert not Redirect.objects.filter(old_url="/universities/national-uni/").exists()

        # 2. Change slug
        uni.slug = "new-national-uni"
        uni.save()

        # Verify redirect was automatically created
        redirect = Redirect.objects.filter(old_url="/universities/national-uni/").first()
        assert redirect is not None
        assert redirect.new_url == "/universities/new-national-uni/"
        assert redirect.is_active

    def test_no_redirect_on_draft_slug_change(self):
        """Test that changing slug of a draft item does NOT create a Redirect."""
        uni = University.objects.create(
            name="جامعة مسودة",
            slug="draft-uni",
            publish_status="draft"
        )
        uni.slug = "new-draft-uni"
        uni.save()

        assert not Redirect.objects.filter(old_url="/universities/draft-uni/").exists()

    def test_chain_redirect_resolution(self):
        """Test chain redirect resolving (A -> B, then B -> C updates to A -> C)."""
        uni = University.objects.create(
            name="جامعة السلسلة",
            slug="uni-a",
            publish_status="published"
        )
        
        # Change slug A -> B
        uni.slug = "uni-b"
        uni.save()
        assert Redirect.objects.filter(old_url="/universities/uni-a/", new_url="/universities/uni-b/").exists()

        # Change slug B -> C
        uni.slug = "uni-c"
        uni.save()

        # Verify A -> B was updated to A -> C
        assert Redirect.objects.filter(old_url="/universities/uni-a/", new_url="/universities/uni-c/").exists()
        # Verify B -> C also exists
        assert Redirect.objects.filter(old_url="/universities/uni-b/", new_url="/universities/uni-c/").exists()

    def test_circular_redirect_loop_prevention(self):
        """Test circular redirect protection (A -> B, then B -> A deletes the reverse redirect)."""
        uni = University.objects.create(
            name="جامعة الحلقات",
            slug="uni-x",
            publish_status="published"
        )
        
        # Change slug X -> Y (Creates X -> Y redirect)
        uni.slug = "uni-y"
        uni.save()
        assert Redirect.objects.filter(old_url="/universities/uni-x/", new_url="/universities/uni-y/").exists()

        # Change slug Y -> X (Should delete X -> Y redirect and create Y -> X)
        uni.slug = "uni-x"
        uni.save()

        assert not Redirect.objects.filter(old_url="/universities/uni-x/", new_url="/universities/uni-y/").exists()
        assert Redirect.objects.filter(old_url="/universities/uni-y/", new_url="/universities/uni-x/").exists()


@pytest.mark.django_db
class TestSEOMixinDuplicateMetaTitleValidation:
    """Test the clean() validation rule for duplicate meta titles in SEOMixin."""

    def test_duplicate_meta_title_on_different_published_items(self):
        """Test that saving two published items with the same meta_title raises ValidationError."""
        from django.core.exceptions import ValidationError

        # Create first published university
        University.objects.create(
            name="الجامعة الأولى",
            slug="uni-1",
            meta_title="دراسة الهندسة في ماليزيا",
            publish_status="published"
        )

        # Try to create second published university with same meta_title
        uni2 = University(
            name="الجامعة الثانية",
            slug="uni-2",
            meta_title="دراسة الهندسة في ماليزيا",
            publish_status="published"
        )

        with pytest.raises(ValidationError) as exc_info:
            uni2.clean()
        
        assert "meta_title" in exc_info.value.message_dict
        assert "عنوان SEO هذا مستخدم بالفعل" in exc_info.value.message_dict["meta_title"][0]

    def test_duplicate_meta_title_allowed_on_drafts(self):
        """Test that duplicate meta_titles are allowed if one of them is a draft."""
        # Create published university
        University.objects.create(
            name="الجامعة الأولى",
            slug="uni-1",
            meta_title="دراسة الطب في ماليزيا",
            publish_status="published"
        )

        # Create draft university with same meta_title (should pass clean)
        uni2 = University(
            name="الجامعة الثانية",
            slug="uni-2",
            meta_title="دراسة الطب في ماليزيا",
            publish_status="unpublished"
        )
        # Should not raise any validation error
        uni2.clean()
        uni2.save()
        assert uni2.pk is not None
