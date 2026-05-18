# تحليل شامل للداشبورد — Sciences Gates

**تاريخ التحليل**: مايو 2026  
**المحلل**: Kiro AI  
**الهدف**: تحديد الثغرات في القوالب، الروابط المفقودة، وعدم استغلال الباك اند بالكامل

---

## 1. ملخص تنفيذي

الداشبورد يمتلك **بنية تحتية قوية جداً** في الباك اند (models, views, forms) لكن القوالب **لا تعكس هذه القوة**. المشكلة الأساسية هي أن قوالب create/edit للجامعات والمعاهد والتخصصات تعرض **20-30% فقط** من الحقول المتاحة في الفورم والنموذج.

---

## 2. خريطة القوالب الموجودة

### 2.1 قوالب الداشبورد الكاملة

```
templates/dashboard/
├── base.html                    ✅ مكتمل
├── home.html                    ✅ مكتمل
├── login.html                   ✅ مكتمل
├── list_page.html               ✅ قالب عام (لكن غير مستخدم بشكل صحيح)
├── form_page.html               ✅ قالب عام
├── delete_confirm.html          ✅ قالب عام
│
├── components/
│   ├── sidebar.html             ✅ مكتمل
│   ├── topbar.html              ✅ مكتمل
│   ├── data_table.html          ✅ مكتمل
│   ├── filter_bar.html          ✅ مكتمل
│   ├── pagination.html          ✅ مكتمل
│   ├── stats_card.html          ✅ مكتمل
│   ├── empty_state.html         ✅ مكتمل
│   ├── form_field.html          ✅ مكتمل
│   ├── form_section.html        ✅ مكتمل
│   ├── formset_container.html   ✅ مكتمل
│   ├── formset_item.html        ✅ مكتمل
│   ├── badge.html               ✅ مكتمل
│   ├── messages.html            ✅ مكتمل
│   └── button_examples.html     ⚠️ ملف أمثلة فقط (غير مستخدم)
│
├── universities/
│   ├── list.html                ⚠️ ناقص جداً (يرث list_page لكن لا يمرر context)
│   ├── create.html              🔴 ناقص (20% من الحقول فقط)
│   ├── edit.html                🔴 ناقص (20% من الحقول فقط)
│   └── delete_confirm.html      ✅ مكتمل
│
├── institutes/
│   ├── list.html                ⚠️ ناقص (يرث base مباشرة بدون list_page)
│   ├── create.html              🔴 ناقص (25% من الحقول فقط)
│   ├── edit.html                🔴 ناقص (25% من الحقول فقط)
│   └── delete_confirm.html      ✅ مكتمل
│
├── majors/
│   ├── list.html                ⚠️ ناقص
│   ├── create.html              🔴 ناقص (15% من الحقول فقط)
│   ├── edit.html                🔴 ناقص (15% من الحقول فقط)
│   └── delete_confirm.html      ✅ مكتمل
│
├── articles/
│   ├── list.html                ✅ مكتمل نسبياً
│   ├── create.html              ✅ مكتمل (يعرض كل الحقول)
│   ├── edit.html                ❓ غير محلل (يفترض مشابه للـ create)
│   └── delete_confirm.html      ✅ مكتمل
│
├── faculties/
│   ├── list.html                ✅ مكتمل
│   ├── create.html              ✅ مكتمل
│   ├── edit.html                ✅ مكتمل
│   └── delete_confirm.html      ✅ مكتمل
│
├── leads/
│   ├── list.html                ✅ مكتمل
│   └── detail.html              ✅ مكتمل
│
├── redirects/
│   ├── list.html                ✅ مكتمل
│   ├── create.html              ✅ مكتمل
│   ├── edit.html                ✅ مكتمل
│   └── delete_confirm.html      ✅ مكتمل
│
├── categories/
│   ├── list.html                ✅ مكتمل
│   ├── create.html              ✅ مكتمل
│   ├── edit.html                ✅ مكتمل
│   └── delete_confirm.html      ✅ مكتمل
│
├── tags/
│   ├── list.html                ✅ مكتمل
│   ├── create.html              ✅ مكتمل
│   ├── edit.html                ✅ مكتمل
│   └── delete_confirm.html      ✅ مكتمل
│
├── users/
│   ├── list.html                ✅ مكتمل
│   ├── create.html              ✅ مكتمل
│   ├── edit.html                ✅ مكتمل
│   └── delete_confirm.html      ✅ مكتمل
│
└── seo/
    └── overview.html            ✅ مكتمل
```

---

## 3. المشكلة الكبرى: القوالب الناقصة

### 3.1 قالب إنشاء/تعديل الجامعة — ناقص 80%

**الحقول المتاحة في `UniversityForm`** (forms/university.py):
```
name, slug, university_type, logo, main_image, location, video_url,
description, admission_requirements, registration_section,
related_majors, related_articles,
publish_status,
meta_title, meta_description, focus_keyword, canonical_url,
robots_index, robots_follow, sitemap_include,
og_title, og_description, og_image
```
**المجموع: 23 حقل**

**الحقول المعروضة في `universities/create.html` و `edit.html`**:
```
name, slug, location, website (غير موجود في الفورم!), description, is_published (خطأ!)
```
**المجموع: 5 حقول فقط**

**الحقول المفقودة من القالب (18 حقل)**:
| الحقل | الأهمية |
|-------|---------|
| `university_type` | 🔴 حرج — نوع الجامعة (حكومية/خاصة) |
| `logo` | 🔴 حرج — شعار الجامعة |
| `main_image` | 🔴 حرج — الصورة الرئيسية |
| `video_url` | 🟡 مهم — رابط الفيديو |
| `admission_requirements` | 🔴 حرج — شروط القبول |
| `registration_section` | 🔴 حرج — قسم التسجيل |
| `related_majors` | 🟡 مهم — التخصصات المرتبطة |
| `related_articles` | 🟡 مهم — المقالات المرتبطة |
| `publish_status` | 🔴 حرج — يستخدم `is_published` الخاطئ بدلاً من `publish_status` |
| `meta_title` | 🔴 حرج — SEO |
| `meta_description` | 🔴 حرج — SEO |
| `focus_keyword` | 🟡 مهم — SEO |
| `canonical_url` | 🟡 مهم — SEO |
| `robots_index` | 🟡 مهم — SEO |
| `robots_follow` | 🟡 مهم — SEO |
| `sitemap_include` | 🟡 مهم — SEO |
| `og_title` | 🟡 مهم — Open Graph |
| `og_description` | 🟡 مهم — Open Graph |
| `og_image` | 🟡 مهم — Open Graph |

**خطأ إضافي**: القالب يستخدم `form.is_published` و `form.website` وهما **غير موجودين** في `UniversityForm`. هذا يعني أن قسم النشر لا يعمل أصلاً.

---

### 3.2 قالب إنشاء/تعديل المعهد — ناقص 75%

**الحقول المتاحة في `InstituteForm`** (forms/institute.py):
```
name, slug, institute_type, main_image,
description, registration_requirements, registration_section,
related_articles,
publish_status,
meta_title, meta_description, focus_keyword, canonical_url,
robots_index, robots_follow, sitemap_include,
og_title, og_description, og_image
```
**المجموع: 19 حقل + CourseFormSet**

**الحقول المعروضة في `institutes/create.html` و `edit.html`**:
```
name, slug, website (غير موجود!), description, is_published (خطأ!)
```
**المجموع: 4 حقول فقط**

**الحقول المفقودة (15 حقل)**:
| الحقل | الأهمية |
|-------|---------|
| `institute_type` | 🔴 حرج — نوع المعهد (لغة/أكاديمي) |
| `main_image` | 🔴 حرج — الصورة الرئيسية |
| `registration_requirements` | 🔴 حرج — شروط التسجيل |
| `registration_section` | 🔴 حرج — قسم التسجيل |
| `related_articles` | 🟡 مهم — المقالات المرتبطة |
| `CourseFormSet` | 🔴 حرج — الدورات المرتبطة بالمعهد |
| كل حقول SEO (9 حقول) | 🔴 حرج — SEO كامل مفقود |

---

### 3.3 قالب إنشاء/تعديل التخصص — ناقص 85%

**الحقول المتاحة في `MajorForm`** (forms/major.py):
```
name, slug, major_category, main_image,
study_duration, bachelor_duration, master_duration, phd_duration,
tuition_fees, study_language, practical_training, career_opportunities,
description, why_study_section, how_to_apply_section,
best_universities, cheap_universities, related_articles,
publish_status,
meta_title, meta_description, focus_keyword, canonical_url,
robots_index, robots_follow, sitemap_include,
og_title, og_description, og_image
```
**المجموع: 29 حقل + 3 FormSets (SubjectsTable, SalaryTable, CountriesTable)**

**الحقول المعروضة في `majors/create.html` و `edit.html`**:
```
name, slug, study_duration, description, is_published (خطأ!)
```
**المجموع: 4 حقول فقط**

**الحقول المفقودة (25 حقل + 3 FormSets)**:
| الحقل | الأهمية |
|-------|---------|
| `major_category` | 🔴 حرج — فئة التخصص |
| `main_image` | 🔴 حرج — الصورة الرئيسية |
| `bachelor_duration` | 🟡 مهم — مدة البكالوريوس |
| `master_duration` | 🟡 مهم — مدة الماجستير |
| `phd_duration` | 🟡 مهم — مدة الدكتوراه |
| `tuition_fees` | 🔴 حرج — الرسوم الدراسية |
| `study_language` | 🔴 حرج — لغة الدراسة |
| `practical_training` | 🟡 مهم — التدريب العملي |
| `career_opportunities` | 🔴 حرج — فرص العمل |
| `why_study_section` | 🔴 حرج — قسم "لماذا تدرس" |
| `how_to_apply_section` | 🔴 حرج — قسم "كيفية التقديم" |
| `best_universities` | 🔴 حرج — أفضل الجامعات |
| `cheap_universities` | 🔴 حرج — الجامعات الاقتصادية |
| `related_articles` | 🟡 مهم — المقالات المرتبطة |
| `SubjectsTableFormSet` | 🔴 حرج — جدول المواد الدراسية |
| `SalaryTableFormSet` | 🔴 حرج — جدول الرواتب |
| `CountriesTableFormSet` | 🔴 حرج — جدول الدول |
| كل حقول SEO (9 حقول) | 🔴 حرج — SEO كامل مفقود |

---

### 3.4 قالب قائمة الجامعات — ناقص في الـ Context

**المشكلة**: `universities/list.html` يرث من `list_page.html` لكن لا يمرر أي context variables مطلوبة.

`list_page.html` يحتاج:
```
items, columns, edit_url_name, delete_url_name,
search_placeholder, filters, base_url, is_paginated, page_obj
```

`universities/list.html` لا يمرر أياً منها — يعتمد على الـ view لكن الـ view (`UniversityListView`) يمرر `universities` كـ context_object_name وليس `items`.

**النتيجة**: جدول البيانات لن يظهر لأن `list_page.html` يبحث عن `items` وليس `universities`.

---

## 4. مشاكل الربط بين القائمة الجانبية والـ Views

### 4.1 ما هو مربوط بشكل صحيح ✅

| القائمة | URL | View | Template |
|---------|-----|------|----------|
| الرئيسية | `dashboard:home` | `DashboardHomeView` | `home.html` |
| الجامعات | `dashboard:university_list` | `UniversityListView` | `universities/list.html` |
| المعاهد | `dashboard:institute_list` | `InstituteListView` | `institutes/list.html` |
| التخصصات | `dashboard:major_list` | `MajorListView` | `majors/list.html` |
| المقالات | `dashboard:article_list` | `ArticleListView` | `articles/list.html` |
| الفئات | `dashboard:category_list` | `CategoryListView` | `categories/list.html` |
| الوسوم | `dashboard:tag_list` | `TagListView` | `tags/list.html` |
| الرسائل | `dashboard:lead_list` | `LeadListView` | `leads/list.html` |
| إعادة التوجيه | `dashboard:redirect_list` | `RedirectListView` | `redirects/list.html` |
| إعدادات SEO | `dashboard:seo_overview` | `SEOOverviewView` | `seo/overview.html` |
| المستخدمون | `dashboard:user_list` | `UserListView` | `users/list.html` |

### 4.2 ما هو موجود في الـ URLs لكن غير موجود في القائمة الجانبية ⚠️

| URL | الوصف | السبب المحتمل |
|-----|-------|---------------|
| `dashboard:faculty_list` | قائمة الكليات | تُفتح من داخل صفحة الجامعة |
| `dashboard:faculty_create` | إنشاء كلية | تُفتح من داخل صفحة الجامعة |
| `dashboard:lead_export` | تصدير الرسائل CSV | زر داخل صفحة الرسائل |
| `dashboard:lead_detail` | تفاصيل رسالة | رابط داخل قائمة الرسائل |

**هذه مقبولة** — لا تحتاج روابط مباشرة في القائمة.

### 4.3 ما هو موجود في الباك اند لكن غير مربوط بالقائمة أو الداشبورد 🔴

| الميزة | الموقع | المشكلة |
|--------|--------|---------|
| `SiteSettings` | `apps.core.models` | لا توجد صفحة إدارة في الداشبورد — يُدار فقط من `/admin/` |
| ملف المستخدم الشخصي | `UserProfile` | لا توجد صفحة "ملفي الشخصي" في الداشبورد |
| إحصائيات الكليات | `Faculty.count()` | لا تظهر في الصفحة الرئيسية للداشبورد |
| إحصائيات الدورات | `Course.count()` | لا تظهر في الصفحة الرئيسية للداشبورد |
| إحصائيات التصنيفات | `Category.count()` | لا تظهر في الصفحة الرئيسية للداشبورد |

---

## 5. عدم استغلال الباك اند بنسبة 100%

### 5.1 نماذج البيانات غير المستغلة في الداشبورد

#### University Model — الحقول غير المعروضة في القوالب
| الحقل | موجود في Form | موجود في Template |
|-------|--------------|------------------|
| `university_type` | ✅ | ❌ |
| `logo` | ✅ | ❌ |
| `main_image` | ✅ | ❌ |
| `video_url` | ✅ | ❌ |
| `admission_requirements` | ✅ | ❌ |
| `registration_section` | ✅ | ❌ |
| `related_majors` | ✅ | ❌ |
| `related_articles` | ✅ | ❌ |
| `publish_status` | ✅ | ❌ (يستخدم `is_published` الخاطئ) |
| كل حقول SEO | ✅ | ❌ |

#### Major Model — الحقول غير المعروضة في القوالب
| الحقل | موجود في Form | موجود في Template |
|-------|--------------|------------------|
| `major_category` | ✅ | ❌ |
| `main_image` | ✅ | ❌ |
| `bachelor_duration` | ✅ | ❌ |
| `master_duration` | ✅ | ❌ |
| `phd_duration` | ✅ | ❌ |
| `tuition_fees` | ✅ | ❌ |
| `study_language` | ✅ | ❌ |
| `practical_training` | ✅ | ❌ |
| `career_opportunities` | ✅ | ❌ |
| `why_study_section` | ✅ | ❌ |
| `how_to_apply_section` | ✅ | ❌ |
| `best_universities` | ✅ | ❌ |
| `cheap_universities` | ✅ | ❌ |
| `related_articles` | ✅ | ❌ |
| `SubjectsTableFormSet` | ✅ | ❌ |
| `SalaryTableFormSet` | ✅ | ❌ |
| `CountriesTableFormSet` | ✅ | ❌ |
| كل حقول SEO | ✅ | ❌ |

#### Institute Model — الحقول غير المعروضة في القوالب
| الحقل | موجود في Form | موجود في Template |
|-------|--------------|------------------|
| `institute_type` | ✅ | ❌ |
| `main_image` | ✅ | ❌ |
| `registration_requirements` | ✅ | ❌ |
| `registration_section` | ✅ | ❌ |
| `related_articles` | ✅ | ❌ |
| `CourseFormSet` | ✅ | ❌ |
| كل حقول SEO | ✅ | ❌ |

### 5.2 Views تمرر بيانات لكن القوالب لا تستخدمها

#### `UniversityListView` يمرر:
- `type_filter` — لكن القالب لا يعرض فلتر النوع
- `faculties_prefetch` — لكن القالب لا يعرض عدد الكليات

#### `DashboardHomeView` يمرر:
- `registration_leads` — لكن القالب لا يعرضه
- `contact_leads` — لكن القالب لا يعرضه
- `total_leads` — مكرر مع `lead_stats.total`

### 5.3 FormSets موجودة في الـ Views لكن غير موجودة في القوالب

| View | FormSet | موجود في Template |
|------|---------|------------------|
| `UniversityCreateView` | `UniversityFAQFormSet` | ❌ مفقود من create.html |
| `UniversityUpdateView` | `UniversityFAQFormSet` | ❌ مفقود من edit.html |
| `InstituteCreateView` | `CourseFormSet` | ❌ مفقود من create.html |
| `InstituteUpdateView` | `CourseFormSet` | ❌ مفقود من edit.html |
| `MajorCreateView` | `SubjectsTableFormSet` | ❌ مفقود من create.html |
| `MajorCreateView` | `SalaryTableFormSet` | ❌ مفقود من create.html |
| `MajorCreateView` | `CountriesTableFormSet` | ❌ مفقود من create.html |
| `MajorUpdateView` | `SubjectsTableFormSet` | ❌ مفقود من edit.html |
| `MajorUpdateView` | `SalaryTableFormSet` | ❌ مفقود من edit.html |
| `MajorUpdateView` | `CountriesTableFormSet` | ❌ مفقود من edit.html |

**هذا يعني**: لا يمكن إضافة كليات/دورات/مواد/رواتب/دول من الداشبورد حالياً رغم أن الكود كامل في الباك اند.

---

## 6. الأخطاء البرمجية في القوالب

### 6.1 استخدام حقول غير موجودة في الفورم

**في `universities/create.html` و `edit.html`**:
```html
<!-- خطأ: form.website غير موجود في UniversityForm -->
{{ form.website }}

<!-- خطأ: form.is_published غير موجود — الصحيح هو form.publish_status -->
{{ form.is_published }}
```

**في `institutes/create.html` و `edit.html`**:
```html
<!-- خطأ: form.website غير موجود في InstituteForm -->
{{ form.website }}

<!-- خطأ: form.is_published غير موجود -->
{{ form.is_published }}
```

**في `majors/create.html` و `edit.html`**:
```html
<!-- خطأ: form.is_published غير موجود -->
{{ form.is_published }}
```

### 6.2 عدم تطابق اسم البحث في الهيدر

**في `templates/components/header.html`**:
```html
<input type="text" name="q" ...>
```

**في `apps/search/views.py`** (SearchView):
```python
query = request.GET.get('query', '')  # يبحث عن 'query' وليس 'q'
```

**النتيجة**: البحث من الهيدر لا يعمل — يرسل `?q=...` لكن الـ view يقرأ `?query=...`.

### 6.3 قالب `list_page.html` غير مستخدم بشكل صحيح

`universities/list.html` يرث من `list_page.html` لكن:
- لا يمرر `items` (يمرر `universities`)
- لا يمرر `columns`
- لا يمرر `edit_url_name`
- لا يمرر `delete_url_name`

بينما `articles/list.html` يرث من `base.html` مباشرة ويبني الجدول يدوياً — وهذا أكثر وضوحاً.

---

## 7. ميزات الباك اند الكاملة غير المستغلة

### 7.1 `SiteSettings` — إدارة إعدادات الموقع

**موجود في**: `apps.core.models.SiteSettings`  
**الحقول**: `site_name`, `site_description`, `phone`, `email`, `whatsapp`, `registration_steps_title`, `registration_steps_content`  
**المشكلة**: لا توجد صفحة إدارة في الداشبورد — يُدار فقط من `/admin/`  
**الحل المطلوب**: إضافة URL + View + Template في الداشبورد

### 7.2 `UserProfile` — الملف الشخصي

**موجود في**: `apps.core.models.UserProfile`  
**المشكلة**: لا توجد صفحة "ملفي الشخصي" في الداشبورد  
**الحل المطلوب**: صفحة لتغيير كلمة المرور وبيانات المستخدم

### 7.3 `Redirect.hit_count` — إحصائيات الـ Redirects

**موجود في**: `apps.redirects.models.Redirect.hit_count`  
**المشكلة**: يتم تحديثه تلقائياً بالـ middleware لكن لا يظهر في الداشبورد الرئيسي  
**الحل المطلوب**: إضافة إحصائية في الصفحة الرئيسية

### 7.4 `Lead.utm_*` — بيانات التتبع

**موجود في**: `apps.leads.models.Lead` — حقول `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`  
**المشكلة**: لا تظهر في صفحة تفاصيل الرسالة أو في الإحصائيات  
**الحل المطلوب**: عرضها في `leads/detail.html` وإضافة تحليل UTM في الصفحة الرئيسية

### 7.5 `Lead.source_page` و `Lead.referrer`

**موجود في**: `apps.leads.models.Lead`  
**المشكلة**: لا تظهر في صفحة تفاصيل الرسالة  
**الحل المطلوب**: عرضها في `leads/detail.html`

---

## 8. مقارنة نسبة الاستغلال لكل قسم

| القسم | حقول الفورم | حقول في القالب | نسبة الاستغلال |
|-------|------------|----------------|----------------|
| المقالات | ~20 حقل | ~18 حقل | ✅ 90% |
| الرسائل | ~12 حقل | ~10 حقل | ✅ 83% |
| إعادة التوجيه | 5 حقول | 5 حقول | ✅ 100% |
| المستخدمون | 6 حقول | 6 حقول | ✅ 100% |
| الفئات | 3 حقول | 3 حقول | ✅ 100% |
| الوسوم | 2 حقول | 2 حقول | ✅ 100% |
| SEO Overview | — | — | ✅ 100% |
| **الجامعات** | **23 حقل** | **5 حقول** | **🔴 22%** |
| **المعاهد** | **19 حقل** | **4 حقول** | **🔴 21%** |
| **التخصصات** | **29 حقل** | **4 حقول** | **🔴 14%** |

---

## 9. أولويات الإصلاح

### الأولوية الأولى 🔴 (حرجة — تمنع إدخال البيانات)

1. **إصلاح `universities/create.html` و `edit.html`**
   - إضافة: `university_type`, `logo`, `main_image`, `video_url`
   - إضافة: `admission_requirements`, `registration_section`
   - إضافة: `related_majors`, `related_articles`
   - تصحيح: `is_published` → `publish_status`
   - إضافة: `UniversityFAQFormSet`
   - إضافة: قسم SEO كامل

2. **إصلاح `institutes/create.html` و `edit.html`**
   - إضافة: `institute_type`, `main_image`
   - إضافة: `registration_requirements`, `registration_section`
   - إضافة: `related_articles`
   - تصحيح: `is_published` → `publish_status`
   - إضافة: `CourseFormSet`
   - إضافة: قسم SEO كامل

3. **إصلاح `majors/create.html` و `edit.html`**
   - إضافة: `major_category`, `main_image`
   - إضافة: `bachelor_duration`, `master_duration`, `phd_duration`
   - إضافة: `tuition_fees`, `study_language`, `practical_training`, `career_opportunities`
   - إضافة: `why_study_section`, `how_to_apply_section`
   - إضافة: `best_universities`, `cheap_universities`, `related_articles`
   - تصحيح: `is_published` → `publish_status`
   - إضافة: `SubjectsTableFormSet`, `SalaryTableFormSet`, `CountriesTableFormSet`
   - إضافة: قسم SEO كامل

### الأولوية الثانية 🟡 (مهمة — تحسين الوظائف)

4. **إصلاح البحث في الهيدر**
   - تغيير `name="q"` إلى `name="query"` في `header.html`

5. **إضافة صفحة إدارة `SiteSettings` في الداشبورد**
   - URL: `dashboard/settings/`
   - View: `SiteSettingsView`
   - Template: `dashboard/settings/edit.html`
   - إضافة رابط في القائمة الجانبية (للـ super_admin)

6. **إصلاح `universities/list.html`**
   - تمرير `columns` و `edit_url_name` و `delete_url_name` بشكل صحيح
   - أو إعادة كتابته مثل `articles/list.html`

### الأولوية الثالثة 🟢 (تحسينات)

7. **إضافة صفحة الملف الشخصي للمستخدم**
   - URL: `dashboard/profile/`
   - View: `UserProfileView`
   - Template: `dashboard/profile/edit.html`

8. **إضافة إحصائيات UTM في صفحة تفاصيل الرسالة**
   - عرض `utm_source`, `utm_medium`, `utm_campaign` في `leads/detail.html`

9. **إضافة إحصائيات `hit_count` للـ Redirects في الصفحة الرئيسية**

10. **إضافة فلتر نوع الجامعة في قائمة الجامعات**
    - الـ view يدعمه بالفعل (`type_filter`) لكن القالب لا يعرضه

---

## 10. ملخص الأرقام

| المؤشر | القيمة |
|--------|--------|
| إجمالي URLs في الداشبورد | 50 URL |
| URLs مربوطة بالقائمة الجانبية | 11 URL |
| URLs تُفتح من داخل الصفحات | 39 URL |
| قوالب مكتملة | 35 قالب |
| قوالب ناقصة جزئياً | 6 قوالب |
| قوالب ناقصة بشكل حرج | 6 قوالب (create/edit للجامعات والمعاهد والتخصصات) |
| حقول فورم موجودة في الباك اند | 71 حقل |
| حقول فورم معروضة في القوالب | ~25 حقل |
| **نسبة استغلال الباك اند الإجمالية** | **~35%** |
| FormSets موجودة في الباك اند | 7 FormSets |
| FormSets معروضة في القوالب | 0 FormSets |
| أخطاء برمجية في القوالب | 4 أخطاء |

---

## 11. الخلاصة

المشروع يمتلك **باك اند احترافي ومكتمل** — النماذج والـ views والـ forms كلها جاهزة ومكتوبة بشكل صحيح. المشكلة الوحيدة هي أن **قوالب create/edit للجامعات والمعاهد والتخصصات** تم كتابتها بشكل مبسط جداً ولا تعكس ما هو موجود في الباك اند.

الأولوية القصوى هي إعادة كتابة هذه الـ 6 قوالب لتعرض كل الحقول المتاحة، مع إضافة صفحة إدارة `SiteSettings` في الداشبورد.

---

*آخر تحديث: مايو 2026*
