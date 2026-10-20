import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major, MajorCategory
from apps.articles.models import Article, Category
from apps.dashboard.forms.university import UniversityForm
from apps.dashboard.forms.institute import InstituteForm
from apps.dashboard.forms.major import MajorForm
from apps.dashboard.forms.article import ArticleForm
from apps.html_editor.widgets import CustomHTMLEditorWidget

User = get_user_model()


@pytest.mark.django_db
class TestWhyChooseSciencesGates:
    """Test suite for 'Why Choose Sciences Gates' section across all models, forms, and views."""

    def test_forms_contain_field_and_widget(self):
        """Verify that all 4 forms contain why_choose_sciences_gates field with CustomHTMLEditorWidget."""
        forms_to_check = [
            (UniversityForm, 'why_choose_sciences_gates'),
            (InstituteForm, 'why_choose_sciences_gates'),
            (MajorForm, 'why_choose_sciences_gates'),
            (ArticleForm, 'why_choose_sciences_gates'),
        ]
        for form_cls, field_name in forms_to_check:
            form = form_cls()
            assert field_name in form.fields, f"{field_name} missing from {form_cls.__name__}"
            widget = form.fields[field_name].widget
            assert isinstance(widget, CustomHTMLEditorWidget), f"{field_name} in {form_cls.__name__} does not use CustomHTMLEditorWidget"

    def test_university_why_choose_rendering(self, client):
        """Test that University detail view renders the section when why_choose_sciences_gates is set."""
        uni = University.objects.create(
            name="جامعة الملايا",
            slug="um-university",
            logo="test.png",
            main_image="test.png",
            location="كوالالمبور",
            publish_status="published",
            description="<p>نبذة</p>",
            why_choose_sciences_gates="<p>وكيل رسمي معتمد وخدمات استقبال وتأشيرة مجانية</p>"
        )
        url = reverse('universities:detail', kwargs={'slug': uni.slug})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "لماذا تختار شركة بوابات العلوم للتسجيل في جامعة الملايا؟" in content
        assert "وكيل رسمي معتمد وخدمات استقبال وتأشيرة مجانية" in content

    def test_institute_why_choose_rendering(self, client):
        """Test that Institute detail view renders the section when why_choose_sciences_gates is set."""
        inst = Institute.objects.create(
            name="معهد إي إل إس",
            slug="els-institute",
            publish_status="published",
            description="<p>نبذة عن المعهد</p>",
            why_choose_sciences_gates="<p>مساعدة كاملة في تحديد المستوى واختيار الدورة المناسبة مجاناً</p>"
        )
        url = reverse('institutes:detail', kwargs={'slug': inst.slug})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "لماذا تختار شركة بوابات العلوم للدراسة في معهد إي إل إس؟" in content
        assert "مساعدة كاملة في تحديد المستوى واختيار الدورة المناسبة مجاناً" in content

    def test_major_why_choose_rendering(self, client):
        """Test that Major detail view renders the section when why_choose_sciences_gates is set."""
        cat = MajorCategory.objects.create(name="الهندسة", slug="engineering")
        major = Major.objects.create(
            name="هندسة البرمجيات",
            slug="software-engineering",
            category=cat,
            publish_status="published",
            description="<p>نبذة عن تخصص هندسة البرمجيات</p>",
            why_choose_sciences_gates="<p>توجيه أكاديمي واختيار الجامعة الأنسب لمستقبلك البرمجي</p>"
        )
        url = reverse('majors:detail', kwargs={'slug': major.slug})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "لماذا تختار شركة بوابات العلوم لدراسة تخصص هندسة البرمجيات؟" in content
        assert "توجيه أكاديمي واختيار الجامعة الأنسب لمستقبلك البرمجي" in content

    def test_article_why_choose_rendering(self, client):
        """Test that Article detail view renders the section when why_choose_sciences_gates is set."""
        user = User.objects.create_user(username='writer', password='password123')
        cat = Category.objects.create(name="نصائح عامة", slug="general-tips")
        article = Article.objects.create(
            title="كيف تبدأ دراستك في ماليزيا",
            slug="how-to-study-in-malaysia",
            category=cat,
            author=user,
            publish_status="published",
            content="<p>محتوى المقال التثقيفي</p>",
            why_choose_sciences_gates="<p>نحن نوفر لك استشارة مجانية مع خبرائنا الأكاديميين</p>"
        )
        url = reverse('articles:detail', kwargs={'slug': article.slug})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "لماذا تختار شركة بوابات العلوم؟" in content
        assert "نحن نوفر لك استشارة مجانية مع خبرائنا الأكاديميين" in content
