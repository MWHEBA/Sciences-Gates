/**
 * Sciences Gates WordPress Importer Frontend Integration
 * Handles fetching, sessionStorage, form autofill, confidence colors, and dynamic formsets.
 */

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------------------
    // 1. IMPORT PAGE LOGIC (URL INPUT)
    // -------------------------------------------------------------------------
    const importForm = document.getElementById('import-fetch-form');
    if (importForm) {
        importForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = document.getElementById('import-submit-btn');
            const urlInput = document.getElementById('import-url');
            const loadingState = document.getElementById('import-loading-state');
            const successState = document.getElementById('import-success-state');
            const errorState = document.getElementById('import-error-state');
            const proceedBtn = document.getElementById('import-proceed-btn');

            // Reset UI states
            loadingState.style.display = 'block';
            successState.style.display = 'none';
            errorState.style.display = 'none';
            submitBtn.disabled = true;

            const formData = new FormData(importForm);
            
            try {
                const response = await fetch('/dashboard/import/fetch/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    // Save mapped data to sessionStorage
                    sessionStorage.setItem('sg_import_data', JSON.stringify(data.mapped_data));

                    // Show success state
                    loadingState.style.display = 'none';
                    successState.style.display = 'block';

                    const warningsContainer = document.getElementById('import-success-warnings');
                    warningsContainer.innerHTML = '';
                    
                    const warnings = data.mapped_data.image_warnings || [];
                    if (warnings.length > 0) {
                        warnings.forEach(warn => {
                            const li = document.createElement('div');
                            li.className = 'text-amber-600 font-semibold';
                            li.textContent = `⚠️ ${warn}`;
                            warningsContainer.appendChild(li);
                        });
                        // Show proceed button to allow users to click manually if there are warnings
                        proceedBtn.style.display = 'inline-block';
                        proceedBtn.onclick = () => {
                            window.location.href = data.redirect_url;
                        };
                    } else {
                        // Auto-redirect if no warnings
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 1500);
                    }
                } else {
                    // Show error state
                    loadingState.style.display = 'none';
                    errorState.style.display = 'block';
                    document.getElementById('import-error-message').textContent = data.error || 'حدث خطأ غير متوقع أثناء جلب البيانات.';
                    submitBtn.disabled = false;
                }
            } catch (err) {
                loadingState.style.display = 'none';
                errorState.style.display = 'block';
                document.getElementById('import-error-message').textContent = 'تعذر الاتصال بخادم الاستيراد. يرجى التحقق من الشبكة.';
                submitBtn.disabled = false;
            }
        });
    }

    // -------------------------------------------------------------------------
    // 2. CREATE PAGE AUTOFILL LOGIC
    // -------------------------------------------------------------------------
    const importDataStr = sessionStorage.getItem('sg_import_data');
    if (importDataStr) {
        try {
            const importData = JSON.parse(importDataStr);
            
            // Wait slightly to let Alpine.js and editors initialize
            setTimeout(() => {
                try {
                    if (importData.form_initial) sg_fill_form(importData.form_initial);
                } catch (err) { console.error('Error in sg_fill_form', err); }
                
                try {
                    if (importData.confidence) sg_apply_confidence(importData.confidence);
                } catch (err) { console.error('Error in sg_apply_confidence', err); }
                
                try {
                    if (importData.image_paths) sg_fill_images(importData.image_paths);
                } catch (err) { console.error('Error in sg_fill_images', err); }
                
                try {
                    sg_fill_formsets(importData);
                } catch (err) { console.error('Error in sg_fill_formsets', err); }
                
                try {
                    sg_show_import_banner(importData.image_warnings);
                } catch (err) { console.error('Error in sg_show_import_banner', err); }
                
                // Scroll back to the top of the page after autofilling completes
                // We use a small timeout to make sure any DOM updates/rendering from formsets are finished
                setTimeout(() => {
                    window.scrollTo({ top: 0, behavior: 'instant' });
                    document.documentElement.scrollTop = 0;
                    document.body.scrollTop = 0;
                }, 150);
                
                // Clean up sessionStorage
                sessionStorage.removeItem('sg_import_data');
            }, 300);
        } catch (e) {
            console.error('Failed to parse import data', e);
        }
    }

    // -------------------------------------------------------------------------
    // 3. BULK IMPORT ALL QUEUE LOGIC
    // -------------------------------------------------------------------------
    const bulkImportBtns = document.querySelectorAll('.bulk-import-all-btn');
    const modal = document.getElementById('bulk-progress-modal');
    const modalTitle = document.getElementById('bulk-modal-title');
    const modalClose = document.getElementById('bulk-modal-close');
    const progressStatus = document.getElementById('bulk-progress-status');
    const progressPercent = document.getElementById('bulk-progress-percent');
    const progressBarInner = document.getElementById('bulk-progress-bar-inner');
    const progressLog = document.getElementById('bulk-progress-log');
    const progressSummary = document.getElementById('bulk-progress-summary');
    const cancelBtn = document.getElementById('bulk-modal-cancel-btn');
    const okBtn = document.getElementById('bulk-modal-ok-btn');

    let bulkImportActive = false;
    let cancelBulkImport = false;

    if (bulkImportBtns.length > 0 && modal) {
        bulkImportBtns.forEach(btn => {
            btn.addEventListener('click', async () => {
                if (bulkImportActive) {
                    alert('هناك عملية استيراد جماعي جارية بالفعل. يرجى الانتظار أو إلغاؤها أولاً.');
                    return;
                }
                const category = btn.getAttribute('data-category');
                const activeSection = document.getElementById(`bulk-${category}-section`);
                if (!activeSection) return;

                // Gather visible rows in this section
                const rows = Array.from(activeSection.querySelectorAll('tbody tr')).filter(row => row.style.display !== 'none');
                
                const queue = [];
                rows.forEach(row => {
                    const triggerBtn = row.querySelector('.trigger-import-btn');
                    if (!triggerBtn) return; // Skip headers/empty rows
                    
                    const url = triggerBtn.getAttribute('data-url');
                    const type = triggerBtn.getAttribute('data-type');
                    const titleEl = row.querySelector('.item-title');
                    const slugEl = row.querySelector('.item-slug');
                    
                    queue.push({
                        url: url,
                        type: type,
                        title: titleEl ? titleEl.textContent.trim() : 'عنصر بدون عنوان',
                        slug: slugEl ? slugEl.textContent.trim() : '',
                        row: row,
                        btn: triggerBtn
                    });
                });

                if (queue.length === 0) {
                    alert('لا توجد عناصر متاحة للاستيراد في هذا القسم.');
                    return;
                }

                // Show modal & Reset state
                modal.style.display = 'flex';
                modalClose.style.display = 'none';
                cancelBtn.style.display = 'inline-block';
                okBtn.style.display = 'none';
                progressSummary.style.display = 'none';
                progressLog.innerHTML = '';
                
                let categoryArabicName = 'العناصر';
                if (category === 'universities') categoryArabicName = 'الجامعات';
                else if (category === 'institutes') categoryArabicName = 'المعاهد';
                else if (category === 'majors') categoryArabicName = 'التخصصات';
                else if (category === 'articles') categoryArabicName = 'المقالات';

                modalTitle.textContent = `🔄 استيراد جماعي: ${categoryArabicName}`;
                progressStatus.textContent = `بدء العملية... (0 من ${queue.length})`;
                progressPercent.textContent = '0%';
                progressBarInner.style.width = '0%';

                const logMessage = (text, isError = false, isSuccess = false) => {
                    const el = document.createElement('div');
                    if (isError) el.style.color = 'var(--danger)';
                    else if (isSuccess) el.style.color = 'var(--success)';
                    el.textContent = text;
                    progressLog.appendChild(el);
                    progressLog.scrollTop = progressLog.scrollHeight;
                };

                logMessage(`بدء استيراد ${queue.length} من ${categoryArabicName}...`);

                bulkImportActive = true;
                cancelBulkImport = false;

                // Disable all import buttons during bulk import to prevent double triggers
                document.querySelectorAll('.bulk-import-all-btn, .trigger-import-btn').forEach(button => {
                    button.disabled = true;
                    button.style.opacity = '0.5';
                    button.style.cursor = 'not-allowed';
                });

                const csrfTokenEl = document.querySelector('[name="csrfmiddlewaretoken"]');
                const csrfToken = csrfTokenEl ? csrfTokenEl.value : '';

                let successCount = 0;
                let failCount = 0;

                try {
                    for (let i = 0; i < queue.length; i++) {
                    if (cancelBulkImport) {
                        logMessage('⚠️ تم إلغاء الاستيراد الجماعي بواسطة المستخدم.', false, false);
                        break;
                    }

                    const item = queue[i];
                    progressStatus.textContent = `جاري استيراد: ${item.title} (${i + 1} من ${queue.length})`;
                    logMessage(`[${i + 1}/${queue.length}] جاري جلب وحفظ: ${item.title}...`);

                    // Update row badge to "جاري الاستيراد"
                    const badge = item.row.querySelector('.import-badge');
                    if (badge) {
                        badge.className = 'import-badge';
                        badge.textContent = 'جاري الاستيراد...';
                        badge.style.backgroundColor = 'var(--warning-light)';
                        badge.style.color = 'var(--warning)';
                        badge.style.border = '1px solid rgba(216, 144, 0, 0.2)';
                    }

                    try {
                        const formData = new FormData();
                        formData.append('url', item.url);
                        formData.append('content_type_override', item.type);

                        const response = await fetch('/dashboard/import/bulk-save/', {
                            method: 'POST',
                            body: formData,
                            headers: {
                                'X-CSRFToken': csrfToken,
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        });

                        const data = await response.json();

                        if (response.ok && data.success) {
                            successCount++;
                            let actionText = 'استيراد';
                            if (data.action === 'created') {
                                actionText = 'استيراد عنصر جديد';
                            } else if (data.action === 'updated') {
                                actionText = 'تحديث البيانات';
                            }
                            logMessage(`✅ نجح ${actionText}: ${item.title}`, false, true);
                            
                            // Update badge to success
                            if (badge) {
                                badge.className = 'import-badge import-badge-success';
                                badge.textContent = data.action === 'created' ? 'مستورد (جديد)' : 'مستورد (تحديث)';
                                badge.style.backgroundColor = '';
                                badge.style.color = '';
                                badge.style.border = '';
                            }
                            
                            // Update trigger button
                            item.btn.className = 'trigger-import-btn import-action-btn import-action-btn-secondary';
                            item.btn.textContent = 'استيراد مجدداً';
                        } else {
                            failCount++;
                            const errorMsg = data.error || 'خطأ غير معروف';
                            logMessage(`❌ فشل استيراد: ${item.title} (${errorMsg})`, true, false);
                            
                            // Update badge to failed
                            if (badge) {
                                badge.className = 'import-badge';
                                badge.textContent = 'فشل الاستيراد';
                                badge.style.backgroundColor = 'var(--danger-light)';
                                badge.style.color = 'var(--danger)';
                                badge.style.border = '1px solid rgba(214, 69, 69, 0.2)';
                            }
                        }
                    } catch (err) {
                        failCount++;
                        logMessage(`❌ فشل استيراد: ${item.title} (خطأ في الاتصال بالشبكة)`, true, false);
                        
                        if (badge) {
                            badge.className = 'import-badge';
                            badge.textContent = 'فشل الاستيراد';
                            badge.style.backgroundColor = 'var(--danger-light)';
                            badge.style.color = 'var(--danger)';
                            badge.style.border = '1px solid rgba(214, 69, 69, 0.2)';
                        }
                    }

                    // Update progress bar
                    const percent = Math.round(((i + 1) / queue.length) * 100);
                    progressPercent.textContent = `${percent}%`;
                    progressBarInner.style.width = `${percent}%`;
                }
                } finally {
                    // Done
                    bulkImportActive = false;
                    cancelBtn.style.display = 'none';
                    okBtn.style.display = 'inline-block';
                    modalClose.style.display = 'block';

                    // Re-enable all import buttons
                    document.querySelectorAll('.bulk-import-all-btn, .trigger-import-btn').forEach(button => {
                        button.disabled = false;
                        button.style.opacity = '';
                        button.style.cursor = '';
                    });

                    progressSummary.style.display = 'block';
                    if (cancelBulkImport) {
                        progressSummary.style.backgroundColor = 'var(--warning-light)';
                        progressSummary.style.borderColor = 'var(--warning)';
                        progressSummary.style.color = 'var(--warning)';
                        progressSummary.textContent = `تم إيقاف العملية. نجاح: ${successCount}، فشل: ${failCount} من إجمالي المكتمل: ${successCount + failCount}`;
                    } else {
                        progressSummary.style.backgroundColor = 'var(--success-light)';
                        progressSummary.style.borderColor = 'var(--success)';
                        progressSummary.style.color = 'var(--success)';
                        progressSummary.textContent = `اكتمل الاستيراد الجماعي! نجاح: ${successCount}، فشل: ${failCount} من إجمالي: ${queue.length}`;
                    }
                }
            });
        });

        cancelBtn.addEventListener('click', () => {
            if (bulkImportActive) {
                cancelBulkImport = true;
                cancelBtn.disabled = true;
                cancelBtn.textContent = 'جاري إيقاف العملية...';
            }
        });

        // Restore cancel button when modal is closed
        okBtn.addEventListener('click', () => {
            cancelBtn.disabled = false;
            cancelBtn.textContent = 'إلغاء العملية';
        });
        modalClose.addEventListener('click', () => {
            cancelBtn.disabled = false;
            cancelBtn.textContent = 'إلغاء العملية';
        });
    }
});

/**
 * Fills flat fields (inputs, select, textareas, rich-text editors)
 */
function sg_fill_form(formInitial) {
    for (const [key, value] of Object.entries(formInitial)) {
        if (value === null || value === undefined) continue;

        // Check if there is an HTML editor mount for this field
        const proEditorMount = document.querySelector(`.pro-editor-mount[data-field-name="${key}"]`);
        if (proEditorMount) {
            const editorArea = proEditorMount.querySelector('.pro-editor-content');
            if (editorArea) {
                editorArea.innerHTML = value;
            }
            const textarea = proEditorMount.querySelector('textarea');
            if (textarea) {
                textarea.value = value;
            }
            continue;
        }

        // Find the input elements (use querySelectorAll to support multiple checkboxes/elements with same name)
        const inputs = document.querySelectorAll(`[name="${key}"]`);
        if (inputs.length === 0) continue;

        // Check if multiple checkboxes exist or if it's a ManyToMany array value
        if (inputs[0].type === 'checkbox' && (Array.isArray(value) || inputs.length > 1)) {
            const valuesArray = Array.isArray(value) ? value.map(String) : [String(value)];
            inputs.forEach(cb => {
                cb.checked = valuesArray.includes(cb.value);
                cb.dispatchEvent(new Event('input', { bubbles: true }));
                cb.dispatchEvent(new Event('change', { bubbles: true }));
            });
            continue;
        }

        const input = inputs[0];

        // Check if this is a SimpleRichTextEditor
        const simpleEditorSibling = input.previousElementSibling;
        if (simpleEditorSibling && simpleEditorSibling.classList.contains('rich-text-toolbar')) {
            const contenteditable = simpleEditorSibling.nextElementSibling;
            if (contenteditable && contenteditable.hasAttribute('contenteditable')) {
                contenteditable.innerHTML = value;
                input.value = value;
                continue;
            }
        }

        if (input.type === 'checkbox') {
            input.checked = !!value;
        } else {
            input.value = value;
        }

        // Trigger change/input events for frameworks like Alpine.js
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }
}

/**
 * Applies confidence classes to input fields
 */
function sg_apply_confidence(confidenceMap) {
    for (const [key, rating] of Object.entries(confidenceMap)) {
        // Apply to regular input, select, textarea
        let el = document.querySelector(`[name="${key}"]`);
        if (!el) continue;

        // If it's a pro-editor hidden textarea, apply style to the mount parent container instead
        const proEditorMount = el.closest('.pro-editor-mount');
        if (proEditorMount) {
            el = proEditorMount;
        } else {
            // If simple-rich-text-editor, style the contenteditable container
            const editorSibling = el.previousElementSibling;
            if (editorSibling && editorSibling.classList.contains('rich-text-toolbar')) {
                const contenteditable = editorSibling.nextElementSibling;
                if (contenteditable && contenteditable.hasAttribute('contenteditable')) {
                    el = contenteditable;
                }
            }
        }

        // Remove old classes
        el.classList.remove('import-confidence-high', 'import-confidence-medium', 'import-confidence-none');

        // Add new class based on rating
        if (rating === 'high') {
            el.classList.add('import-confidence-high');
        } else if (rating === 'medium') {
            el.classList.add('import-confidence-medium');
        } else if (rating === 'none') {
            el.classList.add('import-confidence-none');
        }
    }
}

/**
 * Sets up downloaded image previews and appends hidden fields to post media paths
 */
function sg_fill_images(imagePaths) {
    const form = document.querySelector('form');
    if (!form) return;

    for (const [imgType, imgUrl] of Object.entries(imagePaths)) {
        if (!imgUrl) continue;

        // Resolve Django field name
        let fieldName = 'main_image';
        if (imgType === 'logo') {
            fieldName = 'logo';
        } else if (imgType === 'og_image') {
            fieldName = 'og_image';
        } else if (imgType === 'main_image' || imgType === 'featured_image') {
            if (document.querySelector('[name="featured_image"]')) {
                fieldName = 'featured_image';
            } else {
                fieldName = 'main_image';
            }
        }

        const input = document.querySelector(`[name="${fieldName}"]`);
        if (!input) continue;

        // Add hidden input to pass downloaded path back to Django Formsave
        const hiddenInputName = `imported_${fieldName}_path`;
        let hiddenInput = form.querySelector(`input[name="${hiddenInputName}"]`);
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = hiddenInputName;
            form.appendChild(hiddenInput);
        }
        hiddenInput.value = imgUrl;

        // Update Drag & Drop Image Preview Component
        const uploadZone = document.getElementById(`upload-zone-${input.id}`);
        if (uploadZone) {
            const previewDiv = uploadZone.querySelector('.image-upload-preview');
            const placeholderDiv = uploadZone.querySelector('.image-upload-placeholder');
            const filenameDiv = uploadZone.querySelector('.image-upload-filename');

            if (previewDiv && placeholderDiv) {
                const img = previewDiv.querySelector('img');
                if (img) img.src = imgUrl;
                previewDiv.style.display = 'block';
                placeholderDiv.style.display = 'none';

                if (filenameDiv) {
                    const filenameP = filenameDiv.querySelector('p');
                    if (filenameP) filenameP.textContent = 'تم استيراد الصورة بنجاح';
                    filenameDiv.style.display = 'block';
                }
            }
        }
    }
}

/**
 * Fills inline formsets for Faculties, FAQs, and Majors tables
 */
/**
 * Helper to import programs into a faculty form item
 */
function sg_import_faculty_programs(facultyItem, programs) {
    const fpm = window.facultyProgramsManager;
    if (!fpm) return;
    
    const facultyIndex = facultyItem.getAttribute('data-faculty-index');
    const programsContainer = facultyItem.querySelector('[data-programs-container]');
    const totalFormsInput = facultyItem.querySelector(`[name="faculty-${facultyIndex}-programs-TOTAL_FORMS"]`);
    
    if (programsContainer && totalFormsInput) {
        // Mark existing database-backed programs for deletion
        const existingRows = programsContainer.querySelectorAll('.fpm-program-row');
        existingRows.forEach(row => {
            const idInput = row.querySelector('[name$="-id"]');
            const deleteInput = row.querySelector('[name$="-DELETE"]');
            if (idInput && idInput.value) {
                if (deleteInput) deleteInput.value = 'on';
                row.classList.add('fpm-program-row--deleted');
                row.style.opacity = '0.3';
                row.style.pointerEvents = 'none';
            } else {
                row.remove();
            }
        });
        
        // Add empty row if needed (will be removed as we add programs)
        const remaining = programsContainer.querySelectorAll('.fpm-program-row:not(.fpm-program-row--deleted)');
        if (remaining.length === 0 && !programsContainer.querySelector('.fpm-empty-row')) {
            const emptyRow = document.createElement('tr');
            emptyRow.className = 'fpm-empty-row';
            emptyRow.innerHTML = '<td colspan="4" class="fpm-empty-message">لا توجد برامج مضافة</td>';
            programsContainer.appendChild(emptyRow);
        }
    }
    
    // Open programs wrapper temporarily to allow insertion/resizing
    const wrapper = facultyItem.querySelector('.faculty-item__programs-wrapper');
    if (wrapper) {
        wrapper.style.display = 'block';
    }
    
    // Add imported programs
    programs.forEach(program => {
        fpm.addProgram(facultyItem);
        
        const container = facultyItem.querySelector('[data-programs-container]');
        const allRows = container.querySelectorAll('.fpm-program-row');
        const newRow = allRows[allRows.length - 1];
        
        const nameField = newRow.querySelector('textarea[name$="-name"], input[name$="-name"]');
        const durationInput = newRow.querySelector('input[name$="-duration"]');
        const tuitionInput = newRow.querySelector('input[name$="-tuition_fees"]');
        
        if (nameField) {
            nameField.value = program.name || '';
            if (nameField.tagName === 'TEXTAREA') {
                fpm.autoResizeTextarea(nameField);
            }
        }
        if (durationInput) durationInput.value = program.duration || '';
        if (tuitionInput) tuitionInput.value = program.tuition_fees || '';
    });
}

/**
 * Fills inline formsets for Faculties, FAQs, and Majors tables
 */
/**
 * Normalizes Arabic text to handle spelling variations of Alif, Ya, Ta Marbuta, and spaces.
 */
function normalizeArabic(text) {
    if (!text) return '';
    return text.toString().trim()
        .replace(/[أإآ]/g, 'ا')
        .replace(/ة/g, 'ه')
        .replace(/ى/g, 'ي')
        .replace(/\s+/g, ' ')
        .toLowerCase();
}

/**
 * Fills inline formsets for Faculties, FAQs, and Majors tables
 */
function sg_fill_formsets(importData) {
    // 1. Faculties (using window.facultyProgramsManager and raw html)
    if (window.facultyProgramsManager) {
        let facultiesToImport = [];
        if (importData.faculties_raw_html) {
            try {
                const parsed = window.facultyProgramsManager.parseElementorAccordion(importData.faculties_raw_html);
                if (parsed && parsed.faculties && parsed.faculties.length > 0) {
                    facultiesToImport = parsed.faculties;
                }
            } catch (err) {
                console.error('Error parsing faculties raw HTML', err);
            }
        }
        
        // Fallback to parsed faculties_data if no accordion parsed
        if (facultiesToImport.length === 0 && importData.faculties_data) {
            facultiesToImport = importData.faculties_data;
        }

        const existingFaculties = Array.from(window.facultyProgramsManager.container.querySelectorAll('.faculty-item'));
        
        // Create a map of existing name -> item
        const existingMap = {};
        existingFaculties.forEach(item => {
            const nameInput = item.querySelector('.faculty-item__input') || item.querySelector('input[name$="-name"]');
            if (nameInput) {
                const name = normalizeArabic(nameInput.value);
                if (name) {
                    existingMap[name] = item;
                }
            }
        });

        console.log("Existing faculties Map keys:", Object.keys(existingMap));
        console.log("Faculties to import (normalized):", facultiesToImport.map(f => normalizeArabic(f.name)));

        // Set of reused items to keep track of what not to delete
        const reusedItems = new Set();

        facultiesToImport.forEach(faculty => {
            try {
                const importedName = normalizeArabic(faculty.name);
                const existingItem = existingMap[importedName];
                
                if (existingItem) {
                    console.log(`Reusing faculty: ${faculty.name}`);
                    // Reuse existing item
                    reusedItems.add(existingItem);
                    
                    // Unmark delete
                    const deleteInput = existingItem.querySelector('input[name$="-DELETE"]');
                    if (deleteInput) {
                        deleteInput.value = '';
                        deleteInput.checked = false;
                    }
                    existingItem.style.opacity = '1';
                    existingItem.style.pointerEvents = 'auto';
                    existingItem.classList.remove('faculty-item--deleted');
                    existingItem.style.display = '';
                    
                    // Import programs
                    sg_import_faculty_programs(existingItem, faculty.programs);
                } else {
                    console.log(`Creating new faculty: ${faculty.name}`);
                    // Add new faculty
                    window.facultyProgramsManager.addFaculty();
                    const allItems = window.facultyProgramsManager.container.querySelectorAll('.faculty-item');
                    const newFacultyItem = allItems[allItems.length - 1];
                    
                    const nameInput = newFacultyItem.querySelector('input[name$="-name"]');
                    if (nameInput) {
                        nameInput.value = faculty.name;
                    }
                    
                    sg_import_faculty_programs(newFacultyItem, faculty.programs);
                }
            } catch (err) {
                console.error('Error importing faculty', err);
            }
        });

        // Delete any existing items that were not reused
        existingFaculties.forEach(item => {
            if (!reusedItems.has(item)) {
                const deleteInput = item.querySelector('input[name$="-DELETE"]');
                if (deleteInput) {
                    deleteInput.value = 'on';
                    deleteInput.checked = true;
                }
                item.style.opacity = '0.5';
                item.style.pointerEvents = 'none';
                item.classList.add('faculty-item--deleted');
            }
        });
        
        try {
            window.facultyProgramsManager.closeAllFaculties();
        } catch (err) {}
        
        try {
            window.facultyProgramsManager.updateState();
            window.facultyProgramsManager.updateSortOrders();
        } catch (err) {}
    }

    // 2. FAQs (using window.faqManager and raw html)
    if (window.faqManager) {
        let faqsToImport = [];
        if (importData.faqs_raw_html) {
            try {
                const parsed = window.faqManager.parseElementorAccordion(importData.faqs_raw_html);
                if (parsed && parsed.faqs && parsed.faqs.length > 0) {
                    faqsToImport = parsed.faqs;
                }
            } catch (err) {
                console.error('Error parsing FAQs raw HTML', err);
            }
        }

        // Fallback to parsed faqs_data if no accordion parsed
        if (faqsToImport.length === 0 && importData.faqs_data) {
            faqsToImport = importData.faqs_data;
        }

        const existingFaqs = Array.from(window.faqManager.container.querySelectorAll('.faq-item'));
        const existingMap = {};
        existingFaqs.forEach(item => {
            const questionInput = item.querySelector('input[name$="-question"]');
            if (questionInput) {
                const question = normalizeArabic(questionInput.value);
                if (question) {
                    existingMap[question] = item;
                }
            }
        });
        
        const reusedFaqs = new Set();
        faqsToImport.forEach(faq => {
            try {
                const importedQuestion = normalizeArabic(faq.question);
                const existingItem = existingMap[importedQuestion];
                if (existingItem) {
                    reusedFaqs.add(existingItem);
                    
                    const deleteInput = existingItem.querySelector('input[name$="-DELETE"]');
                    if (deleteInput) {
                        deleteInput.value = '';
                        deleteInput.checked = false;
                    }
                    existingItem.style.opacity = '1';
                    existingItem.style.pointerEvents = 'auto';
                    existingItem.classList.remove('faq-item--deleted');
                    existingItem.style.display = '';
                    
                    const answerInput = existingItem.querySelector('textarea[name$="-answer"]');
                    if (answerInput) {
                        answerInput.value = faq.answer;
                    }
                } else {
                    window.faqManager.addFAQ();
                    const allItems = window.faqManager.container.querySelectorAll('.faq-item');
                    const newFAQItem = allItems[allItems.length - 1];
                    const questionInput = newFAQItem.querySelector('input[name$="-question"]');
                    const answerInput = newFAQItem.querySelector('textarea[name$="-answer"]');
                    if (questionInput) {
                        questionInput.value = faq.question;
                        window.faqManager.updateQuestionPreview(newFAQItem);
                    }
                    if (answerInput) {
                        answerInput.value = faq.answer;
                    }
                }
            } catch (err) {
                console.error('Error importing FAQ', err);
            }
        });
        
        // Delete any existing items that were not reused
        existingFaqs.forEach(item => {
            if (!reusedFaqs.has(item)) {
                const deleteInput = item.querySelector('input[name$="-DELETE"]');
                if (deleteInput) {
                    deleteInput.value = 'on';
                    deleteInput.checked = true;
                }
                item.style.opacity = '0.5';
                item.style.pointerEvents = 'none';
                item.classList.add('faq-item--deleted');
            }
        });
        
        try {
            window.faqManager.updateState();
        } catch (err) {}
    }

    // 3. Subjects Table (Majors)
    if (importData.subjects_tables && importData.subjects_tables.length > 0) {
        sg_clear_django_formset('subjects_tables');
        sg_fill_django_formset('subjects_tables', importData.subjects_tables, {
            'key': 'academic_year',
            'value': 'subjects'
        });
    }

    // 4. Salary Table (Majors)
    if (importData.salary_tables && importData.salary_tables.length > 0) {
        sg_clear_django_formset('salary_tables');
        sg_fill_django_formset('salary_tables', importData.salary_tables, {
            'key': 'job_title',
            'value': 'average_monthly_salary'
        });
    }

    // 5. Countries Table (Majors)
    if (importData.countries_tables && importData.countries_tables.length > 0) {
        sg_clear_django_formset('countries_tables');
        sg_fill_django_formset('countries_tables', importData.countries_tables, {
            'key': 'destination',
            'value': 'annual_fees'
        });
    }
}

/**
 * Clears standard Django formsets (marking existing saved forms for deletion)
 */
function sg_clear_django_formset(prefix) {
    if (!window.formsetManagers) return;
    const manager = window.formsetManagers[prefix];
    if (!manager) return;

    const deleteCheckboxes = manager.formsetContainer.querySelectorAll('input[name$="-DELETE"]');
    deleteCheckboxes.forEach(cb => {
        cb.checked = true;
        cb.dispatchEvent(new Event('change', { bubbles: true }));
    });
}


/**
 * Generic helper to fill standard Django formsets using FormsetManager API
 */
function sg_fill_django_formset(prefix, dataArray, fieldMap) {
    if (!window.formsetManagers) return;
    const manager = window.formsetManagers[prefix];
    if (!manager) return;

    dataArray.forEach((item, index) => {
        // If it's not the first row, add a new form row
        if (index > 0) {
            manager.addForm();
        }

        // Fill values
        for (const [wpKey, djangoField] of Object.entries(fieldMap)) {
            const inputName = `${prefix}-${index}-${djangoField}`;
            const input = manager.formsetContainer.querySelector(`[name="${inputName}"]`);
            if (input) {
                input.value = item[wpKey] || '';
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    });
}

/**
 * Shows the imported content warning banner
 */
function sg_show_import_banner(warnings) {
    // Check if import banner template exists
    let banner = document.getElementById('import-banner');
    if (!banner) {
        // Create banner element dynamically and insert at top of page container
        const formContainer = document.querySelector('form');
        if (!formContainer) return;

        banner = document.createElement('div');
        banner.id = 'import-banner';
        banner.className = 'import-banner';
        
        banner.innerHTML = `
            <svg style="width: 24px; height: 24px; color: var(--warning); flex-shrink: 0;" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            <div style="flex: 1;">
                <strong style="color: var(--text-primary);">تم ملء هذا الفورم تلقائياً من نظام الاستيراد.</strong>
                <p style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">
                    يرجى مراجعة الحقول المميزة بالأصفر (ثقة متوسطة) والأحمر (حاجة للمراجعة أو الإدخال اليدوي).
                </p>
                <div id="import-banner-warnings" style="margin-top: 8px; font-size: 12px; color: var(--danger); line-height: 1.5;">
                </div>
            </div>
            <button type="button" onclick="document.getElementById('import-banner').remove()" style="background: none; border: none; cursor: pointer; color: var(--text-muted); font-size: 16px;">✕</button>
        `;

        formContainer.parentNode.insertBefore(banner, formContainer);
    }

    // Add warnings if any
    const warningsDiv = document.getElementById('import-banner-warnings');
    if (warningsDiv && warnings && warnings.length > 0) {
        warnings.forEach(warn => {
            const p = document.createElement('p');
            p.textContent = `⚠️ ${warn}`;
            warningsDiv.appendChild(p);
        });
    }

    // Display confidence indicator legend
    let legend = document.getElementById('confidence-legend');
    if (!legend) {
        legend = document.createElement('div');
        legend.id = 'confidence-legend';
        legend.className = 'confidence-legend';
        legend.innerHTML = `
            <span class="legend-high">● ثقة عالية</span>
            <span class="legend-medium">● بحاجة لمراجعة</span>
            <span class="legend-none">● إدخال يدوي</span>
        `;
        banner.querySelector('div').appendChild(legend);
    }
}
