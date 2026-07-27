from django.test import TestCase, Client
from django.urls import reverse
from .models import Institute, Course


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
            publish_status='published'
        )
        
        self.institute2 = Institute.objects.create(
            name='معهد اللغات',
            slug='language-institute',
            main_image='test.jpg',
            description='معهد متخصص في اللغات',
            publish_status='published'
        )
        
        # Create unpublished institute (should not appear)
        self.institute3 = Institute.objects.create(
            name='معهد غير منشور',
            slug='unpublished-institute',
            main_image='test.jpg',
            description='معهد غير منشور',
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
        from apps.core.models import SiteSettings
        
        self.client = Client()
        SiteSettings.objects.create(
            site_name='Science Gates',
            registration_steps_title='خطوات التسجيل'
        )
        
        # Create published institute
        self.institute = Institute.objects.create(
            name='معهد التكنولوجيا',
            slug='tech-institute',
            main_image='test.jpg',
            description='وصف المعهد',
            publish_status='published'
        )
        
        # Create courses
        self.course1 = Course.objects.create(
            institute=self.institute,
            course_type='regular',
            duration='3 أشهر',
            fees_myr='3,400',
            fees_usd='857',
            fees_sar='3,216',
            visa_duration='بدون تأشيرة',
            sort_order=1
        )
        
        self.course2 = Course.objects.create(
            institute=self.institute,
            course_type='regular',
            duration='4 أشهر',
            fees_myr='6,300',
            fees_usd='1,588',
            fees_sar='5,960',
            visa_duration='بدون تأشيرة',
            sort_order=2
        )
        
        # Create unpublished institute
        self.unpublished_institute = Institute.objects.create(
            name='معهد غير منشور',
            slug='unpublished-institute',
            main_image='test.jpg',
            description='وصف',
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
        self.assertContains(response, self.course1.duration)
        self.assertContains(response, self.course1.fees_myr)

    def test_detail_view_shows_course_type_groups(self):
        """Test that courses are grouped and sorted by type."""
        # Create an intensive course
        intensive_course = Course.objects.create(
            institute=self.institute,
            course_type='intensive',
            duration='شهر واحد مكثف',
            fees_myr='4,000',
            fees_usd='1,000',
            fees_sar='3,750',
            visa_duration='بدون تأشيرة',
            sort_order=0
        )
        url = reverse('institutes:detail', kwargs={'slug': self.institute.slug})
        response = self.client.get(url)
        courses = response.context['courses']
        # Verification: courses are sorted (regular first, then intensive)
        self.assertEqual(courses[0], self.course1)
        self.assertEqual(courses[1], self.course2)
        self.assertEqual(courses[2], intensive_course)
        # Check template rendering contains headers
        self.assertContains(response, 'مدة الكورس (4 ساعات / يوم)')
        self.assertContains(response, 'مدة الكورس (5 ساعات / يوم)')
    
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
        self.assertContains(response, 'تقديم الطلب والوثائق')
    
    def test_detail_view_query_optimization(self):
        """Test that queries are optimized with prefetch_related."""
        url = reverse('institutes:detail', kwargs={'slug': self.institute.slug})
        
        # This test verifies that prefetch_related is working
        # by checking that accessing related objects doesn't cause additional queries
        # Queries: 1 for redirect check, 1 for institute, 1 for courses, 1 for articles, 1 for tags, 1 for site settings, 1 for attachments, 1 for faqs
        from django.core.cache import cache
        cache.clear()
        with self.assertNumQueries(8):
            response = self.client.get(url)
            # Access the courses to ensure they're prefetched
            list(response.context['courses'])


class InstituteAttachmentTestCase(TestCase):
    """Test cases for InstituteAttachment model and view integration."""

    def test_attachment_saves_file_size_automatically(self):
        """Test that file_size is computed and saved automatically."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Institute, InstituteAttachment

        inst = Institute.objects.create(
            name='Test Institute',
            slug='test-inst',
            main_image='main.png',
            description='Test description'
        )

        test_file = SimpleUploadedFile("brochure.pdf", b"file content here", content_type="application/pdf")
        attachment = InstituteAttachment.objects.create(
            institute=inst,
            title='دليل المعهد',
            file=test_file
        )

        self.assertEqual(attachment.file_size, len(b"file content here"))
        self.assertEqual(attachment.title, 'دليل المعهد')
        self.assertTrue('brochure' in attachment.file.name)
        self.assertTrue(attachment.file.name.endswith('.pdf'))

        # Clean up file
        attachment.delete()

    def test_detail_view_renders_attachments(self):
        """Test that the public detail view lists uploaded attachments."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Institute, InstituteAttachment

        inst = Institute.objects.create(
            name='Published Inst',
            slug='published-inst',
            main_image='main.png',
            description='Test description',
            publish_status='published'
        )

        test_file = SimpleUploadedFile("brochure.pdf", b"content", content_type="application/pdf")
        attachment = InstituteAttachment.objects.create(
            institute=inst,
            title='دليل المعهد المرفق',
            file=test_file
        )

        response = self.client.get(reverse('institutes:detail', kwargs={'slug': inst.slug}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('دليل المعهد المرفق', content)

        # Clean up file
        attachment.delete()

    def test_detail_view_renders_dynamic_fees_info(self):
        """Test that the detail view renders dynamic fees_includes and fees_excludes."""
        from .models import Course

        inst = Institute.objects.create(
            name='معهد اللغات الحديثة',
            slug='modern-lang-inst',
            main_image='main.png',
            description='Test description',
            fees_includes='الكتب الدراسية، والأنشطة الترفيهية',
            fees_excludes='التأمين، ورسوم التسجيل المبدئي',
            publish_status='published'
        )
        
        Course.objects.create(
            institute=inst,
            duration='3 أشهر',
            fees_myr='4,500'
        )

        response = self.client.get(reverse('institutes:detail', kwargs={'slug': inst.slug}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Verify both fields are rendered in the text
        self.assertIn('تشمل الكتب الدراسية، والأنشطة الترفيهية', content)
        self.assertIn('لا تشمل:', content)
        self.assertIn('التأمين، ورسوم التسجيل المبدئي', content)


class InstituteFormTests(TestCase):
    """Test cases for InstituteForm logo validation."""
    
    def test_logo_is_optional_by_default(self):
        """Test that the logo field is optional in manual form submissions."""
        from apps.dashboard.forms.institute import InstituteForm
        
        # Form without logo
        form = InstituteForm(data={
            'name': 'Test Institute',
            'slug': 'test-institute',
            'state': 'kl',
            'city': 'kl',
            'description': 'Test description',
            'publish_status': 'published',
            'imported_main_image_path': '/media/media_library/institute_image/inst-main.png', # bypass main_image validation
        })
        self.assertTrue(form.is_valid() or 'logo' not in form.errors)

    def test_logo_is_not_required_with_imported_logo_path(self):
        """Test that the logo field is optional when imported_logo_path is provided."""
        from apps.dashboard.forms.institute import InstituteForm
        
        # Form without logo file, but with imported_logo_path
        form = InstituteForm(data={
            'name': 'Test Institute',
            'slug': 'test-institute',
            'state': 'kl',
            'city': 'kl',
            'description': 'Test description',
            'publish_status': 'published',
            'imported_logo_path': '/media/media_library/institute_logo/inst-logo.png',
            'imported_main_image_path': '/media/media_library/institute_image/inst-main.png',
        })
        self.assertTrue(form.is_valid() or 'logo' not in form.errors)



