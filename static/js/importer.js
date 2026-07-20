/**
 * Sciences Gates WordPress Importer Frontend Integration
 * Handles fetching, sessionStorage, form autofill, confidence colors, and dynamic formsets.
 */

function sg_init_importer() {
    // -------------------------------------------------------------------------
    // 1. IMPORT PAGE LOGIC (URL INPUT)
    // -------------------------------------------------------------------------


    const pollJobStatus = (jobId, onProgress, onSuccess, onFailure) => {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/sg/import/status/${jobId}/`, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const resData = await res.json();
                if (res.ok && resData.success) {
                    if (resData.status === 'SUCCESS') {
                        clearInterval(interval);
                        onSuccess(resData);
                    } else if (resData.status === 'FAILED') {
                        clearInterval(interval);
                        onFailure(resData.error_message || 'فشلت العملية.');
                    } else {
                        onProgress(resData.progress, resData.status_message);
                    }
                } else {
                    clearInterval(interval);
                    onFailure(resData.error || 'فشل الاتصال بالخادم لمتابعة الحالة.');
                }
            } catch (err) {
                clearInterval(interval);
                onFailure('خطأ في الاتصال بالشبكة أثناء متابعة الحالة.');
            }
        }, 1500);
        return interval;
    };

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
            document.getElementById('import-loading-text').textContent = 'جاري بدء الاتصال بالموقع القديم...';
            successState.style.display = 'none';
            errorState.style.display = 'none';
            submitBtn.disabled = true;

            const formData = new FormData(importForm);
            
            const fetchAndPoll = async (fd) => {
                try {
                    const response = await fetch('/sg/import/fetch/', {
                        method: 'POST',
                        body: fd,
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    });

                    if (!response.ok) {
                        const text = await response.text();
                        let errMsg = `خطأ في الخادم (${response.status})`;
                        try {
                            const errData = JSON.parse(text);
                            errMsg = errData.error || errMsg;
                        } catch(e) {}
                        throw new Error(errMsg);
                    }

                    const data = await response.json();

                    if (data.success) {
                        const jobId = data.job_id;
                        pollJobStatus(
                            jobId,
                            (progress, message) => {
                                document.getElementById('import-loading-text').textContent = `${message} (${progress}%)`;
                            },
                            (resData) => {
                                const finalData = resData.result_data;
                                sessionStorage.setItem('sg_import_data', JSON.stringify(finalData.mapped_data));

                                loadingState.style.display = 'none';
                                successState.style.display = 'block';

                                const warningsContainer = document.getElementById('import-success-warnings');
                                if (warningsContainer) {
                                    warningsContainer.innerHTML = '';
                                    const warnings = finalData.mapped_data.image_warnings || [];
                                    warnings.forEach(warn => {
                                        const li = document.createElement('div');
                                        li.className = 'text-amber-600 font-semibold';
                                        li.textContent = `⚠️ ${warn}`;
                                        warningsContainer.appendChild(li);
                                    });
                                }
                                
                                // Redirect after successful fetch (no prompt needed)
                                const warnings = finalData.mapped_data.image_warnings || [];
                                if (warnings.length > 0) {
                                    proceedBtn.style.display = 'inline-block';
                                    proceedBtn.onclick = () => {
                                        window.location.href = finalData.redirect_url;
                                    };
                                } else {
                                    setTimeout(() => {
                                        window.location.href = finalData.redirect_url;
                                    }, 1500);
                                }
                            },
                            (errorMsg) => {
                                loadingState.style.display = 'none';
                                errorState.style.display = 'block';
                                document.getElementById('import-error-message').textContent = errorMsg;
                                submitBtn.disabled = false;
                            }
                        );
                    } else {
                        loadingState.style.display = 'none';
                        errorState.style.display = 'block';
                        document.getElementById('import-error-message').textContent = data.error || 'حدث خطأ غير متوقع أثناء جلب البيانات.';
                        submitBtn.disabled = false;
                    }
                } catch (err) {
                    loadingState.style.display = 'none';
                    errorState.style.display = 'block';
                    document.getElementById('import-error-message').textContent = err.message || 'تعذر الاتصال بخادم الاستيراد. يرجى التحقق من الشبكة.';
                    submitBtn.disabled = false;
                }
            };

            fetchAndPoll(formData);
        });
    }

    // -------------------------------------------------------------------------
    // 2. CREATE PAGE AUTOFILL LOGIC
    // -------------------------------------------------------------------------
    const importDataStr = sessionStorage.getItem('sg_import_data');
    if (importDataStr && importDataStr !== 'undefined' && importDataStr !== 'null') {
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
                        
                        const competitorUrl = item.btn.getAttribute('data-competitor-url') || '';
                        if (competitorUrl) {
                            formData.append('competitor_url', competitorUrl);
                        }


                        const response = await fetch('/sg/import/bulk-save/', {
                            method: 'POST',
                            body: formData,
                            headers: {
                                'X-CSRFToken': csrfToken,
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        });

                        if (!response.ok) {
                            const text = await response.text();
                            let errMsg = `خطأ في الخادم (${response.status})`;
                            try {
                                const errData = JSON.parse(text);
                                errMsg = errData.error || errMsg;
                            } catch(e) {}
                            throw new Error(errMsg);
                        }

                        const data = await response.json();

                        if (data.success) {
                            const jobId = data.job_id;
                            
                            // Wait for the background job to finish
                            const jobResult = await new Promise((resolve, reject) => {
                                pollJobStatus(
                                    jobId,
                                    (progress, message) => {
                                        progressStatus.textContent = `جاري استيراد: ${item.title} (${i + 1} من ${queue.length}) - ${message} (${progress}%)`;
                                    },
                                    (resData) => {
                                        resolve(resData.result_data);
                                    },
                                    (errorMsg) => {
                                        reject(new Error(errorMsg));
                                    }
                                );
                            });

                            successCount++;
                            let actionText = 'استيراد';
                            if (jobResult.action === 'created') {
                                actionText = 'استيراد عنصر جديد';
                            } else if (jobResult.action === 'updated') {
                                actionText = 'تحديث البيانات';
                            }
                            logMessage(`✅ نجح ${actionText}: ${item.title}`, false, true);
                            
                            // Update badge to success
                            if (badge) {
                                badge.className = 'import-badge import-badge-success';
                                badge.textContent = jobResult.action === 'created' ? 'مستورد (جديد)' : 'مستورد (تحديث)';
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
                        logMessage(`❌ فشل استيراد: ${item.title} (${err.message || 'خطأ في الاتصال بالشبكة'})`, true, false);
                        
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

        // Initialize Interactive Wizard
        sg_init_wizard();
    }
}

// Global variables for wizard state
let wizardQueue = [];
let wizardCurrentIndex = 0;
let wizardFetchedData = {}; // slug -> { status: 'PENDING'|'FETCHING'|'READY'|'FAILED', data, prompt, error }
let currentParsedJSON = null;

function sg_init_wizard() {
    const startWizardBtn = document.getElementById('start-wizard-btn');
    const selectAllMajors = document.getElementById('select-all-majors');
    const wizardModal = document.getElementById('wizard-import-modal');
    
    if (!startWizardBtn || !wizardModal) return;

    // 1. Checkboxes interaction
    const checkboxes = document.querySelectorAll('.select-major-checkbox');
    
    function updateWizardButtonState() {
        const checked = document.querySelectorAll('.select-major-checkbox:checked');
        const count = checked.length;
        const countSpan = document.getElementById('selected-wizard-count');
        if (countSpan) countSpan.textContent = count;
        
        if (count > 0) {
            startWizardBtn.style.display = 'inline-flex';
        } else {
            startWizardBtn.style.display = 'none';
        }
    }

    if (selectAllMajors) {
        selectAllMajors.addEventListener('change', function() {
            checkboxes.forEach(cb => {
                if (!cb.disabled) {
                    cb.checked = selectAllMajors.checked;
                }
            });
            updateWizardButtonState();
        });
    }

    checkboxes.forEach(cb => {
        cb.addEventListener('change', updateWizardButtonState);
    });

    // 2. Start Wizard
    startWizardBtn.addEventListener('click', function() {
        const checked = document.querySelectorAll('.select-major-checkbox:checked');
        wizardQueue = [];
        checked.forEach(cb => {
            wizardQueue.push({
                url: cb.getAttribute('data-url'),
                slug: cb.getAttribute('data-slug'),
                title: cb.getAttribute('data-title'),
                competitorUrl: cb.getAttribute('data-competitor-url') || ''
            });
        });

        if (wizardQueue.length === 0) return;

        wizardCurrentIndex = 0;
        wizardFetchedData = {};
        
        // Initialize cache
        wizardQueue.forEach(item => {
            wizardFetchedData[item.slug] = {
                status: 'PENDING',
                data: null,
                prompt: null,
                error: null
            };
        });

        // Show Modal
        wizardModal.style.display = 'flex';
        
        // Disable page scroll
        document.body.style.overflow = 'hidden';

        // Load first item
        loadWizardItem(wizardCurrentIndex);
    });

    // 3. Tab switching inside wizard
    const tabPasteBtn = document.getElementById('wizard-tab-paste-btn');
    const tabStagingBtn = document.getElementById('wizard-tab-staging-btn');
    const panelPaste = document.getElementById('wizard-panel-paste');
    const panelStaging = document.getElementById('wizard-panel-staging');

    if (tabPasteBtn && tabStagingBtn && panelPaste && panelStaging) {
        tabPasteBtn.addEventListener('click', () => {
            tabPasteBtn.style.borderBottomColor = 'var(--primary)';
            tabPasteBtn.style.color = 'var(--primary)';
            tabStagingBtn.style.borderBottomColor = 'transparent';
            tabStagingBtn.style.color = 'var(--text-muted)';
            panelPaste.style.display = 'flex';
            panelStaging.style.display = 'none';
        });

        tabStagingBtn.addEventListener('click', () => {
            tabStagingBtn.style.borderBottomColor = 'var(--primary)';
            tabStagingBtn.style.color = 'var(--primary)';
            tabPasteBtn.style.borderBottomColor = 'transparent';
            tabPasteBtn.style.color = 'var(--text-muted)';
            panelPaste.style.display = 'none';
            panelStaging.style.display = 'flex';
        });
    }

    // 4. Wizard actions
    const skipBtn = document.getElementById('wizard-skip-btn');
    const saveBtn = document.getElementById('wizard-save-btn');
    const copyBtn = document.getElementById('wizard-copy-prompt-btn');
    const retryBtn = document.getElementById('prefetch-retry-btn');

    if (skipBtn) {
        skipBtn.addEventListener('click', () => {
            advanceWizard();
        });
    }

    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const promptText = document.getElementById('wizard-prompt-text');
            if (promptText) {
                promptText.select();
                document.execCommand('copy');
                copyBtn.textContent = 'تم النسخ! ✓';
                setTimeout(() => {
                    copyBtn.textContent = 'نسخ البرومبت 📋';
                }, 1500);
            }
        });
    }

    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            if (wizardCurrentIndex + 1 < wizardQueue.length) {
                const nextItem = wizardQueue[wizardCurrentIndex + 1];
                prefetchNextItem(wizardCurrentIndex); // Re-triggers fetch
            }
        });
    }

    // JSON paste validation and staging filling
    const jsonPaste = document.getElementById('wizard-json-paste');
    const jsonError = document.getElementById('wizard-json-error');

    if (jsonPaste) {
        jsonPaste.addEventListener('input', function() {
            const val = this.value.trim();
            if (jsonError) {
                jsonError.style.display = 'none';
                jsonError.textContent = '';
            }
            if (saveBtn) saveBtn.disabled = true;
            currentParsedJSON = null;

            if (!val) return;

            let rawVal = val;
            // Strip markdown code block wrappers if pasted
            if (rawVal.includes('```')) {
                const match = rawVal.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
                if (match && match[1]) {
                    rawVal = match[1].trim();
                }
            }

            try {
                const parsed = JSON.parse(rawVal);
                if (!parsed.name) {
                    throw new Error("يجب تضمين اسم التخصص في حقل 'name'");
                }
                currentParsedJSON = parsed;
                if (saveBtn) saveBtn.disabled = false;

                // Fill staging fields
                const nameF = document.getElementById('staging-field-name');
                const bachF = document.getElementById('staging-field-bachelor_duration');
                const mastF = document.getElementById('staging-field-master_duration');
                const phdF = document.getElementById('staging-field-phd_duration');
                const langF = document.getElementById('staging-field-study_language');
                const pracF = document.getElementById('staging-field-practical_training');

                if (nameF) nameF.value = parsed.name || '';
                if (bachF) bachF.value = parsed.bachelor_duration || '';
                if (mastF) mastF.value = parsed.master_duration || '';
                if (phdF) phdF.value = parsed.phd_duration || '';
                if (langF) langF.value = parsed.study_language || '';
                if (pracF) pracF.value = parsed.practical_training || '';

            } catch (e) {
                if (jsonError) {
                    jsonError.textContent = `❌ خطأ في الـ JSON: ${e.message}`;
                    jsonError.style.display = 'block';
                }
            }
        });
    }

    // Listen to changes in staging fields to update currentParsedJSON on the fly
    const stagingInputs = [
        { id: 'staging-field-name', key: 'name' },
        { id: 'staging-field-bachelor_duration', key: 'bachelor_duration' },
        { id: 'staging-field-master_duration', key: 'master_duration' },
        { id: 'staging-field-phd_duration', key: 'phd_duration' },
        { id: 'staging-field-study_language', key: 'study_language' },
        { id: 'staging-field-practical_training', key: 'practical_training' }
    ];

    stagingInputs.forEach(item => {
        const input = document.getElementById(item.id);
        if (input) {
            input.addEventListener('input', function() {
                if (currentParsedJSON) {
                    currentParsedJSON[item.key] = this.value;
                }
            });
        }
    });

    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            if (!currentParsedJSON) return;

            saveBtn.disabled = true;
            saveBtn.textContent = 'جاري الحفظ والتحميل... ⏳';

            const currentItem = wizardQueue[wizardCurrentIndex];
            const cacheEntry = wizardFetchedData[currentItem.slug];

            // Merge currentParsedJSON into cacheEntry.data.mapped_data
            const finalMappedData = cacheEntry.data.mapped_data;
            if (!finalMappedData.form_initial) {
                finalMappedData.form_initial = {};
            }

            // Copy flat fields
            for (const [key, val] of Object.entries(currentParsedJSON)) {
                if (val !== null && typeof val !== 'object') {
                    finalMappedData.form_initial[key] = val;
                }
            }

            // Copy formsets
            const arrayFields = [
                'subjects_tables', 'salary_tables', 'countries_tables',
                'faqs_data', 'faculties_data', 'courses_data', 'tuition_fees',
                'best_universities', 'cheap_universities'
            ];
            arrayFields.forEach(arr => {
                if (currentParsedJSON[arr] !== undefined) {
                    finalMappedData[arr] = currentParsedJSON[arr];
                }
            });

            // Get CSRF Token
            const csrfTokenEl = document.querySelector('[name="csrfmiddlewaretoken"]');
            const csrfToken = csrfTokenEl ? csrfTokenEl.value : '';

            try {
                const response = await fetch('/sg/import/save-draft/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        content_type: 'major',
                        mapped_data: finalMappedData
                    })
                });

                const resData = await response.json();
                if (response.ok && resData.success) {
                    sg_show_toast(`✅ تم حفظ التخصص كمسودة بنجاح: ${resData.name}`, 'success');
                    advanceWizard();
                } else {
                    sg_show_toast(`❌ فشل الحفظ: ${resData.error || 'خطأ غير معروف في السيرفر.'}`, 'danger');
                    saveBtn.disabled = false;
                    saveBtn.textContent = 'حفظ كمسودة وتالي 💾';
                }
            } catch (e) {
                sg_show_toast(`❌ فشل الحفظ: تعذر الاتصال بالشبكة.`, 'danger');
                saveBtn.disabled = false;
                saveBtn.textContent = 'حفظ كمسودة وتالي 💾';
            }
        });
    }
}

function loadWizardItem(index) {
    if (index >= wizardQueue.length) {
        alert("🎉 اكتمل استيراد جميع التخصصات المحددة بنجاح!");
        document.getElementById('wizard-import-modal').style.display = 'none';
        document.body.style.overflow = '';
        window.location.reload();
        return;
    }

    const item = wizardQueue[index];
    const cacheEntry = wizardFetchedData[item.slug];

    // Reset UI Panel/Form states
    const jsonPasteInput = document.getElementById('wizard-json-paste');
    if (jsonPasteInput) jsonPasteInput.value = '';
    
    const jsonErrorDiv = document.getElementById('wizard-json-error');
    if (jsonErrorDiv) jsonErrorDiv.style.display = 'none';
    
    const saveBtn = document.getElementById('wizard-save-btn');
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.textContent = 'حفظ كمسودة وتالي 💾';
    }
    
    // Clear staging inputs
    const fields = [
        'staging-field-name', 'staging-field-bachelor_duration',
        'staging-field-master_duration', 'staging-field-phd_duration',
        'staging-field-study_language', 'staging-field-practical_training'
    ];
    fields.forEach(f => {
        const input = document.getElementById(f);
        if (input) input.value = '';
    });

    // Switch back to Paste Tab
    const tabPasteBtn = document.getElementById('wizard-tab-paste-btn');
    if (tabPasteBtn) tabPasteBtn.click();

    // Update progress bar
    const currentMajorNameSpan = document.getElementById('wizard-current-major-name');
    if (currentMajorNameSpan) currentMajorNameSpan.textContent = item.title;
    
    const progressText = document.getElementById('wizard-progress-text');
    if (progressText) progressText.textContent = `${index + 1} / ${wizardQueue.length}`;
    
    const percent = Math.round(((index + 1) / wizardQueue.length) * 100);
    const progressBar = document.getElementById('wizard-progress-bar-inner');
    if (progressBar) progressBar.style.width = `${percent}%`;

    // Update URLs previews
    const oldUrlLink = document.getElementById('wizard-old-url');
    if (oldUrlLink) {
        oldUrlLink.href = item.url;
    }
    
    const compUrlRow = document.getElementById('wizard-comp-url-row');
    const compUrlLink = document.getElementById('wizard-comp-url');
    if (compUrlRow && compUrlLink) {
        if (item.competitorUrl) {
            compUrlRow.style.display = 'block';
            compUrlLink.href = item.competitorUrl;
        } else {
            compUrlRow.style.display = 'none';
        }
    }

    const promptTextarea = document.getElementById('wizard-prompt-text');

    // Process depending on cache state
    if (cacheEntry.status === 'READY') {
        if (promptTextarea) promptTextarea.value = cacheEntry.prompt;
        prefetchNextItem(index);
    } else if (cacheEntry.status === 'FETCHING') {
        if (promptTextarea) promptTextarea.value = "جاري جلب البيانات وتجهيز البرومبت في الخلفية... يرجى الانتظار.";
        pollFetchStatusForCurrent(item.slug);
    } else if (cacheEntry.status === 'FAILED') {
        if (promptTextarea) promptTextarea.value = `❌ فشل تحضير البيانات: ${cacheEntry.error}\nسيتم المحاولة مجدداً تلقائياً.`;
        triggerFetchAndPoll(item.slug, () => {
            loadWizardItem(index);
        });
    } else {
        // PENDING
        if (promptTextarea) promptTextarea.value = "جاري بدء جلب البيانات وتجهيز البرومبت...";
        triggerFetchAndPoll(item.slug, () => {
            loadWizardItem(index);
        });
    }
}

function triggerFetchAndPoll(slug, callback) {
    const item = wizardQueue.find(q => q.slug === slug);
    if (!item) return;

    const cacheEntry = wizardFetchedData[slug];
    cacheEntry.status = 'FETCHING';

    const csrfTokenEl = document.querySelector('[name="csrfmiddlewaretoken"]');
    const csrfToken = csrfTokenEl ? csrfTokenEl.value : '';

    const formData = new FormData();
    formData.append('url', item.url);
    formData.append('content_type_override', 'major');
    formData.append('lazy_images', 'true');
    if (item.competitorUrl) {
        formData.append('competitor_url', item.competitorUrl);
    }

    fetch('/sg/import/fetch/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const jobId = data.job_id;
            
            // Poll status
            const pollInterval = setInterval(() => {
                fetch(`/sg/import/status/${jobId}/`, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(res => res.json())
                .then(resData => {
                    if (resData.success) {
                        if (resData.status === 'SUCCESS') {
                            clearInterval(pollInterval);
                            cacheEntry.status = 'READY';
                            cacheEntry.data = resData.result_data;
                            if (callback) callback();
                        } else if (resData.status === 'FAILED') {
                            clearInterval(pollInterval);
                            cacheEntry.status = 'FAILED';
                            cacheEntry.error = resData.error_message || 'فشلت العملية.';
                            if (callback) callback();
                        }
                    } else {
                        clearInterval(pollInterval);
                        cacheEntry.status = 'FAILED';
                        cacheEntry.error = resData.error || 'فشل المتابعة.';
                        if (callback) callback();
                    }
                })
                .catch(err => {
                    clearInterval(pollInterval);
                    cacheEntry.status = 'FAILED';
                    cacheEntry.error = 'خطأ في الاتصال بالشبكة.';
                    if (callback) callback();
                });
            }, 1500);
        } else {
            cacheEntry.status = 'FAILED';
            cacheEntry.error = data.error || 'فشل جلب البيانات.';
            if (callback) callback();
        }
    })
    .catch(err => {
        cacheEntry.status = 'FAILED';
        cacheEntry.error = 'تعذر بدء عملية الاستيراد.';
        if (callback) callback();
    });
}

function pollFetchStatusForCurrent(slug) {
    const interval = setInterval(() => {
        const cacheEntry = wizardFetchedData[slug];
        if (cacheEntry.status === 'READY') {
            clearInterval(interval);
            const promptTextarea = document.getElementById('wizard-prompt-text');
            if (promptTextarea) promptTextarea.value = cacheEntry.prompt;
            prefetchNextItem(wizardCurrentIndex);
        } else if (cacheEntry.status === 'FAILED') {
            clearInterval(interval);
            const promptTextarea = document.getElementById('wizard-prompt-text');
            if (promptTextarea) promptTextarea.value = `❌ فشل تحضير البيانات: ${cacheEntry.error}`;
        }
    }, 1000);
}

function prefetchNextItem(currentIndex) {
    const nextIndex = currentIndex + 1;
    const prefetchSpinner = document.getElementById('prefetch-spinner');
    const prefetchStatusText = document.getElementById('prefetch-status-text');
    const prefetchRetryBtn = document.getElementById('prefetch-retry-btn');

    if (nextIndex >= wizardQueue.length) {
        if (prefetchStatusText) prefetchStatusText.textContent = "المعالج: هذا هو العنصر الأخير.";
        if (prefetchSpinner) prefetchSpinner.style.display = 'none';
        if (prefetchRetryBtn) prefetchRetryBtn.style.display = 'none';
        return;
    }

    const nextItem = wizardQueue[nextIndex];
    const cacheEntry = wizardFetchedData[nextItem.slug];

    if (prefetchRetryBtn) prefetchRetryBtn.style.display = 'none';

    if (cacheEntry.status === 'READY') {
        if (prefetchStatusText) prefetchStatusText.textContent = `التالي جاهز: ${nextItem.title} ✓`;
        if (prefetchSpinner) prefetchSpinner.style.display = 'none';
    } else if (cacheEntry.status === 'FETCHING') {
        if (prefetchStatusText) prefetchStatusText.textContent = `جاري تحضير التالي: ${nextItem.title}...`;
        if (prefetchSpinner) prefetchSpinner.style.display = 'inline-block';
        
        const waitInterval = setInterval(() => {
            if (cacheEntry.status === 'READY') {
                clearInterval(waitInterval);
                if (wizardCurrentIndex === currentIndex) {
                    if (prefetchStatusText) prefetchStatusText.textContent = `التالي جاهز: ${nextItem.title} ✓`;
                    if (prefetchSpinner) prefetchSpinner.style.display = 'none';
                }
            } else if (cacheEntry.status === 'FAILED') {
                clearInterval(waitInterval);
                if (wizardCurrentIndex === currentIndex) {
                    if (prefetchStatusText) prefetchStatusText.textContent = `فشل تحضير التالي: ${nextItem.title}`;
                    if (prefetchSpinner) prefetchSpinner.style.display = 'none';
                    if (prefetchRetryBtn) prefetchRetryBtn.style.display = 'inline-block';
                }
            }
        }, 1000);
    } else {
        if (prefetchStatusText) prefetchStatusText.textContent = `جاري تحضير التالي: ${nextItem.title}...`;
        if (prefetchSpinner) prefetchSpinner.style.display = 'inline-block';
        
        triggerFetchAndPoll(nextItem.slug, () => {
            if (wizardCurrentIndex === currentIndex) {
                if (cacheEntry.status === 'READY') {
                    if (prefetchStatusText) prefetchStatusText.textContent = `التالي جاهز: ${nextItem.title} ✓`;
                } else {
                    if (prefetchStatusText) prefetchStatusText.textContent = `فشل تحضير التالي: ${nextItem.title}`;
                    if (prefetchRetryBtn) prefetchRetryBtn.style.display = 'inline-block';
                }
                if (prefetchSpinner) prefetchSpinner.style.display = 'none';
            }
        });
    }
}

function advanceWizard() {
    wizardCurrentIndex++;
    loadWizardItem(wizardCurrentIndex);
}

window.sg_cancel_wizard_prompt = function() {
    if (confirm("هل أنت متأكد من رغبتك في إلغاء معالج الاستيراد؟ سيتم فقدان التقدم الحالي غير المحفوظ.")) {
        const modal = document.getElementById('wizard-import-modal');
        if (modal) modal.style.display = 'none';
        document.body.style.overflow = '';
        window.location.reload();
    }
};

function sg_show_toast(message, type = 'success') {
    let container = document.getElementById('sg-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'sg-toast-container';
        container.style.cssText = `
            position: fixed;
            bottom: 24px;
            left: 24px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            direction: rtl;
        `;
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bgColor = type === 'success' ? 'var(--success)' : 'var(--danger)';
    const textColor = 'var(--white)';
    
    toast.style.cssText = `
        background-color: ${bgColor};
        color: ${textColor};
        padding: 12px 24px;
        border-radius: var(--radius-sm);
        box-shadow: var(--shadow-sm);
        font-size: 14px;
        font-weight: 500;
        min-width: 250px;
        display: flex;
        align-items: center;
        gap: 8px;
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
    `;

    const icon = type === 'success' ? '✓' : '❌';
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    }, 10);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            toast.remove();
            if (container.children.length === 0) {
                container.remove();
            }
        }, 300);
    }, 3000);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', sg_init_importer);
} else {
    sg_init_importer();
}

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
        const yearlyFeesInput = newRow.querySelector('textarea[name$="-yearly_fees"]');
        
        if (nameField) {
            nameField.value = program.name || '';
            if (nameField.tagName === 'TEXTAREA') {
                fpm.autoResizeTextarea(nameField);
            }
        }
        if (durationInput) durationInput.value = program.duration || '';
        if (tuitionInput) tuitionInput.value = program.tuition_fees || '';
        if (yearlyFeesInput) {
            yearlyFeesInput.value = program.yearly_fees || '';
            if (typeof fpm.autoResizeTextarea === 'function') {
                fpm.autoResizeTextarea(yearlyFeesInput);
            }
        }
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

        // Set of reused items to keep track of what not to delete
        const reusedItems = new Set();

        facultiesToImport.forEach(faculty => {
            try {
                const importedName = normalizeArabic(faculty.name);
                const existingItem = existingMap[importedName];
                
                if (existingItem) {
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
                        const mount = answerInput.closest('.pro-editor-mount');
                        if (mount && mount.editorInstance) {
                            mount.editorInstance.setContent(faq.answer);
                        }
                    }
                } else {
                    window.faqManager.importFAQ(faq);
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

    // 3. Institute Courses (using window.coursesManager and courses_data with smart reuse)
    if (window.coursesManager && importData.courses_data && importData.courses_data.length > 0) {
        const existingCourses = Array.from(window.coursesManager.container.querySelectorAll('.course-item'));
        const existingMap = {};
        existingCourses.forEach(item => {
            const durationInput = item.querySelector('input[name$="-duration"]');
            if (durationInput) {
                const duration = normalizeArabic(durationInput.value);
                if (duration) {
                    existingMap[duration] = item;
                }
            }
        });
        
        const reusedCourses = new Set();
        importData.courses_data.forEach(course => {
            try {
                const importedDuration = normalizeArabic(course.duration);
                const existingItem = existingMap[importedDuration];
                if (existingItem) {
                    reusedCourses.add(existingItem);
                    
                    const deleteInput = existingItem.querySelector('input[name$="-DELETE"]');
                    if (deleteInput) {
                        deleteInput.value = '';
                        deleteInput.checked = false;
                    }
                    existingItem.style.opacity = '1';
                    existingItem.style.pointerEvents = 'auto';
                    existingItem.classList.remove('course-item--deleted');
                    existingItem.style.display = '';
                    
                    const myrInput = existingItem.querySelector('input[name$="-fees_myr"]');
                    const usdInput = existingItem.querySelector('input[name$="-fees_usd"]');
                    const sarInput = existingItem.querySelector('input[name$="-fees_sar"]');
                    const visaInput = existingItem.querySelector('input[name$="-visa_duration"]');
                    
                    if (myrInput) myrInput.value = course.fees_myr || '';
                    if (usdInput) usdInput.value = course.fees_usd || '';
                    if (sarInput) sarInput.value = course.fees_sar || '';
                    if (visaInput) visaInput.value = course.visa_duration || '';
                    
                    window.coursesManager.updatePreview(existingItem);
                } else {
                    window.coursesManager.importCourse(course);
                }
            } catch (err) {
                console.error('Error importing course', err);
            }
        });
        
        // Delete any existing items that were not reused
        existingCourses.forEach(item => {
            if (!reusedCourses.has(item)) {
                const deleteInput = item.querySelector('input[name$="-DELETE"]');
                if (deleteInput) {
                    deleteInput.value = 'on';
                    deleteInput.checked = true;
                }
                item.style.opacity = '0.5';
                item.style.pointerEvents = 'none';
                item.classList.add('course-item--deleted');
            }
        });
        
        try {
            window.coursesManager.updateState();
        } catch (err) {}
    }

    // 4. Subjects Table (Majors)
    if (importData.subjects_tables && importData.subjects_tables.length > 0) {
        sg_clear_django_formset('subjects_tables');
        sg_fill_django_formset('subjects_tables', importData.subjects_tables, {
            'academic_year': 'academic_year',
            'subjects': 'subjects',
            'track_name': 'track_name'
        });
    }

    // 4. Salary Table (Majors)
    if (importData.salary_tables && importData.salary_tables.length > 0) {
        sg_clear_django_formset('salary_tables');
        sg_fill_django_formset('salary_tables', importData.salary_tables, {
            'job_title': 'job_title',
            'job_description': 'job_description',
            'average_monthly_salary': 'average_monthly_salary'
        });
    }

    // 5. Countries Table (Majors)
    if (importData.countries_tables && importData.countries_tables.length > 0) {
        sg_clear_django_formset('countries_tables');
        sg_fill_django_formset('countries_tables', importData.countries_tables, {
            'destination': 'destination',
            'study_duration': 'study_duration',
            'annual_fees': 'annual_fees',
            'living_cost': 'living_cost'
        });
    }

    // 6. Tuition Fees JSON Table (Majors)
    if (importData.tuition_fees) {
        const textarea = document.getElementById('id_tuition_fees');
        if (textarea) {
            try {
                const tablesData = typeof importData.tuition_fees === 'string' ? JSON.parse(importData.tuition_fees) : importData.tuition_fees;
                textarea.value = JSON.stringify(tablesData);
                
                const alpineEl = document.querySelector('[x-data^="tuitionFeesManager"]');
                if (alpineEl && window.Alpine) {
                    window.Alpine.$data(alpineEl).tables = tablesData;
                    window.Alpine.$data(alpineEl).updateJSON();
                }
            } catch (e) {
                console.error('Error applying tuition_fees to Alpine.js', e);
            }
        }
    }

    // 7. Best & Cheap Universities Many-to-Many relations
    if (importData.best_universities && Array.isArray(importData.best_universities)) {
        const alpineEl = document.querySelector('[x-data*="relationsSelectComponent"][x-data*="best_universities"]');
        if (alpineEl && window.Alpine) {
            try {
                const data = window.Alpine.$data(alpineEl);
                // Clear existing selection first
                data.selectedItems = [];
                // Uncheck all Django checkboxes
                const checkboxes = alpineEl.querySelectorAll('input[type="checkbox"]');
                checkboxes.forEach(cb => {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                });
                // Select matching items
                importData.best_universities.forEach(univName => {
                    const match = data.allItems.find(item => normalizeArabic(item.name) === normalizeArabic(univName));
                    if (match) {
                        data.selectItem(match);
                    }
                });
            } catch (err) {
                console.error('Error populating best_universities relation select', err);
            }
        }
    }

    if (importData.cheap_universities && Array.isArray(importData.cheap_universities)) {
        const alpineEl = document.querySelector('[x-data*="relationsSelectComponent"][x-data*="cheap_universities"]');
        if (alpineEl && window.Alpine) {
            try {
                const data = window.Alpine.$data(alpineEl);
                // Clear existing selection first
                data.selectedItems = [];
                // Uncheck all Django checkboxes
                const checkboxes = alpineEl.querySelectorAll('input[type="checkbox"]');
                checkboxes.forEach(cb => {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                });
                // Select matching items
                importData.cheap_universities.forEach(univName => {
                    const match = data.allItems.find(item => normalizeArabic(item.name) === normalizeArabic(univName));
                    if (match) {
                        data.selectItem(match);
                    }
                });
            } catch (err) {
                console.error('Error populating cheap_universities relation select', err);
            }
        }
    }
}

/**
 * Clears standard Django formsets (marking existing saved forms for deletion)
 */
function sg_clear_django_formset(prefix) {
    let manager = null;
    let container = null;
    let itemClass = 'form-item';
    let reindexMethod = null;

    if (window.formsetManagers && window.formsetManagers[prefix]) {
        manager = window.formsetManagers[prefix];
        container = manager.formsetContainer;
    } else if (prefix === 'subjects_tables' && window.subjectsManager) {
        manager = window.subjectsManager;
        container = manager.container;
        itemClass = 'subject-item';
        reindexMethod = () => manager.reindexForms();
    } else if (prefix === 'salary_tables' && window.salariesManager) {
        manager = window.salariesManager;
        container = manager.container;
        itemClass = 'salary-item';
        reindexMethod = () => manager.reindexForms();
    } else if (prefix === 'countries_tables' && window.countriesManager) {
        manager = window.countriesManager;
        container = manager.container;
        itemClass = 'country-item';
        reindexMethod = () => manager.reindexForms();
    }

    if (!container) return;

    // Get all existing rows (both saved and unsaved)
    const forms = Array.from(container.querySelectorAll('[data-row-index], [data-form-index]'));
    
    forms.forEach(formEl => {
        const deleteCb = formEl.querySelector('input[name$="-DELETE"]');
        const idInput = formEl.querySelector('input[name$="-id"]');
        
        if (idInput && idInput.value) {
            // Existing DB record: mark as deleted, check DELETE input, hide
            if (deleteCb) {
                deleteCb.checked = true;
                deleteCb.value = 'on';
                deleteCb.dispatchEvent(new Event('change', { bubbles: true }));
            }
            formEl.style.opacity = '0.5';
            formEl.style.pointerEvents = 'none';
            formEl.classList.add(`${itemClass}--deleted`);
            formEl.style.display = 'none';
        } else {
            // Unsaved row: remove completely
            formEl.remove();
        }
    });

    // Update state and reindex if custom manager
    if (manager) {
        if (typeof manager.updateState === 'function') {
            try { manager.updateState(); } catch (e) {}
        }
        if (reindexMethod) {
            try { reindexMethod(); } catch (e) {}
        }
    }
}


function sg_fill_django_formset(prefix, dataArray, fieldMap) {
    let manager = null;
    let addMethod = null;
    let container = null;
    let managementForm = null;
    let updateIndicesMethod = null;
    let itemClass = 'form-item';

    if (window.formsetManagers && window.formsetManagers[prefix]) {
        manager = window.formsetManagers[prefix];
        addMethod = () => manager.addForm();
        container = manager.formsetContainer;
        managementForm = manager.managementForm;
        updateIndicesMethod = () => manager.updateFormIndices();
    } else if (prefix === 'subjects_tables' && window.subjectsManager) {
        manager = window.subjectsManager;
        addMethod = () => manager.addSubject();
        container = manager.container;
        managementForm = manager.totalFormsInput;
        updateIndicesMethod = () => manager.reindexForms();
        itemClass = 'subject-item';
    } else if (prefix === 'salary_tables' && window.salariesManager) {
        manager = window.salariesManager;
        addMethod = () => manager.addSalary();
        container = manager.container;
        managementForm = manager.totalFormsInput;
        updateIndicesMethod = () => manager.reindexForms();
        itemClass = 'salary-item';
    } else if (prefix === 'countries_tables' && window.countriesManager) {
        manager = window.countriesManager;
        addMethod = () => manager.addCountry();
        container = manager.container;
        managementForm = manager.totalFormsInput;
        updateIndicesMethod = () => manager.reindexForms();
        itemClass = 'country-item';
    }

    if (!manager || !container || !managementForm) {
        console.warn(`No manager found for formset prefix: ${prefix}`);
        return;
    }

    // Get all existing form rows in the container (excluding deleted ones)
    const existingForms = Array.from(container.querySelectorAll('[data-row-index]:not([class*="deleted"]), [data-form-index]:not([class*="deleted"])'));
    
    // We will reuse as many existing forms as needed, and add new ones if we need more.
    dataArray.forEach((item, index) => {
        let formEl;
        
        if (index < existingForms.length) {
            // Reuse existing form row
            formEl = existingForms[index];
        } else {
            // Add a new form row
            addMethod();
            const updatedForms = container.querySelectorAll('[data-row-index], [data-form-index]');
            formEl = updatedForms[updatedForms.length - 1];
        }
        
        // Ensure the form is visible and not marked for deletion
        const deleteCb = formEl.querySelector('input[name$="-DELETE"]');
        if (deleteCb) {
            deleteCb.checked = false;
            deleteCb.value = '';
            // Trigger change event to restore opacity/pointerEvents via formset-management handlers
            deleteCb.dispatchEvent(new Event('change', { bubbles: true }));
        }
        formEl.style.opacity = '1';
        formEl.style.pointerEvents = 'auto';
        formEl.classList.remove(`${itemClass}--deleted`);
        formEl.style.display = '';

        // Fill values according to the mapping
        for (const [wpKey, djangoField] of Object.entries(fieldMap)) {
            const input = formEl.querySelector(`[name$="-${djangoField}"]`);
            if (input) {
                input.value = item[wpKey] || '';
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
        
        // If there's a title preview helper, run it
        if (prefix === 'subjects_tables' && window.subjectsManager) {
            window.subjectsManager.updateSubjectPreview(formEl);
        } else if (prefix === 'salary_tables' && window.salariesManager) {
            window.salariesManager.updateSalaryPreview(formEl);
        } else if (prefix === 'countries_tables' && window.countriesManager) {
            window.countriesManager.updateDestinationPreview(formEl);
        }
    });

    // For any remaining existing forms that were not filled (reused), mark them for deletion
    if (existingForms.length > dataArray.length) {
        for (let i = dataArray.length; i < existingForms.length; i++) {
            const formEl = existingForms[i];
            const deleteCb = formEl.querySelector('input[name$="-DELETE"]');
            const idInput = formEl.querySelector('input[name$="-id"]');
            
            if (idInput && idInput.value) {
                // If it is a saved database record, mark it as deleted
                if (deleteCb) {
                    deleteCb.checked = true;
                    deleteCb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            } else {
                // If it's a new unsaved form, we can just remove it
                formEl.remove();
            }
        }
        // Update TOTAL_FORMS count
        const allForms = container.querySelectorAll('[data-row-index], [data-form-index]');
        managementForm.value = allForms.length;
        // Reindex form indices to keep them continuous
        updateIndicesMethod();
    }
}

/**
 * Shows the imported content warning banner
 */
function sg_show_import_banner(warnings, compiledPrompt) {
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

/**
 * Parses and maps manually pasted AI JSON response to form fields and formsets.
 */
function sg_apply_ai_response(aiResponse) {
    if (!aiResponse) return;
    
    // Parse form_initial fields dynamically
    const formInitial = {};
    for (const [key, val] of Object.entries(aiResponse)) {
        if (val !== null && typeof val !== 'object') {
            formInitial[key] = val;
        }
    }

    // Apply flat fields
    sg_fill_form(formInitial);

    // Apply formsets dynamically
    const importData = {};
    const arrayFields = [
        'subjects_tables', 'salary_tables', 'countries_tables',
        'faqs_data', 'faculties_data', 'courses_data', 'tuition_fees',
        'best_universities', 'cheap_universities'
    ];
    arrayFields.forEach(arr => {
        if (aiResponse[arr] !== undefined) {
            importData[arr] = aiResponse[arr];
        }
    });
    
    sg_fill_formsets(importData);
}
