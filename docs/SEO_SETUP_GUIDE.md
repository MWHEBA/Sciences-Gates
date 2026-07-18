# 🚀 دليل إعداد SEO - بوابات العلوم

**المحدّث:** 9 يونيو 2026  
**المدة المتوقعة:** 30-45 دقيقة

---

## 📋 قبل البدء

تأكد من توفر:
- [ ] حساب Google (Gmail)
- [ ] الوصول لملف `.env` في المشروع
- [ ] صلاحيات تشغيل أوامر Python

---

## 1️⃣ إعداد Google Analytics 4

### الخطوة 1: إنشاء حساب GA4

1. افتح [Google Analytics](https://analytics.google.com/)
2. اضغط على **"Start measuring"** أو **"Admin"** (⚙️)
3. اضغط على **"Create Account"**
4. أدخل:
   - **Account name:** Science Gates
   - ✅ Check all data sharing options
   - اضغط **Next**

### الخطوة 2: إنشاء Property

1. **Property name:** Science Gates Website
2. **Reporting time zone:** (GMT+08:00) Malaysia Time
3. **Currency:** MYR (Malaysian Ringgit)
4. اضغط **Next**

### الخطوة 3: معلومات الأعمال

1. **Industry category:** Education
2. **Business size:** Small
3. **How you plan to use Google Analytics:** Select all relevant
4. اضغط **Create**
5. وافق على Terms of Service

### الخطوة 4: إعداد Data Stream

1. اختر **Web** platform
2. أدخل:
   - **Website URL:** `https://sciencesgates.com` (أو domain الحالي)
   - **Stream name:** Science Gates Main Site
3. ✅ Enable **Enhanced measurement** (recommended)
4. اضغط **Create stream**

### الخطوة 5: الحصول على Measurement ID

1. بعد إنشاء Stream، سترى صفحة **Web stream details**
2. **انسخ Measurement ID** (يكون بالشكل: `G-XXXXXXXXXX`)
3. احفظه لاستخدامه في الخطوة التالية

---

## 2️⃣ إعداد Google Search Console

### الخطوة 1: إضافة الموقع

1. افتح [Google Search Console](https://search.google.com/search-console)
2. اضغط **Add property**
3. اختر **URL prefix**
4. أدخل: `https://sciencesgates.com` (أو domain الحالي)
5. اضغط **Continue**

### الخطوة 2: التحقق من الملكية

سيظهر لك عدة طرق للتحقق. استخدم **HTML tag**:

1. اختر **HTML tag**
2. انسخ **content** من meta tag
   ```html
   <meta name="google-site-verification" content="YOUR_CODE_HERE" />
   ```
3. انسخ فقط القيمة (YOUR_CODE_HERE)
4. احفظها لاستخدامها في الخطوة التالية
5. **لا تضغط Verify بعد!** - سنعود لهذه الخطوة

---

## 3️⃣ إضافة IDs للمشروع

### الخطوة 1: فتح ملف .env

افتح ملف `.env` في root المشروع:

```bash
# في مجلد المشروع الرئيسي
notepad .env
# أو
code .env
```

### الخطوة 2: إضافة المتغيرات

أضف هذه السطور في نهاية الملف (أو حدّث القيم إذا كانت موجودة):

```env
# Google Analytics & Search Console
GA4_MEASUREMENT_ID=G-XXXXXXXXXX
GOOGLE_SITE_VERIFICATION=your_verification_code_here
```

**مثال:**
```env
GA4_MEASUREMENT_ID=G-ABC123XYZ
GOOGLE_SITE_VERIFICATION=1234abcd5678efgh
```

### الخطوة 3: حفظ الملف

احفظ الملف واخرج من المحرر.

---

## 4️⃣ جمع Static Files

### الخطوة 1: تشغيل collectstatic

```bash
# في terminal/command prompt
cd "c:\Users\MohYousif\Desktop\Sciences Gates"
python manage.py collectstatic --noinput
```

هذا الأمر سينسخ:
- ✅ `static/robots.txt` → `staticfiles/robots.txt`
- ✅ جميع ملفات CSS/JS/Images

### الخطوة 2: تأكيد النجاح

يجب أن تظهر رسالة مثل:
```
X static files copied to 'staticfiles'
```

---

## 5️⃣ اختبار التفعيل

### الخطوة 1: تشغيل Server

```bash
python manage.py runserver
```

### الخطوة 2: فتح الموقع

افتح المتصفح واذهب إلى:
```
http://localhost:8000
```

### الخطوة 3: فحص GA4

1. افتح **Developer Tools** (F12)
2. اذهب إلى تبويب **Network**
3. ابحث عن طلب إلى `google-analytics.com/g/collect`
4. إذا وجدته → ✅ GA4 يعمل!

### الخطوة 4: فحص Meta Tag

1. في نفس الصفحة، اضغط **View Page Source** (Ctrl+U)
2. ابحث عن `google-site-verification`
3. يجب أن تجد:
   ```html
   <meta name="google-site-verification" content="YOUR_CODE">
   ```
4. إذا وجدتها → ✅ GSC meta tag جاهز!

### الخطوة 5: فحص robots.txt

اذهب إلى:
```
http://localhost:8000/robots.txt
```

يجب أن ترى محتوى مثل:
```txt
User-agent: *
Allow: /
Disallow: /mw-admin/
...
Sitemap: http://localhost:8000/sitemap.xml
```

---

## 6️⃣ التحقق من Google Search Console

### الآن نعود لـ GSC:

1. ارجع لصفحة التحقق في GSC
2. اضغط **Verify**
3. يجب أن تظهر رسالة: ✅ **"Ownership verified"**

إذا ظهر خطأ:
- تأكد أن `.env` محدّث
- تأكد أن Server شغال
- جرب مرة أخرى بعد دقيقة

---

## 7️⃣ اختبار Schema Markup

### الخطوة 1: اختبار صفحة جامعة

1. اذهب إلى أي صفحة جامعة محلياً:
   ```
   http://localhost:8000/universities/[slug]/
   ```

2. افتح [Google Rich Results Test](https://search.google.com/test/rich-results)

3. الصق URL الكامل

4. اضغط **Test URL**

5. يجب أن ترى:
   - ✅ EducationalOrganization
   - ✅ BreadcrumbList
   - ✅ FAQPage (إذا كانت هناك FAQs)

### الخطوة 2: اختبار صفحة تخصص

كرر نفس الخطوات مع صفحة تخصص:
```
http://localhost:8000/majors/[slug]/
```

يجب أن ترى:
- ✅ Course
- ✅ BreadcrumbList

### الخطوة 3: اختبار صفحة مقال

كرر مع صفحة مقال:
```
http://localhost:8000/articles/[slug]/
```

يجب أن ترى:
- ✅ Article
- ✅ BreadcrumbList

---

## 8️⃣ Deploy للإنتاج

### عند رفع التحديثات للموقع الحي:

1. **رفع الملفات:**
   ```bash
   git add .
   git commit -m "Add GA4, GSC, and Schema markup"
   git push
   ```

2. **على السيرفر:**
   ```bash
   # تحديث الكود
   git pull
   
   # جمع Static files
   python manage.py collectstatic --noinput
   
   # إعادة تشغيل Server
   # (حسب إعداد السيرفر - Gunicorn, uWSGI, etc.)
   ```

3. **اختبار على الموقع الحي:**
   - GA4: افتح GA4 Real-time reports
   - GSC: تحقق من Indexing status
   - Schema: اختبر باستخدام Rich Results Test

---

## 9️⃣ المراقبة والمتابعة

### في Google Analytics 4:

**اليومي:**
- افتح **Reports → Realtime**
- تأكد من وجود زوار نشطين

**أسبوعي:**
- **Reports → Engagement → Pages and screens**
- شوف أكثر الصفحات زيارة
- **Reports → Acquisition → Traffic acquisition**
- شوف مصادر الزوار

**شهري:**
- **Reports → Overview**
- راجع نمو الـ traffic
- حدد الصفحات الأفضل أداءً

### في Google Search Console:

**أسبوعي:**
- **Performance → Search results**
  - Total clicks
  - Total impressions
  - Average CTR
  - Average position

- **Coverage**
  - تأكد من عدم وجود errors
  - راقب عدد الصفحات المفهرسة

**شهري:**
- حدد keywords الجديدة
- راقب تحسن الترتيب
- راجع Mobile Usability
- تحقق من Core Web Vitals

---

## 🐛 حل المشاكل الشائعة

### GA4 لا يظهر في الموقع:

**السبب المحتمل:** `.env` غير محدّث أو Server لم يُعاد تشغيله

**الحل:**
1. تأكد أن `GA4_MEASUREMENT_ID` موجود في `.env`
2. أعد تشغيل Server: `python manage.py runserver`
3. امسح cache المتصفح: Ctrl+Shift+Delete

---

### GSC Verification يفشل:

**السبب المحتمل:** Meta tag غير موجود أو Server مش شغال

**الحل:**
1. تأكد أن `GOOGLE_SITE_VERIFICATION` موجود في `.env`
2. تأكد أن Server شغال
3. افتح View Source وابحث عن `google-site-verification`
4. انتظر دقيقة وجرب مرة أخرى

---

### Schema لا يظهر في Rich Results Test:

**السبب المحتمل:** Template tags غير محملة أو خطأ في Schema

**الحل:**
1. تأكد من وجود `{% load schema_tags %}` في أول Template
2. افتح View Source وابحث عن `application/ld+json`
3. انسخ محتوى Schema واختبره في [Schema Validator](https://validator.schema.org/)

---

### robots.txt يعطي 404:

**السبب المحتمل:** Static files لم يتم جمعها

**الحل:**
```bash
python manage.py collectstatic --noinput
```

---

## ✅ Checklist النهائي

### بعد إكمال كل الخطوات:

```markdown
□ GA4 Measurement ID مضاف في .env
□ GSC Verification Code مضاف في .env
□ collectstatic تم تشغيله بنجاح
□ GA4 script يظهر في View Source
□ GSC meta tag يظهر في View Source
□ robots.txt يفتح ويظهر المحتوى
□ Schema يظهر في Rich Results Test
□ GSC Ownership Verified ✅
□ Real-time traffic يظهر في GA4
```

---

## 📚 موارد إضافية

### Documentation:
- [Google Analytics 4 Guide](https://support.google.com/analytics/answer/9304153)
- [Search Console Help](https://support.google.com/webmasters)
- [Schema.org Documentation](https://schema.org/)

### Testing Tools:
- [Rich Results Test](https://search.google.com/test/rich-results)
- [Schema Validator](https://validator.schema.org/)
- [Page Speed Insights](https://pagespeed.web.dev/)

### Internal Docs:
- `SEO_STRATEGY.md` - الاستراتيجية الكاملة
- `SEO_IMPLEMENTATION_STATUS.md` - حالة التنفيذ
- `docs/SEO_CONTENT_GUIDELINES.md` - دليل المحتوى

---

## 💡 نصائح مهمة

1. **احفظ Measurement ID وVerification Code** في مكان آمن
2. **راقب GA4 يومياً** لأول أسبوع للتأكد من العمل
3. **راجع GSC أسبوعياً** لمراقبة الفهرسة والأداء
4. **اختبر Schema بعد كل تحديث** للـ templates
5. **احتفظ بنسخة احتياطية** من `.env` file

---

## 🎯 الخطوة التالية

بعد إكمال الإعداد، انتقل إلى:
- 📝 **Content Creation** - استخدم `docs/SEO_CONTENT_GUIDELINES.md`
- 🔗 **Internal Linking** - راجع الاستراتيجية في `SEO_STRATEGY.md`
- 📊 **Performance Monitoring** - ابدأ تتبع Metrics

---

**آخر تحديث:** 9 يونيو 2026  
**الدعم:** فريق SEO - بوابات العلوم  
**الحالة:** ✅ جاهز للتنفيذ
