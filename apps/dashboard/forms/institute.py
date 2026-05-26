"""
Institute forms for the dashboard.
نماذج المعاهد في لوحة التحكم
"""
from django import forms
from django.forms import inlineformset_factory
from apps.institutes.models import Institute, Course
from apps.core.widgets import SimpleRichTextWidget


class InstituteForm(forms.ModelForm):
    """
    Form for creating and editing institutes with structured template editor.
    نموذج إنشاء وتعديل المعاهد مع محرر القالب المنظم
    """
    
    class Meta:
        model = Institute
        fields = [
            # Basic Information
            'name', 'slug', 'institute_type', 'main_image',
            # Rich Text Sections
            'description', 'registration_requirements', 'registration_section',
            # Relationships
            'related_articles',
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
                'placeholder': 'اسم المعهد',
                'required': True,
                'dir': 'rtl',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الرابط (يدعم الأحرف العربية)',
                'required': True,
                'dir': 'ltr',
            }),
            'institute_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'required': True,
            }),
            'main_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
                'required': True,
            }),
            
            # Rich Text Sections
            'description': SimpleRichTextWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'وصف شامل عن المعهد',
                'rows': 10,
                'dir': 'rtl',
            }),
            'registration_requirements': SimpleRichTextWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'شروط التسجيل في المعهد',
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
                'placeholder': '60 حرف كحد أقصى',
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
                'placeholder': 'اتركه فارغاً للاستخدام الافتراضي',
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
            'name': 'اسم المعهد',
            'slug': 'الرابط',
            'institute_type': 'نوع المعهد',
            'main_image': 'الصورة الرئيسية',
            
            # Rich Text Sections
            'description': 'وصف المعهد',
            'registration_requirements': 'شروط التسجيل',
            'registration_section': 'قسم التسجيل',
            
            # Relationships
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
            'institute_type': 'تصنيف المعهد (لغة أو أكاديمي)',
            'main_image': 'صورة رئيسية للمعهد',
            
            # Rich Text Sections
            'description': 'وصف شامل عن المعهد',
            'registration_requirements': 'شروط التسجيل في المعهد',
            'registration_section': 'معلومات عملية التسجيل والخطوات',
            
            # Relationships
            'related_articles': 'اختر المقالات المرتبطة بهذا المعهد',
            
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


# Create inline formset for Course entries
CourseFormSet = inlineformset_factory(
    Institute,
    Course,
    fields=['name', 'duration', 'fees', 'description', 'notes'],
    extra=1,
    can_delete=True,
    widgets={
        'name': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'اسم الدورة',
            'required': True,
            'dir': 'rtl',
        }),
        'duration': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: 6 أشهر',
            'required': True,
            'dir': 'rtl',
        }),
        'fees': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: 5,000 رنجت ماليزي',
            'required': True,
            'dir': 'rtl',
        }),
        'description': forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'وصف الدورة',
            'rows': 4,
            'required': True,
            'dir': 'rtl',
        }),
        'notes': forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'ملاحظات إضافية عن الدورة',
            'rows': 3,
            'dir': 'rtl',
        }),
    },
    labels={
        'name': 'اسم الدورة',
        'duration': 'مدة الدورة',
        'fees': 'الرسوم',
        'description': 'الوصف',
        'notes': 'ملاحظات',
    },
    help_texts={
        'name': 'اسم الدورة',
        'duration': 'مدة الدورة (مثال: 6 أشهر)',
        'fees': 'الرسوم (مثال: 5,000 رنجت ماليزي)',
        'description': 'وصف الدورة',
        'notes': 'ملاحظات إضافية عن الدورة',
    }
)
