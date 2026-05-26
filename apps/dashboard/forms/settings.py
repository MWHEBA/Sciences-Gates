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
            'registration_steps_content'
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
