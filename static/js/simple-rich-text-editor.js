/**
 * Simple Rich Text Editor
 * Supports: Bold, Italic, H2, H3, H4, UL, OL, Link
 * RTL Support: Full support for Arabic and RTL text
 */

class SimpleRichTextEditor {
    constructor(editorElement) {
        this.editor = editorElement;
        this.toolbar = null;
        this.contentArea = null;
        this.init();
    }

    init() {
        // Create toolbar
        this.createToolbar();
        
        // Make editor contenteditable
        this.editor.setAttribute('contenteditable', 'true');
        this.editor.setAttribute('dir', 'auto');
        this.editor.classList.add('rich-text-content');
        
        // Handle paste events to sanitize content
        this.editor.addEventListener('paste', (e) => this.handlePaste(e));
        
        // Sync content to hidden textarea
        this.editor.addEventListener('input', () => this.syncToTextarea());
        this.editor.addEventListener('blur', () => this.syncToTextarea());
    }

    createToolbar() {
        // Find or create toolbar container
        let toolbar = this.editor.previousElementSibling;
        if (!toolbar || !toolbar.classList.contains('rich-text-toolbar')) {
            toolbar = document.createElement('div');
            toolbar.classList.add('rich-text-toolbar');
            this.editor.parentNode.insertBefore(toolbar, this.editor);
        }
        
        this.toolbar = toolbar;
        
        // Clear existing buttons
        this.toolbar.innerHTML = '';
        
        // Define toolbar buttons
        const buttons = [
            { id: 'bold', label: 'غامق', icon: 'B', command: 'bold', title: 'غامق (Ctrl+B)' },
            { id: 'italic', label: 'مائل', icon: 'I', command: 'italic', title: 'مائل (Ctrl+I)' },
            { id: 'separator1', type: 'separator' },
            { id: 'h2', label: 'H2', icon: 'H2', command: 'formatBlock', value: '<h2>', title: 'عنوان 2' },
            { id: 'h3', label: 'H3', icon: 'H3', command: 'formatBlock', value: '<h3>', title: 'عنوان 3' },
            { id: 'h4', label: 'H4', icon: 'H4', command: 'formatBlock', value: '<h4>', title: 'عنوان 4' },
            { id: 'separator2', type: 'separator' },
            { id: 'ul', label: 'قائمة', icon: '•', command: 'insertUnorderedList', title: 'قائمة نقطية' },
            { id: 'ol', label: 'ترقيم', icon: '1.', command: 'insertOrderedList', title: 'قائمة مرقمة' },
            { id: 'separator3', type: 'separator' },
            { id: 'link', label: 'رابط', icon: '🔗', command: 'createLink', title: 'إدراج رابط' },
            { id: 'unlink', label: 'إزالة رابط', icon: '🔗✕', command: 'unlink', title: 'إزالة الرابط' },
            { id: 'separator4', type: 'separator' },
            { id: 'clear', label: 'مسح', icon: '✕', command: 'removeFormat', title: 'مسح التنسيق' },
        ];
        
        // Create buttons
        buttons.forEach(btn => {
            if (btn.type === 'separator') {
                const separator = document.createElement('div');
                separator.classList.add('toolbar-separator');
                this.toolbar.appendChild(separator);
            } else {
                const button = document.createElement('button');
                button.type = 'button';
                button.id = btn.id;
                button.className = 'toolbar-btn';
                button.title = btn.title;
                button.textContent = btn.icon;
                button.setAttribute('data-command', btn.command);
                if (btn.value) {
                    button.setAttribute('data-value', btn.value);
                }
                
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.executeCommand(btn.command, btn.value || null);
                    this.editor.focus();
                });
                
                this.toolbar.appendChild(button);
            }
        });
    }

    executeCommand(command, value) {
        // Focus editor before executing command
        this.editor.focus();
        
        if (command === 'createLink') {
            const selection = window.getSelection();
            let existingLink = null;
            if (selection && selection.rangeCount > 0) {
                let node = selection.anchorNode;
                while (node && node !== this.editor) {
                    if (node.nodeName === 'A') {
                        existingLink = node;
                        break;
                    }
                    node = node.parentNode;
                }
            }
            
            const defaultUrl = existingLink ? existingLink.getAttribute('href') : 'https://';
            const url = prompt('أدخل عنوان الرابط:', defaultUrl);
            
            if (url) {
                if (existingLink) {
                    existingLink.setAttribute('href', url);
                } else {
                    document.execCommand('createLink', false, url);
                }
            }
        } else if (command === 'formatBlock') {
            document.execCommand(command, false, value);
        } else {
            document.execCommand(command, false, null);
        }
        
        // Sync content after command
        this.syncToTextarea();
    }

    handlePaste(e) {
        e.preventDefault();
        
        // نحفظ الـ selection الحالية
        const sel = window.getSelection();
        if (!sel.rangeCount) return;
        const range = sel.getRangeAt(0);
        
        // نجيب الـ HTML أو النص العادي من الحافظة
        const html = e.clipboardData.getData('text/html');
        const text = e.clipboardData.getData('text/plain');
        
        let contentToInsert = '';
        
        if (html) {
            contentToInsert = this.sanitizeHtml(html);
        } else if (text) {
            // نص عادي — نحول الأسطر لـ <br>
            contentToInsert = text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/\n/g, '<br>');
        }
        
        if (contentToInsert) {
            range.deleteContents();
            const frag = document.createRange().createContextualFragment(contentToInsert);
            range.insertNode(frag);
            range.collapse(false);
            sel.removeAllRanges();
            sel.addRange(range);
        }
        
        // مزامنة مع الـ textarea
        this.syncToTextarea();
    }

    sanitizeHtml(html) {
        /**
         * تنظيف ذكي للـ HTML — يشيل شوائب اللصق من المصادر الخارجية
         * يحافظ على: b, strong, em, i, div, br, h2-h4, ul, ol, li, a
         * يشيل: span, font, style attributes, HTML comments, meta tags
         */
        
        // إزالة HTML comments (مثل <!--StartFragment-->)
        html = html.replace(/<!--[\s\S]*?-->/g, '');
        
        // إزالة opening/closing tags فقط (بدون محتواها) لـ html, head, body
        html = html.replace(/<\/?(html|head|body)[^>]*>/gi, '');
        
        // إزالة style, script بمحتواها + meta, link tags
        html = html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
        html = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
        html = html.replace(/<(meta|link|title)[^>]*\/?>/gi, '');
        html = html.replace(/<title[^>]*>[\s\S]*?<\/title>/gi, '');
        html = html.replace(/<!doctype[^>]*>/gi, '');
        
        const allowedTags = ['b', 'strong', 'em', 'i', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'a', 'br', 'div', 'p'];
        const unwrapTags = ['span', 'font', 'section', 'article', 'mark', 'small', 'big', 'center', 'abbr', 'code', 'pre', 'sub', 'sup'];
        const allowedAttributes = {
            'a': ['href', 'title', 'target', 'style', 'class'],
            'div': ['class', 'style', 'align', 'dir'],
            'p': ['class', 'style', 'align', 'dir'],
            'h2': ['class', 'style', 'align', 'dir'],
            'h3': ['class', 'style', 'align', 'dir'],
            'h4': ['class', 'style', 'align', 'dir'],
            'ul': ['class', 'style', 'align', 'dir'],
            'ol': ['class', 'style', 'align', 'dir'],
            'li': ['class', 'style', 'align', 'dir'],
        };
        
        // إنشاء عنصر مؤقت
        const temp = document.createElement('div');
        temp.innerHTML = html;
        
        // unwrap كل التاجات الزائدة بشكل آمن
        let unwrapFound = true;
        let safetyCounter = 0;
        while (unwrapFound && safetyCounter < 100) {
            safetyCounter++;
            unwrapFound = false;
            const allElements = temp.querySelectorAll('*');
            for (let i = 0; i < allElements.length; i++) {
                const el = allElements[i];
                const tag = el.tagName.toLowerCase();
                if (unwrapTags.includes(tag)) {
                    while (el.firstChild) {
                        el.parentNode.insertBefore(el.firstChild, el);
                    }
                    el.parentNode.removeChild(el);
                    unwrapFound = true;
                    break;
                }
            }
        }
        
        // تنظيف التاجات والـ attributes
        this.cleanElement(temp, allowedTags, allowedAttributes);
        
        return temp.innerHTML;
    }

    cleanElement(element, allowedTags, allowedAttributes) {
        /**
         * تنظيف تكراري — يشيل التاجات الغير مسموحة والـ attributes الزائدة
         */
        const children = Array.from(element.childNodes);
        
        for (let node of children) {
            // إزالة الـ comments
            if (node.nodeType === Node.COMMENT_NODE) {
                element.removeChild(node);
                continue;
            }
            
            if (node.nodeType === Node.ELEMENT_NODE) {
                const tagName = node.tagName.toLowerCase();
                
                // تاجات غير مسموحة — نحولها لنص
                if (!allowedTags.includes(tagName)) {
                    const textNode = document.createTextNode(node.textContent);
                    element.replaceChild(textNode, node);
                    continue;
                }
                
                // إزالة كل الـ attributes الغير مسموحة (بما فيها style)
                const allowedAttrs = allowedAttributes[tagName] || [];
                const attrsToRemove = [];
                for (let attr of node.attributes) {
                    if (!allowedAttrs.includes(attr.name)) {
                        attrsToRemove.push(attr.name);
                    }
                }
                attrsToRemove.forEach(attr => node.removeAttribute(attr));
                
                // التحقق من أمان الروابط
                if (tagName === 'a' && node.hasAttribute('href')) {
                    const href = node.getAttribute('href');
                    if (!this.isValidUrl(href)) {
                        node.removeAttribute('href');
                    }
                }
                
                // تحويل <p> لـ <div>
                if (tagName === 'p') {
                    const div = document.createElement('div');
                    Array.from(node.attributes).forEach(attr => {
                        div.setAttribute(attr.name, attr.value);
                    });
                    while (node.firstChild) {
                        div.appendChild(node.firstChild);
                    }
                    element.replaceChild(div, node);
                    this.cleanElement(div, allowedTags, allowedAttributes);
                    continue;
                }
                
                // تنظيف الأولاد
                this.cleanElement(node, allowedTags, allowedAttributes);
            }
        }
    }

    isValidUrl(url) {
        /**
         * Check if URL is valid and safe
         */
        try {
            // Allow relative URLs and safe protocols
            if (url.startsWith('/') || url.startsWith('#')) {
                return true;
            }
            
            const urlObj = new URL(url);
            const safeProtocols = ['http:', 'https:', 'mailto:'];
            return safeProtocols.includes(urlObj.protocol);
        } catch (e) {
            return false;
        }
    }

    syncToTextarea() {
        /**
         * Sync contenteditable content to hidden textarea
         */
        const textarea = this.editor.nextElementSibling;
        if (textarea && textarea.tagName === 'TEXTAREA') {
            textarea.value = this.editor.innerHTML;
        }
    }

    getContent() {
        /**
         * Get sanitized content from editor
         */
        return this.sanitizeHtml(this.editor.innerHTML);
    }

    setContent(html) {
        /**
         * Set content in editor
         */
        this.editor.innerHTML = this.sanitizeHtml(html);
        this.syncToTextarea();
    }

    clear() {
        /**
         * Clear editor content
         */
        this.editor.innerHTML = '';
        this.syncToTextarea();
    }
}

// Initialize editors when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Find all elements with class 'simple-rich-text-editor'
    const editors = document.querySelectorAll('.simple-rich-text-editor');
    
    editors.forEach(editor => {
        // Skip if already initialized
        if (!editor.hasAttribute('data-editor-initialized')) {
            new SimpleRichTextEditor(editor);
            editor.setAttribute('data-editor-initialized', 'true');
        }
    });
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SimpleRichTextEditor;
}
