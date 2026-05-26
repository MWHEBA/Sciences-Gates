/**
 * Paste Button Component
 * مكون زر لصق موحد قابل لإعادة الاستخدام في أي حقل نصي
 * 
 * الاستخدام:
 * 1. أضف class "paste-trigger" على أي حقل input أو textarea
 * 2. المكون سيضيف زر لصق تلقائياً بجانب الحقل
 * 
 * مثال:
 * <input type="text" class="paste-trigger" placeholder="اضغط على الزر للصق">
 * <textarea class="paste-trigger"></textarea>
 */

class PasteButton {
    constructor() {
        this.init();
    }

    init() {
        // البحث عن جميع الحقول التي تحتوي على class "paste-trigger"
        const fields = document.querySelectorAll('.paste-trigger');
        fields.forEach(field => {
            this.attachPasteButton(field);
        });

        // مراقبة الحقول الجديدة المضافة ديناميكياً
        this.observeNewFields();
    }

    attachPasteButton(field) {
        // تجنب إضافة الزر مرتين
        if (field.dataset.pasteButtonAttached) {
            return;
        }

        field.dataset.pasteButtonAttached = 'true';

        // إنشاء wrapper للحقل والزر
        const wrapper = document.createElement('div');
        wrapper.className = 'paste-button-wrapper';

        // إنشاء الزر
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'paste-button';
        button.title = 'اضغط للصق من الحافظة';
        button.innerHTML = `
            <svg class="paste-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
            </svg>
        `;

        // إضافة event listener للزر
        button.addEventListener('click', (e) => {
            e.preventDefault();
            this.handlePaste(field, button);
        });

        // اعتراض Ctrl+V / لصق يدوي وتنظيف النص تلقائياً
        if (field.getAttribute('data-paste-clean')) {
            field.addEventListener('paste', (e) => {
                const pastedText = (e.clipboardData || window.clipboardData).getData('text');
                if (pastedText) {
                    e.preventDefault();
                    const cleaned = this.cleanPastedText(field, pastedText);
                    field.value = cleaned;
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                    field.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });
        }

        // إدراج الزر بجانب الحقل
        field.parentNode.insertBefore(wrapper, field);
        wrapper.appendChild(field);
        wrapper.appendChild(button);
    }

    async handlePaste(field, button) {
        try {
            // محاولة قراءة من الحافظة
            let text = await navigator.clipboard.readText();
            
            // تنظيف النص حسب نوع الحقل
            text = this.cleanPastedText(field, text);
            
            // إدراج النص في الحقل
            field.value = text;
            
            // تشغيل event change لتحديث أي listeners
            field.dispatchEvent(new Event('change', { bubbles: true }));
            field.dispatchEvent(new Event('input', { bubbles: true }));
            
            // إظهار تأثير النجاح
            this.showSuccess(button);
            
            // التركيز على الحقل
            field.focus();
        } catch (err) {
            // معالجة الأخطاء
            if (err.name === 'NotAllowedError') {
                this.showError(button, 'لا توجد صلاحيات للوصول للحافظة');
            } else if (err.name === 'NotFoundError') {
                this.showError(button, 'الحافظة فارغة');
            } else {
                this.showError(button, 'حدث خطأ في اللصق');
            }
        }
    }

    /**
     * تنظيف النص الملصوق حسب نوع الحقل
     * إذا الحقل عنده data-paste-clean="slug" يتم:
     * 1- إزالة البروتوكول والدومين
     * 2- فك ترميز النصوص العربية المشفرة (percent-encoded)
     * 3- إزالة الـ slashes الزائدة
     */
    cleanPastedText(field, text) {
        const cleanType = field.getAttribute('data-paste-clean');
        
        if (cleanType === 'slug') {
            return this.cleanSlugUrl(text);
        }
        
        return text;
    }

    /**
     * تنظيف رابط ملصوق وتحويله لـ slug نظيف
     * مثال: https://sciencesgates.com/%d8%ac%d8%a7%d9%85%d8%b9%d8%a9-%d9%84%d9%8a%d9%86%d9%83%d9%88%d9%84%d9%86/
     * النتيجة: جامعة-لينكولن-ماليزيا
     */
    cleanSlugUrl(text) {
        let cleaned = text.trim();
        
        // إزالة البروتوكول (http:// أو https://)
        cleaned = cleaned.replace(/^https?:\/\//, '');
        
        // إزالة الدومين (كل شيء قبل أول /)
        const slashIndex = cleaned.indexOf('/');
        if (slashIndex !== -1) {
            cleaned = cleaned.substring(slashIndex + 1);
        } else {
            // لو مفيش / يعني ده مش رابط كامل، نرجعه زي ما هو
            // بس نحاول نفك الترميز برضو
            return this.decodeSlug(cleaned);
        }
        
        // إزالة الـ slashes من البداية والنهاية
        cleaned = cleaned.replace(/^\/+|\/+$/g, '');
        
        // لو فيه أجزاء متعددة (مسارات فرعية)، ناخد الجزء الأخير
        const parts = cleaned.split('/');
        cleaned = parts[parts.length - 1];
        
        // فك ترميز الـ percent-encoding (النصوص العربية المشفرة)
        cleaned = this.decodeSlug(cleaned);
        
        return cleaned;
    }

    /**
     * فك ترميز الـ slug (percent-encoded → نص عربي)
     */
    decodeSlug(text) {
        try {
            return decodeURIComponent(text);
        } catch (e) {
            // لو فشل الفك (ترميز غير صالح)، نرجع النص الأصلي
            return text;
        }
    }

    showSuccess(button) {
        const originalHTML = button.innerHTML;
        button.classList.add('paste-button-success');
        button.innerHTML = `
            <svg class="paste-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        `;

        // إعادة الزر للحالة الأصلية بعد 2 ثانية
        setTimeout(() => {
            button.classList.remove('paste-button-success');
            button.innerHTML = originalHTML;
        }, 2000);
    }

    showError(button, message) {
        const originalHTML = button.innerHTML;
        button.classList.add('paste-button-error');
        button.title = message;
        button.innerHTML = `
            <svg class="paste-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
        `;

        // إعادة الزر للحالة الأصلية بعد 2 ثانية
        setTimeout(() => {
            button.classList.remove('paste-button-error');
            button.innerHTML = originalHTML;
            button.title = 'اضغط للصق من الحافظة';
        }, 2000);
    }

    observeNewFields() {
        // استخدام MutationObserver لمراقبة الحقول الجديدة
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length) {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1) { // Element node
                            // البحث عن حقول جديدة
                            const newFields = node.querySelectorAll?.('.paste-trigger') || [];
                            newFields.forEach(field => {
                                if (!field.dataset.pasteButtonAttached) {
                                    this.attachPasteButton(field);
                                }
                            });

                            // التحقق من أن العقدة نفسها حقل
                            if (node.classList?.contains('paste-trigger') && !node.dataset.pasteButtonAttached) {
                                this.attachPasteButton(node);
                            }
                        }
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
}

// تهيئة المكون عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', () => {
    new PasteButton();
});

// إذا تم تحميل السكريبت بعد DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new PasteButton();
    });
} else {
    new PasteButton();
}
