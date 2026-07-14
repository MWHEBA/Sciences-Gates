"""
University content models including University, Faculty, Program, and FAQ.
"""
from django.db import models
from django.urls import reverse
from apps.core.models import TimestampedModel, PublishableModel, SEOMixin


class University(TimestampedModel, PublishableModel, SEOMixin):
    """University content model."""
    UNIVERSITY_TYPE_CHOICES = [
        ('public', 'جامعة حكومية'),
        ('private', 'جامعة خاصة'),
    ]
    
    STATE_CHOICES = [
        ('kl', 'كوالالمبور'),
        ('selangor', 'سيلانجور'),
        ('penang', 'بينانج'),
        ('johor', 'جوهور'),
        ('kedah', 'قدح'),
        ('kelantan', 'كلنتان'),
        ('melaka', 'ملقا'),
        ('negeri-sembilan', 'نيجري سمبيلان'),
        ('pahang', 'باهانغ'),
        ('perak', 'بيرق'),
        ('perlis', 'برليس'),
        ('sabah', 'صباح'),
        ('sarawak', 'سراوق'),
        ('terengganu', 'ترينجانو'),
        ('putrajaya', 'بوتراجايا'),
        ('labuan', 'لابوان'),
    ]
    CITY_CHOICES = STATE_CHOICES

    STATE_CITIES = {
        'kl': [
            ('kl', 'كوالالمبور'),
        ],
        'selangor': [
            ('shah-alam', 'شاه علم'),
            ('petaling-jaya', 'بيتالينغ جايا'),
            ('klang', 'كلانغ'),
            ('subang-jaya', 'سوبانغ جايا'),
            ('ampang-jaya', 'أمبانغ جايا'),
            ('kajang', 'كاجanغ'),
            ('cyberjaya', 'سيبرجايا'),
            ('putrajaya', 'بوتراجايا'),
            ('rawang', 'راوانغ'),
            ('selayang', 'سيلايانغ'),
            ('bangi', 'بانغي'),
            ('kuala-selangor', 'كوالا سلانغور'),
            ('sungai-buloh', 'سونغاي بولوه'),
            # Keep existing mapped ones to avoid data errors
            ('serdang', 'سردانج'),
            ('semenyih', 'سيمينيه'),
            ('seri-kembangan', 'سري كيمبانجان'),
            ('sungai-long', 'سونغاي لونغ'),
            ('bandar-sunway', 'بندر صنواي'),
            ('damansara', 'دامانسارا'),
            ('gombak', 'غومباك'),
            ('saujana-putra', 'سوجانا بوترا'),
            ('jenjarom', 'جينجاروم'),
            ('other-selangor', 'سيلانجور (عام)'),
        ],
        'penang': [
            ('georgetown', 'جورج تاون'),
            ('bayan-lepas', 'بايان ليباس'),
            ('bukit-mertajam', 'بوكيت ميرتاجام'),
            ('butterworth', 'باتروورث'),
            ('nibong-tebal', 'نيبونغ تيبال'),
            ('perai', 'بيراي'),
            ('tanjung-bungah', 'تانجونغ بونغا'),
            ('ayer-itam', 'آير إيتام'),
            ('other-penang', 'بينانج (عام)'),
        ],
        'johor': [
            ('johor-bahru', 'جوهر بهرو'),
            ('iskandar-puteri', 'إسكندر بوتري'),
            ('pasir-gudang', 'باسير جودانغ'),
            ('kluang', 'كلوانغ'),
            ('muar', 'موار'),
            ('batu-pahat', 'باتو باهات'),
            ('segamat', 'سيغامات'),
            ('kulai', 'كولاي'),
            ('pontian', 'بونتيان'),
            ('kota-tinggi', 'كوتا تينجي'),
            ('mersing', 'ميرسينغ'),
            ('skudai', 'سكوداي'),
            ('other-johor', 'جوهور (عام)'),
        ],
        'kedah': [
            ('alor-setar', 'ألور ستار'),
            ('sungai-petani', 'سونغاي بيتاني'),
            ('kulim', 'كوليم'),
            ('langkawi', 'لانكاوي (كواه)'),
            ('baling', 'بالينغ'),
            ('kubang-pasu', 'كوبانغ باسو'),
            ('jitra', 'جترا'),
            ('yan', 'يان'),
            ('sik', 'سيك'),
            ('padang-terap', 'بادانغ تيراب'),
            ('sintok', 'سينتوت'),
            ('other-kedah', 'قدح (عام)'),
        ],
        'kelantan': [
            ('kota-bharu', 'كوتا بهارو'),
            ('bachok', 'باشوك'),
            ('tanah-merah', 'تاناه ميراه'),
            ('machang', 'ماتشانغ'),
            ('kuala-krai', 'كوالا كراي'),
            ('gua-musang', 'غوا موسانغ'),
            ('pasir-mas', 'باسير ماس'),
            ('pasir-puteh', 'باسير بوتيه'),
            ('tumpat', 'تومبات'),
            ('other-kelantan', 'كلنتان (عام)'),
        ],
        'melaka': [
            ('melaka', 'مدينة ملقا'),
            ('alor-gajah', 'ألور غاجاه'),
            ('jasin', 'جاسين'),
            ('masjid-tanah', 'ماسجيد تاناه'),
            ('merlimau', 'ميرليمو'),
            ('other-melaka', 'ملقا (عام)'),
        ],
        'negeri-sembilan': [
            ('seremban', 'سريمبان'),
            ('nilai', 'نيلاي'),
            ('port-dickson', 'بورت ديكسون'),
            ('bahau', 'باهاو'),
            ('rembau', 'رِمباو'),
            ('kuala-pilah', 'كوالا بيله'),
            ('tampin', 'تامبين'),
            ('jempol', 'جِمبول'),
            ('other-negeri-sembilan', 'نيجري سمبيلان (عام)'),
        ],
        'pahang': [
            ('kuantan', 'كوانتان'),
            ('temerloh', 'تيميرلوه'),
            ('bentong', 'بنتونغ'),
            ('cameron-highlands', 'كاميرون هايلاندز'),
            ('jerantut', 'جيرانتوت'),
            ('pekan', 'بيكان'),
            ('rompin', 'رومبين'),
            ('maran', 'ماران'),
            ('raub', 'راوب'),
            ('gambang', 'غامبانغ'),
            ('other-pahang', 'باهانغ (عام)'),
        ],
        'perak': [
            ('ipoh', 'إيبوه'),
            ('taiping', 'تايبينغ'),
            ('teluk-intan', 'تيلوك إنتان'),
            ('manjung', 'مانجونغ (سيتياوان)'),
            ('kampar', 'كامبار'),
            ('tapah', 'تاباه'),
            ('batu-gajah', 'باتو غاجاه'),
            ('kuala-kangsar', 'كوالا كانغسار'),
            ('lumut', 'لوموت'),
            ('tanjung-malim', 'تانجونغ ماليم'),
            ('seri-iskandar', 'سري اسكندر'),
            ('other-perak', 'بيرق (عام)'),
        ],
        'perlis': [
            ('kangar', 'كانغار'),
            ('arau', 'آراو'),
            ('padang-besar', 'بادانغ بيسار'),
            ('kuala-perlis', 'كوالا بيرليس'),
            ('other-perlis', 'برليس (عام)'),
        ],
        'sabah': [
            ('kota-kinabalu', 'كوتا كينابالو'),
            ('sandakan', 'سانداكان'),
            ('tawau', 'تاواو'),
            ('lahad-datu', 'لحد داتو'),
            ('keningau', 'كينينغاو'),
            ('kodat', 'كودات'),
            ('semporna', 'سيمبورنا'),
            ('ranau', 'راناو'),
            ('beaufort', 'بوفورت'),
            ('tenom', 'تنوم'),
            ('other-sabah', 'صباح (عام)'),
        ],
        'sarawak': [
            ('kuching', 'كوتشينغ'),
            ('miri', 'ميري'),
            ('sibu', 'سيبو'),
            ('bintulu', 'بينتولو'),
            ('sri-aman', 'سري أمان'),
            ('kapit', 'كابيت'),
            ('sarikei', 'سارايكي'),
            ('limbang', 'ليمبانغ'),
            ('betong', 'بيتونغ'),
            ('other-sarawak', 'سراوق (عام)'),
        ],
        'terengganu': [
            ('kuala-terengganu', 'كوالا ترينغانو'),
            ('kemaman', 'كيمان'),
            ('dungun', 'دونغون'),
            ('besut', 'بيسوت'),
            ('marang', 'مارانغ'),
            ('setiu', 'سيتيو'),
            ('hulu-terengganu', 'هولو ترينغانو'),
            ('other-terengganu', 'ترينجانو (عام)'),
        ],
        'putrajaya': [
            ('putrajaya', 'بوتراجايا'),
        ],
        'labuan': [
            ('victoria', 'فيكتوريا (بندر لابوان)'),
            ('labuan', 'لابوان'),
        ],
    }
    
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default='kl',
        verbose_name='الولاية',
        help_text='الولاية التي تقع بها الجامعة لتسهيل التصفية والبحث',
        db_index=True
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='المدينة',
        help_text='المدينة التي تقع بها الجامعة لتسهيل التصفية والبحث',
        db_index=True
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name='اسم الجامعة',
        db_index=True
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='الرابط',
        help_text='رابط الصفحة (يدعم الأحرف العربية)',
        allow_unicode=True
    )
    is_legacy = models.BooleanField(
        default=False,
        verbose_name='رابط قديم',
        help_text='تفعيل هذا الخيار سيجعل الرابط مباشراً بدون بادئة الفئة (مثال: /slug/ بدلاً من /universities/slug/)'
    )
    university_type = models.CharField(
        max_length=20,
        choices=UNIVERSITY_TYPE_CHOICES,
        default='private',
        verbose_name='نوع الجامعة',
        help_text='تصنيف الجامعة (حكومية أو خاصة)',
        db_index=True
    )
    logo = models.ImageField(
        upload_to='universities/logos/',
        verbose_name='شعار الجامعة',
        help_text='شعار الجامعة (PNG مع خلفية شفافة مفضل)'
    )
    logo_alt = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='النص البديل للشعار',
        help_text='النص البديل لشعار الجامعة (SEO)'
    )
    main_image = models.ImageField(
        upload_to='universities/images/',
        verbose_name='الصورة الرئيسية',
        help_text='صورة رئيسية للجامعة'
    )
    main_image_alt = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='النص البديل للصورة الرئيسية',
        help_text='النص البديل للصورة الرئيسية للجامعة (SEO)'
    )
    description = models.TextField(
        verbose_name='الوصف',
        help_text='وصف شامل عن الجامعة'
    )
    location = models.TextField(
        verbose_name='الموقع',
        help_text='موقع الجامعة (المدينة، الولاية)'
    )
    video_url = models.URLField(
        blank=True,
        verbose_name='رابط الفيديو',
    )
    telephone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='رقم الهاتف',
        help_text='رقم هاتف التواصل للجامعة لتسهيل التواصل والبحث المحلي'
    )
    website = models.URLField(
        blank=True,
        verbose_name='الموقع الرسمي للجامعة',
        help_text='رابط الموقع الإلكتروني الرسمي للجامعة (sameAs)'
    )
    admission_requirements = models.TextField(
        blank=True,
        default="",
        verbose_name='شروط القبول العامة / السابقة',
        help_text='شروط القبول العامة أو السابقة في الجامعة (أرشيف)'
    )
    admission_requirements_bachelor = models.TextField(
        blank=True,
        default="",
        verbose_name='شروط القبول للبكالوريوس (Bachelor’s)',
        help_text='شروط القبول الخاصة ببرنامج البكالوريوس'
    )
    admission_requirements_master = models.TextField(
        blank=True,
        default="",
        verbose_name='شروط القبول للماجستير (Master’s)',
        help_text='شروط القبول الخاصة ببرنامج الماجستير'
    )
    admission_requirements_phd = models.TextField(
        blank=True,
        default="",
        verbose_name='شروط القبول للدكتوراه (PhD)',
        help_text='شروط القبول الخاصة ببرنامج الدكتوراه'
    )
    one_time_fees = models.JSONField(
        default=list,
        blank=True,
        verbose_name='رسوم تدفع مرة واحدة',
        help_text='جداول الرسوم الإضافية التي تدفع مرة واحدة بصيغة JSON'
    )


    # Relationships
    related_majors = models.ManyToManyField(
        'majors.Major',
        blank=True,
        related_name='universities',
        verbose_name='التخصصات المرتبطة'
    )
    related_articles = models.ManyToManyField(
        'articles.Article',
        blank=True,
        related_name='universities',
        verbose_name='المقالات المرتبطة'
    )
    tags = models.ManyToManyField(
        'articles.Tag',
        blank=True,
        related_name='universities',
        verbose_name='الوسوم'
    )

    class Meta:
        verbose_name = 'جامعة'
        verbose_name_plural = 'الجامعات'
        ordering = ['name']
        indexes = [
            models.Index(fields=['publish_status']),
            models.Index(fields=['name']),
            models.Index(fields=['publish_status', 'name']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return the absolute URL for this university."""
        return reverse('universities:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Store old slug for redirect creation if slug changes."""
        if self.pk:
            old_instance = University.objects.get(pk=self.pk)
            if old_instance.slug != self.slug and old_instance.is_published:
                # Signal to create redirect (handled in dashboard)
                self._old_slug = old_instance.slug
        super().save(*args, **kwargs)

    def get_location_display(self):
        """Returns the formatted location display (e.g. 'Subang Jaya, Selangor' in Arabic)."""
        state_display = self.get_state_display()
        city_name = ""
        if self.state in self.STATE_CITIES:
            for c_slug, c_name in self.STATE_CITIES[self.state]:
                if c_slug == self.city:
                    city_name = c_name
                    break
        
        if city_name and city_name != state_display and "عام" not in city_name:
            return f"{city_name}، {state_display}"
        return state_display


class Faculty(models.Model):
    """Faculty within a university."""
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='faculties',
        verbose_name='الجامعة'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='اسم الكلية'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور الكلية (الأصغر أولاً)'
    )

    class Meta:
        verbose_name = 'كلية'
        verbose_name_plural = 'الكليات'
        ordering = ['sort_order', 'name']
        unique_together = ['university', 'name']

    def __str__(self):
        return f'{self.name} - {self.university.name}'


class Program(models.Model):
    """Program within a faculty."""
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='programs',
        verbose_name='الكلية'
    )
    major = models.ForeignKey(
        'majors.Major',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='programs',
        verbose_name='التخصص المرتبط',
        help_text='اختر التخصص العام المرتبط بهذا البرنامج (مثال: الوسائط المتعددة)'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='اسم البرنامج'
    )
    duration = models.CharField(
        max_length=100,
        verbose_name='مدة الدراسة',
        help_text='مثال: 4 سنوات'
    )
    tuition_fees = models.CharField(
        max_length=100,
        verbose_name='الرسوم الدراسية',
        help_text='مثال: 20,000 رنجت ماليزي سنوياً'
    )
    yearly_fees = models.JSONField(
        blank=True,
        null=True,
        verbose_name='الرسوم السنوية التفصيلية',
        help_text='رسوم كل سنة دراسية بشكل منفصل (اختياري). مثال: {"السنة الأولى": "5,424", "السنة الثانية": "4,964"}'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور البرنامج (الأصغر أولاً)'
    )


    class Meta:
        verbose_name = 'برنامج'
        verbose_name_plural = 'البرامج'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f'{self.name} - {self.faculty.name}'


class UniversityFAQ(models.Model):
    """FAQ entry for a university."""
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name='الجامعة'
    )
    question = models.CharField(
        max_length=300,
        verbose_name='السؤال'
    )
    answer = models.TextField(
        verbose_name='الإجابة'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض',
        help_text='ترتيب ظهور السؤال (الأصغر أولاً)'
    )

    class Meta:
        verbose_name = 'سؤال شائع'
        verbose_name_plural = 'الأسئلة الشائعة'
        ordering = ['sort_order']

    def __str__(self):
        return self.question


class UniversityAttachment(TimestampedModel):
    """File attachment for a university."""
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='الجامعة'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان الملف'
    )
    file = models.FileField(
        upload_to='universities/attachments/',
        verbose_name='الملف'
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name='حجم الملف (بايت)'
    )

    class Meta:
        verbose_name = 'ملف الجامعة'
        verbose_name_plural = 'ملفات الجامعة'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.university.name}'

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file:
            try:
                self.file.delete(save=False)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error deleting physical file for UniversityAttachment: {e}")
        super().delete(*args, **kwargs)

