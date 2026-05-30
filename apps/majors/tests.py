"""
Tests for Major model.
"""
from django.test import TestCase
from django.urls import reverse


class MajorModelTest(TestCase):
    """Test cases for Major model."""

    def setUp(self):
        """Set up test data."""
        from apps.majors.models import Major
        from apps.core.models import PublishStatus
        
        self.major = Major.objects.create(
            name='هندسة البرمجيات',
            slug='software-engineering',
            description='تخصص هندسة البرمجيات يركز على تطوير البرامج',
            study_duration='4 سنوات',
            tuition_fees='15,000 - 25,000 رنجت سنوياً',
            study_language='الإنجليزية',
            practical_training='متاح في السنة الأخيرة',
            career_opportunities='فرص عمل متعددة في شركات التكنولوجيا',
            why_study_section='هذا التخصص يوفر مهارات عملية',
            how_to_apply_section='يمكنك التقديم عبر الموقع الرسمي',
            publish_status=PublishStatus.PUBLISHED
        )

    def test_major_creation(self):
        """Test creating a major."""
        self.assertEqual(self.major.name, 'هندسة البرمجيات')
        self.assertEqual(self.major.slug, 'software-engineering')
        self.assertTrue(self.major.is_published)

    def test_major_string_representation(self):
        """Test string representation of major."""
        self.assertEqual(str(self.major), 'هندسة البرمجيات')

    def test_major_get_absolute_url(self):
        """Test get_absolute_url method."""
        # Note: This test verifies the method exists and returns the expected format
        # The actual URL routing is tested in task 5.6 (public views)
        url = self.major.get_absolute_url()
        self.assertIn(self.major.slug, url)
        self.assertIn('majors', url)

    def test_major_timestamps(self):
        """Test that timestamps are set correctly."""
        self.assertIsNotNone(self.major.created_at)
        self.assertIsNotNone(self.major.updated_at)

    def test_major_seo_fields(self):
        """Test SEO fields are available."""
        self.major.meta_title = 'هندسة البرمجيات - تخصص متقدم'
        self.major.meta_description = 'تعرف على تخصص هندسة البرمجيات'
        self.major.focus_keyword = 'هندسة برمجيات'
        self.major.save()
        
        self.assertEqual(self.major.meta_title, 'هندسة البرمجيات - تخصص متقدم')
        self.assertEqual(self.major.meta_description, 'تعرف على تخصص هندسة البرمجيات')
        self.assertEqual(self.major.focus_keyword, 'هندسة برمجيات')

    def test_major_publish_status(self):
        """Test publish status functionality."""
        self.assertTrue(self.major.is_published)
        
        self.major.unpublish()
        self.assertFalse(self.major.is_published)
        
        self.major.publish()
        self.assertTrue(self.major.is_published)

    def test_major_slug_change_detection(self):
        """Test slug change detection for redirect creation."""
        old_slug = self.major.slug
        self.major.slug = 'new-software-engineering'
        self.major.save()
        
        # Check that _old_slug was set
        self.assertEqual(self.major._old_slug, old_slug)

    def test_major_quick_info_fields(self):
        """Test quick information fields."""
        self.assertEqual(self.major.tuition_fees, '15,000 - 25,000 رنجت سنوياً')
        self.assertEqual(self.major.study_language, 'الإنجليزية')
        self.assertEqual(self.major.practical_training, 'متاح في السنة الأخيرة')
        self.assertIn('فرص عمل', self.major.career_opportunities)

    def test_major_content_sections(self):
        """Test content section fields."""
        self.assertIn('مهارات عملية', self.major.why_study_section)
        self.assertIn('الموقع الرسمي', self.major.how_to_apply_section)

    def test_major_relationships(self):
        """Test ManyToMany relationships."""
        # Test that relationships can be accessed
        self.assertEqual(self.major.best_universities.count(), 0)
        self.assertEqual(self.major.cheap_universities.count(), 0)
        self.assertEqual(self.major.related_articles.count(), 0)

    def test_major_get_meta_title(self):
        """Test get_meta_title method."""
        # Without meta_title set, should return name
        self.assertEqual(self.major.get_meta_title(), self.major.name)
        
        # With meta_title set, should return meta_title
        self.major.meta_title = 'Custom SEO Title'
        self.assertEqual(self.major.get_meta_title(), 'Custom SEO Title')

    def test_major_get_meta_description(self):
        """Test get_meta_description method."""
        # Without meta_description set, should return description[:160]
        self.assertEqual(self.major.get_meta_description(), self.major.description)
        
        # With meta_description set, should return meta_description
        self.major.meta_description = 'Custom SEO Description'
        self.assertEqual(self.major.get_meta_description(), 'Custom SEO Description')

    def test_major_get_robots_content(self):
        """Test get_robots_content method."""
        # Default should be 'index, follow'
        self.assertEqual(self.major.get_robots_content(), 'index, follow')
        
        # Test with robots_index=False
        self.major.robots_index = False
        self.assertEqual(self.major.get_robots_content(), 'noindex, follow')
        
        # Test with robots_follow=False
        self.major.robots_index = True
        self.major.robots_follow = False
        self.assertEqual(self.major.get_robots_content(), 'index, nofollow')

    def test_major_unpublished_not_visible(self):
        """Test that unpublished majors are not visible."""
        unpublished_major = Major.objects.create(
            name='تخصص غير منشور',
            slug='unpublished-major',
            description='وصف التخصص',
            study_duration='4 سنوات',
            publish_status=PublishStatus.UNPUBLISHED
        )
        
        self.assertFalse(unpublished_major.is_published)
        self.assertEqual(unpublished_major.publish_status, PublishStatus.UNPUBLISHED)


class MajorPublicViewsTest(TestCase):
    """Test cases for Major public views."""

    def setUp(self):
        """Set up test data."""
        from apps.majors.models import Major, SubjectsTable, SalaryTable, CountriesTable
        from apps.core.models import PublishStatus
        
        # Create published major
        self.major = Major.objects.create(
            name='هندسة البرمجيات',
            slug='software-engineering',
            description='تخصص هندسة البرمجيات يركز على تطوير البرامج',
            study_duration='4 سنوات',
            tuition_fees='15,000 - 25,000 رنجت سنوياً',
            study_language='الإنجليزية',
            practical_training='متاح في السنة الأخيرة',
            career_opportunities='فرص عمل متعددة في شركات التكنولوجيا',
            why_study_section='هذا التخصص يوفر مهارات عملية',
            how_to_apply_section='يمكنك التقديم عبر الموقع الرسمي',
            publish_status=PublishStatus.PUBLISHED
        )
        
        # Create unpublished major
        self.unpublished_major = Major.objects.create(
            name='تخصص غير منشور',
            slug='unpublished-major',
            description='وصف التخصص',
            study_duration='4 سنوات',
            publish_status=PublishStatus.UNPUBLISHED
        )
        
        # Create dynamic tables
        self.subjects_table = SubjectsTable.objects.create(
            major=self.major,
            academic_year='السنة الأولى',
            subjects='البرمجة، الرياضيات، الخوارزميات',
            sort_order=1
        )
        
        self.salary_table = SalaryTable.objects.create(
            major=self.major,
            job_title='مهندس برمجيات',
            average_monthly_salary='5,000 - 8,000 رنجت ماليزي',
            sort_order=1
        )
        
        self.countries_table = CountriesTable.objects.create(
            major=self.major,
            destination='ماليزيا',
            study_duration='4 سنوات',
            annual_fees='20,000 - 30,000 رنجت ماليزي',
            living_cost='1,500 - 2,500 رنجت ماليزي شهرياً',
            sort_order=1
        )

    def test_major_list_view_url(self):
        """Test major list view URL."""
        response = self.client.get(reverse('majors:list'))
        self.assertEqual(response.status_code, 200)

    def test_major_list_view_template(self):
        """Test major list view uses correct template."""
        response = self.client.get(reverse('majors:list'))
        self.assertTemplateUsed(response, 'majors/list.html')

    def test_major_list_view_context(self):
        """Test major list view context."""
        response = self.client.get(reverse('majors:list'))
        self.assertIn('majors', response.context)
        self.assertEqual(len(response.context['majors']), 1)
        self.assertEqual(response.context['majors'][0].name, 'هندسة البرمجيات')
        self.assertEqual(response.context['clear_url'], reverse('majors:list'))

    def test_major_list_view_only_published(self):
        """Test that only published majors are shown in list."""
        response = self.client.get(reverse('majors:list'))
        majors = response.context['majors']
        
        # Should only contain published major
        self.assertEqual(majors.count(), 1)
        self.assertTrue(majors[0].is_published)

    def test_major_list_view_pagination(self):
        """Test major list view pagination."""
        # Create 25 majors to test pagination
        for i in range(24):
            Major.objects.create(
                name=f'تخصص {i}',
                slug=f'major-{i}',
                description='وصف التخصص',
                study_duration='4 سنوات',
                publish_status=PublishStatus.PUBLISHED
            )
        
        response = self.client.get(reverse('majors:list'))
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['majors']), 20)

    def test_major_detail_view_url(self):
        """Test major detail view URL."""
        url = reverse('majors:detail', kwargs={'slug': self.major.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_major_detail_view_template(self):
        """Test major detail view uses correct template."""
        url = reverse('majors:detail', kwargs={'slug': self.major.slug})
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'majors/detail.html')

    def test_major_detail_view_context(self):
        """Test major detail view context."""
        url = reverse('majors:detail', kwargs={'slug': self.major.slug})
        response = self.client.get(url)
        
        self.assertIn('major', response.context)
        self.assertEqual(response.context['major'].name, 'هندسة البرمجيات')

    def test_major_detail_view_dynamic_tables(self):
        """Test major detail view includes dynamic tables."""
        url = reverse('majors:detail', kwargs={'slug': self.major.slug})
        response = self.client.get(url)
        
        self.assertIn('subjects_tables', response.context)
        self.assertIn('salary_tables', response.context)
        self.assertIn('countries_tables', response.context)
        
        self.assertEqual(len(response.context['subjects_tables']), 1)
        self.assertEqual(len(response.context['salary_tables']), 1)
        self.assertEqual(len(response.context['countries_tables']), 1)

    def test_major_detail_view_unpublished_not_found(self):
        """Test that unpublished major returns 404."""
        url = reverse('majors:detail', kwargs={'slug': self.unpublished_major.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_major_detail_view_content_rendering(self):
        """Test that major detail view renders content correctly."""
        url = reverse('majors:detail', kwargs={'slug': self.major.slug})
        response = self.client.get(url)
        
        # Check that content is rendered
        self.assertContains(response, self.major.name)
        self.assertContains(response, self.major.study_duration)
        self.assertContains(response, self.major.tuition_fees)

    def test_major_detail_view_tables_rendering(self):
        """Test that dynamic tables are rendered correctly."""
        url = reverse('majors:detail', kwargs={'slug': self.major.slug})
        response = self.client.get(url)
        
        # Check that table content is rendered
        self.assertContains(response, self.subjects_table.academic_year)
        self.assertContains(response, self.salary_table.job_title)
        self.assertContains(response, self.countries_table.destination)

    def test_major_detail_view_query_optimization(self):
        """Test that detail view uses prefetch_related for optimization."""
        url = reverse('majors:detail', kwargs={'slug': self.major.slug})
        
        # This test verifies the view uses prefetch_related for optimization
        # Expected queries: 1 redirect check + 1 major + 3 dynamic tables + 3 relationships = 8
        with self.assertNumQueries(8):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_major_list_view_ordering(self):
        """Test that majors are ordered by name."""
        Major.objects.create(
            name='أ - تخصص',
            slug='a-major',
            description='وصف',
            study_duration='4 سنوات',
            publish_status=PublishStatus.PUBLISHED
        )
        
        response = self.client.get(reverse('majors:list'))
        majors = list(response.context['majors'])
        
        # Check that majors are ordered by name
        for i in range(len(majors) - 1):
            self.assertLessEqual(majors[i].name, majors[i + 1].name)

    def test_major_detail_view_tables_ordering(self):
        """Test that dynamic tables are ordered by sort_order."""
        # Create additional tables with different sort orders
        SubjectsTable.objects.create(
            major=self.major,
            academic_year='السنة الثانية',
            subjects='قواعد البيانات، الشبكات',
            sort_order=2
        )
        
        url = reverse('majors:detail', kwargs={'slug': self.major.slug})
        response = self.client.get(url)
        
        subjects = list(response.context['subjects_tables'])
        # Check that tables are ordered by sort_order
        self.assertEqual(subjects[0].sort_order, 1)
        self.assertEqual(subjects[1].sort_order, 2)

