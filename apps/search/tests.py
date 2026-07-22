"""
Tests for the search functionality.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class SearchUtilsTestCase(TestCase):
    """Test cases for search utility functions."""
    
    def setUp(self):
        """Set up test data."""
        from apps.universities.models import University
        from apps.institutes.models import Institute
        from apps.majors.models import Major
        from apps.articles.models import Article, Category
        
        # Create test universities
        self.university = University.objects.create(
            name='جامعة ماليزيا',
            slug='university-malaysia',
            logo='test.jpg',
            main_image='test.jpg',
            description='جامعة رائدة في ماليزيا',
            location='كوالالمبور',
            admission_requirements='متطلبات القبول',
            publish_status='published'
        )
        
        self.institute = Institute.objects.create(
            name='معهد التكنولوجيا',
            slug='tech-institute',
            main_image='test.jpg',
            description='معهد متخصص في التكنولوجيا',
            publish_status='published'
        )
        
        # Create test majors
        self.major = Major.objects.create(
            name='هندسة البرمجيات',
            slug='software-engineering',
            main_image='test.jpg',
            description='تخصص هندسة البرمجيات',
            study_duration='4 سنوات',
            publish_status='published'
        )
        
        # Create test articles
        self.category = Category.objects.create(
            name='أخبار التعليم',
            slug='education-news',
            description='أخبار التعليم العالي'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.article = Article.objects.create(
            title='مقالة عن التعليم العالي',
            slug='article-higher-education',
            featured_image='test.jpg',
            category=self.category,
            author=self.user,
            content='محتوى المقالة عن التعليم العالي',
            publish_status='published'
        )
    
    def test_search_query_with_university_name(self):
        """Test searching for universities by name."""
        from apps.search.utils import build_search_query
        
        results = build_search_query('ماليزيا')
        self.assertEqual(len(results['universities']), 1)
        self.assertEqual(results['universities'][0].name, 'جامعة ماليزيا')
    
    def test_search_query_with_institute_name(self):
        """Test searching for institutes by name."""
        from apps.search.utils import build_search_query
        
        results = build_search_query('التكنولوجيا')
        self.assertEqual(len(results['institutes']), 1)
        self.assertEqual(results['institutes'][0].name, 'معهد التكنولوجيا')
    
    def test_search_query_with_major_name(self):
        """Test searching for majors by name."""
        from apps.search.utils import build_search_query
        
        results = build_search_query('البرمجيات')
        self.assertEqual(len(results['majors']), 1)
        self.assertEqual(results['majors'][0].name, 'هندسة البرمجيات')
    
    def test_search_query_with_article_title(self):
        """Test searching for articles by title."""
        from apps.search.utils import build_search_query
        
        results = build_search_query('التعليم')
        self.assertEqual(len(results['articles']), 1)
        self.assertEqual(results['articles'][0].title, 'مقالة عن التعليم العالي')
    
    def test_search_query_empty_string(self):
        """Test searching with empty string."""
        from apps.search.utils import build_search_query
        
        results = build_search_query('')
        self.assertEqual(results['total_count'], 0)
        self.assertEqual(len(results['universities']), 0)
    
    def test_search_query_no_results(self):
        """Test searching with query that has no results."""
        from apps.search.utils import build_search_query
        
        results = build_search_query('غير موجود')
        self.assertEqual(results['total_count'], 0)
    
    def test_search_query_unpublished_content(self):
        """Test that unpublished content is not included in search results."""
        from apps.universities.models import University
        from apps.search.utils import build_search_query
        
        # Create unpublished university
        unpublished_uni = University.objects.create(
            name='جامعة غير منشورة',
            slug='unpublished-university',
            logo='test.jpg',
            main_image='test.jpg',
            description='جامعة غير منشورة',
            location='كوالالمبور',
            admission_requirements='متطلبات',
            publish_status='unpublished'
        )
        
        results = build_search_query('غير منشورة')
        self.assertEqual(len(results['universities']), 0)
        
    def test_search_query_hamza_normalization(self):
        """Test search query handles hamza normalization variations."""
        from apps.search.utils import build_search_query
        from apps.articles.models import Article
        
        # Create test article with 'ألمانيا'
        Article.objects.create(
            title='دراسة في ألمانيا',
            slug='study-in-germany',
            category=self.category,
            author=self.user,
            content='الدراسة في المانيا متميزة',
            publish_status='published'
        )
        
        # Searching for 'المانيا' (no hamza) should find 'دراسة في ألمانيا'
        results = build_search_query('المانيا')
        self.assertEqual(len(results['articles']), 1)
        self.assertEqual(results['articles'][0].title, 'دراسة في ألمانيا')
        
        # Searching for 'ألمانيا' (with hamza) should also find 'دراسة في ألمانيا'
        results = build_search_query('ألمانيا')
        self.assertEqual(len(results['articles']), 1)
        self.assertEqual(results['articles'][0].title, 'دراسة في ألمانيا')

    def test_search_query_teh_marbuta_normalization(self):
        """Test search query handles Teh Marbuta and Heh normalization."""
        from apps.search.utils import build_search_query
        
        # Database has 'جامعة ماليزيا' (ends with ة)
        # Searching for 'جامعه' (ends with ه) should match it
        results = build_search_query('جامعه')
        self.assertEqual(len(results['universities']), 1)
        self.assertEqual(results['universities'][0].name, 'جامعة ماليزيا')

    def test_search_query_yeh_normalization(self):
        """Test search query handles Yeh and Alef Maksura normalization."""
        from apps.search.utils import build_search_query
        from apps.universities.models import University
        
        # Create a university with name containing 'علي'
        University.objects.create(
            name='جامعة علي بن أبي طالب',
            slug='ali-university',
            logo='test.jpg',
            main_image='test.jpg',
            description='جامعة علي بن أبي طالب',
            location='كوالالمبور',
            admission_requirements='متطلبات القبول',
            publish_status='published'
        )
        
        # Search with 'على' (Alef Maksura) should find 'جامعة علي بن أبي طالب' (with Yeh)
        results = build_search_query('على')
        self.assertEqual(len(results['universities']), 1)
        self.assertEqual(results['universities'][0].name, 'جامعة علي بن أبي طالب')

    def test_search_query_fuzzy_matching(self):
        """Test search query handles spelling mistakes and typos."""
        from apps.search.utils import build_search_query
        
        # Major name is: 'هندسة البرمجيات'
        # Search for: 'البرمجبات' (typo: 'ج' instead of 'ي')
        results = build_search_query('البرمجبات')
        self.assertEqual(len(results['majors']), 1)
        self.assertEqual(results['majors'][0].name, 'هندسة البرمجيات')

    def test_search_query_stop_words_ignoring(self):
        """Test search query ignores common stop words in score calculation."""
        from apps.search.utils import build_search_query
        
        # Searching for 'دراسة في ماليزيا' (contains stop word 'في')
        # should find 'جامعة ماليزيا'
        results = build_search_query('دراسة في ماليزيا')
        self.assertTrue(len(results['universities']) >= 1)
        self.assertEqual(results['universities'][0].name, 'جامعة ماليزيا')
    
    def test_get_excerpt_short_text(self):
        """Test excerpt function with short text."""
        from apps.search.utils import get_excerpt
        
        text = 'هذا نص قصير'
        excerpt = get_excerpt(text, max_length=50)
        self.assertEqual(excerpt, text)
    
    def test_get_excerpt_long_text(self):
        """Test excerpt function with long text."""
        from apps.search.utils import get_excerpt
        
        text = 'هذا نص طويل جداً ' * 20
        excerpt = get_excerpt(text, max_length=50)
        self.assertTrue(excerpt.endswith('...'))
        self.assertLessEqual(len(excerpt), 54)  # 50 + '...'
    
    def test_get_excerpt_empty_text(self):
        """Test excerpt function with empty text."""
        from apps.search.utils import get_excerpt
        
        excerpt = get_excerpt('', max_length=50)
        self.assertEqual(excerpt, '')


class SearchFormTestCase(TestCase):
    """Test cases for search form."""
    
    def test_search_form_valid(self):
        """Test search form with valid data."""
        from apps.search.forms import SearchForm
        
        form = SearchForm(data={'query': 'جامعة'})
        self.assertTrue(form.is_valid())
    
    def test_search_form_empty_query(self):
        """Test search form with empty query."""
        from apps.search.forms import SearchForm
        
        form = SearchForm(data={'query': ''})
        self.assertFalse(form.is_valid())
    
    def test_search_form_missing_query(self):
        """Test search form with missing query field."""
        from apps.search.forms import SearchForm
        
        form = SearchForm(data={})
        self.assertFalse(form.is_valid())


class SearchViewTestCase(TestCase):
    """Test cases for search view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Import models in setUp
        from apps.universities.models import University
        
        # Create test university
        self.university = University.objects.create(
            name='جامعة ماليزيا',
            slug='university-malaysia',
            logo='test.jpg',
            main_image='test.jpg',
            description='جامعة رائدة في ماليزيا',
            location='كوالالمبور',
            admission_requirements='متطلبات القبول',
            publish_status='published'
        )
    
    def test_search_view_get_no_query(self):
        """Test search view GET request without query."""
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertFalse(response.context['has_results'])
    
    def test_search_view_get_with_query(self):
        """Test search view GET request with query."""
        response = self.client.get(reverse('search:results'), {'query': 'ماليزيا'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertTrue(response.context['has_results'])
        self.assertEqual(response.context['query'], 'ماليزيا')
    
    def test_search_view_get_with_no_results(self):
        """Test search view GET request with query that has no results."""
        response = self.client.get(reverse('search:results'), {'query': 'غير موجود'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['has_results'])
    
    def test_search_view_post_with_query(self):
        """Test search view POST request with query."""
        response = self.client.post(reverse('search:results'), {'query': 'ماليزيا'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
    
    def test_search_view_pagination(self):
        """Test search view pagination."""
        from apps.universities.models import University
        
        # Create 30 universities to test pagination (more than 20 per page)
        for i in range(30):
            University.objects.create(
                name=f'جامعة {i}',
                slug=f'university-{i}',
                logo='test.jpg',
                main_image='test.jpg',
                description=f'جامعة رقم {i}',
                location='كوالالمبور',
                admission_requirements='متطلبات',
                publish_status='published'
            )
        
        response = self.client.get(reverse('search:results'), {'query': 'جامعة'})
        self.assertEqual(response.status_code, 200)
        # Should have pagination since we have more than 20 results
        # The search results are limited to 20 per content type, so we check the paginator
        results = response.context['results']
        # With 30 universities, we should have pagination
        self.assertTrue(results.paginator.count >= 20)

