"""
Article forms for the dashboard.
نماذج المقالات في لوحة التحكم
"""
from django import forms
from apps.articles.models import Article, Category, Tag
from apps.html_editor.widgets import CustomHTMLEditorWidget


class ArticleForm(forms.ModelForm):
    """
    Form for creating and editing articles with Custom HTML Editor.
    نموذج إنشاء وتعديل المقالات مع محرر HTML المخصص
    
    V1 Features:
    - Title, slug, featured image
    - Category and tags
    - Author (auto-set to current user)
    - Content with Custom HTML Editor (Bold, Italic, H2-H4, Lists, Links, Images)
    - Related content (Universities, Institutes, Majors)
    - Publishing status
    - SEO fields
    """
    
    class Meta:
        model = Article
        fields = [
            # Basic Information
            'title', 'slug', 'featured_image', 'featured_image_alt',
            # Content
            'category', 'tags', 'content',
            # Relationships
            'related_universities', 'related_institutes', 'related_majors',
            # Publishing
            'publish_status',
            # SEO Fields
            'meta_title', 'meta_description', 'focus_keyword', 'keyphrase_synonyms', 'canonical_url',
            'robots_index', 'robots_follow', 'sitemap_include',
            'og_title', 'og_description', 'og_image'
        ]
        widgets = {
            # Basic Information Section
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'عنوان المقالة',
                'required': True,
                'dir': 'rtl',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الرابط (يدعم الأحرف العربية)',
                'required': True,
                'dir': 'ltr',
            }),
            'featured_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
                'required': True,
            }),
            'featured_image_alt': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الوصف البديل للصورة المميزة (SEO)',
                'dir': 'rtl',
            }),
            
            # Content Section
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'tags': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2',
            }),
            'content': CustomHTMLEditorWidget(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'محتوى المقالة (يدعم: غامق، مائل، عناوين، قوائم، روابط، صور)',
                'rows': 15,
                'required': True,
                'dir': 'rtl',
            }),
            
            # Relationships
            'related_universities': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2',
            }),
            'related_institutes': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2',
            }),
            'related_majors': forms.CheckboxSelectMultiple(attrs={
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
            'title': 'عنوان المقالة',
            'slug': 'الرابط',
            'featured_image': 'الصورة المميزة',
            'featured_image_alt': 'النص البديل للصورة المميزة',
            
            # Content
            'category': 'الفئة',
            'tags': 'الوسوم',
            'content': 'محتوى المقالة',
            
            # Relationships
            'related_universities': 'الجامعات المرتبطة',
            'related_institutes': 'المعاهد المرتبطة',
            'related_majors': 'التخصصات المرتبطة',
            
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
            'featured_image': 'صورة مميزة للمقالة',
            'featured_image_alt': 'نص يصف محتوى الصورة المميزة للمقالة لمحركات البحث ومستعرضات الصور',
            
            # Content
            'category': 'اختر فئة المقالة',
            'tags': 'اختر الوسوم المرتبطة بالمقالة',
            'content': 'محتوى المقالة (يدعم: غامق، مائل، عناوين H2-H4، قوائم، روابط، صور)',
            
            # Relationships
            'related_universities': 'اختر الجامعات المرتبطة بهذه المقالة',
            'related_institutes': 'اختر المعاهد المرتبطة بهذه المقالة',
            'related_majors': 'اختر التخصصات المرتبطة بهذه المقالة',
            
            # Publishing
            'publish_status': 'المحتوى المنشور فقط يظهر للزوار',
            
            # SEO Fields
            'meta_title': 'يظهر في نتائج البحث (60 حرف كحد أقصى)',
            'meta_description': 'يظهر في نتائج البحث (160 حرف كحد أقصى)',
            'focus_keyword': 'الكلمة المفتاحية الرئيسية للصفحة',
            'keyphrase_synonyms': 'مرادفات للكلمة المفتاحية الرئيسية مفصولة بفواصل (، أو ,)',
            'canonical_url': 'اتركه فارغاً للاستخدام الافتراضي',
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
            if self.data.get('imported_featured_image_path'):
                self.fields['featured_image'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        from apps.importer.services.image_downloader import delete_unused_media_file
        
        imported_featured_image_path = self.data.get('imported_featured_image_path') if self.data else None
        if imported_featured_image_path and (not self.files or 'featured_image' not in self.files):
            relative_path = imported_featured_image_path.replace('/media/', '', 1)
            if instance.featured_image and instance.featured_image.name != relative_path:
                delete_unused_media_file(instance.featured_image.name)
            instance.featured_image = relative_path
            
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


class CategoryForm(forms.ModelForm):
    """
    Form for creating and editing article categories.
    نموذج إنشاء وتعديل فئات المقالات
    """
    
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'اسم الفئة',
                'required': True,
                'dir': 'rtl',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الرابط (يدعم الأحرف العربية)',
                'required': True,
                'dir': 'ltr',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'وصف الفئة',
                'rows': 4,
                'dir': 'rtl',
            }),
        }
        labels = {
            'name': 'اسم الفئة',
            'slug': 'الرابط',
            'description': 'الوصف',
        }
        help_texts = {
            'slug': 'رابط الفئة (يدعم الأحرف العربية)',
            'description': 'وصف الفئة (اختياري)',
        }


class TagForm(forms.ModelForm):
    """
    Form for creating and editing article tags.
    نموذج إنشاء وتعديل وسوم المقالات
    """
    
    class Meta:
        model = Tag
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'اسم الوسم',
                'required': True,
                'dir': 'rtl',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'الرابط (يدعم الأحرف العربية)',
                'required': True,
                'dir': 'ltr',
            }),
        }
        labels = {
            'name': 'اسم الوسم',
            'slug': 'الرابط',
        }
        help_texts = {
            'slug': 'رابط الوسم (يدعم الأحرف العربية)',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            return name
        queryset = Tag.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('هذا الوسم موجود بالفعل بهذا الاسم.')
        return name

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        if not slug:
            return slug
        queryset = Tag.objects.filter(slug__iexact=slug)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('هذا الرابط مستخدم بالفعل لوسم آخر.')
        return slug
