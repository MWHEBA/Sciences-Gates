from django.test import TestCase, Client
from apps.leads.models import Lead, LeadType


class LegalPagesAndConsentTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_privacy_page_returns_200_and_content(self):
        response = self.client.get('/privacy/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn("سياسة الخصوصية", content)
        self.assertIn("PDPA", content)

    def test_terms_page_returns_200_and_content(self):
        response = self.client.get('/terms/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn("الشروط والأحكام", content)

    def test_footer_legal_links_resolve(self):
        response = self.client.get('/')
        content = response.content.decode('utf-8')
        self.assertIn('/privacy/', content)
        self.assertIn('/terms/', content)

    def test_lead_form_records_privacy_consent_audit_trail(self):
        payload = {
            'lead_type': LeadType.CONTACT,
            'name': 'طالب تجريبي',
            'email': 'student@example.com',
            'phone': '+60123456789',
            'nationality': 'سعودي',
            'message': 'استفسار عن القبول',
            'agree_to_privacy': 'on',
        }
        response = self.client.post('/leads/submit/', payload, follow=True)
        self.assertEqual(response.status_code, 200)

        lead = Lead.objects.filter(email='student@example.com').first()
        self.assertIsNotNone(lead)
        self.assertTrue(lead.privacy_consent)
        self.assertIsNotNone(lead.privacy_consent_at)
        self.assertEqual(lead.privacy_policy_version, '1.0')
