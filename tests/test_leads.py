import pytest
from django.urls import reverse
from django.contrib.messages import get_messages
from apps.leads.models import Lead, LeadType, LeadStatus
from apps.leads.forms import ContactLeadForm, RegistrationLeadForm

@pytest.mark.django_db
class TestLeadsSystem:
    """Tests for the modernized Leads and Registration system."""

    def test_contact_lead_form_valid(self):
        form_data = {
            'lead_type': LeadType.CONTACT,
            'name': 'احمد علي',
            'email': 'ahmed@example.com',
            'phone': '+201111111111',
            'nationality': 'مصري',
            'message': 'استفسار عن الخدمات',
            'website': '',
        }
        form = ContactLeadForm(data=form_data)
        assert form.is_valid(), form.errors
        lead = form.save()
        assert lead.nationality == 'مصري'
        assert lead.lead_type == LeadType.CONTACT

    def test_contact_lead_form_custom_nationality(self):
        form_data = {
            'lead_type': LeadType.CONTACT,
            'name': 'جون دو',
            'email': 'john@example.com',
            'phone': '+447777777777',
            'nationality': 'دولة اخرى غير موجودة',
            'custom_nationality': 'بريطاني',
            'message': 'استفسار',
            'website': '',
        }
        form = ContactLeadForm(data=form_data)
        assert form.is_valid(), form.errors
        lead = form.save()
        assert lead.nationality == 'بريطاني'

    def test_contact_lead_form_email_required(self):
        form_data = {
            'lead_type': LeadType.CONTACT,
            'name': 'أحمد',
            'email': '',
            'phone': '+201111111111',
            'nationality': 'مصري',
        }
        form = ContactLeadForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_registration_lead_form_valid(self):
        form_data = {
            'lead_type': LeadType.REGISTRATION,
            'name': 'محمد خالد',
            'email': 'mohamed@example.com',
            'phone': '+966555555555',
            'nationality': 'سعودي',
            'institution_name': 'جامعة مالايا',
            'residence_country': 'السعودية',
            'study_level': 'بكالوريوس',
            'address': 'الرياض، حي الصحافة',
            'message': 'ملاحظات التسجيل',
            'website': '',
        }
        form = RegistrationLeadForm(data=form_data)
        assert form.is_valid(), form.errors
        lead = form.save()
        assert lead.nationality == 'سعودي'
        assert lead.lead_type == LeadType.REGISTRATION
        assert lead.institution_name == 'جامعة مالايا'
        assert lead.residence_country == 'السعودية'
        assert lead.study_level == 'بكالوريوس'
        assert lead.address == 'الرياض، حي الصحافة'

    def test_registration_lead_form_email_required(self):
        form_data = {
            'lead_type': LeadType.REGISTRATION,
            'name': 'محمد خالد',
            'email': '',
            'phone': '+966555555555',
            'nationality': 'سعودي',
            'institution_name': 'جامعة مالايا',
            'residence_country': 'السعودية',
            'study_level': 'بكالوريوس',
            'address': 'الرياض، حي الصحافة',
        }
        form = RegistrationLeadForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_lead_submit_view_routing_registration(self, client):
        url = reverse('leads:submit')
        post_data = {
            'lead_type': 'registration',
            'name': 'ياسر محمد',
            'email': 'yasser@example.com',
            'phone': '+966555555555',
            'nationality': 'سعودي',
            'institution_name': 'معهد لغة',
            'residence_country': 'السعودية',
            'study_level': 'معهد اللغة',
            'address': 'جدة',
            'message': 'أرغب بالتسجيل',
            'website': '',
        }
        response = client.post(url, post_data, follow=True)
        assert response.status_code == 200
        
        # Verify success message and type
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) > 0
        assert 'تم استقبال طلب التسجيل بنجاح' in str(messages[0])

        # Verify DB entry
        lead = Lead.objects.get(email='yasser@example.com')
        assert lead.lead_type == LeadType.REGISTRATION
        assert lead.institution_name == 'معهد لغة'

    def test_lead_submit_view_routing_contact(self, client):
        url = reverse('leads:submit')
        post_data = {
            'lead_type': 'contact',
            'name': 'ياسر محمد',
            'email': 'yasser_contact@example.com',
            'phone': '+966555555555',
            'nationality': 'سعودي',
            'message': 'استفسار عام',
            'website': '',
        }
        response = client.post(url, post_data, follow=True)
        assert response.status_code == 200
        
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) > 0
        assert 'تم استقبال استفسارك بنجاح' in str(messages[0])

        lead = Lead.objects.get(email='yasser_contact@example.com')
        assert lead.lead_type == LeadType.CONTACT

    def test_dashboard_lead_list_separated(self, admin_client):
        # Create one registration and one contact lead
        Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='طالب تسجيل',
            email='student@example.com',
            phone='+201111111111',
            nationality='مصري',
            institution_name='جامعة',
        )
        Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='مستفسر عادي',
            email='asker@example.com',
            phone='+201111111111',
            nationality='مصري',
        )

        url = reverse('dashboard:lead_list')
        
        # Access registrations (default)
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.context['page_title'] == 'طلبات التسجيل'
        assert response.context['lead_type_filter'] == 'registration'
        leads = list(response.context['leads'])
        assert any(l.email == 'student@example.com' for l in leads)
        assert not any(l.email == 'asker@example.com' for l in leads)

        # Access contacts explicitly
        response = admin_client.get(url + '?lead_type=contact')
        assert response.status_code == 200
        assert response.context['page_title'] == 'إدارة الرسائل والاستفسارات'
        assert response.context['lead_type_filter'] == 'contact'
        leads = list(response.context['leads'])
        assert any(l.email == 'asker@example.com' for l in leads)
        assert not any(l.email == 'student@example.com' for l in leads)

        # Search registrations by institution name
        response = admin_client.get(url + '?lead_type=registration&search=جامعة')
        assert response.status_code == 200
        leads = list(response.context['leads'])
        assert any(l.email == 'student@example.com' for l in leads)

        # Search registrations by institution name not matching
        response = admin_client.get(url + '?lead_type=registration&search=مدرسة')
        assert response.status_code == 200
        leads = list(response.context['leads'])
        assert not any(l.email == 'student@example.com' for l in leads)

        # Filter by nationality
        response = admin_client.get(url + '?lead_type=registration&nationality=مصري')
        assert response.status_code == 200
        leads = list(response.context['leads'])
        assert any(l.email == 'student@example.com' for l in leads)

        # Filter by nationality not matching
        response = admin_client.get(url + '?lead_type=registration&nationality=سعودي')
        assert response.status_code == 200
        leads = list(response.context['leads'])
        assert not any(l.email == 'student@example.com' for l in leads)

    def test_dashboard_lead_export_separated(self, admin_client):
        Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='طالب تسجيل',
            email='student_export@example.com',
            phone='+201111111111',
            nationality='مصري',
            institution_name='جامعة مالايا',
            residence_country='مصر',
            study_level='بكالوريوس',
            address='القاهرة',
        )
        Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='مستفسر عادي',
            email='asker_export@example.com',
            phone='+201111111111',
            nationality='مصري',
            message='سؤال',
        )

        url = reverse('dashboard:lead_export')

        # Export Registrations
        response = admin_client.get(url + '?lead_type=registration')
        assert response.status_code == 200
        content = response.content.decode('utf-8-sig') if hasattr(response.content, 'decode') else response.content
        assert 'المؤسسة التعليمية' in content
        assert 'student_export@example.com' in content
        assert 'asker_export@example.com' not in content

        # Export Contacts
        response = admin_client.get(url + '?lead_type=contact')
        assert response.status_code == 200
        content = response.content.decode('utf-8-sig') if hasattr(response.content, 'decode') else response.content
        assert 'الرسالة الاستفسارية' in content
        assert 'asker_export@example.com' in content
        assert 'student_export@example.com' not in content

    def test_country_info_lookup(self):
        from apps.leads.countries import get_country_info, DEFAULT_COUNTRY, DEFAULT_CODE
        # Valid country
        iso, code, placeholder = get_country_info('eg')
        assert iso == 'eg'
        assert code == '+20'
        
        iso_ae, code_ae, _ = get_country_info('ae')
        assert iso_ae == 'ae'
        assert code_ae == '+971'
        
        # Invalid / unknown fallback to Saudi Arabia
        iso_unknown, code_unknown, _ = get_country_info('xx')
        assert iso_unknown == DEFAULT_COUNTRY
        assert code_unknown == DEFAULT_CODE

    def test_phone_countries_context_auto_detect(self, rf):
        from apps.core.context_processors import phone_countries_context
        # Request with Cloudflare country header for Egypt
        request = rf.get('/', HTTP_CF_IPCOUNTRY='EG')
        context = phone_countries_context(request)
        assert context['default_country'] == 'eg'
        assert context['default_code'] == '+20'

        # Request without header defaults to Saudi Arabia
        request_default = rf.get('/')
        context_default = phone_countries_context(request_default)
        assert context_default['default_country'] == 'sa'
        assert context_default['default_code'] == '+966'

