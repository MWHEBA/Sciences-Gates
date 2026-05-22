"""
Major forms for the dashboard.
نماذج التخصصات في لوحة التحكم
"""
from django import forms
from django.forms import inlineformset_factory
from apps.majors.models import Major, SubjectsTable, SalaryTable, CountriesTable
from apps.core.widgets import SimpleRichTextWidget


class MajorForm(forms.ModelForm):
    """
    Form for creating and editing majors with structured template editor.
    نموذج إنشاء وتعديل التخصصات مع محرر القالب المنظم
    """
    
    class Meta:
        model = Major
        fields = [
            # Basic Information
            'name', 'slug', 'major_category', 'main_image',
            # Quick Information Fields
            'study_duration', 'bachelor_duration', 'master_duration', 'phd_duration',
            'tuition_fees', 'study_language', 'practical_training', 'career_opportunities',
            # Rich Text Sections
            'description', 'why_study_section', 'how_to_apply_section',
            # Relationships
            'best_universities', 'cheap_universities', 'related_articles',
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
                'placeholder': 'اسم التخصص',
                'required': True,
                'dir': 'rtl',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الرابط (يدعم الأحرف العربية)',
                'required': True,
                'dir': 'ltr',
            }),
            'major_category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'required': True,
            }),
            'main_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
                'required': True,
            }),
            
            # Quick Information Fields
            'study_duration': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثال: 4 سنوات (عام)',
                'required': True,
                'dir': 'rtl',
            }),
            'bachelor_duration': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثال: 4 سنوات',
                'dir': 'rtl',
            }),
            'master_duration': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثال: سنتان',
                'dir': 'rtl',
            }),
            'phd_duration': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثال: 3-4 سنوات',
                'dir': 'rtl',
            }),
            'tuition_fees': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثال: 15,000 - 25,000 رنجت سنوياً',
                'dir': 'rtl',
            }),
            'study_language': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثال: الإنجليزية',
                'dir': 'rtl',
            }),
            'practical_training': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثال: متاح في السنة الأخيرة',
                'dir': 'rtl',
            }),
            'career_opportunities': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'فرص العمل المتاحة بعد التخرج',
                'rows': 4,
                'dir': 'rtl',
            }),
            
            # Rich Text Sections
            'description': SimpleRichTextWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'وصف شامل عن التخصص',
                'rows': 10,
                'dir': 'rtl',
            }),
            'why_study_section': SimpleRichTextWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'أسباب دراسة هذا التخصص',
                'rows': 8,
                'dir': 'rtl',
            }),
            'how_to_apply_section': SimpleRichTextWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'خطوات التقديم للتخصص',
                'rows': 8,
                'dir': 'rtl',
            }),
            
            # Relationships
            'best_universities': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2',
            }),
            'cheap_universities': forms.CheckboxSelectMultiple(attrs={
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
            'name': 'اسم التخصص',
            'slug': 'الرابط',
            'major_category': 'فئة التخصص',
            'main_image': 'الصورة الرئيسية',
            
            # Quick Information Fields
            'study_duration': 'مدة الدراسة (عام)',
            'bachelor_duration': 'مدة البكالوريوس',
            'master_duration': 'مدة الماجستير',
            'phd_duration': 'مدة الدكتوراه',
            'tuition_fees': 'الرسوم الدراسية',
            'study_language': 'لغة الدراسة',
            'practical_training': 'التدريب العملي',
            'career_opportunities': 'فرص العمل',
            
            # Rich Text Sections
            'description': 'وصف التخصص',
            'why_study_section': 'لماذا تدرس هذا التخصص',
            'how_to_apply_section': 'كيفية التقديم',
            
            # Relationships
            'best_universities': 'أفضل الجامعات',
            'cheap_universities': 'الجامعات الاقتصادية',
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
            'major_category': 'تصنيف التخصص حسب المجال',
            'main_image': 'صورة رئيسية للتخصص',
            
            # Quick Information Fields
            'study_duration': 'مدة الدراسة العامة (مثال: 4 سنوات)',
            'bachelor_duration': 'مدة البكالوريوس (مثال: 4 سنوات)',
            'master_duration': 'مدة الماجستير (مثال: سنتان)',
            'phd_duration': 'مدة الدكتوراه (مثال: 3-4 سنوات)',
            'tuition_fees': 'الرسوم الدراسية (مثال: 15,000 - 25,000 رنجت سنوياً)',
            'study_language': 'لغة الدراسة (مثال: الإنجليزية)',
            'practical_training': 'معلومات التدريب العملي (مثال: متاح في السنة الأخيرة)',
            'career_opportunities': 'فرص العمل المتاحة بعد التخرج',
            
            # Rich Text Sections
            'description': 'وصف شامل عن التخصص (يدعم: غامق، مائل، عناوين، قوائم، روابط)',
            'why_study_section': 'أسباب دراسة هذا التخصص (يدعم: غامق، مائل، عناوين، قوائم، روابط)',
            'how_to_apply_section': 'خطوات التقديم للتخصص (يدعم: غامق، مائل، عناوين، قوائم، روابط)',
            
            # Relationships
            'best_universities': 'اختر أفضل الجامعات لهذا التخصص',
            'cheap_universities': 'اختر الجامعات الاقتصادية لهذا التخصص',
            'related_articles': 'اختر المقالات المرتبطة بهذا التخصص',
            
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


# ============================================================================
# Dynamic Table Formsets
# ============================================================================

# Create inline formset for SubjectsTable entries
SubjectsTableFormSet = inlineformset_factory(
    Major,
    SubjectsTable,
    fields=['academic_year', 'subjects', 'sort_order'],
    extra=1,
    can_delete=True,
    widgets={
        'academic_year': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: السنة الأولى',
            'required': True,
            'dir': 'rtl',
        }),
        'subjects': forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'المواد الدراسية (يمكن فصلها بفواصل)',
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
        'academic_year': 'السنة الدراسية',
        'subjects': 'المواد',
        'sort_order': 'ترتيب العرض',
    },
    help_texts={
        'academic_year': 'السنة الدراسية (مثال: السنة الأولى)',
        'subjects': 'المواد الدراسية (يمكن فصلها بفواصل)',
        'sort_order': 'ترتيب ظهور الصف (الأصغر أولاً)',
    }
)


# Create inline formset for SalaryTable entries
SalaryTableFormSet = inlineformset_factory(
    Major,
    SalaryTable,
    fields=['job_title', 'average_monthly_salary', 'sort_order'],
    extra=1,
    can_delete=True,
    widgets={
        'job_title': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: مهندس برمجيات',
            'required': True,
            'dir': 'rtl',
        }),
        'average_monthly_salary': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: 5,000 - 8,000 رنجت ماليزي',
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
        'job_title': 'المسمى الوظيفي',
        'average_monthly_salary': 'متوسط الراتب الشهري',
        'sort_order': 'ترتيب العرض',
    },
    help_texts={
        'job_title': 'المسمى الوظيفي (مثال: مهندس برمجيات)',
        'average_monthly_salary': 'متوسط الراتب الشهري (مثال: 5,000 - 8,000 رنجت ماليزي)',
        'sort_order': 'ترتيب ظهور الصف (الأصغر أولاً)',
    }
)


# Create inline formset for CountriesTable entries
CountriesTableFormSet = inlineformset_factory(
    Major,
    CountriesTable,
    fields=['destination', 'study_duration', 'annual_fees', 'living_cost', 'sort_order'],
    extra=1,
    can_delete=True,
    widgets={
        'destination': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: ماليزيا',
            'required': True,
            'dir': 'rtl',
        }),
        'study_duration': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: 4 سنوات',
            'required': True,
            'dir': 'rtl',
        }),
        'annual_fees': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: 20,000 - 30,000 رنجت ماليزي',
            'required': True,
            'dir': 'rtl',
        }),
        'living_cost': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: 1,500 - 2,500 رنجت ماليزي شهرياً',
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
        'destination': 'الوجهة',
        'study_duration': 'مدة الدراسة',
        'annual_fees': 'الرسوم السنوية',
        'living_cost': 'تكلفة المعيشة',
        'sort_order': 'ترتيب العرض',
    },
    help_texts={
        'destination': 'الوجهة (مثال: ماليزيا)',
        'study_duration': 'مدة الدراسة (مثال: 4 سنوات)',
        'annual_fees': 'الرسوم السنوية (مثال: 20,000 - 30,000 رنجت ماليزي)',
        'living_cost': 'تكلفة المعيشة (مثال: 1,500 - 2,500 رنجت ماليزي شهرياً)',
        'sort_order': 'ترتيب ظهور الصف (الأصغر أولاً)',
    }
)
