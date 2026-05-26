# خطة تطوير نظام الأسئلة الشائعة (FAQ)
## نظام إدارة ديناميكي احترافي

---

## 📋 جدول المحتويات

1. [التحليل الحالي](#التحليل-الحالي)
2. [المتطلبات والأهداف](#المتطلبات-والأهداف)
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
```python
class UniversityFAQ(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=500)
    answer = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order', 'id']
```

#### Forms (النماذج)
```python
UniversityFAQFormSet = inlineformset_factory(
    University,
    UniversityFAQ,
    fields=['question', 'answer', 'sort_order'],
    extra=1,
    can_delete=True,
    widgets={
        'question': forms.TextInput(attrs={...}),
        'answer': forms.Textarea(attrs={...}),
        'sort_order': forms.NumberInput(attrs={...}),
    }
)
```

#### الوضع الحالي في لوحة التحكم
- **عرض بسيط جداً**: Grid من الـ cards
- **كل card يحتوي على**:
  - حقل السؤال (TextInput)
  - حقل الإجابة (Textarea)
  - حقل ترتيب يدوي (NumberInput)
  - Checkbox للحذف
- **لا يوجد JavaScript**: كل شيء static HTML
- **لا يوجد CSS مخصص**: يستخدم Tailwind فقط
- **لا يوجد drag & drop**: الترتيب يدوي بالأرقام
- **لا يوجد expand/collapse**: كل الحقول ظاهرة دائماً

#### الوضع في الفرونت إند (صفحة الجامعة)
- **Accordion احترافي**: باستخدام Alpine.js
- **عرض منظم**: السؤال كـ header، الإجابة تظهر عند الضغط
- **تصميم جميل**: متناسق مع باقي الموقع
- **يعمل بشكل ممتاز**: لا يحتاج تعديل

---

## 📄 المتطلبات والأهداف

### الأهداف الرئيسية
1. **تحسين تجربة المستخدم** في لوحة التحكم
2. **إضافة إدارة ديناميكية** للأسئلة الشائعة
3. **تسهيل إعادة الترتيب** بدون إدخال أرقام يدوياً
4. **توفير واجهة احترافية** تشبه نظام الكليات والبرامج

### المميزات المطلوبة
- ✅ إضافة سؤال جديد بزر واحد
- ✅ حذف سؤال بزر واضح
- ✅ إعادة ترتيب بالسحب والإفلات (Drag & Drop)
- ✅ توسيع/طي الإجابة (Expand/Collapse)
- ✅ عداد للأسئلة
- ✅ حالة فارغة (Empty State)
- ✅ ترقيم تلقائي
- ✅ أنيميشن سلس

---

## ⚠️ الفجوات والمشاكل

### 1. واجهة مستخدم بدائية
- **المشكلة**: عرض Grid بسيط بدون تفاعل
- **التأثير**: صعوبة في إدارة عدد كبير من الأسئلة
- **الحل المطلوب**: واجهة ديناميكية مع أزرار واضحة

### 2. صعوبة إعادة الترتيب
- **المشكلة**: الترتيب يدوي عبر إدخال أرقام
- **التأثير**: احتمالية تكرار الأرقام، صعوبة في تغيير الترتيب
- **الحل المطلوب**: Drag & Drop مع تحديث تلقائي

### 3. عدم وجود Expand/Collapse
- **المشكلة**: كل الحقول ظاهرة دائماً
- **التأثير**: الصفحة طويلة جداً مع عدد كبير من الأسئلة
- **الحل المطلوب**: إمكانية طي الإجابات

### 4. عدم وجود Empty State
- **المشكلة**: لا توجد رسالة واضحة عند عدم وجود أسئلة
- **التأثير**: المستخدم لا يعرف ماذا يفعل
- **الحل المطلوب**: رسالة واضحة مع دعوة للإضافة

### 5. عدم وجود عداد
- **المشكلة**: لا يوجد عداد لعدد الأسئلة
- **التأثير**: صعوبة في معرفة عدد الأسئلة المضافة
- **الحل المطلوب**: عداد ديناميكي يتحدث مع كل تغيير

---

## 🎯 الرؤية المستهدفة

### تجربة المستخدم المثالية

#### في لوحة التحكم (Dashboard)
```
┌─────────────────────────────────────────────────────────────┐
│  الأسئلة الشائعة                    [3]    [+ إضافة سؤال]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⋮⋮ [1] ما هي شروط القبول في الجامعة؟           [▼] [×]  │
│      └─ [الإجابة مطوية]                                     │
│                                                             │
│  ⋮⋮ [2] كم تبلغ الرسوم الدراسية السنوية؟        [▼] [×]  │
│      └─ [الإجابة مطوية]                                     │
│                                                             │
│  ⋮⋮ [3] هل توفر الجامعة سكن للطلاب؟              [▼] [×]  │
│      └─ [الإجابة مطوية]                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### عند التوسيع (Expand)
```
┌─────────────────────────────────────────────────────────────┐
│  ⋮⋮ [1] ما هي شروط القبول في الجامعة؟           [▲] [×]  │
│      ┌───────────────────────────────────────────────────┐  │
│      │ السؤال: [ما هي شروط القبول في الجامعة؟____]  │  │
│      │                                                   │  │
│      │ الإجابة:                                          │  │
│      │ [شهادة الثانوية العامة بمعدل لا يقل عن 70%___] │  │
│      │ [اختبار القبول الخاص بالجامعة_______________] │  │
│      │ [إثبات إجادة اللغة الإنجليزية_______________] │  │
│      └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### الرموز:
- `⋮⋮` = مقبض السحب (Drag handle)
- `[▼]` = توسيع (Expand)
- `[▲]` = طي (Collapse)
- `[×]` = حذف
- `[+]` = إضافة
- `[3]` = عداد الأسئلة

#### المميزات المطلوبة:
1. **إضافة سؤال جديد** — زر واضح في الأعلى
2. **السحب والإفلات** — لإعادة ترتيب الأسئلة
3. **توسيع/طي** — لإخفاء/إظهار الإجابة
4. **حذف سريع** — أيقونة × واضحة
5. **ترقيم تلقائي** — يتحدث مع كل تغيير
6. **عداد ديناميكي** — يعرض عدد الأسئلة
7. **حالة فارغة** — رسالة واضحة عند عدم وجود أسئلة
8. **أنيميشن سلس** — عند الإضافة/الحذف/التوسيع

---

## 🏗️ البنية التقنية المقترحة

### 1. Django Models (لا تحتاج تعديل)
النموذج الحالي كافٍ تماماً:
```python
class UniversityFAQ(models.Model):
    university = ForeignKey(University)
    question = CharField(max_length=500)
    answer = TextField()
    sort_order = PositiveIntegerField(default=0)
```

### 2. Django Forms (تحتاج تعديل بسيط)

#### الوضع الحالي:
```python
UniversityFAQFormSet = inlineformset_factory(
    University,
    UniversityFAQ,
    fields=['question', 'answer', 'sort_order'],
    extra=1,
    can_delete=True,
    widgets={...}
)
```

#### التعديلات المطلوبة:
```python
# تحديث الـ widgets لتناسب التصميم الجديد
UniversityFAQFormSet = inlineformset_factory(
    University,
    UniversityFAQ,
    fields=['question', 'answer', 'sort_order'],
    extra=0,  # تغيير من 1 إلى 0 (نضيف بالـ JS)
    can_delete=True,
    widgets={
        'question': forms.TextInput(attrs={
            'class': 'faq-item__question-input',
            'placeholder': 'السؤال',
            'required': True,
            'dir': 'rtl',
        }),
        'answer': forms.Textarea(attrs={
            'class': 'faq-item__answer-input',
            'placeholder': 'الإجابة',
            'rows': 4,
            'required': True,
            'dir': 'rtl',
        }),
        'sort_order': forms.HiddenInput(),  # مخفي (يتحدث بالـ JS)
    },
)
```

### 3. Django Views (لا تحتاج تعديل)
الـ Views الحالية تعمل بشكل ممتاز:
- `UniversityCreateView` — يدعم FAQ formset
- `UniversityEditView` — يدعم FAQ formset
- لا حاجة لتعديلات

### 4. Template Structure (تحتاج إعادة بناء)

#### الهيكل المقترح:
```django
<!-- FAQ Section -->
<div class="faq-manager">
    <div class="faq-header">
        <div class="faq-title">
            <h2>الأسئلة الشائعة</h2>
            <span class="faq-counter" id="faq-counter">0</span>
        </div>
        <button type="button" id="faq-add-btn" class="faq-add-btn">
            <svg>...</svg>
            إضافة سؤال
        </button>
    </div>
    
    {{ faq_formset.management_form }}
    
    <div id="faq-items-container" class="faq-items-list">
        {% for faq_form in faq_formset %}
        <div class="faq-item" data-faq-index="{{ forloop.counter0 }}">
            <!-- FAQ Header -->
            <div class="faq-item__header">
                <span class="faq-item__drag-handle">⋮⋮</span>
                <span class="faq-item__number">[{{ forloop.counter }}]</span>
                <span class="faq-item__question-preview">{{ faq_form.question.value }}</span>
                <button type="button" class="faq-item__toggle" data-toggle-answer>
                    <svg class="faq-toggle-icon">...</svg>
                </button>
                <button type="button" class="faq-item__delete" data-delete-faq>
                    <svg>...</svg>
                </button>
            </div>
            
            <!-- FAQ Content (قابل للطي) -->
            <div class="faq-item__content" style="display: none;">
                <div class="faq-item__field">
                    <label>السؤال</label>
                    {{ faq_form.question }}
                </div>
                <div class="faq-item__field">
                    <label>الإجابة</label>
                    {{ faq_form.answer }}
                </div>
                {{ faq_form.sort_order }}
                {{ faq_form.id }}
                {{ faq_form.DELETE }}
            </div>
        </div>
        {% endfor %}
    </div>
    
    <!-- Empty State -->
    <div class="faq-empty-state" id="faq-empty-state">
        <div class="faq-empty-icon">❓</div>
        <p class="faq-empty-text">لا توجد أسئلة شائعة مضافة</p>
        <p class="faq-empty-hint">اضغط "إضافة سؤال" لإضافة سؤال جديد</p>
    </div>
</div>
```

### 5. JavaScript Architecture (جديد بالكامل)

#### الملف المطلوب: `faq-manager.js`

```javascript
/**
 * FAQ Manager
 * إدارة ديناميكية للأسئلة الشائعة
 * 
 * Features:
 * - إضافة/حذف أسئلة
 * - إعادة ترتيب بالسحب والإفلات
 * - توسيع/طي الإجابات
 * - تحديث تلقائي للترتيب والأرقام
 */

class FAQManager {
    constructor() {
        this.container = document.getElementById('faq-items-container');
        this.totalFormsInput = document.getElementById('id_faqs-TOTAL_FORMS');
        this.emptyState = document.getElementById('faq-empty-state');
        this.counterEl = document.getElementById('faq-counter');
        
        if (!this.container || !this.totalFormsInput) return;
        
        this.init();
    }

    init() {
        this.attachAddHandler();
        this.attachItemHandlers();
        this.initDragAndDrop();
        this.updateState();
    }

    // ─── إضافة سؤال جديد ───
    addFAQ() {
        const totalForms = parseInt(this.totalFormsInput.value);
        const newIndex = totalForms;
        const item = this.createFAQItem(newIndex);
        
        this.container.appendChild(item);
        this.totalFormsInput.value = newIndex + 1;
        
        // أنيميشن الظهور
        requestAnimationFrame(() => {
            item.classList.add('faq-item--visible');
        });
        
        this.attachItemHandlers();
        this.updateState();
        this.updateSortOrders();
        
        // توسيع تلقائي للسؤال الجديد
        this.toggleAnswer(item, true);
        
        // Focus على حقل السؤال
        const questionInput = item.querySelector('[name$="-question"]');
        if (questionInput) {
            setTimeout(() => questionInput.focus(), 150);
        }
    }

    // ─── حذف سؤال ───
    deleteFAQ(item) {
        const deleteInput = item.querySelector('[name$="-DELETE"]');
        const idInput = item.querySelector('[name$="-id"]');

        if (idInput && idInput.value) {
            // سؤال موجود في الداتابيز
            deleteInput.value = 'on';
            item.classList.add('faq-item--deleted');
            setTimeout(() => {
                item.style.display = 'none';
                this.updateState();
                this.updateNumbers();
            }, 300);
        } else {
            // سؤال جديد
            item.classList.add('faq-item--deleted');
            setTimeout(() => {
                item.remove();
                this.reindexForms();
                this.updateState();
            }, 300);
        }
    }

    // ─── توسيع/طي الإجابة ───
    toggleAnswer(item, forceExpand = null) {
        const content = item.querySelector('.faq-item__content');
        const toggleBtn = item.querySelector('[data-toggle-answer]');
        const icon = toggleBtn.querySelector('svg');
        
        const isExpanded = content.style.display !== 'none';
        const shouldExpand = forceExpand !== null ? forceExpand : !isExpanded;
        
        if (shouldExpand) {
            content.style.display = 'block';
            icon.classList.add('rotated');
            toggleBtn.setAttribute('aria-expanded', 'true');
        } else {
            content.style.display = 'none';
            icon.classList.remove('rotated');
            toggleBtn.setAttribute('aria-expanded', 'false');
        }
    }

    // ─── إنشاء عنصر FAQ جديد ───
    createFAQItem(index) {
        const item = document.createElement('div');
        item.className = 'faq-item';
        item.setAttribute('data-faq-index', index);
        item.innerHTML = `
            <div class="faq-item__header">
                <span class="faq-item__drag-handle" title="اسحب لإعادة الترتيب">⋮⋮</span>
                <span class="faq-item__number">[${index + 1}]</span>
                <span class="faq-item__question-preview">سؤال جديد</span>
                <button type="button" class="faq-item__toggle" data-toggle-answer aria-expanded="false">
                    <svg class="faq-toggle-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </button>
                <button type="button" class="faq-item__delete" data-delete-faq title="حذف السؤال">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14"/>
                        <line x1="10" y1="11" x2="10" y2="17"/>
                        <line x1="14" y1="11" x2="14" y2="17"/>
                    </svg>
                </button>
            </div>
            <div class="faq-item__content" style="display: none;">
                <div class="faq-item__field">
                    <label for="id_faqs-${index}-question">السؤال</label>
                    <input type="text"
                           name="faqs-${index}-question"
                           id="id_faqs-${index}-question"
                           class="faq-item__question-input"
                           placeholder="السؤال"
                           dir="rtl"
                           required>
                </div>
                <div class="faq-item__field">
                    <label for="id_faqs-${index}-answer">الإجابة</label>
                    <textarea name="faqs-${index}-answer"
                              id="id_faqs-${index}-answer"
                              class="faq-item__answer-input"
                              placeholder="الإجابة"
                              rows="4"
                              dir="rtl"
                              required></textarea>
                </div>
                <input type="hidden" name="faqs-${index}-sort_order" value="${index}">
                <input type="hidden" name="faqs-${index}-id" value="">
                <input type="hidden" name="faqs-${index}-DELETE" value="">
            </div>
        `;
        return item;
    }

    // ─── باقي الـ Methods ───
    reindexForms() { /* ... */ }
    updateNumbers() { /* ... */ }
    updateSortOrders() { /* ... */ }
    updateState() { /* ... */ }
    attachItemHandlers() { /* ... */ }
    initDragAndDrop() { /* ... */ }
}

// تهيئة عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', () => {
    new FAQManager();
});
```

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
--text-primary: #0F172A;
--text-secondary: #475569;
--text-muted: #94A3B8;
```

### 2. هيكل الـ CSS

**`faq-manager.css`** — الملف الجديد
```css
/* ═══ Container ═══ */
.faq-manager {
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-sm);
    padding: 24px;
}

/* ═══ Header ═══ */
.faq-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
}

.faq-title {
    display: flex;
    align-items: center;
    gap: 10px;
}

.faq-title h2 {
    color: var(--text-primary);
    font-size: 18px;
    font-weight: 600;
    margin: 0;
}

.faq-counter {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 24px;
    height: 24px;
    padding: 0 7px;
    border-radius: 12px;
    background-color: var(--primary-light);
    color: var(--primary);
    font-size: 12px;
    font-weight: 600;
}

/* ═══ Add Button ═══ */
.faq-add-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border: 1px dashed var(--border-strong);
    border-radius: var(--radius-sm);
    background: transparent;
    color: var(--text-secondary);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.faq-add-btn:hover {
    border-color: var(--primary);
    color: var(--primary);
    background-color: var(--primary-muted);
}

/* ═══ FAQ Items List ═══ */
.faq-items-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-height: 48px;
}

/* ═══ FAQ Item ═══ */
.faq-item {
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background-color: var(--surface);
    transition: all 0.2s ease;
    opacity: 0;
    transform: translateY(-8px);
}

.faq-item--visible {
    opacity: 1;
    transform: translateY(0);
}

.faq-item:hover {
    border-color: var(--border-strong);
    box-shadow: var(--shadow-card);
}

/* ═══ FAQ Item Header ═══ */
.faq-item__header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background-color: var(--surface-2);
    border-radius: var(--radius-sm) var(--radius-sm) 0 0;
    cursor: pointer;
}

/* ═══ Drag Handle ═══ */
.faq-item__drag-handle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    color: var(--text-muted);
    cursor: grab;
    flex-shrink: 0;
    transition: all 0.15s ease;
}

.faq-item__drag-handle:hover {
    background-color: var(--surface);
    color: var(--text-secondary);
}

.faq-item__drag-handle:active {
    cursor: grabbing;
}

/* ═══ Number Badge ═══ */
.faq-item__number {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 32px;
    height: 28px;
    padding: 0 8px;
    border-radius: 6px;
    background-color: var(--primary-light);
    color: var(--primary);
    font-size: 12px;
    font-weight: 600;
    flex-shrink: 0;
}

/* ═══ Question Preview ═══ */
.faq-item__question-preview {
    flex: 1;
    color: var(--text-primary);
    font-size: 14px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ═══ Toggle Button ═══ */
.faq-item__toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.15s ease;
}

.faq-item__toggle:hover {
    background-color: var(--surface);
    color: var(--text-secondary);
}

.faq-toggle-icon {
    transition: transform 0.2s ease;
}

.faq-toggle-icon.rotated {
    transform: rotate(180deg);
}

/* ═══ Delete Button ═══ */
.faq-item__delete {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.15s ease;
}

.faq-item__delete:hover {
    background-color: var(--danger-light);
    color: var(--danger);
}

/* ═══ FAQ Item Content ═══ */
.faq-item__content {
    padding: 16px;
    border-top: 1px solid var(--border);
    animation: slideDown 0.2s ease;
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* ═══ Form Fields ═══ */
.faq-item__field {
    margin-bottom: 16px;
}

.faq-item__field:last-child {
    margin-bottom: 0;
}

.faq-item__field label {
    display: block;
    color: var(--text-secondary);
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 6px;
}

.faq-item__question-input,
.faq-item__answer-input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background-color: var(--surface);
    color: var(--text-primary);
    font-size: 14px;
    font-family: inherit;
    transition: border-color 0.2s ease;
    box-sizing: border-box;
}

.faq-item__question-input:focus,
.faq-item__answer-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-muted);
}

.faq-item__answer-input {
    resize: vertical;
    min-height: 100px;
}

/* ═══ States ═══ */
.faq-item--dragging {
    opacity: 0.5;
    border-style: dashed;
    border-color: var(--primary);
    background-color: var(--primary-light);
}

.faq-item--deleted {
    opacity: 0;
    transform: translateX(20px);
    pointer-events: none;
    transition: all 0.3s ease;
}

/* ═══ Empty State ═══ */
.faq-empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    border: 2px dashed var(--border);
    border-radius: var(--radius-sm);
    background-color: var(--surface-2);
    text-align: center;
    gap: 12px;
}

.faq-empty-icon {
    font-size: 48px;
    opacity: 0.5;
}

.faq-empty-text {
    color: var(--text-muted);
    font-size: 14px;
    margin: 0;
}

.faq-empty-hint {
    color: var(--text-muted);
    font-size: 12px;
    margin: 0;
    opacity: 0.7;
}

/* ═══ Responsive ═══ */
@media (max-width: 768px) {
    .faq-item__header {
        gap: 8px;
        padding: 10px 12px;
    }
    
    .faq-item__number {
        min-width: 28px;
        height: 24px;
        font-size: 11px;
    }
    
    .faq-item__question-preview {
        font-size: 13px;
    }
}
```

---

## 🎨 تصميم واجهة المستخدم

### 1. إعادة استخدام CSS من Faculty-Programs

#### الأنماط المشتركة (نستخدمها كما هي):
```css
/* من faculty-programs-manager.css */

/* ✅ نستخدم مباشرة */
.faq-item__drag-handle { /* نفس .faculty-item__drag-handle */ }
.faq-item__delete { /* نفس .faculty-item__delete */ }
.faq-item--dragging { /* نفس .faculty-item--dragging */ }
.faq-item--deleted { /* نفس .faculty-item--deleted */ }
.faq-empty-state { /* نفس .faculty-empty-state */ }
.faq-counter { /* نفس .faculty-counter */ }
.faq-add-btn { /* نفس .faculty-add-btn */ }
```

#### الأنماط المخصصة (نضيفها فقط):
```css
/* faq-manager.css - الإضافات الجديدة فقط */

.faq-item {
    /* مشابه لـ .faculty-item لكن بدون grid معقد */
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background-color: var(--surface);
    margin-bottom: 8px;
    transition: all 0.2s ease;
}

.faq-item__header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background-color: var(--surface-2);
    border-bottom: 1px solid var(--border);
}

.faq-item__question-preview {
    flex: 1;
    color: var(--text-primary);
    font-weight: 500;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.faq-item__content {
    padding: 16px;
    display: none; /* يظهر عند التوسيع */
}

.faq-item__content.expanded {
    display: block;
    animation: slideDown 0.2s ease;
}

.faq-item__toggle svg.rotated {
    transform: rotate(180deg);
}

/* باقي الأنماط مشابهة جداً للـ faculty-programs */
```

### 2. هيكل HTML النهائي

```django
<!-- FAQ Section في create.html و edit.html -->
<div style="background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-sm);
            padding: 24px;">
    <section>
        <div class="faq-section__header">
            <div class="faq-section__title">
                <h2 class="text-lg font-semibold">الأسئلة الشائعة</h2>
                <span class="faq-counter" id="faq-counter">0</span>
            </div>
            <button type="button" class="faq-add-btn" id="faq-add-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"/>
                    <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                إضافة سؤال
            </button>
        </div>

        {{ faq_formset.management_form }}

        <div id="faq-items-container">
            {% for faq_form in faq_formset %}
            <div class="faq-item faq-item--existing faq-item--visible" data-faq-index="{{ forloop.counter0 }}">
                <div class="faq-item__header">
                    <div class="faq-item__drag-handle" title="اسحب لإعادة الترتيب">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="9" cy="6" r="1.5"/>
                            <circle cx="15" cy="6" r="1.5"/>
                            <circle cx="9" cy="12" r="1.5"/>
                            <circle cx="15" cy="12" r="1.5"/>
                            <circle cx="9" cy="18" r="1.5"/>
                            <circle cx="15" cy="18" r="1.5"/>
                        </svg>
                    </div>
                    <div class="faq-item__number">{{ forloop.counter }}</div>
                    <div class="faq-item__question-preview">{{ faq_form.question.value|default:"سؤال جديد" }}</div>
                    <button type="button" class="faq-item__toggle" title="عرض/إخفاء الإجابة" data-toggle-answer>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </button>
                    <button type="button" class="faq-item__delete" title="حذف السؤال">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14"/>
                            <line x1="10" y1="11" x2="10" y2="17"/>
                            <line x1="14" y1="11" x2="14" y2="17"/>
                        </svg>
                    </button>
                </div>
                
                <div class="faq-item__content" style="display: none;">
                    <div class="faq-item__field">
                        <label for="{{ faq_form.question.id_for_label }}">السؤال</label>
                        {{ faq_form.question }}
                    </div>
                    <div class="faq-item__field">
                        <label for="{{ faq_form.answer.id_for_label }}">الإجابة</label>
                        {{ faq_form.answer }}
                    </div>
                    {{ faq_form.sort_order }}
                    {{ faq_form.id }}
                    <input type="hidden" name="faqs-{{ forloop.counter0 }}-DELETE" value="">
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="faq-empty-state" id="faq-empty-state">
            <div class="faq-empty-state__icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
            </div>
            <p class="faq-empty-state__text">لا توجد أسئلة شائعة مضافة</p>
            <p class="faq-empty-state__hint">اضغط "إضافة سؤال" لإضافة سؤال جديد</p>
        </div>
    </section>
</div>
```

---

## 📝 خطة التنفيذ

### المرحلة 1: إعداد الملفات (15 دقيقة)

#### 1.1 إنشاء ملف CSS
```bash
# إنشاء faq-manager.css
touch static/css/faq-manager.css
```

**المحتوى**: نسخ الأنماط المشتركة من `faculty-programs-manager.css` وتعديل الأسماء:
- ✅ نسخ: drag-handle, delete button, empty state, counter, add button
- ✅ تعديل: faq-item structure (أبسط من faculty-item)
- ✅ إضافة: question-preview, toggle styles

**الوقت المتوقع**: 10 دقائق

#### 1.2 إنشاء ملف JavaScript
```bash
# إنشاء faq-manager.js
touch static/js/faq-manager.js
```

**المحتوى**: نسخ الهيكل من `faculty-programs-manager.js` وتبسيطه:
- ✅ نسخ: constructor, init, addItem, deleteItem, reindex, updateState
- ✅ حذف: كل ما يتعلق بالـ nested programs
- ✅ تعديل: أسماء المتغيرات والـ selectors
- ✅ إضافة: toggleAnswer method, updateQuestionPreview method

**الوقت المتوقع**: 5 دقائق

---

### المرحلة 2: تطوير CSS (30 دقيقة)

#### 2.1 نسخ الأنماط المشتركة
```css
/* من faculty-programs-manager.css - نسخ مباشر */

/* ═══ Drag Handle ═══ */
.faq-item__drag-handle {
    /* نفس .faculty-item__drag-handle تماماً */
}

/* ═══ Delete Button ═══ */
.faq-item__delete {
    /* نفس .faculty-item__delete تماماً */
}

/* ═══ Empty State ═══ */
.faq-empty-state {
    /* نفس .faculty-empty-state تماماً */
}

/* ═══ Counter ═══ */
.faq-counter {
    /* نفس .faculty-counter تماماً */
}

/* ═══ Add Button ═══ */
.faq-add-btn {
    /* نفس .faculty-add-btn تماماً */
}

/* ═══ States ═══ */
.faq-item--dragging {
    /* نفس .faculty-item--dragging تماماً */
}

.faq-item--deleted {
    /* نفس .faculty-item--deleted تماماً */
}

.faq-item--visible {
    /* نفس .faculty-item--visible تماماً */
}
```

#### 2.2 إضافة الأنماط المخصصة
```css
/* الأنماط الجديدة الخاصة بالـ FAQ فقط */

.faq-item {
    /* أبسط من faculty-item - بدون grid معقد */
}

.faq-item__header {
    /* header بسيط مع question preview */
}

.faq-item__question-preview {
    /* عرض السؤال في الـ header */
}

.faq-item__content {
    /* المحتوى القابل للطي */
}

.faq-item__field {
    /* حاوية الحقل (label + input) */
}

.faq-item__question-input,
.faq-item__answer-input {
    /* تنسيق الحقول */
}

.faq-item__toggle svg.rotated {
    /* أيقونة التوسيع/الطي */
}
```

**الوقت المتوقع**: 30 دقيقة

---

### المرحلة 3: تطوير JavaScript (45 دقيقة)

#### 3.1 نسخ الهيكل الأساسي (10 دقائق)
```javascript
// من faculty-programs-manager.js - نسخ وتعديل الأسماء

class FAQManager {
    constructor() {
        // نفس الهيكل، تغيير الأسماء فقط
        this.container = document.getElementById('faq-items-container');
        this.totalFormsInput = document.getElementById('id_faqs-TOTAL_FORMS');
        this.emptyState = document.getElementById('faq-empty-state');
        this.counterEl = document.getElementById('faq-counter');
        
        if (!this.container || !this.totalFormsInput) return;
        this.init();
    }

    init() {
        this.attachAddHandler();
        this.attachItemHandlers();
        this.updateState();
    }
}
```

#### 3.2 نسخ Methods الأساسية (15 دقيقة)
```javascript
// Methods نسخها مباشرة من FacultyProgramsManager

addFAQ() {
    // نفس addFaculty() لكن بدون programs
}

deleteFAQ(item) {
    // نفس deleteFaculty() تماماً
}

reindexForms() {
    // نفس الكود تماماً، تغيير 'faculties' إلى 'faqs'
}

updateNumbers() {
    // نفس الكود تماماً
}

updateSortOrders() {
    // نفس الكود تماماً
}

updateState() {
    // نفس الكود تماماً
}

attachItemHandlers() {
    // نفس الهيكل، حذف كل ما يتعلق بالـ programs
}

// Drag & Drop - نسخ كامل
onDragStart(e, item) { /* نفس الكود */ }
onDragEnd(e, item) { /* نفس الكود */ }
onDragOver(e, item) { /* نفس الكود */ }
onDrop(e, item) { /* نفس الكود */ }
```

#### 3.3 إضافة Methods الجديدة (20 دقيقة)
```javascript
// Methods جديدة خاصة بالـ FAQ

toggleAnswer(item, forceExpand = null) {
    const content = item.querySelector('.faq-item__content');
    const toggleBtn = item.querySelector('[data-toggle-answer]');
    const icon = toggleBtn.querySelector('svg');
    
    const isExpanded = content.style.display !== 'none';
    const shouldExpand = forceExpand !== null ? forceExpand : !isExpanded;
    
    if (shouldExpand) {
        content.style.display = 'block';
        icon.classList.add('rotated');
    } else {
        content.style.display = 'none';
        icon.classList.remove('rotated');
    }
}

updateQuestionPreview(item) {
    const questionInput = item.querySelector('[name$="-question"]');
    const preview = item.querySelector('.faq-item__question-preview');
    
    if (questionInput && preview) {
        const value = questionInput.value.trim();
        preview.textContent = value || 'سؤال جديد';
    }
}

createFAQItem(index) {
    // مشابه لـ createFacultyItem لكن أبسط (بدون programs)
    const item = document.createElement('div');
    item.className = 'faq-item';
    item.setAttribute('data-faq-index', index);
    item.innerHTML = `...`; // HTML template
    return item;
}
```

**الوقت المتوقع**: 45 دقيقة

---

### المرحلة 4: تحديث Templates (30 دقيقة)

#### 4.1 تحديث create.html (15 دقيقة)
```django
<!-- استبدال القسم الحالي للـ FAQ -->

<!-- القديم (سطر 320-380 تقريباً) -->
<div id="faq-formset">
    {{ faq_formset.management_form }}
    {% for faq_form in faq_formset %}
    <div class="mb-4 p-4 rounded-lg">
        <!-- Grid بسيط -->
    </div>
    {% endfor %}
</div>

<!-- الجديد -->
<div style="background-color: var(--surface); ...">
    <section>
        <div class="faq-section__header">
            <!-- Header مع عداد وزر إضافة -->
        </div>
        
        {{ faq_formset.management_form }}
        
        <div id="faq-items-container">
            {% for faq_form in faq_formset %}
            <div class="faq-item faq-item--existing faq-item--visible">
                <!-- الهيكل الجديد -->
            </div>
            {% endfor %}
        </div>
        
        <div class="faq-empty-state" id="faq-empty-state">
            <!-- Empty state -->
        </div>
    </section>
</div>
```

#### 4.2 تحديث edit.html (15 دقيقة)
- نفس التعديلات في create.html

#### 4.3 إضافة الـ Scripts والـ Styles
```django
{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/html_editor.css' %}">
<link rel="stylesheet" href="{% static 'css/faculty-programs-manager.css' %}">
<link rel="stylesheet" href="{% static 'css/faq-manager.css' %}">  <!-- جديد -->
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/html_editor.js' %}"></script>
<script src="{% static 'js/faculty-programs-manager.js' %}"></script>
<script src="{% static 'js/faq-manager.js' %}"></script>  <!-- جديد -->
{% endblock %}
```

**الوقت المتوقع**: 30 دقيقة

---

### المرحلة 5: تحديث Forms (10 دقيقة)

#### تعديل `apps/dashboard/forms/university.py`
```python
# تحديث UniversityFAQFormSet

UniversityFAQFormSet = inlineformset_factory(
    University,
    UniversityFAQ,
    fields=['question', 'answer', 'sort_order'],
    extra=0,  # تغيير من 1 إلى 0
    can_delete=True,
    widgets={
        'question': forms.TextInput(attrs={
            'class': 'faq-item__question-input',  # تحديث class
            'placeholder': 'السؤال',
            'required': True,
            'dir': 'rtl',
        }),
        'answer': forms.Textarea(attrs={
            'class': 'faq-item__answer-input',  # تحديث class
            'placeholder': 'الإجابة',
            'rows': 4,
            'required': True,
            'dir': 'rtl',
        }),
        'sort_order': forms.HiddenInput(),  # تغيير إلى HiddenInput
    },
    labels={
        'question': 'السؤال',
        'answer': 'الإجابة',
        'sort_order': 'ترتيب العرض',
    },
)
```

**الوقت المتوقع**: 10 دقيقة

---

### المرحلة 6: الاختبار والتحسين (30 دقيقة)

#### 6.1 اختبار الوظائف (20 دقيقة)
- [ ] إضافة سؤال جديد
- [ ] حذف سؤال
- [ ] إعادة ترتيب بالسحب والإفلات
- [ ] توسيع/طي الإجابة
- [ ] تحديث question preview عند الكتابة
- [ ] حفظ البيانات بشكل صحيح
- [ ] Empty state يظهر/يختفي بشكل صحيح
- [ ] العداد يتحدث بشكل صحيح

#### 6.2 إصلاح الـ Bugs (10 دقيقة)
- إصلاح أي مشاكل تظهر في الاختبار

**الوقت المتوقع**: 30 دقيقة

---

## ⏱️ الوقت الإجمالي المتوقع

| المرحلة | الوقت |
|---------|-------|
| 1. إعداد الملفات | 15 دقيقة |
| 2. تطوير CSS | 30 دقيقة |
| 3. تطوير JavaScript | 45 دقيقة |
| 4. تحديث Templates | 30 دقيقة |
| 5. تحديث Forms | 10 دقيقة |
| 6. الاختبار والتحسين | 30 دقيقة |
| **المجموع** | **160 دقيقة (2.5 ساعة)** |

---

## ⚙️ الاعتبارات الفنية

### 1. إعادة استخدام الكود

#### ما نستخدمه من Faculty-Programs:
✅ **CSS (80% إعادة استخدام)**:
- Drag handle styles
- Delete button styles
- Empty state styles
- Counter styles
- Add button styles
- Dragging/Deleted states
- Animations

✅ **JavaScript (70% إعادة استخدام)**:
- Constructor pattern
- init() method
- addItem() logic
- deleteItem() logic
- reindexForms() method
- updateNumbers() method
- updateSortOrders() method
- updateState() method
- Drag & Drop methods (كامل)
- attachItemHandlers() pattern

#### ما نضيفه جديد:
🆕 **CSS (20% جديد)**:
- faq-item structure (أبسط)
- faq-item__header layout
- faq-item__question-preview
- faq-item__content (collapsible)
- faq-item__field styles
- Toggle icon rotation

🆕 **JavaScript (30% جديد)**:
- toggleAnswer() method
- updateQuestionPreview() method
- createFAQItem() template (مبسط)
- Event listener للـ question input

### 2. الفروقات الرئيسية عن Faculty-Programs

| الميزة | Faculty-Programs | FAQ |
|--------|------------------|-----|
| **التعقيد** | Nested (كليات + برامج) | Flat (أسئلة فقط) |
| **الحقول** | 4 حقول (name, duration, fees, sort) | 3 حقول (question, answer, sort) |
| **Expand/Collapse** | للبرامج داخل الكلية | للإجابة داخل السؤال |
| **Preview** | لا يوجد | عرض السؤال في الـ header |
| **JavaScript Lines** | ~450 سطر | ~200 سطر (أبسط) |
| **CSS Lines** | ~240 سطر | ~150 سطر (أبسط) |

### 3. Performance

#### التحسينات:
- ✅ Event delegation للـ buttons
- ✅ Debounce للـ question preview update (300ms)
- ✅ RequestAnimationFrame للـ animations
- ✅ CSS transitions بدل JavaScript animations

#### الحد الأقصى المتوقع:
- **عدد الأسئلة**: 50 سؤال (أكثر من كافٍ)
- **حجم الصفحة**: +15KB (CSS + JS)
- **الأداء**: ممتاز (أبسط من Faculty-Programs)

---

## ✅ Checklist النهائي

### قبل البدء
- [ ] قراءة الخطة كاملة
- [ ] فهم الكود الموجود في Faculty-Programs
- [ ] تجهيز البيئة

### أثناء التنفيذ
- [ ] إنشاء `faq-manager.css`
- [ ] إنشاء `faq-manager.js`
- [ ] تحديث `create.html`
- [ ] تحديث `edit.html`
- [ ] تحديث `forms/university.py`
- [ ] إضافة الـ scripts والـ styles

### الاختبار
- [ ] إضافة سؤال جديد
- [ ] حذف سؤال موجود
- [ ] حذف سؤال جديد (غير محفوظ)
- [ ] إعادة ترتيب بالسحب والإفلات
- [ ] توسيع/طي الإجابة
- [ ] تحديث question preview
- [ ] حفظ النموذج
- [ ] تحميل صفحة التعديل
- [ ] Empty state
- [ ] العداد
- [ ] Responsive على الموبايل

### بعد الانتهاء
- [ ] Code review
- [ ] اختبار على متصفحات مختلفة
- [ ] اختبار Accessibility
- [ ] Commit & Push

---

## 🎯 الخلاصة

### النقاط الرئيسية:
1. **إعادة استخدام 75% من كود Faculty-Programs**
2. **نظام أبسط بكثير** (لا يوجد nesting)
3. **وقت تنفيذ قصير** (~2.5 ساعة)
4. **تصميم متناسق** مع باقي النظام
5. **أداء ممتاز** (أخف من Faculty-Programs)

### الملفات المطلوبة:
- ✅ `static/css/faq-manager.css` (جديد)
- ✅ `static/js/faq-manager.js` (جديد)
- ✅ `templates/dashboard/universities/create.html` (تعديل)
- ✅ `templates/dashboard/universities/edit.html` (تعديل)
- ✅ `apps/dashboard/forms/university.py` (تعديل بسيط)

### الملفات المرجعية:
- 📖 `static/css/faculty-programs-manager.css` (نسخ منها)
- 📖 `static/js/faculty-programs-manager.js` (نسخ منها)

---

**جاهز للتنفيذ! 🚀**
