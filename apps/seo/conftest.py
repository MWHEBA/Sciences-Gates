"""
Pytest configuration and fixtures for SEO app tests.
"""
import pytest
from django.test import RequestFactory
from django.template import Template, Context


@pytest.fixture
def request_factory():
    """Provide Django RequestFactory for creating mock requests."""
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory):
    """Create a mock GET request."""
    return request_factory.get('/')


@pytest.fixture
def template_context():
    """Provide a template context for testing template tags."""
    return Context({})


@pytest.fixture
def render_template():
    """Provide a function to render templates with context."""
    def _render(template_string, context_dict):
        template = Template(template_string)
        context = Context(context_dict)
        return template.render(context)
    return _render
