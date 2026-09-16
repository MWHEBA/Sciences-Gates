"""
Tests for General FAQ Dashboard Views (List, Create, Update, Delete, Toggle).
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.core.models import GeneralFAQ, UserProfile, UserRole


class GeneralFAQDashboardViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='content_admin',
            email='admin@example.com',
            password='Password123!',
            is_staff=True
        )
        self.profile = self.admin_user.profile
        self.profile.role = UserRole.CONTENT_ADMIN
        self.profile.save()

        self.faq = GeneralFAQ.objects.create(
            question="ما هي تكلفة دراسة اللغة الإنجليزية؟",
            slug="english-costs-test",
            answer="تبدأ من 450$ شهرياً في المعاهد المعتمدة.",
            category="english",
            order=1,
            is_published=True,
            is_featured=False
        )

    def test_anonymous_user_redirected(self):
        response = self.client.get(reverse('dashboard:faq_list'))
        self.assertEqual(response.status_code, 302)

    def test_faq_list_view_authenticated(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('dashboard:faq_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ما هي تكلفة دراسة اللغة الإنجليزية؟")
        self.assertContains(response, "english-costs-test")

    def test_faq_create_view(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(reverse('dashboard:faq_create'), {
            'question': 'هل الفيزا مضمونة؟',
            'slug': 'guaranteed-visa',
            'category': 'visa',
            'order': 2,
            'is_published': True,
            'is_featured': True,
            'answer': 'نسبة قبول فيزا ماليزيا تفوق 98% عند اكتمال الوثائق.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(GeneralFAQ.objects.filter(slug='guaranteed-visa').exists())
        created_faq = GeneralFAQ.objects.get(slug='guaranteed-visa')
        self.assertTrue(created_faq.is_featured)

    def test_faq_update_view(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(reverse('dashboard:faq_edit', args=[self.faq.pk]), {
            'question': 'ما هي تكلفة دراسة اللغة الإنجليزية المحدثة؟',
            'slug': 'english-costs-test',
            'category': 'english',
            'order': 1,
            'is_published': True,
            'is_featured': True,
            'answer': 'تبدأ من 500$ شهرياً.',
        })
        self.assertEqual(response.status_code, 302)
        self.faq.refresh_from_db()
        self.assertEqual(self.faq.question, 'ما هي تكلفة دراسة اللغة الإنجليزية المحدثة؟')
        self.assertTrue(self.faq.is_featured)

    def test_faq_delete_view(self):
        self.client.force_login(self.admin_user)
        # GET confirm delete
        get_res = self.client.get(reverse('dashboard:faq_delete', args=[self.faq.pk]))
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, "تأكيد حذف السؤال")

        # POST delete
        post_res = self.client.post(reverse('dashboard:faq_delete', args=[self.faq.pk]))
        self.assertEqual(post_res.status_code, 302)
        self.assertFalse(GeneralFAQ.objects.filter(pk=self.faq.pk).exists())

    def test_faq_ajax_toggle_view(self):
        self.client.force_login(self.admin_user)
        # Toggle is_featured
        res_featured = self.client.post(
            reverse('dashboard:faq_toggle', args=[self.faq.pk]),
            {'field': 'is_featured'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res_featured.status_code, 200)
        data = res_featured.json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['value'])
        self.faq.refresh_from_db()
        self.assertTrue(self.faq.is_featured)

        # Toggle is_published
        res_published = self.client.post(
            reverse('dashboard:faq_toggle', args=[self.faq.pk]),
            {'field': 'is_published'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res_published.status_code, 200)
        self.assertFalse(res_published.json()['value'])
        self.faq.refresh_from_db()
        self.assertFalse(self.faq.is_published)
