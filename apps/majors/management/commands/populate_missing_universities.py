from django.core.management.base import BaseCommand, CommandError
from apps.majors.models import Major
from apps.universities.models import University
from django.db import transaction
import os

class Command(BaseCommand):
    help = 'Populate missing best_universities, cheap_universities and other non-tuition fields for majors.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate university mapping without saving to the database.',
        )
        parser.add_argument(
            '--commit',
            action='store_true',
            help='Commit mapped universities to the database.',
        )
        parser.add_argument(
            '--fields',
            action='store_true',
            help='Populate missing non-tuition content fields for the 11 majors.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        commit = options.get('commit')
        fields_mode = options.get('fields')

        if not dry_run and not commit:
            raise CommandError("يجب تحديد إما --dry-run للمحاكاة أو --commit للتطبيق الفعلي.")

        if fields_mode:
            self.handle_fields_population(dry_run, commit)
        else:
            self.handle_universities_mapping(dry_run, commit)

    def handle_fields_population(self, dry_run, commit):
        FIELDS_MAPPING = {
            'دراسة-الاتصال-الجماهيري-والإعلام-في-م': {
                'how_to_apply_section': (
                    "خطوات التقديم لدراسة تخصص الاتصال الجماهيري والإعلام في ماليزيا:\n"
                    "1. تجهيز الأوراق المطلوبة: نسخة من جواز السفر (كامل الصفحات)، شهادة الثانوية العامة المترجمة، وكشف الدرجات.\n"
                    "2. تقديم الطلب: يمكنك تقديم أوراقك عبر بوابة العلوم (Sciences Gates) للحصول على قبول أكاديمي مبدئي مجاني.\n"
                    "3. شهادة اللغة الإنجليزية: إذا كنت تملك شهادة آيلتس أو توفل قدمها، أو يمكنك دراسة كورس اللغة الإنجليزية المكثف بالجامعة قبل البدء.\n"
                    "4. الحصول على التأشيرة: بعد صدور القبول الأكاديمي، يتم البدء في إجراءات استخراج فيزا الطالب (EMGS) والتي تستغرق عادة من 3 إلى 6 أسابيع.\n"
                    "5. السفر والالتحاق: بعد الحصول على موافقة الفيزا، يمكنك حجز تذكرتك والسفر لماليزيا لإتمام التسجيل الفعلي والبدء بالدراسة."
                )
            },
            'دراسة-التغذية-في-ماليزيا': {
                'career_opportunities': (
                    "الفرص الوظيفية المتاحة لخريجي تخصص التغذية في ماليزيا وخارجها:\n"
                    "- أخصائي تغذية علاجية في المستشفيات والمراكز الطبية.\n"
                    "- مستشار تغذية في الأندية الرياضية والمراكز الصحية.\n"
                    "- أخصائي مراقبة جودة وسلامة الأغذية في شركات تصنيع المواد الغذائية.\n"
                    "- باحث علمي في مراكز الأبحاث الغذائية والجامعات.\n"
                    "- أخصائي تغذية عامة في المنظمات الصحية والوزارات لنشر الوعي الصحي."
                )
            },
            'دراسة-الذكاء-الاصطناعي-في-ماليزيا': {
                'how_to_apply_section': (
                    "خطوات التقديم لدراسة تخصص الذكاء الاصطناعي في ماليزيا:\n"
                    "1. الأوراق المطلوبة: جواز السفر الكامل، شهادة الثانوية العامة المترجمة للإنجليزية وكشف العلامات.\n"
                    "2. التقديم عبر بوابة العلوم: رفع المستندات إلكترونياً للحصول على القبول من الجامعة المناسبة مجاناً.\n"
                    "3. شروط اللغة: تتطلب أغلب الجامعات درجة آيلتس 5.0 أو 5.5، وفي حال عدم توفرها يمكنك دراسة اللغة بالجامعة أولاً.\n"
                    "4. استخراج فيزا الطالب: بعد القبول يتم تقديم الملف لهيئة EMGS للحصول على خطاب الموافقة على الفيزا (VAL).\n"
                    "5. الوصول لماليزيا: بعد صدور تأشيرة الطالب، يمكنك القدوم والبدء في الدراسة مباشرة."
                )
            },
            'دراسة-الصيدلة-في-ماليزيا-صيدلة-سريرية': {
                'how_to_apply_section': (
                    "خطوات التقديم لدراسة تخصص الصيدلة في ماليزيا:\n"
                    "1. تحضير المستندات: جواز سفر ساري، شهادة الثانوية العامة وكشف الدرجات (مع ترجمة معتمدة للغة الإنجليزية).\n"
                    "2. شروط القبول الخاصة: تطلب كليات الصيدلة عادةً معدلات مرتفعة في المواد العلمية (الكيمياء والأحياء).\n"
                    "3. التقديم: قدم مستنداتك عبر مستشاري بوابة العلوم للحصول على القبول الأكاديمي المعتمد مجاناً.\n"
                    "4. إثبات اللغة: يتطلب التخصص عادةً آيلتس بدرجة 5.5 أو 6.0.\n"
                    "5. إجراءات الفيزا: بعد استلام القبول، يتم التقديم على EMGS للحصول على تأشيرة الطالب والسفر لماليزيا."
                )
            },
            'دراسة-العلوم-في-ماليزيا-رسوم-الدراسة-و': {
                'phd_duration': "3-4 سنوات"
            },
            'دراسة-الهندسة-الطبية-الحيوية': {
                'why_study_section': (
                    "لماذا تدرس تخصص الهندسة الطبية الحيوية في ماليزيا؟\n"
                    "- الجمع بين الطب والهندسة: يتيح لك التخصص تطبيق المفاهيم الهندسية لحل المشكلات الطبية وتطوير الرعاية الصحية.\n"
                    "- تجهيزات أكاديمية ممتازة: تمتلك الجامعات الماليزية مختبرات متطورة ومجهزة بأحدث الأجهزة الطبية للتدريب العملي.\n"
                    "- الطلب المرتفع في السوق: هناك حاجة مستمرة لمهندسي الأجهزة الطبية لإدارة وصيانة وتطوير الأجهزة في المستشفيات والشركات الطبية.\n"
                    "- اعتماد Washington Accord: الهندسة في ماليزيا معتمدة دولياً مما يسهل العمل بالخارج بعد التخرج."
                )
            },
            'الهندسة-النووية': {
                'keyphrase_synonyms': "دراسة الهندسة النووية في ماليزيا, تخصص الهندسة النووية ماليزيا, تكاليف الهندسة النووية بماليزيا"
            },
            'علوم-البيانات': {
                'keyphrase_synonyms': "دراسة علوم البيانات في ماليزيا, تخصص تحليل البيانات بماليزيا, Data Science in Malaysia"
            },
            'اللوجستيات-وسلسلة-التوريد': {
                'keyphrase_synonyms': "دراسة اللوجستيات وسلسلة التوريد في ماليزيا, تخصص إدارة اللوجستيات ماليزيا, Logistics and Supply Chain in Malaysia"
            },
            'دراسة-إدارة-الأعمال-في-ماليزيا-رسوم-ال': {
                'bachelor_duration': "3 سنوات",
                'master_duration': "1.5 - 2 سنة",
                'phd_duration': "3-4 سنوات",
                'study_language': "اللغة الإنجليزية",
                'practical_training': "متاح ومدمج في الفصل الدراسي الأخير (تدريب ميداني)"
            },
            'دراسة-إدارة-الفنادق-والضيافة': {
                'bachelor_duration': "3 سنوات",
                'master_duration': "1.5 - 2 سنة",
                'phd_duration': "3-4 سنوات",
                'study_language': "اللغة الإنجليزية",
                'practical_training': "متاح ومدمج في الفصل الدراسي الأخير (تدريب ميداني)"
            },
            'دراسة-إنتاج-الأفلام-والفيديو': {
                'bachelor_duration': "3 سنوات",
                'master_duration': "1.5 - 2 سنة",
                'phd_duration': "3-4 سنوات",
                'study_language': "اللغة الإنجليزية",
                'practical_training': "متاح ومدمج في الفصل الدراسي الأخير (تدريب ميداني)"
            }
        }

        report_lines = []
        report_lines.append("# تقرير محاكاة ملء الحقول التعريفية للتخصصات (Majors Fields Population Report)")
        report_lines.append(f"**حالة التشغيل**: {'محاكاة (Dry Run)' if dry_run else 'تطبيق فعلي (Commit)'}")
        report_lines.append("")
        report_lines.append("| الرقم | اسم التخصص | الحقل المعدل | القيمة المقترحة | حالة التحديث |")
        report_lines.append("|---|---|---|---|---|")

        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for idx, (slug, data) in enumerate(FIELDS_MAPPING.items(), 1):
                try:
                    major = Major.objects.get(slug=slug)
                except Major.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Major not found for slug: {slug}"))
                    continue

                for field, val in data.items():
                    current_val = getattr(major, field, None)
                    
                    # If field is empty, we populate it
                    if not current_val or str(current_val).strip() == "":
                        update_status_str = "تم التحديث" if commit else "مقترح للتحديث"
                        updated_count += 1
                        
                        if commit:
                            setattr(major, field, val)
                            major.save()
                            
                        # Show snippet of value in report
                        val_snippet = val.replace('\n', ' ')
                        if len(val_snippet) > 60:
                            val_snippet = val_snippet[:60] + "..."
                        report_lines.append(f"| {idx} | {major.name} | {field} | {val_snippet} | {update_status_str} |")
                    else:
                        # Skip if it already contains data
                        skipped_count += 1
                        val_snippet = str(current_val).replace('\n', ' ')
                        if len(val_snippet) > 60:
                            val_snippet = val_snippet[:60] + "..."
                        report_lines.append(f"| {idx} | {major.name} | {field} | {val_snippet} | تخطي (يحتوي بيانات) |")

            if dry_run:
                transaction.set_rollback(True)

        report_file = os.path.join(os.getcwd(), 'majors_fields_updates.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))

        self.stdout.write(self.style.SUCCESS(f"\nCompleted fields update. Updated/Proposed: {updated_count}, Skipped: {skipped_count}"))
        self.stdout.write(self.style.SUCCESS(f"Report written to: {report_file}"))

    def handle_universities_mapping(self, dry_run, commit):
        MAPPING = {
            'دراسة-الاتصال-الجماهيري-والإعلام-في-م': {
                'best': ['Taylor\'s', 'Sunway', 'Nottingham', 'MONASH'],
                'cheap': ['UUM', 'UiTM', 'UniMAS', 'UTAR']
            },
            'دراسة-الاقتصاد-في-ماليزيا': {
                'best': ['UM', 'UKM', 'UPM', 'MONASH', 'Taylor\'s'],
                'cheap': ['UUM', 'UTHM', 'UniMAS', 'IIUM']
            },
            'دراسة-البصريات-في-ماليزيا': {
                'best': ['UKM', 'UCSI', 'MSU', 'SEGi', 'MAHSA'],
                'cheap': ['UKM', 'MSU', 'SEGi']
            },
            'دراسة-التجارة-الإلكترونية-في-ماليزيا': {
                'best': ['APU', 'Taylor\'s', 'Sunway', 'MONASH', 'UCSI'],
                'cheap': ['UUM', 'UTAR', 'UTHM', 'UniMAS', 'IIUM']
            },
            'دراسة-التسويق-في-ماليزيا': {
                'best': ['Taylor\'s', 'Sunway', 'MONASH', 'Nottingham', 'UCSI'],
                'cheap': ['UUM', 'UTAR', 'UTHM', 'UniMAS', 'IIUM']
            },
            'دراسة-التغذية-في-ماليزيا': {
                'best': ['Taylor\'s', 'UCSI', 'Nottingham', 'MONASH', 'UKM', 'UPM'],
                'cheap': ['UKM', 'UPM', 'USM', 'IIUM']
            },
            'دراسة-التمريض-في-ماليزيا': {
                'best': ['UM', 'UKM', 'USM', 'UPM', 'UCSI', 'MONASH', 'MAHSA'],
                'cheap': ['UKM', 'USM', 'UPM', 'IIUM', 'UNIMAP']
            },
            'دراسة-الذكاء-الاصطناعي-في-ماليزيا': {
                'best': ['APU', 'UTM', 'MMU', 'Taylor\'s', 'MONASH'],
                'cheap': ['UUM', 'UTHM', 'UNIMAP', 'UniMAS', 'IIUM']
            },
            'دراسة-الرسوم-المتحركة': {
                'best': ['MMU', 'APU', 'Limkokwing', 'Taylor\'s'],
                'cheap': ['UTHM', 'UniMAS', 'UiTM']
            },
            'دراسة-الصحة-العامة-في-ماليزيا': {
                'best': ['UM', 'UKM', 'UPM', 'USM'],
                'cheap': ['UKM', 'UPM', 'USM']
            },
            'دراسة-الصيدلة-في-ماليزيا-صيدلة-سريرية': {
                'best': ['Taylor\'s', 'MONASH', 'UCSI', 'Nottingham', 'USM', 'UKM'],
                'cheap': ['USM', 'UKM', 'IIUM', 'UniKL']
            },
            'دراسة-الطب-البشري-في-ماليزيا': {
                'best': ['UM', 'UKM', 'USM', 'MONASH', 'Taylor\'s', 'UCSI', 'UoC'],
                'cheap': ['UKM', 'USM', 'UiTM', 'MSU']
            },
            'دراسة-العلاج-الطبيعي-في-ماليزيا-العلا': {
                'best': ['MAHSA', 'UCSI', 'UoC', 'MSU', 'INTI'],
                'cheap': ['UniKL', 'UTAR', 'MSU']
            },
            'دراسة-العلاقات-الدولية': {
                'best': ['MONASH', 'Nottingham', 'HELP', 'Taylor\'s', 'APU'],
                'cheap': ['UTAR', 'UUM', 'UKM', 'IIUM']
            },
            'دراسة-علاقات-عامة': {
                'best': ['UTAR', 'Taylor\'s', 'MSU', 'Sunway'],
                'cheap': ['UTAR', 'UUM', 'IIUM', 'UniMAS']
            },
            'دراسة-العلوم-الإنسانية-والاجتماعية-ف': {
                'best': ['UM', 'USM', 'UKM', 'Nottingham', 'MONASH'],
                'cheap': ['UUM', 'UTHM', 'UniMAS', 'IIUM']
            },
            'دراسة-العلوم-في-ماليزيا-رسوم-الدراسة-و': {
                'best': ['Sunway', 'APU', 'UCSI', 'Taylor\'s', 'UTAR', 'UM'],
                'cheap': ['UTAR', 'UUM', 'UKM', 'USM', 'IIUM']
            },
            'دراسة-العلوم-البيئية-في-ماليزيا': {
                'best': ['UM', 'USM', 'UKM', 'UPM', 'Nottingham', 'MONASH'],
                'cheap': ['UUM', 'UTHM', 'UniMAS', 'IIUM']
            },
            'دراسة-الفندقه-والسياحه-في-ماليزيا': {
                'best': ['Taylor\'s', 'Sunway', 'UCSI', 'MSU'],
                'cheap': ['UUM', 'UiTM', 'UTHM', 'UniMAS']
            },
            'دراسة-القانون-في-ماليزيا': {
                'best': ['UM', 'UKM', 'UUM', 'Taylor\'s'],
                'cheap': ['UUM', 'UKM', 'IIUM']
            },
            'اللوجستيات-وسلسلة-التوريد': {
                'best': ['Taylor\'s', 'APU', 'UCSI', 'UPM', 'MSU'],
                'cheap': ['UUM', 'UTHM', 'UTeM', 'UniMAS', 'IIUM']
            },
            'دراسة-المحاسبة-في-ماليزيا': {
                'best': ['Taylor\'s', 'Sunway', 'MONASH', 'UCSI', 'UUM', 'UKM'],
                'cheap': ['UUM', 'UTAR', 'UTHM', 'UniMAS', 'IIUM']
            },
            'دراسة-المختربات-الطبية-في-ماليزيا': {
                'best': ['UKM', 'USM', 'UPM', 'MSU', 'MAHSA'],
                'cheap': ['UKM', 'USM', 'UPM']
            },
            'الموسيقى': {
                'best': ['UCSI', 'Sunway', 'UM'],
                'cheap': ['UiTM', 'UniMAS', 'UUM']
            },
            'النانو-تكنولوجي': {
                'best': ['MONASH', 'Nottingham', 'UTM', 'UM'],
                'cheap': ['UTM', 'UKM', 'USM', 'IIUM', 'UNIMAP']
            },
            'دراسة-الهندسة-الإلكترونية-في-ماليزيا': {
                'best': ['UTM', 'MMU', 'APU', 'Nottingham', 'MONASH'],
                'cheap': ['UTHM', 'UTeM', 'UNIMAP', 'UniMAS']
            },
            'الهندسة-الصناعية': {
                'best': ['UTM', 'UPM', 'UCSI'],
                'cheap': ['UTHM', 'UTeM', 'UniMAS']
            },
            'دراسة-الهندسة-الطبية-الحيوية': {
                'best': ['UM', 'UTM', 'UPM'],
                'cheap': ['UTM', 'UPM']
            },
            'دراسة-الهندسة-في-ماليزيا-رسوم-الدراسة': {
                'best': ['UM', 'UTM', 'USM', 'Taylor\'s', 'Nottingham'],
                'cheap': ['UTHM', 'UTeM', 'UNIMAP', 'UniMAS']
            },
            'دراسة-الهندسة-الكهربائية-في-ماليزيا-ر': {
                'best': ['UTM', 'UPM', 'Nottingham', 'MONASH', 'APU'],
                'cheap': ['UTHM', 'UTeM', 'UNIMAP', 'UniMAS']
            },
            'دراسة-الهندسة-الكيميائية-في-ماليزيا-ر': {
                'best': ['UTP', 'UTM', 'USM', 'Nottingham', 'MONASH'],
                'cheap': ['UTHM', 'UTeM', 'UNIMAP', 'UniMAS']
            },
            'دراسة-الهندسة-المالية-في-ماليزيا': {
                'best': ['MMU', 'Taylor\'s', 'APU'],
                'cheap': ['UTAR', 'UUM']
            },
            'دراسة-الهندسة-المدنية-في-ماليزيا-رسوم': {
                'best': ['UTM', 'USM', 'Nottingham', 'MONASH'],
                'cheap': ['UTHM', 'UTeM', 'UNIMAP', 'UniMAS']
            },
            'الهندسة-المعمارية': {
                'best': ['UTM', 'UM', 'USM', 'Taylor\'s'],
                'cheap': ['UTHM', 'UTeM', 'UNIMAP', 'UniMAS']
            },
            'دراسة-الهندسة-الميكانيكية-في-ماليزيا': {
                'best': ['UTM', 'UPM', 'Nottingham', 'MONASH', 'APU'],
                'cheap': ['UTHM', 'UTeM', 'UNIMAP', 'UniMAS']
            },
            'الهندسة-النووية': {
                'best': ['UTM'],
                'cheap': ['UTM']
            },
            'الوسائط-المتعددة': {
                'best': ['MMU', 'APU', 'Limkokwing', 'Taylor\'s'],
                'cheap': ['UTHM', 'UTeM', 'UniMAS']
            },
            'تصميم-الأزياء': {
                'best': ['Limkokwing', 'Taylor\'s', 'UCSI'],
                'cheap': ['UiTM', 'MSU']
            },
            'دراسة-تصميم-الجرافيك-في-ماليزيا': {
                'best': ['Taylor\'s', 'Sunway', 'MMU', 'APU', 'Limkokwing'],
                'cheap': ['UUM', 'UTHM', 'UniMAS']
            },
            'دراسة-تكنولوجيا-المعلومات-في-ماليزيا': {
                'best': ['APU', 'UTM', 'MMU', 'Taylor\'s', 'MONASH'],
                'cheap': ['UUM', 'UTHM', 'UNIMAP', 'UniMAS', 'IIUM']
            },
            'دراسة-إدارة-الأعمال-في-ماليزيا-رسوم-ال': {
                'best': ['Taylor\'s', 'Sunway', 'MONASH', 'UUM', 'UKM', 'APU'],
                'cheap': ['UUM', 'UTHM', 'UniMAS', 'IIUM']
            },
            'دراسة-إدارة-الفنادق-والضيافة': {
                'best': ['Taylor\'s', 'Sunway', 'UCSI', 'MSU'],
                'cheap': ['UUM', 'UiTM', 'UTHM', 'UniMAS']
            },
            'دراسة-إنتاج-الأفلام-والفيديو': {
                'best': ['MMU', 'Limkokwing', 'Taylor\'s', 'APU'],
                'cheap': ['UiTM', 'UTHM', 'UniMAS']
            },
            'دراسة-اللغة-الانجليزية-في-ماليزيا-أرخ': {
                'best': ['Nottingham', 'Taylor\'s', 'UM', 'UUM'],
                'cheap': ['UUM', 'UKM', 'IIUM', 'UniMAS']
            },
            'دراسة-الدكتوراه-في-إدارة-الأعمال': {
                'best': ['UPM', 'UKM', 'USM', 'Taylor\'s', 'UCSI', 'APU'],
                'cheap': ['UUM', 'UTHM', 'UniMAS', 'IIUM']
            },
            'دراسة-طب-الأسنان-في-ماليزيا': {
                'best': ['UM', 'UKM', 'USM', 'UiTM', 'SEGi', 'MAHSA', 'Lincoln University'],
                'cheap': ['UKM', 'USM', 'UiTM']
            },
            'دراسة-طب-الأشعة-في-ماليزيا-التصوير-الط': {
                'best': ['UM', 'UKM', 'UPM', 'MONASH'],
                'cheap': ['UKM', 'UPM']
            },
            'دراسة-علم-الأحياء-في-ماليزيا': {
                'best': ['UM', 'USM', 'UKM', 'UPM', 'MONASH'],
                'cheap': ['UUM', 'UTHM', 'UniMAS', 'IIUM']
            },
            'دراسة-علم-النفس': {
                'best': ['MONASH', 'Nottingham', 'Sunway', 'HELP', 'Taylor\'s', 'UCSI'],
                'cheap': ['UTAR', 'UUM', 'UKM', 'IIUM', 'UniMAS']
            },
            'علوم-البيانات': {
                'best': ['APU', 'UTM', 'MMU', 'Taylor\'s', 'MONASH'],
                'cheap': ['UUM', 'UTHM', 'UNIMAP', 'UniMAS', 'IIUM']
            },
            'علوم-الحاسوب': {
                'best': ['APU', 'UTM', 'MMU', 'Taylor\'s', 'MONASH'],
                'cheap': ['UUM', 'UTHM', 'UNIMAP', 'UniMAS', 'IIUM']
            },
            'دراسة-العلوم-الرياضية-في-ماليزيا': {
                'best': ['UM', 'UPM', 'USM', 'UKM', 'MSU', 'MAHSA', 'UTAR'],
                'cheap': ['UPM', 'USM', 'UKM', 'UTHM', 'UniMAS']
            },
            'دراسة-علوم-مالية-ومصرفية-في-ماليزيا': {
                'best': ['Taylor\'s', 'Sunway', 'MONASH', 'UCSI', 'UUM', 'UKM', 'APU'],
                'cheap': ['UUM', 'UTAR', 'UTHM', 'UniMAS', 'IIUM']
            },
            'دراسة-ماجستير-إدارة-الأعمال-في-ماليزي': {
                'best': ['UM', 'UKM', 'UPM', 'USM', 'MONASH', 'Taylor\'s', 'Sunway', 'APU'],
                'cheap': ['UUM', 'UTHM', 'UniMAS', 'IIUM']
            },
            'دراسة-هندسة-الاتصالات-في-ماليزيا-رسوم': {
                'best': ['UTM', 'MMU', 'Taylor\'s', 'APU', 'UCSI'],
                'cheap': ['UTHM', 'UTeM', 'UNIMAP', 'UniMAS', 'IIUM']
            },
            'دراسة-هندسة-البترول-في-ماليزيا-رسوم-ال': {
                'best': ['UTP', 'UTM', 'APU'],
                'cheap': ['UTP', 'UTM', 'APU']
            },
            'دراسة-هندسة-البرمجيات-ماليزيا': {
                'best': ['APU', 'UTM', 'MMU', 'Taylor\'s', 'MONASH'],
                'cheap': ['UUM', 'UTHM', 'UNIMAP', 'UniMAS', 'IIUM']
            },
            'دراسة-هندسة-الروبوتات-في-ماليزيا': {
                'best': ['APU', 'UTM', 'MMU', 'MONASH'],
                'cheap': ['UTHM', 'UTeM', 'UNIMAP', 'UniMAS']
            },
            'دراسة-هندسة-الزراعة-في-ماليزيا-رسوم-ال': {
                'best': ['UPM'],
                'cheap': ['UPM']
            },
            'دراسة-هندسة-الطيران-في-ماليزيا-إدارة-ا': {
                'best': ['UPM', 'USM', 'UTM', 'Nottingham'],
                'cheap': ['UPM', 'USM', 'UTM']
            },
            'دراسة-هندسة-الكمبيوتر-في-ماليزيا-رسوم': {
                'best': ['APU', 'UTM', 'MMU', 'MONASH'],
                'cheap': ['UTHM', 'UTeM', 'UNIMAP', 'UniMAS']
            },
            'دراسة-هندسة-المعدات-الطبية': {
                'best': ['UTM', 'UM', 'UPM'],
                'cheap': ['UTM', 'UPM']
            },
            'دراسة-هندسة-الميكاترونيك': {
                'best': ['APU', 'UTM', 'MMU', 'MONASH', 'Nottingham'],
                'cheap': ['UTHM', 'UTeM', 'UNIMAP', 'UniMAS']
            }
        }

        def get_uni_instance(abbr):
            abbr_lower = abbr.lower()
            if abbr_lower == 'um':
                return University.objects.filter(slug__icontains='-um-').first() or University.objects.filter(name__icontains='مالايا').first()
            elif abbr_lower == 'utp':
                return University.objects.filter(name__icontains='بتروناس').first() or University.objects.filter(slug__icontains='utp').first()
            elif abbr_lower == 'unimap':
                return University.objects.filter(name__icontains='برليس').first() or University.objects.filter(slug__icontains='unimap').first()
            elif abbr_lower == 'upm':
                return University.objects.filter(name__icontains='بوترا').first() or University.objects.filter(slug__icontains='upm').first()
            elif 'taylor' in abbr_lower:
                return University.objects.filter(name__icontains='تايلور').first() or University.objects.filter(slug__icontains='taylor').first()
            elif abbr_lower == 'uniten':
                return University.objects.filter(name__icontains='تناجا').first() or University.objects.filter(slug__icontains='tenaga').first()
            elif abbr_lower == 'utar':
                return University.objects.filter(name__icontains='تونكو عبد الرحمن').first() or University.objects.filter(slug__icontains='utar').first()
            elif abbr_lower == 'unimas':
                return University.objects.filter(name__icontains='ساراواك').first() or University.objects.filter(slug__icontains='unimas').first()
            elif abbr_lower == 'uoc':
                return University.objects.filter(name__icontains='سايبرجايا').first() or University.objects.filter(slug__icontains='uoc').first()
            elif abbr_lower == 'city':
                return University.objects.filter(name__icontains='سيتي').first() or University.objects.filter(slug__icontains='city').first()
            elif abbr_lower == 'segi':
                return University.objects.filter(name__icontains='سيجي').first() or University.objects.filter(slug__icontains='segi').first()
            elif abbr_lower == 'sunway':
                return University.objects.filter(name__icontains='سانوي').first() or University.objects.filter(name__icontains='صنواي').first() or University.objects.filter(slug__icontains='sunway').first()
            elif abbr_lower == 'unikl':
                return University.objects.filter(name__icontains='كوالالمبور').first() or University.objects.filter(slug__icontains='unikl').first()
            elif abbr_lower == 'limkokwing':
                return University.objects.filter(name__icontains='ليمكوكوينج').first() or University.objects.filter(slug__icontains='limkokwing').first()
            elif abbr_lower == 'lincoln':
                return University.objects.filter(name__icontains='لينكولن').first() or University.objects.filter(slug__icontains='lincoln').first()
            elif abbr_lower == 'uitm':
                return University.objects.filter(name__icontains='مارا').first() or University.objects.filter(slug__icontains='uitm').first()
            elif abbr_lower == 'utem':
                return University.objects.filter(name__icontains='ملاكا').first() or University.objects.filter(slug__icontains='utem').first()
            elif abbr_lower == 'monash':
                return University.objects.filter(name__icontains='موناش').first() or University.objects.filter(slug__icontains='monash').first()
            elif abbr_lower == 'nottingham':
                return University.objects.filter(name__icontains='نوتنجهام').first() or University.objects.filter(slug__icontains='nottingham').first()
            elif abbr_lower == 'help':
                return University.objects.filter(name__icontains='هيلب').first() or University.objects.filter(name__icontains='help').first() or University.objects.filter(slug__icontains='help').first()
            
            res = University.objects.filter(slug__icontains=abbr_lower).first()
            if not res:
                res = University.objects.filter(name__icontains=abbr).first()
            return res

        report_lines = []
        report_lines.append("# تقرير محاكاة ربط الجامعات بالتخصصات (University Mapping Report)")
        report_lines.append(f"**حالة التشغيل**: {'محاكاة (Dry Run)' if dry_run else 'تطبيق فعلي (Commit)'}")
        report_lines.append("")
        report_lines.append("| الرقم | اسم التخصص | حقل أفضل الجامعات (المقترح) | حقل الجامعات الاقتصادية (المقترح) | حالة التحديث |")
        report_lines.append("|---|---|---|---|---|")

        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for idx, (slug, data) in enumerate(MAPPING.items(), 1):
                try:
                    major = Major.objects.get(slug=slug)
                except Major.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Major not found for slug: {slug}"))
                    continue

                best_added = []
                cheap_added = []

                best_unis_instances = []
                best_action = "مكتمل مسبقاً"
                if major.best_universities.count() == 0:
                    best_action = "جاري الربط"
                    for abbr in data['best']:
                        uni = get_uni_instance(abbr)
                        if uni:
                            best_unis_instances.append(uni)
                            best_added.append(uni.name)
                        else:
                            self.stdout.write(self.style.ERROR(f"University abbreviation '{abbr}' not resolved!"))
                else:
                    best_added = [u.name for u in major.best_universities.all()]

                cheap_unis_instances = []
                cheap_action = "مكتمل مسبقاً"
                if major.cheap_universities.count() == 0:
                    cheap_action = "جاري الربط"
                    for abbr in data['cheap']:
                        uni = get_uni_instance(abbr)
                        if uni:
                            cheap_unis_instances.append(uni)
                            cheap_added.append(uni.name)
                        else:
                            self.stdout.write(self.style.ERROR(f"University abbreviation '{abbr}' not resolved!"))
                else:
                    cheap_added = [u.name for u in major.cheap_universities.all()]

                if best_action == "جاري الربط" or cheap_action == "جاري الربط":
                    update_status_str = "تم الربط" if commit else "مقترح للربط"
                    updated_count += 1
                else:
                    update_status_str = "تخطي (يحتوي بيانات)"
                    skipped_count += 1

                if commit:
                    if best_unis_instances:
                        major.best_universities.add(*best_unis_instances)
                    if cheap_unis_instances:
                        major.cheap_universities.add(*cheap_unis_instances)

                best_str = "، ".join(best_added) if best_added else "لا يوجد"
                cheap_str = ".. ".join(cheap_added) if cheap_added else "لا يوجد"
                report_lines.append(f"| {idx} | {major.name} | {best_str} | {cheap_str} | {update_status_str} |")

            if dry_run:
                transaction.set_rollback(True)

        report_file = os.path.join(os.getcwd(), 'majors_audit_updates.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))

        self.stdout.write(self.style.SUCCESS(f"\nCompleted universities mapping. Updated: {updated_count}, Skipped: {skipped_count}"))
        self.stdout.write(self.style.SUCCESS(f"Report written to: {report_file}"))
