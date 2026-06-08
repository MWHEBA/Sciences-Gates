/**
 * Bulk Paste Component
 * مكون اللصق الجماعي - يسمح بنسخ جداول كاملة ولصقها في النماذج
 * 
 * الاستخدام:
 * const bulkPaste = new BulkPaste({
 *     containerSelector: '#programs-container',
 *     formsetPrefix: 'programs',
 *     fields: ['name', 'duration', 'tuition_fees'],
 *     fieldLabels: { name: 'البرنامج', duration: 'المدة', tuition_fees: 'الرسوم' }
 * });
 */

class BulkPaste {
    constructor(options) {
        this.containerSelector = options.containerSelector;
        this.formsetPrefix = options.formsetPrefix;
        this.fields = options.fields;
        this.fieldLabels = options.fieldLabels || {};
        this.container = document.querySelector(this.containerSelector);
        
        if (!this.container) {
            return;
        }

        this.init();
    }

    init() {
        
        // وضع علامة على أنها تم تهيئتها
        this.container.dataset.bulkPasteInitialized = 'true';
        
        // البحث عن زر الإضافة الموجود
        let addButton = null;
        
        // 1️⃣ البحث داخل الحاوية
        addButton = this.container.querySelector('[data-add-program], [data-add-item]');
        
        // 2️⃣ البحث في الـ parent الأب (faculty-item__programs-wrapper)
        if (!addButton) {
            const programsWrapper = this.container.closest('[class*="programs-wrapper"]');
            
            if (programsWrapper) {
                addButton = programsWrapper.querySelector('[data-add-program], [data-add-item]');
            }
        }
        
        // 3️⃣ البحث في الـ table الأب
        if (!addButton) {
            const table = this.container.closest('table');
            
            if (table) {
                // ابحث عن الـ wrapper بعد الـ table
                let nextElement = table.nextElementSibling;
                while (nextElement) {
                    if (nextElement.classList.contains('fpm-add-program-wrapper')) {
                        addButton = nextElement.querySelector('[data-add-program], [data-add-item]');
                        break;
                    }
                    nextElement = nextElement.nextElementSibling;
                }
            }
        }
        
        // 4️⃣ البحث في الـ parent الأب (faculty-item)
        if (!addButton) {
            const facultyItem = this.container.closest('[class*="faculty-item"]');
            
            if (facultyItem) {
                // ابحث عن جميع الأزرار في faculty-item
                const allButtons = facultyItem.querySelectorAll('button[data-add-program], button[data-add-item]');
                if (allButtons.length > 0) {
                    addButton = allButtons[0];
                }
            }
        }
        
        // 5️⃣ البحث في جميع الأزرار بـ class fpm-add-program-btn
        if (!addButton) {
            const allProgramButtons = document.querySelectorAll('.fpm-add-program-btn');
            
            if (allProgramButtons.length > 0) {
                // ابحث عن الزر الأقرب للـ container
                let closestButton = null;
                let minDistance = Infinity;
                
                allProgramButtons.forEach(btn => {
                    const distance = Math.abs(btn.getBoundingClientRect().top - this.container.getBoundingClientRect().top);
                    if (distance < minDistance) {
                        minDistance = distance;
                        closestButton = btn;
                    }
                });
                
                if (closestButton) {
                    addButton = closestButton;
                }
            }
        }
        
        if (!addButton) {
            return;
        }

        // إنشاء زر اللصق الجماعي
        this.createBulkPasteButton(addButton);
        
        // إنشاء modal المعاينة
        this.createPreviewModal();
    }

    createBulkPasteButton(addButton) {
        // Creating bulk paste button
        
        const bulkPasteBtn = document.createElement('button');
        bulkPasteBtn.type = 'button';
        bulkPasteBtn.className = 'bulk-paste-btn';
        bulkPasteBtn.style.cssText = 'display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border: 1px dashed var(--border-strong); border-radius: 6px; background: transparent; color: var(--text-secondary); font-size: 13px; cursor: pointer; transition: all 0.2s ease; font-family: inherit; font-weight: 600;';
        bulkPasteBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
                <path d="M9 14h6M9 10h6"></path>
            </svg>
            استيراد برامج
        `;

        bulkPasteBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleBulkPaste();
        });

        // إدراج الزر بجانب زر الإضافة
        // تحقق من أن الزر له parent
        if (addButton.parentNode) {
            addButton.parentNode.insertBefore(bulkPasteBtn, addButton.nextSibling);
        }
    }

    createPreviewModal() {
        const modal = document.createElement('div');
        modal.className = 'bulk-paste-modal';
        modal.id = `bulk-paste-modal-${this.formsetPrefix}`;
        modal.innerHTML = `
            <div class="bulk-paste-modal__overlay"></div>
            <div class="bulk-paste-modal__content">
                <div class="bulk-paste-modal__header">
                    <h3>لصق البيانات الجماعية</h3>
                    <button type="button" class="bulk-paste-modal__close" aria-label="إغلاق">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>

                <div class="bulk-paste-modal__body">
                    <!-- خطوة 1: إدخال البيانات -->
                    <div class="bulk-paste-step bulk-paste-step--active" data-step="input">
                        <div class="bulk-paste-step__content">
                            <p class="bulk-paste-instructions">
                                الصق البيانات من جدول (Excel, Google Sheets, إلخ). يجب أن تكون البيانات مفصولة بـ Tab أو فواصل.
                            </p>
                            <textarea 
                                class="bulk-paste-textarea" 
                                placeholder="الصق البيانات هنا...&#10;مثال:&#10;البرنامج 1	4 سنوات	25,000&#10;البرنامج 2	3 سنوات	20,000"
                                dir="rtl"
                            ></textarea>
                            <div class="bulk-paste-info">
                                <p>💡 <strong>نصيحة:</strong> انسخ الجدول من Excel أو Google Sheets والصقه مباشرة هنا</p>
                            </div>
                        </div>
                    </div>

                    <!-- خطوة 2: المعاينة والتحقق -->
                    <div class="bulk-paste-step" data-step="preview">
                        <div class="bulk-paste-step__content">
                            <div class="bulk-paste-preview">
                                <div class="bulk-paste-preview__stats">
                                    <div class="bulk-paste-stat">
                                        <span class="bulk-paste-stat__label">عدد الصفوف:</span>
                                        <span class="bulk-paste-stat__value" data-rows="0">0</span>
                                    </div>
                                    <div class="bulk-paste-stat">
                                        <span class="bulk-paste-stat__label">عدد الأعمدة:</span>
                                        <span class="bulk-paste-stat__value" data-columns="0">0</span>
                                    </div>
                                </div>

                                <div class="bulk-paste-preview__table-wrapper">
                                    <table class="bulk-paste-preview__table">
                                        <thead>
                                            <tr>
                                                ${this.fields.map(field => `
                                                    <th>${this.fieldLabels[field] || field}</th>
                                                `).join('')}
                                            </tr>
                                        </thead>
                                        <tbody class="bulk-paste-preview__tbody">
                                            <!-- سيتم ملؤها ديناميكياً -->
                                        </tbody>
                                    </table>
                                </div>

                                <div class="bulk-paste-warnings" style="display: none;">
                                    <!-- سيتم عرض التحذيرات هنا -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="bulk-paste-modal__footer">
                    <button type="button" class="bulk-paste-btn-cancel">إلغاء</button>
                    <button type="button" class="bulk-paste-btn-next" data-step="input">التالي</button>
                    <button type="button" class="bulk-paste-btn-confirm" style="display: none;">تأكيد اللصق</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.modal = modal;
        this.setupModalEvents();
    }

    setupModalEvents() {
        const overlay = this.modal.querySelector('.bulk-paste-modal__overlay');
        const closeBtn = this.modal.querySelector('.bulk-paste-modal__close');
        const cancelBtn = this.modal.querySelector('.bulk-paste-btn-cancel');
        const nextBtn = this.modal.querySelector('.bulk-paste-btn-next');
        const confirmBtn = this.modal.querySelector('.bulk-paste-btn-confirm');
        const textarea = this.modal.querySelector('.bulk-paste-textarea');

        // إغلاق الـ modal
        const closeModal = () => this.closeModal();
        overlay.addEventListener('click', closeModal);
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);

        // الانتقال للخطوة التالية
        nextBtn.addEventListener('click', () => this.goToPreview());

        // تأكيد اللصق
        confirmBtn.addEventListener('click', () => this.confirmPaste());

        // تحديث المعاينة عند الكتابة
        textarea.addEventListener('input', () => this.updatePreview());
    }

    handleBulkPaste() {
        this.modal.classList.add('bulk-paste-modal--active');
        this.modal.querySelector('.bulk-paste-textarea').focus();
    }

    closeModal() {
        this.modal.classList.remove('bulk-paste-modal--active');
        this.resetModal();
    }

    resetModal() {
        this.modal.querySelector('.bulk-paste-textarea').value = '';
        this.showStep('input');
        this.modal.querySelector('.bulk-paste-btn-next').style.display = 'block';
        this.modal.querySelector('.bulk-paste-btn-confirm').style.display = 'none';
    }

    showStep(stepName) {
        this.modal.querySelectorAll('.bulk-paste-step').forEach(step => {
            step.classList.remove('bulk-paste-step--active');
        });
        this.modal.querySelector(`[data-step="${stepName}"]`).classList.add('bulk-paste-step--active');
    }

    parseData(text) {
        // تنظيف النص
        text = text.trim();
        if (!text) return { rows: [], errors: ['لا توجد بيانات للصق'] };

        // تقسيم الصفوف
        const lines = text.split('\n').filter(line => line.trim());
        const rows = [];
        const errors = [];

        lines.forEach((line, lineIndex) => {
            // محاولة الكشف عن الفاصل (Tab أو Comma)
            let delimiter = '\t';
            if (!line.includes('\t') && line.includes(',')) {
                delimiter = ',';
            }

            const cells = line.split(delimiter).map(cell => cell.trim());

            // التحقق من عدد الأعمدة
            if (cells.length !== this.fields.length) {
                errors.push(
                    `الصف ${lineIndex + 1}: عدد الأعمدة غير متطابق (متوقع: ${this.fields.length}, فعلي: ${cells.length})`
                );
                return;
            }

            // إنشاء كائن الصف
            const row = {};
            this.fields.forEach((field, fieldIndex) => {
                row[field] = cells[fieldIndex];
            });

            rows.push(row);
        });

        return { rows, errors };
    }

    updatePreview() {
        const textarea = this.modal.querySelector('.bulk-paste-textarea');
        const { rows, errors } = this.parseData(textarea.value);

        // تحديث الإحصائيات
        this.modal.querySelector('[data-rows]').textContent = rows.length;
        this.modal.querySelector('[data-columns]').textContent = this.fields.length;

        // تحديث جدول المعاينة
        const tbody = this.modal.querySelector('.bulk-paste-preview__tbody');
        tbody.innerHTML = rows.map((row, index) => `
            <tr class="bulk-paste-preview__row">
                ${this.fields.map(field => `
                    <td class="bulk-paste-preview__cell">${this.escapeHtml(row[field])}</td>
                `).join('')}
            </tr>
        `).join('');

        // عرض/إخفاء التحذيرات
        const warningsDiv = this.modal.querySelector('.bulk-paste-warnings');
        if (errors.length > 0) {
            warningsDiv.innerHTML = `
                <div class="bulk-paste-warning">
                    <div class="bulk-paste-warning__title">⚠️ تحذيرات:</div>
                    <ul class="bulk-paste-warning__list">
                        ${errors.map(error => `<li>${error}</li>`).join('')}
                    </ul>
                </div>
            `;
            warningsDiv.style.display = 'block';
        } else {
            warningsDiv.style.display = 'none';
        }

        // تفعيل/تعطيل زر التالي
        const nextBtn = this.modal.querySelector('.bulk-paste-btn-next');
        nextBtn.disabled = rows.length === 0 || errors.length > 0;
    }

    goToPreview() {
        this.updatePreview();
        this.showStep('preview');
        this.modal.querySelector('.bulk-paste-btn-next').style.display = 'none';
        this.modal.querySelector('.bulk-paste-btn-confirm').style.display = 'block';
    }

    confirmPaste() {
        const textarea = this.modal.querySelector('.bulk-paste-textarea');
        const { rows } = this.parseData(textarea.value);

        if (rows.length === 0) {
            alert('لا توجد بيانات صحيحة للصق');
            return;
        }

        // إضافة الصفوف الجديدة
        rows.forEach(row => {
            this.addRowToFormset(row);
        });

        // إغلاق الـ modal
        this.closeModal();

        // عرض رسالة نجاح
        this.showSuccessMessage(`تم إضافة ${rows.length} صف بنجاح`);
    }

    addRowToFormset(rowData) {
        // إزالة empty row إذا موجودة
        const emptyRow = this.container.querySelector('.fpm-empty-row');
        if (emptyRow) emptyRow.remove();
        
        // الحصول على عدد الصفوف الحالية (بدون empty row)
        const existingRows = this.container.querySelectorAll('.fpm-program-row').length;
        const newIndex = existingRows;

        // إنشاء صف جديد
        const newRow = document.createElement('tr');
        newRow.className = 'fpm-program-row';
        newRow.dataset.programIndex = newIndex;

        // إنشاء الحقول
        let fieldsHtml = '';
        this.fields.forEach(field => {
            const inputName = `${this.formsetPrefix}-${newIndex}-${field}`;
            const value = rowData[field] || '';

            if (field === 'name') {
                fieldsHtml += `
                    <td>
                        <textarea 
                            name="${inputName}" 
                            class="fpm-program-input fpm-program-input--textarea"
                            dir="rtl"
                            rows="1"
                            required
                        >${this.escapeHtml(value)}</textarea>
                    </td>
                `;
            } else {
                fieldsHtml += `
                    <td>
                        <input 
                            type="text" 
                            name="${inputName}" 
                            value="${this.escapeHtml(value)}"
                            class="fpm-program-input fpm-program-input--short"
                            dir="rtl"
                            required
                        >
                    </td>
                `;
            }
        });

        // إضافة حقول النموذج المخفية
        fieldsHtml += `
            <td class="fpm-program-actions">
                <button type="button" class="fpm-delete-program-btn" data-delete-program title="حذف البرنامج" style="display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; border: none; border-radius: 4px; background: transparent; color: var(--text-muted); cursor: pointer; transition: all 0.15s ease; padding: 0;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14"/>
                        <line x1="10" y1="11" x2="10" y2="17"/>
                        <line x1="14" y1="11" x2="14" y2="17"/>
                    </svg>
                </button>
                <input type="hidden" name="${this.formsetPrefix}-${newIndex}-sort_order" value="${newIndex}">
                <input type="hidden" name="${this.formsetPrefix}-${newIndex}-id" value="">
                <input type="hidden" name="${this.formsetPrefix}-${newIndex}-DELETE" value="">
            </td>
        `;

        newRow.innerHTML = fieldsHtml;

        // إضافة الصف للـ container (tbody)
        this.container.appendChild(newRow);

        // إضافة event listener لزر الحذف
        const deleteBtn = newRow.querySelector('[data-delete-program]');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.deleteRow(newRow);
            });
        }

        // تحديث عدد الصفوف في management form
        this.updateFormsetCount();
    }

    deleteRow(row) {
        const programsContainer = row.closest('[data-programs-container]');
        row.remove();
        
        // إذا لم يتبقى برامج، أضف empty row
        const remainingPrograms = programsContainer.querySelectorAll('.fpm-program-row');
        if (remainingPrograms.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.className = 'fpm-empty-row';
            emptyRow.innerHTML = '<td colspan="4" class="fpm-empty-message">لا توجد برامج مضافة</td>';
            programsContainer.appendChild(emptyRow);
        }
        
        this.updateFormsetCount();
    }

    updateFormsetCount() {
        const rowCount = this.container.querySelectorAll('.fpm-program-row').length;
        
        // تحديث management form — البحث بالـ name attribute
        const totalFormsInput = document.querySelector(`[name="${this.formsetPrefix}-TOTAL_FORMS"]`);
        if (totalFormsInput) {
            totalFormsInput.value = rowCount;
        }
    }

    showSuccessMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'bulk-paste-success-message';
        messageDiv.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span>${message}</span>
        `;

        document.body.appendChild(messageDiv);

        // إزالة الرسالة بعد 3 ثوان
        setTimeout(() => {
            messageDiv.classList.add('bulk-paste-success-message--hide');
            setTimeout(() => messageDiv.remove(), 300);
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// تهيئة المكون عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', () => {
    // تأخير التهيئة قليلاً لضمان أن faculty-programs-manager أنشأ العناصر
    setTimeout(() => {
        initAllBulkPaste();
    }, 300);
});

/**
 * تهيئة جميع حاويات الـ bulk paste الموجودة في الصفحة
 */
function initAllBulkPaste() {
    const programContainers = document.querySelectorAll('[data-bulk-paste]');
    
    programContainers.forEach((container, index) => {
        // تخطي الحاويات التي تم تهيئتها بالفعل
        if (container.dataset.bulkPasteInitialized === 'true') {
            return;
        }
        
        // Processing container
        
        // إذا لم يكن للـ container id، أضفه
        let containerId = container.id;
        if (!containerId) {
            containerId = `bulk-paste-container-${Date.now()}-${index}`;
            container.id = containerId;
        }
        
        const config = {
            containerSelector: `#${containerId}`,
            formsetPrefix: container.dataset.bulkPaste,
            fields: (container.dataset.fields || 'name,duration,tuition_fees').split(','),
            fieldLabels: JSON.parse(container.dataset.fieldLabels || '{}')
        };
        
        new BulkPaste(config);
    });
}

/**
 * إعادة تهيئة عند إضافة كليات جديدة ديناميكياً
 * يتم استدعاؤها من faculty-programs-manager.js
 */
function reinitializeBulkPaste() {
    initAllBulkPaste();
}
