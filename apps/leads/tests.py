import pytest
from django.test import override_settings
from django.utils import timezone
from django.core import mail
from hypothesis import given, strategies as st


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
        
        self.assertEqual(LeadType.CONTACT, 'contact')
        self.assertEqual(LeadType.CONTACT, LeadType.CONTACT)
    
    def test_lead_type_choices_count(self):
        """Test that exactly two lead types exist."""
        from .models import LeadType
        
        self.assertEqual(len(LeadType.choices), 2)
    
    def test_lead_type_display_names(self):
        """Test that lead types have Arabic display names."""
        from .models import LeadType
        
        choices_dict = dict(LeadType.choices)
        self.assertEqual(choices_dict['registration'], 'طلب تسجيل')
        self.assertEqual(choices_dict['contact'], 'استفسار')


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
    
    def test_lead_creation_with_utm_parameters(self):
        """Test that lead can be created with UTM parameters."""
        from .models import Lead, LeadType
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='محمود حسن',
            email='mahmoud@example.com',
            phone='+201234567892',
            message='تسجيل جديد',
            utm_source='facebook',
            utm_medium='social',
            utm_campaign='summer_2024',
            utm_term='universities',
            utm_content='banner_ad'
        )
        
        self.assertEqual(lead.utm_source, 'facebook')
        self.assertEqual(lead.utm_medium, 'social')
        self.assertEqual(lead.utm_campaign, 'summer_2024')
        self.assertEqual(lead.utm_term, 'universities')
        self.assertEqual(lead.utm_content, 'banner_ad')
    
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
        self.assertEqual(field.max_length, 20)
    
    def test_source_page_field_blank(self):
        """Test source_page field is blank=True."""
        field = Lead._meta.get_field('source_page')
        self.assertTrue(field.blank)
    
    def test_referrer_field_blank(self):
        """Test referrer field is blank=True."""
        field = Lead._meta.get_field('referrer')
        self.assertTrue(field.blank)
    
    def test_utm_fields_blank(self):
        """Test all UTM fields are blank=True."""
        utm_fields = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
        for field_name in utm_fields:
            field = Lead._meta.get_field(field_name)
            self.assertTrue(field.blank, f'{field_name} should be blank=True')
    
    def test_utm_fields_max_length(self):
        """Test all UTM fields have max_length=100."""
        utm_fields = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
        for field_name in utm_fields:
            field = Lead._meta.get_field(field_name)
            self.assertEqual(field.max_length, 100, f'{field_name} should have max_length=100')
    
    def test_notes_field_blank(self):
        """Test notes field is blank=True."""
        field = Lead._meta.get_field('notes')
        self.assertTrue(field.blank)


class LeadPropertyBasedTests(HypothesisTestCase):
    """Property-based tests for Lead model.
    
    **Validates: Requirements 5, 23**
    """
    
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
    
    @given(
        utm_source=st.text(max_size=100),
        utm_medium=st.text(max_size=100),
        utm_campaign=st.text(max_size=100),
        utm_term=st.text(max_size=100),
        utm_content=st.text(max_size=100)
    )
    def test_lead_utm_parameters_storage(self, utm_source, utm_medium, utm_campaign, utm_term, utm_content):
        """Property: Lead can store any combination of UTM parameters.
        
        **Validates: Requirement 5.6** - WHEN a user submits a Lead_Form, THE Platform SHALL record UTM parameters if present in the URL
        """
        from .models import Lead, LeadType
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='اختبار',
            email='test@example.com',
            phone='+201234567890',
            message='رسالة',
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_term=utm_term,
            utm_content=utm_content
        )
        
        self.assertEqual(lead.utm_source, utm_source)
        self.assertEqual(lead.utm_medium, utm_medium)
        self.assertEqual(lead.utm_campaign, utm_campaign)
        self.assertEqual(lead.utm_term, utm_term)
        self.assertEqual(lead.utm_content, utm_content)
    
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
        """Test that email is sent when a new lead is created."""
        from .models import Lead, LeadType
        
        # Clear the test mailbox
        mail.outbox = []
        
        # Create a new lead
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='أحمد محمد',
            email='ahmed@example.com',
            phone='+201234567890',
            message='أريد التسجيل في الجامعة'
        )
        
        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email details
        email = mail.outbox[0]
        self.assertIn('أحمد محمد', email.subject)
        self.assertIn('طلب تسجيل', email.subject)
    
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
            referrer='https://google.com',
            utm_source='google',
            utm_medium='organic',
            utm_campaign='summer_2024'
        )
        
        # Check email content
        email = mail.outbox[0]
        self.assertIn('فاطمة علي', email.body)
        self.assertIn('fatima@example.com', email.body)
        self.assertIn('+201234567891', email.body)
        self.assertIn('استفسار عن البرامج', email.body)
        self.assertIn('https://example.com/universities', email.body)
        self.assertIn('https://google.com', email.body)
        self.assertIn('google', email.body)
        self.assertIn('organic', email.body)
        self.assertIn('summer_2024', email.body)
    
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
        self.assertIn('الاسم:', email.body)
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
        
        # Check that two emails were sent
        self.assertEqual(len(mail.outbox), 2)
    
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
        """Test that email is not sent when ADMIN_EMAIL is empty."""
        from .models import Lead, LeadType
        
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='اختبار',
            email='test@example.com',
            phone='+201234567890',
            message='رسالة'
        )
        
        # No email should be sent
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
        
        # Email should still be sent
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        # Should contain "غير محدد" (not specified) for missing fields
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
        
        # Email should be sent successfully
        self.assertEqual(len(mail.outbox), 1)
        
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
        
        # Email should be sent successfully
        self.assertEqual(len(mail.outbox), 1)
        
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
    
    @given(
        lead_type=st.sampled_from([LeadType.REGISTRATION, LeadType.CONTACT]),
        name=st.text(min_size=1, max_size=200),
        email=st.emails(),
        phone=st.text(min_size=1, max_size=20),
        message=st.text(min_size=1)
    )
    def test_email_sent_for_any_valid_lead(self, lead_type, name, email, phone, message):
        """Property: Email is sent for any valid lead creation.
        
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
        
        # Email should be sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Email should contain sanitized lead name (newlines removed)
        email_obj = mail.outbox[0]
        sanitized_name = name.replace('\n', ' ').replace('\r', ' ')
        self.assertIn(sanitized_name, email_obj.subject)
    
    @given(
        utm_source=st.text(max_size=100),
        utm_medium=st.text(max_size=100),
        utm_campaign=st.text(max_size=100)
    )
    def test_email_includes_utm_parameters(self, utm_source, utm_medium, utm_campaign):
        """Property: Email includes UTM parameters when present.
        
        **Validates: Requirement 5.6** - WHEN a user submits a Lead_Form, THE Platform SHALL record UTM parameters if present in the URL
        """
        mail.outbox = []
        
        lead = Lead.objects.create(
            lead_type=LeadType.REGISTRATION,
            name='اختبار',
            email='test@example.com',
            phone='+201234567890',
            message='رسالة',
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign
        )
        
        email_obj = mail.outbox[0]
        # Email should contain UTM parameters
        if utm_source:
            self.assertIn(utm_source, email_obj.body)
        if utm_medium:
            self.assertIn(utm_medium, email_obj.body)
        if utm_campaign:
            self.assertIn(utm_campaign, email_obj.body)
