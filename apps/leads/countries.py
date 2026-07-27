"""
Country phone codes configuration.
قائمة الدول وأكواد الهاتف - مرتبة حسب الأولوية
(iso_code, arabic_name, dial_code, placeholder)
"""

# الدول ذات الأولوية (الجمهور الأساسي) - تظهر أولاً
PRIORITY_COUNTRIES = [
    ("sa", "السعودية", "+966", "5XXXXXXXX"),
    ("ae", "الإمارات", "+971", "5XXXXXXXX"),
    ("sd", "السودان", "+249", "9XXXXXXXX"),
    ("eg", "مصر", "+20", "1XXXXXXXX"),
    ("jo", "الأردن", "+962", "7XXXXXXXX"),
    ("iq", "العراق", "+964", "7XXXXXXXXX"),
    ("kw", "الكويت", "+965", "5XXXXXXX"),
    ("bh", "البحرين", "+973", "3XXXXXXX"),
    ("qa", "قطر", "+974", "3XXXXXXX"),
    ("om", "عُمان", "+968", "9XXXXXXX"),
    ("ye", "اليمن", "+967", "7XXXXXXXX"),
    ("ly", "ليبيا", "+218", "9XXXXXXXX"),
    ("ma", "المغرب", "+212", "6XXXXXXXX"),
    ("dz", "الجزائر", "+213", "5XXXXXXXX"),
    ("tn", "تونس", "+216", "2XXXXXXX"),
    ("ps", "فلسطين", "+970", "5XXXXXXXX"),
    ("lb", "لبنان", "+961", "7XXXXXXX"),
    ("sy", "سوريا", "+963", "9XXXXXXXX"),
    ("mr", "موريتانيا", "+222", "XXXXXXXX"),
    ("so", "الصومال", "+252", "6XXXXXXXX"),
    ("dj", "جيبوتي", "+253", "77XXXXXX"),
    ("km", "جزر القمر", "+269", "3XXXXXX"),
    ("my", "ماليزيا", "+60", "1XXXXXXXX"),
]

# باقي دول العالم - أبجدياً بالعربي
OTHER_COUNTRIES = [
    ("af", "أفغانستان", "+93", "7XXXXXXXX"),
    ("al", "ألبانيا", "+355", "6XXXXXXXX"),
    ("de", "ألمانيا", "+49", "15XXXXXXXX"),
    ("ao", "أنغولا", "+244", "9XXXXXXXX"),
    ("uy", "أوروغواي", "+598", "9XXXXXXX"),
    ("uz", "أوزبكستان", "+998", "9XXXXXXXX"),
    ("ug", "أوغندا", "+256", "7XXXXXXXX"),
    ("ua", "أوكرانيا", "+380", "5XXXXXXXX"),
    ("ie", "أيرلندا", "+353", "8XXXXXXXX"),
    ("is", "أيسلندا", "+354", "6XXXXXXX"),
    ("et", "إثيوبيا", "+251", "9XXXXXXXX"),
    ("er", "إريتريا", "+291", "7XXXXXXX"),
    ("es", "إسبانيا", "+34", "6XXXXXXXX"),
    ("au", "أستراليا", "+61", "4XXXXXXXX"),
    ("ee", "إستونيا", "+372", "5XXXXXXX"),
    ("il", "إسرائيل", "+972", "5XXXXXXXX"),
    ("id", "إندونيسيا", "+62", "8XXXXXXXXX"),
    ("ir", "إيران", "+98", "9XXXXXXXXX"),
    ("it", "إيطاليا", "+39", "3XXXXXXXX"),
    ("ar", "الأرجنتين", "+54", "1XXXXXXXXX"),
    ("ec", "الإكوادور", "+593", "9XXXXXXXX"),
    ("br", "البرازيل", "+55", "1XXXXXXXXX"),
    ("pt", "البرتغال", "+351", "9XXXXXXXX"),
    ("ba", "البوسنة", "+387", "6XXXXXXX"),
    ("me", "الجبل الأسود", "+382", "6XXXXXXX"),
    ("cz", "التشيك", "+420", "6XXXXXXXX"),
    ("cl", "تشيلي", "+56", "9XXXXXXXX"),
    ("dk", "الدنمارك", "+45", "2XXXXXXX"),
    ("cv", "الرأس الأخضر", "+238", "9XXXXXX"),
    ("se", "السويد", "+46", "7XXXXXXXX"),
    ("sn", "السنغال", "+221", "7XXXXXXXX"),
    ("ph", "الفلبين", "+63", "9XXXXXXXXX"),
    ("cm", "الكاميرون", "+237", "6XXXXXXXX"),
    ("cg", "الكونغو", "+242", "0XXXXXXXX"),
    ("mx", "المكسيك", "+52", "1XXXXXXXXX"),
    ("gb", "المملكة المتحدة", "+44", "7XXXXXXXXX"),
    ("no", "النرويج", "+47", "4XXXXXXX"),
    ("at", "النمسا", "+43", "6XXXXXXXX"),
    ("ne", "النيجر", "+227", "9XXXXXXX"),
    ("in", "الهند", "+91", "9XXXXXXXXX"),
    ("us", "الولايات المتحدة", "+1", "2XXXXXXXXX"),
    ("jp", "اليابان", "+81", "9XXXXXXXX"),
    ("pk", "باكستان", "+92", "3XXXXXXXXX"),
    ("py", "باراغواي", "+595", "9XXXXXXXX"),
    ("bd", "بنغلاديش", "+880", "1XXXXXXXXX"),
    ("be", "بلجيكا", "+32", "4XXXXXXXX"),
    ("bg", "بلغاريا", "+359", "8XXXXXXXX"),
    ("bj", "بنين", "+229", "9XXXXXXX"),
    ("pe", "بيرو", "+51", "9XXXXXXXX"),
    ("th", "تايلاند", "+66", "8XXXXXXXX"),
    ("tw", "تايوان", "+886", "9XXXXXXXX"),
    ("tr", "تركيا", "+90", "5XXXXXXXXX"),
    ("tm", "تركمانستان", "+993", "6XXXXXXX"),
    ("tz", "تنزانيا", "+255", "7XXXXXXXX"),
    ("tg", "توغو", "+228", "9XXXXXXX"),
    ("td", "تشاد", "+235", "6XXXXXXXX"),
    ("za", "جنوب أفريقيا", "+27", "7XXXXXXXX"),
    ("kr", "كوريا الجنوبية", "+82", "1XXXXXXXXX"),
    ("ge", "جورجيا", "+995", "5XXXXXXXX"),
    ("rw", "رواندا", "+250", "7XXXXXXXX"),
    ("ro", "رومانيا", "+40", "7XXXXXXXX"),
    ("ru", "روسيا", "+7", "9XXXXXXXXX"),
    ("zm", "زامبيا", "+260", "9XXXXXXXX"),
    ("zw", "زيمبابوي", "+263", "7XXXXXXXX"),
    ("ci", "ساحل العاج", "+225", "0XXXXXXXXX"),
    ("sg", "سنغافورة", "+65", "8XXXXXXX"),
    ("lk", "سريلانكا", "+94", "7XXXXXXXX"),
    ("sk", "سلوفاكيا", "+421", "9XXXXXXXX"),
    ("si", "سلوفينيا", "+386", "4XXXXXXX"),
    ("ch", "سويسرا", "+41", "7XXXXXXXX"),
    ("sl", "سيراليون", "+232", "7XXXXXXX"),
    ("rs", "صربيا", "+381", "6XXXXXXXX"),
    ("cn", "الصين", "+86", "1XXXXXXXXXX"),
    ("gh", "غانا", "+233", "2XXXXXXXX"),
    ("gn", "غينيا", "+224", "6XXXXXXXX"),
    ("fr", "فرنسا", "+33", "6XXXXXXXX"),
    ("ve", "فنزويلا", "+58", "4XXXXXXXX"),
    ("fi", "فنلندا", "+358", "4XXXXXXXX"),
    ("vn", "فيتنام", "+84", "9XXXXXXXX"),
    ("cy", "قبرص", "+357", "9XXXXXXX"),
    ("kg", "قيرغيزستان", "+996", "7XXXXXXXX"),
    ("kz", "كازاخستان", "+7", "7XXXXXXXXX"),
    ("hr", "كرواتيا", "+385", "9XXXXXXXX"),
    ("ke", "كينيا", "+254", "7XXXXXXXX"),
    ("co", "كولومبيا", "+57", "3XXXXXXXXX"),
    ("cr", "كوستاريكا", "+506", "8XXXXXXX"),
    ("ca", "كندا", "+1", "2XXXXXXXXX"),
    ("lv", "لاتفيا", "+371", "2XXXXXXX"),
    ("lt", "ليتوانيا", "+370", "6XXXXXXX"),
    ("lu", "لوكسمبورغ", "+352", "6XXXXXXXX"),
    ("lr", "ليبيريا", "+231", "7XXXXXXXX"),
    ("mg", "مدغشقر", "+261", "3XXXXXXXX"),
    ("ml", "مالي", "+223", "7XXXXXXXX"),
    ("mt", "مالطا", "+356", "9XXXXXXX"),
    ("mz", "موزمبيق", "+258", "8XXXXXXXX"),
    ("mm", "ميانمار", "+95", "9XXXXXXXX"),
    ("ng", "نيجيريا", "+234", "8XXXXXXXXX"),
    ("np", "نيبال", "+977", "9XXXXXXXXX"),
    ("nz", "نيوزيلندا", "+64", "2XXXXXXXX"),
    ("nl", "هولندا", "+31", "6XXXXXXXX"),
    ("hu", "المجر", "+36", "2XXXXXXXX"),
    ("hk", "هونغ كونغ", "+852", "5XXXXXXXX"),
]

# القائمة الكاملة مرتبة
ALL_COUNTRIES = PRIORITY_COUNTRIES + OTHER_COUNTRIES

# الدولة الافتراضية
DEFAULT_COUNTRY = "sa"
DEFAULT_CODE = "+966"
DEFAULT_PLACEHOLDER = "5XXXXXXXX"


def get_country_info(iso_code):
    """
    جلب معلومات الدولة (iso_code, dial_code, placeholder) حسب رمز الدولة ISO-2.
    في حال عدم العثور عليها يتم إرجاع الدولة الافتراضية (السعودية).
    """
    if not iso_code:
        return DEFAULT_COUNTRY, DEFAULT_CODE, DEFAULT_PLACEHOLDER
    target = str(iso_code).lower().strip()
    for iso, name, code, placeholder in ALL_COUNTRIES:
        if iso == target:
            return iso, code, placeholder
    return DEFAULT_COUNTRY, DEFAULT_CODE, DEFAULT_PLACEHOLDER

