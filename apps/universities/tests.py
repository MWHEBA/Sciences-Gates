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
        assert response.context['clear_url'] == reverse('universities:list')

    def test_list_view_filter_search_query(self):
        """Test that list view filters by search query (q)."""
        # Search for something that matches the name
        response = self.client.get(reverse('universities:list') + '?q=ماليزيا')
        assert len(response.context['universities']) == 1
        
        # Search for something that does not match
        response = self.client.get(reverse('universities:list') + '?q=أمريكا')
        assert len(response.context['universities']) == 0

    def test_list_view_filter_type(self):
        """Test that list view filters by university type."""
        # By default, university has 'private' type
        response = self.client.get(reverse('universities:list') + '?type=private')
        assert len(response.context['universities']) == 1
        
        response = self.client.get(reverse('universities:list') + '?type=public')
        assert len(response.context['universities']) == 0

    def test_list_view_filter_city(self):
        """Test that list view filters by city mapping."""
        # Location contains 'كوالالمبور', which corresponds to city code 'kl'
        response = self.client.get(reverse('universities:list') + '?city=kl')
        assert len(response.context['universities']) == 1
        
        response = self.client.get(reverse('universities:list') + '?city=selangor')
        assert len(response.context['universities']) == 0


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
    
    def test_detail_view_shows_tabbed_admission_requirements(self):
        """Test that detail view displays the program-specific admission requirements when present."""
        self.university.admission_requirements_bachelor = 'شروط البكالوريوس المميزة'
        self.university.admission_requirements_master = 'شروط الماجستير المميزة'
        self.university.admission_requirements_phd = 'شروط الدكتوراه المميزة'
        self.university.save()
        
        response = self.client.get(
            reverse('universities:detail', kwargs={'slug': self.university.slug})
        )
        content = response.content.decode()
        assert 'شروط البكالوريوس المميزة' in content
        assert 'شروط الماجستير المميزة' in content
        assert 'شروط الدكتوراه المميزة' in content

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
    
    def test_detail_view_query_optimization(self, django_assert_num_queries):
        """Test that detail view uses optimized queries."""
        with django_assert_num_queries(9):
            response = self.client.get(
                reverse('universities:detail', kwargs={'slug': self.university.slug})
            )
            university = response.context['university']
            list(university.faculties.all())
            list(university.faqs.all())


@pytest.mark.django_db
class TestUniversityAttachment:
    """Test UniversityAttachment model and detail view integration."""

    def test_attachment_saves_file_size_automatically(self):
        """Test that file_size is computed and saved automatically."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import University, UniversityAttachment

        uni = University.objects.create(
            name='Test University',
            slug='test-uni',
            logo='logo.png',
            main_image='main.png',
            description='Test description',
            location='Test location'
        )

        test_file = SimpleUploadedFile("brochure.pdf", b"file content here", content_type="application/pdf")
        attachment = UniversityAttachment.objects.create(
            university=uni,
            title='دليل الجامعة',
            file=test_file
        )

        assert attachment.file_size == len(b"file content here")
        assert attachment.title == 'دليل الجامعة'
        assert 'brochure' in attachment.file.name
        assert attachment.file.name.endswith('.pdf')

        # Clean up file
        attachment.delete()

    def test_detail_view_renders_attachments(self, client):
        """Test that the public detail view lists uploaded attachments."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import University, UniversityAttachment

        uni = University.objects.create(
            name='Published Uni',
            slug='published-uni',
            logo='logo.png',
            main_image='main.png',
            description='Test description',
            location='Test location',
            publish_status='published'
        )

        test_file = SimpleUploadedFile("brochure.pdf", b"content", content_type="application/pdf")
        attachment = UniversityAttachment.objects.create(
            university=uni,
            title='دليل الجامعة المرفق',
            file=test_file
        )

        response = client.get(reverse('universities:detail', kwargs={'slug': uni.slug}))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'دليل الجامعة المرفق' in content

        # Clean up file
        attachment.delete()


@pytest.mark.django_db
class TestProgramYearlyFees:
    """Test Program model yearly_fees field and forms."""

    def test_yearly_fees_model_storage(self):
        """Test storing and retrieving yearly_fees JSON on Program model."""
        from .models import University, Faculty, Program

        uni = University.objects.create(
            name='Test Uni',
            slug='test-uni',
            description='Test',
            location='Test'
        )
        faculty = Faculty.objects.create(
            university=uni,
            name='Faculty of Engineering'
        )
        program = Program.objects.create(
            faculty=faculty,
            name='Computer Engineering',
            duration='4 years',
            tuition_fees='15,000 USD',
            yearly_fees={
                "السنة الأولى": "5,424",
                "السنة الثانية": "4,964"
            }
        )

        # Reload from DB
        program.refresh_from_db()
        assert program.yearly_fees == {
            "السنة الأولى": "5,424",
            "السنة الثانية": "4,964"
        }

    def test_program_form_yearly_fees_parsing(self):
        """Test that ProgramForm correctly parses textarea yearly_fees and saves as dict."""
        from apps.dashboard.forms.university import ProgramForm
        from .models import University, Faculty

        uni = University.objects.create(
            name='Test Uni',
            slug='test-uni',
            description='Test',
            location='Test'
        )
        faculty = Faculty.objects.create(
            university=uni,
            name='Faculty of Science'
        )

        # Test valid input
        form_data = {
            'name': 'Physics',
            'duration': '3 years',
            'tuition_fees': '5,000 USD',
            'yearly_fees': 'السنة الأولى: 5,424\nالسنة الثانية: 4,964\nالسنة الثالثة: 6,313',
            'sort_order': 0,
        }
        form = ProgramForm(data=form_data)
        assert form.is_valid()
        program = form.save(commit=False)
        program.faculty = faculty
        program.save()

        assert program.yearly_fees == {
            "السنة الأولى": "5,424",
            "السنة الثانية": "4,964",
            "السنة الثالثة": "6,313"
        }

        # Test invalid input (missing colon)
        invalid_data = form_data.copy()
        invalid_data['yearly_fees'] = 'السنة الأولى 5,424'
        form = ProgramForm(data=invalid_data)
        assert not form.is_valid()
        assert 'yearly_fees' in form.errors

    def test_program_form_initial_value(self):
        """Test that ProgramForm populates initial yearly_fees string from JSON."""
        from apps.dashboard.forms.university import ProgramForm
        from .models import University, Faculty, Program

        uni = University.objects.create(
            name='Test Uni',
            slug='test-uni',
            description='Test',
            location='Test'
        )
        faculty = Faculty.objects.create(
            university=uni,
            name='Faculty of Arts'
        )
        program = Program.objects.create(
            faculty=faculty,
            name='History',
            duration='3 years',
            tuition_fees='4,000 USD',
            yearly_fees={
                "السنة الأولى": "4,000",
                "السنة الثانية": "4,200"
            }
        )

        form = ProgramForm(instance=program)
        assert form.initial['yearly_fees'] == "السنة الأولى: 4,000\nالسنة الثانية: 4,200"


