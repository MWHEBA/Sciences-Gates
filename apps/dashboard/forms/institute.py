"""
Institute forms for the dashboard.
نماذج المعاهد في لوحة التحكم
"""
from django import forms
from django.forms import inlineformset_factory
from apps.institutes.models import Institute, Course, InstituteAttachment, InstituteFAQ
from apps.html_editor.widgets import CustomHTMLEditorWidget


class InstituteForm(forms.ModelForm):
    """
    Form for creating and editing institutes with structured template editor.
    نموذج إنشاء وتعديل المعاهد مع محرر القالب المنظم
    """
    city = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        }),
        required=False,
        label='المدينة',
        help_text='المدينة التي يقع بها المعهد لتسهيل التصفية والبحث'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.universities.models import University
        all_cities = [('', 'اختر المدينة')]
        for state_code, cities in University.STATE_CITIES.items():
            all_cities.extend(cities)
        self.fields['city'].choices = all_cities

        if self.data:
            if self.data.get('imported_main_image_path'):
                self.fields['main_image'].required = False

    class Meta:
        model = Institute
        fields = [
            # Basic Information
            'name', 'slug', 'is_legacy', 'state', 'city', 'logo', 'logo_alt', 'main_image', 'main_image_alt', 'location',
            'telephone', 'website',
            # Rich Text Sections
            'introduction', 'description', 'why_choose_us', 'english_study',
            # Fees Info
            'fees_includes', 'fees_excludes',
            # Relationships
            'related_articles', 'tags',
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
                'placeholder': 'اسم المعهد',
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
            'is_legacy': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500',
            }),
            'state': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'required': True,
            }),
            'logo': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
            }),
            'logo_alt': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الوصف البديل لشعار المعهد (SEO)',
                'dir': 'rtl',
            }),
            'main_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
                'required': True,
            }),
            'main_image_alt': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الوصف البديل للصورة الرئيسية (SEO)',
                'dir': 'rtl',
            }),
            'location': CustomHTMLEditorWidget(attrs={
                'data-placeholder': 'موقع المعهد (المدينة، الولاية)...',
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'رقم هاتف التواصل للمعهد لتسهيل التواصل والبحث المحلي',
                'dir': 'ltr',
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'رابط الموقع الرسمي للمعهد (sameAs)',
                'dir': 'ltr',
            }),
            
            # Rich Text Sections
            'introduction': CustomHTMLEditorWidget(attrs={
                'data-placeholder': 'مقدمة اختيارية تظهر في بداية صفحة المعهد...',
            }),
            'description': CustomHTMLEditorWidget(attrs={
                'data-placeholder': 'وصف شامل عن المعهد...',
            }),
            'why_choose_us': CustomHTMLEditorWidget(attrs={
                'data-placeholder': 'لماذا يختار الطلاب العرب هذا المعهد...',
            }),
            'english_study': CustomHTMLEditorWidget(attrs={
                'data-placeholder': 'معلومات وتفاصيل عن دراسة اللغة الإنجليزية في المعهد...',
            }),
            'fees_includes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثال: تكاليف الدراسة، ورسوم تأشيرة الطالب، ورسوم التأمين الصحي...',
                'rows': 2,
                'dir': 'rtl',
            }),
            'fees_excludes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثال: المصروف الشخصي، السكن المساعد، تذاكر الطيران...',
                'rows': 2,
                'dir': 'rtl',
            }),
            
            # Relationships
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
            'meta_title': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 auto-grow-textarea',
                'placeholder': '60 حرف كحد أقصى',
                'maxlength': '60',
                'dir': 'rtl',
                'rows': 1,
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
            'name': 'اسم المعهد',
            'slug': 'الرابط',
            'is_legacy': 'رابط قديم',
            'state': 'الولاية',
            'city': 'المدينة',
            'logo': 'شعار المعهد',
            'logo_alt': 'النص البديل للشعار',
            'main_image': 'الصورة الرئيسية',
            'main_image_alt': 'النص البديل للصورة الرئيسية',
            'location': 'الموقع',
            'telephone': 'رقم الهاتف',
            'website': 'الموقع الرسمي للمعهد',
            
            # Rich Text Sections
            'introduction': 'المقدمة',
            'description': 'وصف المعهد',
            'why_choose_us': 'لماذا يختار الطلاب العرب المعهد',
            'english_study': 'دراسة اللغة الإنجليزية',
            'fees_includes': 'الرسوم تشمل',
            'fees_excludes': 'الرسوم لا تشمل',
            
            # Relationships
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
            'is_legacy': 'تفعيل هذا الخيار سيجعل الرابط مباشراً بدون بادئة الفئة (مثال: /slug/ بدلاً من /institutes/slug/)',
            'state': 'الولاية التي يقع بها المعهد لتسهيل التصفية والبحث',
            'city': 'المدينة التي يقع بها المعهد لتسهيل التصفية والبحث',
            'logo': 'شعار المعهد (PNG مع خلفية شفافة مفضل)',
            'logo_alt': 'نص يصف محتوى شعار المعهد لمحركات البحث ومستعرضات الصور',
            'main_image': 'صورة رئيسية للمعهد',
            'main_image_alt': 'نص يصف محتوى الصورة الرئيسية للمعهد لمحركات البحث ومستعرضات الصور',
            'location': 'موقع المعهد الجغرافي بالتفصيل',
            'telephone': 'رقم هاتف التواصل للمعهد لتسهيل التواصل والبحث المحلي',
            'website': 'رابط الموقع الإلكتروني الرسمي للمعهد (sameAs)',
            
            # Rich Text Sections
            'introduction': 'مقدمة اختيارية تظهر في بداية صفحة المعهد',
            'description': 'وصف شامل عن المعهد للزوار والطلاب المهتمين',
            'why_choose_us': 'توضيح المميزات وأسباب تفضيل المعهد عن غيره للطلاب العرب',
            'english_study': 'معلومات عن دورات ومستويات اللغة الإنجليزية المتاحة بالمعهد وكيفية دراستها',
            'fees_includes': 'ما تشمله الرسوم الموضحة أدناه',
            'fees_excludes': 'ما لا تشمله الرسوم الموضحة أدناه',
            
            # Relationships
            'related_articles': 'اختر المقالات المرتبطة بهذا المعهد',
            'tags': 'اختر الوسوم المرتبطة بهذا المعهد',
            
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



    def save(self, commit=True):
        instance = super().save(commit=False)
        from apps.importer.services.image_downloader import delete_unused_media_file
        
        imported_logo_path = self.data.get('imported_logo_path') if self.data else None
        if imported_logo_path and (not self.files or 'logo' not in self.files):
            relative_path = imported_logo_path.replace('/media/', '', 1)
            if instance.logo and instance.logo.name != relative_path:
                delete_unused_media_file(instance.logo.name)
            instance.logo = relative_path
            
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


# Create inline formset for Course entries (Fee rows)
CourseFormSet = inlineformset_factory(
    Institute,
    Course,
    fields=['course_type', 'duration', 'fees_myr', 'fees_usd', 'fees_sar', 'visa_duration', 'sort_order'],
    extra=0,
    can_delete=True,
    widgets={
        'course_type': forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'required': True,
            'dir': 'rtl',
        }),
        'duration': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: شهر، شهرين، 3 أشهر',
            'required': True,
            'dir': 'rtl',
        }),
        'fees_myr': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: 3,400',
            'required': True,
            'dir': 'rtl',
        }),
        'fees_usd': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: 857',
            'required': False,
            'dir': 'rtl',
        }),
        'fees_sar': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: 3,216',
            'required': False,
            'dir': 'rtl',
        }),
        'visa_duration': forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'مثال: بدون تأشيرة، 6 أشهر، سنة',
            'required': False,
            'dir': 'rtl',
        }),
        'sort_order': forms.HiddenInput(),
    },
    labels={
        'course_type': 'نوع الكورس',
        'duration': 'مدة الكورس',
        'fees_myr': 'التكلفة بالرنجت MYR',
        'fees_usd': 'التكلفة بالدولار USD',
        'fees_sar': 'التكلفة بالريال SAR',
        'visa_duration': 'مدة تأشيرة الطالب',
        'sort_order': 'الترتيب',
    },
    help_texts={
        'course_type': 'اختر نوع الكورس (عادي / مكثف)',
        'duration': 'مثال: شهر، شهرين، 3 أشهر',
        'fees_myr': 'مثال: 3,400',
        'fees_usd': 'مثال: 857',
        'fees_sar': 'مثال: 3,216',
        'visa_duration': 'مثال: بدون تأشيرة، 6 أشهر، سنة',
        'sort_order': 'ترتيب ظهور الصف في الجدول (الأصغر أولاً)',
    }
)


class InstituteAttachmentForm(forms.ModelForm):
    """Form for uploading files for an institute."""
    class Meta:
        model = InstituteAttachment
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'عنوان الملف (مثال: الكتيب التعريفي، جدول الرسوم الدراسية)',
                'dir': 'rtl',
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
        }
        labels = {
            'title': 'عنوان الملف',
            'file': 'الملف',
        }


InstituteAttachmentFormSet = inlineformset_factory(
    Institute,
    InstituteAttachment,
    form=InstituteAttachmentForm,
    fields=['title', 'file'],
    extra=1,
    can_delete=True,
)


# Create inline formset for FAQ entries
InstituteFAQFormSet = inlineformset_factory(
    Institute,
    InstituteFAQ,
    fields=['question', 'answer', 'sort_order'],
    extra=0,
    can_delete=True,
    widgets={
        'question': forms.TextInput(attrs={
            'class': 'faq-item__question-input',
            'placeholder': 'السؤال',
            'required': True,
            'dir': 'rtl',
        }),
        'answer': CustomHTMLEditorWidget(attrs={
            'data-placeholder': 'الإجابة...',
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
        'question': 'السؤال الشائع',
        'answer': 'الإجابة عن السؤال الشائع',
    }
)


