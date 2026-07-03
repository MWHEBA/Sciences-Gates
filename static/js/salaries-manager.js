/**
 * Salaries Manager
 * إدارة ديناميكية لجدول الآفاق الوظيفية والرواتب المتوقعة
 */

class SalariesManager {
    constructor() {
        this.container = document.getElementById('salary_tables-items-container');
        this.totalFormsInput = document.getElementById('id_salary_tables-TOTAL_FORMS');
        this.emptyState = document.getElementById('salary-empty-state');
        this.counterEl = document.getElementById('salary-counter');
        
        if (!this.container || !this.totalFormsInput) return;
        
        this.init();
    }

    init() {
        this.attachAddHandler();
        this.attachItemHandlers();
        this.updateState();
    }

    // ─── إضافة وظيفة جديدة ───
    attachAddHandler() {
        const addBtn = document.getElementById('salary-add-btn');
        if (addBtn) {
            addBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.addSalary();
            });
        }
    }

    addSalary() {
        const totalForms = parseInt(this.totalFormsInput.value);
        const newIndex = totalForms;

        // طي جميع العناصر المفتوحة حالياً
        this.container.querySelectorAll('.salary-item:not(.salary-item--deleted)').forEach(item => {
            this.toggleContent(item, false);
        });

        const item = this.createSalaryItem(newIndex);
        this.container.appendChild(item);
        this.totalFormsInput.value = newIndex + 1;

        // أنيميشن الظهور
        requestAnimationFrame(() => {
            item.classList.add('salary-item--visible');
        });

        this.attachItemHandlers();
        this.updateState();
        this.updateSortOrders();

        // فتح تلقائي للعنصر الجديد وتوجيه التركيز لأول حقل
        this.toggleContent(item, true);
        const titleInput = item.querySelector('input[name$="-job_title"]');
        if (titleInput) {
            setTimeout(() => titleInput.focus(), 150);
        }
    }

    // ─── إنشاء كود عنصر جديد ───
    createSalaryItem(index) {
        const template = document.getElementById('salary_tables-empty-form');
        if (!template) return null;

        let html = template.innerHTML;
        // استبدال الـ placeholder بالرقم الجديد
        html = html.replace(/__prefix__/g, index);

        const div = document.createElement('div');
        div.innerHTML = html;
        const item = div.firstElementChild;
        item.setAttribute('data-row-index', index);
        
        return item;
    }

    // ─── حذف عنصر ───
    deleteSalary(item) {
        const deleteInput = item.querySelector('input[name$="-DELETE"]');
        const idInput = item.querySelector('input[name$="-id"]');

        if (idInput && idInput.value) {
            // العنصر موجود بالفعل في قاعدة البيانات، سنقوم بتحديده للحذف وإخفائه
            if (deleteInput) {
                deleteInput.value = 'on';
                deleteInput.checked = true;
            }
            item.classList.add('salary-item--deleted');
            setTimeout(() => {
                item.style.display = 'none';
                this.updateState();
                this.updateNumbers();
            }, 300);
        } else {
            // العنصر جديد تماماً ولم يُحفظ، نقوم بحذفه مباشرة من الـ DOM
            item.classList.add('salary-item--deleted');
            setTimeout(() => {
                item.remove();
                this.reindexForms();
                this.updateState();
            }, 300);
        }
    }

    // ─── توسيع وطي محتوى البطاقة ───
    toggleContent(item, forceExpand = null) {
        const content = item.querySelector('.salary-item__content');
        const toggleBtn = item.querySelector('[data-toggle-content]');
        if (!content || !toggleBtn) return;

        const icon = toggleBtn.querySelector('svg');
        const isExpanded = content.classList.contains('expanded');
        const shouldExpand = forceExpand !== null ? forceExpand : !isExpanded;

        if (shouldExpand) {
            content.classList.add('expanded');
            if (icon) icon.classList.add('rotated');
            toggleBtn.setAttribute('aria-expanded', 'true');
        } else {
            content.classList.remove('expanded');
            if (icon) icon.classList.remove('rotated');
            toggleBtn.setAttribute('aria-expanded', 'false');
        }
    }

    // ─── تحديث اسم الوظيفة في الهيدر تلقائياً ───
    updateSalaryPreview(item) {
        const titleInput = item.querySelector('input[name$="-job_title"]');
        const preview = item.querySelector('.salary-item__title-preview');
        
        if (titleInput && preview) {
            const value = titleInput.value.trim();
            preview.textContent = value || 'وظيفة جديدة';
        }
    }

    // ─── إعادة ترقيم النماذج بالترتيب ───
    reindexForms() {
        const allItems = this.container.querySelectorAll('.salary-item');
        
        allItems.forEach((item, idx) => {
            item.setAttribute('data-row-index', idx);
            const inputs = item.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                const name = input.getAttribute('name');
                if (name) {
                    input.setAttribute('name', name.replace(/salary_tables-\d+-/, `salary_tables-${idx}-`));
                }
                const id = input.getAttribute('id');
                if (id) {
                    input.setAttribute('id', id.replace(/id_salary_tables-\d+-/, `id_salary_tables-${idx}-`));
                }
            });
            
            const labels = item.querySelectorAll('label');
            labels.forEach(label => {
                const htmlFor = label.getAttribute('for');
                if (htmlFor) {
                    label.setAttribute('for', htmlFor.replace(/id_salary_tables-\d+-/, `id_salary_tables-${idx}-`));
                }
            });
        });

        this.totalFormsInput.value = allItems.length;
        this.updateNumbers();
    }

    // ─── تحديث الأرقام الظاهرة ───
    updateNumbers() {
        const visibleItems = this.container.querySelectorAll('.salary-item:not(.salary-item--deleted):not([style*="display: none"])');
        visibleItems.forEach((item, idx) => {
            const numberEl = item.querySelector('.salary-item__number');
            if (numberEl) numberEl.textContent = idx + 1;
        });
    }

    // ─── تحديث ترتيب العرض في قاعدة البيانات ───
    updateSortOrders() {
        const visibleItems = this.container.querySelectorAll('.salary-item:not(.salary-item--deleted):not([style*="display: none"])');
        visibleItems.forEach((item, idx) => {
            const sortInput = item.querySelector('input[name$="-sort_order"]');
            if (sortInput) sortInput.value = idx;
        });
    }

    // ─── تحديث حالة القسم بالكامل ───
    updateState() {
        const visibleItems = this.container.querySelectorAll('.salary-item:not(.salary-item--deleted):not([style*="display: none"])');
        const count = visibleItems.length;

        if (this.emptyState) {
            this.emptyState.style.display = count === 0 ? 'flex' : 'none';
        }
        if (this.counterEl) {
            this.counterEl.textContent = count;
            this.counterEl.style.display = count > 0 ? 'inline-flex' : 'none';
        }
    }

    // ─── ربط الأحداث لكل عنصر ───
    attachItemHandlers() {
        // زر الحذف
        this.container.querySelectorAll('.salary-item__delete').forEach(btn => {
            btn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                const item = btn.closest('.salary-item');
                this.deleteSalary(item);
            };
        });

        // زر التوسيع والطي
        this.container.querySelectorAll('[data-toggle-content]').forEach(btn => {
            btn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                const item = btn.closest('.salary-item');
                this.toggleContent(item);
            };
        });

        // النقر على الهيدر نفسه لفتح البطاقة
        this.container.querySelectorAll('.salary-item__header').forEach(header => {
            header.onclick = (e) => {
                if (
                    e.target.closest('.salary-item__delete') ||
                    e.target.closest('[data-toggle-content]') ||
                    e.target.closest('.salary-item__drag-handle')
                ) {
                    return;
                }
                e.preventDefault();
                const item = header.closest('.salary-item');
                this.toggleContent(item);
            };
        });

        // تحديث العنوان عند تعديل المسمى الوظيفي
        this.container.querySelectorAll('input[name$="-job_title"]').forEach(input => {
            input.removeEventListener('input', input._previewHandler);
            input._previewHandler = (e) => {
                const item = e.target.closest('.salary-item');
                this.updateSalaryPreview(item);
            };
            input.addEventListener('input', input._previewHandler);
        });

        // إتاحة السحب والإفلات لإعادة الترتيب
        this.container.querySelectorAll('.salary-item').forEach(item => {
            item.setAttribute('draggable', 'true');
            item.ondragstart = (e) => this.onDragStart(e, item);
            item.ondragend = (e) => this.onDragEnd(e, item);
            item.ondragover = (e) => this.onDragOver(e, item);
            item.ondrop = (e) => this.onDrop(e, item);
        });
    }

    // ─── Drag & Drop Event Handlers ───
    onDragStart(e, item) {
        item.classList.add('salary-item--dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', '');
    }

    onDragEnd(e, item) {
        item.classList.remove('salary-item--dragging');
        this.container.querySelectorAll('.salary-item--drag-over').forEach(el => {
            el.classList.remove('salary-item--drag-over');
        });
        this.updateSortOrders();
        this.reindexForms();
    }

    onDragOver(e, item) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';

        this.container.querySelectorAll('.salary-item--drag-over').forEach(el => {
            el.classList.remove('salary-item--drag-over');
        });

        if (!item.classList.contains('salary-item--dragging')) {
            item.classList.add('salary-item--drag-over');
        }
    }

    onDrop(e, item) {
        e.preventDefault();
        item.classList.remove('salary-item--drag-over');

        const draggedItem = this.container.querySelector('.salary-item--dragging');
        if (draggedItem && draggedItem !== item) {
            const allItems = [...this.container.querySelectorAll('.salary-item:not([style*="display: none"])')];
            const draggedIdx = allItems.indexOf(draggedItem);
            const targetIdx = allItems.indexOf(item);

            if (draggedIdx < targetIdx) {
                item.after(draggedItem);
            } else {
                item.before(draggedItem);
            }
        }
    }
}

// ─── تهيئة عند تحميل الصفحة ───
document.addEventListener('DOMContentLoaded', () => {
    window.salariesManager = new SalariesManager();
});
