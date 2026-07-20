import pytest
from django.urls import reverse
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article
from apps.core.models import PublishStatus

@pytest.mark.django_db
class TestLegacyUrlsRouting:
    """
    Tests for fallback routing of legacy URLs (old URLs without category prefixes).
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        # إنشاء بيانات الاختبار للجامعات
        self.legacy_uni = University.objects.create(
            name='جامعة اختبارية قديمة',
            slug='legacy-uni-slug',
            is_legacy=True,
            publish_status=PublishStatus.PUBLISHED,
            description='وصف الجامعة',
            location='كوالالمبور'
        )
        self.standard_uni = University.objects.create(
            name='جامعة اختبارية قياسية',
            slug='standard-uni-slug',
            is_legacy=False,
            publish_status=PublishStatus.PUBLISHED,
            description='وصف الجامعة',
            location='كوالالمبور'
        )

        # إنشاء بيانات الاختبار للمعاهد
        self.legacy_inst = Institute.objects.create(
            name='معهد اختباري قديم',
            slug='legacy-inst-slug',
            is_legacy=True,
            publish_status=PublishStatus.PUBLISHED,
            description='وصف المعهد'
        )
        self.standard_inst = Institute.objects.create(
            name='معهد اختباري قياسي',
            slug='standard-inst-slug',
            is_legacy=False,
            publish_status=PublishStatus.PUBLISHED,
            description='وصف المعهد'
        )

        # إنشاء بيانات الاختبار للتخصصات
        self.legacy_major = Major.objects.create(
            name='تخصص اختباري قديم',
            slug='legacy-major-slug',
            is_legacy=True,
            publish_status=PublishStatus.PUBLISHED,
            description='وصف التخصص'
        )
        self.standard_major = Major.objects.create(
            name='تخصص اختباري قياسي',
            slug='standard-major-slug',
            is_legacy=False,
            publish_status=PublishStatus.PUBLISHED,
            description='وصف التخصص'
        )

        # إنشاء بيانات الاختبار للمقالات
        self.legacy_article = Article.objects.create(
            title='مقال اختباري قديم',
            slug='legacy-article-slug',
            is_legacy=True,
            publish_status=PublishStatus.PUBLISHED,
            content='<p>محتوى المقال</p>'
        )
        self.standard_article = Article.objects.create(
            title='مقال اختباري قياسي',
            slug='standard-article-slug',
            is_legacy=False,
            publish_status=PublishStatus.PUBLISHED,
            content='<p>محتوى المقال</p>'
        )

    def test_legacy_university_url_resolves(self, client):
        # اختبار تحويل الرابط القديم للجامعة مباشرة للرابط الجديد ببادئة بريديركت 301
        response = client.get('/legacy-uni-slug/')
        assert response.status_code == 301
        assert response.url == '/universities/legacy-uni-slug/'

    def test_prefixed_university_redirects_to_legacy(self, client):
        # الرابط ذو البادئة يجب أن يعمل مباشرة ويرجع 200 (لا توجد إعادة توجيه للرابط القديم)
        url = reverse('universities:detail', kwargs={'slug': self.legacy_uni.slug})
        response = client.get(url)
        assert response.status_code == 200

    def test_legacy_university_redirects_to_prefixed(self, client):
        # اختبار تحويل الرابط القديم للجامعة القياسية إلى رابط ببادئة
        response = client.get('/standard-uni-slug/')
        assert response.status_code == 301
        expected_url = reverse('universities:detail', kwargs={'slug': self.standard_uni.slug})
        assert response.url == expected_url

    def test_prefixed_university_resolves_normally(self, client):
        # اختبار فتح الرابط القياسي ببادئة بشكل طبيعي والحصول على 200
        url = reverse('universities:detail', kwargs={'slug': self.standard_uni.slug})
        response = client.get(url)
        assert response.status_code == 200

    def test_legacy_institute_url_resolves(self, client):
        # اختبار تحويل الرابط القديم للمعهد مباشرة للرابط الجديد ببادئة بريديركت 301
        response = client.get('/legacy-inst-slug/')
        assert response.status_code == 301
        assert response.url == '/institutes/legacy-inst-slug/'

    def test_prefixed_institute_redirects_to_legacy(self, client):
        # الرابط ذو البادئة للمعهد يجب أن يعمل مباشرة ويرجع 200
        url = reverse('institutes:detail', kwargs={'slug': self.legacy_inst.slug})
        response = client.get(url)
        assert response.status_code == 200

    def test_legacy_institute_redirects_to_prefixed(self, client):
        # اختبار تحويل الرابط القديم للمعهد إلى رابط ببادئة
        response = client.get('/standard-inst-slug/')
        assert response.status_code == 301
        expected_url = reverse('institutes:detail', kwargs={'slug': self.standard_inst.slug})
        assert response.url == expected_url

    def test_legacy_major_url_resolves(self, client):
        # اختبار تحويل الرابط القديم للتخصص مباشرة للرابط الجديد ببادئة بريديركت 301
        response = client.get('/legacy-major-slug/')
        assert response.status_code == 301
        assert response.url == '/majors/legacy-major-slug/'

    def test_prefixed_major_redirects_to_legacy(self, client):
        # الرابط ذو البادئة للتخصص يجب أن يعمل مباشرة ويرجع 200
        url = reverse('majors:detail', kwargs={'slug': self.legacy_major.slug})
        response = client.get(url)
        assert response.status_code == 200

    def test_legacy_major_redirects_to_prefixed(self, client):
        # اختبار تحويل الرابط القديم للتخصص إلى رابط ببادئة
        response = client.get('/standard-major-slug/')
        assert response.status_code == 301
        expected_url = reverse('majors:detail', kwargs={'slug': self.standard_major.slug})
        assert response.url == expected_url

    def test_legacy_article_url_resolves(self, client):
        # اختبار تحويل الرابط القديم للمقال مباشرة للرابط الجديد ببادئة بريديركت 301
        response = client.get('/legacy-article-slug/')
        assert response.status_code == 301
        assert response.url == '/articles/legacy-article-slug/'

    def test_prefixed_article_redirects_to_legacy(self, client):
        # الرابط ذو البادئة للمقال يجب أن يعمل مباشرة ويرجع 200
        url = reverse('articles:detail', kwargs={'slug': self.legacy_article.slug})
        response = client.get(url)
        assert response.status_code == 200

    def test_legacy_article_redirects_to_prefixed(self, client):
        # اختبار تحويل الرابط القديم للمقال إلى رابط ببادئة
        response = client.get('/standard-article-slug/')
        assert response.status_code == 301
        expected_url = reverse('articles:detail', kwargs={'slug': self.standard_article.slug})
        assert response.url == expected_url

    def test_slug_collision_resolution_order(self, client):
        # اختبار أولوية التوجيه عند تطابق الرابط القديم باستخدام follow=True لتتبع الـ redirects
        shared_slug = 'shared-legacy-slug'
        
        # إنشاء العناصر الأربعة بنفس الرابط
        uni = University.objects.create(
            name='الجامعة المشتركة',
            slug=shared_slug,
            is_legacy=True,
            publish_status=PublishStatus.PUBLISHED,
            description='وصف',
            location='موقع'
        )
        inst = Institute.objects.create(
            name='المعهد المشترك',
            slug=shared_slug,
            is_legacy=True,
            publish_status=PublishStatus.PUBLISHED,
            description='وصف'
        )
        major = Major.objects.create(
            name='التخصص المشترك',
            slug=shared_slug,
            is_legacy=True,
            publish_status=PublishStatus.PUBLISHED,
            description='وصف'
        )
        art = Article.objects.create(
            title='المقال المشترك',
            slug=shared_slug,
            is_legacy=True,
            publish_status=PublishStatus.PUBLISHED,
            content='محتوى'
        )
        
        # 1. التوجيه يجب أن يؤدي إلى صفحة الجامعة أولاً
        res = client.get(f'/{shared_slug}/', follow=True)
        assert res.status_code == 200
        assert 'الجامعة المشتركة' in res.content.decode('utf-8')
        
        # 2. حذف الجامعة، يجب أن يؤدي التوجيه إلى صفحة المعهد
        uni.delete()
        res = client.get(f'/{shared_slug}/', follow=True)
        assert res.status_code == 200
        assert 'المعهد المشترك' in res.content.decode('utf-8')
        
        # 3. حذف المعهد، يجب أن يؤدي التوجيه إلى صفحة التخصص
        inst.delete()
        res = client.get(f'/{shared_slug}/', follow=True)
        assert res.status_code == 200
        assert 'التخصص المشترك' in res.content.decode('utf-8')
        
        # 4. حذف التخصص، يجب أن يؤدي التوجيه إلى صفحة المقال
        major.delete()
        res = client.get(f'/{shared_slug}/', follow=True)
        assert res.status_code == 200
        assert 'المقال المشترك' in res.content.decode('utf-8')
        
        # 5. حذف المقال، يجب أن يرجع 404
        art.delete()
        res = client.get(f'/{shared_slug}/', follow=True)
        assert res.status_code == 404

