from django.test import TestCase, Client
from django.urls import reverse


class SecurityHeadersMiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_security_headers_exist(self):
        response = self.client.get('/')
        self.assertIn('Content-Security-Policy', response.headers)
        self.assertIn('Permissions-Policy', response.headers)

    def test_csp_directives(self):
        response = self.client.get('/')
        csp = response.headers.get('Content-Security-Policy', '')
        self.assertIn("object-src 'none'", csp)
        self.assertIn("base-uri 'self'", csp)
        self.assertIn("form-action 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("script-src 'self' 'unsafe-inline'", csp)

    def test_permissions_policy_directives(self):
        response = self.client.get('/')
        policy = response.headers.get('Permissions-Policy', '')
        self.assertIn("geolocation=()", policy)
        self.assertIn("microphone=()", policy)
        self.assertIn("camera=()", policy)

    def test_no_x_powered_by_header(self):
        response = self.client.get('/')
        self.assertNotIn('X-Powered-By', response.headers)
        self.assertNotIn('x-powered-by', response.headers)

    def test_x_robots_tag_for_media_requests(self):
        response = self.client.get('/media/uploads/test.jpg')
        self.assertEqual(response.headers.get('X-Robots-Tag'), 'noindex')
