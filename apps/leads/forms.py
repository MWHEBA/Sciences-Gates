"""
Lead forms for lead submission and management.
نماذج الرسائل لتقديم الرسائل والاستفسارات
"""
from django import forms
from django.core.exceptions import ValidationError
import re
from apps.leads.models import Lead, LeadType


class LeadForm(forms.ModelForm):
    """
    Form for lead submission with spam protection.
    نموذج تقديم الرسائل مع حماية من الرسائل العشوائية
    
    Features:
    - User-facing fields: name, email, phone, message, lead_type
    - Honeypot field for spam protection (hidden from users)
    - Email validation using Django's built-in validators
    - Phone validation for common formats
    - Arabic labels and help text
    - CSRF protection (handled by Django middleware)
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
        fields = ['lead_type', 'name', 'email', 'phone', 'message']
        widgets = {
            # Lead Type - hidden in sidebar form, visible in standalone form
            'lead_type': forms.HiddenInput(),
            
            # Name
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الكامل',
                'required': True,
                'dir': 'rtl',
                'maxlength': '200',
            }),
            
            # Email
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'البريد الإلكتروني',
                'dir': 'ltr',
            }),
            
            # Phone
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف',
                'required': True,
                'dir': 'ltr',
                'maxlength': '20',
            }),
            
            # Message
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
            'message': 'الرسالة',
        }
        help_texts = {
            'name': 'أدخل اسمك الكامل',
            'email': 'أدخل بريدك الإلكتروني الصحيح',
            'phone': 'أدخل رقم هاتفك',
            'message': 'اكتب رسالتك أو استفسارك',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # lead_type defaults to 'contact' if not provided
        self.fields['lead_type'].initial = 'contact'
        # email and message are optional
        self.fields['email'].required = False
        self.fields['message'].required = False
    
    def clean_website(self):
        """
        Honeypot validation: reject if honeypot field is filled.
        This field should remain empty as it's hidden from real users.
        """
        website = self.cleaned_data.get('website')
        if website:
            # Silently fail - don't reveal honeypot to bots
            raise ValidationError('Invalid submission')
        return website
    
    def clean_email(self):
        """
        Validate email format.
        Django's EmailField already validates format, but we can add custom validation if needed.
        """
        email = self.cleaned_data.get('email')
        if email:
            # Additional validation: check for common spam patterns
            # Reject emails with suspicious patterns
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
        Accepts common formats: +1234567890, 1234567890, +1-234-567-8900, etc.
        """
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove common separators and spaces
            cleaned_phone = re.sub(r'[\s\-\(\)\.]+', '', phone)
            
            # Check if it contains only digits and optional leading +
            if not re.match(r'^\+?\d{7,20}$', cleaned_phone):
                raise ValidationError('رقم الهاتف غير صحيح. يجب أن يحتوي على 7-20 رقم على الأقل')
            
            # Check for minimum length (at least 7 digits)
            digits_only = re.sub(r'\D', '', phone)
            if len(digits_only) < 7:
                raise ValidationError('رقم الهاتف قصير جداً')
        
        return phone
    
    def clean_message(self):
        """
        Validate message content.
        Message is optional, but if provided check for spam patterns.
        """
        message = self.cleaned_data.get('message')
        if message and message.strip():
            # Check for excessive URLs (spam indicator)
            url_count = len(re.findall(r'https?://', message))
            if url_count > 3:
                raise ValidationError('الرسالة تحتوي على عدد كبير جداً من الروابط')
        
        return message
    
    def clean(self):
        """
        Overall form validation.
        """
        cleaned_data = super().clean()
        
        # Ensure honeypot is empty
        if cleaned_data.get('website'):
            raise ValidationError('Invalid submission')
        
        return cleaned_data
