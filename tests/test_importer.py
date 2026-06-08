import pytest
from unittest.mock import patch, MagicMock
from django.test import override_settings, SimpleTestCase
from apps.importer.services.content_mapper import ContentMapper
from apps.importer.services.wp_client import WPImporterClient, WPNotFoundError, WPAuthError, WPConnectionError

class TestContentMapper(SimpleTestCase):
    """Tests for ContentMapper functionality."""

    def test_city_mapping_exact(self):
        mapper = ContentMapper()
        city, confidence = mapper._map_city('كوالالمبور')
        assert city == 'kl'
        assert confidence == 'high'

        city, confidence = mapper._map_city('Selangor')
        assert city == 'selangor'
        assert confidence == 'high'

        city, confidence = mapper._map_city('ملقا')
        assert city == 'melaka'
        assert confidence == 'high'

    def test_city_mapping_partial(self):
        mapper = ContentMapper()
        city, confidence = mapper._map_city('في كوالالمبور العاصمة')
        assert city == 'kl'
        assert confidence == 'high'

    def test_city_mapping_not_found(self):
        mapper = ContentMapper()
        city, confidence = mapper._map_city('القاهرة')
        assert city == ''
        assert confidence == 'none'

    def test_map_university_data(self):
        mapper = ContentMapper()
        wp_data = {
            'content_type': 'university',
            'name': 'جامعة مالايا الماليزية UM | البرامج والتكاليف والشروط | يو إم 2026',
            'slug': '%d8%ac%d8%a7%d9%85%d8%b9%d8%a9-%d9%85%d8%a7%d9%84%d8%a7%d9%8a%d8%a7',
            'video_url': 'https://youtube.com/watch?v=123',
            'city_raw': 'KL',
            'sub_type': 'private',
            'fields': {
                'description': {'value': 'Decription of Uni', 'confidence': 'high'},
                'location': {'value': 'Kuala Lumpur', 'confidence': 'medium'},
            },
            'seo': {
                'meta_title': 'جامعة مالايا الماليزية UM | البرامج والتكاليف والشروط | يو إم 2026',
                'meta_description': 'SEO Description Here',
                'focus_keyword': 'keyword',
            }
        }
        
        mapped = mapper.map_data(wp_data, downloaded_images={}, image_warnings=[])
        
        assert mapped['content_type'] == 'university'
        assert mapped['form_initial']['name'] == 'جامعة مالايا الماليزية UM'
        assert mapped['form_initial']['slug'] == 'جامعة-مالايا'
        assert mapped['form_initial']['city'] == 'kl'
        assert mapped['form_initial']['description'] == '<div style="text-align: justify;">Decription of Uni</div>'
        assert mapped['form_initial']['meta_title'] == 'جامعة مالايا الماليزية UM | البرامج والتكاليف والشروط | يو إم 2026'
        assert mapped['confidence']['city'] == 'high'
        assert mapped['confidence']['description'] == 'high'
        assert mapped['redirect_url'] == '/dashboard/universities/create/'

    def test_clean_importer_name(self):
        mapper = ContentMapper()
        # Test clean_name (everything before the first pipe/dash separator)
        assert mapper._clean_importer_name('جامعة مالايا الماليزية UM | البرامج والتكاليف والشروط | يو إم 2026') == 'جامعة مالايا الماليزية UM'
        assert mapper._clean_importer_name('جامعة مالايا الماليزية UM - البرامج والتكاليف') == 'جامعة مالايا الماليزية UM'
        assert mapper._clean_importer_name('جامعة مالايا الماليزية UM – البرامج والتكاليف') == 'جامعة مالايا الماليزية UM'
        assert mapper._clean_importer_name('جامعة مالايا الماليزية UM — البرامج والتكاليف') == 'جامعة مالايا الماليزية UM'
        assert mapper._clean_importer_name('جامعة مالايا') == 'جامعة مالايا'
        assert mapper._clean_importer_name('جامعة مالايا | ') == 'جامعة مالايا'



    def test_split_admission_requirements(self):
        mapper = ContentMapper()
        combined_html = (
            "<p>الالتحاق بـ جامعة مالايا يتطلب استيفاء شروط محددة...</p>"
            "<h3>🎓 برنامج البكالوريوس (Bachelor’s)</h3>"
            "<p>متطلبات اللغة للبكالوريوس</p>"
            "<p>المتطلبات الأكاديمية للبكالوريوس</p>"
            "<h3>🎓 برنامج الماجستير (Master’s)</h3>"
            "<p>متطلبات اللغة للماجستير</p>"
            "<p>المتطلبات الأكاديمية للماجستير</p>"
            "<h3>🎓 برنامج الدكتوراه (PhD)</h3>"
            "<p>متطلبات اللغة للدكتوراه</p>"
            "<p>المتطلبات الأكاديمية للدكتوراه</p>"
        )
        
        split = mapper._split_admission_requirements(combined_html)
        
        # Intro and headers should be stripped
        assert "الالتحاق بـ جامعة مالايا" not in split['bachelor']
        assert "برنامج البكالوريوس" not in split['bachelor']
        assert "<p>متطلبات اللغة للبكالوريوس</p>" in split['bachelor']
        assert "<p>المتطلبات الأكاديمية للبكالوريوس</p>" in split['bachelor']
        
        assert "برنامج الماجستير" not in split['master']
        assert "<p>متطلبات اللغة للماجستير</p>" in split['master']
        assert "<p>المتطلبات الأكاديمية للماجستير</p>" in split['master']
        
        assert "برنامج الدكتوراه" not in split['phd']
        assert "<p>متطلبات اللغة للدكتوراه</p>" in split['phd']
        assert "<p>المتطلبات الأكاديمية للدكتوراه</p>" in split['phd']

    def test_split_admission_requirements_no_bachelor_header(self):
        mapper = ContentMapper()
        combined_html = (
            "<p>متطلبات اللغة للبكالوريوس</p>"
            "<p>المتطلبات الأكاديمية للبكالوريوس</p>"
            "<h3>🎓 برنامج الماجستير (Master’s)</h3>"
            "<p>متطلبات اللغة للماجستير</p>"
        )
        
        split = mapper._split_admission_requirements(combined_html)
        
        assert "<p>متطلبات اللغة للبكالوريوس</p>" in split['bachelor']
        assert "برنامج الماجستير" not in split['master']
        assert "<p>متطلبات اللغة للماجستير</p>" in split['master']

    def test_strip_html_content(self):
        mapper = ContentMapper()
        dirty_html = (
            "  \n <p>&nbsp;</p>  <br/> "
            "<p>متطلبات اللغة للبكالوريوس</p>"
            "\n <p>&nbsp;</p>\n&nbsp;\n "
        )
        cleaned = mapper._strip_html_content(dirty_html)
        assert cleaned == "<p>متطلبات اللغة للبكالوريوس</p>"




@override_settings(WP_IMPORTER_BASE_URL='https://old-site.com', WP_IMPORTER_SECRET_KEY='secret')
class TestWPImporterClient(SimpleTestCase):
    """Tests for WPImporterClient."""

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        # Configure Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            'name': 'Test Uni',
            'slug': 'test-uni'
        }
        mock_get.return_value = mock_response

        client = WPImporterClient()
        data = client.fetch('test-uni')
        assert data['name'] == 'Test Uni'
        assert data['slug'] == 'test-uni'

    @patch('requests.get')
    def test_fetch_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = WPImporterClient()
        with pytest.raises(WPNotFoundError):
            client.fetch('not-found-slug')

    @patch('requests.get')
    def test_fetch_auth_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        client = WPImporterClient()
        with pytest.raises(WPAuthError):
            client.fetch('unauthorized-slug')

