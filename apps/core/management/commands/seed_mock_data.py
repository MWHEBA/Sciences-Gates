"""
Management command to seed the database with mock data.
Creates 3 Universities (with 5 faculties and 5 FAQs each), 3 Majors (with 5 rows per table), 3 Institutes, and 3 Articles.
"""
import io
import os
from PIL import Image, ImageDraw
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from apps.universities.models import University, Faculty, Program, UniversityFAQ
from apps.majors.models import Major, SubjectsTable, SalaryTable, CountriesTable
from apps.institutes.models import Institute, Course
from apps.articles.models import Article, Category, Tag
from apps.core.models import PublishStatus


class Command(BaseCommand):
    help = 'Seeds the database with high-quality mock data for testing'

    def add_arguments(self, parser):
        # إضافة خيار لمسح البيانات القديمة قبل الإضافة الجديدة
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing mock data before seeding',
        )

    def create_dummy_image(self, name, color='blue', width=800, height=600):
        # ميثود لإنشاء صورة تجريبية في الذاكرة وحفظها كملف دجانغو
        img = Image.new('RGB', (width, height), color=color)
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        return ContentFile(img_io.getvalue(), name=name)

    def create_stylized_logo(self, name, abbreviation, bg_color):
        # إنشاء لوجو مبسط وأنيق باستخدام مكتبة PIL
        img = Image.new('RGB', (200, 200), color=bg_color)
        draw = ImageDraw.Draw(img)
        # رسم دائرة حدودية بيضاء
        draw.ellipse([20, 20, 180, 180], outline="white", width=4)
        # كتابة اختصار اسم الجامعة أو المعهد في المنتصف
        try:
            draw.text((100, 100), abbreviation, fill="white", anchor="mm", font_size=60)
        except Exception:
            # طريقة بديلة لو مفيش دعم للـ anchor في الخطوط الافتراضية
            draw.text((70, 85), abbreviation, fill="white")
            
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        return ContentFile(img_io.getvalue(), name=name)

    def load_generated_image(self, path, default_color='blue', default_name='default.png'):
        # تحميل الصور اللي تم توليدها بالذكاء الاصطناعي من الجهاز لو موجودة
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    return ContentFile(f.read(), name=os.path.basename(path))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'خطأ أثناء تحميل الصورة {path}: {str(e)}'))
        # لو الملف مش موجود هنرجع صورة ملونة افتراضية كـ fallback
        return self.create_dummy_image(default_name, default_color)

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('بدء عملية حقن البيانات التجريبية الموسعة...'))

        # مسارات الصور المخصصة التي ولدناها
        uni_campus_path = r"C:\Users\MohYousif\.gemini\antigravity-ide\brain\6c174246-eb91-4e3a-a6c0-c54a18fdf00b\university_campus_1780243035011.png"
        se_path = r"C:\Users\MohYousif\.gemini\antigravity-ide\brain\6c174246-eb91-4e3a-a6c0-c54a18fdf00b\software_engineering_1780243049608.png"
        meeting_path = r"C:\Users\MohYousif\.gemini\antigravity-ide\brain\6c174246-eb91-4e3a-a6c0-c54a18fdf00b\business_meeting_1780243073353.png"
        classroom_path = r"C:\Users\MohYousif\.gemini\antigravity-ide\brain\6c174246-eb91-4e3a-a6c0-c54a18fdf00b\language_classroom_1780243088409.png"
        studying_path = r"C:\Users\MohYousif\.gemini\antigravity-ide\brain\6c174246-eb91-4e3a-a6c0-c54a18fdf00b\student_studying_1780243102831.png"

        # 1. مسح البيانات القديمة لو المستخدم حدد خيار --clean
        if options['clean']:
            self.stdout.write(self.style.WARNING('تنظيف البيانات القديمة...'))
            
            mock_uni_slugs = ['global-city-university', 'elite-tech-university', 'national-malaysian-university']
            mock_major_slugs = ['software-engineering', 'artificial-intelligence', 'international-business']
            mock_inst_slugs = ['modern-languages-institute', 'high-technical-institute', 'leadership-development-institute']
            mock_article_slugs = ['study-abroad-guide', 'demanded-majors-2026', 'choosing-right-university']

            University.objects.filter(slug__in=mock_uni_slugs).delete()
            Major.objects.filter(slug__in=mock_major_slugs).delete()
            Institute.objects.filter(slug__in=mock_inst_slugs).delete()
            Article.objects.filter(slug__in=mock_article_slugs).delete()
            
            Category.objects.filter(slug__in=['study-languages', 'career-guidance', 'university-admissions']).delete()
            Tag.objects.filter(slug__in=['malaysia', 'tips', 'programming']).delete()

            self.stdout.write(self.style.SUCCESS('تم تنظيف البيانات القديمة بنجاح!'))

        # 2. الحصول على الكاتب (Author) أو إنشاؤه
        author = User.objects.filter(is_superuser=True).first()
        if not author:
            self.stdout.write('لم يتم العثور على مدير للنظام، جاري إنشاء مستخدم admin...')
            author = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('تم إنشاء مستخدم admin (الباسورد: admin123)'))

        # 3. إنشاء التصنيفات والوسوم للمقالات
        self.stdout.write('جاري إنشاء التصنيفات والوسوم...')
        cat_languages, _ = Category.objects.get_or_create(
            slug='study-languages',
            defaults={'name': 'دراسة اللغات', 'description': 'كل ما يخص دراسة اللغات والتحضير للاختبارات الدولية'}
        )
        cat_career, _ = Category.objects.get_or_create(
            slug='career-guidance',
            defaults={'name': 'التوجيه المهني', 'description': 'نصائح لاختيار التخصص المناسب وربطه بسوق العمل'}
        )
        cat_admissions, _ = Category.objects.get_or_create(
            slug='university-admissions',
            defaults={'name': 'القبولات الجامعية', 'description': 'دليلك للحصول على القبول الجامعي وخطوات التسجيل'}
        )

        tag_malaysia, _ = Tag.objects.get_or_create(slug='malaysia', defaults={'name': 'ماليزيا'})
        tag_tips, _ = Tag.objects.get_or_create(slug='tips', defaults={'name': 'نصائح'})
        tag_programming, _ = Tag.objects.get_or_create(slug='programming', defaults={'name': 'برمجة'})

        # 4. إنشاء التخصصات (3 تخصصات وكل جدول 5 صفوف)
        self.stdout.write('جاري إنشاء التخصصات والجداول (لا تقل عن 5 صفوف لكل جدول)...')
        
        # التخصص الأول: هندسة البرمجيات
        major_se, se_created = Major.objects.get_or_create(
            slug='software-engineering',
            defaults={
                'name': 'هندسة البرمجيات',
                'major_category': 'cs',
                'main_image': self.load_generated_image(se_path, '#0f766e', 'se_main.jpg'),
                'description': 'يركز هذا التخصص على تصميم وتطوير النظم البرمجية المعقدة بأساليب هندسية تضمن الجودة والكفاءة والفعالية.',
                'study_duration': '4 سنوات',
                'bachelor_duration': '4 سنوات',
                'master_duration': 'سنتان',
                'phd_duration': '3 سنوات',
                'tuition_fees': '12,000 - 18,000 رنجت سنوياً',
                'study_language': 'الإنجليزية',
                'practical_training': 'متاح وإلزامي في الفصل الدراسي الأخير',
                'career_opportunities': 'مطور برمجيات، مهندس جودة البرمجيات، أخصائي أمن معلومات، مدير مشاريع تقنية',
                'why_study_section': 'لأن البرمجيات تشكل عصب الحياة الحديثة وتعتبر من أكثر الوظائف طلباً وأعلاها أجوراً عالمياً.',
                'how_to_apply_section': 'تقديم شهادة الثانوية العامة (علمي) بمعدل مناسب وإثبات كفاءة اللغة الإنجليزية.',
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'دراسة هندسة البرمجيات في الخارج | الدليل الكامل',
                'meta_description': 'تعرف على تفاصيل دراسة تخصص هندسة البرمجيات، الرسوم الدراسية، المواد، ومجالات العمل بعد التخرج.',
                'focus_keyword': 'هندسة البرمجيات'
            }
        )
        if se_created:
            # 5 صفوف في جدول المواد
            SubjectsTable.objects.create(major=major_se, academic_year='السنة الأولى', subjects='مقدمة في البرمجة (C++)، رياضيات الحاسوب، تصميم المواقع الإلكترونية، مهارات الاتصال والتواصل', sort_order=1)
            SubjectsTable.objects.create(major=major_se, academic_year='السنة الثانية', subjects='هياكل البيانات والخوارزميات، البرمجة كائنية التوجه (Java)، نظم قواعد البيانات، هندسة البرمجيات 1', sort_order=2)
            SubjectsTable.objects.create(major=major_se, academic_year='السنة الثالثة', subjects='تصميم وبنية البرمجيات، شبكات الحاسوب، اختبار البرمجيات وضمان الجودة، إدارة مشاريع برمجية', sort_order=3)
            SubjectsTable.objects.create(major=major_se, academic_year='السنة الرابعة', subjects='تطوير تطبيقات الهواتف الذكية، الحوسبة السحابية، أمن المعلومات، مشروع التخرج 1', sort_order=4)
            SubjectsTable.objects.create(major=major_se, academic_year='المساقات الاختيارية والتدريب', subjects='تفاعل الإنسان والحاسوب، هندسة متطلبات البرمجيات، الذكاء الاصطناعي، التدريب العملي الميداني', sort_order=5)
            
            # 5 صفوف في جدول الرواتب
            SalaryTable.objects.create(major=major_se, job_title='مطور برمجيات مبتدئ (Junior Web/Mobile Developer)', average_monthly_salary='4,000 - 6,000 رنجت ماليزي', sort_order=1)
            SalaryTable.objects.create(major=major_se, job_title='مهندس برمجيات متوسط (Mid-Level Software Engineer)', average_monthly_salary='6,500 - 8,500 رنجت ماليزي', sort_order=2)
            SalaryTable.objects.create(major=major_se, job_title='مهندس برمجيات أول (Senior Software Engineer)', average_monthly_salary='9,000 - 15,000 رنجت ماليزي', sort_order=3)
            SalaryTable.objects.create(major=major_se, job_title='معماري برمجيات (Software Architect)', average_monthly_salary='16,000 - 22,000 رنجت ماليزي', sort_order=4)
            SalaryTable.objects.create(major=major_se, job_title='مدير تكنولوجيا المعلومات (CTO / IT Director)', average_monthly_salary='25,000+ رنجت ماليزي', sort_order=5)
            
            # 5 صفوف في جدول الدول
            CountriesTable.objects.create(major=major_se, destination='ماليزيا', study_duration='3.5 - 4 سنوات', annual_fees='15,000 - 25,000 رنجت', living_cost='1,500 - 2,500 رنجت شهرياً', sort_order=1)
            CountriesTable.objects.create(major=major_se, destination='تركيا', study_duration='4 سنوات', annual_fees='3,000 - 6,000 دولار', living_cost='400 - 600 دولار شهرياً', sort_order=2)
            CountriesTable.objects.create(major=major_se, destination='بريطانيا', study_duration='3 سنوات', annual_fees='18,000 - 28,000 جنيه إسترليني', living_cost='1,000 - 1,500 جنيه شهرياً', sort_order=3)
            CountriesTable.objects.create(major=major_se, destination='ألمانيا', study_duration='3 سنوات', annual_fees='مجانية (رسوم إدارية 300 يورو)', living_cost='934 يورو شهرياً', sort_order=4)
            CountriesTable.objects.create(major=major_se, destination='كندا', study_duration='4 سنوات', annual_fees='22,000 - 35,000 دولار كندي', living_cost='1,200 - 1,800 دولار كندي شهرياً', sort_order=5)

        # التخصص الثاني: الذكاء الاصطناعي
        major_ai, ai_created = Major.objects.get_or_create(
            slug='artificial-intelligence',
            defaults={
                'name': 'الذكاء الاصطناعي',
                'major_category': 'cs',
                'main_image': self.load_generated_image(se_path, '#6b21a8', 'ai_main.jpg'),
                'description': 'تخصص يركز على تزويد الآلات والبرمجيات بالقدرة على التفكير الذاتي، التعلم، اتخاذ القرارات وحل المشكلات.',
                'study_duration': '4 سنوات',
                'bachelor_duration': '4 سنوات',
                'master_duration': 'سنتان',
                'phd_duration': '3-4 سنوات',
                'tuition_fees': '15,000 - 22,000 رنجت سنوياً',
                'study_language': 'الإنجليزية',
                'practical_training': 'مشاريع عملية مكثفة طوال سنوات الدراسة',
                'career_opportunities': 'مهندس تعلم آلة، مهندس رؤية حاسوبية، محلل بيانات ضخمة، باحث في الذكاء الاصطناعي',
                'why_study_section': 'يمثل الذكاء الاصطناعي الثورة التكنولوجية القادمة وله تأثير متسارع في كافة قطاعات العمل والتصنيع.',
                'how_to_apply_section': 'يتطلب خلفية ممتازة في الرياضيات والإحصاء بالإضافة إلى شهادة الثانوية العامة.',
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'تخصص الذكاء الاصطناعي ومستقبله المهني',
                'meta_description': 'كل ما تريد معرفته عن تخصص الذكاء الاصطناعي، شروط القبول ومواد الدراسة وفرص العمل المتاحة.',
                'focus_keyword': 'الذكاء الاصطناعي'
            }
        )
        if ai_created:
            # 5 صفوف في جدول المواد
            SubjectsTable.objects.create(major=major_ai, academic_year='السنة الأولى', subjects='أسس البرمجة بلغة Python، جبر خطي وتفاضل، مبادئ الذكاء الاصطناعي، إحصاء واحتمالات', sort_order=1)
            SubjectsTable.objects.create(major=major_ai, academic_year='السنة الثانية', subjects='تعلم الآلة (Machine Learning)، هياكل البيانات، قواعد البيانات غير الهيكلية، معالجة الصور الرقمية', sort_order=2)
            SubjectsTable.objects.create(major=major_ai, academic_year='السنة الثالثة', subjects='التعلم العميق (Deep Learning)، الشبكات العصبية الاصطناعية، معالجة اللغات الطبيعية، الروبوتات', sort_order=3)
            SubjectsTable.objects.create(major=major_ai, academic_year='السنة الرابعة', subjects='تطبيقات الذكاء الاصطناعي في الصناعة، أخلاقيات الذكاء الاصطناعي، مشروع التخرج، تحليل البيانات الضخمة', sort_order=4)
            SubjectsTable.objects.create(major=major_ai, academic_year='المساقات الاختيارية والبحث العلمي', subjects='الحوسبة الإدراكية، التعرف على الأنماط، أمن نظم الذكاء الاصطناعي، التدريب الميداني المهني', sort_order=5)
            
            # 5 صفوف في جدول الرواتب
            SalaryTable.objects.create(major=major_ai, job_title='مساعد باحث في الذكاء الاصطناعي (AI Research Assistant)', average_monthly_salary='4,500 - 6,500 رنجت ماليزي', sort_order=1)
            SalaryTable.objects.create(major=major_ai, job_title='مهندس تعلم آلة (ML Engineer)', average_monthly_salary='6,500 - 10,000 رنجت ماليزي', sort_order=2)
            SalaryTable.objects.create(major=major_ai, job_title='عالم بيانات (Data Scientist)', average_monthly_salary='8,000 - 14,000 رنجت ماليزي', sort_order=3)
            SalaryTable.objects.create(major=major_ai, job_title='أخصائي رؤية حاسوبية (Computer Vision Specialist)', average_monthly_salary='10,000 - 16,000 رنجت ماليزي', sort_order=4)
            SalaryTable.objects.create(major=major_ai, job_title='مدير قسم الذكاء الاصطناعي (Head of AI / AI Director)', average_monthly_salary='22,000+ رنجت ماليزي', sort_order=5)
            
            # 5 صفوف في جدول الدول
            CountriesTable.objects.create(major=major_ai, destination='ماليزيا', study_duration='4 سنوات', annual_fees='18,000 - 28,000 رنجت', living_cost='1,500 - 2,500 رنجت شهرياً', sort_order=1)
            CountriesTable.objects.create(major=major_ai, destination='تركيا', study_duration='4 سنوات', annual_fees='4,000 - 8,000 دولار', living_cost='400 - 600 دولار شهرياً', sort_order=2)
            CountriesTable.objects.create(major=major_ai, destination='بريطانيا', study_duration='3 سنوات', annual_fees='20,000 - 32,000 جنيه إسترليني', living_cost='1,000 - 1,500 جنيه شهرياً', sort_order=3)
            CountriesTable.objects.create(major=major_ai, destination='ألمانيا', study_duration='3 سنوات', annual_fees='رسوم إدارية بسيطة', living_cost='934 يورو شهرياً', sort_order=4)
            CountriesTable.objects.create(major=major_ai, destination='الولايات المتحدة', study_duration='4 سنوات', annual_fees='28,000 - 45,000 دولار', living_cost='1,500 - 2,500 دولار شهرياً', sort_order=5)

        # التخصص الثالث: إدارة الأعمال الدولية
        major_ib, ib_created = Major.objects.get_or_create(
            slug='international-business',
            defaults={
                'name': 'إدارة الأعمال الدولية',
                'major_category': 'business',
                'main_image': self.load_generated_image(meeting_path, '#1e3a8a', 'ib_main.jpg'),
                'description': 'دراسة كيفية إدارة المؤسسات والشركات التي تعمل على نطاق عالمي، مع فهم الفروق الاقتصادية والثقافية والتشريعية بين الدول.',
                'study_duration': '3 سنوات',
                'bachelor_duration': '3 سنوات',
                'master_duration': 'سنة ونصف',
                'phd_duration': '3 سنوات',
                'tuition_fees': '10,000 - 15,000 رنجت سنوياً',
                'study_language': 'الإنجليزية',
                'practical_training': 'تدريب ميداني في إحدى الشركات متعددة الجنسيات لـ 3 أشهر',
                'career_opportunities': 'أخصائي استيراد وتصدير، مستشار أعمال دولية، مدير تسويق عالمي، محلل أسواق خارجية',
                'why_study_section': 'مع تسارع وتيرة العولمة، تبحث جميع الشركات عن كفاءات قادرة على إدارة الأعمال العابرة للحدود بكفاءة.',
                'how_to_apply_section': 'تقديم شهادة الثانوية العامة (أدبي أو علمي) وإجادة اللغة الإنجليزية.',
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'دراسة إدارة الأعمال الدولية بالتفصيل',
                'meta_description': 'تعرف على مميزات ومستقبل تخصص إدارة الأعمال الدولية والرسوم الدراسية وفرص العمل والتدريب.',
                'focus_keyword': 'إدارة الأعمال الدولية'
            }
        )
        if ib_created:
            # 5 صفوف في جدول المواد
            SubjectsTable.objects.create(major=major_ib, academic_year='السنة الأولى', subjects='مبادئ الإدارة، الاقتصاد الجزئي، مبادئ المحاسبة والمالية، سلوك تنظيمي وعلاقات عمل', sort_order=1)
            SubjectsTable.objects.create(major=major_ib, academic_year='السنة الثانية', subjects='التسويق الدولي، إدارة سلاسل الإمداد العالمية، الاقتصاد الكلي، إدارة الموارد البشرية الدولية', sort_order=2)
            SubjectsTable.objects.create(major=major_ib, academic_year='السنة الثالثة', subjects='التمويل الدولي، استراتيجيات الأعمال العالمية، التجارة الإلكترونية، قانون الأعمال الدولي', sort_order=3)
            SubjectsTable.objects.create(major=major_ib, academic_year='السنة الرابعة / فصول متقدمة', subjects='إدارة المخاطر في الأسواق الناشئة، الاتصال والذكاء الثقافي، ريادة الأعمال الدولية', sort_order=4)
            SubjectsTable.objects.create(major=major_ib, academic_year='المساقات الاختيارية والمشروع', subjects='التسويق الرقمي، إدارة الجودة الشاملة، مشروع التخرج، التدريب العملي الميداني', sort_order=5)
            
            # 5 صفوف في جدول الرواتب
            SalaryTable.objects.create(major=major_ib, job_title='محلل أعمال مبتدئ (Junior Business Analyst)', average_monthly_salary='3,500 - 5,000 رنجت ماليزي', sort_order=1)
            SalaryTable.objects.create(major=major_ib, job_title='أخصائي تطوير أعمال (Business Development Specialist)', average_monthly_salary='5,000 - 8,000 رنجت ماليزي', sort_order=2)
            SalaryTable.objects.create(major=major_ib, job_title='منسق استيراد وتصدير (Export/Import Coordinator)', average_monthly_salary='6,000 - 9,000 رنجت ماليزي', sort_order=3)
            SalaryTable.objects.create(major=major_ib, job_title='مدير مبيعات دولية (International Sales Manager)', average_monthly_salary='10,000 - 16,000 رنجت ماليزي', sort_order=4)
            SalaryTable.objects.create(major=major_ib, job_title='مدير العمليات العالمية (Global Operations Director)', average_monthly_salary='20,000+ رنجت ماليزي', sort_order=5)
            
            # 5 صفوف في جدول الدول
            CountriesTable.objects.create(major=major_ib, destination='ماليزيا', study_duration='3 سنوات', annual_fees='12,000 - 20,000 رنجت', living_cost='1,500 - 2,500 رنجت شهرياً', sort_order=1)
            CountriesTable.objects.create(major=major_ib, destination='تركيا', study_duration='4 سنوات', annual_fees='2,500 - 5,000 دولار', living_cost='400 - 600 دولار شهرياً', sort_order=2)
            CountriesTable.objects.create(major=major_ib, destination='بريطانيا', study_duration='3 سنوات', annual_fees='16,000 - 26,000 جنيه إسترليني', living_cost='1,000 - 1,500 جنيه شهرياً', sort_order=3)
            CountriesTable.objects.create(major=major_ib, destination='ألمانيا', study_duration='3 سنوات', annual_fees='شبه مجانية (300 يورو للفصل)', living_cost='934 يورو شهرياً', sort_order=4)
            CountriesTable.objects.create(major=major_ib, destination='أستراليا', study_duration='3 سنوات', annual_fees='24,000 - 36,000 دولار أسترالي', living_cost='1,400 - 2,000 دولار أسترالي شهرياً', sort_order=5)

        self.stdout.write(self.style.SUCCESS('تم إنشاء التخصصات بنجاح وجداولها لا تقل عن 5 صفوف!'))

        # 5. إنشاء الجامعات (3 جامعات وكل جامعة 5 كليات و 5 FAQs)
        self.stdout.write('جاري إنشاء الجامعات (5 كليات و 5 أسئلة شائعة لكل جامعة)...')
        
        # الجامعة الأولى: جامعة المدينة العالمية
        uni_global, global_created = University.objects.get_or_create(
            slug='global-city-university',
            defaults={
                'name': 'جامعة المدينة العالمية',
                'university_type': 'private',
                'logo': self.create_stylized_logo('global_logo.png', 'MEDIU', '#0d9488'),
                'main_image': self.load_generated_image(uni_campus_path, '#115e59', 'global_main.jpg'),
                'description': 'جامعة المدينة العالمية هي مؤسسة أكاديمية رائدة مسجلة في وزارة التعليم العالي الماليزية، وتقدم مجموعة واسعة من التخصصات التقنية والإدارية بنظامي التعليم الحضوري والتعليم الافتراضي عبر الإنترنت.',
                'location': 'كوالالمبور، ماليزيا',
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'admission_requirements': 'تشمل شروط القبول العامة الحصول على شهادة الثانوية العامة أو ما يعادلها مصدقة ومترجمة إلى الإنجليزية.',
                'admission_requirements_bachelor': 'الحصول على الثانوية العامة بمعدل لا يقل عن 60%، وشهادة كفاءة باللغة الإنجليزية (آيلتس 5.0) أو ما يعادلها.',
                'admission_requirements_master': 'شهادة البكالوريوس بتقدير جيد فما فوق في تخصص ذي صلة من جامعة معترف بها.',
                'admission_requirements_phd': 'شهادة الماجستير في نفس المجال مع تقديم مقترح بحثي معتمد وخوض المقابلة الأكاديمية.',
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'جامعة المدينة العالمية بماليزيا | التخصصات والرسوم',
                'meta_description': 'كل التفاصيل عن جامعة المدينة العالمية في كوالالمبور، التخصصات المتاحة، الرسوم السنوية وشروط التسجيل للطلاب العرب.',
                'focus_keyword': 'جامعة المدينة العالمية'
            }
        )
        if global_created:
            # 5 كليات للجامعة الأولى
            fac1 = Faculty.objects.create(university=uni_global, name='كلية الحاسبات وتكنولوجيا المعلومات', sort_order=1)
            fac2 = Faculty.objects.create(university=uni_global, name='كلية العلوم الإدارية والمالية', sort_order=2)
            fac3 = Faculty.objects.create(university=uni_global, name='كلية اللغات والدراسات الإنسانية', sort_order=3)
            fac4 = Faculty.objects.create(university=uni_global, name='كلية العلوم التربوية', sort_order=4)
            fac5 = Faculty.objects.create(university=uni_global, name='كلية الهندسة والتقنيات التطبيقية', sort_order=5)
            
            # 5 برامج دراسية لكل كلية بالجامعة الأولى
            fac1_programs = [
                ("بكالوريوس علوم الحاسوب (تطوير البرمجيات)", "3 سنوات", "15,000 رنجت سنوياً"),
                ("بكالوريوس تقنية المعلومات (شبكات النظم)", "3 سنوات", "14,500 رنجت سنوياً"),
                ("بكالوريوس نظم المعلومات الإدارية", "3 سنوات", "13,000 رنجت سنوياً"),
                ("ماجستير علوم الحاسوب المتقدمة", "سنتان", "18,000 رنجت سنوياً"),
                ("دبلوم تقنية المعلومات التطبيقي", "سنتان", "9,000 رنجت سنوياً"),
            ]
            fac2_programs = [
                ("بكالوريوس إدارة الأعمال الدولية", "3 سنوات", "12,000 رنجت سنوياً"),
                ("بكالوريوس المحاسبة والتمويل الدولي", "3 سنوات", "12,500 رنجت سنوياً"),
                ("بكالوريوس التسويق الرقمي", "3 سنوات", "11,500 رنجت سنوياً"),
                ("ماجستير إدارة الأعمال (MBA)", "سنة ونصف", "16,000 رنجت سنوياً"),
                ("بكالوريوس إدارة الموارد البشرية", "3 سنوات", "11,000 رنجت سنوياً"),
            ]
            fac3_programs = [
                ("بكالوريوس اللغة الإنجليزية وآدابها", "3 سنوات", "10,000 رنجت سنوياً"),
                ("بكالوريوس الترجمة الفورية والتحريرية", "3 سنوات", "11,000 رنجت سنوياً"),
                ("بكالوريوس اللغة العربية للناطقين بغيرها", "3 سنوات", "9,000 رنجت سنوياً"),
                ("ماجستير اللغويات التطبيقية", "سنتان", "13,000 رنجت سنوياً"),
                ("بكالوريوس الاتصال الجماهيري والإعلام", "3 سنوات", "10,500 رنجت سنوياً"),
            ]
            fac4_programs = [
                ("بكالوريوس طرق التدريس والمناهج الدراسية", "3 سنوات", "9,500 رنجت سنوياً"),
                ("بكالوريوس التربية الخاصة", "3 سنوات", "10,000 رنجت سنوياً"),
                ("بكالوريوس إدارة المؤسسات التعليمية", "3 سنوات", "10,500 رنجت سنوياً"),
                ("ماجستير أصول التربية", "سنتان", "12,000 رنجت سنوياً"),
                ("دبلوم التأهيل التربوي العالي", "سنة واحدة", "6,500 رنجت سنوياً"),
            ]
            fac5_programs = [
                ("بكالوريوس هندسة النظم الذكية", "4 سنوات", "18,000 رنجت سنوياً"),
                ("بكالوريوس الهندسة الكهربائية والإلكترونية", "4 سنوات", "17,500 رنجت سنوياً"),
                ("بكالوريوس هندسة الاتصالات والشبكات", "4 سنوات", "17,000 رنجت سنوياً"),
                ("ماجستير الإدارة الهندسية", "سنتان", "20,000 رنجت سنوياً"),
                ("بكالوريوس التقنيات الميكانيكية التطبيقية", "3 سنوات", "15,000 رنجت سنوياً"),
            ]

            for i, (name, dur, fees) in enumerate(fac1_programs):
                Program.objects.create(faculty=fac1, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac2_programs):
                Program.objects.create(faculty=fac2, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac3_programs):
                Program.objects.create(faculty=fac3, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac4_programs):
                Program.objects.create(faculty=fac4, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac5_programs):
                Program.objects.create(faculty=fac5, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            
            # 5 أسئلة شائعة للجامعة الأولى
            UniversityFAQ.objects.create(university=uni_global, question='هل الدراسة في جامعة المدينة حضورية بالكامل أم يمكن الدراسة عن بعد؟', answer='توفر الجامعة الخيارين؛ حيث يمكن للطلاب الدراسة حضورياً في الحرم الجامعي بكوالالمبور، أو اختيار نظام التعليم الافتراضي لبعض البرامج المعتمدة.', sort_order=1)
            UniversityFAQ.objects.create(university=uni_global, question='هل شهادة الجامعة معترف بها دولياً؟', answer='نعم، جميع برامج الجامعة معتمدة من هيئة الاعتماد الأكاديمي الماليزية (MQA) ومعترف بها في وزارات التعليم العالي بمختلف الدول العربية.', sort_order=2)
            UniversityFAQ.objects.create(university=uni_global, question='ما هي شروط التقديم لبرامج البكالوريوس؟', answer='الحصول على الثانوية العامة بمعدل لا يقل عن 60% وإثبات كفاءة اللغة الإنجليزية (آيلتس 5.0) أو ما يعادلها.', sort_order=3)
            UniversityFAQ.objects.create(university=uni_global, question='هل توفر الجامعة سكن طلابي؟', answer='نعم، توفر الجامعة خيارات سكن متعددة قريبة من الحرم الجامعي ومجهزة بكافة الخدمات الأساسية وبأسعار مناسبة.', sort_order=4)
            UniversityFAQ.objects.create(university=uni_global, question='ما هي لغة التدريس الأساسية بالجامعة؟', answer='لغة التدريس الأساسية لمعظم التخصصات العلمية والتقنية والإدارية هي اللغة الإنجليزية.', sort_order=5)

        # الجامعة الثانية: جامعة النخبة للتكنولوجيا
        uni_elite, elite_created = University.objects.get_or_create(
            slug='elite-tech-university',
            defaults={
                'name': 'جامعة النخبة للتكنولوجيا',
                'university_type': 'private',
                'logo': self.create_stylized_logo('elite_logo.png', 'ELITE', '#7e22ce'),
                'main_image': self.load_generated_image(se_path, '#581c87', 'elite_main.jpg'), # صورة البرمجة مناسبة لجامعة تكنولوجيا
                'description': 'جامعة النخبة للتكنولوجيا هي جامعة متخصصة في العلوم التقنية المتقدمة وتطبيقات الهندسة الحديثة، وتتميز بارتباطاتها القوية مع كبرى شركات التكنولوجيا في وادي السيليكون ومختلف قطاعات الصناعة.',
                'location': 'سلاغور، ماليزيا',
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'admission_requirements': 'يجب على جميع المتقدمين تقديم المستندات الرسمية واجتياز اختبار القدرات الرياضية والتحليلية بالجامعة.',
                'admission_requirements_bachelor': 'شهادة الثانوية العامة (الفرع العلمي) بمعدل 70% كحد أدنى، وآيلتس 5.5 أو اجتياز سنة تمهيدية لغة.',
                'admission_requirements_master': 'بكالوريوس في علوم الحاسوب أو الهندسة مع معدل تراكمي 2.75/4.00 أو خبرة عملية مناسبة.',
                'admission_requirements_phd': 'ماجستير بحثي أو بمعدل مرتفع مع تقديم ورقة علمية منشورة سابقة أو خطة بحث متميزة.',
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'جامعة النخبة للتكنولوجيا | تخصصات المستقبل والذكاء الاصطناعي',
                'meta_description': 'ادرس تخصصات المستقبل والهندسة والذكاء الاصطناعي في جامعة النخبة الماليزية المرموقة. التفاصيل والقبولات هنا.',
                'focus_keyword': 'جامعة النخبة للتكنولوجيا'
            }
        )
        if elite_created:
            # 5 كليات للجامعة الثانية
            fac1 = Faculty.objects.create(university=uni_elite, name='كلية الذكاء الاصطناعي والروبوتات', sort_order=1)
            fac2 = Faculty.objects.create(university=uni_elite, name='كلية الهندسة والبيئة المبنية', sort_order=2)
            fac3 = Faculty.objects.create(university=uni_elite, name='كلية الأمن السيبراني وعلم الجريمة الرقمية', sort_order=3)
            fac4 = Faculty.objects.create(university=uni_elite, name='كلية ريادة الأعمال وإدارة النظم', sort_order=4)
            fac5 = Faculty.objects.create(university=uni_elite, name='كلية الوسائط المتعددة والتصميم الرقمي', sort_order=5)
            
            # 5 برامج دراسية لكل كلية بالجامعة الثانية
            fac1_programs = [
                ("بكالوريوس الذكاء الاصطناعي والتعلم الآلي", "4 سنوات", "22,000 رنجت سنوياً"),
                ("بكالوريوس هندسة الروبوتات والأتمتة", "4 سنوات", "24,000 رنجت سنوياً"),
                ("بكالوريوس علوم البيانات الضخمة", "3 سنوات", "20,000 رنجت سنوياً"),
                ("ماجستير الذكاء الاصطناعي التطبيقي", "سنتان", "25,000 رنجت سنوياً"),
                ("دكتوراه في التعلم العميق والرؤية الحاسوبية", "3 سنوات", "28,000 رنجت سنوياً"),
            ]
            fac2_programs = [
                ("بكالوريوس الهندسة الميكانيكية والنظم الذكية", "4 سنوات", "20,000 رنجت سنوياً"),
                ("بكالوريوس الهندسة المدنية وتشييد المدن الذكية", "4 سنوات", "19,500 رنجت سنوياً"),
                ("بكالوريوس الهندسة الطبية الحيوية", "4 سنوات", "21,000 رنجت سنوياً"),
                ("بكالوريوس العمارة الحديثة والتصميم المستدام", "5 سنوات", "23,000 رنجت سنوياً"),
                ("ماجستير هندسة المواد المتقدمة", "سنتان", "22,000 رنجت سنوياً"),
            ]
            fac3_programs = [
                ("بكالوريوس أمن الشبكات والتحري الرقمي", "3 سنوات", "19,000 رنجت سنوياً"),
                ("بكالوريوس الدفاع السيبراني وأمن المعلومات", "3 سنوات", "19,500 رنجت سنوياً"),
                ("بكالوريوس علم الجريمة الرقمية والعدالة الجنائية", "3 سنوات", "18,000 رنجت سنوياً"),
                ("ماجستير الأمن السيبراني التنفيذي", "سنة ونصف", "24,000 رنجت سنوياً"),
                ("دبلوم حماية البيانات والخصوصية", "سنة واحدة", "11,000 رنجت سنوياً"),
            ]
            fac4_programs = [
                ("بكالوريوس إدارة الابتكار وريادة الأعمال", "3 سنوات", "16,000 رنجت سنوياً"),
                ("بكالوريوس إدارة المشاريع التكنولوجية", "3 سنوات", "16,500 رنجت سنوياً"),
                ("بكالوريوس إدارة سلاسل الإمداد الرقمية", "3 سنوات", "15,500 رنجت سنوياً"),
                ("ماجستير التحول الرقمي للشركات", "سنة ونصف", "20,000 رنجت سنوياً"),
                ("بكالوريوس المالية التقنية (FinTech)", "3 سنوات", "17,000 رنجت سنوياً"),
            ]
            fac5_programs = [
                ("بكالوريوس تصميم ألعاب الفيديو والوسائط", "3 سنوات", "17,500 رنجت سنوياً"),
                ("بكالوريوس التصميم الجرافيكي ثلاثي الأبعاد", "3 سنوات", "16,500 رنجت سنوياً"),
                ("بكالوريوس تحريك الرسوم والوسائط التفاعلية", "3 سنوات", "17,000 رنجت سنوياً"),
                ("بكالوريوس الإنتاج السينمائي والرقمنة", "3 سنوات", "18,000 رنجت سنوياً"),
                ("ماجستير الفنون الرقمية وتصميم تجربة المستخدم", "سنتان", "21,000 رنجت سنوياً"),
            ]

            for i, (name, dur, fees) in enumerate(fac1_programs):
                Program.objects.create(faculty=fac1, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac2_programs):
                Program.objects.create(faculty=fac2, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac3_programs):
                Program.objects.create(faculty=fac3, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac4_programs):
                Program.objects.create(faculty=fac4, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac5_programs):
                Program.objects.create(faculty=fac5, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            
            # 5 أسئلة شائعة للجامعة الثانية
            UniversityFAQ.objects.create(university=uni_elite, question='هل توجد برامج تبادل طلابي مع جامعات أجنبية؟', answer='نعم، تمتلك الجامعة شراكات تبادل طلابي مع جامعات في بريطانيا وأستراليا، تمكن الطالب من دراسة فصل أو سنة كاملة في الخارج.', sort_order=1)
            UniversityFAQ.objects.create(university=uni_elite, question='هل هناك تدريب ميداني إلزامي قبل التخرج؟', answer='نعم، تتضمن جميع البرامج الهندسية والتقنية فصلاً دراسياً كاملاً مخصصاً للتدريب العملي في كبرى شركات التكنولوجيا.', sort_order=2)
            UniversityFAQ.objects.create(university=uni_elite, question='هل توجد منح دراسية جزئية للطلاب المتفوقين؟', answer='نعم، يقدم معهد النخبة حسومات ومنح دراسية جزئية تتراوح بين 20% إلى 50% للطلاب الحاصلين على معدلات أكاديمية متميزة.', sort_order=3)
            UniversityFAQ.objects.create(university=uni_elite, question='كيف يمكنني حجز موعد لاختبار القبول؟', answer='يتم تحديد موعد الاختبار فور مراجعة الأوراق الثبوتية وقبول طلب الالتحاق مبدئياً عبر بوابة الطالب.', sort_order=4)
            UniversityFAQ.objects.create(university=uni_elite, question='هل يتطلب تخصص الروبوتات خلفية سابقة في البرمجة؟', answer='لا يشترط وجود خلفية برمجية مسبقة، حيث يدرس الطالب مساقات تمهيدية في البرمجة والخوارزميات في الفصل الأول.', sort_order=5)

        # الجامعة الثالثة: الجامعة الوطنية الماليزية
        uni_national, national_created = University.objects.get_or_create(
            slug='national-malaysian-university',
            defaults={
                'name': 'الجامعة الوطنية الماليزية',
                'university_type': 'public',
                'logo': self.create_stylized_logo('national_logo.png', 'UKM', '#1d4ed8'),
                'main_image': self.load_generated_image(uni_campus_path, '#1e3a8a', 'national_main.jpg'),
                'description': 'الجامعة الوطنية الماليزية هي إحدى كبريات الجامعات الحكومية والبحثية الخمس الرائدة في ماليزيا. تأسست في سبعينيات القرن الماضي وتتبوأ مراكز متقدمة جداً في التصنيفات العالمية (QS World University Rankings).',
                'location': 'باني، سيلانجور، ماليزيا',
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'admission_requirements': 'يتطلب التسجيل في هذه الجامعة الحكومية التقديم المبكر نظراً لمحدودية المقاعد المتاحة للطلاب الدوليين.',
                'admission_requirements_bachelor': 'معدل عام لا يقل عن 80% في الثانوية العامة وإجادة تامة للغة الإنجليزية (آيلتس 6.0 كحد أدنى).',
                'admission_requirements_master': 'مؤهل البكالوريوس بتقدير لا يقل عن جيد جداً أو ما يعادله من جامعة معترف بها عالمياً.',
                'admission_requirements_phd': 'ماجستير مع سجل دراسي متميز وموافقة مشرف أكاديمي من الجامعة قبل تقديم الطلب الرسمي.',
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'الدراسة في الجامعة الوطنية الماليزية الحكومية',
                'meta_description': 'تعرف على شروط التسجيل والرسوم الدراسية للطلاب الأجانب في الجامعة الوطنية الماليزية الحكومية وتصنيفها العالمي.',
                'focus_keyword': 'الجامعة الوطنية الماليزية'
            }
        )
        if national_created:
            # 5 كليات للجامعة الثالثة
            fac1 = Faculty.objects.create(university=uni_national, name='كلية العلوم والتقنية', sort_order=1)
            fac2 = Faculty.objects.create(university=uni_national, name='كلية الاقتصاد والتنمية', sort_order=2)
            fac3 = Faculty.objects.create(university=uni_national, name='كلية الطب والعلوم الصحية البشري', sort_order=3)
            fac4 = Faculty.objects.create(university=uni_national, name='كلية طب الأسنان وجراحة الفم', sort_order=4)
            fac5 = Faculty.objects.create(university=uni_national, name='كلية الحقوق والدراسات القانونية المقارنة', sort_order=5)
            
            # 5 برامج دراسية لكل كلية بالجامعة الثالثة
            fac1_programs = [
                ("ماجستير علوم البيانات وتحليل الأعمال", "سنة ونصف", "18,000 رنجت سنوياً"),
                ("بكالوريوس العلوم الحيوية والتقنية الحيوية", "4 سنوات", "14,500 رنجت سنوياً"),
                ("بكالوريوس الكيمياء التطبيقية والصناعية", "4 سنوات", "13,500 رنجت سنوياً"),
                ("بكالوريوس الفيزياء الطبية والإشعاعية", "4 سنوات", "14,000 رنجت سنوياً"),
                ("ماجستير علوم البيئة والتغير المناخي", "سنتان", "19,000 رنجت سنوياً"),
            ]
            fac2_programs = [
                ("بكالوريوس العلوم الاقتصادية وإدارة الأزمات", "3 سنوات", "11,000 رنجت سنوياً"),
                ("بكالوريوس التنمية المستدامة والاقتصاد الأخضر", "3 سنوات", "11,500 رنجت سنوياً"),
                ("بكالوريوس العلوم المالية والمصرفية", "3 سنوات", "12,000 رنجت سنوياً"),
                ("بكالوريوس الإحصاء التطبيقي والاقتصاد القياسي", "3 سنوات", "12,500 رنجت سنوياً"),
                ("ماجستير السياسات الاقتصادية العامة", "سنة ونصف", "15,000 رنجت سنوياً"),
            ]
            fac3_programs = [
                ("بكالوريوس الطب البشري والجراحة (MBBS)", "5 سنوات", "45,000 رنجت سنوياً"),
                ("بكالوريوس العلوم التمريضية الرعائية", "4 سنوات", "18,000 رنجت سنوياً"),
                ("بكالوريوس العلاج الطبيعي والتأهيل الحركي", "4 سنوات", "20,000 رنجت سنوياً"),
                ("بكالوريوس العلوم الصيدلانية السريرية", "4 سنوات", "25,000 رنجت سنوياً"),
                ("ماجستير الصحة العامة والوبائيات", "سنتان", "22,000 رنجت سنوياً"),
            ]
            fac4_programs = [
                ("بكالوريوس طب وجراحة الفم والأسنان (BDS)", "5 سنوات", "40,000 رنجت سنوياً"),
                ("بكالوريوس تقويم الأسنان والفكين", "3 سنوات (بعد BDS)", "35,000 رنجت سنوياً"),
                ("بكالوريوس طب أسنان الأطفال الوقائي", "3 سنوات", "30,000 رنجت سنوياً"),
                ("ماجستير جراحة الوجه والفكين", "3 سنوات", "42,000 رنجت سنوياً"),
                ("دبلوم تكنولوجيا صناعة تعويضات الأسنان", "سنتان", "15,000 رنجت سنوياً"),
            ]
            fac5_programs = [
                ("بكالوريوس القانون المقارن والدراسات الدستورية", "4 سنوات", "14,000 رنجت سنوياً"),
                ("بكالوريوس القانون الدولي والعلاقات الدبلوماسية", "4 سنوات", "15,000 رنجت سنوياً"),
                ("بكالوريوس قانون الأعمال والتحكيم التجاري", "4 سنوات", "16,000 رنجت سنوياً"),
                ("ماجستير العلوم الجنائية وحقوق الإنسان", "سنتان", "18,000 رنجت سنوياً"),
                ("دكتوراه في فلسفة القانون والقوانين المقارنة", "3 سنوات", "22,000 رنجت سنوياً"),
            ]

            for i, (name, dur, fees) in enumerate(fac1_programs):
                Program.objects.create(faculty=fac1, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac2_programs):
                Program.objects.create(faculty=fac2, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac3_programs):
                Program.objects.create(faculty=fac3, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac4_programs):
                Program.objects.create(faculty=fac4, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            for i, (name, dur, fees) in enumerate(fac5_programs):
                Program.objects.create(faculty=fac5, name=name, duration=dur, tuition_fees=fees, sort_order=i+1)
            
            # 5 أسئلة شائعة للجامعة الثالثة
            UniversityFAQ.objects.create(university=uni_national, question='كيف يتم التقديم على التأشيرة الدراسية؟', answer='بعد استلام القبول الجامعي المبدئي ودفع الرسوم المقررة، يتولى قسم التأشيرات بالجامعة إجراءات التقديم على الـ VAL عبر موقع EMGS بالتنسيق مع الطالب.', sort_order=1)
            UniversityFAQ.objects.create(university=uni_national, question='هل يمكنني العمل بدوام جزئي أثناء الدراسة؟', answer='يسمح قانون الهجرة الماليزي للطلاب الدوليين بالعمل بدوام جزئي بحد أقصى 20 ساعة أسبوعياً خلال الإجازات الفصلية فقط وفي قطاعات محددة.', sort_order=2)
            UniversityFAQ.objects.create(university=uni_national, question='ما هو تصنيف الجامعة عالمياً؟', answer='تصنف الجامعة ضمن أفضل 150 جامعة على مستوى العالم وفقاً لتصنيف QS العالمي للجامعات، وتعد من أفضل 5 جامعات بحثية في ماليزيا.', sort_order=3)
            UniversityFAQ.objects.create(university=uni_national, question='هل توفر الجامعة تأمين صحي شامل؟', answer='نعم، تشمل رسوم الخدمات الطلابية تأميناً صحياً سنوياً يغطي العيادات الخارجية وحالات الطوارئ في المستشفيات المعتمدة.', sort_order=4)
            UniversityFAQ.objects.create(university=uni_national, question='ما هي الأوراق المطلوبة للتقديم للماجستير؟', answer='شهادة البكالوريوس مع بيان الدرجات، خطابين توصية أكاديميين، مقترح بحثي (لبرامج البحث)، وشهادة إتقان اللغة الإنجليزية.', sort_order=5)

        # ربط العلاقات المتبادلة بين التخصصات والجامعات
        if se_created or global_created:
            uni_global.related_majors.add(major_se, major_ib)
            major_se.best_universities.add(uni_global)
            major_ib.best_universities.add(uni_global)
            
        if elite_created or ai_created:
            uni_elite.related_majors.add(major_se, major_ai)
            major_se.best_universities.add(uni_elite)
            major_ai.best_universities.add(uni_elite)
            
        if national_created or ib_created:
            uni_national.related_majors.add(major_ib, major_ai)
            major_ib.best_universities.add(uni_national)
            major_ai.best_universities.add(uni_national)
            
            major_se.cheap_universities.add(uni_global)
            major_ib.cheap_universities.add(uni_national)

        self.stdout.write(self.style.SUCCESS('تم إنشاء الجامعات والكليات والـ FAQs وربط التخصصات بنجاح!'))

        # 6. إنشاء المعاهد (3 معاهد وبصور مناسبة)
        self.stdout.write('جاري إنشاء المعاهد (3 معاهد)...')
        
        # المعهد الأول: معهد اللغات الحديثة
        inst_lang, lang_created = Institute.objects.get_or_create(
            slug='modern-languages-institute',
            defaults={
                'name': 'معهد اللغات الحديثة',
                'main_image': self.load_generated_image(classroom_path, '#0284c7', 'lang_main.jpg'), # صورة الفصل الدراسي مناسبة جداً
                'description': 'معهد اللغات الحديثة هو مركز رائد معتمد دولياً لتعليم اللغة الإنجليزية كلغة ثانية، ويقدم دورات مكثفة ومصممة لمساعدة الطلاب الدوليين على اجتياز اختبارات آيلتس وتوفل بنظام تعليمي تفاعلي حديث.',
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'دراسة اللغة الإنجليزية في معهد اللغات الحديثة',
                'meta_description': 'احصل على قبول سريع ودورة لغة إنجليزية مكثفة ومتميزة في معهد اللغات الحديثة لتأهيلك للدراسة الجامعية في ماليزيا.',
                'focus_keyword': 'معهد اللغات الحديثة'
            }
        )
        if lang_created:
            Course.objects.create(
                institute=inst_lang,
                duration='شهر',
                fees_myr='3,400',
                fees_usd='857',
                fees_sar='3,216',
                visa_duration='بدون تاشيرة',
                sort_order=1
            )
            Course.objects.create(
                institute=inst_lang,
                duration='شهرين',
                fees_myr='6,300',
                fees_usd='1,588',
                fees_sar='5,960',
                visa_duration='بدون تاشيرة',
                sort_order=2
            )
            Course.objects.create(
                institute=inst_lang,
                duration='3 أشهر',
                fees_myr='9,200',
                fees_usd='2,318',
                fees_sar='8,703',
                visa_duration='بدون تاشيرة',
                sort_order=3
            )
            Course.objects.create(
                institute=inst_lang,
                duration='6 أشهر',
                fees_myr='21,100',
                fees_usd='5,317',
                fees_sar='19,961',
                visa_duration='6 أشهر',
                sort_order=4
            )

        # المعهد الثاني: المعهد التقني العالي
        inst_tech, tech_created = Institute.objects.get_or_create(
            slug='high-technical-institute',
            defaults={
                'name': 'المعهد التقني العالي',
                'main_image': self.load_generated_image(se_path, '#4b5563', 'tech_main.jpg'), # صورة الكود والشاشات مناسبة للمعهد التقني
                'description': 'يقدم المعهد التقني العالي دبلومات تدريبية مهنية وتطبيقية قصيرة وطويلة المدى، تركز على التطبيقات العملية المباشرة واحتياجات سوق العمل الحديث في مجالات التكنولوجيا وإدارة الشبكات.',
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'المعهد التقني العالي | دبلومات مهنية معتمدة في الشبكات والبرمجة',
                'meta_description': 'سجل الآن في المعهد التقني العالي واحصل على تدريب وتأهيل مهني متميز بشهادات معتمدة تؤهلك لسوق العمل فوراً.',
                'focus_keyword': 'المعهد التقني العالي'
            }
        )
        if tech_created:
            Course.objects.create(
                institute=inst_tech,
                duration='3 أشهر',
                fees_myr='4,500',
                fees_usd='1,000',
                fees_sar='3,750',
                visa_duration='بدون تاشيرة',
                sort_order=1
            )
            Course.objects.create(
                institute=inst_tech,
                duration='6 أشهر',
                fees_myr='8,500',
                fees_usd='1,900',
                fees_sar='7,125',
                visa_duration='6 أشهر',
                sort_order=2
            )
            Course.objects.create(
                institute=inst_tech,
                duration='سنة واحدة',
                fees_myr='16,000',
                fees_usd='3,600',
                fees_sar='13,500',
                visa_duration='سنة',
                sort_order=3
            )

        # المعهد الثالث: معهد إعداد القادة
        inst_lead, lead_created = Institute.objects.get_or_create(
            slug='leadership-development-institute',
            defaults={
                'name': 'معهد إعداد القادة',
                'main_image': self.load_generated_image(meeting_path, '#b45309', 'lead_main.jpg'), # صورة قاعة الاجتماعات مناسبة للإدارة والقيادة
                'description': 'مركز تدريب متقدم يهدف لتأهيل الكوادر الإدارية وتطوير المهارات القيادية والشخصية للأفراد والمؤسسات والشركات، عبر برامج تفاعلية وورش عمل مستمرة بالتعاون مع كبار الخبراء الإداريين.',
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'معهد إعداد القادة لتطوير المهارات الإدارية والتنفيذية',
                'meta_description': 'طور مهاراتك القيادية والتخطيط الاستراتيجي مع ورش العمل والدورات التنفيذية في معهد إعداد القادة المتميز.',
                'focus_keyword': 'معهد إعداد القادة'
            }
        )
        if lead_created:
            Course.objects.create(
                institute=inst_lead,
                duration='أسبوعين',
                fees_myr='3,000',
                fees_usd='675',
                fees_sar='2,530',
                visa_duration='بدون تاشيرة',
                sort_order=1
            )
            Course.objects.create(
                institute=inst_lead,
                duration='شهر',
                fees_myr='5,500',
                fees_usd='1,240',
                fees_sar='4,650',
                visa_duration='بدون تاشيرة',
                sort_order=2
            )

        self.stdout.write(self.style.SUCCESS('تم إنشاء المعاهد والدورات بنجاح!'))

        # 7. إنشاء المقالات (3 مقالات وبصور مناسبة)
        self.stdout.write('جاري إنشاء المقالات (3 مقالات)...')
        
        # المقال الأول: دليلك الشامل للدراسة في الخارج
        art1, art1_created = Article.objects.get_or_create(
            slug='study-abroad-guide',
            defaults={
                'title': 'دليلك الشامل للدراسة في الخارج',
                'featured_image': self.load_generated_image(studying_path, '#e11d48', 'art1_feat.jpg'), # صورة الطالب الذي يدرس مناسبة جداً
                'category': cat_admissions,
                'author': author,
                'content': """
                <p>تعد خطوة الدراسة في الخارج من أهم القرارات التي يتخذها الطالب في حياته الأكاديمية والمهنية. إنها فرصة ممتازة ليس فقط للحصول على تعليم ذي جودة عالية، بل لاكتساب خبرات وتجارب حياتية تثري الشخصية وتفتح آفاقاً جديدة للمستقبل.</p>
                <h2>لماذا تختار الدراسة في الخارج؟</h2>
                <ul>
                    <li>التعرض لبيئة تعليمية متميزة تعتمد على التفكير النقدي والمشاريع العملية.</li>
                    <li>تطوير مهارات لغوية جديدة والتحدث بها بطلاقة في بيئتها الأصلية.</li>
                    <li>بناء شبكة علاقات دولية واسعة مع زملاء وأكاديميين من مختلف الثقافات.</li>
                </ul>
                <h2>كيف تبدأ التخطيط لرحلتك الدراسية؟</h2>
                <p>تبدأ الرحلة باختيار التخصص المناسب الذي يتوافق مع مهاراتك وشغفك وااحتياجات سوق العمل المستقبلي. بعد ذلك، قم بتحديد الميزانية المناسبة وابدأ في مقارنة الجامعات والدول التي تقدم هذا التخصص بكفاءة وتكلفة تتناسب مع قدراتك المادية.</p>
                """,
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'دليلك الشامل للتقديم والدراسة في الخارج بالتفصيل',
                'meta_description': 'اقرأ الدليل الشامل لكيفية التخطيط والتقديم للدراسة في الخارج، واختيار الدولة والجامعة وتجهيز المستندات المطلوبة.',
                'focus_keyword': 'الدراسة في الخارج'
            }
        )
        if art1_created:
            art1.tags.add(tag_malaysia, tag_tips)

        # المقال الثاني: أهم التخصصات المطلوبة في سوق العمل 2026
        art2, art2_created = Article.objects.get_or_create(
            slug='demanded-majors-2026',
            defaults={
                'title': 'أهم التخصصات المطلوبة في سوق العمل 2026',
                'featured_image': self.load_generated_image(se_path, '#ea580c', 'art2_feat.jpg'), # صورة شاشات الكود
                'category': cat_career,
                'author': author,
                'content': """
                <p>يتأثر سوق العمل بشكل مستمر بالثورات التكنولوجية المتتالية وظهور نماذج الذكاء الاصطناعي التوليدي والتحول الرقمي الكامل. هذا التسارع يفرض على الطلاب والباحثين عن فرصة عمل حقيقية اختيار تخصصات ذات قيمة عالية ومطلوبة بشدة في السنوات القادمة.</p>
                <h2>أبرز التخصصات الواعدة لعام 2026 وما بعده:</h2>
                <h3>1. هندسة البرمجيات وتطوير الحلول السحابية</h3>
                <p>جميع المؤسسات أصبحت الآن بحاجة للتحول الرقمي، مما يجعل الطلب على مهندسي البرمجيات ومطوري التطبيقات والحلول السحابية مستمراً وفي تصاعد دائم.</p>
                <h3>2. علوم البيانات وتعلم الآلة</h3>
                <p>تحليل البيانات الضخمة وبناء نماذج الذكاء الاصطناعي هي الركيزة الأساسية لاتخاذ القرارات الاستراتيجية في الشركات الكبرى والمؤسسات التقنية.</p>
                <h3>3. الأمن السيبراني (Cybersecurity)</h3>
                <p>مع زيادة الاعتماد على الحلول الرقمية، تزداد أهمية حماية البيانات والأنظمة ضد الاختراقات والهجمات الإلكترونية.</p>
                """,
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'التخصصات الأكثر طلباً في سوق العمل لعام 2026',
                'meta_description': 'تعرف على التخصصات الأكاديمية والمهنية الواعدة والمطلوبة في سوق العمل العالمي والعربي لعام 2026 ومستقبل التوظيف.',
                'focus_keyword': 'سوق العمل 2026'
            }
        )
        if art2_created:
            art2.tags.add(tag_tips, tag_programming)

        # المقال الثالث: كيف تختار الجامعة المناسبة لمستقبلك
        art3, art3_created = Article.objects.get_or_create(
            slug='choosing-right-university',
            defaults={
                'title': 'كيف تختار الجامعة المناسبة لمستقبلك',
                'featured_image': self.load_generated_image(uni_campus_path, '#2563eb', 'art3_feat.jpg'), # صورة حرم الجامعة
                'category': cat_admissions,
                'author': author,
                'content': """
                <p>بعد اختيار التخصص الأكاديمي، تأتي خطوة اختيار الجامعة المناسبة. إن اسم المؤسسة الأكاديمية ونظامها الدراسي وشراكاتها المهنية تلعب دوراً كبيراً في سهولة دخولك إلى سوق العمل بعد التخرج وحصولك على فرصة عمل متميزة.</p>
                <h2>معايير هامة لاختيار الجامعة المناسبة:</h2>
                <ol>
                    <li><strong>الاعتراف والاعتماد الأكاديمي:</strong> تأكد تماماً أن برامج الجامعة معتمدة محلياً ودولياً ومعترف بها في بلدك الأم لتجنب أي مشاكل في معادلة الشهادة لاحقاً.</li>
                    <li><strong>تكلفة الرسوم والمعيشة:</strong> يجب وضع خطة مالية تغطي الرسوم الدراسية السنوية بالإضافة إلى تكاليف السكن والتأمين والمعيشة دون ضغوط مالية أثناء الدراسة.</li>
                    <li><strong>مستوى التدريب العملي:</strong> ابحث عن الجامعات التي تحتوي برامجها على فصول تدريب عملية إلزامية بالتعاون مع الشركات والمصانع المعتمدة.</li>
                </ol>
                """,
                'publish_status': PublishStatus.PUBLISHED,
                'meta_title': 'معايير اختيار الجامعة الأكاديمية الصحيحة والاعتماد',
                'meta_description': 'تعرف على أهم النصائح والمعايير الذهبية لاختيار الجامعة الأكاديمية المناسبة لميزانيتك وتخصصك ومستقبلك المهني.',
                'focus_keyword': 'اختيار الجامعة'
            }
        )
        if art3_created:
            art3.tags.add(tag_malaysia, tag_tips)

        # ربط العلاقات المتبادلة بين المقالات والجامعات والمعاهد والتخصصات
        if art1_created:
            art1.related_universities.add(uni_global, uni_national)
            art1.related_majors.add(major_ib)
        if art2_created:
            art2.related_universities.add(uni_elite)
            art2.related_majors.add(major_se, major_ai)
            art2.related_institutes.add(inst_tech)
        if art3_created:
            art3.related_universities.add(uni_global, uni_elite, uni_national)
            art3.related_institutes.add(inst_lang)

        self.stdout.write(self.style.SUCCESS('تم إنشاء المقالات بنجاح وربطها بالوسوم والتصنيفات والجامعات والمعاهد!'))
        self.stdout.write(self.style.SUCCESS('=================================================='))
        self.stdout.write(self.style.SUCCESS('تم حقن كافة البيانات التجريبية بنجاح بنسبة 100%!'))
        self.stdout.write(self.style.SUCCESS('=================================================='))
