"""
Search forms for the search app.
"""
from django import forms


class SearchForm(forms.Form):
    """Form for searching across content types."""
    query = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'ابحث عن جامعات أو معاهد أو تخصصات أو مقالات...',
            'dir': 'rtl',
            'autocomplete': 'off',
        }),
        label='البحث'
    )


class AdvancedSearchForm(forms.Form):
    """Advanced search form with filters."""
    
    LANGUAGE_CHOICES = [
        ('', 'جميع اللغات'),
        ('arabic', 'العربية'),
        ('english', 'الإنجليزية'),
        ('both', 'العربية والإنجليزية'),
    ]
    
    UNIVERSITY_TYPE_CHOICES = [
        ('', 'جميع الأنواع'),
        ('public', 'جامعات حكومية'),
        ('private', 'جامعات خاصة'),
    ]
    
    INSTITUTE_TYPE_CHOICES = [
        ('', 'جميع الأنواع'),
        ('language', 'معاهد لغة'),
        ('academic', 'معاهد أكاديمية'),
    ]
    
    MAJOR_CATEGORY_CHOICES = [
        ('', 'جميع الفئات'),
        ('medical', 'التخصصات الطبية'),
        ('engineering', 'التخصصات الهندسية'),
        ('cs', 'الحاسوب والتكنولوجيا'),
        ('business', 'إدارة الأعمال'),
        ('science', 'العلوم'),
        ('other', 'تخصصات أخرى'),
    ]
    
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
            'placeholder': 'ابحث...',
            'dir': 'rtl',
        }),
        label='البحث'
    )
    
    # Tuition fees filter
    min_tuition = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
            'placeholder': 'الحد الأدنى',
        }),
        label='الحد الأدنى للرسوم'
    )
    
    max_tuition = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
            'placeholder': 'الحد الأقصى',
        }),
        label='الحد الأقصى للرسوم'
    )
    
    # Language filter
    study_language = forms.ChoiceField(
        required=False,
        choices=LANGUAGE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
        }),
        label='لغة الدراسة'
    )
    
    # University type filter
    university_type = forms.ChoiceField(
        required=False,
        choices=UNIVERSITY_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
        }),
        label='نوع الجامعة'
    )
    
    # Institute type filter
    institute_type = forms.ChoiceField(
        required=False,
        choices=INSTITUTE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
        }),
        label='نوع المعهد'
    )
    
    # Major category filter
    major_category = forms.ChoiceField(
        required=False,
        choices=MAJOR_CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
        }),
        label='فئة التخصص'
    )
