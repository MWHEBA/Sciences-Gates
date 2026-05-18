"""
Tests for university public views.

Converted from Django TestCase to pytest for faster test execution.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestUniversityListView:
    """Test UniversityListView."""
    
    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Set up test data."""
        from .models import University
        
        self.client = client
        
        # Create published university
        self.university = University.objects.create(
            name='جامعة ماليزيا',
            slug='university-malaysia',
            logo='test.png',
            main_image='test.png',
            description='وصف الجامعة',
            location='كوالالمبور',
            admission_requirements='شروط القبول',
            publish_status='published'
        )
        
        # Create unpublished university (should not appear)
        self.unpublished = University.objects.create(
            name='جامعة غير منشورة',
            slug='unpublished-university',
            logo='test.png',
            main_image='test.png',
            description='وصف',
            location='موقع',
            admission_requirements='شروط',
            publish_status='unpublished'
        )
    
    def test_list_view_returns_200(self):
        """Test that list view returns 200 status code."""
        response = self.client.get(reverse('universities:list'))
        assert response.status_code == 200
    
    def test_list_view_uses_correct_template(self):
        """Test that list view uses correct template."""
        response = self.client.get(reverse('universities:list'))
        assert 'universities/list.html' in [t.name for t in response.templates]
    
    def test_list_view_shows_published_only(self):
        """Test that list view shows only published universities."""
        response = self.client.get(reverse('universities:list'))
        assert 'جامعة ماليزيا' in response.content.decode()
        assert 'جامعة غير منشورة' not in response.content.decode()
    
    def test_list_view_context(self):
        """Test that list view provides correct context."""
        response = self.client.get(reverse('universities:list'))
        assert 'universities' in response.context
        assert len(response.context['universities']) == 1
        assert response.context['universities'][0] == self.university


@pytest.mark.django_db
class TestUniversityDetailView:
    """Test UniversityDetailView."""
    
    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Set up test data."""
        from .models import University, Faculty, Program, UniversityFAQ
        
        self.client = client
        
        # Create published university
        self.university = University.objects.create(
            name='جامعة ماليزيا',
            slug='university-malaysia',
            logo='test.png',
            main_image='test.png',
            description='وصف الجامعة',
            location='كوالالمبور',
            video_url='https://www.youtube.com/embed/test',
            admission_requirements='شروط القبول',
            registration_section='خطوات التسجيل',
            publish_status='published'
        )
        
        # Create faculty with programs
        self.faculty = Faculty.objects.create(
            university=self.university,
            name='كلية الهندسة',
            sort_order=1
        )
        
        self.program = Program.objects.create(
            faculty=self.faculty,
            name='برنامج الهندسة المدنية',
            duration='4 سنوات',
            tuition_fees='20,000 رنجت',
            sort_order=1
        )
        
        # Create FAQ
        self.faq = UniversityFAQ.objects.create(
            university=self.university,
            question='ما هي شروط القبول؟',
            answer='شروط القبول هي...',
            sort_order=1
        )
    
    def test_detail_view_returns_200(self):
        """Test that detail view returns 200 status code."""
        response = self.client.get(
            reverse('universities:detail', kwargs={'slug': self.university.slug})
        )
        assert response.status_code == 200
    
    def test_detail_view_uses_correct_template(self):
        """Test that detail view uses correct template."""
        response = self.client.get(
            reverse('universities:detail', kwargs={'slug': self.university.slug})
        )
        assert 'universities/detail.html' in [t.name for t in response.templates]
    
    def test_detail_view_shows_university_info(self):
        """Test that detail view displays university information."""
        response = self.client.get(
            reverse('universities:detail', kwargs={'slug': self.university.slug})
        )
        assert 'جامعة ماليزيا' in response.content.decode()
        assert 'كوالالمبور' in response.content.decode()
        assert 'وصف الجامعة' in response.content.decode()
    
    def test_detail_view_shows_faculties_and_programs(self):
        """Test that detail view displays faculties and programs."""
        response = self.client.get(
            reverse('universities:detail', kwargs={'slug': self.university.slug})
        )
        assert 'كلية الهندسة' in response.content.decode()
        assert 'برنامج الهندسة المدنية' in response.content.decode()
        assert '4 سنوات' in response.content.decode()
    
    def test_detail_view_shows_faq(self):
        """Test that detail view displays FAQ."""
        response = self.client.get(
            reverse('universities:detail', kwargs={'slug': self.university.slug})
        )
        assert 'ما هي شروط القبول؟' in response.content.decode()
        assert 'شروط القبول هي...' in response.content.decode()
    
    def test_detail_view_context(self):
        """Test that detail view provides correct context."""
        response = self.client.get(
            reverse('universities:detail', kwargs={'slug': self.university.slug})
        )
        assert 'university' in response.context
        assert 'faculties' in response.context
        assert 'faqs' in response.context
        assert response.context['university'] == self.university
        assert len(response.context['faculties']) == 1
        assert len(response.context['faqs']) == 1
    
    def test_detail_view_unpublished_returns_404(self):
        """Test that unpublished university returns 404."""
        from .models import University
        
        unpublished = University.objects.create(
            name='جامعة غير منشورة',
            slug='unpublished-university',
            logo='test.png',
            main_image='test.png',
            description='وصف',
            location='موقع',
            admission_requirements='شروط',
            publish_status='unpublished'
        )
        
        response = self.client.get(
            reverse('universities:detail', kwargs={'slug': unpublished.slug})
        )
        assert response.status_code == 404
    
    def test_detail_view_query_optimization(self):
        """Test that detail view uses optimized queries."""
        with self.assertNumQueries(7):
            response = self.client.get(
                reverse('universities:detail', kwargs={'slug': self.university.slug})
            )
            university = response.context['university']
            list(university.faculties.all())
            list(university.faqs.all())
