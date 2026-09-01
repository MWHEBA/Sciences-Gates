import os
import json
import pytest
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core import mail
from hypothesis import given, settings, strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase
from django.urls import reverse
from apps.leads.models import Lead, LeadType


@pytest.mark.django_db
class TestLeadTypeChoices:
    """Test cases for LeadType choices."""
    
    def test_lead_type_registration_choice(self):
        """Test REGISTRATION choice exists."""
        from apps.leads.models import LeadType
        
        assert LeadType.REGISTRATION == 'registration'
        assert LeadType.REGISTRATION == LeadType.REGISTRATION
    
    def test_lead_type_contact_choice(self):
        """Test CONTACT choice exists."""
        from .models import LeadType
        
        assert LeadType.CONTACT == 'contact'
        assert LeadType.CONTACT == LeadType.CONTACT
    
    def test_lead_type_choices_count(self):
        """Test that exactly two lead types exist."""
        from .models import LeadType
        
        assert len(LeadType.choices) == 2
    
    def test_lead_type_display_names(self):
        """Test that lead types have Arabic display names."""
        from .models import LeadType
        
        choices_dict = dict(LeadType.choices)
        assert choices_dict['registration'] == 'طلب تسجيل'
        assert choices_dict['contact'] == 'استفسار'


class LeadModelCreationTests(TestCase):
    """Test cases for Lead model creation."""
    
    def setUp(self):
        """Create a test lead."""
        from .models import Lead, LeadType
        
        self.lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='أحمد محمد',
            email='ahmed@example.com',
            phone='+201234567890',
            message='أريد التسجيل في الجامعة'
        )
    
    def test_lead_creation_with_required_fields(self):
        """Test that lead is created with required fields."""
        self.assertEqual(self.lead.lead_type, LeadType.REGISTRATION)
        self.assertEqual(self.lead.name, 'أحمد محمد')
        self.assertEqual(self.lead.email, 'ahmed@example.com')
        self.assertEqual(self.lead.phone, '+201234567890')
        self.assertEqual(self.lead.message, 'أريد التسجيل في الجامعة')
    
    def test_lead_creation_with_tracking_fields(self):
        """Test that lead can be created with tracking fields."""
        from .models import Lead, LeadType
        
        lead = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='فاطمة علي',
            email='fatima@example.com',
            phone='+201234567891',
            message='استفسار عن البرامج',
            source_page='https://example.com/universities/cairo',
            referrer='https://google.com'
        )
        
        self.assertEqual(lead.source_page, 'https://example.com/universities/cairo')
        self.assertEqual(lead.referrer, 'https://google.com')
    

    def test_lead_creation_with_status_fields(self):
        """Test that lead can be created with status fields."""
        from .models import Lead, LeadType
        
        lead = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='سارة محمد',
            email='sarah@example.com',
            phone='+201234567893',
            message='استفسار',
            is_read=True,
            notes='تم الرد على الاستفسار'
        )
        
        self.assertTrue(lead.is_read)
        self.assertEqual(lead.notes, 'تم الرد على الاستفسار')
    
    def test_lead_default_is_read_false(self):
        """Test that is_read defaults to False."""
        self.assertFalse(self.lead.is_read)
    
    def test_lead_default_notes_empty(self):
        """Test that notes defaults to empty string."""
        self.assertEqual(self.lead.notes, '')
    
    def test_lead_timestamps_created(self):
        """Test that created_at and updated_at are set."""
        self.assertIsNotNone(self.lead.created_at)
        self.assertIsNotNone(self.lead.updated_at)
        self.assertIsInstance(self.lead.created_at, type(timezone.now()))
    
    def test_lead_timestamps_equal_on_creation(self):
        """Test that created_at and updated_at are equal on creation."""
        # Allow small time difference due to processing
        time_diff = abs((self.lead.updated_at - self.lead.created_at).total_seconds())
        self.assertLess(time_diff, 1)


class LeadModelMethodsTests(TestCase):
    """Test cases for Lead model methods."""
    
    def setUp(self):
        """Create test leads."""
        from .models import Lead, LeadType
        
        self.lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='أحمد محمد',
            email='ahmed@example.com',
            phone='+201234567890',
            message='أريد التسجيل',
            is_read=False
        )
    
    def test_mark_as_read_method(self):
        """Test mark_as_read method."""
        self.assertFalse(self.lead.is_read)
        
        self.lead.mark_as_read()
        
        self.assertTrue(self.lead.is_read)
        
        # Verify it's saved to database
        refreshed_lead = Lead.objects.get(pk=self.lead.pk)
        self.assertTrue(refreshed_lead.is_read)
    
    def test_lead_str_representation(self):
        """Test __str__ method."""
        from .models import LeadType
        
        expected = f'{self.lead.name} - {self.lead.get_lead_type_display()}'
        self.assertEqual(str(self.lead), expected)
        self.assertEqual(str(self.lead), 'أحمد محمد - طلب تسجيل')
    
    def test_lead_str_with_contact_type(self):
        """Test __str__ method with contact type."""
        from .models import Lead, LeadType
        
        contact_lead = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='فاطمة علي',
            email='fatima@example.com',
            phone='+201234567891',
            message='استفسار'
        )
        
        expected = f'{contact_lead.name} - {contact_lead.get_lead_type_display()}'
        self.assertEqual(str(contact_lead), expected)
        self.assertEqual(str(contact_lead), 'فاطمة علي - استفسار')


class LeadModelQueryingTests(TestCase):
    """Test cases for Lead model querying."""
    
    def setUp(self):
        """Create test leads."""
        from .models import Lead, LeadType
        
        # Create registration leads
        for i in range(3):
            Lead.objects.create(
                lead_type=LeadType.REGISTRATION,
                name=f'مسجل {i}',
                email=f'registration{i}@example.com',
                phone=f'+2010000000{i}',
                message='تسجيل'
            )
        
        # Create contact leads
        for i in range(2):
            Lead.objects.create(
                lead_type=LeadType.CONTACT,
                name=f'مستفسر {i}',
                email=f'contact{i}@example.com',
                phone=f'+2010000001{i}',
                message='استفسار'
            )
        
        # Create read lead
        Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='مقروء',
            email='read@example.com',
            phone='+201234567890',
            message='تسجيل',
            is_read=True
        )
    
    def test_filter_by_lead_type_registration(self):
        """Test filtering leads by registration type."""
        from .models import Lead, LeadType
        
        registration_leads = Lead.objects.filter(lead_type=LeadType.REGISTRATION)
        self.assertEqual(registration_leads.count(), 4)  # 3 + 1 read
    
    def test_filter_by_lead_type_contact(self):
        """Test filtering leads by contact type."""
        from .models import Lead, LeadType
        
        contact_leads = Lead.objects.filter(lead_type=LeadType.CONTACT)
        self.assertEqual(contact_leads.count(), 2)
    
    def test_filter_by_is_read_true(self):
        """Test filtering read leads."""
        from .models import Lead
        
        read_leads = Lead.objects.filter(is_read=True)
        self.assertEqual(read_leads.count(), 1)
    
    def test_filter_by_is_read_false(self):
        """Test filtering unread leads."""
        from .models import Lead
        
        unread_leads = Lead.objects.filter(is_read=False)
        # 3 registration + 2 contact = 5 unread (the read one is excluded)
        self.assertEqual(unread_leads.count(), 5)
    
    def test_ordering_by_created_at_descending(self):
        """Test that leads are ordered by created_at descending."""
        leads = Lead.objects.all()
        
        for i in range(len(leads) - 1):
            self.assertGreaterEqual(leads[i].created_at, leads[i + 1].created_at)
    
    def test_count_all_leads(self):
        """Test counting all leads."""
        total_leads = Lead.objects.count()
        self.assertEqual(total_leads, 6)


class LeadModelIndexesTests(TestCase):
    """Test cases for Lead model database indexes."""
    
    def test_created_at_index_exists(self):
        """Test that created_at has an index."""
        # Check Meta.indexes
        indexes = Lead._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        self.assertIn(['created_at'], index_fields)
    
    def test_lead_type_index_exists(self):
        """Test that lead_type has an index."""
        indexes = Lead._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        self.assertIn(['lead_type'], index_fields)
    
    def test_is_read_index_exists(self):
        """Test that is_read has an index."""
        indexes = Lead._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        self.assertIn(['is_read'], index_fields)
    
    def test_lead_type_field_has_db_index(self):
        """Test that lead_type field has db_index=True."""
        field = Lead._meta.get_field('lead_type')
        self.assertTrue(field.db_index)
    
    def test_is_read_field_has_db_index(self):
        """Test that is_read field has db_index=True."""
        field = Lead._meta.get_field('is_read')
        self.assertTrue(field.db_index)


class LeadModelMetaTests(TestCase):
    """Test cases for Lead model Meta class."""
    
    def test_verbose_name(self):
        """Test verbose name."""
        self.assertEqual(Lead._meta.verbose_name, 'رسالة')
    
    def test_verbose_name_plural(self):
        """Test verbose name plural."""
        self.assertEqual(Lead._meta.verbose_name_plural, 'الرسائل')
    
    def test_default_ordering(self):
        """Test default ordering."""
        self.assertEqual(Lead._meta.ordering, ['-created_at'])


class LeadModelFieldsTests(TestCase):
    """Test cases for Lead model fields."""
    
    def test_lead_type_field_max_length(self):
        """Test lead_type field max_length."""
        field = Lead._meta.get_field('lead_type')
        self.assertEqual(field.max_length, 20)
    
    def test_name_field_max_length(self):
        """Test name field max_length."""
        field = Lead._meta.get_field('name')
        self.assertEqual(field.max_length, 200)
    
    def test_email_field_type(self):
        """Test email field is EmailField."""
        field = Lead._meta.get_field('email')
        # EmailField is stored as CharField in Django
        self.assertIn(field.get_internal_type(), ['EmailField', 'CharField'])
    
    def test_phone_field_max_length(self):
        """Test phone field max_length."""
        field = Lead._meta.get_field('phone')
        self.assertEqual(field.max_length, 50)
    
    def test_source_page_field_blank(self):
        """Test source_page field is blank=True."""
        field = Lead._meta.get_field('source_page')
        self.assertTrue(field.blank)
    
    def test_referrer_field_blank(self):
        """Test referrer field is blank=True."""
        field = Lead._meta.get_field('referrer')
        self.assertTrue(field.blank)
    

    def test_notes_field_blank(self):
        """Test notes field is blank=True."""
        field = Lead._meta.get_field('notes')
        self.assertTrue(field.blank)


class LeadPropertyBasedTests(HypothesisTestCase):
    """Property-based tests for Lead model.
    
    **Validates: Requirements 5, 23**
    """
    
    @settings(deadline=None)
    @given(
        lead_type=st.sampled_from([LeadType.REGISTRATION, LeadType.CONTACT]),
        name=st.text(min_size=1, max_size=200),
        email=st.emails(),
        phone=st.text(min_size=1, max_size=20),
        message=st.text(min_size=1)
    )
    def test_lead_creation_with_valid_data(self, lead_type, name, email, phone, message):
        """Property: Lead can be created with any valid combination of required fields.
        
        **Validates: Requirement 5.2** - WHEN a user submits a Lead_Form, THE Platform SHALL store the submission in the database
        """
        from .models import Lead, LeadType
        
        lead = Lead.objects.create(
            lead_type=lead_type,
            name=name,
            email=email,
            phone=phone,
            message=message
        )
        
        self.assertEqual(lead.lead_type, lead_type)
        self.assertEqual(lead.name, name)
        self.assertEqual(lead.email, email)
        self.assertEqual(lead.phone, phone)
        self.assertEqual(lead.message, message)
    

    @settings(deadline=None)
    @given(
        is_read=st.booleans(),
        notes=st.text(max_size=1000)
    )
    def test_lead_status_fields(self, is_read, notes):
        """Property: Lead can store any combination of status fields.
        
        **Validates: Requirement 23.2** - THE Custom_Dashboard SHALL display lead submission details: ... is_read, notes
        """
        from .models import Lead, LeadType
        
        lead = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='اختبار',
            email='test@example.com',
            phone='+201234567890',
            message='رسالة',
            is_read=is_read,
            notes=notes
        )
        
        self.assertEqual(lead.is_read, is_read)
        self.assertEqual(lead.notes, notes)
    
    @given(
        lead_type=st.sampled_from([LeadType.REGISTRATION, LeadType.CONTACT])
    )
    def test_lead_type_filtering(self, lead_type):
        """Property: Leads can be filtered by lead_type and retrieved correctly.
        
        **Validates: Requirement 23.3** - THE Custom_Dashboard SHALL allow filtering leads by form type (Registration Request or Contact Request)
        """
        from .models import Lead, LeadType
        
        # Create leads of both types
        Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='تسجيل',
            email='reg@example.com',
            phone='+201234567890',
            message='رسالة'
        )
        Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='استفسار',
            email='contact@example.com',
            phone='+201234567891',
            message='رسالة'
        )
        
        # Filter by the given lead_type
        filtered_leads = Lead.objects.filter(lead_type=lead_type)
        
        # All filtered leads should have the correct type
        for lead in filtered_leads:
            self.assertEqual(lead.lead_type, lead_type)
    
    @given(
        is_read=st.booleans()
    )
    def test_lead_read_status_filtering(self, is_read):
        """Property: Leads can be filtered by is_read status and retrieved correctly.
        
        **Validates: Requirement 23** - THE Custom_Dashboard SHALL display all submitted Lead_Form entries
        """
        from .models import Lead, LeadType
        
        # Create leads with different read statuses
        Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='مقروء',
            email='read@example.com',
            phone='+201234567890',
            message='رسالة',
            is_read=True
        )
        Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='غير مقروء',
            email='unread@example.com',
            phone='+201234567891',
            message='رسالة',
            is_read=False
        )
        
        # Filter by the given is_read status
        filtered_leads = Lead.objects.filter(is_read=is_read)
        
        # All filtered leads should have the correct read status
        for lead in filtered_leads:
            self.assertEqual(lead.is_read, is_read)
    
    @given(
        st.lists(
            st.tuples(
                st.sampled_from([LeadType.REGISTRATION, LeadType.CONTACT]),
                st.text(min_size=1, max_size=200),
                st.emails(),
                st.text(min_size=1, max_size=20),
                st.text(min_size=1)
            ),
            min_size=1,
            max_size=10
        )
    )
    def test_multiple_leads_creation_and_retrieval(self, leads_data):
        """Property: Multiple leads can be created and retrieved correctly.
        
        **Validates: Requirement 5.2** - WHEN a user submits a Lead_Form, THE Platform SHALL store the submission in the database
        """
        from .models import Lead, LeadType
        
        created_leads = []
        for lead_type, name, email, phone, message in leads_data:
            lead = Lead.objects.create(
                lead_type=lead_type,
                name=name,
                email=email,
                phone=phone,
                message=message
            )
            created_leads.append(lead)
        
        # Verify all leads were created
        self.assertEqual(Lead.objects.count(), len(leads_data))
        
        # Verify each lead can be retrieved
        for created_lead in created_leads:
            retrieved_lead = Lead.objects.get(pk=created_lead.pk)
            self.assertEqual(retrieved_lead.lead_type, created_lead.lead_type)
            self.assertEqual(retrieved_lead.name, created_lead.name)
            self.assertEqual(retrieved_lead.email, created_lead.email)



@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    ADMIN_EMAIL='admin@example.com',
    DEFAULT_FROM_EMAIL='noreply@example.com'
)
class LeadEmailNotificationSignalTests(TestCase):
    """Test cases for lead email notification signal.
    
    **Validates: Requirement 5.7** - THE Platform SHALL send email notifications to administrators when a Lead_Form is submitted
    """
    
    def test_email_sent_on_lead_creation(self):
        """Test that admin email and applicant confirmation email are sent when a new lead is created."""
        from .models import Lead, LeadType
        
        # Clear the test mailbox
        mail.outbox = []
        
        # Create a new lead with email
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='أحمد محمد',
            email='ahmed@example.com',
            phone='+201234567890',
            message='أريد التسجيل في الجامعة'
        )
        
        # Check that two emails were sent (1 for Admin, 1 for Applicant)
        self.assertEqual(len(mail.outbox), 2)
        
        # Check admin email details
        admin_email = mail.outbox[0]
        self.assertIn('أحمد محمد', admin_email.subject)
        self.assertIn('طلب تسجيل', admin_email.subject)

        # Check applicant confirmation email details
        user_email = mail.outbox[1]
        self.assertEqual(user_email.to, ['ahmed@example.com'])
        self.assertIn('تم استلام طلب التسجيل بنجاح', user_email.subject)
        self.assertIn('أحمد محمد', user_email.body)
        self.assertIn('https://wa.me/', user_email.body)

    def test_applicant_confirmation_email_sent(self):
        """Test applicant confirmation email content and pre-filled WhatsApp link."""
        from .models import Lead, LeadType
        mail.outbox = []

        lead = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='سارة محمود',
            email='sara@example.com',
            phone='+201099998888',
            message='استفسار عن القبول'
        )

        self.assertEqual(len(mail.outbox), 2)
        user_email = mail.outbox[1]

        self.assertEqual(user_email.to, ['sara@example.com'])
        self.assertIn('تم استلام استفسارك بنجاح', user_email.subject)
        self.assertIn('سارة محمود', user_email.body)
        self.assertIn('wa.me', user_email.body)

    def test_email_not_sent_on_lead_update(self):
        """Test that email is NOT sent when an existing lead is updated."""
        from .models import Lead, LeadType
        
        # Create a lead
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='أحمد محمد',
            email='ahmed@example.com',
            phone='+201234567890',
            message='أريد التسجيل'
        )
        
        # Clear the mailbox
        mail.outbox = []
        
        # Update the lead
        lead.is_read = True
        lead.notes = 'تم الرد'
        lead.save()
        
        # Check that no email was sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_email_contains_lead_details(self):
        """Test that email contains all lead details."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='فاطمة علي',
            email='fatima@example.com',
            phone='+201234567891',
            message='استفسار عن البرامج',
            source_page='https://example.com/universities',
            referrer='https://google.com'
        )
        
        # Check email content (admin email)
        email = mail.outbox[0]
        self.assertIn('فاطمة علي', email.body)
        self.assertIn('fatima@example.com', email.body)
        self.assertIn('+201234567891', email.body)
        self.assertIn('استفسار عن البرامج', email.body)
        self.assertIn('https://example.com/universities', email.body)
        self.assertIn('https://google.com', email.body)
    
    def test_email_subject_in_arabic(self):
        """Test that email subject is in Arabic."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='محمود حسن',
            email='mahmoud@example.com',
            phone='+201234567892',
            message='تسجيل جديد'
        )
        
        email = mail.outbox[0]
        # Subject should contain Arabic text
        self.assertIn('محمود حسن', email.subject)
        self.assertIn('طلب تسجيل', email.subject)
    
    def test_email_body_in_arabic(self):
        """Test that email body is in Arabic."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='سارة محمد',
            email='sarah@example.com',
            phone='+201234567893',
            message='استفسار'
        )
        
        email = mail.outbox[0]
        # Body should contain Arabic text
        self.assertIn('الاسم', email.body)
        self.assertIn('البريد الإلكتروني:', email.body)
        self.assertIn('رقم الهاتف:', email.body)
        self.assertIn('نوع الرسالة:', email.body)
    
    def test_email_sent_to_admin_email(self):
        """Test that email is sent to ADMIN_EMAIL."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='علي محمد',
            email='ali@example.com',
            phone='+201234567894',
            message='رسالة'
        )
        
        email = mail.outbox[0]
        self.assertIn('admin@example.com', email.to)
    
    def test_email_from_address(self):
        """Test that email is sent from DEFAULT_FROM_EMAIL."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='خالد أحمد',
            email='khaled@example.com',
            phone='+201234567895',
            message='رسالة'
        )
        
        email = mail.outbox[0]
        self.assertEqual(email.from_email, 'noreply@example.com')
    
    def test_multiple_leads_send_multiple_emails(self):
        """Test that multiple leads send multiple emails."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        # Create first lead
        Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='أحمد',
            email='ahmed@example.com',
            phone='+201234567890',
            message='رسالة 1'
        )
        
        # Create second lead
        Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='فاطمة',
            email='fatima@example.com',
            phone='+201234567891',
            message='رسالة 2'
        )
        
        # Check that four emails were sent (2 per lead)
        self.assertEqual(len(mail.outbox), 4)
    
    def test_email_includes_lead_type_display(self):
        """Test that email includes the display name of lead type."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        # Test with REGISTRATION type
        lead1 = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='اختبار 1',
            email='test1@example.com',
            phone='+201234567890',
            message='رسالة'
        )
        
        email1 = mail.outbox[0]
        self.assertIn('طلب تسجيل', email1.body)
        
        mail.outbox = []
        
        # Test with CONTACT type
        lead2 = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='اختبار 2',
            email='test2@example.com',
            phone='+201234567891',
            message='رسالة'
        )
        
        email2 = mail.outbox[0]
        self.assertIn('استفسار', email2.body)
    
    def test_email_includes_timestamp(self):
        """Test that email includes the submission timestamp."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='اختبار',
            email='test@example.com',
            phone='+201234567890',
            message='رسالة'
        )
        
        email = mail.outbox[0]
        # Email should contain timestamp information
        self.assertIn(str(lead.created_at.year), email.body)
    
    @override_settings(ADMIN_EMAIL='')
    def test_email_not_sent_when_admin_email_empty(self):
        """Test that admin email is not sent when ADMIN_EMAIL is empty and lead has no email."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='اختبار',
            email='',
            phone='+201234567890',
            message='رسالة'
        )
        
        # No email should be sent when admin email is empty and lead email is empty
        self.assertEqual(len(mail.outbox), 0)
    
    def test_email_handles_missing_optional_fields(self):
        """Test that email is sent even when optional fields are missing."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='اختبار',
            email='test@example.com',
            phone='+201234567890',
            message='رسالة'
            # No source_page, referrer, or UTM parameters
        )
        
        # Both admin email and user confirmation email should be sent
        self.assertEqual(len(mail.outbox), 2)
        
        email = mail.outbox[0]
        # Should contain "غير محدد" (not specified) for missing fields in admin email
        self.assertIn('غير محدد', email.body)
    
    def test_email_with_special_characters_in_name(self):
        """Test that email is sent with special characters in name."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='أحمد محمد علي-الشرقاوي',
            email='test@example.com',
            phone='+201234567890',
            message='رسالة'
        )
        
        # Admin email and applicant email should be sent successfully
        self.assertEqual(len(mail.outbox), 2)
        
        email = mail.outbox[0]
        self.assertIn('أحمد محمد علي-الشرقاوي', email.subject)
    
    def test_email_with_long_message(self):
        """Test that email is sent with long message."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        long_message = 'أ' * 1000  # 1000 Arabic characters
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='اختبار',
            email='test@example.com',
            phone='+201234567890',
            message=long_message
        )
        
        # Admin email and applicant email should be sent successfully
        self.assertEqual(len(mail.outbox), 2)
        
        email = mail.outbox[0]
        self.assertIn(long_message, email.body)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    ADMIN_EMAIL='admin@example.com',
    DEFAULT_FROM_EMAIL='noreply@example.com'
)
class LeadEmailNotificationPropertyBasedTests(HypothesisTestCase):
    """Property-based tests for lead email notification signal.
    
    **Validates: Requirement 5.7** - THE Platform SHALL send email notifications to administrators when a Lead_Form is submitted
    """
    
    @settings(deadline=None)
    @given(
        lead_type=st.sampled_from([LeadType.REGISTRATION, LeadType.CONTACT]),
        name=st.text(min_size=1, max_size=200),
        email=st.emails(),
        phone=st.text(min_size=1, max_size=20),
        message=st.text(min_size=1)
    )
    def test_email_sent_for_any_valid_lead(self, lead_type, name, email, phone, message):
        """Property: Emails are sent for any valid lead creation.
        
        **Validates: Requirement 5.7** - THE Platform SHALL send email notifications to administrators when a Lead_Form is submitted
        """
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=lead_type,
            name=name,
            email=email,
            phone=phone,
            message=message
        )
        
        # Both admin notification email and applicant confirmation email should be sent
        self.assertEqual(len(mail.outbox), 2)

        
        # Email should contain sanitized lead name (newlines removed and stripped)
        email_obj = mail.outbox[0]
        sanitized_name = name.replace('\n', ' ').replace('\r', ' ').strip()
        self.assertIn(sanitized_name, email_obj.subject)


class UniversityAndInstituteRegistrationModalTests(TestCase):
    """
    اختبارات إرسال نموذج التسجيل السريع من صفحات الجامعات والمعاهد
    """

    def test_registration_form_normalizes_phd_and_accepts_various_countries(self):
        """التحقق من قبول تسجيل الدكتوراه (دكتوراه/دكتوراة) والدول المتعددة في RegistrationLeadForm"""
        from apps.leads.forms import RegistrationLeadForm

        data = {
            'lead_type': 'registration',
            'name': 'طالب دكتوراه',
            'email': 'phd.student@example.com',
            'phone': '+966501234567',
            'nationality': 'سعودي',
            'institution_name': 'جامعة الملايا',
            'residence_country': 'المملكة العربية السعودية',
            'study_level': 'دكتوراه',
            'address': 'الرياض - حي النخيل',
            'message': 'أرغب بالتسجيل في برنامج دكتوراه الهندسة',
        }
        form = RegistrationLeadForm(data=data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        self.assertEqual(form.cleaned_data['study_level'], 'دكتوراه')
        self.assertEqual(form.cleaned_data['residence_country'], 'المملكة العربية السعودية')

    def test_registration_form_normalizes_language_institute(self):
        """التحقق من قبول تسجيل معهد اللغة (معهد لغة / معهد اللغة)"""
        from apps.leads.forms import RegistrationLeadForm

        data = {
            'lead_type': 'registration',
            'name': 'طالب معهد',
            'email': 'institute.student@example.com',
            'phone': '+905551234567',
            'nationality': 'تركي',
            'institution_name': 'معهد EMS للغات',
            'residence_country': 'تركيا',
            'study_level': 'معهد لغة',
            'address': 'إسطنبول',
            'message': 'أريد كورس لغة 6 أشهر',
        }
        form = RegistrationLeadForm(data=data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        self.assertEqual(form.cleaned_data['study_level'], 'معهد اللغة')
        self.assertEqual(form.cleaned_data['residence_country'], 'تركيا')

    def test_registration_submit_from_university_page_preserves_source_page(self):
        """التحقق من حفظ رابط صفحة الجامعة المصدر عند تقديم طلب تسجيل"""
        from django.urls import reverse
        url = reverse('leads:submit')
        payload = {
            'lead_type': 'registration',
            'name': 'محمد عبد الله',
            'email': 'mohamed@example.com',
            'country_code': '+60',
            'phone_number': '123456789',
            'nationality': 'مصري',
            'institution_name': 'جامعة UKM',
            'residence_country': 'مصر',
            'study_level': 'بكالوريوس',
            'address': 'القاهرة',
            'source_page': 'https://sciencesgates.com/universities/ukm/',
        }
        response = self.client.post(url, payload, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('lead_type=registration', response.url)
        self.assertIn('subtype=university', response.url)

        lead = Lead.objects.filter(email='mohamed@example.com').first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.source_page, 'https://sciencesgates.com/universities/ukm/')

    def test_double_submit_deduplication(self):
        """Test that rapid double-clicks (submitting twice in seconds) create only 1 Lead record."""
        url = reverse('leads:submit')
        payload = {
            'lead_type': 'contact',
            'name': 'خالد سامي',
            'email': 'khaled_double@example.com',
            'phone': '+201099887766',
            'nationality': 'مصري',
            'message': 'استفسار أولي',
        }
        # First submission
        res1 = self.client.post(url, payload, follow=True)
        self.assertEqual(res1.status_code, 200)

        # Second submission immediately
        res2 = self.client.post(url, payload, follow=True)
        self.assertEqual(res2.status_code, 200)

        # Exactly 1 Lead record should exist in DB
        leads_count = Lead.objects.filter(email='khaled_double@example.com').count()
        self.assertEqual(leads_count, 1)

    def test_lead_source_page_normalization_and_entity_resolution(self):
        """Test URL normalization to HTTPS and smart Arabic entity name resolution."""
        from apps.articles.models import Article
        Article.objects.create(title="دليل الدراسة في ماليزيا", slug="دليل-الدراسة-في-ماليزيا", content="محتوى تجريبي")

        lead = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='سارة كمال',
            phone='+60123456789',
            source_page='/articles/%D8%AF%D9%84%D9%8A%D9%84-%D8%A7%D9%84%D8%AF%D8%B1%D8%A7%D8%B3%D8%A9-%D9%81%D9%8A-%D9%85%D8%A7%D9%84%D9%8A%D8%B2%D9%8A%D8%A7/'
        )
        self.assertTrue(lead.source_page.startswith('https://sciencesgates.com/articles/'))
        self.assertIn('دليل-الدراسة-في-ماليزيا', lead.source_page_decoded)
        self.assertEqual(lead.source_page_name, 'مقال: دليل الدراسة في ماليزيا')

        lead_uni = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='سارة كمال',
            phone='+60123456789',
            source_page='/universities/%D8%AC%D8%A7%D9%85%D8%B9%D8%A9-%D8%AA%D8%A7%D9%8A%D9%84%D9%88%D8%B1/'
        )
        self.assertTrue(lead_uni.source_page.startswith('https://sciencesgates.com/universities/'))
        self.assertIn('جامعة-تايلور', lead_uni.source_page_decoded)
        self.assertEqual(lead_uni.source_page_name, 'جامعة: جامعة تايلور')

    def test_lead_phone_clean_whatsapp_link(self):
        """Test phone cleaning and WhatsApp link validation."""
        lead_valid = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='علي سالم',
            phone='+60 18-263 8888'
        )
        self.assertEqual(lead_valid.phone_clean, '60182638888')

        lead_short = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='عمرو',
            phone='12345'
        )
        self.assertEqual(lead_short.phone_clean, '')

    def test_traffic_source_display_with_utm_and_direct(self):
        """Test traffic source display for campaigns, referrers, and direct visits."""
        lead_utm = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='ياسر حسني',
            phone='+201011112222',
            utm_source='facebook',
            utm_campaign='%D8%AD%D9%85%D9%84%D8%A9_%D8%A7%D9%84%D8%B5%D9%8A%D9%81_2026'
        )
        self.assertIn('إعلان فيسبوك', lead_utm.traffic_source_display)
        self.assertIn('حملة: حملة الصيف 2026', lead_utm.traffic_source_display)
        self.assertFalse(lead_utm.is_direct_source)

        lead_direct = Lead.objects.create(
            lead_type=LeadType.CONTACT,
            name='منى',
            phone='+201033334444',
            referrer='https://sciencesgates.com/about-us/'
        )
        self.assertEqual(lead_direct.traffic_source_display, 'مباشر')
        self.assertTrue(lead_direct.is_direct_source)

    def test_session_attribution_persistence_in_form(self):
        """Test that LeadBaseForm automatically retrieves UTM parameters from session across pages."""
        session = self.client.session
        session['sg_utm'] = {
            'utm_source': 'google',
            'utm_campaign': 'study_malaysia_2026'
        }
        session.save()

        url = reverse('leads:submit')
        payload = {
            'lead_type': 'contact',
            'name': 'طارق سعيد',
            'email': 'tarek_utm@example.com',
            'phone': '+201055556666',
            'nationality': 'مصري',
            'message': 'استفسار عن التسجيل',
            'source_page': 'https://sciencesgates.com/universities/',
        }
        res = self.client.post(url, payload, follow=True)
        self.assertEqual(res.status_code, 200)

        saved_lead = Lead.objects.filter(email='tarek_utm@example.com').first()
        self.assertIsNotNone(saved_lead)
        self.assertEqual(saved_lead.utm_source, 'google')
        self.assertEqual(saved_lead.utm_campaign, 'study_malaysia_2026')

    def test_lead_email_notification_subject_contains_entity_name(self):
        """Test that admin email notification subject includes the university/major name."""
        from django.core import mail
        mail.outbox.clear()

        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='حسن كيالي',
            email='hassan_sub@example.com',
            phone='+97455554444',
            institution_name='جامعة تايلور Taylor\'s',
            source_page='https://sciencesgates.com/universities/taylors/'
        )

        self.assertGreaterEqual(len(mail.outbox), 1)
        admin_email = mail.outbox[0]
        self.assertIn('حسن كيالي', admin_email.subject)
        self.assertIn('جامعة تايلور', admin_email.subject)

    def test_csv_export_view_uses_decoded_urls_and_sources(self):
        """Test that CSV export outputs readable Arabic URLs and 'مباشر' sources."""
        from django.contrib.auth.models import User
        admin_user = User.objects.create_superuser('admin_csv', 'admin_csv@example.com', 'pass1234')
        self.client.force_login(admin_user)

        Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='كريم عادل',
            email='karim_csv@example.com',
            phone='+201077778888',
            source_page='https://sciencesgates.com/universities/%D8%AC%D8%A7%D9%85%D8%B9%D8%A9-%D9%85%D8%A7%D9%84%D8%A7%D9%8A%D8%A7/',
            referrer='https://sciencesgates.com/'
        )

        url = reverse('dashboard:lead_export')
        response = self.client.get(f"{url}?lead_type=registration")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn('اسم صفحة الإرسال', content)
        self.assertIn('جامعة مالايا', content)
        self.assertIn('مباشر', content)





    

