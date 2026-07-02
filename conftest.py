"""
Pytest configuration and shared fixtures for the entire project.

This file contains:
- Pytest configuration
- Shared fixtures for all tests
- Common test utilities
"""
import os
import sys

# Configure Django settings BEFORE anything else
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

# Setup Django early - this must happen before any Django imports
import django
django.setup()

# Set testing flag to skip heavy context processors/signals during tests
from django.conf import settings
settings.TESTING = True

import pytest


@pytest.fixture
def admin_user(db):
    """
    Create a staff/admin user for testing.
    
    Returns:
        User: A staff user with username 'admin' and password 'testpass123'
    """
    from django.contrib.auth.models import User
    user = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True
    )
    return user


@pytest.fixture
def regular_user(db):
    """
    Create a regular (non-staff) user for testing.
    
    Returns:
        User: A regular user with username 'user' and password 'testpass123'
    """
    from django.contrib.auth.models import User
    user = User.objects.create_user(
        username='user',
        email='user@example.com',
        password='testpass123',
        is_staff=False
    )
    return user


@pytest.fixture
def staff_user(db):
    """
    Create a staff user for testing.
    
    Returns:
        User: A staff user with username 'staff' and password 'testpass123'
    """
    from django.contrib.auth.models import User
    user = User.objects.create_user(
        username='staff',
        email='staff@example.com',
        password='testpass123',
        is_staff=True
    )
    return user


@pytest.fixture
def client():
    """
    Provide Django test client for HTTP requests.
    
    Returns:
        Client: Django test client
    """
    from django.test import Client
    return Client()


@pytest.fixture
def authenticated_client(client, admin_user):
    """
    Provide authenticated Django test client.
    
    Returns:
        Client: Django test client logged in as admin user
    """
    client.login(username='admin', password='testpass123')
    return client


@pytest.fixture
def request_factory():
    """
    Provide Django RequestFactory for creating mock requests.
    
    Returns:
        RequestFactory: Django request factory
    """
    from django.test import RequestFactory
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory):
    """
    Create a mock GET request.
    
    Returns:
        HttpRequest: Mock GET request
    """
    return request_factory.get('/')


@pytest.fixture
def now():
    """
    Get current timezone-aware datetime.
    
    Returns:
        datetime: Current timezone-aware datetime
    """
    from django.utils import timezone
    return timezone.now()


# Pytest markers
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "views: marks tests as view tests"
    )
    config.addinivalue_line(
        "markers", "models: marks tests as model tests"
    )
    config.addinivalue_line(
        "markers", "forms: marks tests as form tests"
    )
    config.addinivalue_line(
        "markers", "seo: marks tests as SEO-related tests"
    )


# Pytest hooks for better output
def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers based on test location.
    """
    for item in items:
        # Add markers based on test file location
        if 'integration' in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif 'unit' in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add markers based on test class name
        if 'View' in item.nodeid:
            item.add_marker(pytest.mark.views)
        elif 'Model' in item.nodeid:
            item.add_marker(pytest.mark.models)
        elif 'Form' in item.nodeid:
            item.add_marker(pytest.mark.forms)
        elif 'SEO' in item.nodeid or 'Sitemap' in item.nodeid or 'Schema' in item.nodeid:
            item.add_marker(pytest.mark.seo)
