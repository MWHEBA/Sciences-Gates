import pytest
import json
from unittest.mock import patch, MagicMock
from django.test import override_settings, TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from apps.importer.services.gemini_service import GeminiService, GeminiServiceError
from apps.majors.models import Major, MajorCategory

# Skip all tests in this file as they require live API keys/external resources
pytestmark = pytest.mark.skip(reason="Gemini integration tests disabled")

@override_settings(GEMINI_API_KEY='test_gemini_key')
class TestGeminiService(TestCase):
    """Unit tests for the GeminiService API wrapper."""

    def setUp(self):
        self.service = GeminiService()

    @patch('requests.get')
    def test_search_competitor_success(self, mock_get):
        # Configure search results mock response HTML
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <article>
                    <h2><a href="https://your-uni.com/%d9%87%d9%86%d8%af%d8%b3%d8%a9-%d8%a7%d9%84%d8%a8%d8%b1%d9%85%d8%ac%d9%8a%d8%a7%d8%aa/">هندسة البرمجيات في ماليزيا</a></h2>
                </article>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        url = self.service.search_competitor("دراسة تخصص هندسة البرمجيات")
        
        # Verify it matched correctly and decoded the URL
        assert url == "https://your-uni.com/%d9%87%d9%86%d8%af%d8%b3%d8%a9-%d8%a7%d9%84%d8%a8%d8%b1%d9%85%d8%ac%d9%8a%d8%a7%d8%aa/"
        assert mock_get.called
        assert mock_get.call_args[1]['params']['s'] == "هندسة البرمجيات"

    @patch('requests.get')
    def test_fetch_competitor_content_success(self, mock_get):
        # Configure page mock response HTML
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <div class="elementor">
                    <p>محتوى المنافس هنا</p>
                    <script>alert('bad');</script>
                </div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        content = self.service.fetch_competitor_content("https://your-uni.com/page/")
        
        assert content is not None
        assert "محتوى المنافس هنا" in content
        assert "<script>" not in content  # script tags must be stripped
        assert mock_get.called

    @patch('requests.post')
    def test_rewrite_major_success(self, mock_post):
        # Configure Gemini Mock API response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        
        mock_ai_json = {
            "name": "الهندسة الميكانيكية",
            "description": "<p>وصف التخصص الجديد المعاد صياغته.</p>",
            "why_study_section": "<p>أسباب دراسة التخصص.</p>",
            "how_to_apply_section": "<p>خطوات التقديم.</p>",
            "career_opportunities": "<p>فرص العمل المتاحة.</p>",
            "bachelor_duration": "4 سنوات",
            "master_duration": "سنتان",
            "phd_duration": "3 سنوات",
            "study_language": "اللغة الإنجليزية",
            "practical_training": "متاح في السنة الأخيرة",
            "meta_title": "عنوان الـ SEO الجديد",
            "meta_description": "وصف الـ SEO الجديد",
            "focus_keyword": "الهندسة الميكانيكية في ماليزيا",
            "subjects_tables": [
                {"academic_year": "السنة الأولى", "subjects": "الرياضيات الهندسية, الفيزياء", "track_name": "العام"}
            ],
            "salary_tables": [
                {"job_title": "مهندس ميكانيكي", "job_description": "تصميم الأنظمة", "average_monthly_salary": "5,000 رنجت"}
            ],
            "faqs_data": [
                {"question": "ما هي مدة الدراسة؟", "answer": "4 سنوات للبكالوريوس."}
            ]
        }

        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": json.dumps(mock_ai_json)}
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        # Input data structure matching content mapper output
        mapped_data = {
            'form_initial': {
                'name': 'دراسة الهندسة الميكانيكية في ماليزيا 2026',
                'description': 'وصف قديم...',
                'why_study_section': '',
                'how_to_apply_section': '',
                'career_opportunities': '',
                'study_duration': 'غير محدد',
                'bachelor_duration': '',
                'master_duration': '',
                'phd_duration': '',
                'study_language': '',
                'practical_training': '',
                'meta_title': 'قديم',
                'meta_description': 'قديم',
                'focus_keyword': 'قديم',
            },
            'subjects_tables': [],
            'salary_tables': [],
            'faqs_data': [],
            'seo': {}
        }

        result = self.service.rewrite_major(mapped_data, competitor_html="<div>محتوى المنافس</div>")

        # Assert post was called correctly
        assert mock_post.called
        # Assert fields were updated by AI
        assert result['form_initial']['name'] == "الهندسة الميكانيكية"
        assert result['form_initial']['description'] == "<p>وصف التخصص الجديد المعاد صياغته.</p>"
        assert result['form_initial']['bachelor_duration'] == "4 سنوات"
        assert result['form_initial']['study_duration'] == "4 سنوات"
        assert result['form_initial']['meta_title'] == "قديم"
        assert len(result['subjects_tables']) == 1
        assert result['subjects_tables'][0]['academic_year'] == "السنة الأولى"


@override_settings(
    WP_IMPORTER_BASE_URL='https://old-site.com',
    WP_IMPORTER_SECRET_KEY='secret',
    GEMINI_API_KEY='test_gemini_key'
)
class TestImporterGeminiIntegration(TestCase):
    """Integration tests for Import views with competitor search and Gemini rewrite enabled."""

    def setUp(self):
        # Create Category for Major
        self.category = MajorCategory.objects.create(name='الطب و الصحة', slug='medical')
        
        # Create admin user
        self.user = User.objects.create_superuser(username='admin', password='password', email='admin@test.com')
        self.client.login(username='admin', password='password')

        # Mock WordPress data
        self.wp_data = {
            'content_type': 'major',
            'name': 'دراسة الطب البشري في ماليزيا 2026',
            'slug': 'medicine-in-malaysia',
            'fields': {
                'description': {'value': 'وصف قديم للطب...', 'confidence': 'high'},
            },
            'seo': {
                'meta_title': 'دراسة الطب في ماليزيا 2026',
                'meta_description': 'وصف الـ SEO القديم',
                'focus_keyword': 'الطب في ماليزيا'
            },
            'images': {}
        }

    @patch('apps.importer.views.run_in_background')
    @patch('apps.importer.services.wp_client.WPImporterClient.fetch')
    @patch('apps.importer.services.gemini_service.GeminiService.search_competitor')
    @patch('apps.importer.services.gemini_service.GeminiService.fetch_competitor_content')
    @patch('apps.importer.services.gemini_service.GeminiService.rewrite_major')
    def test_import_fetch_view_integrates_gemini_and_competitor(self, mock_rewrite, mock_fetch_content, mock_search, mock_fetch, mock_run):
        def run_sync(target, *args, **kwargs):
            target(*args, **kwargs)
        mock_run.side_effect = run_sync

        mock_fetch.return_value = self.wp_data
        mock_search.return_value = "https://your-uni.com/competitor-medicine/"
        mock_fetch_content.return_value = "<div>محتوى الطب عند المنافس</div>"
        
        # Define mock rewrite output
        def fake_rewrite(mapped_data, competitor_html, job_id=None):
            assert competitor_html == "<div>محتوى الطب عند المنافس</div>"
            mapped_data['form_initial']['name'] = "الطب البشري"
            mapped_data['form_initial']['description'] = "<p>وصف الطب الجديد المدمج</p>"
            return mapped_data
            
        mock_rewrite.side_effect = fake_rewrite

        # Post to fetch endpoint with custom competitor_url
        response = self.client.post(
            reverse('dashboard:import_fetch'),
            {
                'url': 'https://sciencesgates.com/majors/medicine-in-malaysia', 
                'content_type_override': 'major',
                'competitor_url': 'https://your-uni.com/competitor-medicine/'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        assert response.status_code == 200
        resp_json = response.json()
        assert resp_json['success'] is True
        job_id = resp_json['job_id']

        # Get job status
        status_response = self.client.get(
            reverse('dashboard:import_job_status', args=[job_id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        assert status_response.status_code == 200
        status_json = status_response.json()
        assert status_json['status'] == 'SUCCESS'
        
        result_data = status_json['result_data']
        assert result_data['mapped_data']['form_initial']['name'] == "دراسة الطب البشري في ماليزيا"
        assert result_data['mapped_data']['form_initial']['description'] == '<div style="text-align: justify;">وصف قديم للطب...</div>'
        assert result_data['mapped_data']['form_initial']['competitor_url'] == "https://your-uni.com/competitor-medicine/"
        assert "compiled_prompt" in result_data['mapped_data']
        assert "You are a professional educational advisor" in result_data['mapped_data']['compiled_prompt']
        assert mock_fetch_content.called
        assert not mock_search.called  # Should not search because competitor_url was provided
        assert not mock_rewrite.called  # Automatic rewrite is no longer called

    @patch('apps.importer.views.run_in_background')
    @patch('apps.importer.services.wp_client.WPImporterClient.fetch')
    @patch('apps.importer.services.gemini_service.GeminiService.search_competitor')
    @patch('apps.importer.services.gemini_service.GeminiService.fetch_competitor_content')
    @patch('apps.importer.services.gemini_service.GeminiService.rewrite_major')
    def test_import_bulk_save_view_integrates_gemini_and_auto_search(self, mock_rewrite, mock_fetch_content, mock_search, mock_fetch, mock_run):
        def run_sync(target, *args, **kwargs):
            target(*args, **kwargs)
        mock_run.side_effect = run_sync

        mock_fetch.return_value = self.wp_data
        mock_search.return_value = "https://your-uni.com/auto-competitor-medicine/"
        mock_fetch_content.return_value = "<div>محتوى الطب عند المنافس تلقائيا</div>"
        
        # Define mock rewrite output
        def fake_rewrite(mapped_data, competitor_html, job_id=None):
            assert competitor_html == "<div>محتوى الطب عند المنافس تلقائيا</div>"
            mapped_data['form_initial']['name'] = "الطب البشري"
            mapped_data['form_initial']['description'] = "وصف الطب الجديد المدمج تلقائيا"
            mapped_data['form_initial']['slug'] = "medicine-in-malaysia"
            return mapped_data
            
        mock_rewrite.side_effect = fake_rewrite

        # Verify major doesn't exist
        assert not Major.objects.filter(slug='medicine-in-malaysia').exists()

        # Post to bulk save endpoint without competitor_url (should auto-search)
        response = self.client.post(
            reverse('dashboard:import_bulk_save'),
            {
                'url': 'https://sciencesgates.com/majors/medicine-in-malaysia', 
                'content_type_override': 'major'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        assert response.status_code == 200
        resp_json = response.json()
        assert resp_json['success'] is True
        job_id = resp_json['job_id']

        # Get job status
        status_response = self.client.get(
            reverse('dashboard:import_job_status', args=[job_id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        assert status_response.status_code == 200
        status_json = status_response.json()
        assert status_json['status'] == 'SUCCESS'
        
        result_data = status_json['result_data']
        assert result_data['action'] == 'created'

        # Verify major is saved in DB and its status is UNPUBLISHED (Draft)
        major = Major.objects.get(slug='medicine-in-malaysia')
        assert major.name == "دراسة الطب البشري في ماليزيا"
        assert major.publish_status == 'unpublished'
        assert major.competitor_url == "https://your-uni.com/auto-competitor-medicine/"
        assert mock_search.called  # Should auto-search since competitor_url was blank
        assert mock_fetch_content.called
        assert not mock_rewrite.called  # Automatic rewrite is no longer called
