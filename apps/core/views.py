"""
Core views for the Science Gates platform.
"""
from django.views.generic import TemplateView, View
from django.shortcuts import redirect
from django.http import Http404
from django.db.models import Q
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article
from apps.core.models import PublishStatus


class HomeView(TemplateView):
    """
    Homepage view displaying featured content from all content types.
    
    Fetches and displays:
    - Featured universities (published, limited to 6)
    - Featured institutes (published, limited to 6)
    - Featured majors (published, limited to 6)
    - Recent articles (published, limited to 6)
    
    Requirements: 1, 19
    """
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        """
        Fetch featured content for the homepage.
        
        Uses select_related and prefetch_related for query optimization.
        Only includes published content.
        
        Query Optimization:
        - Uses select_related for foreign key relationships
        - Uses prefetch_related for many-to-many and reverse foreign key relationships
        - Limits results to 6 items per content type
        """
        context = super().get_context_data(**kwargs)
        
        # Fetch featured universities (published only)
        universities = University.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).prefetch_related(
            'faculties__programs',
            'faqs',
            'related_majors',
            'related_articles'
        )[:6]
        
        # Fetch featured institutes (published only) - Limited to 4 items per user request
        institutes = Institute.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).prefetch_related(
            'courses',
            'related_articles'
        )[:4]
        
        # Fetch featured majors (published only) - Limited to 4 items per user request
        majors = Major.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).prefetch_related(
            'best_universities',
            'cheap_universities',
            'related_articles',
            'subjects_tables',
            'salary_tables',
            'countries_tables'
        )[:4]
        
        # Fetch recent articles (published only)
        articles = Article.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).select_related(
            'category',
            'author'
        ).prefetch_related(
            'tags',
            'related_universities',
            'related_institutes',
            'related_majors'
        ).order_by('-publish_date')[:6]
        
        # Temporary hardcoded FAQs for the homepage
        faqs = [
            {
                'question': 'هل الشهادات الماليزية معترف بها دولياً وعربياً؟',
                'answer': 'نعم، جميع الجامعات الشريكة لنا معترف بها ومصنفة عالمياً ضمن تصنيف QS العالمي، ومعترف بها بالكامل في الدول العربية ومختلف دول العالم.'
            },
            {
                'question': 'ما هي شروط القبول للدراسة في الجامعات الماليزية؟',
                'answer': 'تختلف الشروط حسب التخصص والجامعة، ولكن بشكل عام يُشترط الحصول على شهادة الثانوية العامة بمعدل مناسب للتخصص المطلوب، بالإضافة إلى ما يثبت كفاءة اللغة الإنجليزية (مثل الآيلتس أو التوفل)، وإن لم تتوفر لديك اللغة يمكنك البدء بدورة لغة إنجليزية في الجامعة أو المعهد أولاً.'
            },
            {
                'question': 'هل يمكنني الدراسة في ماليزيا بدون شهادة آيلتس (IELTS)؟',
                'answer': 'نعم، يمكنك الحصول على قبول مشروط، والبدء بدراسة اللغة الإنجليزية في مركز اللغات التابع للجامعة أو في معهد لغة متخصص، ثم الانتقال لدراسة تخصصك الأكاديمي بعد اجتياز اختبار اللغة.'
            },
            {
                'question': 'ما هي تكلفة المعيشة والسكن للطلاب في ماليزيا؟',
                'answer': 'تُعد تكلفة المعيشة في ماليزيا مناسبة جداً واقتصادية مقارنة بالدول الغربية. تتراوح التكلفة الشهرية للمعيشة والسكن المتواضع للطلب ما بين 300 إلى 500 دولار أمريكي، شاملة السكن، الطعام، والمواصلات المحلية.'
            },
            {
                'question': 'كم تستغرق فترة الحصول على القبول الجامعي والفيزا؟',
                'answer': 'يستغرق الحصول على القبول الأكاديمي من الجامعة عادةً ما بين 3 إلى 7 أيام عمل، بينما تستغرق إجراءات استخراج تأشيرة الطالب (VAL) من هيئة التعليم العالي الماليزي (EMGS) ما بين 3 إلى 6 أسابيع.'
            }
        ]

        context.update({
            'universities': universities,
            'featured_universities': universities,
            'institutes': institutes,
            'featured_institutes': institutes,
            'majors': majors,
            'featured_majors': majors,
            'articles': articles,
            'latest_articles': articles,
            'faqs': faqs,
        })
        
        return context


class AboutView(TemplateView):
    """
    About Us page view displaying details about Sciences Gates company.
    """
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch all published universities that have logos
        universities_with_logos = University.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).exclude(logo='').only('name', 'logo')
        context['universities_with_logos'] = universities_with_logos
        return context


class LegacyUrlDetailView(View):
    """
    Fallback view for handling legacy (old style) URLs: /<slug>/.
    Dynamically routes to University, Institute, Major, or Article detail views.
    """
    def dispatch(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        
        # Check University
        university = University.objects.filter(slug=slug).first()
        if university:
            return redirect(university.get_absolute_url(), permanent=True)
                
        # Check Institute
        institute = Institute.objects.filter(slug=slug).first()
        if institute:
            return redirect(institute.get_absolute_url(), permanent=True)
                
        # Check Major
        major = Major.objects.filter(slug=slug).first()
        if major:
            return redirect(major.get_absolute_url(), permanent=True)
                
        # Check Article
        article = Article.objects.filter(slug=slug).first()
        if article:
            return redirect(article.get_absolute_url(), permanent=True)
                
        raise Http404("الصفحة غير موجودة")


