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

        // Find the input element
        const input = document.querySelector(`[name="${key}"]`);
        if (!input) continue;

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

        facultiesToImport.forEach(faculty => {
            try {
                window.facultyProgramsManager.importFaculty(faculty);
            } catch (err) {
                console.error('Error importing faculty', err);
            }
        });
        
        try {
            window.facultyProgramsManager.closeAllFaculties();
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

        faqsToImport.forEach(faq => {
            try {
                window.faqManager.importFAQ(faq);
            } catch (err) {
                console.error('Error importing FAQ', err);
            }
        });
    }

    // 3. Subjects Table (Majors)
    if (importData.subjects_tables && importData.subjects_tables.length > 0) {
        sg_fill_django_formset('subjects_tables', importData.subjects_tables, {
            'key': 'academic_year',
            'value': 'subjects'
        });
    }

    // 4. Salary Table (Majors)
    if (importData.salary_tables && importData.salary_tables.length > 0) {
        sg_fill_django_formset('salary_tables', importData.salary_tables, {
            'key': 'job_title',
            'value': 'average_monthly_salary'
        });
    }

    // 5. Countries Table (Majors)
    if (importData.countries_tables && importData.countries_tables.length > 0) {
        sg_fill_django_formset('countries_tables', importData.countries_tables, {
            'key': 'destination',
            'value': 'annual_fees'
        });
    }
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
