"""
Major forms for the dashboard.
نماذج التخصصات في لوحة التحكم
"""
from django import forms
from django.forms import inlineformset_factory
from apps.majors.models import Major, MajorCategory, SubjectsTable, SalaryTable, CountriesTable, MajorFAQ, MajorAttachment
from apps.core.widgets import SimpleRichTextWidget
from apps.html_editor.widgets import CustomHTMLEditorWidget


class MajorForm(forms.ModelForm):
    """
    Form for creating and editing majors with structured template editor.
    نموذج إنشاء وتعديل التخصصات مع محرر القالب المنظم
    """
    order = forms.IntegerField(
        required=False,
        initial=0,
        label='ترتيب العرض',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '0',
        })
    )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        from apps.core.navigation import auto_shift_order_if_changed
        from apps.majors.models import Major
        auto_shift_order_if_changed(self, Major, instance)
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    class Meta:
        model = Major
        fields = [
            # Basic Information
            'name', 'slug', 'category', 'order', 'main_image',
            # Quick Information Fields
            'bachelor_duration', 'master_duration', 'phd_duration',
            'study_language', 'practical_training', 'career_opportunities', 'competitor_url',
            # Rich Text Sections
            'description', 'why_study_section', 'how_to_apply_section',
            # Relationships
            'best_universities', 'cheap_universities', 'related_articles', 'tags',
            # Publishing
            'publish_status',
            # SEO Fields
            'meta_title', 'meta_description', 'focus_keyword', 'keyphrase_synonyms', 'canonical_url',
            'robots_index', 'robots_follow', 'sitemap_include',
            'og_title', 'og_description', 'og_image'
        ]
        widgets = {
            # Basic Information Section
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 paste-trigger',
                'placeholder': 'اسم التخصص',
                'required': True,
                'dir': 'rtl',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 paste-trigger',
                'placeholder': 'الرابط (يدعم الأحرف العربية)',
                'required': True,
                'dir': 'ltr',
                'data-paste-clean': 'slug',
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'required': True,
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full text-center border-0 p-0 focus:outline-none focus:ring-0 font-normal',
                'style': 'background: transparent; color: var(--text-primary); font-size: 13px;',
                'placeholder': '0',
                'min': '0',
            }),
            'main_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
                'required': True,
            }),
            
            'study_duration': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 paste-trigger',
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
            'career_opportunities': CustomHTMLEditorWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'فرص العمل المتاحة بعد التخرج',
                'rows': 6,
                'dir': 'rtl',
            }),
            
            # Rich Text Sections
            'description': CustomHTMLEditorWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'وصف شامل عن التخصص',
                'rows': 10,
                'dir': 'rtl',
            }),
            'why_study_section': CustomHTMLEditorWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'أسباب دراسة هذا التخصص',
                'rows': 8,
                'dir': 'rtl',
            }),
            'how_to_apply_section': CustomHTMLEditorWidget(attrs={
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
            'tags': forms.CheckboxSelectMultiple(attrs={
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
            'keyphrase_synonyms': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'المرادفات مفصولة بفواصل (مثال: دراسة في ماليزيا، جامعات ماليزيا)',
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
            'category': 'تصنيف التخصص',
            'main_image': 'الصورة الرئيسية',
            
            # Quick Information Fields
            'study_duration': 'مدة الدراسة (عام)',
            'bachelor_duration': 'مدة البكالوريوس',
            'master_duration': 'مدة الماجستير',
            'phd_duration': 'مدة الدكتوراه',
            'study_language': 'لغة الدراسة',
            'practical_training': 'التدريب العملي',
            'career_opportunities': 'فرص العمل',
            'competitor_url': 'رابط التخصص عند المنافس',
            
            # Rich Text Sections
            'description': 'وصف التخصص',
            'why_study_section': 'لماذا تدرس هذا التخصص',
            'how_to_apply_section': 'كيفية التقديم',
            
            # Relationships
            'best_universities': 'أفضل الجامعات',
            'cheap_universities': 'الجامعات الاقتصادية',
            'related_articles': 'المقالات المرتبطة',
            'tags': 'الوسوم',
            
            # Publishing
            'publish_status': 'حالة النشر',
            
            # SEO Fields
            'meta_title': 'عنوان SEO',
            'meta_description': 'وصف SEO',
            'focus_keyword': 'الكلمة المفتاحية',
            'keyphrase_synonyms': 'مرادفات الكلمة المفتاحية',
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
            'category': 'التصنيف الهرمي للتخصص',
            'main_image': 'صورة رئيسية للتخصص',
            
            # Quick Information Fields
            'study_duration': 'مدة الدراسة العامة (مثال: 4 سنوات)',
            'bachelor_duration': 'مدة البكالوريوس (مثال: 4 سنوات)',
            'master_duration': 'مدة الماجستير (مثال: سنتان)',
            'phd_duration': 'مدة الدكتوراه (مثال: 3-4 سنوات)',
            'study_language': 'لغة الدراسة (مثال: الإنجليزية)',
            'practical_training': 'معلومات التدريب العملي (مثال: متاح في السنة الأخيرة)',
            'career_opportunities': 'فرص العمل المتاحة بعد التخرج',
            'competitor_url': 'رابط صفحة التخصص على موقع المنافس المستخدمة في دمج المحتوى',
            
            # Rich Text Sections
            'description': 'وصف شامل عن التخصص',
            'why_study_section': 'أسباب دراسة هذا التخصص',
            'how_to_apply_section': 'خطوات التقديم للتخصص',
            
            # Relationships
            'best_universities': 'اختر أفضل الجامعات لهذا التخصص',
            'cheap_universities': 'اختر الجامعات الاقتصادية لهذا التخصص',
            'related_articles': 'اختر المقالات المرتبطة بهذا التخصص',
            'tags': 'اختر الوسوم المرتبطة بهذا التخصص',
            
            # Publishing
            'publish_status': 'المحتوى المنشور فقط يظهر للزوار',
            
            # SEO Fields
            'meta_title': 'يظهر في نتائج البحث (60 حرف كحد أقصى)',
            'meta_description': 'يظهر في نتائج البحث (160 حرف كحد أقصى)',
            'focus_keyword': 'الكلمة المفتاحية الرئيسية للصفحة',
            'keyphrase_synonyms': 'مرادفات للكلمة المفتاحية الرئيسية مفصولة بفواصل (، أو ,)',
            'canonical_url': 'اتركه فارغاً لاستخدام الرابط الافتراضي',
            'robots_index': 'السماح لمحركات البحث بفهرسة هذه الصفحة',
            'robots_follow': 'السماح لمحركات البحث بتتبع الروابط في هذه الصفحة',
            'sitemap_include': 'تضمين هذه الصفحة في ملف sitemap.xml',
            'og_title': 'العنوان عند المشاركة على وسائل التواصل',
            'og_description': 'الوصف عند المشاركة على وسائل التواصل',
            'og_image': 'الصورة عند المشاركة على وسائل التواصل (1200x630 بكسل)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data:
            if self.data.get('imported_main_image_path'):
                self.fields['main_image'].required = False

        # Populate category choices efficiently (flat list)
        choices = [('', '---------')]
        for cat in MajorCategory.objects.all().order_by('name'):
            choices.append((cat.id, cat.name))
        self.fields['category'].choices = choices

    def save(self, commit=True):
        instance = super().save(commit=False)
        from apps.importer.services.image_downloader import delete_unused_media_file
        
        imported_main_image_path = self.data.get('imported_main_image_path') if self.data else None
        if imported_main_image_path and (not self.files or 'main_image' not in self.files):
            relative_path = imported_main_image_path.replace('/media/', '', 1)
            if instance.main_image and instance.main_image.name != relative_path:
                delete_unused_media_file(instance.main_image.name)
            instance.main_image = relative_path
            
        imported_og_image_path = self.data.get('imported_og_image_path') if self.data else None
        if imported_og_image_path and (not self.files or 'og_image' not in self.files):
            relative_path = imported_og_image_path.replace('/media/', '', 1)
            if instance.og_image and instance.og_image.name != relative_path:
                delete_unused_media_file(instance.og_image.name)
            instance.og_image = relative_path
            
        if commit:
            instance.save()
            self.save_m2m()
        return instance


# ============================================================================
# Dynamic Table Formsets
# ============================================================================

# Create inline formset for SubjectsTable entries
SubjectsTableFormSet = inlineformset_factory(
    Major,
    SubjectsTable,
    fields=['track_name', 'academic_year', 'subjects', 'sort_order'],
    extra=0,
    can_delete=True,
    widgets={
        'track_name': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'المسار الفرعي (مثال: الرسوم المتحركة أو المؤثرات البصرية - اتركه فارغاً للعام)',
            'dir': 'rtl',
        }),
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
        'track_name': 'المسار الفرعي',
        'academic_year': 'السنة الدراسية',
        'subjects': 'المواد',
        'sort_order': 'ترتيب العرض',
    },
    help_texts={
        'track_name': 'المسار أو التخصص الفرعي (مثال: الرسوم المتحركة)',
        'academic_year': 'السنة الدراسية (مثال: السنة الأولى)',
        'subjects': 'المواد الدراسية (يمكن فصلها بفواصل)',
        'sort_order': 'ترتيب ظهور الصف (الأصغر أولاً)',
    }
)


# Create inline formset for SalaryTable entries
SalaryTableFormSet = inlineformset_factory(
    Major,
    SalaryTable,
    fields=['job_title', 'job_description', 'average_monthly_salary', 'sort_order'],
    extra=0,
    can_delete=True,
    widgets={
        'job_title': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: مهندس برمجيات',
            'required': True,
            'dir': 'rtl',
        }),
        'job_description': forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: تصميم التطبيقات وتجربة المستخدم',
            'rows': 3,
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
        'job_description': 'طبيعة العمل',
        'average_monthly_salary': 'متوسط الراتب الشهري',
        'sort_order': 'ترتيب العرض',
    },
    help_texts={
        'job_title': 'المسمى الوظيفي (مثال: مهندس برمجيات)',
        'job_description': 'طبيعة العمل أو الوصف المختصر للوظيفة',
        'average_monthly_salary': 'متوسط الراتب الشهري (مثال: 5,000 - 8,000 رنجت ماليزي)',
        'sort_order': 'ترتيب ظهور الصف (الأصغر أولاً)',
    }
)


# Create inline formset for CountriesTable entries
CountriesTableFormSet = inlineformset_factory(
    Major,
    CountriesTable,
    fields=['destination', 'study_duration', 'annual_fees', 'living_cost', 'sort_order'],
    extra=0,
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


class MajorCategoryForm(forms.ModelForm):
    """Form for creating and editing major categories in dashboard."""
    class Meta:
        model = MajorCategory
        fields = ['name', 'slug', 'description', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 paste-trigger',
                'placeholder': 'اسم التصنيف',
                'dir': 'rtl',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 paste-trigger',
                'placeholder': 'الرابط (يدعم الأحرف العربية)',
                'dir': 'ltr',
                'data-paste-clean': 'slug',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'وصف التصنيف',
                'rows': 4,
                'dir': 'rtl',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'ترتيب العرض (مثال: 1)',
                'min': 0,
            }),
        }
        labels = {
            'name': 'اسم التصنيف',
            'slug': 'الرابط',
            'description': 'الوصف',
            'sort_order': 'ترتيب العرض',
        }


# Create inline formsets for MajorFAQ and MajorAttachment
MajorFAQFormSet = inlineformset_factory(
    Major,
    MajorFAQ,
    fields=['question', 'answer', 'sort_order'],
    extra=0,
    can_delete=True,
    widgets={
        'question': forms.TextInput(attrs={
            'class': 'faq-item__question-input',
            'placeholder': 'السؤال الشائع',
            'required': True,
        }),
        'answer': CustomHTMLEditorWidget(attrs={
            'data-placeholder': 'الإجابة بالتفصيل...',
            'required': True,
        }),
        'sort_order': forms.HiddenInput(),
    },
    labels={
        'question': 'السؤال',
        'answer': 'الإجابة',
        'sort_order': 'ترتيب العرض',
    },
    help_texts={
        'question': 'السؤال الشائع حول التخصص',
        'answer': 'إجابة السؤال بالتفصيل',
        'sort_order': 'ترتيب ظهور السؤال (الأصغر أولاً)',
    }
)


MajorAttachmentFormSet = inlineformset_factory(
    Major,
    MajorAttachment,
    fields=['title', 'file'],
    extra=1,
    can_delete=True,
    widgets={
        'title': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'عنوان الملف (مثال: الخطة الدراسية للتخصص)',
            'dir': 'rtl',
        }),
        'file': forms.FileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        }),
    },
    labels={
        'title': 'عنوان الملف',
        'file': 'الملف المرفق',
    },
    help_texts={
        'title': 'اسم أو وصف الملف المرفق (مثال: دليل التخصص)',
        'file': 'الملف المراد إرفاقه (PDF، Word، إلخ)',
    }
)


