from django import forms
from apps.core.models import SiteSettings

class SiteSettingsForm(forms.ModelForm):
    """
    Form for editing global site settings.
    نموذج تعديل إعدادات الموقع العامة
    """
    class Meta:
        model = SiteSettings
        fields = [
            'site_name',
            'site_description',
            'phone',
            'email',
            'whatsapp',
            'registration_steps_title',
            'registration_steps_content',
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'اسم الموقع',
                'required': True,
            }),
            'site_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'وصف مختصر للموقع يظهر لمحركات البحث',
                'rows': 3,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '+9665xxxxxxxx',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'info@example.com',
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '9665xxxxxxxx',
            }),
            'registration_steps_title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'خطوات التسجيل',
                'required': True,
            }),
            'registration_steps_content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'محتوى خطوات التسجيل (يدعم وسوم HTML)',
                'rows': 6,
            }),
        }
        labels = {
            'site_name': 'اسم الموقع',
            'site_description': 'وصف الموقع',
            'phone': 'رقم الهاتف',
            'email': 'البريد الإلكتروني',
            'whatsapp': 'رقم WhatsApp',
            'registration_steps_title': 'عنوان قسم خطوات التسجيل',
            'registration_steps_content': 'محتوى خطوات التسجيل',
        }
        help_texts = {
            'site_name': 'الاسم الأساسي الذي يظهر في أعلى الموقع وعنوان الصفحات',
            'site_description': 'الوصف التعريفي الأساسي للموقع',
            'phone': 'رقم الهاتف للتواصل المباشر',
            'email': 'البريد الإلكتروني الأساسي للمراسلات',
            'whatsapp': 'أدخل الرقم الدولي بدون مفتاح + أو أصفار (مثال: 966500000000)',
            'registration_steps_title': 'العنوان الرئيسي الذي يظهر في جميع صفحات الجامعات والمعاهد',
            'registration_steps_content': 'محتوى تفصيلي لخطوات التسجيل، يمكنك استخدام تنسيق HTML هنا',
        }

class SiteSEOSettingsForm(forms.ModelForm):
    """
    Form for editing site-wide SEO settings.
    نموذج تعديل إعدادات محركات البحث
    """
    class Meta:
        model = SiteSettings
        fields = [
            'ga4_measurement_id',
            'google_site_verification',
            'enable_ga4',
        ]
        widgets = {
            'ga4_measurement_id': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'G-XXXXXXXXXX',
                'dir': 'ltr',
            }),
            'google_site_verification': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'your_verification_code_here',
                'dir': 'ltr',
            }),
            'enable_ga4': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
        }
        labels = {
            'ga4_measurement_id': 'Google Analytics 4 Measurement ID',
            'google_site_verification': 'Google Site Verification Code',
            'enable_ga4': 'تفعيل Google Analytics 4',
        }
        help_texts = {
            'ga4_measurement_id': 'احصل عليه من Google Analytics 4 → Admin → Data Streams',
            'google_site_verification': 'احصل عليه من Google Search Console → Settings → Verification',
            'enable_ga4': 'قم بإيقافه مؤقتاً في حالة الصيانة أو اختبار التطوير',
        }

class SEOSettingsForm(forms.Form):
    """Form for SEO management actions."""
    action = forms.ChoiceField(
        choices=[
            ('regenerate_sitemap', 'إعادة توليد خريطة الموقع'),
            ('clear_seo_cache', 'مسح ذاكرة التخزين المؤقت لـ SEO'),
            ('test_ga4', 'اختبار اتصال Google Analytics'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        }),
        label='الإجراء'
    )
