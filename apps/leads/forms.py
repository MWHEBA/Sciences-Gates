"""
Lead forms for lead submission and management.
نماذج الرسائل لتقديم الرسائل والاستفسارات
"""
from django import forms
from django.core.exceptions import ValidationError
import re
from apps.leads.models import Lead, LeadType

# exact choices matching the Fluent Forms export dropdown options
NATIONALITY_CHOICES = [
    ('', '- اختر الجنسية -'),
    ('مصر', 'مصر'),
    ('السعودية', 'السعودية'),
    ('ليبيا', 'ليبيا'),
    ('المغرب', 'المغرب'),
    ('الجزائر', 'الجزائر'),
    ('البحرين', 'البحرين'),
    ('قطر', 'قطر'),
    ('الصومال', 'الصومال'),
    ('الاردن', 'الأردن'),
    ('فلسطين', 'فلسطين'),
    ('العراق', 'العراق'),
    ('لبنان', 'لبنان'),
    ('سوريا', 'سوريا'),
    ('تونس', 'تونس'),
    ('السودان', 'السودان'),
    ('موريتانيا', 'موريتانيا'),
    ('عمان', 'عمان'),
    ('اليمن', 'اليمن'),
    ('الكويت', 'الكويت'),
    ('جيبوتى', 'جيبوتي'),
    ('جزر القمر', 'جزر القمر'),
    ('الامارات العربية المتحدة', 'الامارات العربية المتحدة'),
    ('دولة اخرى غير موجودة', 'دولة أخرى'),
]

RESIDENCE_CHOICES = [
    ('', '- اختر دولة الإقامة -'),
    ('مصر', 'مصر'),
    ('السعودية', 'السعودية'),
    ('ليبيا', 'ليبيا'),
    ('المغرب', 'المغرب'),
    ('الجزائر', 'الجزائر'),
    ('البحرين', 'البحرين'),
    ('قطر', 'قطر'),
    ('الصومال', 'الصومال'),
    ('الاردن', 'الأردن'),
    ('فلسطين', 'فلسطين'),
    ('العراق', 'العراق'),
    ('لبنان', 'لبنان'),
    ('سوريا', 'سوريا'),
    ('تونس', 'تونس'),
    ('السودان', 'السودان'),
    ('موريتانيا', 'موريتانيا'),
    ('عمان', 'عمان'),
    ('اليمن', 'اليمن'),
    ('الكويت', 'الكويت'),
    ('جيبوتى', 'جيبوتي'),
    ('جزر القمر', 'جزر القمر'),
    ('الامارات العربية المتحدة', 'الامارات العربية المتحدة'),
    ('دولة اخرى غير موجودة', 'دولة أخرى'),
]

STUDY_LEVEL_CHOICES = [
    ('', '- اختر المرحلة الدراسية -'),
    ('بكالوريوس', 'بكالوريوس'),
    ('ماجستير', 'ماجستير'),
    ('دكتوراة', 'دكتوراة'),
    ('معهد اللغة', 'معهد اللغة'),
]


class LeadBaseForm(forms.ModelForm):
    """
    Base form containing honeypot spam protection and general validation logic.
    """
    # Honeypot field - hidden from users, bots will fill it
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'display:none;',
            'tabindex': '-1',
            'autocomplete': 'off',
        }),
        label='الموقع الإلكتروني',
        help_text='اتركه فارغاً'
    )

    class Meta:
        model = Lead
        fields = []

    def clean_website(self):
        """
        Honeypot validation: reject if honeypot field is filled.
        """
        website = self.cleaned_data.get('website')
        if website:
            raise ValidationError('Invalid submission')
        return website

    def clean_email(self):
        """
        Validate email format and spam patterns.
        """
        email = self.cleaned_data.get('email')
        if email:
            spam_patterns = [
                r'test@',
                r'spam@',
                r'fake@',
            ]
            for pattern in spam_patterns:
                if re.search(pattern, email, re.IGNORECASE):
                    raise ValidationError('البريد الإلكتروني غير صحيح')
        return email

    def clean_phone(self):
        """
        Validate phone number format.
        """
        phone = self.cleaned_data.get('phone')
        if phone:
            cleaned_phone = re.sub(r'[\s\-\(\)\.]+', '', phone)
            if not re.match(r'^\+?\d{7,20}$', cleaned_phone):
                raise ValidationError('رقم الهاتف غير صحيح. يجب أن يحتوي على 7-20 رقم على الأقل')
            digits_only = re.sub(r'\D', '', phone)
            if len(digits_only) < 7:
                raise ValidationError('رقم الهاتف قصير جداً')
        return phone

    def clean_message(self):
        """
        Validate message content.
        """
        message = self.cleaned_data.get('message')
        if message and message.strip():
            url_count = len(re.findall(r'https?://', message))
            if url_count > 3:
                raise ValidationError('الرسالة تحتوي على عدد كبير جداً من الروابط')
        return message

    def clean(self):
        """
        Overall form validation.
        """
        cleaned_data = super().clean()
        if cleaned_data.get('website'):
            raise ValidationError('Invalid submission')

        # Cloudflare Turnstile Verification
        from django.conf import settings
        is_testing = getattr(settings, 'TESTING', False)
        
        from django.conf import settings
        turnstile_secret = getattr(settings, 'TURNSTILE_SECRET_KEY', None)
        
        if turnstile_secret and not is_testing:
            import requests
            turnstile_response = self.data.get('cf-turnstile-response') if self.data else None
            if not turnstile_response:
                raise ValidationError('يرجى التحقق من اختبار الأمان (Turnstile).')
            
            try:
                verify_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
                resp = requests.post(verify_url, data={
                    'secret': turnstile_secret,
                    'response': turnstile_response,
                }, timeout=10)
                
                result = resp.json()
                if not result.get('success'):
                    raise ValidationError('فشل التحقق من اختبار الأمان (Turnstile). يرجى المحاولة مرة أخرى.')
            except ValidationError:
                raise
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Turnstile verification request failed: {e}")

        # Handle merging nationality and custom_nationality
        nationality = cleaned_data.get('nationality')
        custom_nationality = cleaned_data.get('custom_nationality')
        
        if nationality == 'دولة اخرى غير موجودة':
            if custom_nationality and custom_nationality.strip():
                cleaned_data['nationality'] = custom_nationality.strip()
            else:
                self.add_error('custom_nationality', 'يرجى كتابة اسم الدولة/الجنسية الأخرى.')

        return cleaned_data


class ContactLeadForm(LeadBaseForm):
    """
    Form for Contact/Inquiry submissions.
    """
    custom_nationality = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اكتب اسم الدولة/الجنسية الأخرى',
            'dir': 'rtl',
        }),
        label='اكتب اسم الدولة'
    )

    class Meta(LeadBaseForm.Meta):
        fields = ['lead_type', 'name', 'email', 'phone', 'nationality', 'message']
        widgets = {
            'lead_type': forms.HiddenInput(),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الكامل',
                'required': True,
                'dir': 'rtl',
                'maxlength': '200',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'البريد الإلكتروني',
                'required': True,
                'dir': 'ltr',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف',
                'required': True,
                'dir': 'ltr',
                'maxlength': '20',
            }),
            'nationality': forms.Select(
                choices=NATIONALITY_CHOICES,
                attrs={
                    'class': 'form-control',
                    'required': True,
                }
            ),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'الرسالة أو الاستفسار',
                'dir': 'rtl',
                'rows': 4,
            }),
        }
        labels = {
            'lead_type': 'نوع الرسالة',
            'name': 'الاسم الكامل',
            'email': 'البريد الإلكتروني',
            'phone': 'رقم الهاتف',
            'nationality': 'الجنسية',
            'message': 'الرسالة',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lead_type'].initial = LeadType.CONTACT
        self.fields['email'].required = True
        self.fields['message'].required = False


class RegistrationLeadForm(LeadBaseForm):
    """
    Form for University/Institute Registration submissions.
    """
    custom_nationality = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'reg-input',
            'placeholder': 'اكتب اسم الدولة/الجنسية الأخرى',
            'dir': 'rtl',
        }),
        label='اكتب اسم الدولة'
    )

    class Meta(LeadBaseForm.Meta):
        fields = [
            'lead_type', 'name', 'email', 'phone', 'nationality', 
            'institution_name', 'residence_country', 'study_level', 'address', 'message'
        ]
        widgets = {
            'lead_type': forms.HiddenInput(),
            'name': forms.TextInput(attrs={
                'class': 'reg-input',
                'placeholder': 'أدخل اسم الطالب الكامل',
                'required': True,
                'dir': 'rtl',
                'maxlength': '200',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'reg-input',
                'placeholder': 'name@example.com',
                'required': True,
                'dir': 'ltr',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'reg-input',
                'placeholder': 'رقم الهاتف',
                'required': True,
                'dir': 'ltr',
                'maxlength': '20',
            }),
            'nationality': forms.Select(
                choices=NATIONALITY_CHOICES,
                attrs={
                    'class': 'reg-select',
                    'required': True,
                }
            ),
            'institution_name': forms.HiddenInput(),
            'residence_country': forms.Select(
                choices=RESIDENCE_CHOICES,
                attrs={
                    'class': 'reg-select',
                    'required': True,
                }
            ),
            'study_level': forms.Select(
                choices=STUDY_LEVEL_CHOICES,
                attrs={
                    'class': 'reg-select',
                    'required': True,
                }
            ),
            'address': forms.TextInput(attrs={
                'class': 'reg-input',
                'placeholder': 'المدينة، المنطقة، الشارع',
                'required': True,
                'dir': 'rtl',
            }),
            'message': forms.Textarea(attrs={
                'class': 'reg-textarea',
                'placeholder': 'أدخل أي تفاصيل أو متطلبات خاصة...',
                'dir': 'rtl',
                'rows': 4,
            }),
        }
        labels = {
            'lead_type': 'نوع الرسالة',
            'name': 'الاسم الكامل للطالب',
            'email': 'البريد الإلكتروني',
            'phone': 'رقم الهاتف',
            'nationality': 'الجنسية',
            'institution_name': 'اسم المؤسسة',
            'residence_country': 'دولة الإقامة',
            'study_level': 'المرحلة الدراسية',
            'address': 'عنوان الإقامة',
            'message': 'ملاحظات إضافية',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lead_type'].initial = LeadType.REGISTRATION
        self.fields['email'].required = True
        self.fields['message'].required = False


# Keep LeadForm for backward compatibility
class LeadForm(ContactLeadForm):
    """
    LeadForm legacy class subclassing ContactLeadForm.
    """
    pass

