"""
Tests for WordPress importer services.
اختبارات خدمات استيراد المحتوى من WordPress
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.models import MediaFile
from apps.importer.services.content_mapper import ContentMapper
from apps.importer.services.image_downloader import download_and_optimize_image


class ContentMapperAltTextTests(TestCase):
    """
    Tests for auto-generation of alt text when WordPress provides empty alt text.
    اختبارات توليد النص البديل التلقائي عندما يكون فارغاً من WordPress
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.mapper = ContentMapper()

    def test_empty_alt_text_generates_fallback_for_logo(self):
        """
        Test that when imported logo has empty alt text,
        form_initial gets generated logo_alt and confidence becomes 'generated'.
        """
        # Create a MediaFile with empty alt text (simulating WordPress import)
        media_file = MediaFile.objects.create(
            original_filename='logo.png',
            file='test_logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='',  # Empty alt text from WordPress
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        wp_data = {
            'content_type': 'university',
            'name': 'جامعة مالايا الماليزية',
            'slug': 'university-of-malaya',
            'fields': {},
            'seo': {},
            'faculties': [],
            'faqs': []
        }

        downloaded_images = {
            'logo': media_file,
        }

        result = self.mapper.map_data(wp_data, downloaded_images, [])

        # Assert logo_alt was auto-generated
        self.assertEqual(
            result['form_initial']['logo_alt'],
            'شعار جامعة مالايا الماليزية'
        )
        
        # Assert confidence is marked as 'generated', not 'high'
        self.assertEqual(
            result['confidence']['logo_alt'],
            'generated'
        )

    def test_empty_alt_text_generates_fallback_for_main_image(self):
        """
        Test that when imported main_image has empty alt text,
        form_initial gets entity name as alt text and confidence becomes 'generated'.
        """
        media_file = MediaFile.objects.create(
            original_filename='main.jpg',
            file='test_main.jpg',
            file_size=2048,
            width=800,
            height=600,
            alt_text='',  # Empty alt text from WordPress
            source_type=MediaFile.SourceType.UNIVERSITY_IMAGE,
            uploaded_by=self.user
        )

        wp_data = {
            'content_type': 'university',
            'name': 'جامعة التكنولوجيا الماليزية',
            'slug': 'utm',
            'fields': {},
            'seo': {},
            'faculties': [],
            'faqs': []
        }

        downloaded_images = {
            'main_image': media_file,
        }

        result = self.mapper.map_data(wp_data, downloaded_images, [])

        # Assert main_image_alt was auto-generated (just the entity name)
        self.assertEqual(
            result['form_initial']['main_image_alt'],
            'جامعة التكنولوجيا الماليزية'
        )
        
        # Assert confidence is marked as 'generated'
        self.assertEqual(
            result['confidence']['main_image_alt'],
            'generated'
        )

    def test_real_alt_text_from_wordpress_is_preserved(self):
        """
        Test that when WordPress provides real alt text, it is kept exactly
        and confidence is marked as 'high'.
        """
        media_file = MediaFile.objects.create(
            original_filename='logo.png',
            file='test_logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='شعار جامعة مالايا الماليزية - University of Malaya Logo',  # Real alt from WP
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        wp_data = {
            'content_type': 'university',
            'name': 'جامعة مالايا الماليزية',
            'slug': 'university-of-malaya',
            'fields': {},
            'seo': {},
            'faculties': [],
            'faqs': []
        }

        downloaded_images = {
            'logo': media_file,
        }

        result = self.mapper.map_data(wp_data, downloaded_images, [])

        # Assert real alt text is preserved exactly
        self.assertEqual(
            result['form_initial']['logo_alt'],
            'شعار جامعة مالايا الماليزية - University of Malaya Logo'
        )
        
        # Assert confidence is 'high' for real alt text
        self.assertEqual(
            result['confidence']['logo_alt'],
            'high'
        )

    def test_whitespace_only_alt_text_is_treated_as_empty(self):
        """
        Test that alt text containing only whitespace is treated as empty
        and triggers auto-generation.
        """
        media_file = MediaFile.objects.create(
            original_filename='logo.png',
            file='test_logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='   ',  # Whitespace only
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        wp_data = {
            'content_type': 'university',
            'name': 'جامعة بوترا',
            'slug': 'upm',
            'fields': {},
            'seo': {},
            'faculties': [],
            'faqs': []
        }

        downloaded_images = {
            'logo': media_file,
        }

        result = self.mapper.map_data(wp_data, downloaded_images, [])

        # Assert auto-generation happened
        self.assertEqual(
            result['form_initial']['logo_alt'],
            'شعار جامعة بوترا'
        )
        
        self.assertEqual(
            result['confidence']['logo_alt'],
            'generated'
        )

    def test_empty_entity_name_results_in_empty_alt_text(self):
        """
        Test that when entity name is empty, no alt text is generated
        and confidence is 'none'.
        """
        media_file = MediaFile.objects.create(
            original_filename='logo.png',
            file='test_logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='',
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        wp_data = {
            'content_type': 'university',
            'name': '',  # Empty name
            'slug': 'test',
            'fields': {},
            'seo': {},
            'faculties': [],
            'faqs': []
        }

        downloaded_images = {
            'logo': media_file,
        }

        result = self.mapper.map_data(wp_data, downloaded_images, [])

        # Assert no alt text was generated
        self.assertEqual(
            result['form_initial'].get('logo_alt', ''),
            ''
        )
        
        # Assert confidence is 'none'
        self.assertEqual(
            result['confidence']['logo_alt'],
            'none'
        )

    def test_both_logo_and_main_image_with_mixed_alt_text(self):
        """
        Test mixed scenario: logo has real alt text (keep it),
        main_image has empty alt text (generate it).
        """
        logo = MediaFile.objects.create(
            original_filename='logo.png',
            file='test_logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='Official University Logo',  # Real alt text
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        main_image = MediaFile.objects.create(
            original_filename='main.jpg',
            file='test_main.jpg',
            file_size=2048,
            width=800,
            height=600,
            alt_text='',  # Empty alt text
            source_type=MediaFile.SourceType.UNIVERSITY_IMAGE,
            uploaded_by=self.user
        )

        wp_data = {
            'content_type': 'university',
            'name': 'جامعة الملايا',
            'slug': 'um',
            'fields': {},
            'seo': {},
            'faculties': [],
            'faqs': []
        }

        downloaded_images = {
            'logo': logo,
            'main_image': main_image,
        }

        result = self.mapper.map_data(wp_data, downloaded_images, [])

        # Logo: Real alt text preserved
        self.assertEqual(
            result['form_initial']['logo_alt'],
            'Official University Logo'
        )
        self.assertEqual(result['confidence']['logo_alt'], 'high')

        # Main image: Auto-generated
        self.assertEqual(
            result['form_initial']['main_image_alt'],
            'جامعة الملايا'
        )
        self.assertEqual(result['confidence']['main_image_alt'], 'generated')

    def test_institute_and_major_content_types(self):
        """
        Test that auto-generation works for institute and major content types.
        """
        # Test Institute
        media_file_inst = MediaFile.objects.create(
            original_filename='inst_logo.png',
            file='inst_logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='',
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        wp_data_inst = {
            'content_type': 'institute',
            'name': 'معهد التدريب الماليزي',
            'slug': 'mti',
            'fields': {},
            'seo': {},
            'faculties': [],
            'faqs': []
        }

        result_inst = self.mapper.map_data(wp_data_inst, {'logo': media_file_inst}, [])
        
        self.assertEqual(
            result_inst['form_initial']['logo_alt'],
            'شعار معهد التدريب الماليزي'
        )
        self.assertEqual(result_inst['confidence']['logo_alt'], 'generated')

        # Test Major
        media_file_major = MediaFile.objects.create(
            original_filename='major_img.jpg',
            file='major_img.jpg',
            file_size=2048,
            width=800,
            height=600,
            alt_text='',
            source_type=MediaFile.SourceType.MAJOR_IMAGE,
            uploaded_by=self.user
        )

        wp_data_major = {
            'content_type': 'major',
            'name': 'هندسة البرمجيات',
            'slug': 'software-engineering',
            'fields': {},
            'seo': {},
            'faculties': [],
            'faqs': []
        }

        result_major = self.mapper.map_data(wp_data_major, {'main_image': media_file_major}, [])
        
        self.assertEqual(
            result_major['form_initial']['main_image_alt'],
            'هندسة البرمجيات'
        )
        self.assertEqual(result_major['confidence']['main_image_alt'], 'generated')



class ImageDownloaderDuplicateTests(TestCase):
    """
    Tests for image duplicate detection in image downloader.
    اختبارات منع تكرار الصور عند الاستيراد من الووردبريس
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.test_url = 'https://example.com/test-logo.png'

    @patch('apps.importer.services.image_downloader.requests.get')
    def test_image_downloads_first_time(self, mock_get):
        """
        Test that image downloads successfully on first fetch.
        اختبار أن الصورة تُحمّل بنجاح في المرة الأولى
        """
        # Mock successful image download
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.iter_content = lambda chunk_size: [b'\x89PNG\r\n\x1a\n' + b'\x00' * 100]
        mock_get.return_value = mock_response

        # Mock Pillow Image
        with patch('apps.importer.services.image_downloader.Image') as mock_image:
            mock_img = MagicMock()
            mock_img.format = 'PNG'
            mock_img.width = 200
            mock_img.height = 200
            mock_image.open.return_value = mock_img

            media_file, warning = download_and_optimize_image(
                url=self.test_url,
                alt_text='Test Logo',
                description='Test description',
                title='Test Title',
                source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
                user=self.user
            )

            # Assert image was created
            self.assertIsNotNone(media_file)
            self.assertIsNone(warning)
            
            # Assert source_url is saved
            self.assertEqual(media_file.source_url, self.test_url)
            self.assertEqual(media_file.title, 'Test Title')

    @patch('apps.importer.services.image_downloader.requests.get')
    def test_image_not_downloaded_second_time(self, mock_get):
        """
        Test that same URL returns existing MediaFile without downloading again.
        اختبار أن نفس الرابط يرجع الصورة الموجودة بدون تحميل جديد
        """
        # Create existing media file with source_url
        existing_media = MediaFile.objects.create(
            original_filename='test-logo.png',
            file='test-logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='Existing Alt Text',
            caption='Existing Caption',
            description='Original description',
            source_url=self.test_url,  # Same URL
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        # Try to download again with same URL
        media_file, warning = download_and_optimize_image(
            url=self.test_url,
            alt_text='New Alt Text',  # Different alt text
            description='New description',  # Different description
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            user=self.user
        )

        # Assert no download happened (requests.get was never called)
        mock_get.assert_not_called()

        # Assert returned media file is the existing one
        self.assertIsNotNone(media_file)
        self.assertIsNone(warning)
        self.assertEqual(media_file.id, existing_media.id)
        self.assertEqual(media_file.alt_text, 'Existing Alt Text')  # Original preserved
        
        # Assert no duplicate was created
        self.assertEqual(MediaFile.objects.count(), 1)

    @patch('apps.importer.services.image_downloader.requests.get')
    def test_different_urls_download_separately(self, mock_get):
        """
        Test that different URLs create separate MediaFile instances.
        اختبار أن روابط مختلفة تُنشئ صور منفصلة
        """
        url1 = 'https://example.com/logo1.png'
        url2 = 'https://example.com/logo2.png'
        
        # Create first media file
        MediaFile.objects.create(
            original_filename='logo1.png',
            file='logo1.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='Logo 1',
            description='First logo',
            source_url=url1,
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        # Mock successful download for second URL
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.iter_content = lambda chunk_size: [b'\x89PNG\r\n\x1a\n' + b'\x00' * 100]
        mock_get.return_value = mock_response

        with patch('apps.importer.services.image_downloader.Image') as mock_image:
            mock_img = MagicMock()
            mock_img.format = 'PNG'
            mock_img.width = 200
            mock_img.height = 200
            mock_image.open.return_value = mock_img

            # Try to download second URL
            media_file2, warning = download_and_optimize_image(
                url=url2,
                alt_text='Logo 2',
                description='Second logo',
                source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
                user=self.user
            )

            # Assert second image was downloaded (not reused)
            self.assertIsNotNone(media_file2)
            self.assertIsNone(warning)
            
            # Assert two separate media files exist
            self.assertEqual(MediaFile.objects.count(), 2)

    def test_url_hash_marker_format(self):
        """
        Test that source_url field is properly saved.
        اختبار أن حقل source_url بيتحفظ صح
        """
        test_url = 'https://example.com/image.png'
        
        media = MediaFile.objects.create(
            original_filename='test.png',
            file='test.png',
            file_size=1024,
            width=200,
            height=200,
            source_url=test_url,
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )
        
        # Assert source_url is saved correctly
        self.assertEqual(media.source_url, test_url)
        
        # Assert can query by source_url
        found = MediaFile.objects.filter(source_url=test_url).first()
        self.assertIsNotNone(found)
        self.assertEqual(found.id, media.id)

    @patch('apps.importer.services.image_downloader.requests.get')
    def test_metadata_updates_on_reimport(self, mock_get):
        """
        Test that caption, title, description update when reimporting same URL with new metadata.
        اختبار أن Caption و Description يتحدثوا عند إعادة استيراد نفس الرابط ببيانات جديدة
        """
        # Create existing media file
        existing_media = MediaFile.objects.create(
            original_filename='test-logo.png',
            file='test-logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='Old Alt Text',
            caption='Old Caption',
            title='Old Title',
            description='Old description',
            source_url=self.test_url,
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        # Reimport with updated metadata
        media_file, warning = download_and_optimize_image(
            url=self.test_url,
            alt_text='New Alt Text',
            caption='New Caption from WordPress',
            title='New Title from WordPress',
            description='New description from WordPress',
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            user=self.user
        )

        # Assert no new file was created
        self.assertEqual(MediaFile.objects.count(), 1)
        mock_get.assert_not_called()

        # Refresh from database
        existing_media.refresh_from_db()

        # Assert metadata was updated
        self.assertEqual(existing_media.alt_text, 'New Alt Text')
        self.assertEqual(existing_media.caption, 'New Caption from WordPress')
        self.assertEqual(existing_media.title, 'New Title from WordPress')
        
        # Assert description updated cleanly (no markers)
        self.assertEqual(existing_media.description, 'New description from WordPress')

    @patch('apps.importer.services.image_downloader.requests.get')
    def test_metadata_not_overwritten_with_empty_values(self, mock_get):
        """
        Test that existing metadata is not overwritten with empty values on reimport.
        اختبار أن البيانات الموجودة لا تُستبدل بقيم فارغة عند إعادة الاستيراد
        """
        # Create existing media file with good metadata
        existing_media = MediaFile.objects.create(
            original_filename='test-logo.png',
            file='test-logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='Good Alt Text',
            caption='Good Caption',
            description='Good description',
            source_url=self.test_url,
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        # Reimport with empty metadata
        media_file, warning = download_and_optimize_image(
            url=self.test_url,
            alt_text='',  # Empty
            caption='',  # Empty
            description='',  # Empty
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            user=self.user
        )

        # Assert no new file was created
        self.assertEqual(MediaFile.objects.count(), 1)
        mock_get.assert_not_called()

        # Refresh from database
        existing_media.refresh_from_db()

        # Assert original metadata preserved
        self.assertEqual(existing_media.alt_text, 'Good Alt Text')
        self.assertEqual(existing_media.caption, 'Good Caption')
        self.assertEqual(existing_media.description, 'Good description')

    @patch('apps.importer.services.image_downloader.requests.get')
    def test_url_marker_preserved_across_updates(self, mock_get):
        """
        Test that source_url is preserved even after multiple updates.
        اختبار أن source_url محفوظ دائماً حتى بعد تحديثات متعددة
        """
        # Create initial media
        existing_media = MediaFile.objects.create(
            original_filename='test-logo.png',
            file='test-logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='Alt 1',
            description='Description 1',
            source_url=self.test_url,
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        # First update
        media_file, _ = download_and_optimize_image(
            url=self.test_url,
            alt_text='Alt 2',
            description='Description 2',
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            user=self.user
        )
        
        existing_media.refresh_from_db()
        self.assertEqual(existing_media.source_url, self.test_url)
        self.assertEqual(existing_media.description, 'Description 2')

        # Second update
        media_file, _ = download_and_optimize_image(
            url=self.test_url,
            alt_text='Alt 3',
            description='Description 3',
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            user=self.user
        )
        
        existing_media.refresh_from_db()
        self.assertEqual(existing_media.source_url, self.test_url)
        self.assertEqual(existing_media.description, 'Description 3')

