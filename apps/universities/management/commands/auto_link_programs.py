"""
Management command to auto-link University Programs to Majors.
أمر إداري لربط وتحديث حقول التخصص المرتبط لجميع البرامج الجامعية آلياً وبدقة متناهية.
"""
import re
from collections import Counter
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.majors.models import Major
from apps.universities.models import Program


class Command(BaseCommand):
    help = 'Auto-link university programs to their most accurate major based on program name.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--commit',
            action='store_true',
            help='Save changes to the database (defaults to dry-run simulation mode).'
        )
        parser.add_argument(
            '--verbose-samples',
            type=int,
            default=15,
            help='Number of sample results to print.'
        )

    def handle(self, *args, **options):
        commit = options['commit']
        verbose_samples = options['verbose_samples']

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"=== {'EXECUTION MODE (COMMIT)' if commit else 'SIMULATION MODE (DRY RUN)'} ==="
        ))

        all_majors = list(Major.objects.all())
        majors_by_id = {m.id: m for m in all_majors}

        # Rules ordered by (Major ID, Priority, Patterns)
        rules = [
            # ─── 1. SPECIALIZED COMPUTING & IT ───
            (64, 100, [
                r'\b(cyber\s*security|information\s*security|network\s*security|computer\s*security|digital\s*forensics?|cloud\s*security)\b',
                r'(أمن\s*(المعلومات|السيبراني|الشبكات|الحاسوب)|التحقيق\s*الجنائي\s*الرقمي)'
            ]),
            (114, 100, [
                r'\b(data\s*science|data\s*analytics|big\s*data|business\s*analytics|data\s*engineering)\b',
                r'(علوم\s*البيانات|تحليل\s*البيانات|البيانات\s*الضخمة|ذكاء\s*الأعمال\s*وتحليل\s*البيانات)'
            ]),
            (74, 100, [
                r'\b(artificial\s*intelligence|machine\s*learning|deep\s*learning|intelligent\s*systems?)\b',
                r'(الذكاء\s*الاصطناعي|تعلم\s*الآلة|الأنظمة\s*الذكية)'
            ]),
            (120, 95, [
                r'\b(software\s*engineering|software\s*development|software\s*technology)\b',
                r'(هندسة\s*البرمجيات|تطوير\s*البرمجيات|تقنية\s*البرمجيات)'
            ]),
            (75, 95, [
                r'\b(3d\s*animation|animation\s*and|digital\s*animation|visual\s*effects|vfx|\banimation\b)\b',
                r'(الرسوم\s*المتحركة|الأنيميشن|المؤثرات\s*البصرية|الرسوم\s*ثلاثية\s*الأبعاد)'
            ]),
            (105, 90, [
                r'\b(multimedia|interactive\s*media|games?\s*development|game\s*design|digital\s*media|game\s*technology|games?\s*software|creative\s*multimedia|digital\s*games?)\b',
                r'(الوسائط\s*المتعددة|تطوير\s*الألعاب|تصميم\s*الألعاب|الميديا\s*التفاعلية|الوسائط\s*الرقمية)'
            ]),
            (107, 90, [
                r'\b(graphic\s*design|visual\s*communication\s*design|advertising\s*design|creative\s*advertising|creative\s*design|visual\s*arts?)\b',
                r'(تصميم\s*الجرافيك|التصميم\s*الجرافيكي|التصميم\s*المرئي|تصميم\s*الإعلانات|الفنون\s*البصرية)'
            ]),
            (124, 88, [
                r'\b(computer\s*engineering|computer\s*systems\s*engineering|computer\s*and\s*communication\s*engineering|computer\s*system\s*and\s*networking|computer\s*network\s*engineering)\b',
                r'(هندسة\s*الكمبيوتر|هندسة\s*الحاسوب|هندسة\s*أنظمة\s*الحاسوب|هندسة\s*شبكات\s*الحاسوب)'
            ]),
            (115, 85, [
                r'\b(computer\s*science|computing|computer\s*studies)\b',
                r'(علوم\s*الحاسوب|علوم\s*الحاسب|علوم\s*الكمبيوتر|الحوسبة)'
            ]),
            (108, 80, [
                r'\b(information\s*technology|infotech|information\s*systems|business\s*information\s*systems|it\s*management|technology\s*management|information\s*science)\b',
                r'(تكنولوجيا\s*المعلومات|تقنية\s*المعلومات|نظم\s*المعلومات|إدارة\s*التكنولوجيا|علم\s*المعلومات)'
            ]),

            # ─── 2. SPECIALIZED ENGINEERING ───
            (121, 95, [
                r'\b(robotics|robotics\s*and\s*automation|robotic\s*engineering)\b',
                r'(هندسة\s*الروبوتات|الروبوتات|الروبوت|الأنظمة\s*الروبوتية)'
            ]),
            (126, 95, [
                r'\b(mechatronics|mechatronic\s*engineering|electromechanical\s*engineering)\b',
                r'(هندسة\s*الميكاترونيك|الميكاترونكس|ميكاترونيك|كهروميكانيكية)'
            ]),
            (96, 95, [
                r'\b(biomedical\s*engineering|bioengineering|biological\s*engineering|bioprocess\s*engineering)\b',
                r'(هندسة\s*الطبية\s*الحيوية|الهندسة\s*الحيوية|هندسة\s*طبية\s*حيوية|هندسة\s*العمليات\s*الحيوية)'
            ]),
            (125, 95, [
                r'\b(medical\s*electronic\s*engineering|clinical\s*engineering|medical\s*instrumentation|medical\s*device)\b',
                r'(هندسة\s*المعدات\s*الطبية|الأجهزة\s*الطبية|إلكترونيات\s*طبية)'
            ]),
            (119, 95, [
                r'\b(petroleum\s*engineering|petroleum\s*geoscience|oil\s*and\s*gas|drilling\s*engineering|offshore\s*engineering)\b',
                r'(هندسة\s*البترول|هندسة\s*النفط\s*والغاز|علوم\s*البترول|الهندسة\s*البحرية\s*والبترولية)'
            ]),
            (123, 95, [
                r'\b(aerospace\s*engineering|aeronautical\s*engineering|aircraft\s*maintenance|aviation\s*management|aviation\s*engineering|avionics|aircraft\s*engineering)\b',
                r'(هندسة\s*الطيران|هندسة\s*الفضاء|صيانة\s*الطائرات|إدارة\s*الطيران|إلكترونيات\s*الطيران)'
            ]),
            (98, 92, [
                r'\b(chemical\s*engineering|petrochemical\s*engineering|polymer\s*engineering|chemical\s*process|biochemical\s*engineering|oleochemical|material\s*engineering|materials?\s*science\s*and\s*engineering)\b',
                r'(هندسة\s*كيميائية|الهندسة\s*الكيميائية|هندسة\s*البتروكيماويات|هندسة\s*البوليمرات|هندسة\s*المواد)'
            ]),
            (100, 92, [
                r'\b(civil\s*engineering|construction\s*engineering|structural\s*engineering|quantity\s*surveying|building\s*surveying|construction\s*management|infrastructure\s*engineering|geotechnical\s*engineering|highway\s*engineering)\b',
                r'(هندسة\s*مدنية|الهندسة\s*المدنية|هندسة\s*التشييد|هندسة\s*البناء|حساب\s*الكميات|إدارة\s*المشاريع\s*الإنشائية|هندسة\s*التربة\s*والأساسات)'
            ]),
            (102, 90, [
                r'\b(mechanical\s*engineering|automotive\s*engineering|motorsport\s*engineering|marine\s*engineering|naval\s*architecture|thermofluid|energy\s*engineering)\b',
                r'(هندسة\s*ميكانيكية|الهندسة\s*الميكانيكية|هندسة\s*السيارات|هندسة\s*المحركات|الهندسة\s*البحرية|هندسة\s*الطاقة)'
            ]),
            (95, 88, [
                r'\b(industrial\s*engineering|manufacturing\s*engineering|production\s*engineering|manufacturing\s*technology)\b',
                r'(هندسة\s*صناعية|الهندسة\s*الصناعية|هندسة\s*التصنيع|هندسة\s*الإنتاج)'
            ]),
            (97, 88, [
                r'\b(electrical\s*engineering|electrical\s*and\s*electronic|electrical\s*power|power\s*systems?\s*engineering|high\s*voltage|electrical\s*systems?\s*engineering)\b',
                r'(هندسة\s*كهربائية|الهندسة\s*الكهربائية|هندسة\s*القوى\s*الكهربائية|كهرباء\s*وإلكترونيات|هندسة\s*أنظمة\s*كهربائية)'
            ]),
            (118, 88, [
                r'\b(telecommunication\s*engineering|telecommunications?|network\s*engineering|communication\s*engineering)\b',
                r'(هندسة\s*الاتصالات|هندسة\s*شبكات|هندسة\s*الاتصالات\s*والشبكات)'
            ]),
            (93, 85, [
                r'\b(electronic\s*engineering|microelectronics?|microelectronic\s*engineering|semiconductor|vlsi|applied\s*electronics)\b',
                r'(هندسة\s*إلكترونية|الهندسة\s*الإلكترونية|الإلكترونيات\s*الدقيقة|الإلكترونيات\s*التطبيقية)'
            ]),
            (101, 88, [
                r'\b(architecture|architectural\s*studies|interior\s*architecture|landscape\s*architecture|interior\s*design|urban\s*planning|town\s*planning)\b',
                r'(هندسة\s*معمارية|الهندسة\s*المعمارية|العمارة|التصميم\s*الداخلي|عمارة\s*البيئة|التخطيط\s*العمراني)'
            ]),
            (127, 88, [
                r'\b(environmental\s*engineering|water\s*resources\s*engineering)\b',
                r'(هندسة\s*بيئية|الهندسة\s*البيئية|هندسة\s*الموارد\s*المائية)'
            ]),
            (103, 90, [
                r'\b(nuclear\s*engineering|nuclear\s*science)\b',
                r'(هندسة\s*نووية|العلوم\s*النووية)'
            ]),
            (122, 85, [
                r'\b(agricultural\s*engineering|agricultural\s*science|agriculture|agronomy|horticulture|plantation\s*management|agribusiness|crop\s*science|soil\s*science|forestry|animal\s*science|veterinary)\b',
                r'(هندسة\s*الزراعة|العلوم\s*الزراعية|الزراعة|البساتين|إدارة\s*المزارع|وقاية\s*النبات|الغابات|الإنتاج\s*الحيواني|البيطرة)'
            ]),
            (99, 90, [
                r'\b(financial\s*engineering|quantitative\s*finance)\b',
                r'(هندسة\s*مالية|الهندسة\s*المالية)'
            ]),
            (104, 50, [
                r'\b(general\s*engineering|engineering\s*\(general\)|applied\s*engineering|engineering\s*technology)\b',
                r'(الهندسة\s*العامة|هندسة\s*عامة|تكنولوجيا\s*الهندسة)'
            ]),

            # ─── 3. MEDICAL & HEALTH SCIENCES ───
            (78, 98, [
                r'\b(medicine|surgery|mbbs|medical\s*doctor|clinical\s*medicine|doctor\s*of\s*medicine)\b',
                r'(الطب\s*البشري|طب\s*وجراحة|الطب\s*العام|دكتور\s*في\s*الطب|الطب\s*السريري)'
            ]),
            (110, 98, [
                r'\b(dentistry|dental\s*surgery|dental\s*science|bds|dental\s*technology|oral\s*health|orthodontics|periodontics|prosthodontics|dental)\b',
                r'(طب\s*الأسنان|جراحة\s*الأسنان|طب\s*وجراحة\s*الفم\s*والأسنان|صحة\s*الفم|تقويم\s*الأسنان|علوم\s*الأسنان)'
            ]),
            (77, 98, [
                r'\b(pharmacy|pharmaceutical\s*sciences?|pharmaceutics|clinical\s*pharmacy|pharmacology|pharm\.?\s*d|cosmeceutical|pharmaceutical\s*technology)\b',
                r'(صيدلة|الصيدلة|علوم\s*صيدلانية|صيدلة\s*إكلينيكية|صيدلة\s*سريرية|علم\s*الأدوية|تكنولوجيا\s*صيدلانية)'
            ]),
            (73, 95, [
                r'\b(nursing|nursing\s*science|midwifery)\b',
                r'(تمريض|التمريض|علوم\s*التمريض|القبالة)'
            ]),
            (79, 95, [
                r'\b(physiotherapy|physical\s*therapy|occupational\s*therapy|rehabilitation\s*science|audiology|speech\s*therapy|chiropractic)\b',
                r'(علاج\s*طبيعي|العلاج\s*الطبيعي|العلاج\s*الوظيفي|التأهيل\s*الطبي|السمعيات|علاج\s*النطق)'
            ]),
            (111, 95, [
                r'\b(radiography|medical\s*imaging|medical\s*radiation|radiotherapy|diagnostic\s*imaging|radiation\s*therapy)\b',
                r'(طب\s*الأشعة|التصوير\s*الطبي|أشعة\s*تشخيصية|علاج\s*إشعاعي|علوم\s*الأشعة)'
            ]),
            (90, 95, [
                r'\b(medical\s*laboratory|biomedical\s*sciences?|clinical\s*laboratory|medical\s*microbiology|biomedicine|laboratory\s*technology|clinical\s*science)\b',
                r'(مختبرات\s*طبية|المختبرات\s*الطبية|التحاليل\s*الطبية|العلوم\s*الطبية\s*الحيوية|الطب\s*الحيوي)'
            ]),
            (67, 95, [
                r'\b(optometry|vision\s*science|ophthalmic\s*science|orthoptics)\b',
                r'(بصريات|البصريات|علوم\s*الرؤية|فحص\s*البصر)'
            ]),
            (72, 95, [
                r'\b(nutrition|dietetics|food\s*science\s*and\s*nutrition|clinical\s*nutrition|nutritional\s*sciences?|food\s*technology|food\s*science|food\s*biotechnology)\b',
                r'(تغذية|التغذية|علوم\s*الأغذية\s*والتغذية|تغذية\s*علاجية|علم\s*الحميات|تكنولوجيا\s*الأغذية|علوم\s*الأغذية)'
            ]),
            (76, 92, [
                r'\b(public\s*health|occupational\s*safety\s*and\s*health|environmental\s*health|health\s*administration|healthcare\s*management|health\s*science|health\s*services)\b',
                r'(صحة\s*عامة|الصحة\s*العامة|السلامة\s*والصحة\s*المهنية|صحة\s*بيئية|إدارة\s*الرعاية\s*الصحية|العلوم\s*الصحية)'
            ]),

            # ─── 4. BUSINESS, FINANCE, LAW & MANAGEMENT ───
            (117, 98, [
                r'\b(mba|master\s*of\s*business\s*administration)\b',
                r'(ماجستير\s*إدارة\s*الأعمال|mba)'
            ]),
            (109, 98, [
                r'\b(dba|doctor\s*of\s*business\s*administration)\b',
                r'(دكتوراه\s*إدارة\s*الأعمال|dba)'
            ]),
            (89, 95, [
                r'\b(accounting|accountancy|audit|auditing|taxation|forensic\s*accounting|bachelor\s*of\s*accounting)\b',
                r'(محاسبة|المحاسبة|تدقيق\s*حسابات|مراجعة\s*وضرائب|المحاسبة\s*الجنائية)'
            ]),
            (116, 92, [
                r'\b(finance|banking|financial\s*technology|fintech|islamic\s*banking|islamic\s*finance|investment\s*management|financial\s*planning|wealth\s*management|financial\s*mathematics)\b',
                r'(علوم\s*مالية|مصرفية|المالية|البنوك|الصيرفة\s*الإسلامية|التمويل\s*الإسلامي|إدارة\s*الاستثمار|التكنولوجيا\s*المالية|تخطيط\s*مالي|الرياضيات\s*المالية)'
            ]),
            (85, 95, [
                r'\b(actuarial\s*science|actuarial\s*studies|actuarial\s*mathematics|actuary)\b',
                r'(علوم\s*اكتوارية|العلوم\s*الاكتوارية|الرياضيات\s*الاكتوارية|اكتوارية)'
            ]),
            (66, 90, [
                r'\b(economics|applied\s*economics|econometrics|business\s*economics|islamic\s*economics|development\s*economics)\b',
                r'(اقتصاد|الاقتصاد|اقتصاد\s*تطبيقي|اقتصاد\s*قياسي|اقتصاد\s*إسلامي|اقتصاد\s*الأعمال)'
            ]),
            (71, 90, [
                r'\b(marketing|digital\s*marketing|brand\s*management|retail\s*marketing|marketing\s*communications?|advertising\s*and\s*branding)\b',
                r'(تسويق|التسويق|تسويق\s*رقمي|تسويق\s*إلكتروني|إدارة\s*العلامات\s*التجارية|الدعاية\s*والعلامات\s*التجارية)'
            ]),
            (68, 92, [
                r'\b(e-?commerce|electronic\s*commerce|digital\s*business|e-?business)\b',
                r'(تجارة\s*إلكترونية|التجارة\s*الإلكترونية|أعمال\s*رقمية)'
            ]),
            (88, 92, [
                r'\b(logistics|supply\s*chain|procurement|maritime\s*management|transportation\s*management|shipping\s*management)\b',
                r'(لوجستيات|اللوجستيات|سلسلة\s*التوريد|سلاسل\s*الإمداد|إدارة\s*الموانئ|النقل\s*واللوجستيات)'
            ]),
            (128, 92, [
                r'\b(hotel\s*management|hospitality\s*management|culinary\s*arts|food\s*and\s*beverage\s*management|hotel\s*and\s*catering|hospitality)\b',
                r'(إدارة\s*الفنادق|إدارة\s*الضيافة|فنون\s*الطهي|إدارة\s*الفندقة\s*والضيافة|الضيافة)'
            ]),
            (86, 88, [
                r'\b(tourism|tourism\s*management|event\s*management|ecotourism|leisure\s*and\s*tourism|conventions?\s*and\s*events?)\b',
                r'(سياحة|السياحة|الفندقة\s*والسياحة|إدارة\s*السياحة|إدارة\s*الفعاليات|إدارة\s*المؤتمرات)'
            ]),
            (69, 75, [
                r'\b(business\s*administration|human\s*resource|hrm|international\s*business|business\s*management|entrepreneurship|general\s*management|business\s*studies|corporate\s*management|operations\s*management|public\s*management|creative\s*industry\s*management|real\s*estate|property\s*management|business\s*mathematics)\b',
                r'(إدارة\s*الأعمال|الموارد\s*البشرية|الأعمال\s*الدولية|إدارة\s*أعمال|ريادة\s*الأعمال|إدارة\s*الشركات|إدارة\s*العمليات|إدارة\s*عامة|إدارة\s*العقارات)'
            ]),
            (87, 95, [
                r'\b(laws?|llb|llm|jurisprudence|legal\s*studies|syariah\s*and\s*law|sharia\s*and\s*law|commercial\s*law|international\s*law)\b',
                r'(قانون|القانون|الحقوق|شريعة\s*وقانون|علوم\s*قانونية|قانون\s*دولي|قانون\s*تجاري)'
            ]),

            # ─── 5. ARTS, MEDIA, SOCIAL SCIENCES & LANGUAGES ───
            (80, 92, [
                r'\b(international\s*relations|international\s*studies|diplomacy|global\s*affairs|strategic\s*studies)\b',
                r'(علاقات\s*دولية|العلاقات\s*الدولية|دراسات\s*دولية|الدبلوماسية|دراسات\s*استراتيجية)'
            ]),
            (81, 92, [
                r'\b(public\s*relations|corporate\s*communications?)\b',
                r'(علاقات\s*عامة|العلاقات\s*العامة|تواصل\s*مؤسسي)'
            ]),
            (65, 88, [
                r'\b(mass\s*communication|journalism|broadcasting|media\s*studies|media\s*production|publishing|communication\s*studies|communication\s*with|new\s*media|communication)\b',
                r'(اتصال\s*جماهيري|الاتصال\s*الجماهيري|إعلام|الصحافة\s*والإعلام|صحافة|الإذاعة\s*والتلفزيون|دراسات\s*إعلامية|الاتصال)'
            ]),
            (63, 95, [
                r'\b(film\s*production|film\s*and\s*television|cinematography|screen\s*arts|directing|film\s*studies|motion\s*picture)\b',
                r'(إنتاج\s*الأفلام|الأفلام\s*والفيديو|السينما|الإخراج\s*السينمائي|صناعة\s*السينما)'
            ]),
            (106, 95, [
                r'\b(fashion\s*design|textile\s*design|apparel\s*design|fashion\s*merchandising|footwear\s*design|textiles?)\b',
                r'(تصميم\s*الأزياء|تصميم\s*المنسوجات|تصميم\s*الملابس|تسويق\s*الأزياء|المنسوجات)'
            ]),
            (91, 95, [
                r'\b(music|music\s*performance|music\s*production|audio\s*engineering|sound\s*engineering|music\s*composition)\b',
                r'(موسيقى|الموسيقى|الإنتاج\s*الموسيقي|هندسة\s*الصوت|الأداء\s*الموسيقي)'
            ]),
            (113, 95, [
                r'\b(psychology|counselling|behavioral\s*science|clinical\s*psychology|educational\s*psychology)\b',
                r'(علم\s*النفس|الإرشاد\s*النفسي|العلوم\s*السلوكية|علم\s*النفس\s*السريري|علم\s*النفس\s*التربوي)'
            ]),
            (129, 95, [
                r'\b(english\s*language|english\s*literature|tesl|tefl|applied\s*linguistics|translation\s*and\s*interpreting|english\s*for\s*international\s*communication)\b',
                r'(لغة\s*إنجليزية|اللغة\s*الإنجليزية|أدب\s*إنجليزي|تدريس\s*اللغة\s*الإنجليزية|الترجمة\s*الفورية|اللغويات\s*التطبيقية)'
            ]),
            (84, 95, [
                r'\b(sports?\s*science|exercise\s*science|sports?\s*coaching|physical\s*education|sports?\s*management|sports?\s*rehabilitation)\b',
                r'(علوم\s*الرياضة|التربية\s*البدنية|التدريب\s*الرياضي|علوم\s*الحركة|التأهيل\s*الرياضي|الإدارة\s*الرياضية)'
            ]),
            (112, 90, [
                r'\b(biology|biotechnology|microbiology|bioscience|genetics|molecular\s*biology|marine\s*biology|cell\s*biology|biochemistry|biological\s*sciences?)\b',
                r'(علم\s*الأحياء|التقنية\s*الحيوية|التكنولوجيا\s*الحيوية|الأحياء\s*الدقيقة|علم\s*الوراثة|الكيمياء\s*الحيوية|الأحياء\s*البحرية)'
            ]),
            (83, 90, [
                r'\b(environmental\s*science|ecology|aquatic\s*resource|aquaculture|fisheries|marine\s*science|conservation\s*biology)\b',
                r'(العلوم\s*البيئية|علوم\s*البيئة|الاستزراع\s*المائي|علوم\s*المصايد|البيئة\s*والتنوع\s*الحيوي)'
            ]),
            (92, 95, [
                r'\b(nanotechnology|nano\s*science|nano\s*materials)\b',
                r'(النانو\s*تكنولوجي|تقنية\s*النانو|علوم\s*النانو)'
            ]),
            (82, 70, [
                r'\b(humanities|social\s*sciences?|sociology|anthropology|philosophy|history|cultural\s*studies|islamic\s*studies|syariah|quran|hadith|usuluddin|daawah|da’wah|arabic\s*studies|malay\s*studies|chinese\s*studies|malay\s*language|early\s*childhood\s*education|education|education\s*\(|vocational\s*education)\b',
                r'(العلوم\s*الإنسانية|العلوم\s*الاجتماعية|علم\s*الاجتماع|الأنثروبولوجيا|الفلسفة|التاريخ|الدراسات\s*الإسلامية|الشريعة|أصول\s*الدين|الدراسات\s*العربية|الدعوة\s*والقيادة|اللغة\s*الملايوية|تربية\s*الطفولة\s*المبكرة|التربية\s*والتعليم)'
            ]),
        ]

        exclude_patterns = [
            r'^\s*(foundation\s*in\s*(arts|science|general|studies|business|it|engineering)|سنة\s*تحضيرية|السنة\s*التحضيرية)\s*$',
            r'^\s*(general\s*studies|liberal\s*arts|american\s*degree\s*transfer\s*program|interdisciplinary\s*studies)\s*$',
            r'^\s*(intensive\s*english|certificate\s*in\s*english|foundation\s*program)\s*$',
            r'^\s*(doctor\s*of\s*philosophy\s*\(phd\)|phd\s*\(by\s*research\)|doctor\s*of\s*philosophy\s*\(by\s*research\)|master\s*of\s*science\s*\(by\s*research\))\s*$'
        ]

        def match_program_name(name):
            name_lower = name.lower()
            for ep in exclude_patterns:
                if re.search(ep, name_lower, re.IGNORECASE):
                    return None
            sorted_rules = sorted(rules, key=lambda x: x[1], reverse=True)
            for m_id, _, patterns in sorted_rules:
                for pat in patterns:
                    if re.search(pat, name_lower, re.IGNORECASE):
                        return majors_by_id.get(m_id)
            return None

        programs = list(Program.objects.select_related('faculty', 'faculty__university', 'major').all())
        total_count = len(programs)
        matched_count = 0
        none_count = 0
        changed_count = 0
        programs_to_update = []
        major_stats = Counter()

        for p in programs:
            target_major = match_program_name(p.name)
            old_major_id = p.major_id
            new_major_id = target_major.id if target_major else None

            if target_major:
                matched_count += 1
                major_stats[target_major.name] += 1
            else:
                none_count += 1

            if old_major_id != new_major_id:
                changed_count += 1
                p.major = target_major
                programs_to_update.append(p)

        self.stdout.write(self.style.SUCCESS(f"\n[+] Summary Statistics:"))
        self.stdout.write(f"   * Total Programs in Database: {total_count}")
        self.stdout.write(self.style.SUCCESS(f"   * High-Confidence Matched: {matched_count} ({(matched_count/total_count)*100:.1f}%)"))
        self.stdout.write(self.style.WARNING(f"   * Set to None (Doubt / Vague / Generic): {none_count} ({(none_count/total_count)*100:.1f}%)"))
        self.stdout.write(f"   * Total Records Needing Update: {changed_count}")

        if commit:
            self.stdout.write(self.style.MIGRATE_LABEL("\n[*] Applying changes to database..."))
            with transaction.atomic():
                Program.objects.bulk_update(programs_to_update, ['major'], batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"[OK] Successfully updated {len(programs_to_update)} programs in the database!"))
        else:
            self.stdout.write(self.style.NOTICE(f"\n[i] [DRY RUN] No database changes applied. Use --commit to apply changes."))
