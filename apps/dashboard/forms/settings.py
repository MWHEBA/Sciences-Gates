from django import forms
from apps.core.models import SiteSettings

class SiteSettingsForm(forms.ModelForm):
    """
    Form for editing global site settings.
    نموذج تعديل إعدادات الموقع العامة
    """
    maintenance_estimated_end = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'datetime-local',
            },
            format='%Y-%m-%dT%H:%M'
        ),
        label='موعد الانتهاء المتوقع',
        help_text='تحديد موعد الانتهاء يعرض عداداً تنازلياً ويساعد محركات البحث في جدولة الزيارة القادمة'
    )

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
            'maintenance_mode',
            'maintenance_title',
            'maintenance_message',
            'maintenance_estimated_end',
            'maintenance_bypass_ips',
            'maintenance_bypass_staff',
            'email_smtp_use_dynamic',
            'email_smtp_host',
            'email_smtp_port',
            'email_smtp_user',
            'email_smtp_password',
            'email_smtp_use_tls',
            'email_smtp_use_ssl',
            'email_from_address',
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
            'maintenance_mode': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
            'maintenance_title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'صيانة مجدولة',
            }),
            'maintenance_message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الموقع قيد الصيانة حالياً. سنعود قريباً.',
                'rows': 3,
            }),
            'maintenance_bypass_ips': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '127.0.0.1\n8.8.8.8',
                'rows': 2,
            }),
            'maintenance_bypass_staff': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
            'email_smtp_use_dynamic': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
            'email_smtp_host': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'smtp.gmail.com',
                'dir': 'ltr',
            }),
            'email_smtp_port': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '587',
                'dir': 'ltr',
            }),
            'email_smtp_user': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'username@gmail.com',
                'dir': 'ltr',
            }),
            'email_smtp_password': forms.PasswordInput(render_value=True, attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '••••••••',
                'dir': 'ltr',
                'autocomplete': 'new-password',
            }),
            'email_smtp_use_tls': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
            'email_smtp_use_ssl': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
            'email_from_address': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'noreply@sciencesgates.com',
                'dir': 'ltr',
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
            'maintenance_mode': 'تفعيل وضع الصيانة',
            'maintenance_title': 'عنوان صفحة الصيانة',
            'maintenance_message': 'رسالة صفحة الصيانة',
            'maintenance_bypass_ips': 'عناوين IP المستثناة',
            'maintenance_bypass_staff': 'السماح لمدراء الموقع بالتصفح (Staff)',
            'email_smtp_use_dynamic': 'تفعيل إعدادات SMTP مخصصة',
            'email_smtp_host': 'خادم SMTP',
            'email_smtp_port': 'منفذ SMTP',
            'email_smtp_user': 'اسم مستخدم SMTP',
            'email_smtp_password': 'كلمة مرور SMTP',
            'email_smtp_use_tls': 'تفعيل TLS',
            'email_smtp_use_ssl': 'تفعيل SSL',
            'email_from_address': 'عنوان البريد الإلكتروني للمرسل (From Address)',
        }
        help_texts = {
            'site_name': 'الاسم الأساسي الذي يظهر في أعلى الموقع وعنوان الصفحات',
            'site_description': 'الوصف التعريفي الأساسي للموقع',
            'phone': 'رقم الهاتف للتواصل المباشر',
            'email': 'البريد الإلكتروني الأساسي للمراسلات',
            'whatsapp': 'أدخل الرقم الدولي بدون مفتاح + أو أصفار (مثال: 966500000000)',
            'registration_steps_title': 'العنوان الرئيسي الذي يظهر في جميع صفحات الجامعات والمعاهد',
            'registration_steps_content': 'محتوى تفصيلي لخطوات التسجيل، يمكنك استخدام تنسيق HTML هنا',
            'maintenance_mode': 'إغلاق الموقع للزوار وعرض صفحة الصيانة الكلية',
            'maintenance_title': 'العنوان الرئيسي الذي سيظهر للزوار على صفحة الصيانة',
            'maintenance_message': 'الرسالة التفصيلية التي ستظهر للزوار لشرح سبب الصيانة',
            'maintenance_bypass_ips': 'عناوين IP المسموح لها بتخطي الصيانة وتصفح الموقع بشكل طبيعي (كل عنوان في سطر)',
            'maintenance_bypass_staff': 'عند التفعيل، يمكن للمشرفين والمسؤولين المسجلين دخولهم تصفح الموقع بشكل طبيعي',
            'email_smtp_use_dynamic': 'عند التفعيل، سيقوم النظام بإرسال رسائل البريد الإلكتروني باستخدام هذه الإعدادات بدلاً من الإعدادات الافتراضية في ملف .env.',
            'email_smtp_host': 'عنوان خادم SMTP الخاص بمزود الخدمة (لمساحة عمل جوجل استخدم: smtp.gmail.com)',
            'email_smtp_port': 'المنفذ المستخدم للإرسال (لمساحة عمل جوجل استخدم 587 مع TLS أو 465 مع SSL)',
            'email_smtp_user': 'البريد الإلكتروني بالكامل المستخدم لتسجيل الدخول، مثال: noreply@sciencesgates.com',
            'email_smtp_password': 'كلمة مرور الحساب. في حالة استخدام Google Workspace، يجب إنشاء واستخدام كلمة مرور تطبيق (App Password) وليس كلمة مرور الحساب العادية.',
            'email_smtp_use_tls': 'تأمين الاتصال باستخدام TLS (مستحسن ومطلوب للمنفذ 587)',
            'email_smtp_use_ssl': 'تأمين الاتصال باستخدام SSL (مستحسن ومطلوب للمنفذ 465)',
            'email_from_address': 'البريد الذي سيظهر للمستلمين كمستلم للرسالة، يجب أن يكون معتمداً من Google Workspace للإرسال بالنيابة عنه أو يطابق اسم المستخدم أعلاه لتفادي حظر الرسائل.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.email_smtp_password:
            # We pre-fill the password field with a dummy value to indicate it is set
            self.initial['email_smtp_password'] = '••••••••'
            self.fields['email_smtp_password'].initial = '••••••••'
            self.fields['email_smtp_password'].required = False

    def clean_email_smtp_password(self):
        password = self.cleaned_data.get('email_smtp_password')
        if password == '••••••••' and self.instance and self.instance.pk:
            return self.instance.email_smtp_password
        if password and password != '••••••••':
            from apps.core.utils import SMTPCryptography
            return SMTPCryptography.encrypt(password)
        return ""

    def clean(self):
        cleaned_data = super().clean()
        use_tls = cleaned_data.get('email_smtp_use_tls')
        use_ssl = cleaned_data.get('email_smtp_use_ssl')
        use_dynamic = cleaned_data.get('email_smtp_use_dynamic')

        if use_dynamic:
            host = cleaned_data.get('email_smtp_host')
            port = cleaned_data.get('email_smtp_port')
            user = cleaned_data.get('email_smtp_user')
            password = cleaned_data.get('email_smtp_password')
            from_email = cleaned_data.get('email_from_address')

            if not host:
                self.add_error('email_smtp_host', 'خادم SMTP مطلوب عند تفعيل SMTP مخصص.')
            if not port:
                self.add_error('email_smtp_port', 'منفذ SMTP مطلوب عند تفعيل SMTP مخصص.')
            if not user:
                self.add_error('email_smtp_user', 'اسم مستخدم SMTP مطلوب عند تفعيل SMTP مخصص.')
            if not password:
                self.add_error('email_smtp_password', 'كلمة مرور SMTP مطلوبة عند تفعيل SMTP مخصص.')
            if not from_email:
                self.add_error('email_from_address', 'بريد المرسل الافتراضي مطلوب عند تفعيل SMTP مخصص.')

            # Check for TLS/SSL exclusivity
            if use_tls and use_ssl:
                raise forms.ValidationError('لا يمكن تفعيل TLS و SSL معاً في نفس الوقت. يرجى اختيار نوع تشفير واحد فقط.')

        return cleaned_data

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
