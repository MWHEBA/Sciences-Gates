"""
General FAQ forms for dashboard.
نموذج إدارة الأسئلة الشائعة العامة في لوحة التحكم
"""
from django import forms
from apps.core.models import GeneralFAQ
from apps.core.navigation import auto_shift_order_if_changed, get_next_order
from apps.html_editor.widgets import CustomHTMLEditorWidget


class GeneralFAQForm(forms.ModelForm):
    """
    Form for creating and editing General Platform FAQs.
    نموذج إضافة وتعديل الأسئلة الشائعة العامة
    """
    order = forms.IntegerField(
        required=False,
        label='ترتيب العرض',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '0',
            'min': '0',
        }),
        help_text='ترتيب ظهور السؤال ضمن القائمة (يبدأ من 1)'
    )

    class Meta:
        model = GeneralFAQ
        fields = [
            'question',
            'slug',
            'category',
            'order',
            'is_featured',
            'is_published',
            'answer',
        ]
        widgets = {
            'question': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'اكتب نص السؤال بوضوح...',
                'required': True,
                'dir': 'rtl',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm',
                'placeholder': 'admission-requirements (اتركه فارغاً للتوليد التلقائي)',
                'dir': 'ltr',
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'required': True,
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
            'answer': CustomHTMLEditorWidget(attrs={
                'data-placeholder': 'اكتب الإجابة الشاملة هنا...',
            }),
        }
        labels = {
            'question': 'نص السؤال',
            'slug': 'المعرف اللاتيني (Slug)',
            'category': 'التصنيف',
            'is_featured': 'تمييز في الصفحة الرئيسية (Featured)',
            'is_published': 'حالة النشر (منشور)',
            'answer': 'نص الإجابة',
        }
        help_texts = {
            'slug': 'معرف لاتيني فريد يُستخدم في الرابط المباشر والـ Anchor (#slug). اتركه فارغاً ليتم توليده تلقائياً.',
            'is_featured': 'عند التفعيل يظهر السؤال ضمن أهم 5 أسئلة في الصفحة الرئيسية.',
            'is_published': 'عند إلغاء التفعيل لن يظهر السؤال للزوار في صفحة الأسئلة أو الرئيسية.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get('order'):
            self.initial['order'] = get_next_order(GeneralFAQ)

    def save(self, commit=True):
        instance = super().save(commit=False)
        auto_shift_order_if_changed(self, GeneralFAQ, instance)
        if commit:
            instance.save()
        return instance
