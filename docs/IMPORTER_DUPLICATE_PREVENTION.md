# WordPress Importer: منع تكرار الصور

## المشكلة

عند استيراد الجامعات من الووردبريس، كان النظام **يحمل الصورة في كل مرة** حتى لو:
- الصورة موجودة مسبقاً في إدارة الوسائط
- تم استيراد نفس الجامعة أكثر من مرة (مثلاً عند المعاينة بدون نشر)
- تم تعديل بيانات الجامعة وإعادة استيرادها

النتيجة: **تكرار الصور** في إدارة الوسائط، إهدار للمساحة، وصعوبة في الإدارة.

---

## الحل

### 1. فحص الصور المكررة بـ URL Hash

النظام الآن **يفحص أولاً** إذا كانت الصورة موجودة مسبقاً قبل التحميل:

```python
# حساب hash من الـ URL
url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
url_marker = f"[WP_URL_HASH:{url_hash}]"

# البحث عن صورة موجودة بنفس الـ URL
existing_media = MediaFile.objects.filter(
    description__contains=url_marker
).first()

if existing_media:
    # الصورة موجودة - نرجع المرجع القديم بدون تحميل جديد
    return existing_media, None
```

### 2. تخزين URL Hash في Description

عند حفظ الصورة لأول مرة، النظام يضيف علامة مخفية في حقل `description`:

```python
final_description = f"{description}\n[WP_URL_HASH:{url_hash}]"
```

**مثال:**
```
Description: Logo file imported from WordPress
[WP_URL_HASH:a3f5e9c8b2d1f4a6e8c9d2b3f5a6e8c9]
```

هذه العلامة:
- ✅ مخفية عن المستخدم (في نهاية النص)
- ✅ مستمرة عبر التحديثات
- ✅ فريدة لكل URL (MD5 hash)

### 3. تحديث البيانات الوصفية عند إعادة الاستيراد

إذا تم استيراد نفس الصورة مرة أخرى مع بيانات محدثة، النظام:

| الحقل | السلوك |
|-------|---------|
| **Alt Text** | يُحدث إذا كان القيمة الجديدة مختلفة وغير فارغة |
| **Caption** | يُحدث إذا كان القيمة الجديدة مختلفة وغير فارغة |
| **Description** | يُحدث مع **الحفاظ على URL hash marker** |
| **Title** | لا يتغير (مُولَّد من اسم الملف الأصلي) |
| **File** | لا يُحمل مرة أخرى (يبقى الملف القديم) |

```python
if alt_text and alt_text.strip() and alt_text.strip() != existing_media.alt_text:
    existing_media.alt_text = alt_text.strip()
    updated = True

if caption and caption.strip() and caption.strip() != existing_media.caption:
    existing_media.caption = caption.strip()
    updated = True

if description and description.strip():
    # تحديث الوصف مع الحفاظ على URL marker
    if url_marker not in new_desc:
        existing_media.description = f"{new_desc}\n{url_marker}"
    updated = True

if updated:
    existing_media.save()
```

---

## السيناريوهات

### السيناريو 1: استيراد جامعة لأول مرة

```
1. المستخدم يدخل رابط جامعة من الووردبريس
2. النظام يجلب البيانات والصور
3. الصور تُحمل وتُحفظ مع URL hash marker
4. ✅ النتيجة: صورة واحدة في إدارة الوسائط
```

### السيناريو 2: معاينة بدون نشر، ثم استيراد مرة أخرى

```
1. المستخدم يعاين الجامعة (بدون نشر)
2. الصور تُحمل → صورة واحدة موجودة
3. المستخدم يستورد نفس الجامعة مرة أخرى
4. النظام يفحص: الصورة موجودة (نفس الـ URL)
5. ✅ النتيجة: نفس الصورة تُستخدم (بدون تكرار)
```

### السيناريو 3: تعديل بيانات الصورة في الووردبريس

```
1. الجامعة موجودة في النظام
2. المحرر يُحدث alt text في الووردبريس
3. المستخدم يستورد الجامعة مرة أخرى
4. النظام يفحص: الصورة موجودة
5. النظام يُحدث alt_text بالقيمة الجديدة
6. ✅ النتيجة: صورة واحدة مع بيانات محدثة
```

### السيناريو 4: صور مختلفة لجامعات مختلفة

```
1. استيراد جامعة A (logo: url1.png)
2. استيراد جامعة B (logo: url2.png)
3. URL مختلف → hash مختلف
4. ✅ النتيجة: صورتان منفصلتان (صحيح)
```

---

## الفوائد

| الفائدة | قبل | بعد |
|---------|-----|-----|
| **تكرار الصور** | ✖️ كل استيراد = صورة جديدة | ✅ صورة واحدة لكل URL |
| **إهدار المساحة** | ✖️ صور مكررة تملأ القرص | ✅ لا تكرار = مساحة موفرة |
| **سهولة الإدارة** | ✖️ صعب تمييز الصور المكررة | ✅ إدارة وسائط نظيفة |
| **البيانات الوصفية** | ✖️ قد تتعارض أو تُفقد | ✅ تُحدث تلقائياً بذكاء |
| **الأداء** | ✖️ تحميل في كل مرة | ✅ بدون تحميل إذا موجودة |

---

## الاختبارات

تم إضافة اختبارات شاملة للتأكد من صحة العمل:

```python
class ImageDownloaderDuplicateTests(TestCase):
    def test_image_downloads_first_time(self):
        """أن الصورة تُحمّل بنجاح في المرة الأولى"""
        
    def test_image_not_downloaded_second_time(self):
        """أن نفس الرابط يرجع الصورة الموجودة بدون تحميل جديد"""
        
    def test_different_urls_download_separately(self):
        """أن روابط مختلفة تُنشئ صور منفصلة"""
        
    def test_metadata_updates_on_reimport(self):
        """أن Caption و Description يتحدثوا عند إعادة الاستيراد"""
        
    def test_metadata_not_overwritten_with_empty_values(self):
        """أن البيانات الموجودة لا تُستبدل بقيم فارغة"""
        
    def test_url_marker_preserved_across_updates(self):
        """أن علامة الـ URL hash محفوظة دائماً حتى بعد تحديثات متعددة"""
```

تشغيل الاختبارات:
```bash
python manage.py test apps.importer.tests.ImageDownloaderDuplicateTests
```

---

## الملفات المعدلة

| الملف | التعديل |
|-------|---------|
| `apps/importer/services/image_downloader.py` | إضافة فحص التكرار + تحديث البيانات الوصفية |
| `apps/importer/tests.py` | إضافة اختبارات شاملة للتكرار والتحديث |
| `docs/IMPORTER_DUPLICATE_PREVENTION.md` | هذا الملف (التوثيق) |

---

## ملاحظات فنية

### لماذا MD5 Hash؟
- سريع في الحساب
- ثابت الطول (32 حرف)
- كافي لهذا الغرض (ليس لأمان حساس)
- مدعوم في Python standard library

### لماذا في Description وليس حقل منفصل؟
- ✅ لا يحتاج migration جديدة
- ✅ حقل Description نادراً ما يُستخدم في الووردبريس
- ✅ العلامة مخفية في النهاية (لا تؤثر على العرض)
- ✅ سهل البحث بـ `description__contains`

### هل يمكن أن يتعارض مع description عادية؟
لا، لأن:
1. العلامة بتنسيق فريد: `[WP_URL_HASH:...]`
2. تُضاف في نهاية النص
3. يتم الحفاظ عليها عبر التحديثات

---

## أمثلة من قاعدة البيانات

### قبل التعديل:
```
id | file                     | alt_text              | description
---|--------------------------|----------------------|-------------
1  | logo_um_20260101.webp    | شعار جامعة مالايا    | Logo imported from WP
2  | logo_um_20260102.webp    | شعار جامعة مالايا    | Logo imported from WP
3  | logo_um_20260103.webp    | شعار جامعة مالايا    | Logo imported from WP
```
❌ **3 صور مكررة لنفس الجامعة**

### بعد التعديل:
```
id | file                     | alt_text              | description
---|--------------------------|----------------------|-------------
1  | logo_um_20260101.webp    | شعار جامعة مالايا    | Logo imported from WP
   |                          |                      | [WP_URL_HASH:a3f5e9c8...]
```
✅ **صورة واحدة فقط، تُعاد استخدامها تلقائياً**

---

## الخلاصة

التحديث الجديد يمنع **تكرار الصور** عند استيراد الجامعات من الووردبريس بشكل تلقائي وذكي:

1. ✅ فحص تلقائي قبل التحميل
2. ✅ تحديث البيانات الوصفية بذكاء
3. ✅ الحفاظ على البيانات القيمة
4. ✅ إدارة وسائط نظيفة ومنظمة
5. ✅ أداء أفضل (بدون تحميلات غير ضرورية)
