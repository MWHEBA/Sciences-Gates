"""
University forms for the dashboard.
نماذج الجامعات في لوحة التحكم
"""
from django import forms
from django.forms import inlineformset_factory
from apps.universities.models import University, UniversityFAQ, Faculty, Program, UniversityAttachment
from apps.html_editor.widgets import CustomHTMLEditorWidget


class UniversityForm(forms.ModelForm):
    """
    Form for creating and editing universities with structured template editor.
    نموذج إنشاء وتعديل الجامعات مع محرر القالب المنظم
    """
    city = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        }),
        required=False,
        label='المدينة',
        help_text='المدينة التي تقع بها الجامعة لتسهيل التصفية والبحث'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        all_cities = [('', 'اختر المدينة')]
        for state_code, cities in University.STATE_CITIES.items():
            all_cities.extend(cities)
        self.fields['city'].choices = all_cities

        if self.data:
            if self.data.get('imported_logo_path'):
                self.fields['logo'].required = False
            if self.data.get('imported_main_image_path'):
                self.fields['main_image'].required = False

    class Meta:
        model = University
        fields = [
            # Basic Information
            'name', 'slug', 'university_type', 'state', 'city', 'logo', 'main_image', 'location', 'video_url',
            'telephone', 'website',
            # Rich Text Sections
            'description',
            'admission_requirements_bachelor', 'admission_requirements_master', 'admission_requirements_phd', 'one_time_fees',
            # Relationships
            'related_majors', 'related_articles', 'tags',
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
                'placeholder': 'اسم الجامعة',
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
            'university_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'required': True,
            }),
            'state': forms.Select(attrs={
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
            'location': CustomHTMLEditorWidget(attrs={
                'data-placeholder': 'موقع الجامعة (المدينة، الولاية)...',
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'رابط فيديو YouTube أو Vimeo',
                'dir': 'ltr',
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'رقم الهاتف (مثال: \u200e+60 3-1234 5678)',
                'dir': 'ltr',
                'style': 'text-align: left; direction: ltr;',
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'رابط الموقع الرسمي للجامعة (sameAs)',
                'dir': 'ltr',
            }),
            
            # Rich Text Sections — Professional HTML Editor
            'description': CustomHTMLEditorWidget(attrs={
                'data-placeholder': 'وصف شامل عن الجامعة...',
            }),
            'admission_requirements_bachelor': CustomHTMLEditorWidget(attrs={
                'data-placeholder': 'شروط القبول لبرنامج البكالوريوس (Bachelor’s)...',
            }),
            'admission_requirements_master': CustomHTMLEditorWidget(attrs={
                'data-placeholder': 'شروط القبول لبرنامج الماجستير (Master’s)...',
            }),
            'admission_requirements_phd': CustomHTMLEditorWidget(attrs={
                'data-placeholder': 'شروط القبول لبرنامج الدكتوراه (PhD)...',
            }),
            'one_time_fees': forms.Textarea(attrs={
                'class': 'hidden',
                'id': 'id_one_time_fees',
                'style': 'display: none;',
            }),
            
            # Relationships
            'related_majors': forms.CheckboxSelectMultiple(attrs={
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
            'name': 'اسم الجامعة',
            'slug': 'الرابط (Slug)',
            'university_type': 'نوع الجامعة',
            'state': 'الولاية',
            'city': 'المدينة',
            'logo': 'شعار الجامعة',
            'main_image': 'الصورة الرئيسية',
            'location': 'الموقع',
            'video_url': 'رابط الفيديو',
            'telephone': 'رقم الهاتف',
            'website': 'الموقع الرسمي للجامعة',
            
            # Rich Text Sections
            'description': 'وصف الجامعة',
            'admission_requirements_bachelor': 'شروط القبول للبكالوريوس (Bachelor’s)',
            'admission_requirements_master': 'شروط القبول للماجستير (Master’s)',
            'admission_requirements_phd': 'شروط القبول للدكتوراه (PhD)',
            
            # Relationships
            'related_majors': 'التخصصات المرتبطة',
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
            'university_type': 'تصنيف الجامعة (حكومية أو خاصة)',
            'state': 'الولاية التي تقع بها الجامعة لتسهيل التصفية والبحث',
            'city': 'المدينة التي تقع بها الجامعة لتسهيل التصفية والبحث',
            'logo': 'شعار الجامعة (PNG مع خلفية شفافة مفضل)',
            'main_image': 'صورة رئيسية للجامعة',
            'location': 'موقع الجامعة (المدينة، الولاية)',
            'telephone': 'رقم هاتف التواصل للجامعة لتسهيل التواصل والبحث المحلي',
            'website': 'رابط الموقع الإلكتروني الرسمي للجامعة (sameAs)',
            
            # Rich Text Sections
            'description': 'وصف شامل عن الجامعة',
            'admission_requirements_bachelor': 'شروط القبول الخاصة ببرنامج البكالوريوس',
            'admission_requirements_master': 'شروط القبول الخاصة ببرنامج الماجستير',
            'admission_requirements_phd': 'شروط القبول الخاصة ببرنامج الدكتوراه',
            
            # Relationships
            'related_majors': 'اختر التخصصات المرتبطة بهذه الجامعة',
            'related_articles': 'اختر المقالات المرتبطة بهذه الجامعة',
            
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

    def clean_one_time_fees(self):
        data = self.cleaned_data.get('one_time_fees')
        if not data:
            return []
        
        # If it's already parsed as a list/dict (by Django's JSONField parser)
        if isinstance(data, list):
            parsed_data = data
        elif isinstance(data, str):
            import json
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("فشل في معالجة بيانات الرسوم الإضافية")
        else:
            raise forms.ValidationError("صيغة البيانات غير صحيحة")
            
        if not isinstance(parsed_data, list):
            raise forms.ValidationError("يجب أن تكون الرسوم الإضافية عبارة عن قائمة من الجداول")
            
        for idx, table in enumerate(parsed_data):
            if not isinstance(table, dict):
                raise forms.ValidationError(f"الجدول رقم {idx+1} غير صالح")
            if 'title' not in table or 'headers' not in table or 'rows' not in table:
                raise forms.ValidationError(f"الجدول رقم {idx+1} ينقصه حقول أساسية (العنوان أو الأعمدة أو الصفوف)")
            if not isinstance(table['headers'], list):
                raise forms.ValidationError(f"أعمدة الجدول رقم {idx+1} غير صالحة")
            if not isinstance(table['rows'], list):
                raise forms.ValidationError(f"صفوف الجدول رقم {idx+1} غير صالحة")
            for r_idx, row in enumerate(table['rows']):
                if not isinstance(row, list):
                    raise forms.ValidationError(f"الصف رقم {r_idx+1} في الجدول رقم {idx+1} غير صالح")
                    
        return parsed_data


# Create inline formset for FAQ entries
UniversityFAQFormSet = inlineformset_factory(
    University,
    UniversityFAQ,
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
        'answer': 'إجابة السؤال',
        'sort_order': 'ترتيب ظهور السؤال (الأصغر أولاً)',
    }
)


# Create inline formset for Faculty entries
class FacultyFormSetForm(forms.ModelForm):
    """Form for Faculty in inline formset"""
    class Meta:
        model = Faculty
        fields = ['name', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'faculty-item__input',
                'placeholder': 'اسم الكلية',
                'required': True,
                'dir': 'rtl',
            }),
            'sort_order': forms.HiddenInput(),
        }
        labels = {
            'name': 'اسم الكلية',
            'sort_order': 'ترتيب العرض',
        }


from django.forms.models import BaseInlineFormSet

class BaseFacultyFormSet(BaseInlineFormSet):
    """
    Custom FormSet to handle unique validation conflicts on Faculty name and university.
    If a faculty with the same name exists but is marked for deletion in the same transaction,
    we ignore the validation error because the conflict will be resolved upon saving.
    Also handles matching and updating existing faculties during import when duplicates are submitted.
    """
    def clean(self):
        super().clean()
        
        def normalize_arabic(text):
            if not text:
                return ""
            import re
            text = text.strip()
            text = re.sub(r'[أإآ]', 'ا', text)
            text = re.sub(r'ة', 'ه', text)
            text = re.sub(r'ى', 'ي', text)
            text = re.sub(r'\s+', ' ', text)
            return text.lower()
            
        # Collect all existing faculties for this university
        if self.instance and self.instance.pk:
            existing_faculties = {
                normalize_arabic(f.name): f 
                for f in Faculty.objects.filter(university=self.instance)
            }
        else:
            existing_faculties = {}
            
        if not existing_faculties:
            return

        for form in self.forms:
            # Skip if already marked for deletion
            if self.can_delete and self._should_delete_form(form):
                continue
                
            # We only care about new forms (unsaved instances)
            if form.instance and not form.instance.pk:
                name = form.cleaned_data.get('name')
                if name:
                    norm_name = normalize_arabic(name)
                    existing_obj = existing_faculties.get(norm_name)
                    if existing_obj:
                        # Find if there is an old form in this formset that is currently bound to this existing_obj
                        old_form = None
                        for f in self.forms:
                            if f.instance and f.instance.pk == existing_obj.pk:
                                old_form = f
                                break
                                
                        if old_form:
                            # If the old form is marked for deletion, swap them!
                            if self.can_delete and self._should_delete_form(old_form):
                                # Delete old programs of the existing faculty from database to avoid duplicates
                                existing_obj.programs.all().delete()
                                
                                # Swap instances:
                                # Give the old form a new dummy instance with no PK
                                old_form.instance = Faculty(university=self.instance)
                                # Bind the existing_obj to the new form
                                form.instance = existing_obj
                                form.instance.name = name
                                
                                # Remove program_formset from old_form so it's not processed/saved
                                if hasattr(old_form, 'program_formset'):
                                    del old_form.program_formset
                                
                                # Clear unique validation errors on the new form
                                if form._errors:
                                    for field in list(form._errors.keys()):
                                        filtered = [
                                            err for err in form._errors[field]
                                            if not any(w in str(err) for w in ['موجود', 'سلفا', 'exists', 'معا', 'already exists'])
                                        ]
                                        if filtered:
                                            form._errors[field] = form.error_class(filtered)
                                        else:
                                            del form._errors[field]
                        else:
                            # Delete old programs of the existing faculty from database to avoid duplicates
                            existing_obj.programs.all().delete()
                            
                            # Bind the existing_obj to the new form directly
                            form.instance = existing_obj
                            form.instance.name = name
                            
                            # Clear unique validation errors on the new form
                            if form._errors:
                                for field in list(form._errors.keys()):
                                    filtered = [
                                        err for err in form._errors[field]
                                        if not any(w in str(err) for w in ['موجود', 'سلفا', 'exists', 'معا', 'already exists'])
                                    ]
                                    if filtered:
                                        form._errors[field] = form.error_class(filtered)
                                    else:
                                        del form._errors[field]

    def validate_unique(self):
        super().validate_unique()
        
        # Get IDs of forms marked for deletion in this formset
        deleted_ids = set()
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                if form.instance and form.instance.pk:
                    deleted_ids.add(form.instance.pk)
        
        if not deleted_ids:
            return
            
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
                
            if not form._errors:
                continue
                
            name = form.cleaned_data.get('name')
            if name and form.instance:
                # Find if any conflicting instance exists in the database
                qs = Faculty.objects.filter(university=self.instance, name__iexact=name)
                if form.instance.pk:
                    qs = qs.exclude(pk=form.instance.pk)
                
                conflicting_instance = qs.first()
                if conflicting_instance and conflicting_instance.pk in deleted_ids:
                    # Clean the unique error from the form since the conflicting database entry is being deleted
                    for key in list(form._errors.keys()):
                        filtered_errors = []
                        for err in form._errors[key]:
                            err_str = str(err)
                            if any(word in err_str for word in ['موجود', 'سلفا', 'exists', 'معا', 'already exists']):
                                continue
                            filtered_errors.append(err)
                        
                        if filtered_errors:
                            form._errors[key] = form.error_class(filtered_errors)
                        else:
                            del form._errors[key]


UniversityFacultyFormSet = inlineformset_factory(
    University,
    Faculty,
    form=FacultyFormSetForm,
    formset=BaseFacultyFormSet,
    fields=['name', 'sort_order'],
    extra=0,
    max_num=100,
    can_delete=True,
)


# ============================================================================
# Nested Program Formset for Faculty
# ============================================================================

class YearlyFeesFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.yearly_fees:
            # Convert JSON dict to newline-separated string
            lines = []
            for year, fee in self.instance.yearly_fees.items():
                lines.append(f"{year}: {fee}")
            self.initial['yearly_fees'] = "\n".join(lines)

    def clean_yearly_fees(self):
        data = self.cleaned_data.get('yearly_fees')
        if not data:
            return None
        
        # If it's already a dict (e.g. from initial parsing or JSON processing)
        if isinstance(data, dict):
            return data
            
        yearly_fees_dict = {}
        # Support both windows and unix newlines
        lines = [line.strip() for line in data.replace('\r\n', '\n').split('\n') if line.strip()]
        for line_num, line in enumerate(lines, 1):
            if ':' not in line:
                raise forms.ValidationError(
                    f"تنسيق غير صحيح في السطر {line_num}. يجب أن يكون التنسيق 'السنة: الرسوم' (مثال: السنة الأولى: 5,000)"
                )
            parts = line.split(':', 1)
            key = parts[0].strip()
            val = parts[1].strip()
            if not key or not val:
                raise forms.ValidationError(
                    f"بيانات ناقصة في السطر {line_num}. يجب تحديد السنة والرسوم."
                )
            yearly_fees_dict[key] = val
            
        return yearly_fees_dict


class ProgramFormSetForm(YearlyFeesFormMixin, forms.ModelForm):
    """Form for Program in nested formset within Faculty"""
    yearly_fees = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'fpm-program-input fpm-program-input--textarea',
            'placeholder': 'السنة الاولى: 5,424\nالسنة الثانية: 4,964',
            'dir': 'rtl',
            'rows': 2,
        }),
        required=False,
        label='الرسوم السنوية التفصيلية',
        help_text='رسوم كل سنة دراسية بشكل منفصل (اختياري).'
    )

    class Meta:
        model = Program
        fields = ['major', 'name', 'duration', 'tuition_fees', 'yearly_fees', 'sort_order']
        widgets = {
            'major': forms.Select(attrs={
                'class': 'fpm-program-input fpm-program-input--select',
                'dir': 'rtl',
            }),
            'name': forms.Textarea(attrs={
                'class': 'fpm-program-input fpm-program-input--textarea',
                'placeholder': 'اسم البرنامج',
                'dir': 'rtl',
                'required': True,
                'rows': 1,
            }),
            'duration': forms.TextInput(attrs={
                'class': 'fpm-program-input fpm-program-input--short',
                'placeholder': '4 سنوات',
                'dir': 'rtl',
                'required': True,
            }),
            'tuition_fees': forms.TextInput(attrs={
                'class': 'fpm-program-input fpm-program-input--short',
                'placeholder': '25,000 دولار',
                'dir': 'rtl',
                'required': True,
            }),
            'sort_order': forms.HiddenInput(),
        }
        labels = {
            'major': 'التخصص المرتبط',
            'name': 'اسم البرنامج',
            'duration': 'مدة الدراسة',
            'tuition_fees': 'الرسوم الدراسية',
            'yearly_fees': 'الرسوم السنوية التفصيلية',
            'sort_order': 'ترتيب العرض',
        }


# Nested Program Formset
NestedProgramFormSet = inlineformset_factory(
    Faculty,
    Program,
    form=ProgramFormSetForm,
    fields=['major', 'name', 'duration', 'tuition_fees', 'yearly_fees', 'sort_order'],
    extra=0,
    max_num=50,
    can_delete=True,
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


class ProgramForm(YearlyFeesFormMixin, forms.ModelForm):
    """
    Form for creating and editing programs.
    نموذج إنشاء وتعديل البرامج
    """
    yearly_fees = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'السنة الاولى: 5,424\nالسنة الثانية: 4,964',
            'dir': 'rtl',
            'rows': 3,
        }),
        required=False,
        label='الرسوم السنوية التفصيلية',
        help_text='رسوم كل سنة دراسية بشكل منفصل (اختياري).'
    )
    
    class Meta:
        model = Program
        fields = ['major', 'name', 'duration', 'tuition_fees', 'yearly_fees', 'sort_order']
        widgets = {
            'major': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'dir': 'rtl',
            }),
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
            'major': 'التخصص المرتبط',
            'name': 'اسم البرنامج',
            'duration': 'مدة الدراسة',
            'tuition_fees': 'الرسوم الدراسية',
            'yearly_fees': 'الرسوم السنوية التفصيلية',
            'sort_order': 'ترتيب العرض',
        }
        help_texts = {
            'major': 'اختر التخصص العام المرتبط بهذا البرنامج (مثال: الوسائط المتعددة)',
            'name': 'اسم البرنامج (مثال: هندسة البرمجيات)',
            'duration': 'مدة الدراسة (مثال: 4 سنوات)',
            'tuition_fees': 'الرسوم الدراسية (مثال: 20,000 رنجت ماليزي سنوياً)',
            'yearly_fees': 'رسوم كل سنة دراسية بشكل منفصل (اختياري).',
            'sort_order': 'ترتيب ظهور البرنامج (الأصغر أولاً)',
        }



# Create inline formset for Program entries
ProgramFormSet = inlineformset_factory(
    Faculty,
    Program,
    form=ProgramForm,
    fields=['major', 'name', 'duration', 'tuition_fees', 'yearly_fees', 'sort_order'],
    extra=1,
    can_delete=True,
)


class UniversityAttachmentForm(forms.ModelForm):
    """Form for uploading files for a university."""
    class Meta:
        model = UniversityAttachment
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'عنوان الملف (مثال: الكتيب التعريفي، دليل الرسوم)',
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


UniversityAttachmentFormSet = inlineformset_factory(
    University,
    UniversityAttachment,
    form=UniversityAttachmentForm,
    fields=['title', 'file'],
    extra=1,
    can_delete=True,
)

