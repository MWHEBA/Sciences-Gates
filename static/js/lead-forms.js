/**
 * Lead Forms Submissions Controller (Phase 3)
 * Unified AJAX / Fetch submission handler for all lead generation forms across Sciences Gates.
 * 
 * Features:
 * - Real-time Eastern Arabic (٠-٩) and Persian (۰-۹) digit normalization on phone fields.
 * - Combining country_code + phone_number into phone before submission.
 * - Client-side validation with inline error rendering and auto-focusing on first invalid field.
 * - Submitting via standard Fetch API with CSRF token and X-Requested-With header.
 * - JSON response handling: 200 (redirect), 400 (inline validation errors), 429 (rate limit banner).
 * - Automatic CSRF error retry (403): re-syncs fresh csrftoken and retries submission once.
 * - Watchdog timer (12s) to prevent frozen submit buttons on network stalls.
 * - Modal preservation: keeps multi-step registration modal open on validation error without page reload.
 */

(function () {
    'use strict';

    // Helper to convert Eastern Arabic and Persian numerals to standard ASCII (0-9)
    function convertArabicNumerals(str) {
        if (!str) return '';
        return String(str)
            .replace(/[٠-٩]/g, function (d) {
                return String.fromCharCode(d.charCodeAt(0) - 1632 + 48);
            })
            .replace(/[۰-۹]/g, function (d) {
                return String.fromCharCode(d.charCodeAt(0) - 1776 + 48);
            });
    }

    // Helper to read cookie by name
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Helper to find or create an inline error slot (.form-error) for standard forms
    function getErrorSlot(field, create) {
        if (!field) return null;
        var anchor = field.closest('.intl-phone-wrapper') || field;
        var slot = anchor.nextElementSibling;
        if (slot && slot.classList && slot.classList.contains('form-error')) {
            return slot;
        }
        if (!create) return null;
        slot = document.createElement('p');
        slot.className = 'form-error';
        slot.setAttribute('role', 'alert');
        slot.dataset.autoError = 'true';
        slot.style.display = 'none';
        anchor.insertAdjacentElement('afterend', slot);
        return slot;
    }

    // Helper to show inline error for a field
    function showFieldError(field, message) {
        if (!field) return;
        field.classList.add('is-invalid');
        field.classList.add('reg-input--invalid');
        
        // Check for wizard-specific error container first (reg_fieldname_error)
        var wizardError = document.getElementById(field.id + '_error');
        if (wizardError) {
            wizardError.textContent = message;
            wizardError.style.display = 'block';
            return;
        }

        var slot = getErrorSlot(field, true);
        if (slot) {
            slot.textContent = message;
            slot.style.display = 'block';
        }
    }

    // Helper to clear error for a field
    function clearFieldError(field) {
        if (!field) return;
        field.classList.remove('is-invalid');
        field.classList.remove('reg-input--invalid');

        var wizardError = document.getElementById(field.id + '_error');
        if (wizardError) {
            wizardError.textContent = '';
            wizardError.style.display = 'none';
        }

        var slot = getErrorSlot(field, false);
        if (slot) {
            slot.textContent = '';
            slot.style.display = 'none';
        }
    }

    // Clear all inline errors in a form
    function clearAllErrors(form) {
        if (!form) return;
        form.querySelectorAll('.is-invalid, .reg-input--invalid').forEach(function (el) {
            el.classList.remove('is-invalid');
            el.classList.remove('reg-input--invalid');
        });
        form.querySelectorAll('.form-error, .reg-field-error').forEach(function (el) {
            el.textContent = '';
            el.style.display = 'none';
        });
        var banner = form.querySelector('.lead-form-alert');
        if (banner) {
            banner.remove();
        }
    }

    // Helper to display top banner alert in form
    function showFormAlert(form, message, type) {
        if (!form) return;
        var existing = form.querySelector('.lead-form-alert');
        if (existing) existing.remove();

        var alert = document.createElement('div');
        alert.className = 'lead-form-alert alert alert--' + (type || 'error');
        alert.setAttribute('role', 'alert');
        alert.style.margin = '0 0 1rem 0';
        alert.style.padding = '0.75rem 1rem';
        alert.style.borderRadius = 'var(--radius-sm, 6px)';
        alert.style.fontSize = '0.875rem';
        alert.textContent = message;

        form.insertBefore(alert, form.firstChild);
        if (typeof alert.scrollIntoView === 'function') {
            alert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    // Unlock form and its submit buttons
    function unlockLeadForm(form) {
        if (!form) return;
        form.removeAttribute('data-submitting');
        if (typeof window.unlockForm === 'function') {
            window.unlockForm(form);
        } else {
            var submitBtns = form.querySelectorAll('button[type="submit"], input[type="submit"]');
            submitBtns.forEach(function (btn) {
                btn.disabled = false;
                btn.style.pointerEvents = '';
                btn.style.opacity = '';
                btn.style.cursor = '';
                btn.classList.remove('is-loading');
                var originalText = btn.getAttribute('data-original-text');
                if (originalText) {
                    btn.innerHTML = originalText;
                }
            });
        }
    }

    // Lock form and submit buttons with loading indicator
    function lockLeadForm(form) {
        if (!form) return;
        form.dataset.submitting = 'true';
        var submitBtns = form.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitBtns.forEach(function (btn) {
            if (!btn.hasAttribute('data-original-text')) {
                btn.setAttribute('data-original-text', btn.innerHTML || btn.value);
            }
            btn.style.pointerEvents = 'none';
            btn.style.opacity = '0.7';
            btn.style.cursor = 'wait';
            btn.classList.add('is-loading');
            btn.innerHTML = '<span style="opacity:0.85">⏳ جاري الإرسال...</span>';
        });
    }

    // Attach real-time input numeral conversion and error clearance
    function setupFormInputs(form) {
        var phoneInputs = form.querySelectorAll('input[type="tel"], input[name="phone_number"], input[name="phone"]');
        phoneInputs.forEach(function (input) {
            input.addEventListener('input', function () {
                var converted = convertArabicNumerals(this.value);
                if (this.value !== converted) {
                    this.value = converted;
                }
                clearFieldError(this);
            });
        });

        var allInputs = form.querySelectorAll('input, select, textarea');
        allInputs.forEach(function (input) {
            input.addEventListener('input', function () {
                clearFieldError(this);
            });
            input.addEventListener('change', function () {
                clearFieldError(this);
            });
        });
    }

    // Combine phone number components before payload serialization
    function ensureCombinedPhone(form) {
        var phoneInput = form.querySelector('input[name="phone_number"]');
        var hiddenCode = form.querySelector('input[name="country_code"]');
        var combinedPhone = form.querySelector('input[name="phone"]');

        if (phoneInput && combinedPhone) {
            var rawVal = convertArabicNumerals(phoneInput.value).trim();
            var cleanDigits = rawVal.replace(/\D/g, '').replace(/^0+/, '');
            var codeVal = hiddenCode ? hiddenCode.value.trim() : '+60';
            if (cleanDigits) {
                combinedPhone.value = codeVal + cleanDigits;
            } else {
                combinedPhone.value = '';
            }
        }
    }

    // Handle AJAX Fetch submission
    function handleLeadFormSubmit(form, e, isRetry) {
        e.preventDefault();
        e.stopPropagation();

        if (form.dataset.submitting === 'true' && !isRetry) {
            return false;
        }

        // Live CSRF token sync before creating FormData
        if (typeof window.syncAllFormsCsrf === 'function') {
            window.syncAllFormsCsrf();
        }

        // Combine country code + phone number
        ensureCombinedPhone(form);

        // Wizard-specific client-side step validation if available
        if (form.id === 'regWizardForm') {
            if (typeof window.validateRegistrationStep1 === 'function' && !window.validateRegistrationStep1()) {
                var alpineContainer = form.closest('[x-data]');
                if (alpineContainer && alpineContainer.__x && alpineContainer.__x.$data) {
                    alpineContainer.__x.$data.regStep = 1;
                }
                unlockLeadForm(form);
                return false;
            }
            if (typeof window.validateRegistrationStep2 === 'function' && !window.validateRegistrationStep2()) {
                var alpineCont = form.closest('[x-data]');
                if (alpineCont && alpineCont.__x && alpineCont.__x.$data) {
                    alpineCont.__x.$data.regStep = 2;
                }
                unlockLeadForm(form);
                return false;
            }
        } else {
            // General required fields check
            var isValid = true;
            var firstInvalid = null;
            var requiredInputs = form.querySelectorAll('[required]');
            requiredInputs.forEach(function (field) {
                if (!field.value || !field.value.trim()) {
                    isValid = false;
                    if (!firstInvalid) firstInvalid = field;
                    showFieldError(field, 'هذا الحقل مطلوب.');
                }
            });

            if (!isValid) {
                if (firstInvalid && typeof firstInvalid.focus === 'function') {
                    if (typeof firstInvalid.scrollIntoView === 'function') {
                        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                    firstInvalid.focus();
                }
                unlockLeadForm(form);
                return false;
            }
        }

        // Lock form with loading indicator
        lockLeadForm(form);

        // 12s Watchdog timer
        var watchdog = setTimeout(function () {
            if (document.body.contains(form) && form.dataset.submitting === 'true') {
                unlockLeadForm(form);
                showFormAlert(form, 'استغرقت عملية الإرسال وقتاً أطول من المعتاد. يرجى التحقق من اتصالك بالإنترنت وإعادة المحاولة.', 'error');
            }
        }, 12000);

        var formData = new FormData(form);
        var csrfToken = getCookie('csrftoken') || (form.querySelector('input[name="csrfmiddlewaretoken"]') ? form.querySelector('input[name="csrfmiddlewaretoken"]').value : '');

        var submitUrl = form.getAttribute('action') || '/leads/submit/';

        fetch(submitUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin'
        })
        .then(function (response) {
            clearTimeout(watchdog);
            return response.json().then(function (data) {
                return { status: response.status, ok: response.ok, data: data };
            }).catch(function () {
                return { status: response.status, ok: response.ok, data: null };
            });
        })
        .then(function (result) {
            var status = result.status;
            var data = result.data;

            // 1. Success (200 / 201)
            if (result.ok && data && data.success) {
                var redirectUrl = data.redirect_url || '/leads/thank-you/';
                // Remove local draft
                try {
                    var formKey = 'sg_lead_draft_' + window.location.pathname.split('/').join('_');
                    localStorage.removeItem(formKey);
                } catch (e) {}

                window.location.href = redirectUrl;
                return;
            }

            // 2. CSRF Failure (403) -> Retry once with fresh token
            if (status === 403 && !isRetry) {
                if (typeof window.syncAllFormsCsrf === 'function') {
                    window.syncAllFormsCsrf();
                }
                setTimeout(function () {
                    handleLeadFormSubmit(form, e, true);
                }, 300);
                return;
            }

            // 3. Rate Limited (429)
            if (status === 429 || (data && data.rate_limit)) {
                unlockLeadForm(form);
                var rateMsg = (data && data.message) ? data.message : 'تم تجاوز الحد المسموح به من الطلبات خلال الساعة الأخيرة لحماية الخدمة.';
                showFormAlert(form, rateMsg, 'error');
                return;
            }

            // 4. Validation Error (400)
            if (status === 400 && data && data.errors) {
                unlockLeadForm(form);
                var firstInvalidField = null;
                var errorKeys = Object.keys(data.errors);

                errorKeys.forEach(function (fieldKey) {
                    var errArr = data.errors[fieldKey];
                    var errMsg = (errArr && errArr.length && errArr[0].message) ? errArr[0].message : 'يرجى تصحيح هذا الحقل.';

                    // Find matching input element
                    var inputEl = form.querySelector('[name="' + fieldKey + '"]');
                    if (fieldKey === 'phone') {
                        inputEl = form.querySelector('[name="phone_number"]') || inputEl;
                    }
                    if (inputEl) {
                        showFieldError(inputEl, errMsg);
                        if (!firstInvalidField) firstInvalidField = inputEl;
                    }
                });

                var generalMsg = data.message || 'حدث خطأ في النموذج. يرجى التحقق من البيانات المدخلة.';
                showFormAlert(form, generalMsg, 'error');

                if (firstInvalidField) {
                    // If in wizard, step navigation
                    if (form.id === 'regWizardForm') {
                        var isStep1Field = ['name', 'email', 'phone', 'phone_number', 'nationality', 'custom_nationality'].indexOf(firstInvalidField.name) !== -1;
                        var alpineModal = form.closest('[x-data]');
                        if (alpineModal && alpineModal.__x && alpineModal.__x.$data) {
                            alpineModal.__x.$data.regStep = isStep1Field ? 1 : 2;
                        }
                    }
                    if (typeof firstInvalidField.scrollIntoView === 'function') {
                        firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                    firstInvalidField.focus();
                }
                return;
            }

            // 5. General / Unexpected error
            unlockLeadForm(form);
            var errMessage = (data && data.message) ? data.message : 'حدث خطأ غير متوقع أثناء إرسال البيانات. يرجى المحاولة مرة أخرى.';
            showFormAlert(form, errMessage, 'error');
        })
        .catch(function (error) {
            clearTimeout(watchdog);
            unlockLeadForm(form);
            showFormAlert(form, 'تعذر الاتصال بالخادم. يرجى التحقق من اتصال الإنترنت والمحاولة مرة أخرى.', 'error');
        });
    }

    // Initialize all lead forms on DOM ready
    function initLeadForms() {
        var leadForms = document.querySelectorAll('form[data-lead-form], form[action*="/leads/submit"], form[action*="leads:submit"], form[id="regWizardForm"]');
        leadForms.forEach(function (form) {
            if (form.dataset.leadFormInit === 'true') return;
            form.dataset.leadFormInit = 'true';

            setupFormInputs(form);

            // Intercept form submit
            form.addEventListener('submit', function (e) {
                handleLeadFormSubmit(form, e, false);
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLeadForms);
    } else {
        initLeadForms();
    }

    // Expose utility to window
    window.initLeadForms = initLeadForms;
})();
