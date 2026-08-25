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
    - Featured universities (published, limited to 3)
    - Featured institutes (published, limited to 3)
    - Featured majors (published, limited to 3)
    - Recent articles (published, limited to 3)
    
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
        - Limits featured content to 3 items per type
        """
        context = super().get_context_data(**kwargs)
        from apps.core.navigation import get_navigation_slots_dict, build_curated_list_with_dedup_fallback
        
        # Fetch featured universities (published only) using curated slots + fallback
        univ_pool = University.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).order_by('order', 'name').prefetch_related(
            'faculties__programs',
            'faqs',
            'related_majors',
            'related_articles'
        )
        univ_slots = get_navigation_slots_dict('home_featured_univ')
        universities = build_curated_list_with_dedup_fallback(univ_slots, univ_pool, 3)
        
        # Fetch featured institutes (published only) using curated slots + fallback
        inst_pool = Institute.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).order_by('order', 'name').prefetch_related(
            'courses',
            'related_articles'
        )
        inst_slots = get_navigation_slots_dict('home_featured_institute')
        institutes = build_curated_list_with_dedup_fallback(inst_slots, inst_pool, 2)
        
        # Fetch featured majors (published only) using curated slots + fallback
        major_pool = Major.objects.filter(
            publish_status=PublishStatus.PUBLISHED
        ).order_by('order', 'name').prefetch_related(
            'best_universities',
            'cheap_universities',
            'related_articles',
            'subjects_tables',
            'salary_tables',
            'countries_tables'
        )
        major_slots = get_navigation_slots_dict('home_featured_major')
        majors = build_curated_list_with_dedup_fallback(major_slots, major_pool, 2)
        
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
        ).order_by('-publish_date')[:3]
        
        # Temporary hardcoded FAQs for the homepage
        faqs = [
            {
                'question': 'هل الشهادات الماليزية معترف بها دولياً وعربياً؟',
                'answer': 'نعم، الجامعات الشريكة تشتمل على جامعات حكومية وخاصة مرموقة معتمدة رسمياً، من بينها جامعات مصنفة ضمن تصنيفات QS العالمية ومقبولة في الدول العربية وخارجها.'
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
                'answer': 'تُعد تكلفة المعيشة في ماليزيا مناسبة جداً واقتصادية مقارنة بالدول الغربية. تتراوح التكلفة الشهرية للمعيشة والسكن للطلاب عادةً ما بين 400 إلى 800 دولار أمريكي، شاملة السكن والطعام والمواصلات حسب نمط الحياة والمدينة.'
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


class ContactView(TemplateView):
    """
    Contact Us page view displaying company contact details and inquiry form.
    """
    template_name = 'contact.html'


class VisaTrackingView(FormView):
    """
    متابعة حالة الفيزا الدراسية (EMGS) وتقديم طلبات الدعم
    """
    template_name = 'visa_tracking.html'
    form_class = LeadForm
    success_url = reverse_lazy('visa_tracking')

    def post(self, request, *args, **kwargs):
        from django.core.cache import cache
        from django.conf import settings
        is_testing = getattr(settings, 'TESTING', False)
        from apps.core.utils import get_client_ip
        ip_address = get_client_ip(request)
        rate_key = f"visa_rate_limit_{ip_address}"
        submissions = cache.get(rate_key, 0)
        
        if submissions >= 3 and not is_testing:
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


def csrf_failure(request, reason=""):
    """
    Custom CSRF failure handler.
    Handles CSRF failures gracefully for both public visitors and dashboard admins.
    Prevents public visitors (submitting contact/lead forms) from being redirected to the admin login page.
    """
    from django.http import JsonResponse
    from django.conf import settings

    # 1. Handle AJAX / JSON requests
    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.META.get('HTTP_ACCEPT', '')
        or request.content_type == 'application/json'
    )
    if is_ajax:
        return JsonResponse({
            'success': False,
            'csrf_error': True,
            'message': 'انتهت الجلسة المؤقتة للنموذج، يرجى إعادة تحميل الصفحة والمحاولة مرة أخرى.'
        }, status=403)

    # 2. Handle authenticated users
    if request.user.is_authenticated:
        messages.info(request, 'أنت مسجل الدخول بالفعل.')
        if getattr(request.user, 'is_staff', False):
            return redirect('dashboard:home')
        return redirect('home')

    # 3. Determine if request originated from dashboard area
    referer = request.META.get('HTTP_REFERER', '')
    path = request.path or ''
    dashboard_prefix = f"/{getattr(settings, 'DASHBOARD_URL', 'sg/').strip('/')}"
    admin_prefix = f"/{getattr(settings, 'ADMIN_URL', 'mw-admin/').strip('/')}"

    is_dashboard = (
        path.startswith(dashboard_prefix) or 
        path.startswith(admin_prefix) or 
        dashboard_prefix in referer or 
        admin_prefix in referer
    )

    if is_dashboard:
        messages.warning(request, 'انتهت الجلسة المؤقتة للنموذج، يرجى التحديث والمحاولة مرة أخرى.')
        return redirect('dashboard:login')

    # 4. Public Visitor: redirect back to source_page, referer, or current path (never dashboard:login)
    from django.utils.http import url_has_allowed_host_and_scheme
    messages.warning(request, 'انتهت الجلسة المؤقتة للنموذج، يرجى إعادة محاولة إرسال البيانات.')
    
    allowed_hosts = {request.get_host(), 'sciencesgates.com', 'www.sciencesgates.com', 'localhost:8000', '127.0.0.1:8000'}
    
    source_page = request.POST.get('source_page', '').strip()
    if source_page and url_has_allowed_host_and_scheme(source_page, allowed_hosts=allowed_hosts, require_https=request.is_secure()):
        return redirect(source_page)

    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts=allowed_hosts, require_https=request.is_secure()):
        return redirect(referer)

    if path and path.startswith('/'):
        return redirect(path)

    return redirect('home')



class PrivacyView(TemplateView):
    """View for displaying Privacy Policy page."""
    template_name = 'privacy.html'


class TermsView(TemplateView):
    """View for displaying Terms of Service page."""
    template_name = 'terms.html'




