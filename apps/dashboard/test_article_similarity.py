import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from apps.articles.models import Article, Category, Tag, ArticleFAQ, IgnoredSimilarity
from apps.redirects.models import Redirect
from apps.core.models import UserProfile, UserRole

@pytest.fixture
def content_admin_client(client, db):
    user = User.objects.create_user(username='admin', password='password')
    profile = user.profile
    profile.role = UserRole.CONTENT_ADMIN
    profile.save()
    client.login(username='admin', password='password')
    return client

@pytest.fixture
def articles_fixture(db):
    cat = Category.objects.create(name='Test Category', slug='test-category')
    
    art_a = Article.objects.create(
        title='دليل الدراسة في ماليزيا بالتفصيل',
        slug='study-malaysia-detail',
        featured_image='articles/test.jpg',
        content='هذا المقال يحتوي على معلومات مفصلة عن الدراسة في ماليزيا وتكاليفها والجامعات المعترف بها بالتفصيل.',
        category=cat,
        publish_status='published'
    )
    art_b = Article.objects.create(
        title='دليل شامل عن الدراسة في ماليزيا بالتفصيل',
        slug='comprehensive-study-malaysia',
        featured_image='articles/test.jpg',
        content='هذا المقال يحتوي على معلومات مفصلة عن الدراسة في ماليزيا وتكاليفها والجامعات المعترف بها بالتفصيل.',
        category=cat,
        publish_status='published'
    )
    
    tag = Tag.objects.create(name='ماليزيا', slug='malaysia')
    art_b.tags.add(tag)
    
    faq = ArticleFAQ.objects.create(
        article=art_b,
        question='ما هي تكاليف الدراسة؟',
        answer='التكاليف مناسبة وتبدأ من 3000 دولار سنوياً.'
    )
    
    return art_a, art_b, tag, faq

@pytest.mark.django_db
def test_similarity_scan(content_admin_client, articles_fixture):
    art_a, art_b, _, _ = articles_fixture
    url = reverse('dashboard:article_similarity') + '?scan=true&threshold=70&mode=both'
    response = content_admin_client.get(url)
    assert response.status_code == 200
    assert 'duplicate_pairs' in response.context
    pairs = response.context['duplicate_pairs']
    assert len(pairs) == 1
    # Check Jaccard similarities
    assert pairs[0]['title_similarity'] >= 70.0
    assert pairs[0]['content_similarity'] >= 70.0

@pytest.mark.django_db
def test_ignore_and_restore_action(content_admin_client, articles_fixture):
    art_a, art_b, _, _ = articles_fixture
    url = reverse('dashboard:article_similarity_action')
    
    # Test ignore
    response = content_admin_client.post(url, {
        'action': 'ignore',
        'article_a_id': art_a.id,
        'article_b_id': art_b.id
    })
    assert response.status_code == 200
    low_id = min(art_a.id, art_b.id)
    high_id = max(art_a.id, art_b.id)
    assert IgnoredSimilarity.objects.filter(article_a_id=low_id, article_b_id=high_id).exists()
    
    # Test restore
    response = content_admin_client.post(url, {
        'action': 'restore',
        'article_a_id': art_a.id,
        'article_b_id': art_b.id
    })
    assert response.status_code == 200
    assert not IgnoredSimilarity.objects.filter(article_a_id=low_id, article_b_id=high_id).exists()

@pytest.mark.django_db
def test_auto_merge_action(content_admin_client, articles_fixture):
    art_a, art_b, tag, faq = articles_fixture
    url = reverse('dashboard:article_similarity_action')
    
    # Auto-merge: keep art_a, delete art_b
    response = content_admin_client.post(url, {
        'action': 'auto_merge',
        'article_a_id': art_a.id,
        'article_b_id': art_b.id,
        'keep_id': art_a.id,
        'delete_id': art_b.id
    })
    assert response.status_code == 200
    
    # art_b should be deleted
    assert not Article.objects.filter(id=art_b.id).exists()
    
    # art_a should inherit tags and FAQs
    assert art_a.tags.filter(id=tag.id).exists()
    assert art_a.faqs.filter(question=faq.question).exists()
    
    # Redirects should be created
    assert Redirect.objects.filter(old_url=f"/articles/{art_b.slug}/", new_url=f"/articles/{art_a.slug}/").exists()
    assert Redirect.objects.filter(old_url=f"/{art_b.slug}/", new_url=f"/articles/{art_a.slug}/").exists()

@pytest.mark.django_db
def test_manual_merge_view_flow(content_admin_client, articles_fixture):
    art_a, art_b, tag, faq = articles_fixture
    url = reverse('dashboard:article_manual_merge', kwargs={'keep_id': art_a.id, 'delete_id': art_b.id})
    
    # GET request
    response = content_admin_client.get(url)
    assert response.status_code == 200
    assert 'form' in response.context
    
    # POST request
    post_data = {
        'title': 'مستقبل الدراسة في ماليزيا المدمج',
        'slug': 'study-malaysia-detail-merged',
        'content': 'نص جديد بعد التعديل والدمج اليدوي.',
        'category': art_a.category.id,
        'publish_status': 'published',
        'author': User.objects.get(username='admin').id,
        'faqs-TOTAL_FORMS': '0',
        'faqs-INITIAL_FORMS': '0',
        'faqs-MIN_NUM_FORMS': '0',
        'faqs-MAX_NUM_FORMS': '1000',
    }
    response = content_admin_client.post(url, post_data)
    assert response.status_code == 302
    
    # art_a should be updated
    art_a.refresh_from_db()
    assert art_a.title == 'مستقبل الدراسة في ماليزيا المدمج'
    assert art_a.content == 'نص جديد بعد التعديل والدمج اليدوي.'
    
    # art_b should be deleted
    assert not Article.objects.filter(id=art_b.id).exists()
    
    # Redirects should be created
    assert Redirect.objects.filter(old_url=f"/articles/{art_b.slug}/", new_url=f"/articles/{art_a.slug}/").exists()

@pytest.mark.django_db
def test_similarity_scan_different_countries(content_admin_client):
    cat = Category.objects.create(name='Test Cat', slug='test-cat')
    
    # Saudi Arabia vs Turkey (different countries)
    art_saudi = Article.objects.create(
        title='الجامعات المعتمدة في السعودية للطلاب للعام الجديد',
        slug='accredited-universities-saudi',
        content='مقال طويل يحتوي على محتوى مفصل للجامعات المعتمدة في المملكة العربية السعودية للطلاب الراغبين بالدراسة للعام الجديد.',
        category=cat,
        publish_status='published'
    )
    art_turkey = Article.objects.create(
        title='الجامعات المعتمدة في تركيا للطلاب للعام الجديد',
        slug='accredited-universities-turkey',
        content='مقال طويل يحتوي على محتوى مفصل للجامعات المعتمدة في الجمهورية التركية للطلاب الراغبين بالدراسة للعام الجديد.',
        category=cat,
        publish_status='published'
    )
    
    url = reverse('dashboard:article_similarity') + '?scan=true&threshold=50&mode=title'
    response = content_admin_client.get(url)
    assert response.status_code == 200
    pairs = response.context.get('duplicate_pairs', [])
    
    # Even though titles have high word overlap ("الجامعات المعتمدة في ... للطلاب للعام الجديد"),
    # they differ in country, so similarity is forced to 0% and they must NOT match.
    for pair in pairs:
        ids = {pair['article_a'].id, pair['article_b'].id}
        assert not (art_saudi.id in ids and art_turkey.id in ids)

@pytest.mark.django_db
def test_similarity_scan_generic_vs_country(content_admin_client):
    cat = Category.objects.create(name='Test Cat', slug='test-cat')
    
    # Generic vs Turkey (one empty country, one non-empty country)
    art_generic = Article.objects.create(
        title='الجامعات المعتمدة للطلاب للعام الجديد',
        slug='accredited-universities-generic',
        content='مقال طويل يحتوي على محتوى مفصل للجامعات المعتمدة للطلاب الراغبين بالدراسة للعام الجديد.',
        category=cat,
        publish_status='published'
    )
    art_turkey = Article.objects.create(
        title='الجامعات المعتمدة في تركيا للطلاب للعام الجديد',
        slug='accredited-universities-turkey-2',
        content='مقال طويل يحتوي على محتوى مفصل للجامعات المعتمدة في تركيا للطلاب الراغبين بالدراسة للعام الجديد.',
        category=cat,
        publish_status='published'
    )
    
    url = reverse('dashboard:article_similarity') + '?scan=true&threshold=50&mode=title'
    response = content_admin_client.get(url)
    assert response.status_code == 200
    pairs = response.context.get('duplicate_pairs', [])
    
    for pair in pairs:
        ids = {pair['article_a'].id, pair['article_b'].id}
        assert not (art_generic.id in ids and art_turkey.id in ids)

@pytest.mark.django_db
def test_similarity_scan_same_country(content_admin_client):
    cat = Category.objects.create(name='Test Cat', slug='test-cat')
    
    # Turkey vs Turkey (same country)
    art_turkey_1 = Article.objects.create(
        title='دليل الجامعات المعتمدة في تركيا',
        slug='accredited-universities-turkey-a',
        content='مقال طويل يحتوي على محتوى مفصل للجامعات المعتمدة في تركيا للطلاب الراغبين بالدراسة للعام الجديد.',
        category=cat,
        publish_status='published'
    )
    art_turkey_2 = Article.objects.create(
        title='الجامعات المعتمدة في تركيا بالتفصيل',
        slug='accredited-universities-turkey-b',
        content='مقال طويل يحتوي على محتوى مفصل للجامعات المعتمدة في تركيا للطلاب الراغبين بالدراسة للعام الجديد.',
        category=cat,
        publish_status='published'
    )
    
    url = reverse('dashboard:article_similarity') + '?scan=true&threshold=50&mode=title'
    response = content_admin_client.get(url)
    assert response.status_code == 200
    pairs = response.context.get('duplicate_pairs', [])
    
    # Since both target Turkey, they should match as duplicates.
    matched = False
    for pair in pairs:
        ids = {pair['article_a'].id, pair['article_b'].id}
        if art_turkey_1.id in ids and art_turkey_2.id in ids:
            matched = True
            break
    assert matched
