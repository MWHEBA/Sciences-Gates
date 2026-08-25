from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse

from apps.articles.models import Article, Category
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.core.models import UserRole
from apps.seo.models import SEOAnalysisDetail
from apps.dashboard.views import PreviewMetaAndBannerMixin

@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "sciencesgates.com"])
class Phase2SEOPreviewTests(TestCase):
    def setUp(self):
        # Create different users
        self.superadmin = User.objects.create_user(username="super_admin_user", password="pass123")
        self.superadmin.is_staff = True
        self.superadmin.save()
        self.superadmin.profile.role = UserRole.SUPER_ADMIN
        self.superadmin.profile.save()

        self.content_admin = User.objects.create_user(username="content_admin_user", password="pass123")
        self.content_admin.is_staff = True
        self.content_admin.save()
        self.content_admin.profile.role = UserRole.CONTENT_ADMIN
        self.content_admin.profile.save()

        self.regular_user = User.objects.create_user(username="regular_user", password="pass123")
        self.regular_user.profile.role = UserRole.SEO_ADMIN
        self.regular_user.profile.save()

        # Create basic categories and objects for testing previews
        self.category = Category.objects.create(name="أخبار", slug="news")
        
        image = SimpleUploadedFile("test_img.jpg", b"image_data", content_type="image/jpeg")
        self.article = Article.objects.create(
            title="مقالة تجريبية للمعاينة",
            slug="test-article-preview",
            featured_image=image,
            content="<p>محتوى المقالة التجريبية للتأكد من المعاينة والتحليل.</p>",
            publish_status="unpublished",
        )

        uni_logo = SimpleUploadedFile("uni_logo.png", b"logo_data", content_type="image/png")
        uni_main = SimpleUploadedFile("uni_main.png", b"main_data", content_type="image/png")
        self.university = University.objects.create(
            name="جامعة تجريبية للمعاينة",
            slug="test-university-preview",
            logo=uni_logo,
            main_image=uni_main,
            description="وصف الجامعة التجريبية للمعاينة والتحليل.",
            location="كوالالمبور",
            admission_requirements="شروط القبول للجامعة التجريبية.",
            publish_status="unpublished",
        )

        self.institute = Institute.objects.create(
            name="معهد تجريبي للمعاينة",
            slug="test-institute-preview",
            main_image=SimpleUploadedFile("inst_img.jpg", b"inst_img_data", content_type="image/jpeg"),
            description="وصف المعهد التجريبي للمعاينة والتحليل.",
            why_choose_us="لماذا تختار المعهد التجريبي للمعاينة والتحليل للاستفادة الكاملة من الدورات والبرامج.",
            publish_status="unpublished",
        )

        self.major = Major.objects.create(
            name="تخصص تجريبي للمعاينة",
            slug="test-major-preview",
            description="وصف التخصص التجريبي للمعاينة والتحليل.",
            publish_status="unpublished",
        )

    def test_anonymous_user_redirected_to_login(self):
        """Verify anonymous user is redirected to dashboard login page."""
        preview_urls = [
            reverse("dashboard:preview_article", kwargs={"pk": self.article.pk}),
            reverse("dashboard:preview_university", kwargs={"pk": self.university.pk}),
            reverse("dashboard:preview_institute", kwargs={"pk": self.institute.pk}),
            reverse("dashboard:preview_major", kwargs={"pk": self.major.pk}),
        ]

        for url in preview_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("dashboard:login"), response.url)

    def test_regular_user_access_denied_403(self):
        """Verify standard authenticated user gets 403 forbidden."""
        self.client.login(username="regular_user", password="pass123")
        preview_urls = [
            reverse("dashboard:preview_article", kwargs={"pk": self.article.pk}),
            reverse("dashboard:preview_university", kwargs={"pk": self.university.pk}),
            reverse("dashboard:preview_institute", kwargs={"pk": self.institute.pk}),
            reverse("dashboard:preview_major", kwargs={"pk": self.major.pk}),
        ]

        for url in preview_urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [302, 403])

    def test_authorized_staff_can_access_previews(self):
        """Verify Content Admin and Super Admin can access previews and get 200 with banner & meta."""
        for user_name in ["content_admin_user", "super_admin_user"]:
            self.client.login(username=user_name, password="pass123")
            
            preview_urls = [
                reverse("dashboard:preview_article", kwargs={"pk": self.article.pk}),
                reverse("dashboard:preview_university", kwargs={"pk": self.university.pk}),
                reverse("dashboard:preview_institute", kwargs={"pk": self.institute.pk}),
                reverse("dashboard:preview_major", kwargs={"pk": self.major.pk}),
            ]

            for url in preview_urls:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                
                # Check response header
                self.assertEqual(response.get("X-Robots-Tag"), "noindex, nofollow")

                # Check body/meta injection in HTML content
                content = response.content.decode("utf-8")
                self.assertIn('<meta name="robots" content="noindex,nofollow">', content)
                self.assertIn("هذه معاينة مسودة — غير منشورة للعموم", content)

    def test_html_injection_fallback_safely_works(self):
        """Test that PreviewMetaAndBannerMixin fallback returns unchanged HTML if head/body tags are absent."""
        class MockResponse:
            def __init__(self, content):
                self.content = content.encode("utf-8")
            def render(self):
                pass
            def decode(self, *args, **kwargs):
                return self.content.decode(*args, **kwargs)

        class MockView:
            def render_to_response(self, context, **kwargs):
                return MockResponse(context.get("html"))

        class TestView(PreviewMetaAndBannerMixin, MockView):
            pass

        # Case 1: HTML without any head/body tag
        raw_html = "<div>Simple Div Only</div>"
        view_instance = TestView()
        res = view_instance.render_to_response({"html": raw_html})
        res_content = res.content.decode("utf-8")
        self.assertEqual(res_content, raw_html)

        # Case 2: HTML with head only
        raw_html = "<html><head><title>Test</title></head></html>"
        res = view_instance.render_to_response({"html": raw_html})
        res_content = res.content.decode("utf-8")
        self.assertIn('<meta name="robots" content="noindex,nofollow">', res_content)
        self.assertNotIn("هذه معاينة مسودة", res_content)

        # Case 3: HTML with body only
        raw_html = "<html><body><main>Content</main></body></html>"
        res = view_instance.render_to_response({"html": raw_html})
        res_content = res.content.decode("utf-8")
        self.assertNotIn('<meta name="robots" content="noindex,nofollow">', res_content)
        self.assertIn("هذه معاينة مسودة — غير منشورة للعموم", res_content)

    def test_preview_mode_analysis_database_non_modification(self):
        """Verify that ?preview=1 transiently analyzes the content and strictly does not touch the DB."""
        self.client.login(username="content_admin_user", password="pass123")

        # Define targets to check
        targets = [
            ("articles", self.article),
            ("universities", self.university),
            ("institutes", self.institute),
            ("majors", self.major),
        ]

        for content_type, obj in targets:
            # Initial values
            self.assertEqual(obj.seo_score, 0)
            self.assertEqual(obj.seo_grade, "needs_improvement")
            self.assertEqual(obj.seo_critical_count, 0)
            self.assertEqual(obj.seo_warning_count, 0)
            self.assertIsNone(obj.seo_last_analysis)
            self.assertFalse(SEOAnalysisDetail.objects.filter(object_id=obj.pk).exists())

            analyze_url = reverse("dashboard:seo_analyze", kwargs={"content_type": content_type, "pk": obj.pk}) + "?preview=1"
            
            response = self.client.post(analyze_url, HTTP_HOST="sciencesgates.com", secure=True)
            self.assertEqual(response.status_code, 200)
            
            json_data = response.json()
            self.assertEqual(json_data["status"], "success")
            self.assertEqual(json_data["source"], "preview")
            self.assertIn("seo_score", json_data)
            self.assertIn("report", json_data)

            # Retrieve from DB to assert values are completely unmodified
            obj.refresh_from_db()
            self.assertEqual(obj.seo_score, 0)
            self.assertEqual(obj.seo_grade, "needs_improvement")
            self.assertEqual(obj.seo_critical_count, 0)
            self.assertEqual(obj.seo_warning_count, 0)
            self.assertIsNone(obj.seo_last_analysis)

            # Assert no SEOAnalysisDetail was created
            self.assertFalse(SEOAnalysisDetail.objects.filter(object_id=obj.pk).exists())
