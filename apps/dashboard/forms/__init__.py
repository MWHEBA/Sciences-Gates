"""
Dashboard forms package.
نماذج لوحة التحكم
"""
from django import forms
from django.contrib.auth.models import User
from apps.core.models import UserProfile, UserRole
from django.contrib.auth.forms import PasswordResetForm
from .university import UniversityForm, UniversityFAQFormSet, UniversityFacultyFormSet, FacultyForm, ProgramFormSet, UniversityAttachmentFormSet
from .institute import InstituteForm, CourseFormSet, InstituteAttachmentFormSet, InstituteFAQFormSet
from .major import MajorForm, MajorCategoryForm, SubjectsTableFormSet, SalaryTableFormSet, CountriesTableFormSet, MajorFAQFormSet, MajorAttachmentFormSet
from .article import ArticleForm, ArticleFAQFormSet, CategoryForm, TagForm, ArticleAttachmentFormSet
from .settings import SiteSettingsForm, SiteSEOSettingsForm, SEOSettingsForm


class DashboardLoginForm(forms.Form):
    """
    Form for dashboard login.
    نموذج تسجيل الدخول إلى لوحة التحكم
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'اسم المستخدم',
            'autocomplete': 'username',
            'required': True,
        }),
        label='اسم المستخدم'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'كلمة المرور',
            'autocomplete': 'current-password',
            'required': True,
        }),
        label='كلمة المرور'
    )


class UserCreateForm(forms.ModelForm):
    """
    Form for creating a new user with profile and role.
    نموذج إنشاء مستخدم جديد مع الملف الشخصي والدور
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'كلمة المرور',
            'autocomplete': 'new-password',
        }),
        label='كلمة المرور',
        help_text='يجب أن تكون قوية وتحتوي على أحرف وأرقام'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'تأكيد كلمة المرور',
            'autocomplete': 'new-password',
        }),
        label='تأكيد كلمة المرور'
    )
    role = forms.ChoiceField(
        choices=UserRole.choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        }),
        label='الدور',
        help_text='اختر دور المستخدم في لوحة التحكم'
    )
    receive_registration_emails = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500',
        }),
        label='استقبال إيميلات التسجيل',
        help_text='تفعيل استقبال إشعارات طلبات التسجيل الجديدة عبر البريد الإلكتروني'
    )
    receive_inquiry_emails = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500',
        }),
        label='استقبال إيميلات الاستفسارات',
        help_text='تفعيل استقبال إشعارات الاستفسارات الجديدة عبر البريد الإلكتروني'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'اسم المستخدم',
                'required': True,
                'autocomplete': 'username',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'البريد الإلكتروني',
                'required': True,
                'autocomplete': 'email',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الاسم الأول',
                'autocomplete': 'given-name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الاسم الأخير',
                'autocomplete': 'family-name',
            }),
        }
        labels = {
            'username': 'اسم المستخدم',
            'email': 'البريد الإلكتروني',
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
        }

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('كلمات المرور غير متطابقة')

        # Check username uniqueness
        username = cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError('اسم المستخدم موجود بالفعل')

        # Check email uniqueness
        email = cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('البريد الإلكتروني موجود بالفعل')

        return cleaned_data

    def save(self, commit=True):
        """Save user and create profile with role and email preferences."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_staff = True  # Allow dashboard access
        if commit:
            user.save()
            # Create or update profile with role and preferences
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.receive_registration_emails = self.cleaned_data.get('receive_registration_emails', True)
            profile.receive_inquiry_emails = self.cleaned_data.get('receive_inquiry_emails', True)
            profile.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """
    Form for updating an existing user and their role.
    نموذج تحديث مستخدم موجود ودوره
    """
    role = forms.ChoiceField(
        choices=UserRole.choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        }),
        label='الدور',
        help_text='اختر دور المستخدم في لوحة التحكم'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'كلمة المرور الجديدة (اختياري)',
            'autocomplete': 'new-password',
        }),
        label='كلمة المرور الجديدة',
        required=False,
        help_text='اتركها فارغة إذا لم تكن تريد تغيير كلمة المرور'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'تأكيد كلمة المرور الجديدة',
            'autocomplete': 'new-password',
        }),
        label='تأكيد كلمة المرور الجديدة',
        required=False
    )

    receive_registration_emails = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500',
        }),
        label='استقبال إيميلات التسجيل',
        help_text='تفعيل استقبال إشعارات طلبات التسجيل الجديدة عبر البريد الإلكتروني'
    )
    receive_inquiry_emails = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500',
        }),
        label='استقبال إيميلات الاستفسارات',
        help_text='تفعيل استقبال إشعارات الاستفسارات الجديدة عبر البريد الإلكتروني'
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'البريد الإلكتروني',
                'autocomplete': 'email',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الاسم الأول',
                'autocomplete': 'given-name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الاسم الأخير',
                'autocomplete': 'family-name',
            }),
        }
        labels = {
            'email': 'البريد الإلكتروني',
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with current role and email preferences."""
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['role'].initial = self.instance.profile.role
            self.fields['receive_registration_emails'].initial = self.instance.profile.receive_registration_emails
            self.fields['receive_inquiry_emails'].initial = self.instance.profile.receive_inquiry_emails

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password or password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('كلمات المرور غير متطابقة')

        # Check email uniqueness (excluding current user)
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('البريد الإلكتروني موجود بالفعل')

        return cleaned_data

    def save(self, commit=True):
        """Save user and update profile role and email preferences."""
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
            profile = user.profile
            profile.role = self.cleaned_data['role']
            profile.receive_registration_emails = self.cleaned_data.get('receive_registration_emails', True)
            profile.receive_inquiry_emails = self.cleaned_data.get('receive_inquiry_emails', True)
            profile.save()
        return user


class RedirectForm(forms.ModelForm):
    """
    Form for creating and updating redirects.
    نموذج إنشاء وتحديث إعادات التوجيه
    """
    class Meta:
        from apps.redirects.models import Redirect
        model = Redirect
        fields = ['old_url', 'new_url', 'is_active', 'notes']
        widgets = {
            'old_url': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '/old-url/',
                'required': True,
            }),
            'new_url': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '/new-url/',
                'required': True,
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'ملاحظات إضافية عن سبب التوجيه',
                'rows': 3,
            }),
        }
        labels = {
            'old_url': 'الرابط القديم',
            'new_url': 'الرابط الجديد',
            'is_active': 'نشط',
            'notes': 'ملاحظات',
        }
        help_texts = {
            'old_url': 'الرابط القديم الذي سيتم إعادة توجيهه (مثال: /old-url/)',
            'new_url': 'الرابط الجديد الذي سيتم التوجيه إليه (مثال: /new-url/)',
            'is_active': 'تفعيل أو تعطيل هذا التوجيه',
            'notes': 'ملاحظات إضافية عن سبب التوجيه',
        }

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        old_url = cleaned_data.get('old_url', '').strip()
        new_url = cleaned_data.get('new_url', '').strip()

        # Validate URLs are not empty
        if not old_url:
            raise forms.ValidationError('الرابط القديم مطلوب')
        if not new_url:
            raise forms.ValidationError('الرابط الجديد مطلوب')

        # Validate URLs are different
        if old_url == new_url:
            raise forms.ValidationError('الرابط القديم والجديد يجب أن يكونا مختلفين')

        # Validate URLs start with /
        if not old_url.startswith('/'):
            raise forms.ValidationError('الرابط القديم يجب أن يبدأ بـ /')
        if not new_url.startswith('/'):
            raise forms.ValidationError('الرابط الجديد يجب أن يبدأ بـ /')

        return cleaned_data

    def save(self, commit=True):
        """Save redirect with normalized URLs."""
        redirect_obj = super().save(commit=False)
        # Normalize URLs
        redirect_obj.old_url = redirect_obj.old_url.strip()
        redirect_obj.new_url = redirect_obj.new_url.strip()
        if commit:
            redirect_obj.save()
        return redirect_obj


class DashboardPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form that restricts password resets to staff/superuser accounts only.
    """
    email = forms.EmailField(
        label="البريد الإلكتروني",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'login-input',
            'placeholder': 'أدخل بريدك الإلكتروني المسجل',
            'autocomplete': 'email',
            'required': True,
        })
    )

    def get_users(self, email):
        active_users = super().get_users(email)
        return [u for u in active_users if u.is_staff or u.is_superuser]


__all__ = [
    'DashboardLoginForm',
    'DashboardPasswordResetForm',
    'UserCreateForm',
    'UserUpdateForm',
    'RedirectForm',
    'UniversityForm',
    'UniversityFAQFormSet',
    'UniversityFacultyFormSet',
    'UniversityAttachmentFormSet',
    'FacultyForm',
    'ProgramFormSet',
    'InstituteForm',
    'CourseFormSet',
    'InstituteAttachmentFormSet',
    'MajorForm',
    'MajorCategoryForm',
    'SubjectsTableFormSet',
    'SalaryTableFormSet',
    'CountriesTableFormSet',
    'ArticleForm',
    'ArticleFAQFormSet',
    'ArticleAttachmentFormSet',
    'CategoryForm',
    'TagForm',
    'SiteSettingsForm',
    'SiteSEOSettingsForm',
    'SEOSettingsForm',
]
