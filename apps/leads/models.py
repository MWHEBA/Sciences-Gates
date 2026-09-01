from functools import lru_cache
from urllib.parse import unquote, urlparse, parse_qs
from django.db import models
from django.apps import apps
from django.conf import settings
from apps.core.models import TimestampedModel


@lru_cache(maxsize=256)
def resolve_entity_name_from_path(path_clean, query_string=''):
    """
    Smart Entity Resolution Engine with LRU caching.
    Maps a URL path and query to an official Arabic entity/page name.
    """
    if not path_clean:
        return "الصفحة الرئيسية"
    
    parts = [p for p in path_clean.strip('/').split('/') if p]
    if not parts:
        return "الصفحة الرئيسية"
    
    # Check fixed static pages
    first = parts[0].lower()
    if first in ('about-us', 'about'):
        return "صفحة من نحن"
    elif first == 'contact':
        return "صفحة اتصل بنا"
    elif first == 'visa-tracking':
        return "صفحة تتبع التأشيرة (EMGS)"
    elif first == 'privacy':
        return "صفحة سياسة الخصوصية"
    elif first == 'terms':
        return "صفحة الشروط والأحكام"
    elif first == 'search':
        if query_string:
            qs = parse_qs(query_string)
            q_val = qs.get('q', [''])[0].strip()
            if q_val:
                return f"صفحة البحث عن: ({unquote(q_val)})"
        return "صفحة البحث"
    elif first == 'leads':
        return "نموذج التقديم والاستفسار"
    
    # 1. Universities
    if first == 'universities':
        if len(parts) == 1:
            if query_string:
                qs = parse_qs(query_string)
                if 'type' in qs and qs['type'][0] == 'private':
                    return "دليل الجامعات الخاصة"
                elif 'type' in qs and qs['type'][0] == 'public':
                    return "دليل الجامعات الحكومية"
            return "دليل الجامعات"
        elif len(parts) >= 2:
            if parts[1] == 'state' and len(parts) >= 3:
                state_slug = parts[2]
                return f"جامعات ولاية: {state_slug}"
            slug = parts[-1]
            try:
                University = apps.get_model('universities', 'University')
                uni = University.objects.filter(slug__in=[slug, unquote(slug)]).first()
                if uni:
                    return f"جامعة: {uni.name}"
            except Exception:
                pass
            return f"جامعة: {slug.replace('-', ' ').replace('_', ' ')}"
            
    # 2. Majors / Programs
    elif first in ('majors', 'courses'):
        if len(parts) == 1:
            return "دليل التخصصات الدراسية"
        elif len(parts) >= 2:
            if parts[1] == 'category' and len(parts) >= 3:
                cat_slug = parts[2]
                try:
                    MajorCategory = apps.get_model('majors', 'MajorCategory')
                    cat = MajorCategory.objects.filter(slug__in=[cat_slug, unquote(cat_slug)]).first()
                    if cat:
                        return f"فئة تخصصات: {cat.name}"
                except Exception:
                    pass
                return f"فئة تخصصات: {cat_slug.replace('-', ' ')}"
            slug = parts[-1]
            try:
                Major = apps.get_model('majors', 'Major')
                major = Major.objects.filter(slug__in=[slug, unquote(slug)]).first()
                if major:
                    return f"تخصص: {major.name}"
            except Exception:
                pass
            return f"تخصص: {slug.replace('-', ' ').replace('_', ' ')}"
            
    # 3. Institutes
    elif first == 'institutes':
        if len(parts) == 1:
            return "دليل معاهد اللغة"
        elif len(parts) >= 2:
            slug = parts[-1]
            try:
                Institute = apps.get_model('institutes', 'Institute')
                inst = Institute.objects.filter(slug__in=[slug, unquote(slug)]).first()
                if inst:
                    return f"معهد: {inst.name}"
            except Exception:
                pass
            return f"معهد: {slug.replace('-', ' ').replace('_', ' ')}"
            
    # 4. Articles
    elif first == 'articles':
        if len(parts) == 1:
            return "مدونة المقالات"
        elif len(parts) >= 2:
            slug = parts[-1]
            try:
                Article = apps.get_model('articles', 'Article')
                art = Article.objects.filter(slug__in=[slug, unquote(slug)]).first()
                if art:
                    return f"مقال: {art.title}"
            except Exception:
                pass
            return f"مقال: {slug.replace('-', ' ').replace('_', ' ')}"
            
    # 5. Author
    elif first == 'author':
        slug = parts[-1]
        return f"صفحة الكاتب: {slug.replace('-', ' ')}"
        
    # 6. Legacy single-segment URLs (/<slug>/)
    if len(parts) == 1:
        slug = parts[0]
        slug_candidates = [slug, unquote(slug)]
        try:
            University = apps.get_model('universities', 'University')
            uni = University.objects.filter(slug__in=slug_candidates).first()
            if uni:
                return f"جامعة: {uni.name}"
        except Exception:
            pass
        try:
            Institute = apps.get_model('institutes', 'Institute')
            inst = Institute.objects.filter(slug__in=slug_candidates).first()
            if inst:
                return f"معهد: {inst.name}"
        except Exception:
            pass
        try:
            Major = apps.get_model('majors', 'Major')
            major = Major.objects.filter(slug__in=slug_candidates).first()
            if major:
                return f"تخصص: {major.name}"
        except Exception:
            pass
        try:
            Article = apps.get_model('articles', 'Article')
            art = Article.objects.filter(slug__in=slug_candidates).first()
            if art:
                return f"مقال: {art.title}"
        except Exception:
            pass
            
    # Fallback
    last_part = parts[-1]
    return last_part.replace('-', ' ').replace('_', ' ')


class LeadType(models.TextChoices):
    """Lead type choices."""
    REGISTRATION = 'registration', 'طلب تسجيل'
    CONTACT = 'contact', 'استفسار'


class LeadStatus(models.TextChoices):
    """Lead pipeline status choices."""
    NEW = 'new', 'جديد'
    CONTACTED = 'contacted', 'تم التواصل'
    IN_PROGRESS = 'in_progress', 'قيد المتابعة'
    REGISTERED = 'registered', 'تم التسجيل'
    CANCELLED = 'cancelled', 'ملغي / غير مهتم'



class Lead(TimestampedModel):
    """Lead model for storing form submissions."""
    lead_type = models.CharField(
        max_length=20,
        choices=LeadType.choices,
        verbose_name='نوع الرسالة',
        db_index=True
    )
    name = models.CharField(
        max_length=200,
        verbose_name='الاسم الكامل'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='البريد الإلكتروني'
    )
    phone = models.CharField(
        max_length=50,
        verbose_name='رقم الهاتف'
    )
    message = models.TextField(
        blank=True,
        null=True,
        verbose_name='محتوى الرسالة'
    )
    nationality = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='الجنسية'
    )
    institution_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='المؤسسة التعليمية',
        help_text='اسم الجامعة أو المعهد الذي تم التقديم عليه'
    )
    residence_country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='دولة الإقامة'
    )
    study_level = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='المرحلة الدراسية'
    )
    address = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name='عنوان الإقامة'
    )
    privacy_consent = models.BooleanField(
        default=False,
        verbose_name='موافقة سياسة الخصوصية'
    )
    privacy_consent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الموافقة على الخصوصية'
    )
    privacy_policy_version = models.CharField(
        max_length=20,
        default='1.0',
        blank=True,
        verbose_name='إصدار سياسة الخصوصية'
    )

    
    # Tracking fields (Expanded to 500 chars to avoid data truncation with Arabic encoded URLs)
    source_page = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='صفحة المصدر',
        help_text='الصفحة التي تم إرسال النموذج منها'
    )
    referrer = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='المصدر',
        help_text='رابط المصدر (HTTP Referrer)'
    )
    utm_source = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='مصدر الحملة (utm_source)',
        help_text='مثل: google, facebook, tiktok, instagram'
    )
    utm_medium = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='وسيط الحملة (utm_medium)',
        help_text='مثل: cpc, story, organic, direct'
    )
    utm_campaign = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='اسم الحملة (utm_campaign)'
    )
    utm_term = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='الكلمة المفتاحية (utm_term)'
    )
    utm_content = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='محتوى الإعلان (utm_content)'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='عنوان IP'
    )

    # Status fields
    status = models.CharField(
        max_length=30,
        choices=LeadStatus.choices,
        default=LeadStatus.NEW,
        verbose_name='حالة المتابعة',
        db_index=True
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='تم قراءتها',
        db_index=True
    )
    is_archived = models.BooleanField(
        default=False,
        verbose_name='مؤرشفة',
        db_index=True
    )
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات'
    )
    
    class Meta:
        verbose_name = 'رسالة'
        verbose_name_plural = 'الرسائل'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['lead_type']),
            models.Index(fields=['is_read']),
            models.Index(fields=['is_archived']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['lead_type', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
            models.Index(fields=['is_archived', 'lead_type', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.name} - {self.get_lead_type_display()}'
    
    def save(self, *args, **kwargs):
        """Normalize URL fields, enforce HTTPS, and auto-enrich entity data before saving."""
        if self.source_page:
            s_page = self.source_page.strip()
            if s_page.startswith('/'):
                base_site_url = getattr(settings, 'SITE_URL', 'https://sciencesgates.com').rstrip('/')
                s_page = f"{base_site_url}{s_page}"
            if s_page.startswith('http://sciencesgates.com'):
                s_page = s_page.replace('http://sciencesgates.com', 'https://sciencesgates.com', 1)
            elif s_page.startswith('http://www.sciencesgates.com'):
                s_page = s_page.replace('http://www.sciencesgates.com', 'https://sciencesgates.com', 1)
            self.source_page = s_page[:500]

        if self.referrer:
            self.referrer = self.referrer.strip()[:500]

        # Auto-enrich institution_name from detected entity if empty
        if not self.institution_name and self.source_page:
            try:
                decoded_url = unquote(self.source_page)
                parsed = urlparse(decoded_url)
                parts = [p for p in parsed.path.strip('/').split('/') if p]
                if len(parts) >= 2 and parts[0] == 'universities':
                    slug = parts[-1]
                    University = apps.get_model('universities', 'University')
                    uni = University.objects.filter(slug__in=[slug, unquote(slug)]).first()
                    if uni:
                        self.institution_name = uni.name
                elif len(parts) >= 2 and parts[0] == 'institutes':
                    slug = parts[-1]
                    Institute = apps.get_model('institutes', 'Institute')
                    inst = Institute.objects.filter(slug__in=[slug, unquote(slug)]).first()
                    if inst:
                        self.institution_name = inst.name
            except Exception:
                pass

        super().save(*args, **kwargs)

    def mark_as_read(self):
        """Mark lead as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])

    def archive(self):
        """Archive the lead."""
        self.is_archived = True
        self.save(update_fields=['is_archived'])

    def unarchive(self):
        """Unarchive the lead."""
        self.is_archived = False
        self.save(update_fields=['is_archived'])

    @property
    def source_page_decoded(self):
        """Returns the full unquoted Arabic URL for clean display."""
        if not self.source_page:
            return ""
        return unquote(self.source_page)

    @property
    def referrer_decoded(self):
        """Returns the full unquoted referrer URL."""
        if not self.referrer:
            return ""
        return unquote(self.referrer)

    @property
    def source_page_name(self):
        """Extract a readable page name or official entity name from source_page URL."""
        if not self.source_page:
            return ""
        try:
            decoded_url = unquote(self.source_page)
            parsed = urlparse(decoded_url)
            return resolve_entity_name_from_path(parsed.path, parsed.query)
        except Exception:
            return self.source_page_decoded or self.source_page

    @property
    def source_entity_short(self):
        """Short entity name or page name for email subject lines."""
        if self.institution_name:
            return self.institution_name
        name = self.source_page_name
        if name and name != "الصفحة الرئيسية":
            return name
        return ""

    @property
    def phone_clean(self):
        """Get the cleaned phone number for WhatsApp wa.me links, validating minimum length."""
        if not self.phone:
            return ""
        try:
            SiteSettings = apps.get_model('core', 'SiteSettings')
            cleaned = SiteSettings.clean_whatsapp_number(self.phone)
        except Exception:
            import re
            cleaned = re.sub(r'\D', '', str(self.phone))
            if cleaned.startswith('00'):
                cleaned = cleaned[2:]
        if len(cleaned) >= 8:
            return cleaned
        return ""

    @property
    def traffic_source_display(self):
        """Extract a readable marketing traffic source including decoded UTM campaign details."""
        # 1. Check UTM parameters first (highest fidelity marketing attribution)
        if self.utm_source:
            source_raw = unquote(self.utm_source).strip()
            source_lower = source_raw.lower()
            source_label_map = {
                'google': 'إعلان جوجل (Google Ads)',
                'facebook': 'إعلان فيسبوك (Facebook Ads)',
                'fb': 'إعلان فيسبوك (Facebook)',
                'instagram': 'إعلان إنستغرام (Instagram)',
                'ig': 'إعلان إنستغرام (Instagram)',
                'tiktok': 'إعلان تيك توك (TikTok)',
                'snapchat': 'إعلان سناب شات (Snapchat)',
                'twitter': 'إعلان تويتر (X/Twitter)',
                'youtube': 'إعلان يوتيوب (YouTube)',
                'linkedin': 'إعلان لينكد إن (LinkedIn)',
            }
            platform_name = source_label_map.get(source_lower, f"حملة: {source_raw}")
            
            details = []
            if self.utm_campaign:
                camp_clean = unquote(self.utm_campaign).strip().replace('-', ' ').replace('_', ' ')
                details.append(f"حملة: {camp_clean}")
            if self.utm_medium and self.utm_medium.lower() not in ('cpc', 'cpm', 'paid', 'ad'):
                med_clean = unquote(self.utm_medium).strip()
                details.append(f"وسيط: {med_clean}")
            if self.utm_content:
                cnt_clean = unquote(self.utm_content).strip()
                details.append(f"محتوى: {cnt_clean}")
                
            if details:
                return f"{platform_name} - ({' | '.join(details)})"
            return platform_name

        # 2. Check Referrer domain
        if not self.referrer:
            return "مباشر"
            
        try:
            parsed = urlparse(self.referrer)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Internal navigation is direct
            if not domain or domain in ('sciencesgates.com', 'localhost', '127.0.0.1', 'testserver'):
                return "مباشر"
                
            common_sources = {
                'google': 'بحث جوجل (Google)',
                'bing': 'بحث بينغ (Bing)',
                'yahoo': 'بحث ياهو (Yahoo)',
                'facebook.com': 'فيسبوك (Facebook)',
                'instagram.com': 'إنستغرام (Instagram)',
                'linkedin.com': 'لينكد إن (LinkedIn)',
                'twitter.com': 'تويتر (Twitter/X)',
                't.co': 'تويتر (Twitter/X)',
                'youtube.com': 'يوتيوب (YouTube)',
                'tiktok.com': 'تيك توك (TikTok)',
                'snapchat.com': 'سناب شات (Snapchat)',
                't.me': 'تيليجرام (Telegram)',
                'telegram.org': 'تيليجرام (Telegram)',
                'whatsapp.com': 'واتساب (WhatsApp)',
            }
            for key, val in common_sources.items():
                if key in domain:
                    return val
            return domain
        except Exception:
            return "مباشر"

    @property
    def is_direct_source(self):
        """Returns True if the traffic source is direct / internal with no external campaign/referrer."""
        return self.traffic_source_display == "مباشر"

    @property
    def referrer_name(self):
        """Legacy property alias for backward compatibility."""
        return self.traffic_source_display
