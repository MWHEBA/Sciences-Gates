"""
Core views for the Science Gates platform.
"""
from django.views.generic import TemplateView, View, FormView
from django.shortcuts import redirect
from django.http import Http404
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse_lazy
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article
from apps.core.models import PublishStatus
from apps.leads.forms import LeadForm



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
        
        # Fetch featured universities (published only) - Limited to 3 items per user request
        universities = University.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).prefetch_related(
            'faculties__programs',
            'faqs',
            'related_majors',
            'related_articles'
        )[:3]
        
        # Fetch featured institutes (published only) - Limited to 2 items per user request
        institutes = Institute.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).prefetch_related(
            'courses',
            'related_articles'
        )[:2]
        
        # Fetch featured majors (published only) - Limited to 2 items per user request
        majors = Major.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).prefetch_related(
            'best_universities',
            'cheap_universities',
            'related_articles',
            'subjects_tables',
            'salary_tables',
            'countries_tables'
        )[:2]
        
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


class VisaTrackingView(FormView):
    """
    متابعة حالة الفيزا الدراسية (EMGS) وتقديم طلبات الدعم
    """
    template_name = 'visa_tracking.html'
    form_class = LeadForm
    success_url = reverse_lazy('visa_tracking')

    def post(self, request, *args, **kwargs):
        from django.core.cache import cache
        ip_address = request.META.get('REMOTE_ADDR')
        rate_key = f"visa_rate_limit_{ip_address}"
        submissions = cache.get(rate_key, 0)
        
        if submissions >= 3:
            messages.error(request, 'تم تجاوز الحد الأقصى للطلبات المسموحة في الساعة. يرجى المحاولة لاحقاً.')
            form = self.get_form()
            return self.form_invalid(form)
            
        cache.set(rate_key, submissions + 1, 3600)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # بنجهز سياق الصفحة وبنمرر رابط الصفحة كـ source_page للموديل
        context = super().get_context_data(**kwargs)
        context['source_page'] = self.request.build_absolute_uri(self.request.path)
        return context

    def form_valid(self, form):
        # حفظ طلب الدعم كـ Lead من نوع استفسار وإضافة علامة تدل على المصدر
        lead = form.save(commit=False)
        lead.lead_type = 'contact'
        lead.source_page = self.request.build_absolute_uri(self.request.path)
        lead.referrer = self.request.META.get('HTTP_REFERER', '')
        
        # بنضيف مقدمة لرسالة الطالب عشان لو الإدمن شافها في لوحة التحكم يفهم إنها من صفحة الفيزا
        user_msg = lead.message or ""
        lead.message = f"💬 [طلب مساعدة في تتبع الفيزا - EMGS]\n\n{user_msg}".strip()
        
        lead.save()
        messages.success(
            self.request,
            'تم إرسال طلب المساعدة بنجاح. سيقوم أحد مستشارينا بالتحقق من حالة طلبك والتواصل معك قريباً.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        # رسالة خطأ للمستخدم في حال وجود مشاكل في الفورم
        messages.error(
            self.request,
            'حدث خطأ في إرسال النموذج. يرجى التحقق من صحة البيانات المدخلة.'
        )
        return super().form_invalid(form)



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


