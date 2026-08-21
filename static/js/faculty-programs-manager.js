/**
 * Faculty Programs Manager
 * إدارة ديناميكية للكليات والبرامج معاً
 * 
 * Features:
 * - إضافة/حذف كليات وبرامجها
 * - إعادة ترتيب بالسحب والإفلات
 * - توسيع/طي البرامج داخل كل كلية
 * - تحديث تلقائي للترتيب والأرقام
 */

class FacultyProgramsManager {
    constructor() {
        this.container = document.getElementById('faculty-items-container');
        this.totalFormsInput = document.getElementById('id_faculties-TOTAL_FORMS');
        this.emptyState = document.getElementById('faculty-empty-state');
        this.counterEl = document.getElementById('faculty-counter');
        
        if (!this.container || !this.totalFormsInput) return;
        
        this.init();
    }

    init() {
        this.attachAddHandler();
        this.attachItemHandlers();
        this.updateState();
        this.initTextareaAutoResize();
        this.initMajorSelect2();
        this.setupSelect2Autofocus();
    }

    initTextareaAutoResize() {
        // Auto-resize on input
        this.container.addEventListener('input', (e) => {
            if (e.target.classList.contains('fpm-program-input--textarea')) {
                this.autoResizeTextarea(e.target);
            }
        });

        // Watch for dynamically added textareas (bulk paste, Elementor import, manual add)
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const textareas = node.querySelectorAll('.fpm-program-input--textarea');
                        textareas.forEach(textarea => this.autoResizeTextarea(textarea));
                        if (node.classList.contains('fpm-program-input--textarea')) {
                            this.autoResizeTextarea(node);
                        }
                    }
                });
            });
        });
        observer.observe(this.container, { childList: true, subtree: true });

        // Initial resize for all existing textareas
        setTimeout(() => {
            this.container.querySelectorAll('.fpm-program-input--textarea').forEach(textarea => {
                this.autoResizeTextarea(textarea);
            });
        }, 100);
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight + 2) + 'px';
    }

    // ─── إضافة كلية جديدة ───
    attachAddHandler() {
        const addBtn = document.getElementById('faculty-add-btn');
        if (addBtn) {
            addBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.addFaculty();
            });
        }

        // ─── استيراد كليات جماعية ───
        const bulkImportBtn = document.getElementById('faculty-bulk-import-btn');
        if (bulkImportBtn) {
            bulkImportBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.openBulkImportModal();
            });
        }
    }

    addFaculty() {
        const totalForms = parseInt(this.totalFormsInput.value);
        const newIndex = totalForms;

        const item = this.createFacultyItem(newIndex);
        this.container.appendChild(item);
        this.totalFormsInput.value = newIndex + 1;

        // أنيميشن الظهور
        requestAnimationFrame(() => {
            item.classList.add('faculty-item--visible');
        });

        this.attachItemHandlers();
        this.updateState();
        this.updateSortOrders();

        // Focus على حقل الاسم
        const nameInput = item.querySelector('input[name$="-name"]');
        if (nameInput) {
            setTimeout(() => nameInput.focus(), 150);
        }

        // إعادة تهيئة الـ bulk paste للبرامج الجديدة
        if (typeof reinitializeBulkPaste === 'function') {
            setTimeout(() => {
                reinitializeBulkPaste();
            }, 200);
        }
    }

    createFacultyItem(index) {
        const item = document.createElement('div');
        item.className = 'faculty-item';
        item.setAttribute('data-faculty-index', index);
        item.innerHTML = `
            <div class="faculty-item__drag-handle" title="اسحب لإعادة الترتيب">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="9" cy="6" r="1.5"/>
                    <circle cx="15" cy="6" r="1.5"/>
                    <circle cx="9" cy="12" r="1.5"/>
                    <circle cx="15" cy="12" r="1.5"/>
                    <circle cx="9" cy="18" r="1.5"/>
                    <circle cx="15" cy="18" r="1.5"/>
                </svg>
            </div>
            <div class="faculty-item__content">
                <div class="faculty-item__number">${index + 1}</div>
                <input type="text"
                       name="faculties-${index}-name"
                       id="id_faculties-${index}-name"
                       class="faculty-item__input"
                       placeholder="اسم الكلية"
                       dir="rtl"
                       required>
                <input type="hidden"
                       name="faculties-${index}-sort_order"
                       id="id_faculties-${index}-sort_order"
                       value="${index}">
                <input type="hidden"
                       name="faculties-${index}-id"
                       id="id_faculties-${index}-id"
                       value="">
            </div>
            <button type="button" class="faculty-item__toggle" title="عرض/إخفاء البرامج" data-toggle-programs>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </button>
            <button type="button" class="faculty-item__delete" title="حذف الكلية">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14"/>
                    <line x1="10" y1="11" x2="10" y2="17"/>
                    <line x1="14" y1="11" x2="14" y2="17"/>
                </svg>
            </button>
            <input type="hidden"
                   name="faculties-${index}-DELETE"
                   id="id_faculties-${index}-DELETE"
                   value="">
            
            <!-- Programs Container -->
            <div class="faculty-item__programs-wrapper" style="display: none;">
                <input type="hidden" name="faculty-${index}-programs-TOTAL_FORMS" value="0">
                <input type="hidden" name="faculty-${index}-programs-INITIAL_FORMS" value="0">
                <input type="hidden" name="faculty-${index}-programs-MIN_NUM_FORMS" value="0">
                <input type="hidden" name="faculty-${index}-programs-MAX_NUM_FORMS" value="50">
                
                <table class="fpm-programs-table">
                    <thead>
                        <tr>
                            <th>التخصصات</th>
                            <th>المدة الدراسية</th>
                            <th>الرسوم السنوية</th>
                            <th>الرسوم بالسنوات (اختياري)</th>
                            <th width="40"></th>
                        </tr>
                    </thead>
                    <tbody class="fpm-programs-tbody" 
                           data-programs-container
                           data-bulk-paste="faculty-${index}-programs"
                           data-fields="name,duration,tuition_fees,yearly_fees"
                           data-field-labels='{"name": "البرنامج", "duration": "المدة الدراسية", "tuition_fees": "الرسوم السنوية", "yearly_fees": "الرسوم التفصيلية بالسنوات"}'
                           id="programs-container-${index}">
                        <tr class="fpm-empty-row">
                            <td colspan="5" class="fpm-empty-message">لا توجد برامج مضافة</td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="fpm-add-program-wrapper">
                    <button type="button" class="fpm-add-program-btn" data-add-program style="display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border: none; border-radius: 6px; background: var(--primary); color: #ffffff; font-size: 13px; cursor: pointer; transition: all 0.2s ease; font-family: inherit; font-weight: 600;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19"/>
                            <line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                        إضافة برنامج
                    </button>
                </div>
            </div>
        `;
        return item;
    }

    // ─── حذف كلية ───
    deleteFaculty(item) {
        const deleteInput = item.querySelector('input[name$="-DELETE"]');
        const idInput = item.querySelector('input[name$="-id"]');

        if (idInput && idInput.value) {
            // كلية موجودة في الداتابيز
            deleteInput.value = 'on';
            item.classList.add('faculty-item--deleted');
            setTimeout(() => {
                item.style.display = 'none';
                this.updateState();
                this.updateNumbers();
            }, 300);
        } else {
            // كلية جديدة
            item.classList.add('faculty-item--deleted');
            setTimeout(() => {
                item.remove();
                this.reindexForms();
                this.updateState();
            }, 300);
        }
    }

    // ─── توسيع/طي البرامج ───
    togglePrograms(facultyItem) {
        const wrapper = facultyItem.querySelector('.faculty-item__programs-wrapper');
        const toggleBtn = facultyItem.querySelector('[data-toggle-programs]');
        const icon = toggleBtn.querySelector('svg');
        
        const isExpanded = wrapper.style.display !== 'none';
        
        if (isExpanded) {
            wrapper.style.display = 'none';
            icon.classList.remove('rotated');
        } else {
            wrapper.style.display = 'block';
            icon.classList.add('rotated');
            
            // Resize textareas inside this wrapper now that they are visible
            wrapper.querySelectorAll('.fpm-program-input--textarea').forEach(textarea => {
                this.autoResizeTextarea(textarea);
            });
            
            // تهيئة Select2 للبرامج داخل الكلية بعد فتحها
            this.initMajorSelect2(wrapper);
        }
    }

    // ─── إضافة برنامج ───
    addProgram(facultyItem) {
        const facultyIndex = facultyItem.getAttribute('data-faculty-index');
        const programsContainer = facultyItem.querySelector('[data-programs-container]');
        const totalFormsInput = facultyItem.querySelector(`[name="faculty-${facultyIndex}-programs-TOTAL_FORMS"]`);
        const programIndex = parseInt(totalFormsInput.value);
        
        // إزالة empty row
        const emptyRow = programsContainer.querySelector('.fpm-empty-row');
        if (emptyRow) emptyRow.remove();
        
        // جلب قالب اختيار التخصص وتخصيصه للسطر الجديد
        const majorSelectContainer = document.getElementById('major-select-template-container');
        let majorSelectHTML = '';
        if (majorSelectContainer) {
            const selectEl = majorSelectContainer.querySelector('select').cloneNode(true);
            selectEl.name = `faculty-${facultyIndex}-programs-${programIndex}-major`;
            selectEl.id = `id_faculty-${facultyIndex}-programs-${programIndex}-major`;
            majorSelectHTML = selectEl.outerHTML;
        } else {
            majorSelectHTML = `<select name="faculty-${facultyIndex}-programs-${programIndex}-major" class="fpm-program-input fpm-program-input--select" dir="rtl"><option value="">---------</option></select>`;
        }
        
        // إنشاء صف جديد
        const row = document.createElement('tr');
        row.className = 'fpm-program-row';
        row.setAttribute('data-program-index', programIndex);
        row.innerHTML = `
            <td>
                <textarea name="faculty-${facultyIndex}-programs-${programIndex}-name"
                          class="fpm-program-input fpm-program-input--textarea"
                          placeholder="اسم البرنامج"
                          dir="rtl"
                          rows="1"
                          required></textarea>
                <div class="mt-2 text-xs text-gray-500" style="margin-top: 6px;">
                    <span style="color: var(--text-muted); display: block; margin-bottom: 2px;">التخصص المرتبط:</span>
                    ${majorSelectHTML}
                </div>
            </td>
            <td>
                <input type="text" 
                       name="faculty-${facultyIndex}-programs-${programIndex}-duration"
                       class="fpm-program-input fpm-program-input--short"
                       placeholder="4 سنوات"
                       dir="rtl"
                       required>
            </td>
            <td>
                <input type="text" 
                       name="faculty-${facultyIndex}-programs-${programIndex}-tuition_fees"
                       class="fpm-program-input fpm-program-input--short"
                       placeholder="25,000 دولار"
                       dir="rtl"
                       required>
            </td>
            <td>
                <textarea name="faculty-${facultyIndex}-programs-${programIndex}-yearly_fees"
                          class="fpm-program-input fpm-program-input--textarea"
                          placeholder="السنة الاولى: 5,424\nالسنة الثانية: 4,964"
                          dir="rtl"
                          rows="2"></textarea>
            </td>
            <td class="fpm-program-actions">
                <button type="button" class="fpm-delete-program-btn" data-delete-program title="حذف البرنامج">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14"/>
                        <line x1="10" y1="11" x2="10" y2="17"/>
                        <line x1="14" y1="11" x2="14" y2="17"/>
                    </svg>
                </button>
                <input type="hidden" name="faculty-${facultyIndex}-programs-${programIndex}-sort_order" value="${programIndex}">
                <input type="hidden" name="faculty-${facultyIndex}-programs-${programIndex}-id" value="">
                <input type="hidden" name="faculty-${facultyIndex}-programs-${programIndex}-DELETE" value="">
            </td>
        `;
        
        programsContainer.appendChild(row);
        totalFormsInput.value = programIndex + 1;
        
        // تهيئة Select2 للتخصص المرتبط بالسطر الجديد
        this.initMajorSelect2(row);

        // Focus على حقل الاسم
        const nameInput = row.querySelector('[name$="-name"]');
        setTimeout(() => nameInput.focus(), 100);
        
        // ربط حدث الحذف
        this.attachProgramDeleteHandler(row);
    }

    // ─── حذف برنامج ───
    deleteProgram(programRow) {
        const deleteInput = programRow.querySelector('[name$="-DELETE"]');
        const idInput = programRow.querySelector('[name$="-id"]');
        
        if (idInput && idInput.value) {
            // برنامج موجود
            deleteInput.value = 'on';
            if (deleteInput.type === 'checkbox') {
                deleteInput.checked = true;
            }
            programRow.classList.add('fpm-program-row--deleted');
            programRow.style.opacity = '0.3';
            programRow.style.pointerEvents = 'none';
        } else {
            // برنامج جديد
            const programsContainer = programRow.closest('[data-programs-container]');
            programRow.remove();
            
            // إذا لم يتبقى برامج، أضف empty row
            const remainingPrograms = programsContainer.querySelectorAll('.fpm-program-row:not(.fpm-program-row--deleted)');
            if (remainingPrograms.length === 0) {
                const emptyRow = document.createElement('tr');
                emptyRow.className = 'fpm-empty-row';
                emptyRow.innerHTML = '<td colspan="5" class="fpm-empty-message">لا توجد برامج مضافة</td>';
                programsContainer.appendChild(emptyRow);
            }
        }
    }

    // ─── إعادة ترقيم الفورمات ───
    reindexForms() {
        const allItems = this.container.querySelectorAll('.faculty-item');
        
        allItems.forEach((item, idx) => {
            item.setAttribute('data-faculty-index', idx);
            const inputs = item.querySelectorAll('input');
            inputs.forEach(input => {
                const name = input.getAttribute('name');
                if (name) {
                    input.setAttribute('name', name.replace(/faculties-\d+-/, `faculties-${idx}-`));
                }
                const id = input.getAttribute('id');
                if (id) {
                    input.setAttribute('id', id.replace(/id_faculties-\d+-/, `id_faculties-${idx}-`));
                }
            });
        });

        this.totalFormsInput.value = allItems.length;
        this.updateNumbers();
    }

    // ─── تحديث الأرقام ───
    updateNumbers() {
        const visibleItems = this.container.querySelectorAll('.faculty-item:not(.faculty-item--deleted):not([style*="display: none"])');
        visibleItems.forEach((item, idx) => {
            const numberEl = item.querySelector('.faculty-item__number');
            if (numberEl) numberEl.textContent = idx + 1;
        });
    }

    // ─── تحديث ترتيب العرض ───
    updateSortOrders() {
        const visibleItems = this.container.querySelectorAll('.faculty-item:not(.faculty-item--deleted):not([style*="display: none"])');
        visibleItems.forEach((item, idx) => {
            const sortInput = item.querySelector('input[name$="-sort_order"]');
            if (sortInput) sortInput.value = idx;
            const numberEl = item.querySelector('.faculty-item__number');
            if (numberEl) numberEl.textContent = idx + 1;
        });
    }

    // ─── تحديث الحالة ───
    updateState() {
        const visibleItems = this.container.querySelectorAll('.faculty-item:not(.faculty-item--deleted):not([style*="display: none"])');
        const count = visibleItems.length;

        if (this.emptyState) {
            this.emptyState.style.display = count === 0 ? 'flex' : 'none';
        }
        if (this.counterEl) {
            this.counterEl.textContent = count;
            this.counterEl.style.display = count > 0 ? 'inline-flex' : 'none';
        }
    }

    // ─── ربط أحداث العناصر ───
    attachItemHandlers() {
        // أزرار الحذف
        this.container.querySelectorAll('.faculty-item__delete').forEach(btn => {
            btn.onclick = (e) => {
                e.preventDefault();
                const item = btn.closest('.faculty-item');
                this.deleteFaculty(item);
            };
        });

        // أزرار التوسيع/الطي
        this.container.querySelectorAll('[data-toggle-programs]').forEach(btn => {
            btn.onclick = (e) => {
                e.preventDefault();
                const item = btn.closest('.faculty-item');
                this.togglePrograms(item);
            };
        });

        // أزرار إضافة البرامج
        this.container.querySelectorAll('[data-add-program]').forEach(btn => {
            btn.onclick = (e) => {
                e.preventDefault();
                const facultyItem = btn.closest('.faculty-item');
                this.addProgram(facultyItem);
            };
        });

        // أزرار حذف البرامج
        this.container.querySelectorAll('[data-delete-program]').forEach(btn => {
            this.attachProgramDeleteHandler(btn.closest('.fpm-program-row'));
        });

        // السحب والإفلات للكليات والنقر على السطر بالكامل ما عدا الاسم والاجراءات
        this.container.querySelectorAll('.faculty-item').forEach(item => {
            const handle = item.querySelector('.faculty-item__drag-handle');
            if (handle) {
                item.setAttribute('draggable', 'false');
                handle.addEventListener('mousedown', () => {
                    item.setAttribute('draggable', 'true');
                });
                const disableDrag = () => {
                    item.setAttribute('draggable', 'false');
                };
                handle.addEventListener('mouseup', disableDrag);
                handle.addEventListener('mouseleave', disableDrag);
                item.addEventListener('dragend', disableDrag);
            } else {
                item.setAttribute('draggable', 'true');
            }
            item.ondragstart = (e) => this.onDragStart(e, item);
            item.ondragend = (e) => this.onDragEnd(e, item);
            item.ondragover = (e) => this.onDragOver(e, item);
            item.ondrop = (e) => this.onDrop(e, item);

            item.onclick = (e) => {
                if (
                    e.target.closest('.faculty-item__input') ||
                    e.target.closest('.faculty-item__delete') ||
                    e.target.closest('.faculty-item__toggle') ||
                    e.target.closest('.faculty-item__drag-handle') ||
                    e.target.closest('.faculty-item__programs-wrapper')
                ) {
                    return;
                }
                e.preventDefault();
                this.togglePrograms(item);
            };
        });
    }

    attachProgramDeleteHandler(programRow) {
        const deleteBtn = programRow.querySelector('[data-delete-program]');
        if (deleteBtn) {
            deleteBtn.onclick = (e) => {
                e.preventDefault();
                this.deleteProgram(programRow);
            };
        }
    }

    // ─── Drag & Drop ───
    onDragStart(e, item) {
        item.classList.add('faculty-item--dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', '');
    }

    onDragEnd(e, item) {
        item.classList.remove('faculty-item--dragging');
        this.container.querySelectorAll('.faculty-item--drag-over').forEach(el => {
            el.classList.remove('faculty-item--drag-over');
        });
        this.updateSortOrders();
        this.reindexForms();
    }

    onDragOver(e, item) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';

        this.container.querySelectorAll('.faculty-item--drag-over').forEach(el => {
            el.classList.remove('faculty-item--drag-over');
        });

        if (!item.classList.contains('faculty-item--dragging')) {
            item.classList.add('faculty-item--drag-over');
        }
    }

    onDrop(e, item) {
        e.preventDefault();
        item.classList.remove('faculty-item--drag-over');

        const draggedItem = this.container.querySelector('.faculty-item--dragging');
        if (draggedItem && draggedItem !== item) {
            const allItems = [...this.container.querySelectorAll('.faculty-item:not([style*="display: none"])')];
            const draggedIdx = allItems.indexOf(draggedItem);
            const targetIdx = allItems.indexOf(item);

            if (draggedIdx < targetIdx) {
                item.after(draggedItem);
            } else {
                item.before(draggedItem);
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // استيراد كليات جماعية من كود Elementor Accordion
    // ═══════════════════════════════════════════════════════════════════════════════

    openBulkImportModal() {
        if (!this.bulkImportModal) {
            this.createBulkImportModal();
        }
        this.bulkImportModal.classList.add('bulk-import-modal--active');
        this.bulkImportModal.querySelector('.bulk-import-textarea').focus();
    }

    createBulkImportModal() {
        const modal = document.createElement('div');
        modal.className = 'bulk-import-modal';
        modal.id = 'faculty-bulk-import-modal';
        modal.innerHTML = `
            <div class="bulk-import-modal__overlay"></div>
            <div class="bulk-import-modal__content">
                <div class="bulk-import-modal__header">
                    <h3>استيراد كليات من Elementor</h3>
                    <button type="button" class="bulk-import-modal__close" aria-label="إغلاق">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>

                <div class="bulk-import-modal__body">
                    <!-- خطوة 1: إدخال الكود -->
                    <div class="bulk-import-step bulk-import-step--active" data-step="input">
                        <div class="bulk-import-step__content">
                            <p class="bulk-import-instructions">
                                الصق كود HTML من Elementor Accordion (انسخ الكود من المنتور مباشرة)
                            </p>
                            <textarea 
                                class="bulk-import-textarea" 
                                placeholder="الصق كود Elementor Accordion هنا..."
                                dir="rtl"
                                spellcheck="false"
                            ></textarea>
                            <div class="bulk-import-info">
                                <p>💡 <strong>كيفية الاستخدام:</strong></p>
                                <ul>
                                    <li>افتح صفحة المنتور التي تحتوي على Accordion</li>
                                    <li>افتح أدوات المتصفح (F12)</li>
                                    <li>انسخ كود الـ Accordion كاملاً</li>
                                    <li>الصقه هنا واضغط "التالي"</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <!-- خطوة 2: المعاينة والتحقق -->
                    <div class="bulk-import-step" data-step="preview">
                        <div class="bulk-import-step__content">
                            <div class="bulk-import-preview">
                                <div class="bulk-import-preview__stats">
                                    <div class="bulk-import-stat">
                                        <span class="bulk-import-stat__label">عدد الكليات:</span>
                                        <span class="bulk-import-stat__value" data-faculties="0">0</span>
                                    </div>
                                    <div class="bulk-import-stat">
                                        <span class="bulk-import-stat__label">إجمالي البرامج:</span>
                                        <span class="bulk-import-stat__value" data-programs="0">0</span>
                                    </div>
                                </div>

                                <div class="bulk-import-preview__list">
                                    <div class="bulk-import-preview__title">الكليات المكتشفة:</div>
                                    <ul class="bulk-import-preview__items">
                                        <!-- سيتم ملؤها ديناميكياً -->
                                    </ul>
                                </div>

                                <div class="bulk-import-warnings" style="display: none;">
                                    <!-- سيتم عرض التحذيرات هنا -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="bulk-import-modal__footer">
                    <button type="button" class="bulk-import-btn-cancel">إلغاء</button>
                    <button type="button" class="bulk-import-btn-next" data-step="input">التالي</button>
                    <button type="button" class="bulk-import-btn-confirm" style="display: none;">تأكيد الاستيراد</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.bulkImportModal = modal;
        this.setupBulkImportEvents();
    }

    setupBulkImportEvents() {
        const overlay = this.bulkImportModal.querySelector('.bulk-import-modal__overlay');
        const closeBtn = this.bulkImportModal.querySelector('.bulk-import-modal__close');
        const cancelBtn = this.bulkImportModal.querySelector('.bulk-import-btn-cancel');
        const nextBtn = this.bulkImportModal.querySelector('.bulk-import-btn-next');
        const confirmBtn = this.bulkImportModal.querySelector('.bulk-import-btn-confirm');
        const textarea = this.bulkImportModal.querySelector('.bulk-import-textarea');

        // إغلاق الـ modal
        const closeModal = () => this.closeBulkImportModal();
        overlay.addEventListener('click', closeModal);
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);

        // الانتقال للخطوة التالية
        nextBtn.addEventListener('click', () => this.goToBulkImportPreview());

        // تأكيد الاستيراد
        confirmBtn.addEventListener('click', () => this.confirmBulkImport());

        // تحديث المعاينة عند الكتابة
        textarea.addEventListener('input', () => this.updateBulkImportPreview());
    }

    closeBulkImportModal() {
        this.bulkImportModal.classList.remove('bulk-import-modal--active');
        this.resetBulkImportModal();
    }

    resetBulkImportModal() {
        this.bulkImportModal.querySelector('.bulk-import-textarea').value = '';
        this.showBulkImportStep('input');
        this.bulkImportModal.querySelector('.bulk-import-btn-next').style.display = 'block';
        this.bulkImportModal.querySelector('.bulk-import-btn-confirm').style.display = 'none';
    }

    showBulkImportStep(stepName) {
        this.bulkImportModal.querySelectorAll('.bulk-import-step').forEach(step => {
            step.classList.remove('bulk-import-step--active');
        });
        this.bulkImportModal.querySelector(`[data-step="${stepName}"]`).classList.add('bulk-import-step--active');
    }

    parseElementorAccordion(htmlString) {
        try {
            // تنظيف الـ HTML من الوسوم الخارجية
            const cleanHtml = htmlString.trim();
            
            // إنشاء parser آمن
            const parser = new DOMParser();
            const doc = parser.parseFromString(cleanHtml, 'text/html');

            // البحث عن .elementor-accordion (بغض النظر عن العمق)
            const accordion = doc.querySelector('.elementor-accordion');
            if (!accordion) {
                return { faculties: [], errors: ['لم يتم العثور على Elementor Accordion في الكود'] };
            }

            const faculties = [];
            const errors = [];

            // لكل accordion item
            accordion.querySelectorAll('.elementor-accordion-item').forEach((item, itemIndex) => {
                try {
                    // استخراج اسم الكلية
                    const titleEl = item.querySelector('.elementor-accordion-title');
                    const facultyName = titleEl ? titleEl.textContent.trim() : `كلية بدون اسم ${itemIndex + 1}`;

                    if (!facultyName) {
                        errors.push(`الكلية ${itemIndex + 1}: لم يتم العثور على اسم`);
                        return;
                    }

                    // البحث عن الجدول
                    const table = item.querySelector('table');
                    const programs = [];

                    if (table) {
                        const tbody = table.querySelector('tbody');
                        if (tbody) {
                            const rows = tbody.querySelectorAll('tr');

                            rows.forEach((row, rowIndex) => {
                                // تخطي أي صف يحتوي على <th> (صفوف الـ header)
                                if (row.querySelector('th')) {
                                    return;
                                }

                                const cells = Array.from(row.querySelectorAll('td')).map(cell => cell.textContent.trim().replace(/\s+/g, ' '));
                                if (cells.length === 0) return;

                                if (cells.length >= 3) {
                                    const name = cells[0];
                                    const duration = cells[1];
                                    const tuitionFees = cells[2];

                                    // تخطي الصفوف الفارغة أو التي تحتوي على &nbsp; فقط
                                    if (!name || !duration || !tuitionFees || name === '\u00A0' || duration === '\u00A0' || tuitionFees === '\u00A0') {
                                        return;
                                    }

                                    const newProgram = {
                                        name,
                                        duration,
                                        tuition_fees: tuitionFees,
                                        yearly_fees: ''
                                    };

                                    if (tuitionFees.includes(':') || tuitionFees.includes('السنة') || tuitionFees.includes('year')) {
                                        newProgram.yearly_fees = tuitionFees;
                                    }

                                    programs.push(newProgram);
                                } else if (programs.length > 0) {
                                    // This is a sub-fee/rowspan row
                                    const prevProgram = programs[programs.length - 1];
                                    const feeVal = cells[cells.length - 1];

                                    if (feeVal && feeVal !== '\u00A0') {
                                        if (!prevProgram.yearly_fees) {
                                            if (prevProgram.tuition_fees && (prevProgram.tuition_fees.includes(':') || prevProgram.tuition_fees.includes('السنة') || prevProgram.tuition_fees.includes('year'))) {
                                                prevProgram.yearly_fees = prevProgram.tuition_fees;
                                            } else {
                                                prevProgram.yearly_fees = '';
                                            }
                                        }
                                        prevProgram.yearly_fees = prevProgram.yearly_fees 
                                            ? prevProgram.yearly_fees + '\n' + feeVal 
                                            : feeVal;
                                    }
                                } else {
                                    errors.push(`${facultyName} - الصف ${rowIndex + 1}: عدد الأعمدة غير كافي`);
                                }
                            });
                        }
                    }

                    faculties.push({
                        name: facultyName,
                        programs
                    });
                } catch (e) {
                    errors.push(`خطأ في معالجة الكلية ${itemIndex + 1}: ${e.message}`);
                }
            });

            if (faculties.length === 0) {
                return { faculties: [], errors: ['لم يتم العثور على أي كليات في الكود'] };
            }

            return { faculties, errors };
        } catch (e) {
            return { faculties: [], errors: [`خطأ في تحليل الكود: ${e.message}`] };
        }
    }

    updateBulkImportPreview() {
        const textarea = this.bulkImportModal.querySelector('.bulk-import-textarea');
        const { faculties, errors } = this.parseElementorAccordion(textarea.value);

        // تخزين البيانات للاستخدام لاحقاً
        this.bulkImportData = { faculties, errors };

        // تحديث الإحصائيات
        const totalPrograms = faculties.reduce((sum, f) => sum + f.programs.length, 0);
        this.bulkImportModal.querySelector('[data-faculties]').textContent = faculties.length;
        this.bulkImportModal.querySelector('[data-programs]').textContent = totalPrograms;

        // تحديث قائمة الكليات
        const itemsList = this.bulkImportModal.querySelector('.bulk-import-preview__items');
        itemsList.innerHTML = faculties.map(faculty => `
            <li class="bulk-import-preview__item">
                <span class="bulk-import-preview__item-name">${this.escapeHtml(faculty.name)}</span>
                <span class="bulk-import-preview__item-count">${faculty.programs.length} برنامج</span>
            </li>
        `).join('');

        // عرض/إخفاء التحذيرات
        const warningsDiv = this.bulkImportModal.querySelector('.bulk-import-warnings');
        if (errors.length > 0) {
            warningsDiv.innerHTML = `
                <div class="bulk-import-warning">
                    <div class="bulk-import-warning__title">⚠️ تحذيرات:</div>
                    <ul class="bulk-import-warning__list">
                        ${errors.map(error => `<li>${error}</li>`).join('')}
                    </ul>
                </div>
            `;
            warningsDiv.style.display = 'block';
        } else {
            warningsDiv.style.display = 'none';
        }

        // تفعيل/تعطيل زر التالي
        const nextBtn = this.bulkImportModal.querySelector('.bulk-import-btn-next');
        nextBtn.disabled = faculties.length === 0 || errors.length > 0;
    }

    goToBulkImportPreview() {
        this.updateBulkImportPreview();
        this.showBulkImportStep('preview');
        this.bulkImportModal.querySelector('.bulk-import-btn-next').style.display = 'none';
        this.bulkImportModal.querySelector('.bulk-import-btn-confirm').style.display = 'block';
    }

    confirmBulkImport() {
        if (!this.bulkImportData || this.bulkImportData.faculties.length === 0) {
            alert('لا توجد بيانات صحيحة للاستيراد');
            return;
        }

        // استيراد الكليات والبرامج
        this.bulkImportData.faculties.forEach(faculty => {
            this.importFaculty(faculty);
        });

        // إغلاق جميع الكليات المستوردة
        this.closeAllFaculties();

        // إغلاق الـ modal
        this.closeBulkImportModal();

        // عرض رسالة نجاح
        this.showBulkImportSuccess(`تم استيراد ${this.bulkImportData.faculties.length} كلية بنجاح`);
    }

    importFaculty(faculty) {
        // إضافة الكلية
        this.addFaculty();

        // الحصول على آخر faculty-item مُضاف
        const allItems = this.container.querySelectorAll('.faculty-item');
        const newFacultyItem = allItems[allItems.length - 1];

        // ملء اسم الكلية
        const nameInput = newFacultyItem.querySelector('input[name$="-name"]');
        if (nameInput) {
            nameInput.value = faculty.name;
        }

        // فتح programs-wrapper مؤقتاً لإضافة البرامج
        const wrapper = newFacultyItem.querySelector('.faculty-item__programs-wrapper');
        if (wrapper) {
            wrapper.style.display = 'block';
        }

        // إضافة البرامج
        faculty.programs.forEach(program => {
            this.addProgram(newFacultyItem);

            // الحصول على آخر صف مُضاف
            const programsContainer = newFacultyItem.querySelector('[data-programs-container]');
            const allRows = programsContainer.querySelectorAll('.fpm-program-row');
            const newRow = allRows[allRows.length - 1];

            // ملء بيانات البرنامج - استخدام textarea للـ name بدلاً من input
            const nameField = newRow.querySelector('textarea[name$="-name"], input[name$="-name"]');
            const durationInput = newRow.querySelector('input[name$="-duration"]');
            const tuitionInput = newRow.querySelector('input[name$="-tuition_fees"]');
            const yearlyFeesInput = newRow.querySelector('textarea[name$="-yearly_fees"]');

            if (nameField) {
                nameField.value = program.name;
                // إذا كان textarea، نحتاج نعمل auto-resize
                if (nameField.tagName === 'TEXTAREA') {
                    this.autoResizeTextarea(nameField);
                }
            }
            if (durationInput) durationInput.value = program.duration;
            if (tuitionInput) tuitionInput.value = program.tuition_fees;
            if (yearlyFeesInput) {
                yearlyFeesInput.value = program.yearly_fees || '';
                if (typeof this.autoResizeTextarea === 'function') {
                    this.autoResizeTextarea(yearlyFeesInput);
                }
            }
        });
    }

    closeAllFaculties() {
        // إغلاق جميع الكليات بإخفاء البرامج
        this.container.querySelectorAll('.faculty-item').forEach(item => {
            const wrapper = item.querySelector('.faculty-item__programs-wrapper');
            const toggleBtn = item.querySelector('[data-toggle-programs]');
            const icon = toggleBtn ? toggleBtn.querySelector('svg') : null;
            
            if (wrapper) {
                wrapper.style.display = 'none';
            }
            if (icon) {
                icon.classList.remove('rotated');
            }
        });
    }

    showBulkImportSuccess(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'bulk-import-success-message';
        messageDiv.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span>${message}</span>
        `;

        document.body.appendChild(messageDiv);

        // إزالة الرسالة بعد 3 ثوان
        setTimeout(() => {
            messageDiv.classList.add('bulk-import-success-message--hide');
            setTimeout(() => messageDiv.remove(), 300);
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ─── تهيئة Select2 للتخصص المرتبط ───
    initMajorSelect2(context) {
        if (typeof jQuery === 'undefined' || !jQuery.fn.select2) return;
        const selector = '.fpm-major-select, select[name$="-major"]';
        const $targets = context ? jQuery(context).find(selector).addBack(selector) : jQuery(selector);
        
        $targets.each(function() {
            const $el = jQuery(this);
            // تجاهل القالب المخفي
            if ($el.closest('#major-select-template-container').length) return;
            if (!$el.hasClass('select2-hidden-accessible')) {
                $el.select2({
                    placeholder: 'اختر التخصص المرتبط',
                    allowClear: true,
                    dir: 'rtl',
                    width: '100%'
                });
            }
        });
    }

    // ─── فوكس أوتوماتيك على خانة البحث عند فتح القائمة ───
    setupSelect2Autofocus() {
        if (typeof jQuery === 'undefined') return;
        if (window._select2MajorAutofocusAttached) return;
        window._select2MajorAutofocusAttached = true;

        jQuery(document).on('select2:open', function() {
            const focusSearch = function() {
                const searchField = document.querySelector('.select2-container--open .select2-search__field');
                if (searchField) {
                    searchField.focus();
                }
            };
            focusSearch();
            setTimeout(focusSearch, 30);
            setTimeout(focusSearch, 100);
        });
    }
}

// ─── تهيئة عند تحميل الصفحة ───
document.addEventListener('DOMContentLoaded', () => {
    window.facultyProgramsManager = new FacultyProgramsManager();
});
