"""
University forms for the dashboard.
نماذج الجامعات في لوحة التحكم
"""
from django import forms
from django.forms import inlineformset_factory
from apps.universities.models import University, UniversityFAQ, Faculty, Program
from apps.core.widgets import SimpleRichTextWidget


class UniversityForm(forms.ModelForm):
    """
    Form for creating and editing universities with structured template editor.
    نموذج إنشاء وتعديل الجامعات مع محرر القالب المنظم
    """
    
    class Meta:
        model = University
        fields = [
            # Basic Information
            'name', 'slug', 'university_type', 'logo', 'main_image', 'location', 'video_url',
            # Rich Text Sections
            'description', 'admission_requirements', 'registration_section',
            # Relationships
            'related_majors', 'related_articles',
            # Publishing
            'publish_status',
            # SEO Fields
            'meta_title', 'meta_description', 'focus_keyword', 'canonical_url',
            'robots_index', 'robots_follow', 'sitemap_include',
            'og_title', 'og_description', 'og_image'
        ]
        widgets = {
            # Basic Information Section
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'اسم الجامعة',
                'required': True,
                'dir': 'rtl',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الرابط (يدعم الأحرف العربية)',
                'required': True,
                'dir': 'ltr',
            }),
            'university_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'required': True,
            }),
            'logo': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
                'required': True,
            }),
            'main_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
                'required': True,
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'موقع الجامعة (المدينة، الولاية)',
                'required': True,
                'dir': 'rtl',
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'رابط فيديو YouTube أو Vimeo',
                'dir': 'ltr',
            }),
            
            # Rich Text Sections
            'description': SimpleRichTextWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'وصف شامل عن الجامعة',
                'rows': 10,
                'dir': 'rtl',
            }),
            'admission_requirements': SimpleRichTextWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'شروط القبول في الجامعة',
                'rows': 8,
                'dir': 'rtl',
            }),
            'registration_section': SimpleRichTextWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'معلومات عملية التسجيل والخطوات',
                'rows': 8,
                'dir': 'rtl',
            }),
            
            # Relationships
            'related_majors': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2',
            }),
            'related_articles': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2',
            }),
            
            # Publishing
            'publish_status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            
            # SEO Fields
            'meta_title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'عنوان SEO (60 حرف كحد أقصى)',
                'maxlength': '60',
                'dir': 'rtl',
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'وصف SEO (160 حرف كحد أقصى)',
                'rows': 3,
                'maxlength': '160',
                'dir': 'rtl',
            }),
            'focus_keyword': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الكلمة المفتاحية الرئيسية',
                'dir': 'rtl',
            }),
            'canonical_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الرابط الأساسي (اتركه فارغاً للاستخدام الافتراضي)',
                'dir': 'ltr',
            }),
            'robots_index': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500',
            }),
            'robots_follow': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500',
            }),
            'sitemap_include': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500',
            }),
            'og_title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'عنوان Open Graph (60 حرف كحد أقصى)',
                'maxlength': '60',
                'dir': 'rtl',
            }),
            'og_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'وصف Open Graph (160 حرف كحد أقصى)',
                'rows': 3,
                'maxlength': '160',
                'dir': 'rtl',
            }),
            'og_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
            }),
        }
        labels = {
            # Basic Information
            'name': 'اسم الجامعة',
            'slug': 'الرابط',
            'university_type': 'نوع الجامعة',
            'logo': 'شعار الجامعة',
            'main_image': 'الصورة الرئيسية',
            'location': 'الموقع',
            'video_url': 'رابط الفيديو',
            
            # Rich Text Sections
            'description': 'وصف الجامعة',
            'admission_requirements': 'شروط القبول',
            'registration_section': 'قسم التسجيل',
            
            # Relationships
            'related_majors': 'التخصصات المرتبطة',
            'related_articles': 'المقالات المرتبطة',
            
            # Publishing
            'publish_status': 'حالة النشر',
            
            # SEO Fields
            'meta_title': 'عنوان SEO',
            'meta_description': 'وصف SEO',
            'focus_keyword': 'الكلمة المفتاحية',
            'canonical_url': 'الرابط الأساسي',
            'robots_index': 'السماح بالفهرسة',
            'robots_follow': 'السماح بتتبع الروابط',
            'sitemap_include': 'تضمين في خريطة الموقع',
            'og_title': 'عنوان Open Graph',
            'og_description': 'وصف Open Graph',
            'og_image': 'صورة Open Graph',
        }
        help_texts = {
            # Basic Information
            'slug': 'رابط الصفحة (يدعم الأحرف العربية)',
            'university_type': 'تصنيف الجامعة (حكومية أو خاصة)',
            'logo': 'شعار الجامعة (PNG مع خلفية شفافة مفضل)',
            'main_image': 'صورة رئيسية للجامعة',
            'location': 'موقع الجامعة (المدينة، الولاية)',
            'video_url': 'رابط فيديو YouTube أو Vimeo',
            
            # Rich Text Sections
            'description': 'وصف شامل عن الجامعة (يدعم: غامق، مائل، عناوين، قوائم، روابط)',
            'admission_requirements': 'شروط القبول في الجامعة (يدعم: غامق، مائل، عناوين، قوائم، روابط)',
            'registration_section': 'معلومات عملية التسجيل والخطوات (يدعم: غامق، مائل، عناوين، قوائم، روابط)',
            
            # Relationships
            'related_majors': 'اختر التخصصات المرتبطة بهذه الجامعة',
            'related_articles': 'اختر المقالات المرتبطة بهذه الجامعة',
            
            # Publishing
            'publish_status': 'المحتوى المنشور فقط يظهر للزوار',
            
            # SEO Fields
            'meta_title': 'يظهر في نتائج البحث (60 حرف كحد أقصى)',
            'meta_description': 'يظهر في نتائج البحث (160 حرف كحد أقصى)',
            'focus_keyword': 'الكلمة المفتاحية الرئيسية للصفحة',
            'canonical_url': 'اتركه فارغاً لاستخدام الرابط الافتراضي',
            'robots_index': 'السماح لمحركات البحث بفهرسة هذه الصفحة',
            'robots_follow': 'السماح لمحركات البحث بتتبع الروابط في هذه الصفحة',
            'sitemap_include': 'تضمين هذه الصفحة في ملف sitemap.xml',
            'og_title': 'العنوان عند المشاركة على وسائل التواصل',
            'og_description': 'الوصف عند المشاركة على وسائل التواصل',
            'og_image': 'الصورة عند المشاركة على وسائل التواصل (1200x630 بكسل)',
        }


# Create inline formset for FAQ entries
UniversityFAQFormSet = inlineformset_factory(
    University,
    UniversityFAQ,
    fields=['question', 'answer', 'sort_order'],
    extra=1,
    can_delete=True,
    widgets={
        'question': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'السؤال',
            'required': True,
            'dir': 'rtl',
        }),
        'answer': forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'الإجابة',
            'rows': 4,
            'required': True,
            'dir': 'rtl',
        }),
        'sort_order': forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'ترتيب العرض',
            'min': '0',
            'dir': 'ltr',
        }),
    },
    labels={
        'question': 'السؤال',
        'answer': 'الإجابة',
        'sort_order': 'ترتيب العرض',
    },
    help_texts={
        'question': 'السؤال الشائع',
        'answer': 'إجابة السؤال',
        'sort_order': 'ترتيب ظهور السؤال (الأصغر أولاً)',
    }
)


# ============================================================================
# Faculty and Program Forms
# ============================================================================

class FacultyForm(forms.ModelForm):
    """
    Form for creating and editing faculties.
    نموذج إنشاء وتعديل الكليات
    """
    
    class Meta:
        model = Faculty
        fields = ['name', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'اسم الكلية',
                'required': True,
                'dir': 'rtl',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'ترتيب العرض',
                'min': '0',
                'dir': 'ltr',
            }),
        }
        labels = {
            'name': 'اسم الكلية',
            'sort_order': 'ترتيب العرض',
        }
        help_texts = {
            'name': 'اسم الكلية (مثال: كلية الهندسة)',
            'sort_order': 'ترتيب ظهور الكلية (الأصغر أولاً)',
        }


class ProgramForm(forms.ModelForm):
    """
    Form for creating and editing programs.
    نموذج إنشاء وتعديل البرامج
    """
    
    class Meta:
        model = Program
        fields = ['name', 'duration', 'tuition_fees', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'اسم البرنامج',
                'required': True,
                'dir': 'rtl',
            }),
            'duration': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثال: 4 سنوات',
                'required': True,
                'dir': 'rtl',
            }),
            'tuition_fees': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثال: 20,000 رنجت ماليزي سنوياً',
                'required': True,
                'dir': 'rtl',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'ترتيب العرض',
                'min': '0',
                'dir': 'ltr',
            }),
        }
        labels = {
            'name': 'اسم البرنامج',
            'duration': 'مدة الدراسة',
            'tuition_fees': 'الرسوم الدراسية',
            'sort_order': 'ترتيب العرض',
        }
        help_texts = {
            'name': 'اسم البرنامج (مثال: هندسة البرمجيات)',
            'duration': 'مدة الدراسة (مثال: 4 سنوات)',
            'tuition_fees': 'الرسوم الدراسية (مثال: 20,000 رنجت ماليزي سنوياً)',
            'sort_order': 'ترتيب ظهور البرنامج (الأصغر أولاً)',
        }


# Create inline formset for Program entries
ProgramFormSet = inlineformset_factory(
    Faculty,
    Program,
    form=ProgramForm,
    fields=['name', 'duration', 'tuition_fees', 'sort_order'],
    extra=1,
    can_delete=True,
)
