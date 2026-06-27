"""
Tests for WordPress importer services.
اختبارات خدمات استيراد المحتوى من WordPress
"""
import io
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



class ContentMapperNameCleaningTests(TestCase):
    """
    Tests for removing date/year patterns from university/institute names.
    اختبارات حذف التواريخ والسنوات من أسماء الجامعات والمعاهد عند الاستيراد
    """

    def setUp(self):
        self.mapper = ContentMapper()

    def test_clean_name_with_single_year(self):
        self.assertEqual(self.mapper._clean_importer_name("جامعة ماليزيا 2024"), "جامعة ماليزيا")

    def test_clean_name_with_year_in_parentheses(self):
        self.assertEqual(self.mapper._clean_importer_name("جامعة ماليزيا (2024)"), "جامعة ماليزيا")

    def test_clean_name_with_year_range(self):
        self.assertEqual(self.mapper._clean_importer_name("معهد العلوم والتقنية 2023-2024"), "معهد العلوم والتقنية")

    def test_clean_name_with_year_range_in_parentheses(self):
        self.assertEqual(self.mapper._clean_importer_name("معهد العلوم والتقنية (2023/2024)"), "معهد العلوم والتقنية")

    def test_clean_name_with_eastern_arabic_numerals(self):
        self.assertEqual(self.mapper._clean_importer_name("جامعة مالايا ٢٠٢٤"), "جامعة مالايا")

    def test_clean_name_with_prefix_word_laam(self):
        self.assertEqual(self.mapper._clean_importer_name("جامعة ماليزيا لعام 2024"), "جامعة ماليزيا")

    def test_clean_name_with_prefix_word_am(self):
        self.assertEqual(self.mapper._clean_importer_name("جامعة العلوم عام 2024"), "جامعة العلوم")

    def test_clean_name_without_date(self):
        self.assertEqual(self.mapper._clean_importer_name("جامعة العلوم والتكنولوجيا"), "جامعة العلوم والتكنولوجيا")

    def test_clean_name_with_separator_and_date(self):
        self.assertEqual(self.mapper._clean_importer_name("جامعة مالايا - 2024"), "جامعة مالايا")

    def test_clean_name_with_non_year_numbers(self):
        # 6 October University should not lose its "6" since it's not a 4-digit year.
        self.assertEqual(self.mapper._clean_importer_name("جامعة 6 أكتوبر"), "جامعة 6 أكتوبر")


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
    def test_image_content_identical_no_overwrite(self, mock_get):
        """
        Test that when the downloaded image content is identical to local file,
        no file overwrite happens, but metadata updates successfully.
        """
        # 1. Create existing media file in DB
        existing_media = MediaFile.objects.create(
            original_filename='test-logo.png',
            file='test-logo.png',
            file_size=100,  # Match mock content size
            width=200,
            height=200,
            alt_text='Existing Alt Text',
            caption='Existing Caption',
            description='Original description',
            source_url=self.test_url,
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        # 2. Mock successful download of the same content
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

            # Mock default_storage.open to return the same byte content
            with patch('django.core.files.storage.default_storage.open', return_value=io.BytesIO(b'mocked_webp_data')) as mock_open:
                # Mock img.save to write the same mocked data
                def mock_save(output, format, **kwargs):
                    output.write(b'mocked_webp_data')
                mock_img.save = mock_save

                # Patch FieldFile.save to assert it is NOT called
                with patch('django.db.models.fields.files.FieldFile.save') as mock_file_save:
                    media_file, warning = download_and_optimize_image(
                        url=self.test_url,
                        alt_text='New Alt Text',
                        caption='New Caption',
                        description='New description',
                        source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
                        user=self.user
                    )

                    # Assert requests.get was called
                    mock_get.assert_called_once()
                    
                    # Assert no file overwrite happened
                    mock_file_save.assert_not_called()

                    # Assert returned media file is the existing one
                    self.assertEqual(media_file.id, existing_media.id)
                    self.assertEqual(media_file.alt_text, 'New Alt Text')
                    self.assertEqual(media_file.caption, 'New Caption')
                    self.assertEqual(MediaFile.objects.count(), 1)

    @patch('apps.importer.services.image_downloader.requests.get')
    def test_image_content_different_overwrites_file(self, mock_get):
        """
        Test that when the downloaded image content is different,
        the local file on disk is deleted and overwritten with the new content.
        """
        # 1. Create existing media file in DB
        existing_media = MediaFile.objects.create(
            original_filename='test-logo.png',
            file='test-logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='Existing Alt Text',
            source_url=self.test_url,
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        # 2. Mock successful download of different content
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.iter_content = lambda chunk_size: [b'\x89PNG\r\n\x1a\n' + b'\x00' * 100]
        mock_get.return_value = mock_response

        # Mock Pillow Image
        with patch('apps.importer.services.image_downloader.Image') as mock_image:
            mock_img = MagicMock()
            mock_img.format = 'PNG'
            mock_img.width = 300  # New width
            mock_img.height = 300  # New height
            mock_image.open.return_value = mock_img

            # Mock default_storage to return different bytes
            with patch('django.core.files.storage.default_storage.open', return_value=io.BytesIO(b'old_webp_data')):
                with patch('django.core.files.storage.default_storage.exists', return_value=True):
                    with patch('django.core.files.storage.default_storage.delete') as mock_delete:
                        # Mock img.save to write new mocked data
                        def mock_save(output, format, **kwargs):
                            output.write(b'new_webp_data')
                        mock_img.save = mock_save

                        # Patch FieldFile.save to assert it IS called
                        with patch('django.db.models.fields.files.FieldFile.save') as mock_file_save:
                            media_file, warning = download_and_optimize_image(
                                url=self.test_url,
                                alt_text='Updated Alt',
                                source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
                                user=self.user
                            )

                            # Assert deletion of old file was called
                            mock_delete.assert_called_once_with(existing_media.file.name)
                            
                            # Assert file saving was called
                            mock_file_save.assert_called_once()
                            
                            # Assert metadata and sizes updated
                            self.assertEqual(media_file.id, existing_media.id)
                            self.assertEqual(media_file.alt_text, 'Updated Alt')
                            self.assertEqual(media_file.width, 300)
                            self.assertEqual(media_file.height, 300)

    @patch('apps.importer.services.image_downloader.requests.get')
    def test_image_download_failure_fallbacks_to_existing(self, mock_get):
        """
        Test that when download fails, it returns the existing media file
        with a warning message instead of failing the import.
        """
        # 1. Create existing media file in DB
        existing_media = MediaFile.objects.create(
            original_filename='test-logo.png',
            file='test-logo.png',
            file_size=1024,
            width=200,
            height=200,
            alt_text='Existing Alt Text',
            source_url=self.test_url,
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        # 2. Mock failed download
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Try download
        media_file, warning = download_and_optimize_image(
            url=self.test_url,
            alt_text='New Alt Text',
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            user=self.user
        )

        # Assert it fell back to existing media file and returned a warning
        self.assertIsNotNone(media_file)
        self.assertEqual(media_file.id, existing_media.id)
        self.assertIn("فشل تحديث ملف الصورة", warning)
        
        # Assert metadata is updated even on fallback
        self.assertEqual(media_file.alt_text, 'New Alt Text')

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
            file_size=100,  # Match mock content size
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

        # Mock successful download of the same content
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

            # Mock default_storage.open to return the same byte content
            with patch('django.core.files.storage.default_storage.open', return_value=io.BytesIO(b'mocked_webp_data')):
                # Mock img.save to write the same mocked data
                def mock_save(output, format, **kwargs):
                    output.write(b'mocked_webp_data')
                mock_img.save = mock_save

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
        mock_get.assert_called_once()

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
            file_size=100,  # Match mock size
            width=200,
            height=200,
            alt_text='Good Alt Text',
            caption='Good Caption',
            description='Good description',
            source_url=self.test_url,
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
            uploaded_by=self.user
        )

        # Mock successful download of the same content
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

            # Mock default_storage.open to return the same byte content
            with patch('django.core.files.storage.default_storage.open', return_value=io.BytesIO(b'mocked_webp_data')):
                # Mock img.save to write the same mocked data
                def mock_save(output, format, **kwargs):
                    output.write(b'mocked_webp_data')
                mock_img.save = mock_save

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
        mock_get.assert_called_once()

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

    def test_normalize_image_url_function(self):
        """Test normalize_image_url helper function."""
        from apps.importer.services.image_downloader import normalize_image_url
        url1 = "http://sciencesgates.com/wp-content/uploads/2026/06/logo-150x150.png?w=200"
        url2 = "https://sciencesgates.com/wp-content/uploads/2026/06/logo.png"
        self.assertEqual(normalize_image_url(url1), url2)

        # Test advanced suffix patterns
        self.assertEqual(
            normalize_image_url("https://sciencesgates.com/wp-content/uploads/2026/06/logo-768x257-1.png"),
            "https://sciencesgates.com/wp-content/uploads/2026/06/logo.png"
        )
        self.assertEqual(
            normalize_image_url("https://sciencesgates.com/wp-content/uploads/2026/06/logo-scaled.jpg"),
            "https://sciencesgates.com/wp-content/uploads/2026/06/logo.jpg"
        )

    def test_zero_kb_file_raises_exception(self):
        """Test that a 0 KB file (in production/non-mocked situation) raises an exception."""
        from unittest.mock import patch, MagicMock
        with patch('apps.importer.services.image_downloader.requests.get') as mock_get:
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
                mock_img.__class__.__name__ = 'Image'  # Not Mock/MagicMock
                mock_image.open.return_value = mock_img

                from apps.importer.services.image_downloader import download_and_optimize_image
                media_file, warning = download_and_optimize_image(
                    url=self.test_url,
                    alt_text='Test Logo',
                    source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
                    user=self.user
                )
                self.assertIsNone(media_file)
                self.assertIn("فارغ", warning)

    def test_signal_reuses_existing_media_file(self):
        """Test that sync_media_file signal handler reuses existing MediaFile by path."""
        from apps.universities.models import University
        from django.contrib.contenttypes.models import ContentType

        # Create a MediaFile (simulating import before university is saved)
        media_file = MediaFile.objects.create(
            original_filename='uni-logo.webp',
            file='media_library/university_logo/uni-logo.webp',
            file_size=1234,
            source_url='https://example.com/uni-logo.png',
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO
        )

        # Create university referencing this file
        uni = University.objects.create(
            name='Test University for Signals',
            slug='test-uni-signals',
            logo='media_library/university_logo/uni-logo.webp'
        )

        # Count should remain 1 (no duplicate MediaFile created)
        self.assertEqual(MediaFile.objects.filter(file='media_library/university_logo/uni-logo.webp').count(), 1)
        
        # Verify the existing MediaFile was linked to the University
        media_file.refresh_from_db()
        self.assertEqual(media_file.content_type, ContentType.objects.get_for_model(University))
        self.assertEqual(media_file.object_id, uni.pk)
        self.assertEqual(media_file.source_type, MediaFile.SourceType.UNIVERSITY_LOGO)


class ContentMapperTagsTests(TestCase):
    """
    Tests for WP tags extraction, mapping, and dynamic creation.
    اختبارات استخراج وتعيين وإنشاء الوسوم تلقائياً
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.mapper = ContentMapper()

    def test_tags_are_mapped_and_created_if_missing(self):
        """
        Test that tags list is mapped into form_initial and missing tags are created in DB.
        """
        from apps.articles.models import Tag
        
        # Initially, there are no tags
        self.assertEqual(Tag.objects.count(), 0)

        wp_data = {
            'content_type': 'university',
            'name': 'جامعة ماليزيا',
            'slug': 'malaysia-uni',
            'fields': {},
            'seo': {},
            'faculties': [],
            'faqs': [],
            'tags': ['ماليزيا', 'الدراسة في الخارج', 'Engineering']
        }

        result = self.mapper.map_data(wp_data, {}, [])

        # Verify tags are created in the database
        self.assertEqual(Tag.objects.count(), 3)
        tags_in_db = Tag.objects.all().order_by('id')
        self.assertEqual(tags_in_db[0].name, 'ماليزيا')
        self.assertEqual(tags_in_db[0].slug, 'ماليزيا')
        self.assertEqual(tags_in_db[1].name, 'الدراسة في الخارج')
        self.assertEqual(tags_in_db[1].slug, 'الدراسة-في-الخارج')
        self.assertEqual(tags_in_db[2].name, 'Engineering')
        self.assertEqual(tags_in_db[2].slug, 'engineering')

        # Verify tag IDs are populated in form_initial
        expected_ids = list(Tag.objects.values_list('id', flat=True))
        self.assertEqual(sorted(result['form_initial']['tags']), sorted(expected_ids))
        self.assertEqual(result['confidence']['tags'], 'high')

    def test_existing_tags_are_reused(self):
        """
        Test that existing tags are reused and not duplicated.
        """
        from apps.articles.models import Tag
        existing_tag = Tag.objects.create(name='ماليزيا', slug='malaysia-tag')

        wp_data = {
            'content_type': 'university',
            'name': 'جامعة ماليزيا',
            'slug': 'malaysia-uni',
            'fields': {},
            'seo': {},
            'faculties': [],
            'faqs': [],
            'tags': ['ماليزيا']
        }

        result = self.mapper.map_data(wp_data, {}, [])

        # Assert no new tag was created
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(result['form_initial']['tags'], [existing_tag.id])


class ContentMapperRedirectAndMediaReplacementTests(TestCase):
    """
    Tests for ContentMapper redirection logic on duplicates and media replacement cleanup.
    اختبارات منطق التوجيه للروابط المكررة وتنظيف الوسائط المستبدلة
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser2', password='testpass2')
        self.mapper = ContentMapper()

    def test_redirect_to_edit_if_university_exists(self):
        from apps.universities.models import University
        uni = University.objects.create(
            name='جامعة مالايا',
            slug='um-slug',
            university_type='public'
        )
        wp_data = {
            'content_type': 'university',
            'name': 'جامعة مالايا',
            'slug': 'um-slug',
            'fields': {},
            'seo': {},
            'faculties': [],
            'faqs': []
        }
        result = self.mapper.map_data(wp_data, {}, [])
        self.assertEqual(result['redirect_url'], f'/dashboard/universities/{uni.id}/edit/')

    def test_redirect_to_edit_if_institute_exists(self):
        from apps.institutes.models import Institute
        inst = Institute.objects.create(
            name='معهد ماليزيا',
            slug='inst-slug'
        )
        wp_data = {
            'content_type': 'institute',
            'name': 'معهد ماليزيا',
            'slug': 'inst-slug',
            'fields': {},
            'seo': {}
        }
        result = self.mapper.map_data(wp_data, {}, [])
        self.assertEqual(result['redirect_url'], f'/dashboard/institutes/{inst.id}/edit/')

    def test_redirect_to_edit_if_major_exists(self):
        from apps.majors.models import Major
        major = Major.objects.create(
            name='هندسة الحاسوب',
            slug='computer-engineering-slug'
        )
        wp_data = {
            'content_type': 'major',
            'name': 'هندسة الحاسوب',
            'slug': 'computer-engineering-slug',
            'fields': {},
            'seo': {}
        }
        result = self.mapper.map_data(wp_data, {}, [])
        self.assertEqual(result['redirect_url'], f'/dashboard/majors/{major.id}/edit/')

    def test_redirect_to_edit_if_article_exists(self):
        from apps.articles.models import Article
        article = Article.objects.create(
            title='مقال جديد',
            slug='article-slug'
        )
        wp_data = {
            'content_type': 'article',
            'name': 'مقال جديد',
            'slug': 'article-slug',
            'fields': {},
            'seo': {}
        }
        result = self.mapper.map_data(wp_data, {}, [])
        self.assertEqual(result['redirect_url'], f'/dashboard/articles/{article.id}/edit/')

    def test_delete_unused_media_file_on_save(self):
        from apps.universities.models import University
        from apps.importer.services.image_downloader import delete_unused_media_file
        
        # Create media file
        media_file = MediaFile.objects.create(
            original_filename='old_logo.png',
            file='old_logo.png',
            file_size=100,
            width=50,
            height=50,
            uploaded_by=self.user
        )
        
        # Create a university referencing this media file
        uni = University.objects.create(
            name='جامعة اختبار',
            slug='test-uni-media',
            logo='old_logo.png',
            university_type='public'
        )
        
        # Verify it exists in db
        self.assertTrue(MediaFile.objects.filter(file='old_logo.png').exists())
        
        # Replace the logo with a new one
        uni.logo = 'new_logo.png'
        uni.save()
        
        # Call the helper manually to verify it correctly cleans up the unused file
        delete_unused_media_file('old_logo.png')
        
        # Verify old_logo MediaFile is deleted
        self.assertFalse(MediaFile.objects.filter(file='old_logo.png').exists())


class BulkSaveAPITests(TestCase):
    """
    Tests for bulk saving service and the ImportBulkSaveAPIView endpoint.
    اختبارات خدمة الحفظ الجماعي ومسار الـ API المخصص للحفظ الجماعي
    """
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='password')
        self.client.force_login(self.user)
        # Create a mock MediaFile in DB
        self.mock_image = MediaFile.objects.create(
            original_filename='mock.png',
            file='mock.png',
            file_size=1024,
            width=200,
            height=200,
            uploaded_by=self.user
        )

    @patch('apps.importer.services.wp_client.requests.get')
    def test_bulk_save_api_university(self, mock_get):
        """
        Test ImportBulkSaveAPIView successfully fetches and saves a university.
        """
        # Mock WordPress API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content_type': 'university',
            'name': 'جامعة دبي التكنولوجية',
            'slug': 'dubai-tech-university',
            'city_raw': 'كوالالمبور',
            'images': {
                'logo': {'url': 'https://example.com/logo.png'},
                'main_image': {'url': 'https://example.com/main.jpg'}
            },
            'fields': {
                'location': {'value': 'دبي، الإمارات', 'confidence': 'high'},
                'description': {'value': 'وصف لجامعة دبي التكنولوجية العريقة.', 'confidence': 'high'},
                'publish_status': {'value': 'unpublished', 'confidence': 'high'},
            },
            'seo': {
                'meta_title': 'جامعة دبي التكنولوجية',
                'meta_description': 'كل التفاصيل عن الدراسة في جامعة دبي التكنولوجية',
            },
            'faculties': [],
            'faqs': []
        }
        mock_get.return_value = mock_response

        # Mock download_and_optimize_image to return our mock image
        with patch('apps.importer.views.download_and_optimize_image', return_value=(self.mock_image, None)):
            response = self.client.post('/dashboard/import/bulk-save/', {
                'url': 'https://old-site.com/university/dubai-tech-university/',
                'content_type_override': 'university'
            })
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['content_type'], 'university')
            self.assertEqual(data['name'], 'جامعة دبي التكنولوجية')
            
            # Verify database entry
            from apps.universities.models import University
            self.assertTrue(University.objects.filter(slug='dubai-tech-university').exists())
            uni = University.objects.get(slug='dubai-tech-university')
            self.assertEqual(uni.name, 'جامعة دبي التكنولوجية')
            self.assertEqual(uni.university_type, 'private')

    @patch('apps.importer.services.wp_client.requests.get')
    def test_bulk_save_api_article(self, mock_get):
        """
        Test ImportBulkSaveAPIView successfully fetches and saves an article.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content_type': 'article',
            'name': 'مقال برمجة جديد',
            'slug': 'new-programming-article',
            'images': {
                'main_image': {'url': 'https://example.com/main.jpg'}
            },
            'fields': {
                'title': {'value': 'مقال برمجة جديد', 'confidence': 'high'},
                'content': {'value': '<p>محتوى المقال الجديد</p>', 'confidence': 'high'},
                'publish_status': {'value': 'unpublished', 'confidence': 'high'},
            },
            'seo': {
                'meta_title': 'مقال برمجة جديد',
                'meta_description': 'ملخص المقال',
            }
        }
        mock_get.return_value = mock_response

        # Mock download_and_optimize_image to return our mock image
        with patch('apps.importer.views.download_and_optimize_image', return_value=(self.mock_image, None)):
            response = self.client.post('/dashboard/import/bulk-save/', {
                'url': 'https://old-site.com/new-programming-article/',
                'content_type_override': 'article'
            })
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['content_type'], 'article')
            
            # Verify database entry
            from apps.articles.models import Article
            self.assertTrue(Article.objects.filter(slug='new-programming-article').exists())
            article = Article.objects.get(slug='new-programming-article')
            self.assertEqual(article.title, 'مقال برمجة جديد')

    @patch('apps.importer.services.wp_client.requests.get')
    def test_bulk_save_unicode_slug_slugification(self, mock_get):
        """
        Test that a slug containing spaces and capital letters gets slugified
        and passes the unicode slug validation.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content_type': 'article',
            'name': 'سكن جامعة MMU في ملاكا',
            'slug': 'سكن جامعة MMU في ملاكا',
            'images': {},
            'fields': {
                'title': {'value': 'سكن جامعة MMU في ملاكا', 'confidence': 'high'},
                'content': {'value': '<p>محتوى السكن</p>', 'confidence': 'high'},
                'publish_status': {'value': 'unpublished', 'confidence': 'high'},
            },
            'seo': {}
        }
        mock_get.return_value = mock_response

        response = self.client.post('/dashboard/import/bulk-save/', {
            'url': 'https://old-site.com/سكن-جامعة-MMU-في-ملاكا/',
            'content_type_override': 'article'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        from apps.articles.models import Article
        self.assertTrue(Article.objects.filter(slug='سكن-جامعة-mmu-في-ملاكا').exists())
        article = Article.objects.get(slug='سكن-جامعة-mmu-في-ملاكا')
        self.assertEqual(article.slug, 'سكن-جامعة-mmu-في-ملاكا')

    @patch('apps.importer.services.wp_client.requests.get')
    def test_bulk_save_program_duration_fees_fallback(self, mock_get):
        """
        Test that university programs with blank duration or tuition fees
        automatically fallback to 'غير محدد' and save successfully.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content_type': 'university',
            'name': 'جامعة الشارقة',
            'slug': 'sharjah-university',
            'city_raw': 'كوالالمبور',
            'images': {},
            'fields': {
                'location': {'value': 'الشارقة', 'confidence': 'high'},
                'description': {'value': 'وصف', 'confidence': 'high'},
                'publish_status': {'value': 'unpublished', 'confidence': 'high'},
            },
            'seo': {},
            'faculties': [
                {
                    'name': 'كلية الهندسة',
                    'programs': [
                        {
                            'name': 'بكالوريوس الهندسة الكهربائية',
                            'duration': '',
                            'tuition_fees': ' '
                        }
                    ]
                }
            ],
            'faqs': []
        }
        mock_get.return_value = mock_response

        response = self.client.post('/dashboard/import/bulk-save/', {
            'url': 'https://old-site.com/university/sharjah-university/',
            'content_type_override': 'university'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        from apps.universities.models import Program
        prog = Program.objects.get(name='بكالوريوس الهندسة الكهربائية')
        self.assertEqual(prog.duration, 'غير محدد')
        self.assertEqual(prog.tuition_fees, 'غير محدد')

    @patch('apps.importer.services.wp_client.requests.get')
    def test_bulk_save_program_cleanup_validation(self, mock_get):
        """
        Test that programs with name > 200 chars are truncated,
        and programs with empty names are completely skipped.
        """
        long_name = "ب" * 250
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content_type': 'university',
            'name': 'جامعة عجمان',
            'slug': 'ajman-university',
            'city_raw': 'كوالالمبور',
            'images': {},
            'fields': {
                'location': {'value': 'عجمان', 'confidence': 'high'},
                'description': {'value': 'وصف', 'confidence': 'high'},
                'publish_status': {'value': 'unpublished', 'confidence': 'high'},
            },
            'seo': {},
            'faculties': [
                {
                    'name': 'كلية الهندسة',
                    'programs': [
                        {
                            'name': long_name,
                            'duration': '4 سنوات',
                            'tuition_fees': '20,000 رنجت'
                        },
                        {
                            'name': '',
                            'duration': '3 سنوات',
                            'tuition_fees': '15,000 رنجت'
                        }
                    ]
                }
            ],
            'faqs': []
        }
        mock_get.return_value = mock_response

        response = self.client.post('/dashboard/import/bulk-save/', {
            'url': 'https://old-site.com/university/ajman-university/',
            'content_type_override': 'university'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        from apps.universities.models import Program
        self.assertFalse(Program.objects.filter(duration='3 سنوات').exists())
        
        prog = Program.objects.get(duration='4 سنوات')
        self.assertEqual(prog.name, "ب" * 200)

    @patch('apps.importer.services.wp_client.requests.get')
    def test_bulk_save_image_replacement_on_update(self, mock_get):
        """
        Test that during update, the university logo is replaced by the newly
        imported logo path, even if it already has an existing logo in the DB.
        """
        from apps.universities.models import University
        
        uni = University.objects.create(
            name='جامعة عجمان القديمة',
            slug='ajman-uni-image-test',
            logo='old_logo.png',
            university_type='public'
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content_type': 'university',
            'name': 'جامعة عجمان القديمة',
            'slug': 'ajman-uni-image-test',
            'city_raw': 'كوالالمبور',
            'images': {
                'logo': {'url': 'https://example.com/new_logo.png'},
            },
            'fields': {
                'location': {'value': 'عجمان', 'confidence': 'high'},
                'description': {'value': 'وصف', 'confidence': 'high'},
                'publish_status': {'value': 'unpublished', 'confidence': 'high'},
            },
            'seo': {},
            'faculties': [],
            'faqs': []
        }
        mock_get.return_value = mock_response

        new_media = MediaFile.objects.create(
            original_filename='new_logo.png',
            file='new_logo.png',
            file_size=1024,
            width=200,
            height=200,
            uploaded_by=self.user
        )

        with patch('apps.importer.views.download_and_optimize_image', return_value=(new_media, None)):
            response = self.client.post('/dashboard/import/bulk-save/', {
                'url': 'https://old-site.com/university/ajman-uni-image-test/',
                'content_type_override': 'university'
            })
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            
            uni.refresh_from_db()
            self.assertEqual(uni.logo, 'new_logo.png')






