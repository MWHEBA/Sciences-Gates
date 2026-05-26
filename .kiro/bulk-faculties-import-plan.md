# خطة تنفيذ: زر "إضافة كليات جماعية" من كود Elementor Accordion

## نظرة عامة

إضافة زر **"إضافة كليات جماعية"** بجوار زر "إضافة كلية" في صفحة `/dashboard/universities/create/`، يقوم بتحليل كود HTML من Elementor Accordion وتحويله تلقائياً إلى كليات وبرامج داخل النموذج.

---

## تحليل المدخلات

### الأنماط الثلاثة المدعومة

الكود الوارد من Elementor يأتي بثلاثة أشكال، كلها تحتوي على نفس البنية الجوهرية:

```
النمط 1: <div class="elementor-accordion">...</div>
النمط 2: <div class="elementor-widget-container"><div class="elementor-accordion">...</div></div>
النمط 3: <div class="elementor-element ... elementor-widget-accordion ..."><div class="elementor-widget-container"><div class="elementor-accordion">...</div></div></div>
```

### البنية الجوهرية لكل كلية (accordion item)

```html
<div class="elementor-accordion-item">
  <!-- عنوان الكلية -->
  <div class="elementor-tab-title">
    <a class="elementor-accordion-title">اسم الكلية هنا</a>
  </div>
  <!-- محتوى البرامج -->
  <div class="elementor-tab-content">
    <table>
      <tbody>
        <tr><th>التخصصات</th><th>المدة الدراسية</th><th>الرسوم السنوية</th></tr>
        <tr><td>اسم البرنامج</td><td>المدة</td><td>الرسوم</td></tr>
        ...
      </tbody>
    </table>
  </div>
</div>
```

### حالات خاصة يجب التعامل معها

| الحالة | التفاصيل |
|--------|----------|
| الصف الأول `<th>` | يجب تخطيه — هو header وليس بيانات |
| `<p>` داخل `<td>` | مثل `<td><p>4,333 دولار</p></td>` — استخراج النص فقط |
| وسوم HTML داخل النص | تنظيف كامل بـ `textContent` |
| مسافات زائدة | `trim()` على كل قيمة |
| كليات بدون جدول | تُضاف بدون برامج |
| جداول بدون header row | التعامل مع كل الصفوف كبيانات |

---

## الخطة التنفيذية

### الملفات المتأثرة

```
static/js/faculty-programs-manager.js   ← إضافة زر + دالة الاستيراد
static/js/faculty-programs-manager.min.js ← يُحدَّث بـ npm run build:js
templates/dashboard/universities/create.html ← لا تعديل مطلوب
templates/dashboard/universities/edit.html  ← لا تعديل مطلوب
```

> **ملاحظة:** لا نحتاج ملف JS جديد — كل الكود يضاف داخل `FacultyProgramsManager` كـ method جديدة.

---

### الخطوة 1 — إضافة زر "إضافة كليات جماعية" في الـ HTML المُنشأ

**الموقع:** دالة `attachAddHandler()` في `FacultyProgramsManager`

**التعديل:** إضافة زر جديد بجوار زر "إضافة كلية" الموجود في الـ DOM.

```javascript
// في attachAddHandler()
const bulkImportBtn = document.getElementById('faculty-bulk-import-btn');
if (bulkImportBtn) {
    bulkImportBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.openBulkImportModal();
    });
}
```

**التعديل في `create.html`:** إضافة الزر في الـ template بجوار `faculty-add-btn`:

```html
<div class="faculty-section__header">
    <div class="faculty-section__title">...</div>
    <div style="display: flex; gap: 8px;">
        <button type="button" class="faculty-bulk-import-btn" id="faculty-bulk-import-btn">
            <!-- أيقونة import -->
            إضافة كليات جماعية
        </button>
        <button type="button" class="faculty-add-btn" id="faculty-add-btn">
            <!-- أيقونة + -->
            إضافة كلية
        </button>
    </div>
</div>
```

---

### الخطوة 2 — بناء Modal الاستيراد

**الموقع:** method جديدة `createBulkImportModal()` في `FacultyProgramsManager`

**البنية:**

```
Modal
├── Header: "استيراد كليات من Elementor"
├── Body
│   ├── Step 1 — input
│   │   ├── تعليمات الاستخدام
│   │   └── textarea لاستقبال الكود
│   └── Step 2 — preview
│       ├── إحصائيات (عدد الكليات، إجمالي البرامج)
│       └── جدول معاينة قابل للتعديل
│           ├── اسم الكلية
│           └── عدد البرامج
└── Footer
    ├── زر إلغاء
    ├── زر التالي (step 1)
    └── زر تأكيد الاستيراد (step 2)
```

**CSS:** يستخدم نفس أنماط `.bulk-paste-modal` الموجودة في `bulk-paste.css` — لا CSS جديد.

---

### الخطوة 3 — دالة تحليل كود Elementor

**الموقع:** method جديدة `parseElementorAccordion(htmlString)` في `FacultyProgramsManager`

**خوارزمية التحليل:**

```
1. إنشاء DOMParser لتحليل الـ HTML string بأمان
2. البحث عن .elementor-accordion (بغض النظر عن العمق)
3. لكل .elementor-accordion-item:
   a. استخراج اسم الكلية من .elementor-accordion-title → textContent.trim()
   b. البحث عن table داخل .elementor-tab-content
   c. لكل <tr> داخل <tbody>:
      - تخطي الصف إذا كان يحتوي على <th> (header row)
      - استخراج النص من كل <td> بـ textContent.trim()
      - تجاهل الصفوف الفارغة
   d. بناء كائن { name, programs: [{name, duration, tuition_fees}] }
4. إرجاع مصفوفة الكليات
```

**مثال الناتج:**

```javascript
[
  {
    name: "تخصصات السنة التحضيرية في جامعة لينكولن",
    programs: [
      { name: "السنة التحضيرية في العلوم / Foundation in Science", duration: "1 سنة", tuition_fees: "3,500 دولار" },
      { name: "السنة التحضيرية في الفنون / Foundation in Arts", duration: "1 سنة", tuition_fees: "3,500 دولار" },
    ]
  },
  {
    name: "كلية الطب ضمن جامعة لينكولن ماليزيا",
    programs: [...]
  }
]
```

---

### الخطوة 4 — دالة الاستيراد الفعلي

**الموقع:** method جديدة `importFaculties(faculties)` في `FacultyProgramsManager`

**الخوارزمية:**

```
لكل كلية في المصفوفة:
  1. استدعاء this.addFaculty() لإنشاء الكلية
  2. الحصول على آخر faculty-item مُضاف
  3. ملء حقل الاسم بـ faculty.name
  4. فتح programs-wrapper (display: block)
  5. لكل برنامج في faculty.programs:
     a. استدعاء this.addProgram(facultyItem)
     b. ملء حقول name, duration, tuition_fees في آخر صف مُضاف
```

**ملاحظة مهمة:** `addFaculty()` و `addProgram()` موجودتان بالفعل — نستخدمهما مباشرة بدون إعادة كتابة.

---

### الخطوة 5 — معاينة قبل الاستيراد

**الموقع:** method جديدة `renderImportPreview(faculties)` في `FacultyProgramsManager`

**الشكل:**

```
┌─────────────────────────────────────────┐
│ تم العثور على 3 كليات، 11 برنامج        │
├─────────────────────────────────────────┤
│ ✓ تخصصات السنة التحضيرية (3 برامج)     │
│ ✓ كلية الطب (6 برامج)                  │
│ ✓ كلية طب الأسنان (2 برامج)            │
└─────────────────────────────────────────┘
```

---

### الخطوة 6 — معالجة الأخطاء

| الحالة | الاستجابة |
|--------|-----------|
| HTML فارغ | رسالة: "الرجاء لصق كود HTML" |
| لا يوجد `.elementor-accordion` | رسالة: "لم يتم العثور على accordion في الكود" |
| accordion موجود لكن بدون items | رسالة: "لا توجد كليات في الكود" |
| كلية بدون اسم | تُضاف باسم "كلية بدون اسم" |
| برنامج بعدد أعمدة أقل من 3 | يُتخطى مع تحذير في المعاينة |

---

## ترتيب التنفيذ

```
1. تعديل create.html — إضافة زر "إضافة كليات جماعية"
2. إضافة createBulkImportModal() في faculty-programs-manager.js
3. إضافة parseElementorAccordion() في faculty-programs-manager.js
4. إضافة renderImportPreview() في faculty-programs-manager.js
5. إضافة importFaculties() في faculty-programs-manager.js
6. ربط الأحداث في attachAddHandler()
7. npm run build:js لتحديث الـ minified file
```

---

## ملاحظات تقنية

- **لا DOMParser مخاوف أمنية:** الكود يُحلَّل في بيئة معزولة ولا يُنفَّذ
- **لا CSS جديد:** نستخدم `.bulk-paste-modal` و `.bulk-paste-btn` الموجودين
- **لا ملفات جديدة:** كل الكود داخل `faculty-programs-manager.js`
- **الـ edit.html مدعوم تلقائياً** لأنه يستخدم نفس الـ JS
