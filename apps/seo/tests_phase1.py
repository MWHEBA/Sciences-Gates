from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.articles.models import Article
from apps.core.models import UserRole
from apps.seo.models import SEOAnalysisDetail


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "sciencesgates.com"])
class Phase1SEOAnalyzerTests(TestCase):
    def setUp(self):
        self.superadmin = User.objects.create_user(username="super", password="pass123")
        self.superadmin.is_staff = True
        self.superadmin.save(update_fields=["is_staff"])
        self.superadmin.profile.role = UserRole.SUPER_ADMIN
        self.superadmin.profile.save(update_fields=["role"])

        image = SimpleUploadedFile("f.jpg", b"filecontent", content_type="image/jpeg")
        self.article = Article.objects.create(
            title="Sample Article For SEO",
            slug="sample-article-for-seo",
            featured_image=image,
            content="<h2>Intro</h2><p>" + ("word " * 600) + "</p>",
            publish_status="unpublished",
            meta_title="This is a valid SEO title length for article testing",
            meta_description="This is a valid meta description used to verify analyzer scoring and rendering output in dashboard.",
        )

    def test_unpublished_preview_superadmin_only(self):
        url = reverse("articles:detail", kwargs={"slug": self.article.slug}) + "?preview=1"

        anon_response = self.client.get(url)
        self.assertEqual(anon_response.status_code, 404)

        self.client.login(username="super", password="pass123")
        admin_response = self.client.get(url)
        self.assertEqual(admin_response.status_code, 200)

    def test_analyze_endpoint_requires_superadmin(self):
        url = reverse("dashboard:seo_analyze", kwargs={"content_type": "articles", "pk": self.article.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "UNAUTHORIZED")

    def test_analyze_and_detail_success_and_store_json(self):
        self.client.login(username="super", password="pass123")

        analyze_url = reverse("dashboard:seo_analyze", kwargs={"content_type": "articles", "pk": self.article.pk})
        analyze_response = self.client.post(analyze_url, HTTP_HOST="sciencesgates.com", secure=True)
        self.assertEqual(analyze_response.status_code, 200)
        analyze_json = analyze_response.json()
        self.assertEqual(analyze_json["status"], "success")

        self.article.refresh_from_db()
        self.assertIsNotNone(self.article.seo_last_analysis)

        detail = SEOAnalysisDetail.objects.get(object_id=self.article.pk)
        self.assertIn("score_summary", detail.analysis_report_json)

        detail_url = reverse("dashboard:seo_detail", kwargs={"content_type": "articles", "pk": self.article.pk})
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, 200)

        detail_json = detail_response.json()
        self.assertEqual(detail_json["status"], "success")

        serp_url = detail_json.get("serp_preview", {}).get("url", "")
        self.assertTrue(serp_url.startswith("https://sciencesgates.com"))
        self.assertNotIn("testserver", serp_url)
