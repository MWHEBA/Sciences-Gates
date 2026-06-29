import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from apps.core.models import UserRole
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article, Category


@pytest.mark.django_db
class TestBulkActions:
    """Tests for dashboard bulk action views."""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Set up test client and users with different roles."""
        self.client = client
        
        # Create a content admin user
        self.content_admin = User.objects.create_user(
            username='contentadmin',
            password='testpass123',
            is_staff=True
        )
        self.content_admin.profile.role = UserRole.CONTENT_ADMIN
        self.content_admin.profile.save()
        
        # Create a non-staff user for authorization check
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='testpass123',
            is_staff=False
        )
        self.regular_user.profile.role = UserRole.SEO_ADMIN
        self.regular_user.profile.save()

    def test_bulk_actions_require_content_admin(self):
        """Test that non-staff or regular users are redirected/blocked."""
        url = reverse('dashboard:university_bulk_action')
        
        # Unauthenticated redirects to login
        response = self.client.post(url, {'action': 'delete', 'selected_ids': [1]})
        assert response.status_code == 302
        assert 'login' in response.url
        
        # Regular user gets 403 Forbidden
        self.client.login(username='regularuser', password='testpass123')
        response = self.client.post(url, {'action': 'delete', 'selected_ids': [1]})
        assert response.status_code == 403

    def test_bulk_actions_warning_if_no_ids(self):
        """Test warning messages and redirection if no ids are selected."""
        self.client.login(username='contentadmin', password='testpass123')
        
        entities = [
            ('dashboard:university_bulk_action', 'dashboard:university_list'),
            ('dashboard:institute_bulk_action', 'dashboard:institute_list'),
            ('dashboard:major_bulk_action', 'dashboard:major_list'),
            ('dashboard:article_bulk_action', 'dashboard:article_list'),
        ]
        
        for url_name, list_url_name in entities:
            url = reverse(url_name)
            list_url = reverse(list_url_name)
            response = self.client.post(url, {'action': 'delete', 'selected_ids': []})
            assert response.status_code == 302
            assert response.url == list_url

    def test_university_bulk_actions(self):
        """Test bulk publish, unpublish, and delete on Universities."""
        self.client.login(username='contentadmin', password='testpass123')
        
        # Create test universities
        u1 = University.objects.create(
            name='University 1',
            slug='uni-1',
            logo='test.png',
            main_image='test.png',
            description='Test 1',
            publish_status='unpublished'
        )
        u2 = University.objects.create(
            name='University 2',
            slug='uni-2',
            logo='test.png',
            main_image='test.png',
            description='Test 2',
            publish_status='unpublished'
        )
        
        url = reverse('dashboard:university_bulk_action')
        
        # Bulk Publish
        response = self.client.post(url, {
            'action': 'publish',
            'selected_ids': [u1.id, u2.id]
        })
        assert response.status_code == 302
        assert response.url == reverse('dashboard:university_list')
        
        u1.refresh_from_db()
        u2.refresh_from_db()
        assert u1.publish_status == 'published'
        assert u2.publish_status == 'published'
        
        # Bulk Unpublish
        response = self.client.post(url, {
            'action': 'unpublish',
            'selected_ids': [u1.id, u2.id]
        })
        assert response.status_code == 302
        
        u1.refresh_from_db()
        u2.refresh_from_db()
        assert u1.publish_status == 'unpublished'
        assert u2.publish_status == 'unpublished'
        
        # Bulk Delete
        response = self.client.post(url, {
            'action': 'delete',
            'selected_ids': [u1.id, u2.id]
        })
        assert response.status_code == 302
        assert not University.objects.filter(id__in=[u1.id, u2.id]).exists()

    def test_institute_bulk_actions(self):
        """Test bulk publish, unpublish, and delete on Institutes."""
        self.client.login(username='contentadmin', password='testpass123')
        
        # Create test institutes
        i1 = Institute.objects.create(
            name='Institute 1',
            slug='inst-1',
            main_image='test.jpg',
            description='Test 1',
            publish_status='unpublished'
        )
        i2 = Institute.objects.create(
            name='Institute 2',
            slug='inst-2',
            main_image='test.jpg',
            description='Test 2',
            publish_status='unpublished'
        )
        
        url = reverse('dashboard:institute_bulk_action')
        
        # Bulk Publish
        response = self.client.post(url, {
            'action': 'publish',
            'selected_ids': [i1.id, i2.id]
        })
        assert response.status_code == 302
        
        i1.refresh_from_db()
        i2.refresh_from_db()
        assert i1.publish_status == 'published'
        assert i2.publish_status == 'published'
        
        # Bulk Unpublish
        response = self.client.post(url, {
            'action': 'unpublish',
            'selected_ids': [i1.id, i2.id]
        })
        assert response.status_code == 302
        
        i1.refresh_from_db()
        i2.refresh_from_db()
        assert i1.publish_status == 'unpublished'
        assert i2.publish_status == 'unpublished'
        
        # Bulk Delete
        response = self.client.post(url, {
            'action': 'delete',
            'selected_ids': [i1.id, i2.id]
        })
        assert response.status_code == 302
        assert not Institute.objects.filter(id__in=[i1.id, i2.id]).exists()

    def test_major_bulk_actions(self):
        """Test bulk publish, unpublish, and delete on Majors."""
        self.client.login(username='contentadmin', password='testpass123')
        
        # Create test majors
        m1 = Major.objects.create(
            name='Major 1',
            slug='major-1',
            description='Test 1',
            study_duration='4 years',
            publish_status='unpublished'
        )
        m2 = Major.objects.create(
            name='Major 2',
            slug='major-2',
            description='Test 2',
            study_duration='4 years',
            publish_status='unpublished'
        )
        
        url = reverse('dashboard:major_bulk_action')
        
        # Bulk Publish
        response = self.client.post(url, {
            'action': 'publish',
            'selected_ids': [m1.id, m2.id]
        })
        assert response.status_code == 302
        
        m1.refresh_from_db()
        m2.refresh_from_db()
        assert m1.publish_status == 'published'
        assert m2.publish_status == 'published'
        
        # Bulk Unpublish
        response = self.client.post(url, {
            'action': 'unpublish',
            'selected_ids': [m1.id, m2.id]
        })
        assert response.status_code == 302
        
        m1.refresh_from_db()
        m2.refresh_from_db()
        assert m1.publish_status == 'unpublished'
        assert m2.publish_status == 'unpublished'
        
        # Bulk Delete
        response = self.client.post(url, {
            'action': 'delete',
            'selected_ids': [m1.id, m2.id]
        })
        assert response.status_code == 302
        assert not Major.objects.filter(id__in=[m1.id, m2.id]).exists()

    def test_article_bulk_actions(self):
        """Test bulk publish, unpublish, and delete on Articles."""
        self.client.login(username='contentadmin', password='testpass123')
        
        # Create category and articles
        cat = Category.objects.create(name='Category 1', slug='cat-1')
        a1 = Article.objects.create(
            title='Article 1',
            slug='art-1',
            featured_image='articles/test.jpg',
            content='Content 1',
            category=cat,
            author=self.content_admin,
            publish_status='unpublished'
        )
        a2 = Article.objects.create(
            title='Article 2',
            slug='art-2',
            featured_image='articles/test.jpg',
            content='Content 2',
            category=cat,
            author=self.content_admin,
            publish_status='unpublished'
        )
        
        url = reverse('dashboard:article_bulk_action')
        
        # Bulk Publish
        response = self.client.post(url, {
            'action': 'publish',
            'selected_ids': [a1.id, a2.id]
        })
        assert response.status_code == 302
        
        a1.refresh_from_db()
        a2.refresh_from_db()
        assert a1.publish_status == 'published'
        assert a2.publish_status == 'published'
        
        # Bulk Unpublish
        response = self.client.post(url, {
            'action': 'unpublish',
            'selected_ids': [a1.id, a2.id]
        })
        assert response.status_code == 302
        
        a1.refresh_from_db()
        a2.refresh_from_db()
        assert a1.publish_status == 'unpublished'
        assert a2.publish_status == 'unpublished'
        
        # Bulk Delete
        response = self.client.post(url, {
            'action': 'delete',
            'selected_ids': [a1.id, a2.id]
        })
        assert response.status_code == 302
        assert not Article.objects.filter(id__in=[a1.id, a2.id]).exists()
