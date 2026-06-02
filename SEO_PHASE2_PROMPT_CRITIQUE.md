# SEO Analyzer Phase 2 — نقد الـ Prompt والـ Prompt الصح

**تاريخ المراجعة:** 31 مايو 2026  
**مرجع:** البرومبت الأصلي "Implement SEO Analyzer Phase 2 using Rendered Page Analysis"  
**سياق:** يُقرأ هذا المستند بجانب `PROJECT_SEO_EDITOR_READINESS_REPORT.md`

---

## القسم الأول: نقد الـ Prompt الأصلي

### المشكلة الجوهرية: تناقض داخلي حاد

البرومبت يبدأ بجملة حاسمة:

> *"The final SEO score must be based on the fully rendered page HTML exactly as search engines would see it."*

وفي نفس الوقت `PROJECT_SEO_EDITOR_READINESS_REPORT.md` يوثّق بوضوح:

> *"Lack of Draft Preview URL — The editor does not support previewing draft articles using secure tokens, meaning authors must publish an article to preview its design."*

**الخلاصة:** البرومبت يطلب تحليل الـ rendered page بما فيها الـ draft pages — لكن الـ draft preview غير موجود أصلاً وغير مبني في المشروع. البرومبت يعامل هذا كـ "requirement جاهز للتنفيذ" بدلاً من الاعتراف بأنه infrastructure مفقودة تحتاج بناء منفصل أولاً.

---

### النقد التفصيلي

---

#### 🔴 مشكلة 1: الـ Prompt يطلب "Phase 2" لكنه فعلياً بناء جديد من الصفر

الـ Phase 1 الموجود يعمل على تحليل editor fields مباشرة ويحفظ:
- `seo_score`
- `seo_grade`  
- `seo_critical_count`
- `seo_warning_count`
- `seo_last_analysis`
- `SEOAnalysisDetail` model لتفاصيل الـ audit

البرومبت الجديد يقول:

> *"This is not sufficient. The analyzer must evaluate final HTML, final heading structure, final links..."*

هذا ليس extension — هذا **تغيير فلسفي كامل** في كيفية حساب الـ score. الـ Agent لن يعرف هل يعدّل على الكود الحالي أم يبني نظاماً موازياً.

**ما ينقص البرومبت:** جملة واضحة تقول:
> *"Phase 1 exists and يجب الإبقاء عليه. Phase 2 يضيف rendered analysis layer فوقه، ولا يحذف ما هو موجود."*

---

#### 🔴 مشكلة 2: طريقة الـ Rendering غامضة تقنياً

البرومبت يكتب:

```
Page URL → Render HTML → Analyze HTML → Generate Score
```

لكن في Django هناك 3 طرق مختلفة لعمل rendering، كل واحدة لها تبعات مختلفة:

| الطريقة | التعقيد | الدقة | المشكلة |
|---------|---------|-------|---------|
| `RequestFactory` + view function | منخفض | متوسطة | قد يفوّت بعض الـ context processors |
| `Client().get(url)` داخلياً | متوسط | عالية | يتطلب published content أو session خاص |
| Headless browser (Playwright) | عالٍ جداً | كاملة | out of scope كلياً للمشروع الحالي |

الـ Phase 1 الحالي بنى الـ rendering باستخدام `RequestFactory` مع محاكاة كاملة للـ session والـ host. هذا القرار موثَّق في `apps/seo/views.py` وجاء بعد دراسة.

البرومبت الجديد لا يحدد: هل نستخدم نفس الأسلوب؟ هل يتوسَّع عليه؟ هل يُستبدل؟

**النتيجة:** الـ Agent سيختار بنفسه وقد يختار غلط أو يعيد اختراع ما هو موجود.

---

#### 🔴 مشكلة 3: الـ Draft Preview هو مشروع كامل، وليس متطلباً عابراً

البرومبت يطلب:

```
/dashboard/preview/article/{id}/
/dashboard/preview/university/{id}/
/dashboard/preview/institute/{id}/
/dashboard/preview/major/{id}/
```

ويشترط:
> *"Preview URLs must render the page exactly as the public frontend would render it."*

هذا يعني بناء:

1. **4 preview views منفصلة** — كل واحدة تستدعي نفس الـ context الخاص بالـ public view المقابلة لها
2. **نظام أمان** للـ draft content — يمنع الوصول العام مع السماح للـ dashboard users
3. **Secure token system** أو session-based access للـ unpublished content
4. **اندماج الـ analyzer** مع هذه الـ URLs بشكل يطلب الـ HTML داخلياً

البرومبت يذكر هذا في سطر واحد كأنه بند بسيط. في الواقع هو **الجزء الأكثر تعقيداً في الـ Phase 2 كله.**

**أسئلة غائبة بالكامل:**
- هل الـ preview URL يتطلب login؟ (يُفترض نعم، لكن لم يُذكر)
- كيف يُمنَع الـ public access للـ draft content؟
- هل الـ analyzer يستدعي الـ preview URL عبر HTTP request داخلي؟ وبأي credentials؟
- ما العلاقة بين الـ preview URL والـ public URL؟ هل نفس الـ template أم template مختلف؟

---

#### 🔴 مشكلة 4: التعارض بين نتيجتين غير محسوم

البرومبت يقول في نفس الوقت:

> *"Editor Checks ≠ Final SEO Score"*  
> *"Do NOT remove editor-level checks."*

هذا يعني أن النظام النهائي سيكون لديه:
- **نتيجة A:** من تحليل الـ editor fields (Phase 1 — موجود)
- **نتيجة B:** من تحليل الـ rendered page (Phase 2 — مطلوب)

**الأسئلة الغائبة:**
- أيهما يُعرَض للمستخدم في الـ dashboard form بشكل رئيسي؟
- أيهما يُحفَظ في `seo_score` في الـ database؟
- هل يُضاف `rendered_seo_score` جديد بجانب `seo_score` الحالي؟
- ما العلاقة بين `SEOAnalysisDetail` الموجود والنتائج الجديدة؟
- هل تُحذف نتيجة Phase 1 من الـ UI أم تبقى كـ "editor hints" منفصلة؟

بدون إجابة على هذه الأسئلة، الـ Agent سيتخذ قرارات تصميمية مصيرية بنفسه — وقد تتعارض مع توقعاتك.

---

#### 🟠 مشكلة 5: "Keep current analyzer UI" + "Expand it" = تعارض

البرومبت يقول:

> *"Keep current analyzer UI. Expand it to include: SEO Score, Google Preview, Heading Tree, Schema Analysis, Internal Links Analysis, Images Analysis, Meta Analysis, Content Analysis, Recommendations"*

هذا ليس "keep" — هذا إضافة 7 إلى 8 sections جديدة كاملة. لو الـ Agent أخذ كلمة "keep" حرفياً، سيحاول الإضافة فوق الـ layout الحالي بطريقة قد تكون مشوَّهة.

**ما ينقص البرومبت:** وصف للـ layout المستهدف:
- هل sections جديدة في نفس الـ panel؟
- هل tabs منفصلة؟
- هل accordion sections؟
- ما ترتيب الأقسام؟

---

#### 🟠 مشكلة 6: أمان الـ Preview غير محدد

الـ draft content حساس — لم يُنشر بعد ويجب ألا يكون متاحاً للعموم. البرومبت لا يذكر:

- هل الـ preview URL محمية بـ `LoginRequiredMixin`؟
- هل هناك secure token في الـ URL (مثل `/preview/{id}/?token=abc123`)?
- هل الـ token له expiry time؟
- هل الـ preview يُعرَض في iframe داخل الـ dashboard أم في tab جديد؟

هذا الغياب قد يؤدي إلى ثغرة أمنية حقيقية إذا نفَّذ الـ Agent preview URLs بدون حماية كافية.

---

#### 🟠 مشكلة 7: "Future Compatibility" كـ Requirement يولِّد Over-Engineering

البرومبت يقول:

> *"Design the analyzer so future phases can add: Readability analysis, Keyword density, AI recommendations, Competitor comparison without refactoring the core architecture."*

هذا مبدأ تصميمي صحيح من الناحية النظرية، لكن كـ requirement قابل للتنفيذ الآن — هو خطأ.

**لماذا؟** الـ Agent سيحاول بناء:
- Abstract base classes للـ analyzers
- Plugin registry system
- Interface contracts لكل نوع تحليل مستقبلي

... وكل هذا التعقيد لحاجات غير موجودة الآن، في مشروع حجمه محدود.

الصح: اكتبه كـ design note لا كـ requirement:
> *"NOTE: Keep the architecture modular enough to extend later, but do not over-abstract prematurely."*

---

#### 🟡 مشكلة 8: الـ Prompt لا يُشير إلى ما هو موجود بالفعل

البرومبت يُعطي انطباعاً بأن النظام الحالي بدائي. لكن `apps/seo/services/` يحتوي فعلاً على:

- `html_parser.py` — يحلل الـ HTML
- `page_analyzer.py` — يحلل الصفحة
- `scoring.py` — يحسب الـ score
- `schema_validator.py` — يتحقق من الـ schema
- `content_profiles.py` — profiles مختلفة لكل نوع محتوى
- `model_checks.py` — يتحقق من الـ DB fields

**الخطر:** الـ Agent قد يُعيد بناء هذه الـ services من الصفر بدلاً من الاستفادة منها وتوسيعها.

---

### جدول ملخص المشاكل

| # | المشكلة | مستوى الخطورة | التأثير المحتمل |
|---|---------|--------------|----------------|
| 1 | Phase 2 يتجاهل Phase 1 الموجود | 🔴 حرجة | الـ Agent يُعيد البناء أو يتعارض مع الموجود |
| 2 | طريقة الـ Rendering غامضة | 🔴 حرجة | اختيار خاطئ يُلغي ميزة الـ RequestFactory الحالية |
| 3 | Draft Preview = مشروع مستقل لا متطلب عابر | 🔴 حرجة | underestimated scope — يؤخر التنفيذ |
| 4 | تعارض بين نتيجتين دون حسم | 🔴 حرجة | الـ Agent يتخذ قرارات DB مصيرية بنفسه |
| 5 | "Keep UI" + إضافة 8 sections | 🟠 عالية | UI مشوَّهة أو ترتيب غير منطقي |
| 6 | أمان الـ Preview غير محدد | 🟠 عالية | ثغرة أمنية محتملة في الـ draft URLs |
| 7 | Future compatibility كـ requirement | 🟠 عالية | over-engineering غير مبرر |
| 8 | لا يذكر الـ services الموجودة في `apps/seo/services/` | 🟡 متوسطة | إعادة اختراع ما هو مبني |

---

---

## القسم الثاني: الـ Prompt الصح

---

```
==================================================
SEO Analyzer Phase 2 — Rendered Page Analysis Layer
==================================================

CONTEXT
=======

Phase 1 is already fully implemented and must NOT be touched or removed.

Phase 1 (existing) works as follows:
- Renders the page using Django RequestFactory (see apps/seo/views.py)
- Analyzes rendered HTML via services in apps/seo/services/
  (html_parser.py, page_analyzer.py, scoring.py, schema_validator.py,
   content_profiles.py, model_checks.py)
- Saves results in SEOMixin fields: seo_score, seo_grade,
  seo_critical_count, seo_warning_count, seo_last_analysis
- Saves detailed audit log in SEOAnalysisDetail model (JSONField)
- Exposes AJAX endpoint: dashboard/seo/analyze/<content_type>/<pk>/
- Exposes detail endpoint: dashboard/seo/detail/<content_type>/<pk>/
- Displays results in dashboard form via the existing SEO panel

Phase 2 adds a new capability on top of Phase 1.
Phase 2 does NOT replace Phase 1 score logic.


OBJECTIVE
=========

Phase 2 adds a dedicated Draft Preview System.

Currently, the SEO analyzer can only analyze published pages
because the public frontend requires publish_status='published'.

Phase 2 must allow the analyzer to analyze DRAFT content
before it is published, using secure preview URLs.


SCOPE — PHASE 2 ONLY
=====================

Phase 2 is ONLY the Draft Preview System.

It does NOT include:
- New scoring algorithms (Phase 1 handles scoring)
- New UI sections (planned for Phase 3)
- Readability analysis
- Keyword density
- AI suggestions
- Competitor comparison

These are future phases. Do NOT implement them now.
Do NOT add abstract layers or plugin systems for them.
Keep the code simple and direct.


STEP 1: Build Secure Draft Preview URLs
========================================

Create 4 preview views inside the dashboard app:

  /dashboard/preview/article/<int:pk>/
  /dashboard/preview/university/<int:pk>/
  /dashboard/preview/institute/<int:pk>/
  /dashboard/preview/major/<int:pk>/

Rules for each preview view:

1. Access Control:
   - Requires login (LoginRequiredMixin)
   - Requires ContentAdminRequiredMixin OR SuperAdminRequiredMixin
   - No public access — not even with a token
   - Return 403 if user is not authorized

2. Rendering:
   - The preview must use the EXACT same template and context
     as the public frontend view for that content type
   - Use the same view logic from the public app
     (e.g. universities/views.py UniversityDetailView)
   - Include all context: breadcrumbs, faqs, faculties, related_articles, etc.
   - Do NOT create new templates — reuse the existing public templates

3. Draft Support:
   - The preview must work for BOTH published and unpublished content
   - Do NOT filter by publish_status in the preview view
   - Add a visible banner at the top of the preview:
     "هذه معاينة مسودة — غير منشورة للعموم"
     (Use a simple injected div, not a template change)

4. URL Registration:
   - Register all 4 URLs in apps/dashboard/urls.py
   - Use the app_name = 'dashboard' namespace:
     dashboard:preview_article, dashboard:preview_university,
     dashboard:preview_institute, dashboard:preview_major


STEP 2: Connect Preview to Existing SEO Analyzer
=================================================

The existing SEO analyzer (Phase 1) uses RequestFactory internally
to render pages. It is invoked via:
  dashboard/seo/analyze/<content_type>/<pk>/

Currently it always renders the public URL.

Modify the existing analyzer endpoint to accept an optional parameter:
  ?preview=1

When ?preview=1 is passed:
- Use the dashboard preview URL instead of the public URL
- The RequestFactory request must simulate an authenticated
  staff user to pass the LoginRequired check on the preview view
- Render the preview URL and analyze its HTML output
- The resulting score and analysis are temporary (not saved to DB)
  Return them in the AJAX response as usual
- Add a flag in the JSON response: "source": "preview"

When ?preview=1 is NOT passed (default):
- Behavior is unchanged from Phase 1
- Uses public URL, saves score to DB as usual
- Response includes "source": "published"

The existing score fields in SEOMixin (seo_score, seo_grade, etc.)
are ONLY updated from published page analysis.
Preview analysis results are NOT saved to the database.


STEP 3: Add Preview Button in Dashboard Forms
=============================================

In the following dashboard form templates:
  templates/dashboard/universities/form.html
  templates/dashboard/institutes/form.html  (create.html + edit.html)
  templates/dashboard/majors/form.html  (create.html + edit.html)
  templates/dashboard/articles/form.html

Add two buttons in the SEO panel section:

Button 1 — "تحليل المسودة" (Analyze Draft)
  - Visible only when the content is unpublished (publish_status != 'published')
  - On click: calls the existing AJAX endpoint with ?preview=1
  - Shows the same results panel as the existing analyze button
  - Results are clearly labeled: "تحليل مسودة — لن يُحفَظ"

Button 2 — "معاينة الصفحة" (Preview Page)
  - Always visible
  - On click: opens the preview URL in a new browser tab
  - Uses the pk from the current form

For the "تحليل المسودة" button:
- Use the same JS logic as the existing "تحليل SEO" button
- Just append ?preview=1 to the AJAX URL
- Add a visual indicator in the results panel when source == "preview"
  Example: a yellow banner saying "هذه نتائج مؤقتة للمسودة"


DATABASE CHANGES
================

None required for Phase 2.

- Do NOT add new fields to SEOMixin
- Do NOT create new models
- Preview analysis results are transient (AJAX only, not persisted)
- Existing seo_score and related fields remain unchanged in behavior


SECURITY REQUIREMENTS
=====================

1. Preview views must reject unauthenticated requests with HTTP 302
   redirect to dashboard login, not HTTP 200 with empty content

2. Preview views must reject non-staff users with HTTP 403

3. The internal RequestFactory call inside the analyzer (for ?preview=1)
   must use a simulated authenticated staff user
   Do NOT expose the preview URL to the public internet

4. No token-based access — session-based authentication only


WHAT TO MODIFY
==============

Files to CREATE (new):
  [none — no new service files needed]

Files to MODIFY:
  apps/dashboard/urls.py
    → Add 4 preview URL patterns

  apps/dashboard/views.py
    → Add 4 preview view classes (one per content type)
    → Modify the internal rendering logic in the SEO analyzer
      to handle ?preview=1 parameter

  templates/dashboard/universities/form.html
  templates/dashboard/institutes/create.html
  templates/dashboard/institutes/edit.html
  templates/dashboard/majors/create.html
  templates/dashboard/majors/edit.html
  templates/dashboard/articles/form.html
    → Add "تحليل المسودة" and "معاينة الصفحة" buttons in SEO panel

Files to NOT TOUCH:
  apps/seo/services/  (all files — Phase 1 logic, do not modify)
  apps/seo/models.py  (no DB changes)
  apps/core/models.py (SEOMixin — no new fields)
  Any public frontend templates (universities, institutes, majors, articles)


EXPECTED OUTPUT
===============

After Phase 2:

1. A content admin can open an unpublished article/university/institute/major
   in the dashboard form

2. They click "معاينة الصفحة" → a new tab opens showing the draft
   exactly as it would look when published, with a clear "مسودة" banner

3. They click "تحليل المسودة" → the SEO panel runs the full Phase 1
   analysis on the draft content, shows the score and recommendations,
   but does NOT save anything to the database

4. When the content is published and they click the regular "تحليل SEO"
   button → behavior is identical to Phase 1, score is saved to DB

5. No regressions in Phase 1 behavior


OUT OF SCOPE FOR PHASE 2
=========================

The following are planned for future phases.
Do NOT implement them now. Do NOT add placeholders for them.

- Google Preview (SERP simulation)
- Heading Tree visualization
- Internal Links count and analysis
- Images without alt text report
- Schema validation UI
- Content length bar
- Recommendations engine UI
- Readability score
- Keyword density
- AI suggestions
- Competitor analysis
==================================================
```

---

## القسم الثالث: لماذا هذا الـ Prompt أفضل؟

| البُعد | الـ Prompt الأصلي | الـ Prompt الصح |
|-------|-----------------|----------------|
| **Scope** | ضبابي — "Phase 2" يضم 10+ features | محدد — Phase 2 = Draft Preview فقط |
| **الـ Phase 1** | لا يُذكر كأساس موجود | موثَّق بالتفصيل كنقطة انطلاق |
| **Rendering Method** | "Render HTML" بلا تفاصيل | `RequestFactory` موثَّق + شرط `?preview=1` |
| **Draft Preview** | سطر واحد ضمن requirements | Step كامل مع rules و security و behavior |
| **الـ DB** | غامض — هل يُضاف fields؟ | صريح: لا تغييرات في DB |
| **الأمان** | غائب تماماً | محدد: login required, no public access, HTTP 403 |
| **ما لا يُلمَس** | غير محدد | قائمة صريحة بكل الملفات المحظورة |
| **Future compatibility** | requirement يولّد over-engineering | مُزال بالكامل من الـ scope |
| **Score DB conflict** | غير محسوم | صريح: preview لا يُحفَظ، published يُحفَظ |
| **UI Changes** | "Keep UI + expand" = تناقض | أزرار محددة بالاسم والسلوك والشرط |

---

*هذا المستند يُحدَّث كلما تطورت متطلبات الـ Phase 2.*
