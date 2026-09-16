"""
Data migration to seed initial 14 General FAQs into the database.
Uses update_or_create to ensure idempotency across multiple runs.
"""
from django.db import migrations


INITIAL_SEED_FAQS = [
    {
        'id': 'admission-requirements',
        'category': 'admissions',
        'question': 'ما هي شروط ومعدلات القبول للدراسة في الجامعات الماليزية؟',
        'answer': 'تختلف شروط القبول بحسب الجامعة والدرجة العلمية والتخصص؛ بالنسبة لبرامج البكالوريوس، تشترط معظم الجامعات شهادة الثانوية العامة بمعدل لا يقل عن <bdi>60%</bdi> إلى <bdi>70%</bdi> للتخصصات الهندسية والإدارية وتكنولوجيا المعلومات، بينما تتطلب التخصصات الطبية والصيدلانية معدلات أعلى لا تقل عن <bdi>80%</bdi> إلى <bdi>85%</bdi>. أما لمرحلة الماجستير فيُشترط الحصول على شهادة بكالوريوس بمعدل تراكمي <bdi>(CGPA 2.50 / 4.00)</bdi> كحد أدنى. يمكنك استكشاف تفاصيل الشروط لكل تخصص عبر <a href="/majors/" class="faq-link">دليل التخصصات الدراسية</a>.',
        'featured': True,
    },
    {
        'id': 'required-documents',
        'category': 'admissions',
        'question': 'ما هي المستندات الرسمية المطلوبة للتقديم واستخراج القبول؟',
        'answer': 'المستندات الأساسية المطلوبة للتقديم تشمل: نسخة واضحة وملونة من جميع صفحات جواز السفر (صالح لمدة لا تقل عن 18 شهراً)، كشف علامات وشهادة الثانوية العامة باللغة الإنجليزية أو مترجمة ومصدقة، صور شخصية بخلفية بيضاء، وشهادة إتقان اللغة الإنجليزية <bdi>(IELTS / TOEFL)</bdi> إن وُجدت. لمرحلة الدراسات العليا يُضاف السيرة الذاتية، خطاب التوصية، ومقترح البحث لطلاب الدكتوراه.',
        'featured': False,
    },
    {
        'id': 'academic-intakes',
        'category': 'admissions',
        'question': 'كم يستغرق استخراج القبول الجامعي وما هي مواعيد الفصول الدراسية؟',
        'answer': 'يستغرق استخراج القبول المبدئي في الجامعات الخاصة من <bdi>3</bdi> إلى <bdi>7</bdi> أيام عمل، بينما يتطلب في الجامعات الحكومية من <bdi>2</bdi> إلى <bdi>4</bdi> أسابيع. تتوزع الفصول الدراسية الرئيسية في ماليزيا على مدار العام: الفصول الأساسية تبدأ في (فبراير / مارس) و (سبتمبر / أكتوبر)، بالإضافة إلى فصول إضافية في (مايو / يوليو) في عدة جامعات.',
        'featured': False,
    },
    {
        'id': 'visa-process',
        'category': 'visa',
        'question': 'ما هي خطوات وإجراءات استخراج فيزا الطالب لماليزيا (eVAL)؟',
        'answer': 'تبدأ الإجراءات بعد صدور القبول الجامعي بتقديم ملف التأشيرة إلى هيئة <bdi>(EMGS)</bdi> الحكومية وإجراء الفحص الطبي في بلد الطالب. تصدر موافقة التأشيرة الإلكترونية <bdi>(eVAL)</bdi> خلال <bdi>3-6</bdi> أسابيع، ليقوم الطالب بعدها باستخراج تأشيرة الدخول المفردة <bdi>(SEV)</bdi> والسفر إلى ماليزيا. يمكنك متابعة حالة ملفك لحظة بلحظة عبر <a href="/visa-tracking/" class="faq-link">نظام تتبع الفيزا</a>.',
        'featured': True,
    },
    {
        'id': 'visa-approval-timeline',
        'category': 'visa',
        'question': 'كم تستغرق موافقة الفيزا الدراسية وما هي نسبة قبولها؟',
        'answer': 'تستغرق معالجة التأشيرة لدى دائرة الهجرة وهيئة <bdi>EMGS</bdi> من <bdi>3</bdi> إلى <bdi>6</bdi> أسابيع في المتوسط. وتبلغ نسبة قبول تأشيرات الطلاب في ماليزيا أكثر من <bdi>98%</bdi> عند اكتمال المستندات وسلامة الفحص الطبي وصلاحية جواز السفر.',
        'featured': False,
    },
    {
        'id': 'family-dependent-visa',
        'category': 'visa',
        'question': 'هل يمكن لولي الأمر أو عائلة الطالب مرافقته والإقامة في ماليزيا؟',
        'answer': 'نعم، يتيح قانون الهجرة الماليزي لطلاب الدراسات العليا (الماجستير والدكتوراه) استقدام الزوج/الزوجة والأبناء بتأشيرة مرافق <bdi>(Dependent Visa)</bdi>. كما يمكن لأولياء أمور طلاب المدارس والمعاهد تحت سن <bdi>18</bdi> عاماً الحصول على تأشيرة ولي أمر <bdi>(Guardian Visa)</bdi>.',
        'featured': False,
    },
    {
        'id': 'tuition-fees-overview',
        'category': 'costs',
        'question': 'كم تبلغ الرسوم الدراسية السنوية في الجامعات والمعاهد الماليزية؟',
        'answer': 'تعتبر ماليزيا من أكثر الوجهات الاقتصادية جودة؛ حيث تتراوح رسوم البكالوريوس بين <bdi>3,500$</bdi> و <bdi>8,000$</bdi> سنوياً لمعظم التخصصات الهندسية والإدارية، وبين <bdi>15,000$</bdi> و <bdi>25,000$</bdi> سنوياً للطب البشري وطب الأسنان. أما دورات اللغة الإنجليزية فتتراوح بين <bdi>450$</bdi> و <bdi>750$</bdi> شهرياً. للمزيد تفضل بزيارة <a href="/institutes/" class="faq-link">دليل معاهد اللغة</a>.',
        'featured': True,
    },
    {
        'id': 'living-costs-malaysia',
        'category': 'costs',
        'question': 'ما هو متوسط تكلفة المعيشة والسكن الشهري للطالب في ماليزيا؟',
        'answer': 'يحتاج الطالب الدولي في المتوسط بين <bdi>400$</bdi> و <bdi>700$</bdi> شهرياً (حوالي <bdi>1,800</bdi> إلى <bdi>3,200</bdi> رينجت ماليزي MYR). يغطي هذا المبلغ السكن الجامعي أو الخارجي المشترك، الوجبات، المواصلات العامة وشبكة القطارات الحديثة، وفواتير الاتصالات والإنترنت.',
        'featured': True,
    },
    {
        'id': 'part-time-work',
        'category': 'costs',
        'question': 'هل يُسمح للطلاب الدوليين بالعمل الجزئي أثناء فترة دراستهم؟',
        'answer': 'تسمح القوانين الماليزية للطلاب الدوليين بالعمل بدوام جزئي بحد أقصى <bdi>20</bdi> ساعة أسبوعياً خلال الإجازات الفصلية والعطلات الرسمية التي تزيد عن <bdi>7</bdi> أيام، وذلك في قطاعات محددة (المطاعم، المتاجر، محطات الوقود، والفنادق) بعد أخذ موافقة إدارة الجامعة ودائرة الهجرة.',
        'featured': False,
    },
    {
        'id': 'study-without-ielts',
        'category': 'english',
        'question': 'هل يمكنني الحصول على قبول وبدء الدراسة بدون شهادة آيلتس (IELTS)؟',
        'answer': 'نعم بكل تأكيد؛ تمنح الجامعات الماليزية قبولاً مشروطاً <bdi>(Conditional Offer)</bdi>، حيث يخضع الطالب لاختبار تحديد مستوى للغة الإنجليزية فور وصوله، أو يلتحق بدورة لغة مكثفة في معهد الجامعة أو في أحد <a href="/institutes/" class="faq-link">معاهد اللغة الإنجليزية المعتمدة</a> قبل بدء الدراسة الأكاديمية.',
        'featured': True,
    },
    {
        'id': 'english-institutes-duration',
        'category': 'english',
        'question': 'ما هي مدة دراسة اللغة الإنجليزية المطلوبة للالتحاق بالجامعة؟',
        'answer': 'تعتمد المدة على مستواك الحالي ودرجة الآيلتس المطلوبة لتخصصك (عادة بين <bdi>5.0</bdi> إلى <bdi>6.5</bdi>). تتراوح مدة برامج اللغة الإنجليزية المكثفة بين <bdi>3</bdi> أشهر إلى <bdi>9</bdi> أشهر مقسمة على مستويات شهرية متدرجة.',
        'featured': False,
    },
    {
        'id': 'international-accreditation',
        'category': 'recognition',
        'question': 'هل الشهادات الصادرة من الجامعات الماليزية معترف بها دولياً وعربياً؟',
        'answer': 'نعم؛ تخضع جميع البرامج الأكاديمية لرقابة هيئة الاعتماد الأكاديمي الماليزية <bdi>(MQA)</bdi> ووزارة التعليم العالي الماليزية. كما أن الجامعات الماليزية الشريكة معترف بها في معظم وزارات التعليم العالي العربية ومصنفة ضمن أفضل جامعات العالم في تصنيف <bdi>QS World University Rankings</bdi>. تفضل بالاطلاع على <a href="/universities/" class="faq-link">دليل الجامعات المعتمدة</a>.',
        'featured': False,
    },
    {
        'id': 'public-vs-private-universities',
        'category': 'recognition',
        'question': 'ما الفرق بين الجامعات الحكومية والجامعات الخاصة وفروع الجامعات الأجنبية؟',
        'answer': 'الجامعات الحكومية تمتاز بالرسوم المنخفضة والتصنيف العالمي المتقدم جداً وتتطلب معدلات قبول أعلى ومواعيد تقديم مبكرة. الجامعات الخاصة تتميز بمرونة مواعيد القبول، التدريس باللغة الإنجليزية 100%، وتوفير شراكات دولية وبرامج التبادل (Dual Degree). كما توجد فروع لجامعات بريطانية وأسترالية عريقة تمنح نفس شهادة الجامعة الأم.',
        'featured': False,
    },
    {
        'id': 'how-to-start-application',
        'category': 'services',
        'question': 'كيف أبدأ التقديم والحصول على استشارة مجانية مع بوابات العلوم؟',
        'answer': 'الأمر في غاية السهولة: يمكنك التواصل معنا مباشرة عبر <a href="https://wa.me/60182638888" target="_blank" rel="noopener noreferrer" class="faq-link">محادثة الواتساب الفورية</a>، أو تعبئة نموذج الاستفسار عبر <a href="/contact/" class="faq-link">صفحة التواصل</a> مع إرفاق شهادتك الثانوية أو الجامعية، وسيقوم أحد مستشارينا الأكاديميين بتقييم مؤهلاتك وتزويدك بالخيارات والمنح المناسبة خلال أقل من <bdi>24</bdi> ساعة.',
        'featured': False,
    },
]


def seed_general_faqs(apps, schema_editor):
    GeneralFAQ = apps.get_model('core', 'GeneralFAQ')

    for order_idx, faq in enumerate(INITIAL_SEED_FAQS, start=1):
        GeneralFAQ.objects.update_or_create(
            slug=faq['id'],
            defaults={
                'question': faq['question'],
                'answer': faq['answer'],
                'category': faq['category'],
                'order': order_idx,
                'is_featured': faq.get('featured', False),
                'is_published': True,
            }
        )


def reverse_general_faqs(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_alter_sitesettings_site_name_generalfaq'),
    ]

    operations = [
        migrations.RunPython(seed_general_faqs, reverse_general_faqs),
    ]
