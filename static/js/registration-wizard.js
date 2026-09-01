/**
 * Registration Wizard Controller
 * Handles client-side step validation, inline error highlighting,
 * Eastern Arabic numeral conversion, phone number normalization,
 * Submit lock recovery, and smooth step navigation.
 */
(function () {
    'use strict';

    // Helper to convert Eastern Arabic numerals (٠-٩) and Persian numerals (۰-۹) to standard ASCII (0-9)
    function convertArabicNumerals(str) {
        if (!str) return '';
        return str
            .replace(/[٠-٩]/g, function (d) {
                return String.fromCharCode(d.charCodeAt(0) - 1632 + 48);
            })
            .replace(/[۰-۹]/g, function (d) {
                return String.fromCharCode(d.charCodeAt(0) - 1776 + 48);
            });
    }

    // Helper to display inline error message
    function setFieldError(fieldId, errorMsg) {
        var field = document.getElementById(fieldId);
        var errorContainer = document.getElementById(fieldId + '_error');
        if (field) {
            field.classList.add('reg-input--invalid');
        }
        if (errorContainer) {
            errorContainer.textContent = errorMsg;
            errorContainer.style.display = 'block';
        }
    }

    // Helper to clear inline error message
    function clearFieldError(fieldId) {
        var field = document.getElementById(fieldId);
        var errorContainer = document.getElementById(fieldId + '_error');
        if (field) {
            field.classList.remove('reg-input--invalid');
        }
        if (errorContainer) {
            errorContainer.textContent = '';
            errorContainer.style.display = 'none';
        }
    }

    // Clear all step 1 errors
    function clearStep1Errors() {
        clearFieldError('reg_name');
        clearFieldError('reg_email');
        clearFieldError('reg_phone');
        clearFieldError('reg_nationality');
        clearFieldError('reg_custom_nationality');
    }

    // Clear all step 2 errors
    function clearStep2Errors() {
        clearFieldError('reg_level');
        clearFieldError('reg_residence');
        clearFieldError('reg_address');
    }

    // Helper to reset submit button state on validation failure
    function resetSubmitButtonState() {
        var form = document.getElementById('regWizardForm');
        if (form) {
            form.removeAttribute('data-submitting');
        }
        var submitBtn = document.getElementById('regSubmitBtn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.style.pointerEvents = '';
            submitBtn.style.opacity = '';
            submitBtn.style.cursor = '';
            submitBtn.innerHTML = 'إرسال طلب التسجيل';
        }
    }

    // Step 1 Validation (Pure inline feedback, no browser alerts)
    window.validateRegistrationStep1 = function () {
        clearStep1Errors();
        var isValid = true;
        var firstInvalidField = null;

        var nameInput = document.getElementById('reg_name');
        var emailInput = document.getElementById('reg_email');
        var phoneInput = document.getElementById('reg_phone');
        var nationalitySelect = document.getElementById('reg_nationality');
        var customNatInput = document.getElementById('reg_custom_nationality');

        var nameVal = (nameInput ? nameInput.value : '').trim();
        var emailVal = (emailInput ? emailInput.value : '').trim();
        var rawPhone = (phoneInput ? phoneInput.value : '').trim();
        var phoneVal = convertArabicNumerals(rawPhone);
        if (phoneInput && rawPhone !== phoneVal) {
            phoneInput.value = phoneVal;
        }

        var nationalityVal = (nationalitySelect ? nationalitySelect.value : '').trim();

        // 1. Name validation
        if (!nameVal) {
            setFieldError('reg_name', 'يرجى إدخال اسم الطالب الكامل.');
            isValid = false;
            if (!firstInvalidField) firstInvalidField = nameInput;
        } else if (nameVal.length < 3) {
            setFieldError('reg_name', 'اسم الطالب يجب أن يكون 3 أحرف على الأقل.');
            isValid = false;
            if (!firstInvalidField) firstInvalidField = nameInput;
        }

        // 2. Email validation
        if (!emailVal) {
            setFieldError('reg_email', 'يرجى إدخال البريد الإلكتروني.');
            isValid = false;
            if (!firstInvalidField) firstInvalidField = emailInput;
        } else {
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(emailVal)) {
                setFieldError('reg_email', 'صيغة البريد الإلكتروني غير صحيحة.');
                isValid = false;
                if (!firstInvalidField) firstInvalidField = emailInput;
            } else if (/^(test|spam|fake|temp|dummy)@/i.test(emailVal)) {
                setFieldError('reg_email', 'يرجى إدخال بريد إلكتروني حقيقي للتواصل.');
                isValid = false;
                if (!firstInvalidField) firstInvalidField = emailInput;
            }
        }

        // 3. Phone validation
        if (!phoneVal) {
            setFieldError('reg_phone', 'يرجى إدخال رقم الهاتف.');
            isValid = false;
            if (!firstInvalidField) firstInvalidField = phoneInput;
        } else {
            var cleanDigits = phoneVal.replace(/\D/g, '');
            if (cleanDigits.length < 6) {
                setFieldError('reg_phone', 'رقم الهاتف قصير جداً، يرجى كتابة الرقم كاملاً.');
                isValid = false;
                if (!firstInvalidField) firstInvalidField = phoneInput;
            }
        }

        // 4. Nationality validation
        if (!nationalityVal) {
            setFieldError('reg_nationality', 'يرجى اختيار الجنسية.');
            isValid = false;
            if (!firstInvalidField) firstInvalidField = nationalitySelect;
        } else if (['دولة اخرى غير موجودة', 'دولة أخرى غير موجودة', 'دولة أخرى', 'أخرى'].indexOf(nationalityVal) !== -1) {
            var customVal = (customNatInput ? customNatInput.value : '').trim();
            if (!customVal) {
                setFieldError('reg_custom_nationality', 'يرجى كتابة اسم الدولة أو الجنسية.');
                isValid = false;
                if (!firstInvalidField) firstInvalidField = customNatInput;
            }
        }

        if (!isValid && firstInvalidField) {
            if (typeof firstInvalidField.scrollIntoView === 'function') {
                firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            firstInvalidField.focus();
        }

        return isValid;
    };

    // Step 2 Validation (Pure inline feedback, no browser alerts)
    window.validateRegistrationStep2 = function () {
        clearStep2Errors();
        var isValid = true;
        var firstInvalidField = null;

        var levelSelect = document.getElementById('reg_level');
        var residenceSelect = document.getElementById('reg_residence');
        var addressInput = document.getElementById('reg_address');

        var levelVal = (levelSelect ? levelSelect.value : '').trim();
        var residenceVal = (residenceSelect ? residenceSelect.value : '').trim();
        var addressVal = (addressInput ? addressInput.value : '').trim();

        // 1. Level validation
        if (!levelVal) {
            setFieldError('reg_level', 'يرجى اختيار المرحلة الدراسية.');
            isValid = false;
            if (!firstInvalidField) firstInvalidField = levelSelect;
        }

        // 2. Residence country validation
        if (!residenceVal) {
            setFieldError('reg_residence', 'يرجى اختيار دولة الإقامة الحالية.');
            isValid = false;
            if (!firstInvalidField) firstInvalidField = residenceSelect;
        }

        // 3. Address / City validation
        if (!addressVal) {
            setFieldError('reg_address', 'يرجى كتابة المدينة أو العنوان الحالي.');
            isValid = false;
            if (!firstInvalidField) firstInvalidField = addressInput;
        }

        if (!isValid && firstInvalidField) {
            if (typeof firstInvalidField.scrollIntoView === 'function') {
                firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            firstInvalidField.focus();
        }

        return isValid;
    };

    // Backward compatibility aliases
    window.validateStep1 = window.validateRegistrationStep1;
    window.validateStep2 = window.validateRegistrationStep2;

    // Attach real-time input error clearing and enter key interception
    function initRegistrationWizard() {
        var form = document.getElementById('regWizardForm');
        if (!form) return;

        // Auto-clear errors on typing
        var inputIds = [
            'reg_name', 'reg_email', 'reg_phone',
            'reg_nationality', 'reg_custom_nationality',
            'reg_level', 'reg_residence', 'reg_address'
        ];

        inputIds.forEach(function (id) {
            var el = document.getElementById(id);
            if (el) {
                el.addEventListener('input', function () {
                    clearFieldError(id);
                });
                el.addEventListener('change', function () {
                    clearFieldError(id);
                });
            }
        });

        // Convert Arabic numerals in real time on phone input
        var phoneInput = document.getElementById('reg_phone');
        if (phoneInput) {
            phoneInput.addEventListener('input', function () {
                var converted = convertArabicNumerals(this.value);
                if (this.value !== converted) {
                    this.value = converted;
                }
            });
        }

        // Intercept Enter key on Step 1 inputs to smoothly advance to Step 2
        var step1Inputs = form.querySelectorAll('#reg_name, #reg_email, #reg_phone, #reg_custom_nationality');
        step1Inputs.forEach(function (input) {
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    var nextBtn = document.getElementById('regNextBtn');
                    if (nextBtn) {
                        nextBtn.click();
                    } else if (window.validateRegistrationStep1()) {
                        var alpineContainer = form.closest('[x-data]');
                        if (alpineContainer && alpineContainer.__x && alpineContainer.__x.$data) {
                            alpineContainer.__x.$data.regStep = 2;
                            var scrollContainer = form.querySelector('.reg-modal-scrollable');
                            if (scrollContainer) scrollContainer.scrollTop = 0;
                        }
                    }
                }
            });
        });

        // Form Submit Handler
        form.addEventListener('submit', function (e) {
            // Live CSRF Synchronization
            if (typeof window.syncAllFormsCsrf === 'function') {
                window.syncAllFormsCsrf();
            }

            var s1Valid = window.validateRegistrationStep1();
            if (!s1Valid) {
                e.preventDefault();
                var alpineContainer = form.closest('[x-data]');
                if (alpineContainer && alpineContainer.__x && alpineContainer.__x.$data) {
                    alpineContainer.__x.$data.regStep = 1;
                }
                resetSubmitButtonState();
                return false;
            }

            var s2Valid = window.validateRegistrationStep2();
            if (!s2Valid) {
                e.preventDefault();
                var alpineContainer = form.closest('[x-data]');
                if (alpineContainer && alpineContainer.__x && alpineContainer.__x.$data) {
                    alpineContainer.__x.$data.regStep = 2;
                }
                resetSubmitButtonState();
                return false;
            }

            // Normalization: Combine country code and phone number (stripping non-digits and leading zeros)
            var hiddenCode = document.getElementById('reg_country_code') || form.querySelector('input[name="country_code"]');
            var combinedPhone = document.getElementById('reg_phone_combined') || form.querySelector('input[name="phone"]');

            if (phoneInput && combinedPhone) {
                var codeVal = hiddenCode ? hiddenCode.value.trim() : '+60';
                var cleanPhone = convertArabicNumerals(phoneInput.value).replace(/\D/g, '').replace(/^0+/, '');
                combinedPhone.value = codeVal + cleanPhone;
            }

            // Build structured summary message
            var nationality = (document.getElementById('reg_nationality') || {}).value || '';
            var customNat = (document.getElementById('reg_custom_nationality') || {}).value || '';
            if (['دولة اخرى غير موجودة', 'دولة أخرى غير موجودة', 'دولة أخرى', 'أخرى'].indexOf(nationality) !== -1 && customNat.trim()) {
                nationality = customNat.trim() + ' (دولة أخرى)';
            }

            var level = (document.getElementById('reg_level') || {}).value || '';
            var residence = (document.getElementById('reg_residence') || {}).value || '';
            var address = (document.getElementById('reg_address') || {}).value || '';
            var notes = (document.getElementById('reg_notes') || {}).value || '';
            var messageInput = document.getElementById('reg_combined_message') || form.querySelector('input[name="message"]');
            if (messageInput) {
                messageInput.value = notes ? notes.trim() : '';
            }

            // Set loading button visual state
            var submitBtn = document.getElementById('regSubmitBtn');
            if (submitBtn) {
                submitBtn.style.pointerEvents = 'none';
                submitBtn.style.opacity = '0.7';
                submitBtn.innerHTML = '⏳ جاري إرسال طلب التسجيل...';
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initRegistrationWizard);
    } else {
        initRegistrationWizard();
    }
})();
