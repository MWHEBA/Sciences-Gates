from django.test import TestCase, Client
from django.urls import reverse
from .models import Institute


class InstituteListViewTest(TestCase):
    """Test cases for InstituteListView."""
    
    def setUp(self):
        """Set up test data."""
        from .models import Institute
        
        self.client = Client()
        
        # Create published institutes
        self.institute1 = Institute.objects.create(
            name='معهد التكنولوجيا',
            slug='tech-institute',
            main_image='test.jpg',
            description='معهد متخصص في التكنولوجيا',
            registration_requirements='شروط التسجيل',
            publish_status='published'
        )
        
        self.institute2 = Institute.objects.create(
            name='معهد اللغات',
            slug='language-institute',
            main_image='test.jpg',
            description='معهد متخصص في اللغات',
            registration_requirements='شروط التسجيل',
            publish_status='published'
        )
        
        # Create unpublished institute (should not appear)
        self.institute3 = Institute.objects.create(
            name='معهد غير منشور',
            slug='unpublished-institute',
            main_image='test.jpg',
            description='معهد غير منشور',
            registration_requirements='شروط التسجيل',
            publish_status='unpublished'
        )
    
    def test_list_view_url_exists(self):
        """Test that the list view URL exists."""
        response = self.client.get(reverse('institutes:list'))
        self.assertEqual(response.status_code, 200)
    
    def test_list_view_uses_correct_template(self):
        """Test that the list view uses the correct template."""
        response = self.client.get(reverse('institutes:list'))
        self.assertTemplateUsed(response, 'institutes/list.html')
    
    def test_list_view_shows_only_published_institutes(self):
        """Test that only published institutes are displayed."""
        response = self.client.get(reverse('institutes:list'))
        self.assertEqual(len(response.context['institutes']), 2)
        self.assertIn(self.institute1, response.context['institutes'])
        self.assertIn(self.institute2, response.context['institutes'])
        self.assertNotIn(self.institute3, response.context['institutes'])
    
    def test_list_view_pagination(self):
        """Test that pagination works correctly."""
        # Create 25 institutes to test pagination
        for i in range(3, 26):
            Institute.objects.create(
                name=f'معهد {i}',
                slug=f'institute-{i}',
                main_image='test.jpg',
                description='وصف',
                registration_requirements='شروط',
                publish_status='published'
            )
        
        response = self.client.get(reverse('institutes:list'))
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['institutes']), 20)
    
    def test_list_view_context_data(self):
        """Test that context data is correct."""
        response = self.client.get(reverse('institutes:list'))
        self.assertIn('institutes', response.context)
        self.assertIn('is_paginated', response.context)
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['clear_url'], reverse('institutes:list'))


class InstituteDetailViewTest(TestCase):
    """Test cases for InstituteDetailView."""
    
    def setUp(self):
        """Set up test data."""
        from .models import Institute, Course
        
        self.client = Client()
        
        # Create published institute
        self.institute = Institute.objects.create(
            name='معهد التكنولوجيا',
            slug='tech-institute',
            main_image='test.jpg',
            description='وصف المعهد',
            registration_requirements='شروط التسجيل',
            registration_section='خطوات التسجيل',
            publish_status='published'
        )
        
        # Create courses
        self.course1 = Course.objects.create(
            institute=self.institute,
            name='دورة البرمجة',
            duration='3 أشهر',
            fees='5000 رنجت',
            description='وصف الدورة',
            notes='ملاحظات'
        )
        
        self.course2 = Course.objects.create(
            institute=self.institute,
            name='دورة الويب',
            duration='4 أشهر',
            fees='6000 رنجت',
            description='وصف الدورة',
            notes=''
        )
        
        # Create unpublished institute
        self.unpublished_institute = Institute.objects.create(
            name='معهد غير منشور',
            slug='unpublished-institute',
            main_image='test.jpg',
            description='وصف',
            registration_requirements='شروط',
            publish_status='unpublished'
        )
    
    def test_detail_view_url_exists(self):
        """Test that the detail view URL exists."""
        url = reverse('institutes:detail', kwargs={'slug': self.institute.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_detail_view_uses_correct_template(self):
        """Test that the detail view uses the correct template."""
        url = reverse('institutes:detail', kwargs={'slug': self.institute.slug})
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'institutes/detail.html')
    
    def test_detail_view_shows_institute_data(self):
        """Test that institute data is displayed correctly."""
        url = reverse('institutes:detail', kwargs={'slug': self.institute.slug})
        response = self.client.get(url)
        self.assertEqual(response.context['institute'], self.institute)
        self.assertContains(response, self.institute.name)
        self.assertContains(response, self.institute.description)
    
    def test_detail_view_shows_courses(self):
        """Test that courses are displayed."""
        url = reverse('institutes:detail', kwargs={'slug': self.institute.slug})
        response = self.client.get(url)
        self.assertEqual(len(response.context['courses']), 2)
        self.assertIn(self.course1, response.context['courses'])
        self.assertIn(self.course2, response.context['courses'])
        self.assertContains(response, self.course1.name)
        self.assertContains(response, self.course2.name)
    
    def test_detail_view_unpublished_institute_not_found(self):
        """Test that unpublished institutes return 404."""
        url = reverse('institutes:detail', kwargs={'slug': self.unpublished_institute.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_detail_view_context_data(self):
        """Test that context data is correct."""
        url = reverse('institutes:detail', kwargs={'slug': self.institute.slug})
        response = self.client.get(url)
        self.assertIn('institute', response.context)
        self.assertIn('courses', response.context)
    
    def test_detail_view_registration_section(self):
        """Test that registration section is displayed."""
        url = reverse('institutes:detail', kwargs={'slug': self.institute.slug})
        response = self.client.get(url)
        self.assertContains(response, self.institute.registration_section)
    
    def test_detail_view_query_optimization(self):
        """Test that queries are optimized with prefetch_related."""
        url = reverse('institutes:detail', kwargs={'slug': self.institute.slug})
        
        # This test verifies that prefetch_related is working
        # by checking that accessing related objects doesn't cause additional queries
        # Queries: 1 for redirect check, 1 for institute, 1 for courses, 1 for articles
        with self.assertNumQueries(4):
            response = self.client.get(url)
            # Access the courses to ensure they're prefetched
            list(response.context['courses'])

