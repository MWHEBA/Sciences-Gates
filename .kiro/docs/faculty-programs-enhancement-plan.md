# خطة تطوير قسم الكليات والبرامج الأكاديمية
## نظام إدارة ديناميكي احترافي متكامل

---

## 📋 جدول المحتويات

1. [التحليل الحالي](#التحليل-الحالي)
2. [المتطلبات من العرض الفني](#المتطلبات-من-العرض-الفني)
3. [الفجوات والمشاكل](#الفجوات-والمشاكل)
4. [الرؤية المستهدفة](#الرؤية-المستهدفة)
5. [البنية التقنية المقترحة](#البنية-التقنية-المقترحة)
6. [تصميم واجهة المستخدم](#تصميم-واجهة-المستخدم)
7. [خطة التنفيذ](#خطة-التنفيذ)
8. [الاعتبارات الفنية](#الاعتبارات-الفنية)

---

## 🔍 التحليل الحالي

### البنية الموجودة

#### Models (قاعدة البيانات)
```
University (الجامعة)
  ├── Faculty (الكلية)
  │     ├── name: CharField
  │     ├── sort_order: PositiveIntegerField
  │     └── programs: RelatedManager
  │
  └── Program (البرنامج)
        ├── name: CharField
        ├── duration: CharField
        ├── tuition_fees: CharField
        └── sort_order: PositiveIntegerField
```

#### الوضع الحالي في لوحة التحكم
- **Faculty Formset**: نموذج بسيط جداً يحتوي فقط على:
  - حقل اسم الكلية
  - حقل ترتيب يدوي (رقم)
  - checkbox للحذف

- **لا يوجد إدارة للبرامج داخل الكليات** في نموذج إنشاء الجامعة
- البرامج يتم إدارتها بشكل منفصل (غير واضح من الكود الحالي)

#### الوضع في الفرونت إند (صفحة الجامعة)
- **Accordion للكليات**: كل كلية تفتح وتعرض البرامج بداخلها
- **عرض البرامج**: 
  - اسم البرنامج
  - مدة الدراسة
  - الرسوم السنوية
- **التصميم**: احترافي مع Alpine.js للـ accordion

---

## 📄 المتطلبات من العرض الفني

### النص الأصلي:
> **قسم التخصصات والكليات سيتم بناؤه كبيانات منظمة وليس كنص حر، بحيث يحتوي كل Accordion على اسم الكلية، وداخل كل كلية جدول يشمل: اسم التخصص، مدة الدراسة، والرسوم الدراسية.**

### التفسير:
1. **بيانات منظمة** — ليس HTML حر، بل حقول structured
2. **Accordion** — كل كلية accordion منفصل
3. **جدول البرامج** — داخل كل كلية:
   - اسم التخصص/البرنامج
   - مدة الدراسة
   - الرسوم الدراسية

### المتطلبات الإضافية المستنتجة:
- إدارة ديناميكية كاملة من لوحة التحكم
- إضافة/حذف/تعديل الكليات والبرامج
- إعادة ترتيب سهلة
- تجربة مستخدم احترافية


---

## ⚠️ الفجوات والمشاكل

### 1. عدم وجود إدارة متكاملة
- **المشكلة**: لا يمكن إضافة البرامج داخل الكليات في نفس نموذج إنشاء الجامعة
- **التأثير**: يحتاج المستخدم لإنشاء الجامعة أولاً، ثم العودة لإضافة الكليات والبرامج بشكل منفصل
- **الحل المطلوب**: Nested formsets — كليات وبرامج في نموذج واحد

### 2. واجهة مستخدم بسيطة جداً
- **المشكلة**: الواجهة الحالية للكليات بدائية (حقل نص + رقم ترتيب + checkbox)
- **التأثير**: تجربة مستخدم ضعيفة، صعوبة في إدارة عدد كبير من الكليات
- **الحل المطلوب**: واجهة ديناميكية مع drag & drop، أزرار واضحة، عرض هرمي

### 3. عدم وجود معاينة مباشرة
- **المشكلة**: لا يمكن رؤية كيف ستظهر البيانات في الفرونت إند أثناء الإدخال
- **التأثير**: احتمالية أخطاء في الإدخال، عدم وضوح النتيجة النهائية
- **الحل المطلوب**: Live preview أو على الأقل تنسيق يشبه العرض النهائي

### 4. صعوبة إعادة الترتيب
- **المشكلة**: الترتيب يدوي عبر إدخال أرقام
- **التأثير**: صعوبة في تغيير الترتيب، احتمالية تكرار الأرقام
- **الحل المطلوب**: Drag & drop مع تحديث تلقائي للترتيب

### 5. عدم وجود validation متقدم
- **المشكلة**: لا يوجد تحقق من:
  - تكرار أسماء الكليات
  - وجود كلية بدون برامج
  - صحة تنسيق الرسوم والمدة
- **الحل المطلوب**: Validation شامل على مستوى الفورم والـ JS


---

## 🎯 الرؤية المستهدفة

### تجربة المستخدم المثالية

#### في لوحة التحكم (Dashboard)
```
┌─────────────────────────────────────────────────────────────┐
│  الكليات والبرامج الأكاديمية                    [+ إضافة كلية] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⋮⋮ [1] كلية الهندسة                          [▼] [×]      │
│      ├─ هندسة البرمجيات  │ 4 سنوات  │ 25,000 RM  [×]      │
│      ├─ هندسة الحاسوب    │ 4 سنوات  │ 24,000 RM  [×]      │
│      └─ [+ إضافة برنامج]                                    │
│                                                             │
│  ⋮⋮ [2] كلية الطب                             [▼] [×]      │
│      ├─ الطب البشري      │ 6 سنوات  │ 45,000 RM  [×]      │
│      ├─ طب الأسنان       │ 5 سنوات  │ 40,000 RM  [×]      │
│      └─ [+ إضافة برنامج]                                    │
│                                                             │
│  ⋮⋮ [3] كلية إدارة الأعمال                    [▼] [×]      │
│      └─ [+ إضافة برنامج]                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

الرموز:
⋮⋮ = مقبض السحب (Drag handle)
[▼] = توسيع/طي البرامج
[×] = حذف
[+] = إضافة
```

#### المميزات المطلوبة:
1. **إضافة كلية جديدة** — زر واضح في الأعلى
2. **إضافة برامج داخل كل كلية** — زر داخل كل كلية
3. **السحب والإفلات** — لإعادة ترتيب الكليات والبرامج
4. **توسيع/طي** — لإخفاء/إظهار البرامج داخل الكلية
5. **حذف سريع** — أيقونة × واضحة
6. **ترقيم تلقائي** — يتحدث مع كل تغيير
7. **حالة فارغة** — رسالة واضحة عند عدم وجود كليات


---

## 🏗️ البنية التقنية المقترحة

### 1. Django Models (لا تحتاج تعديل)
النماذج الحالية كافية:
- `Faculty` — الكلية
- `Program` — البرنامج (مرتبط بالكلية)

### 2. Django Forms (تحتاج تطوير كبير)

#### الوضع الحالي:
```python
# فقط formset للكليات
UniversityFacultyFormSet = inlineformset_factory(
    University, Faculty,
    fields=['name', 'sort_order'],
    extra=0, max_num=100
)
```

#### المطلوب:
```python
# Nested Formsets — كليات وبرامج معاً

# 1. Program Formset (داخل كل كلية)
ProgramFormSet = inlineformset_factory(
    Faculty, Program,
    fields=['name', 'duration', 'tuition_fees', 'sort_order'],
    extra=0, max_num=50, can_delete=True
)

# 2. Faculty Form مع Programs
class FacultyFormWithPrograms(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ['name', 'sort_order']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ربط ProgramFormSet بهذا الفورم
        if self.instance.pk:
            self.programs = ProgramFormSet(
                instance=self.instance,
                prefix=f'programs-{self.prefix}'
            )

# 3. University Faculty Formset
UniversityFacultyFormSet = inlineformset_factory(
    University, Faculty,
    form=FacultyFormWithPrograms,
    extra=0, max_num=100, can_delete=True
)
```


### 3. Django Views (تحتاج تعديل متوسط)

#### التعديلات المطلوبة في `UniversityCreateView`:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    
    if self.request.POST:
        context['faculty_formset'] = UniversityFacultyFormSet(
            self.request.POST, 
            instance=self.object
        )
        # معالجة nested programs لكل كلية
        context['faculty_formset'] = self._attach_program_formsets(
            context['faculty_formset'], 
            self.request.POST
        )
    else:
        context['faculty_formset'] = UniversityFacultyFormSet(
            instance=self.object
        )
    
    return context

def form_valid(self, form):
    faculty_formset = context['faculty_formset']
    
    # حفظ الكليات
    if faculty_formset.is_valid():
        faculties = faculty_formset.save(commit=False)
        
        # حفظ البرامج لكل كلية
        for faculty_form in faculty_formset:
            if hasattr(faculty_form, 'programs'):
                programs_formset = faculty_form.programs
                if programs_formset.is_valid():
                    programs_formset.instance = faculty_form.instance
                    programs_formset.save()
    
    return redirect('dashboard:university_edit', pk=self.object.pk)
```

### 4. Template Structure (تحتاج إعادة بناء كاملة)

```django
<!-- الهيكل المقترح -->
<div class="faculty-programs-manager">
    <div class="fpm-header">
        <h2>الكليات والبرامج الأكاديمية</h2>
        <button type="button" id="add-faculty-btn" class="fpm-add-btn">
            <svg>...</svg>
            إضافة كلية
        </button>
    </div>
    
    {{ faculty_formset.management_form }}
    
    <div id="faculties-container" class="fpm-faculties-list">
        {% for faculty_form in faculty_formset %}
        <div class="fpm-faculty-item" data-faculty-index="{{ forloop.counter0 }}">
            
            <!-- Faculty Header (دائماً ظاهر) -->
            <div class="fpm-faculty-header">
                <span class="fpm-drag-handle" title="اسحب لإعادة الترتيب">⋮⋮</span>
                <span class="fpm-faculty-number">[{{ forloop.counter }}]</span>
                
                <!-- حقل اسم الكلية -->
                {{ faculty_form.name }}
                
                <!-- أزرار التحكم -->
                <button type="button" 
                        class="fpm-toggle-btn" 
                        data-toggle-programs
                        aria-expanded="false"
                        title="عرض/إخفاء البرامج">
                    <svg class="fpm-toggle-icon">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </button>
                
                <button type="button" 
                        class="fpm-delete-btn" 
                        data-delete-faculty
                        title="حذف الكلية">
                    <svg>...</svg>
                </button>
                
                <!-- Hidden fields -->
                {{ faculty_form.sort_order }}
                {{ faculty_form.id }}
                {{ faculty_form.DELETE }}
            </div>
            
            <!-- Programs Table Container (قابل للطي) -->
            <div class="fpm-programs-wrapper" style="display: none;">
                {{ faculty_form.programs.management_form }}
                
                <!-- الجدول الديناميكي -->
                <table class="fpm-programs-table">
                    <thead>
                        <tr>
                            <th>التخصصات</th>
                            <th>المدة الدراسية</th>
                            <th>الرسوم السنوية</th>
                            <th width="50"></th>
                        </tr>
                    </thead>
                    <tbody class="fpm-programs-tbody" data-programs-container>
                        {% for program_form in faculty_form.programs %}
                        <tr class="fpm-program-row" data-program-index="{{ forloop.counter0 }}">
                            <td>{{ program_form.name }}</td>
                            <td>{{ program_form.duration }}</td>
                            <td>{{ program_form.tuition_fees }}</td>
                            <td class="fpm-program-actions">
                                <button type="button" 
                                        class="fpm-delete-program-btn" 
                                        data-delete-program
                                        title="حذف البرنامج">
                                    <svg>...</svg>
                                </button>
                                {{ program_form.sort_order }}
                                {{ program_form.id }}
                                {{ program_form.DELETE }}
                            </td>
                        </tr>
                        {% empty %}
                        <tr class="fpm-empty-row">
                            <td colspan="5" class="fpm-empty-message">
                                لا توجد برامج مضافة
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                
                <!-- زر إضافة برنامج -->
                <div class="fpm-add-program-wrapper">
                    <button type="button" 
                            class="fpm-add-program-btn" 
                            data-add-program
                            data-faculty-index="{{ forloop.counter0 }}">
                        <svg>...</svg>
                        إضافة برنامج
                    </button>
                </div>
            </div>
            
        </div>
        {% endfor %}
    </div>
    
    <!-- Empty State -->
    <div class="fpm-empty-state" id="faculties-empty-state" style="display: none;">
        <div class="fpm-empty-icon">📚</div>
        <p class="fpm-empty-text">لا توجد كليات مضافة</p>
        <p class="fpm-empty-hint">اضغط "إضافة كلية" لإضافة كلية جديدة</p>
    </div>
</div>

<!-- Template للكلية الجديدة (مخفي) -->
<template id="faculty-template">
    <div class="fpm-faculty-item" data-faculty-index="__INDEX__">
        <div class="fpm-faculty-header">
            <span class="fpm-drag-handle">⋮⋮</span>
            <span class="fpm-faculty-number">[__NUMBER__]</span>
            <input type="text" 
                   name="faculties-__INDEX__-name" 
                   class="fpm-faculty-name-input"
                   placeholder="اسم الكلية"
                   dir="rtl"
                   required>
            <button type="button" class="fpm-toggle-btn" data-toggle-programs>
                <svg class="fpm-toggle-icon">...</svg>
            </button>
            <button type="button" class="fpm-delete-btn" data-delete-faculty>
                <svg>...</svg>
            </button>
            <input type="hidden" name="faculties-__INDEX__-sort_order" value="__INDEX__">
            <input type="hidden" name="faculties-__INDEX__-id" value="">
            <input type="hidden" name="faculties-__INDEX__-DELETE" value="">
        </div>
        <div class="fpm-programs-wrapper" style="display: none;">
            <input type="hidden" name="faculties-__INDEX__-programs-TOTAL_FORMS" value="0">
            <input type="hidden" name="faculties-__INDEX__-programs-INITIAL_FORMS" value="0">
            <input type="hidden" name="faculties-__INDEX__-programs-MIN_NUM_FORMS" value="0">
            <input type="hidden" name="faculties-__INDEX__-programs-MAX_NUM_FORMS" value="50">
            <table class="fpm-programs-table">
                <thead>
                    <tr>
                        <th>التخصصات</th>
                        <th>المدة الدراسية</th>
                        <th>الرسوم السنوية</th>
                        <th width="50"></th>
                    </tr>
                </thead>
                <tbody class="fpm-programs-tbody" data-programs-container>
                    <tr class="fpm-empty-row">
                        <td colspan="4" class="fpm-empty-message">لا توجد برامج مضافة</td>
                    </tr>
                </tbody>
            </table>
            <div class="fpm-add-program-wrapper">
                <button type="button" class="fpm-add-program-btn" data-add-program>
                    <svg>...</svg>
                    إضافة برنامج
                </button>
            </div>
        </div>
    </div>
</template>

<!-- Template للبرنامج الجديد (مخفي) -->
<template id="program-template">
    <tr class="fpm-program-row" data-program-index="__PROG_INDEX__">
        <td>
            <input type="text" 
                   name="faculties-__FAC_INDEX__-programs-__PROG_INDEX__-name"
                   class="fpm-program-input"
                   placeholder="اسم البرنامج"
                   dir="rtl"
                   required>
        </td>
        <td>
            <input type="text" 
                   name="faculties-__FAC_INDEX__-programs-__PROG_INDEX__-duration"
                   class="fpm-program-input fpm-program-input--short"
                   placeholder="4 سنوات"
                   dir="rtl"
                   required>
        </td>
        <td>
            <input type="text" 
                   name="faculties-__FAC_INDEX__-programs-__PROG_INDEX__-tuition_fees"
                   class="fpm-program-input fpm-program-input--short"
                   placeholder="25,000 دولار"
                   dir="rtl"
                   required>
        </td>
        <td class="fpm-program-actions">
            <button type="button" class="fpm-delete-program-btn" data-delete-program>
                <svg>...</svg>
            </button>
            <input type="hidden" name="faculties-__FAC_INDEX__-programs-__PROG_INDEX__-sort_order" value="__PROG_INDEX__">
            <input type="hidden" name="faculties-__FAC_INDEX__-programs-__PROG_INDEX__-id" value="">
            <input type="hidden" name="faculties-__FAC_INDEX__-programs-__PROG_INDEX__-DELETE" value="">
        </td>
    </tr>
</template>
```


### 5. JavaScript Architecture (جديد بالكامل)

#### الملفات المطلوبة:

**`faculty-programs-manager.js`** — المدير الرئيسي
```javascript
class FacultyProgramsManager {
    constructor() {
        this.facultiesContainer = document.getElementById('faculties-container');
        this.totalFacultiesInput = document.getElementById('id_faculties-TOTAL_FORMS');
        this.facultyIndex = 0;
        this.init();
    }
    
    // إدارة الكليات
    addFaculty() { }
    deleteFaculty(facultyElement) { }
    reorderFaculties() { }
    
    // إدارة البرامج
    addProgram(facultyElement) { }
    deleteProgram(programElement) { }
    reorderPrograms(facultyElement) { }
    
    // Drag & Drop
    initDragAndDrop() { }
    
    // Collapse/Expand
    togglePrograms(facultyElement) { }
    
    // Validation
    validateFaculty(facultyElement) { }
    validateProgram(programElement) { }
}
```

#### المكتبات المساعدة المقترحة:
- **SortableJS** — للـ drag & drop (خفيفة وقوية)
- **Alpine.js** — للـ collapse/expand (موجودة بالفعل في المشروع)

---

## 🎨 تصميم واجهة المستخدم

### 1. الألوان والأنماط (من Design System الموجود)
```css
/* استخدام CSS Variables الموجودة */
--primary: #0B2D4D;
--secondary: #C8A041;
--success: #0C7A43;
--danger: #D64545;
--border: #E4EAF0;
--surface: #FFFFFF;
--surface-2: #F7FAFC;
```

### 2. هيكل الـ CSS

**`faculty-programs-manager.css`**
```css
/* ═══ Container ═══ */
.faculty-programs-manager { }

/* ═══ Faculty Item ═══ */
.fpm-faculty-item {
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    margin-bottom: 12px;
    background: var(--surface);
}

.fpm-faculty-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: var(--surface-2);
    border-bottom: 1px solid var(--border);
}

/* ═══ Programs Container ═══ */
.fpm-programs-container {
    padding: 16px;
    display: none; /* يظهر عند التوسيع */
}

.fpm-programs-container.expanded {
    display: block;
}

/* ═══ Program Item ═══ */
.fpm-program-item {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr auto;
    gap: 12px;
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    margin-bottom: 8px;
    background: var(--surface);
}

/* ═══ Drag Handle ═══ */
.fpm-drag-handle {
    cursor: grab;
    color: var(--text-muted);
}

.fpm-drag-handle:active {
    cursor: grabbing;
}

/* ═══ States ═══ */
.fpm-faculty-item--dragging {
    opacity: 0.5;
    border-style: dashed;
}

.fpm-program-item--deleted {
    opacity: 0.3;
    pointer-events: none;
}
```


### 3. تفاصيل التصميم

#### Faculty Item (الكلية)
```
┌────────────────────────────────────────────────────────┐
│ ⋮⋮ [1] [كلية الهندسة________________]  [▼] [×]       │ ← Header
├────────────────────────────────────────────────────────┤
│  Programs Container (قابل للطي)                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ [هندسة البرمجيات] [4 سنوات] [25,000 RM]  [×]   │ │
│  │ [هندسة الحاسوب]   [4 سنوات] [24,000 RM]  [×]   │ │
│  │ [+ إضافة برنامج]                                 │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

#### Program Item (البرنامج)
```
┌─────────────────────────────────────────────────────────┐
│ [اسم البرنامج_______] [المدة____] [الرسوم_____]  [×]  │
│  ↑ Name (2fr)         ↑ Duration  ↑ Fees       ↑ Del   │
│                         (1fr)      (1fr)        (auto)  │
└─────────────────────────────────────────────────────────┘
```

#### Empty State
```
┌─────────────────────────────────────────────────────────┐
│                          📚                             │
│                                                         │
│              لا توجد كليات مضافة                       │
│         اضغط "إضافة كلية" لإضافة كلية جديدة            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 خطة التنفيذ

### المرحلة 1: التحضير والتخطيط (يوم واحد)
- [x] تحليل الكود الحالي
- [x] فهم المتطلبات من العرض الفني
- [x] تحديد الفجوات
- [x] كتابة خطة تنفيذية شاملة
- [ ] مراجعة الخطة مع الفريق

### المرحلة 2: تطوير Backend (2-3 أيام)

#### 2.1 Django Forms
- [ ] إنشاء `ProgramFormSet` للبرامج
- [ ] تعديل `FacultyFormSetForm` لدعم nested programs
- [ ] إنشاء `FacultyFormWithPrograms` class
- [ ] تحديث `UniversityFacultyFormSet`
- [ ] كتابة unit tests للـ forms

#### 2.2 Django Views
- [ ] تعديل `UniversityCreateView.get_context_data()`
- [ ] تعديل `UniversityCreateView.form_valid()`
- [ ] إضافة معالجة nested formsets
- [ ] معالجة الأخطاء والـ validation
- [ ] تحديث `UniversityEditView` بنفس المنطق
- [ ] كتابة integration tests


### المرحلة 3: تطوير Frontend (3-4 أيام)

#### 3.1 HTML Template
- [ ] إنشاء هيكل HTML الجديد
- [ ] إضافة management forms للكليات والبرامج
- [ ] إنشاء template للكلية الفارغة (للاستنساخ بالـ JS)
- [ ] إنشاء template للبرنامج الفارغ (للاستنساخ بالـ JS)
- [ ] إضافة empty state
- [ ] إضافة الأزرار والأيقونات

#### 3.2 CSS Styling
- [ ] إنشاء `faculty-programs-manager.css`
- [ ] تصميم Faculty Item
- [ ] تصميم Program Item
- [ ] تصميم Drag handles
- [ ] تصميم Buttons وأيقونات الحذف
- [ ] تصميم Empty state
- [ ] تصميم حالات Hover/Active/Dragging
- [ ] تصميم Responsive للموبايل
- [ ] تصميم Animations والـ transitions

#### 3.3 JavaScript Logic
- [ ] إنشاء `FacultyProgramsManager` class
- [ ] تطبيق إضافة كلية جديدة
- [ ] تطبيق حذف كلية
- [ ] تطبيق إضافة برنامج داخل كلية
- [ ] تطبيق حذف برنامج
- [ ] تطبيق Drag & Drop للكليات
- [ ] تطبيق Drag & Drop للبرامج
- [ ] تطبيق Collapse/Expand للبرامج
- [ ] تطبيق تحديث الترتيب التلقائي
- [ ] تطبيق Validation على الـ client-side
- [ ] تطبيق إدارة management forms
- [ ] معالجة الأخطاء والـ edge cases

### المرحلة 4: التكامل والاختبار (2 يوم)
- [ ] دمج Backend مع Frontend
- [ ] اختبار إنشاء جامعة جديدة مع كليات وبرامج
- [ ] اختبار تعديل جامعة موجودة
- [ ] اختبار حذف كليات وبرامج
- [ ] اختبار إعادة الترتيب
- [ ] اختبار Validation
- [ ] اختبار على متصفحات مختلفة
- [ ] اختبار Responsive على أجهزة مختلفة
- [ ] إصلاح الـ bugs

### المرحلة 5: التحسين والتوثيق (1 يوم)
- [ ] تحسين الأداء
- [ ] تحسين Accessibility
- [ ] إضافة Loading states
- [ ] إضافة Success/Error messages
- [ ] كتابة التوثيق الفني
- [ ] كتابة دليل المستخدم
- [ ] Code review نهائي

### المرحلة 6: النشر والمتابعة (نصف يوم)
- [ ] Deploy على staging
- [ ] اختبار نهائي على staging
- [ ] Deploy على production
- [ ] مراقبة الأداء
- [ ] جمع feedback من المستخدمين


---

## ⚙️ الاعتبارات الفنية

### 1. Nested Formsets في Django

#### التحدي:
Django لا يدعم nested formsets بشكل مباشر (formset داخل formset)

#### الحلول المقترحة:

**الحل 1: Manual Nesting (موصى به)**
```python
# في الـ View
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    
    faculty_formset = UniversityFacultyFormSet(instance=self.object)
    
    # ربط program formsets يدوياً
    for faculty_form in faculty_formset:
        if faculty_form.instance.pk:
            faculty_form.program_formset = ProgramFormSet(
                instance=faculty_form.instance,
                prefix=f'programs-{faculty_form.prefix}'
            )
        else:
            faculty_form.program_formset = ProgramFormSet(
                prefix=f'programs-{faculty_form.prefix}'
            )
    
    context['faculty_formset'] = faculty_formset
    return context
```

**الحل 2: استخدام مكتبة `django-nested-inline`**
- مكتبة جاهزة لدعم nested formsets
- قد تكون أثقل من الحل اليدوي
- تحتاج تقييم قبل الاستخدام

**الحل 3: AJAX-based approach**
- تحميل البرامج عبر AJAX عند فتح الكلية
- أخف على الصفحة الأولية
- يحتاج endpoints إضافية

**التوصية**: الحل 1 (Manual Nesting) — أكثر تحكم وأقل dependencies

### 2. إدارة Management Forms

#### التحدي:
كل formset يحتاج management form خاص به:
- `TOTAL_FORMS` — عدد الفورمات الكلي
- `INITIAL_FORMS` — عدد الفورمات الموجودة مسبقاً
- `MIN_NUM_FORMS` — الحد الأدنى
- `MAX_NUM_FORMS` — الحد الأقصى

#### الحل:
```javascript
class FormsetManager {
    updateManagementForm(formsetPrefix) {
        const totalInput = document.getElementById(`id_${formsetPrefix}-TOTAL_FORMS`);
        const forms = document.querySelectorAll(`[data-formset="${formsetPrefix}"]`);
        totalInput.value = forms.length;
    }
    
    reindexForms(formsetPrefix) {
        const forms = document.querySelectorAll(`[data-formset="${formsetPrefix}"]`);
        forms.forEach((form, index) => {
            // تحديث أسماء الحقول
            form.querySelectorAll('input, select, textarea').forEach(field => {
                const name = field.getAttribute('name');
                if (name) {
                    field.setAttribute('name', 
                        name.replace(/\d+/, index)
                    );
                }
            });
        });
    }
}
```


### 3. Drag & Drop Implementation

#### المكتبة المقترحة: SortableJS
```javascript
// تهيئة Sortable للكليات
new Sortable(document.getElementById('faculties-container'), {
    handle: '.fpm-drag-handle',
    animation: 150,
    ghostClass: 'fpm-faculty-item--dragging',
    onEnd: (evt) => {
        this.updateFacultySortOrders();
    }
});

// تهيئة Sortable للبرامج داخل كل كلية
document.querySelectorAll('.fpm-programs-list').forEach(programsList => {
    new Sortable(programsList, {
        handle: '.fpm-program-drag-handle',
        animation: 150,
        ghostClass: 'fpm-program-item--dragging',
        onEnd: (evt) => {
            this.updateProgramSortOrders(programsList);
        }
    });
});
```

#### البديل: Drag & Drop API الأصلي
- أخف وزناً
- يحتاج كود أكثر
- دعم أقل للمتصفحات القديمة

### 4. Performance Optimization

#### التحديات المحتملة:
- عدد كبير من الكليات (10+)
- عدد كبير من البرامج في كل كلية (20+)
- إعادة rendering متكررة

#### الحلول:
1. **Lazy Loading للبرامج**
   - تحميل البرامج فقط عند فتح الكلية
   - استخدام AJAX أو تخزين البيانات في `data-*` attributes

2. **Virtual Scrolling**
   - إذا كان العدد كبير جداً (50+ كلية)
   - استخدام مكتبة مثل `react-window` أو `vue-virtual-scroller`

3. **Debouncing للـ Validation**
   - عدم التحقق من الصحة مع كل keystroke
   - استخدام debounce بـ 300-500ms

4. **Event Delegation**
   - استخدام event delegation بدل ربط event لكل عنصر
   ```javascript
   document.getElementById('faculties-container').addEventListener('click', (e) => {
       if (e.target.matches('.fpm-delete-faculty')) {
           this.deleteFaculty(e.target.closest('.fpm-faculty-item'));
       }
   });
   ```

### 5. Validation Strategy

#### Client-Side Validation
```javascript
validateFaculty(facultyElement) {
    const nameInput = facultyElement.querySelector('[name$="-name"]');
    const errors = [];
    
    // اسم الكلية مطلوب
    if (!nameInput.value.trim()) {
        errors.push('اسم الكلية مطلوب');
    }
    
    // التحقق من التكرار
    const allNames = this.getAllFacultyNames();
    if (allNames.filter(n => n === nameInput.value).length > 1) {
        errors.push('اسم الكلية مكرر');
    }
    
    // عرض الأخطاء
    this.showErrors(facultyElement, errors);
    return errors.length === 0;
}

validateProgram(programElement) {
    const nameInput = programElement.querySelector('[name$="-name"]');
    const durationInput = programElement.querySelector('[name$="-duration"]');
    const feesInput = programElement.querySelector('[name$="-tuition_fees"]');
    const errors = [];
    
    if (!nameInput.value.trim()) {
        errors.push('اسم البرنامج مطلوب');
    }
    
    if (!durationInput.value.trim()) {
        errors.push('مدة الدراسة مطلوبة');
    }
    
    if (!feesInput.value.trim()) {
        errors.push('الرسوم الدراسية مطلوبة');
    }
    
    this.showErrors(programElement, errors);
    return errors.length === 0;
}
```

#### Server-Side Validation
```python
# في الـ Form
def clean(self):
    cleaned_data = super().clean()
    
    # التحقق من عدم وجود كلية بدون برامج
    if not self.programs_formset.is_valid():
        raise ValidationError('يجب إضافة برنامج واحد على الأقل لكل كلية')
    
    return cleaned_data
```


### 6. Accessibility (A11y)

#### المتطلبات:
- [ ] جميع الأزرار لها `aria-label` واضح
- [ ] Keyboard navigation كامل (Tab, Enter, Escape)
- [ ] Screen reader support
- [ ] Focus management صحيح
- [ ] Color contrast مناسب (WCAG AA)

#### التطبيق:
```html
<!-- مثال: زر إضافة كلية -->
<button 
    type="button" 
    id="add-faculty-btn"
    aria-label="إضافة كلية جديدة"
    class="fpm-add-faculty-btn">
    <svg aria-hidden="true">...</svg>
    <span>إضافة كلية</span>
</button>

<!-- مثال: Accordion -->
<button 
    type="button"
    class="fpm-toggle-programs"
    aria-expanded="false"
    aria-controls="programs-container-0"
    aria-label="عرض/إخفاء البرامج">
    ▼
</button>

<div 
    id="programs-container-0"
    class="fpm-programs-container"
    role="region"
    aria-labelledby="faculty-name-0">
    <!-- Programs -->
</div>
```

### 7. Error Handling

#### سيناريوهات الأخطاء:
1. **فشل حفظ الكلية** — عرض رسالة خطأ واضحة
2. **فشل حفظ البرنامج** — تحديد البرنامج المعطل
3. **تكرار الأسماء** — تحذير فوري
4. **حقول فارغة** — validation قبل الإرسال
5. **فشل الاتصال** — retry mechanism

#### التطبيق:
```javascript
async saveFaculty(facultyData) {
    try {
        const response = await fetch('/api/faculties/', {
            method: 'POST',
            body: JSON.stringify(facultyData)
        });
        
        if (!response.ok) {
            throw new Error('فشل حفظ الكلية');
        }
        
        this.showSuccess('تم حفظ الكلية بنجاح');
    } catch (error) {
        this.showError('حدث خطأ أثناء حفظ الكلية: ' + error.message);
        console.error(error);
    }
}
```

### 8. Browser Compatibility

#### المتصفحات المستهدفة:
- Chrome/Edge (آخر نسختين)
- Firefox (آخر نسختين)
- Safari (آخر نسختين)
- Mobile browsers (iOS Safari, Chrome Mobile)

#### الميزات التي تحتاج Polyfills:
- `Array.prototype.findIndex` — IE11
- `Promise` — IE11
- `fetch` — IE11
- CSS Grid — IE11 (fallback)

#### الحل:
```html
<!-- في الـ template -->
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6,fetch"></script>
<script src="{% static 'js/faculty-programs-manager.js' %}"></script>
```

---

## 📊 مقاييس النجاح

### 1. الأداء
- [ ] وقت تحميل الصفحة < 2 ثانية
- [ ] وقت استجابة الـ drag & drop < 100ms
- [ ] وقت إضافة كلية/برنامج < 200ms

### 2. تجربة المستخدم
- [ ] إمكانية إضافة 10 كليات بـ 5 برامج لكل منها في < 5 دقائق
- [ ] معدل أخطاء الإدخال < 5%
- [ ] رضا المستخدمين > 90%

### 3. الجودة التقنية
- [ ] Test coverage > 80%
- [ ] Zero critical bugs
- [ ] Lighthouse score > 90
- [ ] Accessibility score > 95

---

## 🚀 التوصيات النهائية

### الأولويات:
1. **عالية**: Nested formsets + Basic UI
2. **متوسطة**: Drag & drop + Validation
3. **منخفضة**: Advanced features (live preview, AJAX)

### النهج المقترح:
1. **MVP أولاً** — إنشاء نسخة أساسية تعمل
2. **Iterate** — إضافة المميزات تدريجياً
3. **Test continuously** — اختبار مع كل إضافة
4. **Gather feedback** — من المستخدمين الفعليين

### المخاطر المحتملة:
- **Complexity** — Nested formsets معقدة، تحتاج وقت
- **Performance** — عدد كبير من العناصر قد يبطئ الصفحة
- **Browser compatibility** — بعض الميزات قد لا تعمل على متصفحات قديمة

### خطة التخفيف:
- بدء بـ MVP بسيط
- اختبار مبكر ومتكرر
- استخدام Progressive Enhancement
- توفير fallbacks للمتصفحات القديمة

---

## 📚 المراجع والموارد

### Django Documentation
- [Formsets](https://docs.djangoproject.com/en/stable/topics/forms/formsets/)
- [Inline Formsets](https://docs.djangoproject.com/en/stable/topics/forms/modelforms/#inline-formsets)

### JavaScript Libraries
- [SortableJS](https://sortablejs.github.io/Sortable/)
- [Alpine.js](https://alpinejs.dev/)

### Design Patterns
- [Nested Formsets Pattern](https://stackoverflow.com/questions/501719/dynamically-adding-a-form-to-a-django-formset-with-ajax)
- [Django Nested Inline](https://github.com/s-block/django-nested-inline)

---

**تاريخ الإنشاء**: 2026-05-24  
**الإصدار**: 1.0  
**الحالة**: جاهز للمراجعة والتنفيذ


---

## 🔄 تحديث: الشكل النهائي الفعلي (بناءً على الصورة)

### الشكل الفعلي في الفرونت إند:

```
┌─────────────────────────────────────────────────────────────────────┐
│ ▼ كلية الطب ضمن جامعة لينكولن ماليزيا                              │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ التخصصات          │ المدة الدراسية │ الرسوم السنوية            │ │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ Doctor of Medicine │ 5 سنوات        │ 14,000 دولار            │ │
│ │ دكتوراه في الطب    │                │                          │ │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ دبلوم الدراسات... │ 1 سنة          │ 7,267 دولار             │ │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ Master of Medical  │ 1 سنة          │ 8,000 دولار             │ │
│ │ ماجستير في العلوم │                │                          │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ▼ كلية طب الأسنان ضمن جامعة لينكولن ماليزيا                        │
├─────────────────────────────────────────────────────────────────────┤
│ (مطوي - لم يتم فتحه)                                                │
└─────────────────────────────────────────────────────────────────────┘
```

### الملاحظات الهامة من الصورة:

#### 1. **جدول HTML حقيقي** (ليس cards)
- Header: `التخصصات | المدة الدراسية | الرسوم السنوية`
- Rows: كل برنامج في صف منفصل
- Styling: جدول احترافي بـ borders وألوان متناسقة

#### 2. **Accordion للكليات**
- كل كلية = accordion item
- العنوان: "كلية X ضمن جامعة Y"
- المحتوى: جدول البرامج

#### 3. **محتوى ثنائي اللغة**
- اسم البرنامج بالإنجليزي في السطر الأول
- اسم البرنامج بالعربي في السطر الثاني (نفس الخلية)

#### 4. **تنسيق البيانات**
- المدة: "X سنوات" أو "X سنة"
- الرسوم: "X,XXX دولار" (بفاصلة للآلاف)

---

## 🔧 تعديلات على البنية التقنية

### 1. تحديث Program Model

**الحقول الحالية كافية** — لا حاجة لتعديل كبير:

```python
class Program(models.Model):
    """Program within a faculty."""
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='programs')
    
    # الاسم (حالياً عربي فقط، لاحقاً سيُضاف name_en)
    name = models.CharField(max_length=200, verbose_name='اسم البرنامج')
    
    # المدة والرسوم (موجودة بالفعل)
    duration = models.CharField(max_length=100, verbose_name='مدة الدراسة', help_text='مثال: 4 سنوات')
    tuition_fees = models.CharField(max_length=100, verbose_name='الرسوم الدراسية', help_text='مثال: 20,000 رنجت')
    
    sort_order = models.PositiveIntegerField(default=0, verbose_name='ترتيب العرض')
    
    class Meta:
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f'{self.name} - {self.faculty.name}'

# ملاحظة: لاحقاً عند تطوير النسخة الإنجليزية:
# - سيُضاف حقل name_en
# - قد يُحوّل tuition_fees إلى DecimalField
# - قد يُضاف حقل currency
```

### 2. تحديث واجهة لوحة التحكم

#### الشكل المطلوب في Dashboard:

```
┌─────────────────────────────────────────────────────────────────────┐
│  الكليات والبرامج الأكاديمية                    [+ إضافة كلية]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ⋮⋮ [1] [كلية الهندسة_______________]           [▼] [×]            │
│      ┌────────────────────────────────────────────────────────────┐│
│      │ التخصصات          │ المدة الدراسية │ الرسوم السنوية │ [×] ││
│      ├────────────────────────────────────────────────────────────┤│
│      │ [هندسة البرمجيات] │ [4 سنوات]      │ [25000]        │ [×] ││
│      │ [هندسة الحاسوب]   │ [4 سنوات]      │ [24000]        │ [×] ││
│      │                                                            ││
│      │ [+ إضافة برنامج]                                          ││
│      └────────────────────────────────────────────────────────────┘│
│                                                                     │
│  ⋮⋮ [2] [كلية الطب__________________]           [▼] [×]            │
│      (مطوي - لم يتم فتحه)                                          │
│                                                                     │
│  ⋮⋮ [3] [كلية إدارة الأعمال_________]           [▼] [×]            │
│      ┌────────────────────────────────────────────────────────────┐│
│      │ التخصصات          │ المدة الدراسية │ الرسوم السنوية │ [×] ││
│      ├────────────────────────────────────────────────────────────┤│
│      │ (لا توجد برامج مضافة)                                     ││
│      │                                                            ││
│      │ [+ إضافة برنامج]                                          ││
│      └────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

الرموز:
⋮⋮ = مقبض السحب (Drag handle)
[▼] = توسيع/طي الجدول
[×] = حذف
[___] = حقل إدخال

ملاحظة: حقل الاسم الإنجليزي سيُضاف لاحقاً عند تطوير النسخة الإنجليزية من الموقع
```

#### سلوك الواجهة:

**عند الضغط على "إضافة كلية":**
1. يظهر سطر جديد مطوي (collapsed)
2. يحتوي على حقل اسم الكلية فارغ
3. زر [▼] لفتح الجدول
4. زر [×] للحذف

**عند فتح الكلية (الضغط على ▼):**
1. يتوسع السطر
2. يظهر جدول ديناميكي بالعناوين:
   - `التخصصات (عربي)`
   - `التخصصات (EN)`
   - `المدة الدراسية`
   - `الرسوم السنوية`
   - عمود الحذف
3. زر "إضافة برنامج" في الأسفل

**عند الضغط على "إضافة برنامج":**
1. يضاف صف جديد في الجدول
2. جميع الحقول فارغة وجاهزة للإدخال
3. Focus تلقائي على حقل "التخصصات (عربي)"

### 3. تحديث ProgramForm

```python
class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'duration', 'tuition_fees', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'fpm-program-input',
                'placeholder': 'اسم البرنامج',
                'dir': 'rtl',
                'required': True
            }),
            'duration': forms.TextInput(attrs={
                'class': 'fpm-program-input fpm-program-input--short',
                'placeholder': '4 سنوات',
                'dir': 'rtl',
                'required': True
            }),
            'tuition_fees': forms.TextInput(attrs={
                'class': 'fpm-program-input fpm-program-input--short',
                'placeholder': '25,000 دولار',
                'dir': 'rtl',
                'required': True
            }),
            'sort_order': forms.HiddenInput()
        }
```

### 4. تحديث Template للفرونت إند

```django
<!-- في templates/universities/detail.html -->
{% if faculties %}
<section class="detail-section">
    <div class="detail-section-header">
        <h2 class="detail-section-title">الكليات والبرامج الأكاديمية</h2>
    </div>
    
    <div class="detail-faculties-accordion">
        {% for faculty in faculties %}
        <div class="detail-faculty-item" x-data="{ open: false }">
            <!-- Faculty Header -->
            <button 
                class="detail-faculty-header"
                @click="open = !open"
                :aria-expanded="open">
                <span class="detail-faculty-name">
                    {{ faculty.name }} ضمن {{ university.name }}
                </span>
                <svg class="detail-faculty-icon" :class="{ 'rotated': open }">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </button>

            <!-- Programs Table -->
            <div class="detail-faculty-content" x-show="open" x-collapse>
                {% if faculty.programs.all %}
                <table class="detail-programs-table">
                    <thead>
                        <tr>
                            <th>التخصصات</th>
                            <th>المدة الدراسية</th>
                            <th>الرسوم السنوية</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for program in faculty.programs.all %}
                        <tr>
                            <td class="detail-program-name">{{ program.name }}</td>
                            <td class="detail-program-duration">{{ program.duration }}</td>
                            <td class="detail-program-fees">{{ program.tuition_fees }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <p class="detail-empty-state">لا توجد برامج متاحة حالياً</p>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
</section>
{% endif %}
```

### 5. تحديث CSS للجدول

```css
/* ═══ Programs Table ═══ */
.detail-programs-table {
    width: 100%;
    border-collapse: collapse;
    background: var(--surface);
    border: 1px solid var(--border);
}

.detail-programs-table thead {
    background: var(--primary);
    color: white;
}

.detail-programs-table th {
    padding: 14px 20px;
    text-align: right;
    font-weight: 600;
    font-size: 15px;
    border-left: 1px solid rgba(255, 255, 255, 0.1);
}

.detail-programs-table th:last-child {
    border-left: none;
}

.detail-programs-table tbody tr {
    border-bottom: 1px solid var(--border);
    transition: background-color 0.15s ease;
}

.detail-programs-table tbody tr:hover {
    background-color: var(--surface-2);
}

.detail-programs-table td {
    padding: 16px 20px;
    text-align: right;
    border-left: 1px solid var(--border);
}

.detail-programs-table td:last-child {
    border-left: none;
}

/* Program Name Cell */
.detail-program-name {
    color: var(--text-primary);
    font-weight: 500;
}

/* Duration & Fees */
.detail-program-duration,
.detail-program-fees {
    color: var(--text-secondary);
    white-space: nowrap;
}

/* Responsive */
@media (max-width: 768px) {
    .detail-programs-table {
        display: block;
        overflow-x: auto;
    }
    
    .detail-programs-table th,
    .detail-programs-table td {
        padding: 12px 14px;
        font-size: 14px;
    }
}
```

---

## 📝 تحديث خطة التنفيذ

### المرحلة 0: ~~Migration~~ (غير مطلوبة حالياً)
- النماذج الحالية كافية
- لا حاجة لـ migration في هذه المرحلة
- عند تطوير النسخة الإنجليزية لاحقاً:
  - [ ] إضافة حقل `name_en` للبرامج
  - [ ] إضافة حقل `name_en` للكليات
  - [ ] Data migration للبيانات الموجودة

### تعديلات على المراحل الأخرى:
- **المرحلة 2.1**: تحديث ProgramForm بالحقول الجديدة
- **المرحلة 3.1**: تحديث Template بجدول HTML
- **المرحلة 3.2**: تحديث CSS لتصميم الجدول
- **المرحلة 3.3**: تحديث JS لدعم الحقول الإضافية

---

## ✅ الخلاصة المحدثة

الفرق الرئيسي:
- ❌ **ليس**: Cards للبرامج
- ✅ **بل**: جدول HTML احترافي
- ✅ **مع**: أسماء ثنائية اللغة (عربي + إنجليزي)
- ✅ **و**: تنسيق احترافي للأرقام والعملات


---

## 🎬 سيناريوهات الاستخدام التفصيلية

### السيناريو 1: إضافة كلية جديدة فارغة

**الخطوات:**
1. المستخدم يضغط على زر "إضافة كلية"
2. يظهر سطر جديد **مطوي** (collapsed)
3. السطر يحتوي على:
   - مقبض السحب ⋮⋮
   - رقم الكلية [4]
   - حقل إدخال فارغ لاسم الكلية (focus تلقائي)
   - زر [▼] للتوسيع
   - زر [×] للحذف
4. الجدول **مخفي** حتى يضغط المستخدم على [▼]

**الكود:**
```javascript
addFaculty() {
    const facultyIndex = parseInt(this.totalFacultiesInput.value);
    
    // استنساخ template الكلية
    const template = document.getElementById('faculty-template');
    const clone = template.content.cloneNode(true);
    
    // تحديث الـ indices
    const facultyItem = clone.querySelector('.fpm-faculty-item');
    facultyItem.setAttribute('data-faculty-index', facultyIndex);
    
    // تحديث الأرقام والأسماء
    clone.querySelector('.fpm-faculty-number').textContent = `[${facultyIndex + 1}]`;
    clone.querySelectorAll('[name*="__INDEX__"]').forEach(input => {
        input.name = input.name.replace('__INDEX__', facultyIndex);
    });
    
    // إضافة للـ DOM
    this.facultiesContainer.appendChild(clone);
    
    // تحديث management form
    this.totalFacultiesInput.value = facultyIndex + 1;
    
    // Focus على حقل الاسم
    const nameInput = facultyItem.querySelector('.fpm-faculty-name-input');
    setTimeout(() => nameInput.focus(), 100);
    
    // ربط الأحداث
    this.attachFacultyEvents(facultyItem);
    
    // تحديث الحالة
    this.updateEmptyState();
}
```

---

### السيناريو 2: فتح كلية وإضافة برامج

**الخطوات:**
1. المستخدم يكتب اسم الكلية: "كلية الهندسة"
2. يضغط على زر [▼] لفتح الجدول
3. يظهر جدول فارغ مع العناوين:
   ```
   ┌────────────────────────────────────────────────────────┐
   │ التخصصات       │ المدة الدراسية │ الرسوم السنوية │   │
   ├────────────────────────────────────────────────────────┤
   │ (لا توجد برامج مضافة)                                 │
   │                                                        │
   │ [+ إضافة برنامج]                                      │
   └────────────────────────────────────────────────────────┘
   ```
4. يضغط على "إضافة برنامج"
5. يظهر صف جديد في الجدول مع حقول فارغة
6. Focus تلقائي على حقل "التخصصات (عربي)"
7. يملأ البيانات:
   - عربي: "هندسة البرمجيات"
   - EN: "Software Engineering"
   - المدة: "4 سنوات"
   - الرسوم: "25000"
8. يضغط "إضافة برنامج" مرة أخرى لإضافة برنامج ثاني

**الكود:**
```javascript
togglePrograms(facultyItem) {
    const wrapper = facultyItem.querySelector('.fpm-programs-wrapper');
    const toggleBtn = facultyItem.querySelector('[data-toggle-programs]');
    const icon = toggleBtn.querySelector('.fpm-toggle-icon');
    
    const isExpanded = wrapper.style.display !== 'none';
    
    if (isExpanded) {
        // طي الجدول
        wrapper.style.display = 'none';
        toggleBtn.setAttribute('aria-expanded', 'false');
        icon.classList.remove('rotated');
    } else {
        // فتح الجدول
        wrapper.style.display = 'block';
        toggleBtn.setAttribute('aria-expanded', 'true');
        icon.classList.add('rotated');
    }
}

addProgram(facultyItem) {
    const facultyIndex = facultyItem.getAttribute('data-faculty-index');
    const programsContainer = facultyItem.querySelector('[data-programs-container]');
    const totalFormsInput = facultyItem.querySelector(`[name="faculties-${facultyIndex}-programs-TOTAL_FORMS"]`);
    const programIndex = parseInt(totalFormsInput.value);
    
    // إزالة empty row إذا كان موجود
    const emptyRow = programsContainer.querySelector('.fpm-empty-row');
    if (emptyRow) emptyRow.remove();
    
    // استنساخ template البرنامج
    const template = document.getElementById('program-template');
    const clone = template.content.cloneNode(true);
    
    // تحديث الـ indices
    clone.querySelectorAll('[name*="__FAC_INDEX__"]').forEach(input => {
        input.name = input.name.replace('__FAC_INDEX__', facultyIndex);
    });
    clone.querySelectorAll('[name*="__PROG_INDEX__"]').forEach(input => {
        input.name = input.name.replace('__PROG_INDEX__', programIndex);
    });
    
    // إضافة للجدول
    programsContainer.appendChild(clone);
    
    // تحديث management form
    totalFormsInput.value = programIndex + 1;
    
    // Focus على حقل الاسم
    const programRow = programsContainer.lastElementChild;
    const nameInput = programRow.querySelector('[name$="-name"]');
    setTimeout(() => nameInput.focus(), 100);
    
    // ربط أحداث الحذف
    this.attachProgramEvents(programRow);
}
```

---

### السيناريو 3: حذف برنامج

**الخطوات:**
1. المستخدم يضغط على زر [×] بجانب برنامج
2. إذا كان البرنامج **جديد** (لم يُحفظ بعد):
   - يُحذف الصف فوراً من الجدول
   - يُعاد ترقيم البرامج المتبقية
3. إذا كان البرنامج **موجود** (محفوظ في DB):
   - يُعلّم للحذف (DELETE = true)
   - يُخفى الصف مع opacity
   - يُحذف فعلياً عند الحفظ

**الكود:**
```javascript
deleteProgram(programRow) {
    const deleteInput = programRow.querySelector('[name$="-DELETE"]');
    const idInput = programRow.querySelector('[name$="-id"]');
    
    if (idInput && idInput.value) {
        // برنامج موجود — نعلمه للحذف
        deleteInput.value = 'on';
        programRow.classList.add('fpm-program-row--deleted');
        programRow.style.opacity = '0.3';
        programRow.style.pointerEvents = 'none';
    } else {
        // برنامج جديد — نحذفه من DOM
        const facultyItem = programRow.closest('.fpm-faculty-item');
        const programsContainer = programRow.closest('[data-programs-container]');
        
        programRow.remove();
        
        // إعادة ترقيم البرامج
        this.reindexPrograms(facultyItem);
        
        // إذا لم يتبقى برامج، نعرض empty row
        const remainingPrograms = programsContainer.querySelectorAll('.fpm-program-row:not(.fpm-program-row--deleted)');
        if (remainingPrograms.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.className = 'fpm-empty-row';
            emptyRow.innerHTML = '<td colspan="5" class="fpm-empty-message">لا توجد برامج مضافة</td>';
            programsContainer.appendChild(emptyRow);
        }
    }
}
```

---

### السيناريو 4: حذف كلية كاملة

**الخطوات:**
1. المستخدم يضغط على زر [×] بجانب الكلية
2. تظهر رسالة تأكيد: "هل تريد حذف هذه الكلية وجميع برامجها؟"
3. إذا وافق:
   - إذا كانت الكلية **جديدة**: تُحذف فوراً
   - إذا كانت **موجودة**: تُعلّم للحذف وتُخفى
4. يُعاد ترقيم الكليات المتبقية

**الكود:**
```javascript
deleteFaculty(facultyItem) {
    const facultyName = facultyItem.querySelector('.fpm-faculty-name-input').value || 'هذه الكلية';
    const programsCount = facultyItem.querySelectorAll('.fpm-program-row:not(.fpm-program-row--deleted)').length;
    
    let confirmMessage = `هل تريد حذف "${facultyName}"؟`;
    if (programsCount > 0) {
        confirmMessage += `\n\nسيتم حذف ${programsCount} برنامج مرتبط بها.`;
    }
    
    if (!confirm(confirmMessage)) return;
    
    const deleteInput = facultyItem.querySelector('[name$="-DELETE"]');
    const idInput = facultyItem.querySelector('[name$="-id"]');
    
    if (idInput && idInput.value) {
        // كلية موجودة — نعلمها للحذف
        deleteInput.value = 'on';
        facultyItem.classList.add('fpm-faculty-item--deleted');
        facultyItem.style.display = 'none';
    } else {
        // كلية جديدة — نحذفها من DOM
        facultyItem.remove();
    }
    
    // إعادة ترقيم الكليات
    this.reindexFaculties();
    
    // تحديث الحالة الفارغة
    this.updateEmptyState();
}
```

---

### السيناريو 5: إعادة ترتيب الكليات بالسحب

**الخطوات:**
1. المستخدم يسحب الكلية من مقبض ⋮⋮
2. أثناء السحب:
   - الكلية المسحوبة تصبح شبه شفافة
   - يظهر مؤشر للموقع الجديد
3. عند الإفلات:
   - تنتقل الكلية للموقع الجديد
   - يُعاد ترقيم جميع الكليات تلقائياً
   - يُحدث حقل `sort_order` لكل كلية

**الكود:**
```javascript
initDragAndDrop() {
    new Sortable(this.facultiesContainer, {
        handle: '.fpm-drag-handle',
        animation: 200,
        ghostClass: 'fpm-faculty-item--dragging',
        dragClass: 'fpm-faculty-item--drag',
        onEnd: (evt) => {
            this.reindexFaculties();
            this.updateSortOrders();
        }
    });
}

updateSortOrders() {
    const facultyItems = this.facultiesContainer.querySelectorAll('.fpm-faculty-item:not(.fpm-faculty-item--deleted)');
    
    facultyItems.forEach((item, index) => {
        // تحديث الرقم المعروض
        item.querySelector('.fpm-faculty-number').textContent = `[${index + 1}]`;
        
        // تحديث sort_order
        const sortInput = item.querySelector('[name$="-sort_order"]');
        if (sortInput) sortInput.value = index;
    });
}
```

---

## 🎨 تفاصيل CSS للجدول الديناميكي

```css
/* ═══ Programs Table ═══ */
.fpm-programs-table {
    width: 100%;
    border-collapse: collapse;
    background: var(--surface);
    border: 1px solid var(--border);
    margin-top: 12px;
}

.fpm-programs-table thead {
    background: var(--primary);
    color: white;
}

.fpm-programs-table th {
    padding: 12px 16px;
    text-align: right;
    font-weight: 600;
    font-size: 14px;
    border-left: 1px solid rgba(255, 255, 255, 0.1);
}

.fpm-programs-table th:last-child {
    border-left: none;
    text-align: center;
}

.fpm-programs-table tbody tr {
    border-bottom: 1px solid var(--border);
    transition: background-color 0.15s ease;
}

.fpm-programs-table tbody tr:hover:not(.fpm-empty-row) {
    background-color: var(--surface-2);
}

.fpm-programs-table td {
    padding: 10px 16px;
    vertical-align: middle;
}

/* Program Input Fields */
.fpm-program-input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 14px;
    transition: border-color 0.2s ease;
}

.fpm-program-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-muted);
}

.fpm-program-input--short {
    max-width: 150px;
}

/* Empty Row */
.fpm-empty-row {
    background-color: var(--surface-2);
}

.fpm-empty-message {
    text-align: center;
    padding: 24px;
    color: var(--text-muted);
    font-size: 14px;
}

/* Deleted Program Row */
.fpm-program-row--deleted {
    opacity: 0.3;
    pointer-events: none;
    background-color: var(--danger-light);
}

/* Add Program Button */
.fpm-add-program-wrapper {
    padding: 12px 16px;
    border-top: 1px solid var(--border);
    background: var(--surface-2);
}

.fpm-add-program-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border: 1px dashed var(--border-strong);
    border-radius: 6px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.fpm-add-program-btn:hover {
    border-color: var(--primary);
    color: var(--primary);
    background-color: var(--primary-muted);
}

/* Delete Program Button */
.fpm-delete-program-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.15s ease;
}

.fpm-delete-program-btn:hover {
    background-color: var(--danger-light);
    color: var(--danger);
}

.fpm-program-actions {
    text-align: center;
}
```


---

## 📌 ملخص التبسيطات النهائية

### ما تم تبسيطه:

1. **عمود واحد للاسم** (بدلاً من عربي + إنجليزي)
   - حالياً: `name` فقط
   - مستقبلاً: سيُضاف `name_en` عند تطوير النسخة الإنجليزية

2. **الجدول في Dashboard**:
   ```
   ┌──────────────────────────────────────────────────┐
   │ التخصصات │ المدة الدراسية │ الرسوم السنوية │ [×] │
   └──────────────────────────────────────────────────┘
   ```
   - 3 أعمدة بيانات + عمود الحذف
   - بدلاً من 4 أعمدة بيانات

3. **الجدول في Frontend**:
   ```
   ┌────────────────────────────────────────────────┐
   │ التخصصات │ المدة الدراسية │ الرسوم السنوية │
   └────────────────────────────────────────────────┘
   ```
   - نفس البنية البسيطة

4. **لا حاجة لـ Migration**:
   - النماذج الحالية كافية
   - `Program.name` موجود بالفعل
   - `Program.duration` موجود
   - `Program.tuition_fees` موجود

### الخطة جاهزة للتنفيذ:

✅ **Backend**: Forms + Views (nested formsets)
✅ **Frontend**: Template + CSS + JavaScript
✅ **UX**: Drag & drop + Collapse/Expand + Dynamic add/remove
✅ **Validation**: Client + Server side
✅ **Accessibility**: ARIA labels + Keyboard navigation

### التوقيت المتوقع:
- **Backend**: 2-3 أيام
- **Frontend**: 3-4 أيام
- **Testing**: 2 أيام
- **Total**: 7-9 أيام عمل

---

**الخطة محدثة ونهائية ✓**
**جاهزة للمراجعة والتنفيذ ✓**
