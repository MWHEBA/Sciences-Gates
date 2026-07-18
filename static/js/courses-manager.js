/**
 * Courses/Fees Manager
 * إدارة ديناميكية لأسطر جدول رسوم المعهد
 * Matches faq-manager.js features and behavior
 */

class CoursesManager {
    constructor() {
        this.container = document.getElementById('course-items-container');
        this.totalFormsInput = document.getElementById('id_courses-TOTAL_FORMS');
        this.emptyState = document.getElementById('course-empty-state');
        this.counterEl = document.getElementById('courses-counter');
        
        if (!this.container || !this.totalFormsInput) return;
        
        this.init();
    }

    init() {
        this.attachAddHandler();
        this.attachBulkImportHandler();
        this.attachItemHandlers();
        this.updateState();
    }

    attachAddHandler() {
        const addBtn = document.getElementById('course-add-btn');
        if (addBtn) {
            addBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.addCourse();
            });
        }
    }

    attachBulkImportHandler() {
        const bulkBtn = document.getElementById('course-bulk-import-btn');
        if (bulkBtn) {
            bulkBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.openBulkImportModal();
            });
        }
    }

    addCourse() {
        const totalForms = parseInt(this.totalFormsInput.value);
        const newIndex = totalForms;

        // Collapse all existing courses
        this.container.querySelectorAll('.course-item:not(.course-item--deleted)').forEach(item => {
            this.toggleContent(item, false);
        });

        const item = this.createCourseItem(newIndex);
        this.container.appendChild(item);
        this.totalFormsInput.value = newIndex + 1;

        // Animation
        requestAnimationFrame(() => {
            item.classList.add('course-item--visible');
        });

        this.attachItemHandlers();
        this.updateState();
        this.updateSortOrders();

        // Auto-expand new item
        this.toggleContent(item, true);

        // Focus duration input
        const durationInput = item.querySelector('input[name$="-duration"]');
        if (durationInput) {
            setTimeout(() => durationInput.focus(), 150);
        }
    }

    importCourse(course) {
        this.addCourse();

        const allItems = this.container.querySelectorAll('.course-item');
        const newCourseItem = allItems[allItems.length - 1];

        const typeInput = newCourseItem.querySelector('select[name$="-course_type"]');
        const durationInput = newCourseItem.querySelector('input[name$="-duration"]');
        const myrInput = newCourseItem.querySelector('input[name$="-fees_myr"]');
        const usdInput = newCourseItem.querySelector('input[name$="-fees_usd"]');
        const sarInput = newCourseItem.querySelector('input[name$="-fees_sar"]');
        const visaInput = newCourseItem.querySelector('input[name$="-visa_duration"]');

        if (typeInput) {
            typeInput.value = course.course_type || 'undefined';
        }
        if (durationInput) {
            durationInput.value = course.duration || '';
            this.updatePreview(newCourseItem);
        }
        if (myrInput) {
            myrInput.value = course.fees_myr || '';
        }
        if (usdInput) {
            usdInput.value = course.fees_usd || '';
        }
        if (sarInput) {
            sarInput.value = course.fees_sar || '';
        }
        if (visaInput) {
            visaInput.value = course.visa_duration || '';
        }
    }

    createCourseItem(index) {
        const item = document.createElement('div');
        item.className = 'course-item';
        item.setAttribute('data-course-index', index);
        item.innerHTML = `
            <div class="course-item__header">
                <span class="course-item__drag-handle" title="اسحب لإعادة الترتيب">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="9" cy="6" r="1.5"/>
                        <circle cx="15" cy="6" r="1.5"/>
                        <circle cx="9" cy="12" r="1.5"/>
                        <circle cx="15" cy="12" r="1.5"/>
                        <circle cx="9" cy="18" r="1.5"/>
                        <circle cx="15" cy="18" r="1.5"/>
                    </svg>
                </span>
                <div class="course-item__number">${index + 1}</div>
                <span class="course-item__title-preview">صف رسوم جديد</span>
                <button type="button" class="course-item__toggle" title="عرض/إخفاء الحقول" data-toggle-content>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </button>
                <button type="button" class="course-item__delete" title="حذف">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14"/>
                        <line x1="10" y1="11" x2="10" y2="17"/>
                        <line x1="14" y1="11" x2="14" y2="17"/>
                    </svg>
                </button>
            </div>
            <div class="course-item__content">
                <div class="course-grid">
                    <div class="course-item__field">
                        <label for="id_courses-${index}-course_type">نوع الكورس</label>
                        <select name="courses-${index}-course_type" id="id_courses-${index}-course_type" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" dir="rtl">
                            <option value="undefined">بدون ساعات</option>
                            <option value="regular">4 ساعات</option>
                            <option value="intensive">5 ساعات</option>
                            <option value="super_intensive">6 ساعات</option>
                        </select>
                    </div>
                    <div class="course-item__field">
                        <label for="id_courses-${index}-duration">مدة الكورس</label>
                        <input type="text" name="courses-${index}-duration" id="id_courses-${index}-duration" class="course-duration-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="مثال: شهر، شهرين" required dir="rtl">
                    </div>
                    <div class="course-item__field">
                        <label for="id_courses-${index}-fees_myr">الرسوم (MYR)</label>
                        <input type="text" name="courses-${index}-fees_myr" id="id_courses-${index}-fees_myr" class="course-fees-myr-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="مثال: 3,400" required dir="rtl">
                    </div>
                    <div class="course-item__field">
                        <label for="id_courses-${index}-fees_usd">الرسوم (USD)</label>
                        <input type="text" name="courses-${index}-fees_usd" id="id_courses-${index}-fees_usd" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="مثال: 857" dir="rtl">
                    </div>
                    <div class="course-item__field">
                        <label for="id_courses-${index}-fees_sar">الرسوم (SAR)</label>
                        <input type="text" name="courses-${index}-fees_sar" id="id_courses-${index}-fees_sar" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="مثال: 3,216" dir="rtl">
                    </div>
                    <div class="course-item__field">
                        <label for="id_courses-${index}-visa_duration">تأشيرة الطالب</label>
                        <input type="text" name="courses-${index}-visa_duration" id="id_courses-${index}-visa_duration" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="مثال: بدون تأشيرة" dir="rtl">
                    </div>
                </div>
                <input type="hidden" name="courses-${index}-sort_order" value="${index}">
                <input type="hidden" name="courses-${index}-id" value="">
                <input type="hidden" name="courses-${index}-DELETE" value="">
            </div>
        `;
        return item;
    }

    deleteItem(item) {
        const deleteInput = item.querySelector('input[name$="-DELETE"]');
        const idInput = item.querySelector('input[name$="-id"]');

        if (idInput && idInput.value) {
            deleteInput.value = 'on';
            item.classList.add('course-item--deleted');
            setTimeout(() => {
                item.style.display = 'none';
                this.updateState();
                this.updateNumbers();
            }, 300);
        } else {
            item.classList.add('course-item--deleted');
            setTimeout(() => {
                item.remove();
                this.reindexForms();
                this.updateState();
            }, 300);
        }
    }

    toggleContent(item, forceExpand = null) {
        const content = item.querySelector('.course-item__content');
        const toggleBtn = item.querySelector('[data-toggle-content]');
        const icon = toggleBtn.querySelector('svg');
        
        const isExpanded = content.classList.contains('expanded');
        const shouldExpand = forceExpand !== null ? forceExpand : !isExpanded;
        
        if (shouldExpand) {
            content.classList.add('expanded');
            icon.classList.add('rotated');
            toggleBtn.setAttribute('aria-expanded', 'true');
        } else {
            content.classList.remove('expanded');
            icon.classList.remove('rotated');
            toggleBtn.setAttribute('aria-expanded', 'false');
        }
    }

    updatePreview(item) {
        const durationInput = item.querySelector('input[name$="-duration"]');
        const feesMyrInput = item.querySelector('input[name$="-fees_myr"]');
        const typeSelect = item.querySelector('select[name$="-course_type"]');
        const preview = item.querySelector('.course-item__title-preview');
        
        if (preview) {
            const duration = durationInput ? durationInput.value.trim() : '';
            const feesMyr = feesMyrInput ? feesMyrInput.value.trim() : '';
            
            let typeLabel = '';
            if (typeSelect) {
                const selectedOption = typeSelect.options[typeSelect.selectedIndex];
                if (selectedOption) {
                    typeLabel = selectedOption.text.trim();
                }
            }
            
            if (duration || feesMyr || typeLabel) {
                const parts = [];
                if (typeLabel) parts.push(`النوع: ${typeLabel}`);
                if (duration) parts.push(`المدة: ${duration}`);
                if (feesMyr) parts.push(`الرسوم: ${feesMyr} MYR`);
                preview.textContent = parts.join(' | ');
            } else {
                preview.textContent = 'صف رسوم جديد';
            }
        }
    }

    reindexForms() {
        const allItems = this.container.querySelectorAll('.course-item');
        
        allItems.forEach((item, idx) => {
            item.setAttribute('data-course-index', idx);
            const inputs = item.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                const name = input.getAttribute('name');
                if (name) {
                    input.setAttribute('name', name.replace(/courses-\d+-/, `courses-${idx}-`));
                }
                const id = input.getAttribute('id');
                if (id) {
                    input.setAttribute('id', id.replace(/id_courses-\d+-/, `id_courses-${idx}-`));
                }
            });
            
            const labels = item.querySelectorAll('label');
            labels.forEach(label => {
                const htmlFor = label.getAttribute('for');
                if (htmlFor) {
                    label.setAttribute('for', htmlFor.replace(/id_courses-\d+-/, `id_courses-${idx}-`));
                }
            });
        });

        this.totalFormsInput.value = allItems.length;
        this.updateNumbers();
    }

    updateNumbers() {
        const visibleItems = this.container.querySelectorAll('.course-item:not(.course-item--deleted):not([style*="display: none"])');
        visibleItems.forEach((item, idx) => {
            const numberEl = item.querySelector('.course-item__number');
            if (numberEl) numberEl.textContent = idx + 1;
        });
    }

    updateSortOrders() {
        const visibleItems = this.container.querySelectorAll('.course-item:not(.course-item--deleted):not([style*="display: none"])');
        visibleItems.forEach((item, idx) => {
            const sortInput = item.querySelector('input[name$="-sort_order"]');
            if (sortInput) sortInput.value = idx;
        });
    }

    updateState() {
        const visibleItems = this.container.querySelectorAll('.course-item:not(.course-item--deleted):not([style*="display: none"])');
        const count = visibleItems.length;

        if (this.emptyState) {
            this.emptyState.style.display = count === 0 ? 'flex' : 'none';
        }
        if (this.counterEl) {
            this.counterEl.textContent = count;
            this.counterEl.style.display = count > 0 ? 'inline-flex' : 'none';
        }
    }

    attachItemHandlers() {
        // Delete buttons
        this.container.querySelectorAll('.course-item__delete').forEach(btn => {
            btn.onclick = (e) => {
                e.preventDefault();
                const item = btn.closest('.course-item');
                this.deleteItem(item);
            };
        });

        // Toggle buttons
        this.container.querySelectorAll('[data-toggle-content]').forEach(btn => {
            btn.onclick = (e) => {
                e.preventDefault();
                const item = btn.closest('.course-item');
                this.toggleContent(item);
            };
        });

        // Click header (except buttons/drag handle)
        this.container.querySelectorAll('.course-item__header').forEach(header => {
            header.onclick = (e) => {
                if (
                    e.target.closest('.course-item__delete') ||
                    e.target.closest('.course-item__toggle') ||
                    e.target.closest('.course-item__drag-handle')
                ) {
                    return;
                }
                e.preventDefault();
                const item = header.closest('.course-item');
                this.toggleContent(item);
            };
        });

        // Change inputs -> update preview title
        this.container.querySelectorAll('input, select').forEach(input => {
            if (input.name.includes('-duration') || input.name.includes('-fees_myr') || input.name.includes('-course_type')) {
                const eventType = input.tagName.toLowerCase() === 'select' ? 'change' : 'input';
                input.addEventListener(eventType, (e) => {
                    const item = e.target.closest('.course-item');
                    this.updatePreview(item);
                });
            }
        });

        // Drag & Drop
        this.container.querySelectorAll('.course-item').forEach(item => {
            const handle = item.querySelector('.course-item__drag-handle');
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
        });
        
        // Initial preview titles for existing rows
        this.container.querySelectorAll('.course-item').forEach(item => {
            this.updatePreview(item);
        });
    }

    onDragStart(e, item) {
        item.classList.add('course-item--dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', '');
    }

    onDragEnd(e, item) {
        item.classList.remove('course-item--dragging');
        this.container.querySelectorAll('.course-item--drag-over').forEach(el => {
            el.classList.remove('course-item--drag-over');
        });
        this.updateSortOrders();
        this.reindexForms();
    }

    onDragOver(e, item) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';

        this.container.querySelectorAll('.course-item--drag-over').forEach(el => {
            el.classList.remove('course-item--drag-over');
        });

        if (!item.classList.contains('course-item--dragging')) {
            item.classList.add('course-item--drag-over');
        }
    }

    onDrop(e, item) {
        e.preventDefault();
        item.classList.remove('course-item--drag-over');

        const draggedItem = this.container.querySelector('.course-item--dragging');
        if (draggedItem && draggedItem !== item) {
            const allItems = [...this.container.querySelectorAll('.course-item:not([style*="display: none"])')];
            const draggedIdx = allItems.indexOf(draggedItem);
            const targetIdx = allItems.indexOf(item);

            if (draggedIdx < targetIdx) {
                item.after(draggedItem);
            } else {
                item.before(draggedItem);
            }
        }
    }

    openBulkImportModal() {
        if (!this.bulkImportModal) {
            this.createBulkImportModal();
        }
        this.bulkImportModal.classList.add('faq-bulk-import-modal--active');
        this.bulkImportModal.querySelector('.faq-bulk-import-textarea').focus();
    }

    createBulkImportModal() {
        const modal = document.createElement('div');
        modal.className = 'faq-bulk-import-modal';
        modal.id = 'course-bulk-import-modal';
        modal.innerHTML = `
            <div class="faq-bulk-import-modal__overlay"></div>
            <div class="faq-bulk-import-modal__content">
                <div class="faq-bulk-import-modal__header">
                    <h3>استيراد الرسوم من Elementor</h3>
                    <button type="button" class="faq-bulk-import-modal__close" aria-label="إغلاق">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>

                <div class="faq-bulk-import-modal__body">
                    <!-- خطوة 1: إدخال الكود -->
                    <div class="faq-bulk-import-step faq-bulk-import-step--active" data-step="input">
                        <div class="faq-bulk-import-step__content">
                            <p class="faq-bulk-import-instructions">
                                الصق كود HTML من Elementor Accordion (الذي يحتوي على جداول رسوم المعهد بالعملات المختلفة)
                            </p>
                            <textarea 
                                class="faq-bulk-import-textarea" 
                                placeholder="الصق كود Elementor Accordion هنا..."
                                dir="rtl"
                                spellcheck="false"
                                style="min-height: 250px;"
                            ></textarea>
                            <div class="faq-bulk-import-info">
                                <p>💡 <strong>كيفية الاستخدام:</strong></p>
                                <ul>
                                    <li>افتح صفحة المعهد القديمة التي تحتوي على الرسوم.</li>
                                    <li>افتح أدوات المتصفح (F12) وانسخ كود الأكورديون أو جدول الرسوم كاملاً.</li>
                                    <li>الصقه هنا واضغط "التالي" لمعاينة البيانات قبل حفظها.</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <!-- خطوة 2: المعاينة والتحقق -->
                    <div class="faq-bulk-import-step" data-step="preview">
                        <div class="faq-bulk-import-step__content">
                            <div class="faq-bulk-import-preview">
                                <div class="faq-bulk-import-preview__stats">
                                    <div class="faq-bulk-import-stat">
                                        <span class="faq-bulk-import-stat__label">عدد الصفوف المكتشفة:</span>
                                        <span class="faq-bulk-import-stat__value" data-courses="0">0</span>
                                    </div>
                                </div>

                                <div class="faq-bulk-import-preview__list">
                                    <div class="faq-bulk-import-preview__title">الصفوف والأسعار المكتشفة:</div>
                                    <ul class="faq-bulk-import-preview__items">
                                        <!-- سيتم ملؤها ديناميكياً -->
                                    </ul>
                                </div>

                                <div class="faq-bulk-import-warnings" style="display: none;">
                                    <!-- سيتم عرض التحذيرات هنا -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="faq-bulk-import-modal__footer">
                    <button type="button" class="faq-bulk-import-btn-cancel">إلغاء</button>
                    <button type="button" class="faq-bulk-import-btn-next" data-step="input">التالي</button>
                    <button type="button" class="faq-bulk-import-btn-confirm" style="display: none;">تأكيد الاستيراد</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.bulkImportModal = modal;
        this.setupBulkImportEvents();
    }

    setupBulkImportEvents() {
        const overlay = this.bulkImportModal.querySelector('.faq-bulk-import-modal__overlay');
        const closeBtn = this.bulkImportModal.querySelector('.faq-bulk-import-modal__close');
        const cancelBtn = this.bulkImportModal.querySelector('.faq-bulk-import-btn-cancel');
        const nextBtn = this.bulkImportModal.querySelector('.faq-bulk-import-btn-next');
        const confirmBtn = this.bulkImportModal.querySelector('.faq-bulk-import-btn-confirm');
        const textarea = this.bulkImportModal.querySelector('.faq-bulk-import-textarea');

        const closeModal = () => this.closeBulkImportModal();
        overlay.addEventListener('click', closeModal);
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);

        nextBtn.addEventListener('click', () => this.goToBulkImportPreview());
        confirmBtn.addEventListener('click', () => this.confirmBulkImport());
        textarea.addEventListener('input', () => this.updateBulkImportPreview());
    }

    closeBulkImportModal() {
        this.bulkImportModal.classList.remove('faq-bulk-import-modal--active');
        this.resetBulkImportModal();
    }

    resetBulkImportModal() {
        this.bulkImportModal.querySelector('.faq-bulk-import-textarea').value = '';
        this.showBulkImportStep('input');
        this.bulkImportModal.querySelector('.faq-bulk-import-btn-next').style.display = 'block';
        this.bulkImportModal.querySelector('.faq-bulk-import-btn-confirm').style.display = 'none';
    }

    showBulkImportStep(stepName) {
        this.bulkImportModal.querySelectorAll('.faq-bulk-import-step').forEach(step => {
            step.classList.remove('faq-bulk-import-step--active');
        });
        this.bulkImportModal.querySelector(`[data-step="${stepName}"]`).classList.add('faq-bulk-import-step--active');
    }

    parseElementorFees(htmlString) {
        try {
            const cleanHtml = htmlString.trim();
            const parser = new DOMParser();
            const doc = parser.parseFromString(cleanHtml, 'text/html');

            const accordion = doc.querySelector('.elementor-accordion');
            let tables = [];

            if (accordion) {
                const accItems = accordion.querySelectorAll('.elementor-accordion-item');
                accItems.forEach((item, idx) => {
                    const titleEl = item.querySelector('.elementor-accordion-title');
                    const title = titleEl ? titleEl.textContent.trim() : '';

                    const contentEl = item.querySelector('.elementor-tab-content');
                    if (contentEl) {
                        const table = contentEl.querySelector('table');
                        if (table) {
                            tables.push({ title, element: table });
                        }
                    }
                });
            } else {
                const directTables = doc.querySelectorAll('table');
                directTables.forEach((table, idx) => {
                    let title = `جدول مستورد ${idx + 1}`;
                    let prev = table.previousElementSibling;
                    if (prev && (prev.tagName.startsWith('H') || prev.classList.contains('elementor-heading-title'))) {
                        title = prev.textContent.trim();
                    }
                    tables.push({ title, element: table });
                });
            }

            if (tables.length === 0) {
                return { courses: [], errors: ['لم يتم العثور على أي جداول رسوم في الكود المرفق.'] };
            }

            const coursesMap = {};
            const errors = [];

            tables.forEach(({ title, element }) => {
                const lowerTitle = title.toLowerCase();
                let currency = 'usd';
                if (lowerTitle.includes('myr') || lowerTitle.includes('rm') || lowerTitle.includes('رنجت') || lowerTitle.includes('ماليزي')) {
                    currency = 'myr';
                } else if (lowerTitle.includes('sar') || lowerTitle.includes('ريال') || lowerTitle.includes('سعودي')) {
                    currency = 'sar';
                } else if (lowerTitle.includes('usd') || lowerTitle.includes('دولار') || lowerTitle.includes('$')) {
                    currency = 'usd';
                }

                const rows = element.querySelectorAll('tr');
                let currentSection = '';

                rows.forEach((row) => {
                    const thCells = row.querySelectorAll('th');
                    if (thCells.length === 1) {
                        currentSection = thCells[0].textContent.trim();
                        return;
                    }

                    if (thCells.length > 0) {
                        return;
                    }

                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 3) {
                        const duration = cells[0].textContent.trim();
                        const feeVal = cells[1].textContent.trim();
                        const visaVal = cells[2].textContent.trim();

                        if (!duration || !feeVal) return;

                        const cleanedFee = feeVal.replace(/[^\d\.,]/g, '').trim();

                        let course_type = 'undefined';
                        const secLower = currentSection.toLowerCase();
                        if (secLower.includes('6 ساعات') || secLower.includes('6 hours') || secLower.includes('٦ ساعات')) {
                            course_type = 'super_intensive';
                        } else if (secLower.includes('مكثف') || secLower.includes('intensive') || secLower.includes('5 ساعات') || secLower.includes('5 hours') || secLower.includes('٥ ساعات')) {
                            course_type = 'intensive';
                        } else if (secLower.includes('عادي') || secLower.includes('regular') || secLower.includes('4 ساعات') || secLower.includes('4 hours') || secLower.includes('٤ ساعات')) {
                            course_type = 'regular';
                        }

                        const mapKey = duration + '_' + course_type;
                        if (!coursesMap[mapKey]) {
                            coursesMap[mapKey] = {
                                duration: duration,
                                course_type: course_type,
                                fees_myr: '',
                                fees_usd: '',
                                fees_sar: '',
                                visa_duration: visaVal !== 'غير محدد' ? visaVal : ''
                            };
                        }

                        if (currency === 'myr') {
                            coursesMap[mapKey].fees_myr = cleanedFee;
                        } else if (currency === 'usd') {
                            coursesMap[mapKey].fees_usd = cleanedFee;
                        } else if (currency === 'sar') {
                            coursesMap[mapKey].fees_sar = cleanedFee;
                        }

                        if (visaVal && visaVal !== 'غير محدد' && !coursesMap[mapKey].visa_duration) {
                            coursesMap[mapKey].visa_duration = visaVal;
                        }
                    }
                });
            });

            // Fill missing fees_myr with USD estimation
            Object.values(coursesMap).forEach(c => {
                if (!c.fees_myr && c.fees_usd) {
                    const usdVal = parseFloat(c.fees_usd.replace(/,/g, ''));
                    if (!isNaN(usdVal)) {
                        c.fees_myr = Math.round(usdVal * 4.7).toLocaleString();
                    }
                }
            });

            const courses = Object.values(coursesMap);
            if (courses.length === 0) {
                return { courses: [], errors: ['لم يتم العثور على أي صفوف رسوم صالحة.'] };
            }

            return { courses, errors };
        } catch (e) {
            return { courses: [], errors: [`خطأ أثناء تحليل الكود: ${e.message}`] };
        }
    }

    updateBulkImportPreview() {
        const textarea = this.bulkImportModal.querySelector('.faq-bulk-import-textarea');
        const { courses, errors } = this.parseElementorFees(textarea.value);

        this.bulkImportData = { courses, errors };

        this.bulkImportModal.querySelector('[data-courses]').textContent = courses.length;

        const itemsList = this.bulkImportModal.querySelector('.faq-bulk-import-preview__items');
        itemsList.innerHTML = courses.map(c => `
            <li class="faq-bulk-import-preview__item" style="display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 10px; border-bottom: 1px solid var(--border);">
                <span class="faq-bulk-import-preview__item-question" style="font-weight: 600; color: var(--text-primary);">
                    ${this.escapeHtml(c.duration)} (${c.course_type === 'intensive' ? 'مكثف' : 'عادي'})
                </span>
                <span style="font-size: 13px; color: var(--text-secondary); direction: ltr;">
                    RM ${c.fees_myr || '—'} | $ ${c.fees_usd || '—'} | SAR ${c.fees_sar || '—'}
                </span>
            </li>
        `).join('');

        const warningsDiv = this.bulkImportModal.querySelector('.faq-bulk-import-warnings');
        if (errors.length > 0) {
            warningsDiv.innerHTML = `
                <div class="faq-bulk-import-warning">
                    <div class="faq-bulk-import-warning__title">⚠️ تحذيرات:</div>
                    <ul class="faq-bulk-import-warning__list">
                        ${errors.map(error => `<li>${this.escapeHtml(error)}</li>`).join('')}
                    </ul>
                </div>
            `;
            warningsDiv.style.display = 'block';
        } else {
            warningsDiv.style.display = 'none';
        }

        const nextBtn = this.bulkImportModal.querySelector('.faq-bulk-import-btn-next');
        nextBtn.disabled = courses.length === 0 || errors.length > 0;
    }

    goToBulkImportPreview() {
        this.updateBulkImportPreview();
        this.showBulkImportStep('preview');
        this.bulkImportModal.querySelector('.faq-bulk-import-btn-next').style.display = 'none';
        this.bulkImportModal.querySelector('.faq-bulk-import-btn-confirm').style.display = 'block';
    }

    confirmBulkImport() {
        if (!this.bulkImportData || this.bulkImportData.courses.length === 0) {
            alert('لا توجد بيانات صحيحة للاستيراد');
            return;
        }

        this.bulkImportData.courses.forEach(course => {
            this.importCourse(course);
        });

        this.closeBulkImportModal();
        this.showBulkImportSuccess(`تم استيراد ${this.bulkImportData.courses.length} صف رسوم بنجاح`);
    }

    showBulkImportSuccess(message) {
        const successMessage = document.createElement('div');
        successMessage.className = 'faq-bulk-import-success-message';
        successMessage.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            <span>${message}</span>
        `;
        document.body.appendChild(successMessage);

        setTimeout(() => {
            successMessage.classList.add('faq-bulk-import-success-message--hide');
            setTimeout(() => successMessage.remove(), 300);
        }, 3000);
    }

    escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.coursesManager = new CoursesManager();
});
