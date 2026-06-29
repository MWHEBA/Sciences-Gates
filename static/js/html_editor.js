/**
 * Professional HTML Editor — Sciences Gates Dashboard
 * Features: Bold, Italic, Underline, Strikethrough, H2-H4, UL, OL,
 *           Blockquote, Link, Unlink, Undo, Redo, Clear Format
 * RTL Support: Full Arabic/RTL support
 * Keyboard Shortcuts: Ctrl+B, Ctrl+I, Ctrl+U, Ctrl+Z, Ctrl+Y
 */

class ProfessionalHTMLEditor {
    constructor(containerElement) {
        this.container = containerElement;
        this.container.editorInstance = this;
        this.editorArea = null;
        this.hiddenTextarea = null;
        this.toolbar = null;
        this.activeButtons = new Set();
        this.undoStack = [];
        this.redoStack = [];
        this._init();
    }

    // ─── SVG Icons ────────────────────────────────────────────────────────────
    static ICONS = {
        bold: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/><path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/></svg>`,
        italic: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="4" x2="10" y2="4"/><line x1="14" y1="20" x2="5" y2="20"/><line x1="15" y1="4" x2="9" y2="20"/></svg>`,
        underline: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"/><line x1="4" y1="21" x2="20" y2="21"/></svg>`,
        strikethrough: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17.3 12H6.7"/><path d="M10 7.5c0-1.4 1.3-2.5 3-2.5s3 1.1 3 2.5"/><path d="M7 16.5c0 1.4 1.3 2.5 3 2.5h4c1.7 0 3-1.1 3-2.5"/></svg>`,
        h2: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h8"/><path d="M4 6v12"/><path d="M12 6v12"/><path d="M21 18h-4c0-4 4-3 4-6 0-1.5-1-2-2-2s-2 .5-2 2"/></svg>`,
        h3: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h8"/><path d="M4 6v12"/><path d="M12 6v12"/><path d="M17.5 10.5c1.7-1 3.5 0 3.5 1.5a2 2 0 0 1-2 2"/><path d="M17 16.5c2 1.5 4 .3 4-1.5a2 2 0 0 0-2-2"/></svg>`,
        h4: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h8"/><path d="M4 6v12"/><path d="M12 6v12"/><path d="M17 10v4h4"/><path d="M21 10v8"/></svg>`,
        ul: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="9" y1="6" x2="20" y2="6"/><line x1="9" y1="12" x2="20" y2="12"/><line x1="9" y1="18" x2="20" y2="18"/><circle cx="4" cy="6" r="1" fill="currentColor" stroke="none"/><circle cx="4" cy="12" r="1" fill="currentColor" stroke="none"/><circle cx="4" cy="18" r="1" fill="currentColor" stroke="none"/></svg>`,
        ol: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="10" y1="6" x2="21" y2="6"/><line x1="10" y1="12" x2="21" y2="12"/><line x1="10" y1="18" x2="21" y2="18"/><path d="M4 6h1v4"/><path d="M4 10h2"/><path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"/></svg>`,
        blockquote: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"/><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"/></svg>`,
        link: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>`,
        unlink: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.84 12.25l1.72-1.71h-.02a5.004 5.004 0 0 0-.12-7.07 5.006 5.006 0 0 0-6.95 0l-1.72 1.71"/><path d="M5.17 11.75l-1.71 1.71a5.004 5.004 0 0 0 .12 7.07 5.006 5.006 0 0 0 6.95 0l1.72-1.71"/><line x1="8" y1="2" x2="8" y2="5"/><line x1="2" y1="8" x2="5" y2="8"/><line x1="16" y1="19" x2="16" y2="22"/><line x1="19" y1="16" x2="22" y2="16"/></svg>`,
        undo: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/></svg>`,
        redo: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 7v6h-6"/><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13"/></svg>`,
        alignRight: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="21" y1="10" x2="7" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="21" y1="18" x2="7" y2="18"/></svg>`,
        alignCenter: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="10" x2="6" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="18" y1="18" x2="6" y2="18"/></svg>`,
        alignLeft: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="10" x2="17" y2="10"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="14" x2="21" y2="14"/><line x1="3" y1="18" x2="17" y2="18"/></svg>`,
        alignJustify: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="21" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="21" y1="18" x2="3" y2="18"/></svg>`,
        eye: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`,
        code: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
        rtl: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4H9.5a3.5 3.5 0 0 0 0 7H12"/><path d="M12 4v16"/><path d="M16 4v16"/><path d="M2 12l4 4-4 4"/></svg>`,
        ltr: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H6.5a3.5 3.5 0 0 0 0 7H9"/><path d="M9 4v16"/><path d="M13 4v16"/><path d="M22 12l-4 4 4 4"/></svg>`,
        image: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>`,
        clear: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/><line x1="2" y1="2" x2="22" y2="22"/></svg>`,
        fontSize: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M9 17h6"/><path d="M6 4v14"/><path d="M18 4v14"/></svg>`,
        fontColor: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M9 17h6"/><path d="M6 4v14"/><path d="M18 4v14"/><line x1="3" y1="20" x2="21" y2="20" stroke="currentColor" stroke-width="3"/></svg>`,
        table: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>`,
        insertIcon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>`,
        magic: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 4 5 5M3 21l10-10M20.96 2.04a2.12 2.12 0 0 0-3 0l-5.32 5.32 3 3 5.32-5.32a2.12 2.12 0 0 0 0-3Z"/><path d="M19 16c.5 0 1 .5 1 1v1c0 .5-.5 1-1 1h-1c-.5 0-1-.5-1-1v-1c0-.5.5-1 1-1h1ZM10 4c.5 0 1 .5 1 1v1c0 .5-.5 1-1 1H9c-.5 0-1-.5-1-1V5c0-.5.5-1 1-1h1ZM6 14c.5 0 1 .5 1 1v1c0 .5-.5 1-1 1H5c-.5 0-1-.5-1-1v-1c0-.5.5-1 1-1h1Z"/></svg>`,
    };

    // ─── Toolbar Config ────────────────────────────────────────────────────────
    static TOOLBAR_GROUPS = [
        [
            { id: 'undo',          icon: 'undo',          title: 'تراجع (Ctrl+Z)',       action: 'undo' },
            { id: 'redo',          icon: 'redo',          title: 'إعادة (Ctrl+Y)',        action: 'redo' },
        ],
        [
            { id: 'bold',          icon: 'bold',          title: 'غامق (Ctrl+B)',         action: 'bold',          toggle: true },
            { id: 'italic',        icon: 'italic',        title: 'مائل (Ctrl+I)',          action: 'italic',        toggle: true },
            { id: 'underline',     icon: 'underline',     title: 'تسطير (Ctrl+U)',         action: 'underline',     toggle: true },
        ],
        [
            { id: 'h2',            icon: 'h2',            title: 'عنوان 2',                action: 'formatBlock',   value: 'h2',  toggle: true },
            { id: 'h3',            icon: 'h3',            title: 'عنوان 3',                action: 'formatBlock',   value: 'h3',  toggle: true },
            { id: 'h4',            icon: 'h4',            title: 'عنوان 4',                action: 'formatBlock',   value: 'h4',  toggle: true },
        ],
        [
            { id: 'ul',            icon: 'ul',            title: 'قائمة نقطية',            action: 'insertUnorderedList', toggle: true },
            { id: 'ol',            icon: 'ol',            title: 'قائمة مرقمة',            action: 'insertOrderedList',   toggle: true },
            { id: 'blockquote',    icon: 'blockquote',    title: 'اقتباس',                 action: 'formatBlock',   value: 'blockquote', toggle: true },
        ],
        [
            { id: 'alignRight',    icon: 'alignRight',    title: 'محاذاة لليمين',         action: 'justifyRight' },
            { id: 'alignCenter',   icon: 'alignCenter',   title: 'محاذاة للمركز',         action: 'justifyCenter' },
            { id: 'alignLeft',     icon: 'alignLeft',     title: 'محاذاة لليسار',         action: 'justifyLeft' },
            { id: 'alignJustify',  icon: 'alignJustify',  title: 'محاذاة متساوية',        action: 'justifyFull' },
        ],
        [
            { id: 'rtl',           icon: 'rtl',           title: 'اتجاه RTL',              action: 'setRTL' },
            { id: 'ltr',           icon: 'ltr',           title: 'اتجاه LTR',              action: 'setLTR' },
        ],
        [
            { id: 'link',          icon: 'link',          title: 'إدراج رابط',             action: 'createLink' },
            { id: 'unlink',        icon: 'unlink',        title: 'إزالة الرابط',           action: 'unlink' },
            { id: 'image',         icon: 'image',         title: 'إدراج صورة',             action: 'insertImage' },
        ],
        [
            { id: 'clear',         icon: 'clear',         title: 'مسح التنسيق',            action: 'removeFormat' },
        ],
        [
            { id: 'table',         icon: 'table',         title: 'إدراج جدول',             action: 'insertTable' },
        ],
        [
            { id: 'insertIcon',    icon: 'insertIcon',    title: 'إدراج أيقونة',           action: 'insertIcon' },
        ],
    ];

    // ─── Font Size Options ─────────────────────────────────────────────────────
    static FONT_SIZES = [
        { label: 'صغير', value: 12 },
        { label: 'عادي', value: 14 },
        { label: 'وسط', value: 16 },
        { label: 'كبير', value: 18 },
        { label: 'كبير جداً', value: 24 },
    ];

    // ─── Line Height Options ───────────────────────────────────────────────────
    static LINE_HEIGHTS = [
        { label: 'ضيق (1)', value: '1' },
        { label: 'مضغوط (1.2)', value: '1.2' },
        { label: 'متوسط (1.5)', value: '1.5' },
        { label: 'عادي (1.75)', value: '1.75' },
        { label: 'مريح (2)', value: '2' },
        { label: 'واسع (2.5)', value: '2.5' },
        { label: 'مزدوج (3)', value: '3' },
    ];

    // ─── Color Palette (Word-style) ───────────────────────────────────────────
    static COLOR_PALETTE = [
        '#000000', '#434343', '#666666', '#999999', '#B7B7B7', '#CCCCCC', '#D9D9D9', '#EFEFEF', '#F3F3F3', '#FFFFFF',
        '#980000', '#FF0000', '#FF9900', '#FFFF00', '#00FF00', '#00FFFF', '#4A86E8', '#0000FF', '#9900FF', '#FF00FF',
        '#E6B8AF', '#F4CCCC', '#FCE5CD', '#FFF2CC', '#D9EAD3', '#D0E0E3', '#C9DAF8', '#CFE2F3', '#D9D2E9', '#EAD1DC',
        '#DD7E6B', '#EA9999', '#F9CB9C', '#FFE599', '#B6D7A8', '#A2C4C9', '#A4C2F4', '#9FC5E8', '#B4A7D6', '#D5A6BD',
        '#CC4125', '#E06666', '#F6B26B', '#FFD966', '#93C47D', '#76A5AF', '#6D9EEB', '#6FA8DC', '#8E7CC3', '#C27BA0',
        '#A61C00', '#CC0000', '#E69138', '#F1C232', '#6AA84F', '#45818E', '#3C78D8', '#3D85C6', '#674EA7', '#A64D79',
        '#85200C', '#990000', '#B45F06', '#BF9000', '#38761D', '#134F5C', '#1155CC', '#0B5394', '#351C75', '#741B47',
        '#5B0F00', '#660000', '#783F04', '#7F6000', '#274E13', '#0C343D', '#1C4587', '#073763', '#20124D', '#4C1130',
    ];

    // ─── Minimal Toolbar Config (الأدوات الأساسية فقط) ───────────────────────
    static MINIMAL_TOOLBAR_IDS = new Set([
        'undo', 'redo', 'bold', 'h2', 'h3', 'ul',
        'alignRight', 'alignCenter', 'alignLeft', 'alignJustify',
        'table',
    ]);

    // ─── Init ──────────────────────────────────────────────────────────────────
    _init() {
        this._isMinimalMode = true; // افتراضياً الوضع المصغر
        // حفظ المحتوى الأصلي قبل ما _buildDOM يمسح الـ container
        const initialTextarea = this.container.querySelector('textarea[data-is-initial]');
        this._initialName = initialTextarea ? initialTextarea.getAttribute('data-name') : '';
        this._initialValue = initialTextarea ? initialTextarea.value : '';
        this._buildDOM();
        this._bindEvents();
        this._loadInitialContent();
    }

    _buildDOM() {
        // Clear container
        this.container.innerHTML = '';
        this.container.classList.add('pro-editor-wrapper');

        // Toolbar
        this.toolbar = document.createElement('div');
        this.toolbar.className = 'pro-editor-toolbar';
        this.toolbar.setAttribute('role', 'toolbar');
        this.toolbar.setAttribute('aria-label', 'أدوات التحرير');

        // Add mode toggle button at the beginning
        const modeGroup = document.createElement('div');
        modeGroup.className = 'pro-editor-toolbar-group';

        const modeBtn = document.createElement('button');
        modeBtn.type = 'button';
        modeBtn.className = 'pro-editor-btn pro-editor-mode-btn';
        modeBtn.id = `btn-${this.container.id || 'editor'}-mode`;
        modeBtn.title = 'تبديل بين المحرر المرئي و HTML';
        modeBtn.setAttribute('aria-label', 'تبديل الوضع');
        modeBtn.setAttribute('data-mode', 'visual');
        modeBtn.innerHTML = ProfessionalHTMLEditor.ICONS.eye;
        modeBtn.addEventListener('mousedown', (e) => {
            e.preventDefault();
            const currentMode = modeBtn.getAttribute('data-mode');
            this._switchMode(currentMode === 'visual' ? 'text' : 'visual');
        });

        const beautifyBtn = document.createElement('button');
        beautifyBtn.type = 'button';
        beautifyBtn.className = 'pro-editor-btn pro-editor-beautify-btn';
        beautifyBtn.id = `btn-${this.container.id || 'editor'}-beautify`;
        beautifyBtn.title = 'تنسيق وترتيب الكود (Beautify HTML)';
        beautifyBtn.setAttribute('aria-label', 'تنسيق الكود');
        beautifyBtn.style.display = 'none';
        beautifyBtn.innerHTML = ProfessionalHTMLEditor.ICONS.magic + '<span class="pro-btn-label" style="margin-right: 4px; font-size: 11px;">تنسيق الكود</span>';
        beautifyBtn.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this._beautifyCode();
        });
        this._beautifyBtn = beautifyBtn;

        modeGroup.appendChild(modeBtn);
        modeGroup.appendChild(beautifyBtn);
        this.toolbar.appendChild(modeGroup);

        // Separator
        const sep0 = document.createElement('div');
        sep0.className = 'pro-editor-separator';
        sep0.setAttribute('aria-hidden', 'true');
        this.toolbar.appendChild(sep0);

        ProfessionalHTMLEditor.TOOLBAR_GROUPS.forEach((group, groupIndex) => {
            const groupEl = document.createElement('div');
            groupEl.className = 'pro-editor-toolbar-group';

            group.forEach(btnConfig => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'pro-editor-btn';
                btn.id = `btn-${this.container.id || 'editor'}-${btnConfig.id}`;
                btn.title = btnConfig.title;
                btn.setAttribute('aria-label', btnConfig.title);
                btn.setAttribute('data-action', btnConfig.action);
                if (btnConfig.value) btn.setAttribute('data-value', btnConfig.value);
                if (btnConfig.toggle) btn.setAttribute('data-toggle', 'true');
                btn.innerHTML = ProfessionalHTMLEditor.ICONS[btnConfig.icon] || btnConfig.icon;
                groupEl.appendChild(btn);
            });

            this.toolbar.appendChild(groupEl);

            // Separator between groups (not after last)
            if (groupIndex < ProfessionalHTMLEditor.TOOLBAR_GROUPS.length - 1) {
                const sep = document.createElement('div');
                sep.className = 'pro-editor-separator';
                sep.setAttribute('aria-hidden', 'true');
                this.toolbar.appendChild(sep);
            }
        });

        // ─── Font Size Select (Word-style combobox) ────────────────────────────
        const fontSep = document.createElement('div');
        fontSep.className = 'pro-editor-separator';
        fontSep.setAttribute('aria-hidden', 'true');
        this.toolbar.appendChild(fontSep);

        const fontSizeGroup = document.createElement('div');
        fontSizeGroup.className = 'pro-editor-toolbar-group';

        this._fontSizeSelect = document.createElement('select');
        this._fontSizeSelect.className = 'pro-editor-fontsize-select';
        this._fontSizeSelect.title = 'حجم الخط';
        this._fontSizeSelect.setAttribute('aria-label', 'حجم الخط');

        const defaultOpt = document.createElement('option');
        defaultOpt.value = '';
        defaultOpt.textContent = 'الحجم';
        defaultOpt.disabled = true;
        defaultOpt.selected = true;
        this._fontSizeSelect.appendChild(defaultOpt);

        ProfessionalHTMLEditor.FONT_SIZES.forEach(size => {
            const opt = document.createElement('option');
            opt.value = size.value;
            opt.textContent = size.label;
            this._fontSizeSelect.appendChild(opt);
        });

        this._fontSizeSelect.addEventListener('change', () => {
            const size = this._fontSizeSelect.value;
            if (!size) return;
            this.editorArea.focus();
            document.execCommand('fontSize', false, '7');
            // Replace browser's font size with exact px
            const fontElements = this.editorArea.querySelectorAll('font[size="7"]');
            fontElements.forEach(el => {
                const span = document.createElement('span');
                span.style.fontSize = size + 'px';
                span.innerHTML = el.innerHTML;
                el.parentNode.replaceChild(span, el);
            });
            this._fontSizeSelect.value = '';
            this._syncToTextarea();
        });

        fontSizeGroup.appendChild(this._fontSizeSelect);
        this.toolbar.appendChild(fontSizeGroup);

        // ─── Line Height Select ────────────────────────────────────────────────
        const lineHeightSep = document.createElement('div');
        lineHeightSep.className = 'pro-editor-separator';
        lineHeightSep.setAttribute('aria-hidden', 'true');
        this.toolbar.appendChild(lineHeightSep);

        const lineHeightGroup = document.createElement('div');
        lineHeightGroup.className = 'pro-editor-toolbar-group';

        this._lineHeightSelect = document.createElement('select');
        this._lineHeightSelect.className = 'pro-editor-lineheight-select';
        this._lineHeightSelect.title = 'ارتفاع السطر';
        this._lineHeightSelect.setAttribute('aria-label', 'ارتفاع السطر');

        const lhDefaultOpt = document.createElement('option');
        lhDefaultOpt.value = '';
        lhDefaultOpt.textContent = 'السطر';
        lhDefaultOpt.disabled = true;
        lhDefaultOpt.selected = true;
        this._lineHeightSelect.appendChild(lhDefaultOpt);

        ProfessionalHTMLEditor.LINE_HEIGHTS.forEach(lh => {
            const opt = document.createElement('option');
            opt.value = lh.value;
            opt.textContent = lh.label;
            this._lineHeightSelect.appendChild(opt);
        });

        this._lineHeightSelect.addEventListener('change', () => {
            const lh = this._lineHeightSelect.value;
            if (!lh) return;
            this.editorArea.focus();

            const selection = window.getSelection();
            if (selection && selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                // تطبيق على البلوك الحالي
                let block = range.startContainer;
                if (block.nodeType === 3) block = block.parentElement;
                // الوصول لأقرب block element
                while (block && block !== this.editorArea && window.getComputedStyle(block).display === 'inline') {
                    block = block.parentElement;
                }
                if (block && block !== this.editorArea) {
                    block.style.lineHeight = lh;
                } else {
                    // لو مفيش بلوك، طبق على المحرر كله
                    this.editorArea.style.lineHeight = lh;
                }
            } else {
                this.editorArea.style.lineHeight = lh;
            }

            this._lineHeightSelect.value = '';
            this._syncToTextarea();
        });

        lineHeightGroup.appendChild(this._lineHeightSelect);
        this.toolbar.appendChild(lineHeightGroup);

        // ─── Font Color Button (Word-style split button) ───────────────────────
        const colorSep = document.createElement('div');
        colorSep.className = 'pro-editor-separator';
        colorSep.setAttribute('aria-hidden', 'true');
        this.toolbar.appendChild(colorSep);

        const fontColorGroup = document.createElement('div');
        fontColorGroup.className = 'pro-editor-toolbar-group';

        this._fontColorBtn = document.createElement('button');
        this._fontColorBtn.type = 'button';
        this._fontColorBtn.className = 'pro-editor-btn pro-editor-color-btn';
        this._fontColorBtn.title = 'لون الخط';
        this._fontColorBtn.setAttribute('aria-label', 'لون الخط');
        this._fontColorBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 20h16"/>
                <path d="M9.5 4h5l4.5 12H5z" fill="none"/>
                <path d="M12 4l4 12M12 4L8 16"/>
                <line x1="7" y1="13" x2="17" y2="13"/>
            </svg>
            <span class="pro-color-indicator" style="background-color: #000000;"></span>
        `;
        this._currentFontColor = '#000000';

        this._fontColorBtn.addEventListener('mousedown', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this._toggleColorPalette();
        });

        fontColorGroup.appendChild(this._fontColorBtn);
        this.toolbar.appendChild(fontColorGroup);

        // ─── Compact/Minimal Toggle Button (آخر زر في الشريط) ──────────────────
        const compactSep = document.createElement('div');
        compactSep.className = 'pro-editor-separator';
        compactSep.setAttribute('aria-hidden', 'true');
        this.toolbar.appendChild(compactSep);

        const compactGroup = document.createElement('div');
        compactGroup.className = 'pro-editor-toolbar-group';

        const compactBtn = document.createElement('button');
        compactBtn.type = 'button';
        compactBtn.className = 'pro-editor-btn pro-editor-compact-btn';
        compactBtn.id = `btn-${this.container.id || 'editor'}-compact`;
        compactBtn.title = 'تبديل شريط الأدوات (مصغر / كامل)';
        compactBtn.setAttribute('aria-label', 'تبديل شريط الأدوات');
        compactBtn.setAttribute('aria-pressed', 'false');
        compactBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="8 9 12 5 16 9"></polyline><polyline points="8 15 12 19 16 15"></polyline></svg>`;
        compactBtn.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this._toggleMinimalMode();
        });

        compactGroup.appendChild(compactBtn);
        this.toolbar.appendChild(compactGroup);
        this._compactBtn = compactBtn;

        // Visual panel (WYSIWYG)
        const visualPanel = document.createElement('div');
        visualPanel.className = 'pro-editor-panel is-active';
        visualPanel.id = `panel-visual-${this.container.id || 'editor'}`;
        visualPanel.setAttribute('data-mode', 'visual');

        // Editor area
        this.editorArea = document.createElement('div');
        this.editorArea.className = 'pro-editor-content';
        this.editorArea.contentEditable = 'true';
        this.editorArea.setAttribute('dir', 'auto');
        this.editorArea.setAttribute('role', 'textbox');
        this.editorArea.setAttribute('aria-multiline', 'true');
        this.editorArea.setAttribute('aria-label', 'محرر النصوص');
        this.editorArea.setAttribute('spellcheck', 'true');

        visualPanel.appendChild(this.editorArea);

        // Text panel (HTML source)
        const textPanel = document.createElement('div');
        textPanel.className = 'pro-editor-panel';
        textPanel.id = `panel-text-${this.container.id || 'editor'}`;
        textPanel.setAttribute('data-mode', 'text');

        this.textArea = document.createElement('textarea');
        this.textArea.className = 'pro-editor-textarea';
        this.textArea.setAttribute('dir', 'ltr');
        this.textArea.setAttribute('spellcheck', 'false');
        this.textArea.setAttribute('aria-label', 'محرر HTML');

        textPanel.appendChild(this.textArea);

        // Footer: word count
        const footer = document.createElement('div');
        footer.className = 'pro-editor-footer';
        this._wordCountEl = document.createElement('span');
        this._wordCountEl.className = 'pro-editor-wordcount';
        this._wordCountEl.textContent = '0 كلمة';
        footer.appendChild(this._wordCountEl);

        // Hidden textarea (carries value on form submit)
        this.hiddenTextarea = document.createElement('textarea');
        this.hiddenTextarea.style.display = 'none';
        this.hiddenTextarea.setAttribute('aria-hidden', 'true');

        this.container.appendChild(this.toolbar);
        this.container.appendChild(visualPanel);
        this.container.appendChild(textPanel);
        this.container.appendChild(footer);
        this.container.appendChild(this.hiddenTextarea);

        this._modeBtn = modeBtn;
    }

    _bindEvents() {
        // Toolbar button clicks
        this.toolbar.addEventListener('mousedown', (e) => {
            const btn = e.target.closest('.pro-editor-btn');
            if (!btn) return;
            // استثناء أزرار التبديل — عندها event listeners خاصة
            if (btn.classList.contains('pro-editor-mode-btn') || btn.classList.contains('pro-editor-compact-btn')) return;
            e.preventDefault(); // Prevent focus loss from editor
            this._handleToolbarAction(btn);
        });

        // Editor input → sync + update toolbar state + word count
        this.editorArea.addEventListener('input', () => {
            this._syncToTextarea();
            this._updateWordCount();
        });

        // Editor click/selection → update toolbar state
        this.editorArea.addEventListener('click', () => {
            this._updateToolbarState();
            this._updateFontSizeDisplay();
        });

        // Text area input → sync to editor
        this.textArea.addEventListener('input', () => {
            this._syncFromTextarea();
        });

        // Selection change → update active button states and font size
        document.addEventListener('selectionchange', () => {
            if (document.activeElement === this.editorArea || this.editorArea.contains(document.activeElement)) {
                this._updateToolbarState();
                this._updateFontSizeDisplay();
            }
        });

        // Keyboard shortcuts
        this.editorArea.addEventListener('keydown', (e) => this._handleKeydown(e));

        // Paste: strip unsafe HTML
        this.editorArea.addEventListener('paste', (e) => this._handlePaste(e));

        // Focus/blur visual feedback
        this.editorArea.addEventListener('focus', () => this.container.classList.add('is-focused'));
        this.editorArea.addEventListener('blur', () => {
            this.container.classList.remove('is-focused');
            this._syncToTextarea();
        });

        this.textArea.addEventListener('focus', () => this.container.classList.add('is-focused'));
        this.textArea.addEventListener('blur', () => {
            this.container.classList.remove('is-focused');
            this._syncFromTextarea();
        });
    }

    _loadInitialContent() {
        // استخدام المحتوى المحفوظ من _init (قبل ما _buildDOM يمسح الـ container)
        if (this._initialName) {
            this.hiddenTextarea.name = this._initialName;
        }
        if (this._initialValue) {
            this.editorArea.innerHTML = this._initialValue;
        }
        this._syncToTextarea();
        this._updateWordCount();
        this._bindAllTableEvents();
        this._bindImageEvents();
        
        // تطبيق الوضع المصغر افتراضياً
        this._applyMinimalMode();
    }

    // ─── Toolbar Actions ───────────────────────────────────────────────────────
    _handleToolbarAction(btn) {
        const action = btn.getAttribute('data-action');
        const value = btn.getAttribute('data-value') || null;

        switch (action) {
            case 'createLink':
                this.editorArea.focus();
                this._insertLink();
                break;
            case 'insertImage':
                this.editorArea.focus();
                this._insertImage();
                break;
            case 'insertTable':
                this._showTablePicker(btn);
                break;
            case 'insertIcon':
                this.editorArea.focus();
                this._insertIcon();
                break;
            case 'changeFontSize':
                this._showFontSizeDropdown(btn);
                break;
            case 'changeFontColor':
                this._showFontColorDropdown(btn);
                break;
            case 'formatBlock':
                this.editorArea.focus();
                this._toggleBlock(value, btn);
                break;
            case 'setRTL':
                this.editorArea.focus();
                this.editorArea.setAttribute('dir', 'rtl');
                this.editorArea.style.textAlign = 'right';
                break;
            case 'setLTR':
                this.editorArea.focus();
                this.editorArea.setAttribute('dir', 'ltr');
                this.editorArea.style.textAlign = 'left';
                break;
            case 'removeFormat':
                this.editorArea.focus();
                this._clearFormatting();
                break;
            default:
                this.editorArea.focus();
                document.execCommand(action, false, value);
        }

        this._syncToTextarea();
        this._updateToolbarState();
    }

    _insertLink() {
        const selection = window.getSelection();
        const selectedText = selection ? selection.toString() : '';

        // Simple inline modal
        const modal = this._createLinkModal(selectedText, (url, text, newTab) => {
            if (!url) return;
            this.editorArea.focus();

            if (selectedText) {
                document.execCommand('createLink', false, url);
                // Set target if needed
                const links = this.editorArea.querySelectorAll('a');
                links.forEach(a => {
                    if (a.href === url || a.getAttribute('href') === url) {
                        if (newTab) a.setAttribute('target', '_blank');
                        else a.removeAttribute('target');
                    }
                });
            } else {
                const a = document.createElement('a');
                a.href = url;
                a.textContent = text || url;
                if (newTab) a.setAttribute('target', '_blank');
                if (selection && selection.rangeCount > 0) {
                    const range = selection.getRangeAt(0);
                    range.deleteContents();
                    range.insertNode(a);
                    range.setStartAfter(a);
                    range.collapse(true);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
            }
            this._syncToTextarea();
        });

        document.body.appendChild(modal);
        modal.querySelector('.pro-link-url').focus();
    }

    _insertImage() {
        const modal = this._createImageUploadModal((imageUrl, altText, width, height) => {
            if (!imageUrl) return;
            this.editorArea.focus();

            const img = document.createElement('img');
            img.src = imageUrl;
            img.alt = altText || 'صورة';
            img.style.maxWidth = '100%';
            img.style.height = 'auto';
            img.style.borderRadius = 'var(--radius-sm)';
            img.style.marginTop = '0.5em';
            img.style.marginBottom = '0.5em';
            
            if (width) img.style.width = width + 'px';
            if (height) img.style.height = height + 'px';

            const selection = window.getSelection();
            if (selection && selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                range.insertNode(img);
                range.setStartAfter(img);
                range.collapse(true);
                selection.removeAllRanges();
                selection.addRange(range);
            } else {
                this.editorArea.appendChild(img);
            }

            this._syncToTextarea();
        });

        document.body.appendChild(modal);
    }

    _toggleColorPalette() {
        // Close existing palette if open
        const existing = document.querySelector('.pro-color-palette');
        if (existing) {
            existing.remove();
            return;
        }

        const palette = document.createElement('div');
        palette.className = 'pro-color-palette';

        let html = '<div class="pro-palette-grid">';
        ProfessionalHTMLEditor.COLOR_PALETTE.forEach(color => {
            html += `<button class="pro-palette-swatch" data-color="${color}" style="background-color: ${color};" title="${color}"></button>`;
        });
        html += '</div>';

        palette.innerHTML = html;

        // Apply color on swatch click
        palette.querySelectorAll('.pro-palette-swatch').forEach(swatch => {
            swatch.addEventListener('mousedown', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const color = swatch.getAttribute('data-color');
                this._applyFontColor(color);
                palette.remove();
            });
        });

        document.body.appendChild(palette);

        // Position below the color button - calculate position after rendering
        setTimeout(() => {
            const rect = this._fontColorBtn.getBoundingClientRect();
            const paletteRect = palette.getBoundingClientRect();
            
            let top = rect.bottom + 6;
            let left = rect.left;
            
            // Adjust if palette goes off-screen to the right
            if (left + paletteRect.width > window.innerWidth) {
                left = window.innerWidth - paletteRect.width - 8;
            }
            
            // Adjust if palette goes off-screen to the bottom
            if (top + paletteRect.height > window.innerHeight) {
                top = rect.top - paletteRect.height - 6;
            }
            
            palette.style.position = 'fixed';
            palette.style.top = top + 'px';
            palette.style.left = left + 'px';
            palette.style.zIndex = '10000';
        }, 0);

        // Close on outside click
        const closePalette = (e) => {
            if (!palette.contains(e.target) && e.target !== this._fontColorBtn) {
                palette.remove();
                document.removeEventListener('mousedown', closePalette);
            }
        };
        setTimeout(() => {
            document.addEventListener('mousedown', closePalette);
        }, 10);
    }

    _applyFontColor(color) {
        this._currentFontColor = color;
        // Update indicator
        const indicator = this._fontColorBtn.querySelector('.pro-color-indicator');
        if (indicator) indicator.style.backgroundColor = color;

        this.editorArea.focus();
        document.execCommand('foreColor', false, color);
        this._syncToTextarea();
    }

    _positionDropdown(dropdown, range) {
        if (!range) {
            const selection = window.getSelection();
            if (!selection || selection.rangeCount === 0) return;
            range = selection.getRangeAt(0);
        }

        const rect = range.getBoundingClientRect();

        dropdown.style.position = 'fixed';
        dropdown.style.top = (rect.bottom + 5) + 'px';
        dropdown.style.left = rect.left + 'px';
        dropdown.style.zIndex = '10000';
    }

    _positionDropdownToButton(dropdown, btn) {
        const rect = btn.getBoundingClientRect();

        dropdown.style.position = 'fixed';
        dropdown.style.top = (rect.bottom + 5) + 'px';
        dropdown.style.left = rect.left + 'px';
        dropdown.style.zIndex = '10000';
    }

    _createLinkModal(selectedText, onConfirm) {
        const overlay = document.createElement('div');
        overlay.className = 'pro-editor-modal-overlay';
        overlay.innerHTML = `
            <div class="pro-editor-modal" role="dialog" aria-modal="true" aria-label="إدراج رابط">
                <div class="pro-editor-modal-header">
                    <span>إدراج رابط</span>
                    <button type="button" class="pro-modal-close" aria-label="إغلاق">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>
                <div class="pro-editor-modal-body">
                    <div class="pro-modal-field">
                        <label>عنوان الرابط (URL)</label>
                        <input type="url" class="pro-link-url" placeholder="https://" dir="ltr" />
                    </div>
                    ${!selectedText ? `
                    <div class="pro-modal-field">
                        <label>نص الرابط</label>
                        <input type="text" class="pro-link-text" placeholder="نص يظهر للقارئ" dir="rtl" />
                    </div>` : ''}
                    <label class="pro-modal-checkbox">
                        <input type="checkbox" class="pro-link-newtab" />
                        <span>فتح في تبويب جديد</span>
                    </label>
                </div>
                <div class="pro-editor-modal-footer">
                    <button type="button" class="pro-modal-cancel">إلغاء</button>
                    <button type="button" class="pro-modal-confirm">إدراج</button>
                </div>
            </div>
        `;

        const close = () => overlay.remove();

        overlay.querySelector('.pro-modal-close').addEventListener('click', close);
        overlay.querySelector('.pro-modal-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

        overlay.querySelector('.pro-modal-confirm').addEventListener('click', () => {
            const url = overlay.querySelector('.pro-link-url').value.trim();
            const textEl = overlay.querySelector('.pro-link-text');
            const text = textEl ? textEl.value.trim() : selectedText;
            const newTab = overlay.querySelector('.pro-link-newtab').checked;
            close();
            onConfirm(url, text, newTab);
        });

        // Enter key confirms
        overlay.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                overlay.querySelector('.pro-modal-confirm').click();
            } else if (e.key === 'Escape') {
                close();
            }
        });

        return overlay;
    }

    _createImageUploadModal(onConfirm) {
        const overlay = document.createElement('div');
        overlay.className = 'pro-editor-modal-overlay';
        overlay.innerHTML = `
            <div class="pro-editor-modal" role="dialog" aria-modal="true" aria-label="إدراج صورة">
                <div class="pro-editor-modal-header">
                    <span>إدراج صورة</span>
                    <button type="button" class="pro-modal-close" aria-label="إغلاق">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>
                <div class="pro-editor-modal-body">
                    <div class="pro-modal-field">
                        <label>اختر صورة</label>
                        <div class="pro-image-upload-zone">
                            <input type="file" class="pro-image-file-input" accept="image/*" style="display:none;" />
                            <div class="pro-image-upload-placeholder">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                    <circle cx="8.5" cy="8.5" r="1.5"/>
                                    <polyline points="21 15 16 10 5 21"/>
                                </svg>
                                <p>اسحب الصورة هنا أو اضغط للاختيار</p>
                                <span class="pro-image-upload-hint">JPG, PNG, WebP (الحد الأقصى 5MB)</span>
                            </div>
                            <div class="pro-image-preview" style="display:none;">
                                <img class="pro-image-preview-img" src="" alt="معاينة" />
                                <div class="pro-image-preview-info">
                                    <span class="pro-image-preview-name"></span>
                                    <span class="pro-image-preview-size"></span>
                                </div>
                            </div>
                            <div class="pro-image-upload-progress" style="display:none;">
                                <div class="pro-progress-bar">
                                    <div class="pro-progress-fill"></div>
                                </div>
                                <span class="pro-progress-text">0%</span>
                            </div>
                        </div>
                    </div>
                    <div class="pro-modal-field">
                        <label>نص بديل (Alt Text)</label>
                        <input type="text" class="pro-image-alt" placeholder="وصف الصورة للقارئ" dir="rtl" />
                    </div>
                    <div class="pro-modal-field">
                        <label>الحجم (اختياري)</label>
                        <div class="pro-image-size-inputs">
                            <input type="number" class="pro-image-width" placeholder="العرض (px)" min="50" max="1200" />
                            <span>×</span>
                            <input type="number" class="pro-image-height" placeholder="الارتفاع (px)" min="50" max="1200" />
                        </div>
                    </div>
                </div>
                <div class="pro-editor-modal-footer">
                    <button type="button" class="pro-modal-cancel">إلغاء</button>
                    <button type="button" class="pro-modal-confirm" disabled>إدراج</button>
                </div>
            </div>
        `;

        const fileInput = overlay.querySelector('.pro-image-file-input');
        const uploadZone = overlay.querySelector('.pro-image-upload-zone');
        const placeholder = overlay.querySelector('.pro-image-upload-placeholder');
        const preview = overlay.querySelector('.pro-image-preview');
        const previewImg = overlay.querySelector('.pro-image-preview-img');
        const previewName = overlay.querySelector('.pro-image-preview-name');
        const previewSize = overlay.querySelector('.pro-image-preview-size');
        const progressDiv = overlay.querySelector('.pro-image-upload-progress');
        const progressFill = overlay.querySelector('.pro-progress-fill');
        const progressText = overlay.querySelector('.pro-progress-text');
        const altInput = overlay.querySelector('.pro-image-alt');
        const widthInput = overlay.querySelector('.pro-image-width');
        const heightInput = overlay.querySelector('.pro-image-height');
        const confirmBtn = overlay.querySelector('.pro-modal-confirm');
        let uploadedImageUrl = null;
        let uploadedImageSize = null;

        const close = () => overlay.remove();

        overlay.querySelector('.pro-modal-close').addEventListener('click', close);
        overlay.querySelector('.pro-modal-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

        // File input click
        placeholder.addEventListener('click', () => fileInput.click());

        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('is-dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('is-dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('is-dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                this._uploadImage(fileInput.files[0], overlay, previewImg, previewName, previewSize, placeholder, preview, progressDiv, progressFill, progressText, confirmBtn, (url, size) => {
                    uploadedImageUrl = url;
                    uploadedImageSize = size;
                });
            }
        });

        // File input change
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                this._uploadImage(fileInput.files[0], overlay, previewImg, previewName, previewSize, placeholder, preview, progressDiv, progressFill, progressText, confirmBtn, (url, size) => {
                    uploadedImageUrl = url;
                    uploadedImageSize = size;
                });
            }
        });

        // Confirm button
        confirmBtn.addEventListener('click', () => {
            if (!uploadedImageUrl) return;
            const altText = altInput.value.trim();
            const width = widthInput.value ? parseInt(widthInput.value) : null;
            const height = heightInput.value ? parseInt(heightInput.value) : null;
            close();
            onConfirm(uploadedImageUrl, altText, width, height);
        });

        // Enter key confirms
        overlay.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && uploadedImageUrl) {
                confirmBtn.click();
            } else if (e.key === 'Escape') {
                close();
            }
        });

        return overlay;
    }

    _uploadImage(file, modal, previewImg, previewName, previewSize, placeholder, preview, progressDiv, progressFill, progressText, confirmBtn, onSuccess) {
        const formData = new FormData();
        formData.append('image', file);

        // Get CSRF token from cookie
        const csrfToken = this._getCsrfToken();
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken);
        }

        // Show progress
        placeholder.style.display = 'none';
        progressDiv.style.display = 'flex';

        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressFill.style.width = percentComplete + '%';
                progressText.textContent = Math.round(percentComplete) + '%';
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.success) {
                    // Show preview
                    previewImg.src = response.url;
                    previewName.textContent = response.filename;
                    previewSize.textContent = `${response.size.width}×${response.size.height}px`;
                    preview.style.display = 'flex';
                    progressDiv.style.display = 'none';
                    confirmBtn.disabled = false;
                    onSuccess(response.url, response.size);
                } else {
                    alert('خطأ: ' + response.error);
                    placeholder.style.display = 'block';
                    progressDiv.style.display = 'none';
                }
            } else {
                alert('خطأ في الرفع');
                placeholder.style.display = 'block';
                progressDiv.style.display = 'none';
            }
        });

        xhr.addEventListener('error', () => {
            alert('خطأ في الاتصال');
            placeholder.style.display = 'block';
            progressDiv.style.display = 'none';
        });

        xhr.open('POST', '/dashboard/editor/upload-image/');
        xhr.send(formData);
    }

    _getCsrfToken() {
        // Try to get from cookie
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        // Try to get from meta tag
        if (!cookieValue) {
            const token = document.querySelector('[name=csrfmiddlewaretoken]');
            if (token) cookieValue = token.value;
        }
        return cookieValue;
    }

    _createImageModal(onConfirm) {
        const overlay = document.createElement('div');
        overlay.className = 'pro-editor-modal-overlay';
        overlay.innerHTML = `
            <div class="pro-editor-modal" role="dialog" aria-modal="true" aria-label="إدراج صورة">
                <div class="pro-editor-modal-header">
                    <span>إدراج صورة</span>
                    <button type="button" class="pro-modal-close" aria-label="إغلاق">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>
                <div class="pro-editor-modal-body">
                    <div class="pro-modal-field">
                        <label>رابط الصورة (URL)</label>
                        <input type="url" class="pro-image-url" placeholder="https://example.com/image.jpg" dir="ltr" />
                    </div>
                    <div class="pro-modal-field">
                        <label>نص بديل (Alt Text)</label>
                        <input type="text" class="pro-image-alt" placeholder="وصف الصورة للقارئ" dir="rtl" />
                    </div>
                </div>
                <div class="pro-editor-modal-footer">
                    <button type="button" class="pro-modal-cancel">إلغاء</button>
                    <button type="button" class="pro-modal-confirm">إدراج</button>
                </div>
            </div>
        `;

        const close = () => overlay.remove();

        overlay.querySelector('.pro-modal-close').addEventListener('click', close);
        overlay.querySelector('.pro-modal-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

        overlay.querySelector('.pro-modal-confirm').addEventListener('click', () => {
            const imageUrl = overlay.querySelector('.pro-image-url').value.trim();
            const altText = overlay.querySelector('.pro-image-alt').value.trim();
            close();
            onConfirm(imageUrl, altText);
        });

        // Enter key confirms
        overlay.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                overlay.querySelector('.pro-modal-confirm').click();
            } else if (e.key === 'Escape') {
                close();
            }
        });

        return overlay;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // ─── TABLE ENGINE ──────────────────────────────────────────────────────────
    // ═══════════════════════════════════════════════════════════════════════════

    // ─── Grid Picker Popup ─────────────────────────────────────────────────────
    _showTablePicker(btn) {
        const existing = document.querySelector('.pro-table-picker');
        if (existing) { existing.remove(); return; }

        const picker = document.createElement('div');
        picker.className = 'pro-table-picker';
        picker.innerHTML = `
            <div class="pro-table-picker-label">إدراج جدول</div>
            <div class="pro-table-picker-grid"></div>
            <div class="pro-table-picker-size">1 × 1</div>
        `;

        const ROWS = 8, COLS = 10;
        const grid = picker.querySelector('.pro-table-picker-grid');
        const sizeLabel = picker.querySelector('.pro-table-picker-size');
        grid.style.gridTemplateColumns = `repeat(${COLS}, 1fr)`;

        let cells = [];
        for (let r = 1; r <= ROWS; r++) {
            for (let c = 1; c <= COLS; c++) {
                const cell = document.createElement('div');
                cell.className = 'pro-table-picker-cell';
                cell.dataset.row = r;
                cell.dataset.col = c;
                grid.appendChild(cell);
                cells.push(cell);
            }
        }

        const highlight = (maxR, maxC) => {
            cells.forEach(cell => {
                const r = +cell.dataset.row, c = +cell.dataset.col;
                cell.classList.toggle('is-active', r <= maxR && c <= maxC);
            });
            sizeLabel.textContent = `${maxR} × ${maxC}`;
        };

        grid.addEventListener('mouseover', (e) => {
            const cell = e.target.closest('.pro-table-picker-cell');
            if (!cell) return;
            highlight(+cell.dataset.row, +cell.dataset.col);
        });

        grid.addEventListener('mouseleave', () => highlight(0, 0));

        grid.addEventListener('click', (e) => {
            const cell = e.target.closest('.pro-table-picker-cell');
            if (!cell) return;
            picker.remove();
            this._insertTable(+cell.dataset.row, +cell.dataset.col);
        });

        document.body.appendChild(picker);

        // Position below button
        setTimeout(() => {
            const rect = btn.getBoundingClientRect();
            const pRect = picker.getBoundingClientRect();
            let top = rect.bottom + 6;
            let left = rect.left;
            if (left + pRect.width > window.innerWidth) left = window.innerWidth - pRect.width - 8;
            if (top + pRect.height > window.innerHeight) top = rect.top - pRect.height - 6;
            picker.style.top = top + 'px';
            picker.style.left = left + 'px';
        }, 0);

        const close = (e) => {
            if (!picker.contains(e.target) && e.target !== btn) {
                picker.remove();
                document.removeEventListener('mousedown', close);
            }
        };
        setTimeout(() => document.addEventListener('mousedown', close), 10);
    }

    // ─── Build & Insert Table ──────────────────────────────────────────────────
    _insertTable(rows, cols) {
        this._saveState('إدراج جدول');
        this.editorArea.focus();

        const table = document.createElement('table');
        table.className = 'pro-editor-table';
        table.setAttribute('data-pro-table', '1');

        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        for (let c = 0; c < cols; c++) {
            const th = document.createElement('th');
            th.contentEditable = 'true';
            th.innerHTML = `<br>`;
            headerRow.appendChild(th);
        }
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        for (let r = 1; r < rows; r++) {
            const tr = document.createElement('tr');
            for (let c = 0; c < cols; c++) {
                const td = document.createElement('td');
                td.contentEditable = 'true';
                td.innerHTML = `<br>`;
                tr.appendChild(td);
            }
            tbody.appendChild(tr);
        }
        table.appendChild(tbody);

        // Wrapper for overflow
        const wrapper = document.createElement('div');
        wrapper.className = 'pro-table-wrapper';
        wrapper.appendChild(table);

        // Insert at cursor or append
        const sel = window.getSelection();
        if (sel && sel.rangeCount > 0) {
            const range = sel.getRangeAt(0);
            range.deleteContents();
            range.insertNode(wrapper);
            // Move cursor after table
            const after = document.createElement('p');
            after.innerHTML = '<br>';
            wrapper.after(after);
            range.setStart(after, 0);
            range.collapse(true);
            sel.removeAllRanges();
            sel.addRange(range);
        } else {
            this.editorArea.appendChild(wrapper);
        }

        this._syncToTextarea();
        this._bindTableEvents(table);
    }

    // ─── Bind Table Events ─────────────────────────────────────────────────────
    _bindTableEvents(table) {
        table.addEventListener('click', (e) => {
            const cell = e.target.closest('td, th');
            if (!cell) return;
            
            // Multi-select with Shift/Ctrl
            if (e.shiftKey || e.ctrlKey) {
                e.preventDefault();
                this._toggleCellSelection(cell, table, e.ctrlKey);
            } else {
                // Single select
                table.querySelectorAll('td, th').forEach(c => c.classList.remove('is-selected'));
                cell.classList.add('is-selected');
            }
            
            this._showTableToolbar(cell, table);
        });

        // Save state on cell content change
        table.addEventListener('input', (e) => {
            const cell = e.target.closest('td, th');
            if (cell) {
                // Debounce: only save every 1 second
                if (!cell.dataset.lastSave || Date.now() - cell.dataset.lastSave > 1000) {
                    this._saveState('تعديل محتوى الخلية');
                    cell.dataset.lastSave = Date.now();
                }
            }
        });
    }

    _toggleCellSelection(cell, table, isCtrl) {
        if (isCtrl) {
            // Toggle individual cell
            cell.classList.toggle('is-selected');
        } else {
            // Shift: select range
            const allCells = Array.from(table.querySelectorAll('td, th'));
            const lastSelected = table.querySelector('td.is-selected, th.is-selected');
            
            if (!lastSelected) {
                cell.classList.add('is-selected');
                return;
            }
            
            const startIdx = allCells.indexOf(lastSelected);
            const endIdx = allCells.indexOf(cell);
            const [min, max] = startIdx < endIdx ? [startIdx, endIdx] : [endIdx, startIdx];
            
            allCells.forEach((c, i) => {
                c.classList.toggle('is-selected', i >= min && i <= max);
            });
        }
    }

    // ─── Floating Table Toolbar ────────────────────────────────────────────────
    _showTableToolbar(activeCell, table) {
        // Remove existing toolbar
        document.querySelector('.pro-table-toolbar')?.remove();

        const toolbar = document.createElement('div');
        toolbar.className = 'pro-table-toolbar';
        toolbar.setAttribute('data-table-toolbar', '1');

        const groups = [
            {
                label: 'صف',
                items: [
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="7" rx="1"/><line x1="3" y1="14" x2="21" y2="14"/><line x1="12" y1="14" x2="12" y2="21"/><line x1="7" y1="17" x2="17" y2="17"/></svg>`, title: 'إضافة صف فوق',   action: 'addRowAbove' },
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="14" width="18" height="7" rx="1"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="12" y1="3" x2="12" y2="10"/><line x1="7" y1="6" x2="17" y2="6"/></svg>`, title: 'إضافة صف تحت',   action: 'addRowBelow' },
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="1"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="8" y1="8" x2="16" y2="16"/><line x1="16" y1="8" x2="8" y2="16"/></svg>`, title: 'حذف الصف',        action: 'deleteRow',  danger: true },
                ],
            },
            {
                label: 'عمود',
                items: [
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="18" rx="1"/><line x1="14" y1="3" x2="14" y2="21"/><line x1="14" y1="12" x2="21" y2="12"/><line x1="17" y1="7" x2="17" y2="17"/></svg>`, title: 'إضافة عمود يمين', action: 'addColRight' },
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="14" y="3" width="7" height="18" rx="1"/><line x1="10" y1="3" x2="10" y2="21"/><line x1="3" y1="12" x2="10" y2="12"/><line x1="6" y1="7" x2="6" y2="17"/></svg>`, title: 'إضافة عمود يسار', action: 'addColLeft' },
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="1"/><line x1="12" y1="3" x2="12" y2="21"/><line x1="8" y1="8" x2="16" y2="16"/><line x1="16" y1="8" x2="8" y2="16"/></svg>`, title: 'حذف العمود',      action: 'deleteCol',  danger: true },
                ],
            },
            {
                label: 'دمج',
                items: [
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="1"/><line x1="12" y1="3" x2="12" y2="21" stroke-dasharray="3 2"/><line x1="3" y1="12" x2="21" y2="12" stroke-dasharray="3 2"/><polyline points="9,9 12,12 15,9"/><polyline points="9,15 12,12 15,15"/></svg>`, title: 'دمج الخلايا',    action: 'mergeCells' },
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="1"/><line x1="12" y1="3" x2="12" y2="21"/><line x1="3" y1="12" x2="21" y2="12"/><polyline points="15,9 12,12 9,9"/><polyline points="15,15 12,12 9,15"/></svg>`, title: 'فك الدمج',       action: 'splitCell' },
                ],
            },
            {
                label: 'محاذاة',
                items: [
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="21" y1="8" x2="3" y2="8"/><line x1="21" y1="12" x2="3" y2="12"/><line x1="21" y1="16" x2="7" y2="16"/></svg>`, title: 'محاذاة يمين',  action: 'cellAlignRight' },
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="8" x2="6" y2="8"/><line x1="21" y1="12" x2="3" y2="12"/><line x1="18" y1="16" x2="6" y2="16"/></svg>`, title: 'محاذاة وسط',   action: 'cellAlignCenter' },
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="8" x2="17" y2="8"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="16" x2="17" y2="16"/></svg>`, title: 'محاذاة يسار',  action: 'cellAlignLeft' },
                ],
            },
            {
                label: 'خلفية',
                items: [
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="12" cy="12" r="4" fill="currentColor" stroke="none" opacity="0.5"/></svg>`, title: 'خلفية الخلية', action: 'cellBgColor' },
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="8" y1="8" x2="16" y2="16"/><line x1="16" y1="8" x2="8" y2="16"/></svg>`, title: 'مسح الخلفية',  action: 'cellBgClear' },
                ],
            },
            {
                label: 'جدول',
                items: [
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="8" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="16" y2="21"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/></svg>`, title: 'تحديد الجدول كله', action: 'selectTable' },
                    { icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>`, title: 'حذف الجدول',       action: 'deleteTable', danger: true },
                ],
            },
        ];

        groups.forEach((group, gi) => {
            if (gi > 0) {
                const sep = document.createElement('div');
                sep.className = 'pro-table-toolbar-sep';
                toolbar.appendChild(sep);
            }
            const groupEl = document.createElement('div');
            groupEl.className = 'pro-table-toolbar-group';

            const lbl = document.createElement('span');
            lbl.className = 'pro-table-toolbar-label';
            lbl.textContent = group.label;
            groupEl.appendChild(lbl);

            const btns = document.createElement('div');
            btns.className = 'pro-table-toolbar-btns';

            group.items.forEach(item => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'pro-table-btn' + (item.danger ? ' is-danger' : '');
                btn.title = item.title;
                btn.innerHTML = item.icon;
                btn.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this._handleTableAction(item.action, activeCell, table, btn);
                });
                btns.appendChild(btn);
            });

            groupEl.appendChild(btns);
            toolbar.appendChild(groupEl);
        });

        document.body.appendChild(toolbar);
        this._positionTableToolbar(toolbar, table);

        // Close on outside click (but not on table cells)
        const closeHandler = (e) => {
            if (toolbar.contains(e.target)) return;
            if (e.target.closest('[data-pro-table]')) return;
            toolbar.remove();
            document.removeEventListener('mousedown', closeHandler);
        };
        setTimeout(() => document.addEventListener('mousedown', closeHandler), 10);

        // Reposition on scroll/resize
        const reposition = () => {
            if (!document.body.contains(toolbar)) {
                window.removeEventListener('scroll', reposition, true);
                window.removeEventListener('resize', reposition);
                return;
            }
            this._positionTableToolbar(toolbar, table);
        };
        window.addEventListener('scroll', reposition, true);
        window.addEventListener('resize', reposition);
    }

    _positionTableToolbar(toolbar, table) {
        const rect = table.getBoundingClientRect();
        const tRect = toolbar.getBoundingClientRect();
        let top = rect.top - tRect.height - 8;
        let left = rect.left;

        if (top < 8) top = rect.bottom + 8;
        if (left + tRect.width > window.innerWidth) left = window.innerWidth - tRect.width - 8;
        if (left < 8) left = 8;

        toolbar.style.top = top + 'px';
        toolbar.style.left = left + 'px';
    }

    // ─── Table Actions ─────────────────────────────────────────────────────────
    _handleTableAction(action, cell, table, btn) {
        // Save state before any table modification
        if (['addRowAbove', 'addRowBelow', 'deleteRow', 'addColRight', 'addColLeft', 'deleteCol', 'mergeCells', 'splitCell', 'deleteTable'].includes(action)) {
            this._saveState(`جدول: ${action}`);
        }

        const selectedCells = Array.from(table.querySelectorAll('td.is-selected, th.is-selected'));
        const activeCells = selectedCells.length > 0 ? selectedCells : [cell];
        
        const row = cell.closest('tr');
        const tbody = table.querySelector('tbody');
        const thead = table.querySelector('thead');
        const allRows = Array.from(table.querySelectorAll('tr'));
        const rowIndex = allRows.indexOf(row);
        const cellIndex = Array.from(row.cells).indexOf(cell);
        const colCount = row.cells.length;

        switch (action) {

            case 'addRowAbove': {
                const newRow = this._createRow(colCount, false);
                row.before(newRow);
                break;
            }

            case 'addRowBelow': {
                const newRow = this._createRow(colCount, false);
                row.after(newRow);
                break;
            }

            case 'deleteRow': {
                const rowsToDelete = new Set(activeCells.map(c => c.closest('tr')));
                if (rowsToDelete.size === allRows.length) { this._deleteTable(table); break; }
                rowsToDelete.forEach(r => r.remove());
                break;
            }

            case 'addColRight': {
                allRows.forEach((tr, ri) => {
                    const isHeader = tr.closest('thead') !== null;
                    const newCell = document.createElement(isHeader ? 'th' : 'td');
                    newCell.contentEditable = 'true';
                    newCell.innerHTML = '<br>';
                    const ref = tr.cells[cellIndex];
                    if (ref) ref.after(newCell);
                    else tr.appendChild(newCell);
                });
                break;
            }

            case 'addColLeft': {
                allRows.forEach((tr, ri) => {
                    const isHeader = tr.closest('thead') !== null;
                    const newCell = document.createElement(isHeader ? 'th' : 'td');
                    newCell.contentEditable = 'true';
                    newCell.innerHTML = '<br>';
                    const ref = tr.cells[cellIndex];
                    if (ref) ref.before(newCell);
                    else tr.prepend(newCell);
                });
                break;
            }

            case 'deleteCol': {
                if (colCount <= 1) { this._deleteTable(table); break; }
                allRows.forEach(tr => {
                    const c = tr.cells[cellIndex];
                    if (c) c.remove();
                });
                break;
            }

            case 'mergeCells': {
                if (activeCells.length < 2) break;
                const firstCell = activeCells[0];
                let totalContent = firstCell.innerHTML;
                let totalSpan = parseInt(firstCell.getAttribute('colspan') || 1);
                
                activeCells.slice(1).forEach(c => {
                    totalContent += c.innerHTML;
                    totalSpan += parseInt(c.getAttribute('colspan') || 1);
                    c.remove();
                });
                
                firstCell.setAttribute('colspan', totalSpan);
                firstCell.innerHTML = totalContent;
                break;
            }

            case 'splitCell': {
                activeCells.forEach(c => {
                    const span = parseInt(c.getAttribute('colspan') || 1);
                    if (span <= 1) return;
                    c.removeAttribute('colspan');
                    for (let i = 1; i < span; i++) {
                        const isHeader = c.tagName === 'TH';
                        const newCell = document.createElement(isHeader ? 'th' : 'td');
                        newCell.contentEditable = 'true';
                        newCell.innerHTML = '<br>';
                        c.after(newCell);
                    }
                });
                break;
            }

            case 'cellAlignRight':
                this._saveState('محاذاة يمين');
                activeCells.forEach(c => c.style.textAlign = 'right');
                break;
            case 'cellAlignCenter':
                this._saveState('محاذاة وسط');
                activeCells.forEach(c => c.style.textAlign = 'center');
                break;
            case 'cellAlignLeft':
                this._saveState('محاذاة يسار');
                activeCells.forEach(c => c.style.textAlign = 'left');
                break;

            case 'cellBgColor':
                this._saveState('تغيير خلفية الخلية');
                this._showCellColorPicker(activeCells, btn);
                return; // Don't sync yet

            case 'cellBgClear':
                this._saveState('مسح خلفية الخلية');
                activeCells.forEach(c => c.style.backgroundColor = '');
                break;

            case 'selectTable':
                table.querySelectorAll('td, th').forEach(c => c.classList.add('is-selected'));
                setTimeout(() => table.querySelectorAll('td, th').forEach(c => c.classList.remove('is-selected')), 800);
                return;

            case 'deleteTable':
                this._deleteTable(table);
                document.querySelector('.pro-table-toolbar')?.remove();
                break;
        }

        // Re-bind events after DOM changes
        this._bindTableEvents(table);
        this._syncToTextarea();
    }

    _createRow(colCount, isHeader = false) {
        const tr = document.createElement('tr');
        for (let i = 0; i < colCount; i++) {
            const cell = document.createElement(isHeader ? 'th' : 'td');
            cell.contentEditable = 'true';
            cell.innerHTML = '<br>';
            tr.appendChild(cell);
        }
        return tr;
    }

    _deleteTable(table) {
        const wrapper = table.closest('.pro-table-wrapper') || table;
        wrapper.remove();
        this._syncToTextarea();
    }

    // ─── Cell Background Color Picker ──────────────────────────────────────────
    _showCellColorPicker(cells, triggerBtn) {
        const cellsArray = Array.isArray(cells) ? cells : [cells];
        const existing = document.querySelector('.pro-cell-color-palette');
        if (existing) { existing.remove(); return; }

        const palette = document.createElement('div');
        palette.className = 'pro-color-palette pro-cell-color-palette';

        let html = '<div class="pro-palette-grid">';
        ProfessionalHTMLEditor.COLOR_PALETTE.forEach(color => {
            html += `<button class="pro-palette-swatch" data-color="${color}" style="background-color:${color};" title="${color}"></button>`;
        });
        html += '</div>';
        palette.innerHTML = html;

        palette.querySelectorAll('.pro-palette-swatch').forEach(swatch => {
            swatch.addEventListener('mousedown', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const color = swatch.getAttribute('data-color');
                cellsArray.forEach(c => c.style.backgroundColor = color);
                palette.remove();
                this._syncToTextarea();
            });
        });

        document.body.appendChild(palette);

        setTimeout(() => {
            const rect = triggerBtn.getBoundingClientRect();
            const pRect = palette.getBoundingClientRect();
            let top = rect.bottom + 6;
            let left = rect.left;
            if (left + pRect.width > window.innerWidth) left = window.innerWidth - pRect.width - 8;
            if (top + pRect.height > window.innerHeight) top = rect.top - pRect.height - 6;
            palette.style.position = 'fixed';
            palette.style.top = top + 'px';
            palette.style.left = left + 'px';
            palette.style.zIndex = '10001';
        }, 0);

        const close = (e) => {
            if (!palette.contains(e.target)) {
                palette.remove();
                document.removeEventListener('mousedown', close);
            }
        };
        setTimeout(() => document.addEventListener('mousedown', close), 10);
    }

    // ─── Re-bind tables on content load ───────────────────────────────────────
    _bindAllTableEvents() {
        this.editorArea.querySelectorAll('table[data-pro-table]').forEach(t => this._bindTableEvents(t));
    }

    // ─── Image Selection & Resize ──────────────────────────────────────────────
    _bindImageEvents() {
        this.editorArea.addEventListener('click', (e) => {
            const img = e.target.closest('img');
            if (!img) {
                // Deselect all images
                this.editorArea.querySelectorAll('img.is-selected').forEach(i => {
                    i.classList.remove('is-selected');
                    this._removeImageToolbar();
                });
                return;
            }

            e.preventDefault();
            e.stopPropagation();

            // Deselect other images
            this.editorArea.querySelectorAll('img.is-selected').forEach(i => {
                if (i !== img) i.classList.remove('is-selected');
            });

            img.classList.add('is-selected');
            this._showImageToolbar(img);
        });
    }

    _showImageToolbar(img) {
        this._removeImageToolbar();

        const toolbar = document.createElement('div');
        toolbar.className = 'pro-image-toolbar';
        toolbar.setAttribute('data-image-toolbar', '1');

        const width = img.width || img.naturalWidth || 0;
        const height = img.height || img.naturalHeight || 0;
        const aspectRatio = width / height;

        toolbar.innerHTML = `
            <div class="pro-image-toolbar-group">
                <span class="pro-image-toolbar-label">العرض:</span>
                <input type="number" class="pro-image-toolbar-input pro-image-width" value="${width}" min="50" max="1200" />
                <span class="pro-image-toolbar-label">px</span>
            </div>
            <div class="pro-image-toolbar-sep"></div>
            <div class="pro-image-toolbar-group">
                <span class="pro-image-toolbar-label">الارتفاع:</span>
                <input type="number" class="pro-image-toolbar-input pro-image-height" value="${height}" min="50" max="1200" />
                <span class="pro-image-toolbar-label">px</span>
            </div>
            <div class="pro-image-toolbar-sep"></div>
            <button class="pro-image-toolbar-btn pro-image-lock-ratio" title="قفل النسبة">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            </button>
            <button class="pro-image-toolbar-btn pro-image-reset" title="إعادة تعيين">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
            </button>
            <button class="pro-image-toolbar-btn pro-image-delete is-danger" title="حذف">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
            </button>
        `;

        const widthInput = toolbar.querySelector('.pro-image-width');
        const heightInput = toolbar.querySelector('.pro-image-height');
        const lockBtn = toolbar.querySelector('.pro-image-lock-ratio');
        const resetBtn = toolbar.querySelector('.pro-image-reset');
        const deleteBtn = toolbar.querySelector('.pro-image-delete');

        let lockRatio = true;
        const originalWidth = width;
        const originalHeight = height;

        // Lock ratio button
        lockBtn.classList.add('is-active');
        lockBtn.addEventListener('click', (e) => {
            e.preventDefault();
            lockRatio = !lockRatio;
            lockBtn.classList.toggle('is-active', lockRatio);
        });

        // Width change
        widthInput.addEventListener('change', () => {
            const newWidth = parseInt(widthInput.value) || width;
            img.style.width = newWidth + 'px';
            if (lockRatio) {
                const newHeight = Math.round(newWidth / aspectRatio);
                img.style.height = newHeight + 'px';
                heightInput.value = newHeight;
            }
            this._syncToTextarea();
        });

        // Height change
        heightInput.addEventListener('change', () => {
            const newHeight = parseInt(heightInput.value) || height;
            img.style.height = newHeight + 'px';
            if (lockRatio) {
                const newWidth = Math.round(newHeight * aspectRatio);
                img.style.width = newWidth + 'px';
                widthInput.value = newWidth;
            }
            this._syncToTextarea();
        });

        // Reset button
        resetBtn.addEventListener('click', (e) => {
            e.preventDefault();
            img.style.width = '';
            img.style.height = '';
            widthInput.value = originalWidth;
            heightInput.value = originalHeight;
            this._syncToTextarea();
        });

        // Delete button
        deleteBtn.addEventListener('click', (e) => {
            e.preventDefault();
            img.remove();
            toolbar.remove();
            this._syncToTextarea();
        });

        document.body.appendChild(toolbar);
        this._positionImageToolbar(toolbar, img);

        // Reposition on scroll
        const reposition = () => {
            if (!document.body.contains(toolbar)) {
                window.removeEventListener('scroll', reposition, true);
                return;
            }
            this._positionImageToolbar(toolbar, img);
        };
        window.addEventListener('scroll', reposition, true);

        // Close on outside click
        const closeHandler = (e) => {
            if (toolbar.contains(e.target) || e.target === img) return;
            this._removeImageToolbar();
            document.removeEventListener('mousedown', closeHandler);
        };
        setTimeout(() => document.addEventListener('mousedown', closeHandler), 10);
    }

    _positionImageToolbar(toolbar, img) {
        const rect = img.getBoundingClientRect();
        const tRect = toolbar.getBoundingClientRect();
        let top = rect.top - tRect.height - 8;
        let left = rect.left;

        if (top < 8) top = rect.bottom + 8;
        if (left + tRect.width > window.innerWidth) left = window.innerWidth - tRect.width - 8;
        if (left < 8) left = 8;

        toolbar.style.top = top + 'px';
        toolbar.style.left = left + 'px';
    }

    _removeImageToolbar() {
        document.querySelector('[data-image-toolbar]')?.remove();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // ─── END TABLE ENGINE ──────────────────────────────────────────────────────
    // ═══════════════════════════════════════════════════════════════════════════

    _toggleBlock(tag, btn) {
        // Check current block type
        const currentBlock = document.queryCommandValue('formatBlock').toLowerCase();
        if (currentBlock === tag) {
            // Toggle off → revert to paragraph
            document.execCommand('formatBlock', false, 'p');
        } else {
            document.execCommand('formatBlock', false, tag);
        }
    }

    // ─── Undo/Redo Stack ──────────────────────────────────────────────────────
    _saveState(description = 'تعديل') {
        // Save current state to undo stack
        this.undoStack.push({
            html: this.editorArea.innerHTML,
            description: description,
            timestamp: Date.now(),
        });
        // Clear redo stack when new action is performed
        this.redoStack = [];
        // Limit stack size to 50 states
        if (this.undoStack.length > 50) this.undoStack.shift();
    }

    _undo() {
        if (this.undoStack.length === 0) return;
        // Save current state to redo stack
        this.redoStack.push({
            html: this.editorArea.innerHTML,
            description: 'إعادة',
            timestamp: Date.now(),
        });
        // Restore previous state
        const state = this.undoStack.pop();
        this.editorArea.innerHTML = state.html;
        this._syncToTextarea();
        this._bindAllTableEvents();
    }

    _redo() {
        if (this.redoStack.length === 0) return;
        // Save current state to undo stack
        this.undoStack.push({
            html: this.editorArea.innerHTML,
            description: 'تراجع',
            timestamp: Date.now(),
        });
        // Restore next state
        const state = this.redoStack.pop();
        this.editorArea.innerHTML = state.html;
        this._syncToTextarea();
        this._bindAllTableEvents();
    }

    // ─── Clear Formatting ──────────────────────────────────────────────────────
    _clearFormatting() {
        this._saveState('مسح التنسيق');
        
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) return;

        const range = selection.getRangeAt(0);
        const container = range.commonAncestorContainer;
        const element = container.nodeType === Node.TEXT_NODE ? container.parentElement : container;

        // If selection is in a table cell, clear cell formatting
        const cell = element.closest('td, th');
        if (cell) {
            // Clear cell styles
            cell.style.backgroundColor = '';
            cell.style.textAlign = '';
            cell.style.color = '';
            cell.style.fontSize = '';
            cell.style.fontWeight = '';
            cell.style.fontStyle = '';
            cell.style.textDecoration = '';
            
            // Clear text formatting inside cell
            const spans = cell.querySelectorAll('span[style], strong, b, em, i, u, s, del, strike, font');
            spans.forEach(span => {
                while (span.firstChild) {
                    span.parentNode.insertBefore(span.firstChild, span);
                }
                span.parentNode.removeChild(span);
            });
            
            this._syncToTextarea();
            return;
        }

        // For regular text selection, use browser's removeFormat
        document.execCommand('removeFormat', false, null);
        
        // Also remove inline styles
        const selectedElements = this._getSelectedElements(range);
        selectedElements.forEach(el => {
            if (el.nodeType === Node.ELEMENT_NODE) {
                el.removeAttribute('style');
                el.removeAttribute('class');
            }
        });

        this._syncToTextarea();
    }

    _getSelectedElements(range) {
        const elements = [];
        const walker = document.createTreeWalker(
            range.commonAncestorContainer,
            NodeFilter.SHOW_ELEMENT,
            null,
            false
        );

        let node;
        while (node = walker.nextNode()) {
            if (range.intersectsNode(node)) {
                elements.push(node);
            }
        }
        return elements;
    }

    // ─── Keyboard Shortcuts ────────────────────────────────────────────────────
    _handleKeydown(e) {
        if (e.ctrlKey || e.metaKey) {
            switch (e.key.toLowerCase()) {
                case 'b':
                    e.preventDefault();
                    this._saveState('غامق');
                    document.execCommand('bold', false, null);
                    this._updateToolbarState();
                    break;
                case 'i':
                    e.preventDefault();
                    this._saveState('مائل');
                    document.execCommand('italic', false, null);
                    this._updateToolbarState();
                    break;
                case 'u':
                    e.preventDefault();
                    this._saveState('تسطير');
                    document.execCommand('underline', false, null);
                    this._updateToolbarState();
                    break;
                case 'z':
                    if (e.shiftKey) {
                        e.preventDefault();
                        this._redo();
                    } else {
                        e.preventDefault();
                        this._undo();
                    }
                    this._updateToolbarState();
                    break;
                case 'y':
                    e.preventDefault();
                    this._redo();
                    this._updateToolbarState();
                    break;
                case 'k':
                    e.preventDefault();
                    this._insertLink();
                    break;
            }
        }
    }

    // ─── Paste Handler ─────────────────────────────────────────────────────────
    _handlePaste(e) {
        e.preventDefault();

        // نحفظ الـ selection الحالية
        const sel = window.getSelection();
        if (!sel.rangeCount) return;
        const range = sel.getRangeAt(0);

        const html = e.clipboardData.getData('text/html');
        const text = e.clipboardData.getData('text/plain');

        let contentToInsert = '';

        if (html) {
            contentToInsert = this._sanitize(html);
        } else if (text) {
            // نص عادي — نحول الأسطر الجديدة لـ <br>
            contentToInsert = text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/\n/g, '<br>');
        }

        if (contentToInsert) {
            // نحذف المحتوى المحدد (لو فيه)
            range.deleteContents();

            // نعمل fragment من الـ HTML النظيف
            const frag = document.createRange().createContextualFragment(contentToInsert);
            range.insertNode(frag);

            // نحرك الـ cursor لنهاية المحتوى الملصوق
            range.collapse(false);
            sel.removeAllRanges();
            sel.addRange(range);
        }

        this._syncToTextarea();
    }

    // ─── HTML Sanitizer (ذكي — ينظف شوائب اللصق من المصادر الخارجية) ────────
    _sanitize(html) {
        // الخطوة 1: إزالة HTML comments (مثل <!--StartFragment--> و <!--EndFragment-->)
        html = html.replace(/<!--[\s\S]*?-->/g, '');

        // الخطوة 2: إزالة opening/closing tags فقط (بدون محتواها) لـ html, head, body
        html = html.replace(/<\/?(html|head|body)[^>]*>/gi, '');

        // الخطوة 3: إزالة <meta>, <style>, <script>, <link>, <title> tags بمحتواها
        html = html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
        html = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
        html = html.replace(/<(meta|link|title)[^>]*\/?>/gi, '');
        html = html.replace(/<title[^>]*>[\s\S]*?<\/title>/gi, '');
        html = html.replace(/<!doctype[^>]*>/gi, '');

        const ALLOWED_TAGS = new Set([
            'b', 'strong', 'em', 'i', 'u', 's', 'del', 'strike',
            'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'a', 'blockquote',
            'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'colgroup', 'col', 'div', 'br', 'p',
        ]);

        // التاجات اللي نشيلها ونحافظ على محتواها (unwrap)
        const UNWRAP_TAGS = new Set([
            'span', 'font', 'section', 'article', 'header', 'footer',
            'main', 'aside', 'nav', 'figure', 'figcaption', 'mark',
            'small', 'big', 'center', 'abbr', 'cite', 'code', 'pre',
            'sub', 'sup', 'details', 'summary', 'label',
        ]);

        const ALLOWED_ATTRS = {
            'a':     ['href', 'title', 'target'],
            'img':   ['src', 'alt', 'width', 'height'],
            'table': ['class', 'data-pro-table'],
            'th':    ['colspan', 'rowspan', 'class'],
            'td':    ['colspan', 'rowspan', 'class'],
            'tr':    ['class'],
            'col':   ['style'],
            'div':   [],
        };

        const temp = document.createElement('div');
        temp.innerHTML = html;

        // الخطوة 4: unwrap كل التاجات الزائدة (span, font, إلخ) بشكل آمن
        let unwrapFound = true;
        let safetyCounter = 0;
        while (unwrapFound && safetyCounter < 100) {
            safetyCounter++;
            unwrapFound = false;
            const allElements = temp.querySelectorAll('*');
            for (let i = 0; i < allElements.length; i++) {
                const el = allElements[i];
                const tag = el.tagName.toLowerCase();
                if (UNWRAP_TAGS.has(tag)) {
                    while (el.firstChild) {
                        el.parentNode.insertBefore(el.firstChild, el);
                    }
                    el.parentNode.removeChild(el);
                    unwrapFound = true;
                    break;
                }
            }
        }

        // الخطوة 5: تنظيف التاجات الغير مسموحة وإزالة الـ attributes
        const clean = (node) => {
            const children = Array.from(node.childNodes);
            children.forEach(child => {
                if (child.nodeType === Node.COMMENT_NODE) {
                    node.removeChild(child);
                    return;
                }

                if (child.nodeType === Node.ELEMENT_NODE) {
                    const tag = child.tagName.toLowerCase();

                    if (!ALLOWED_TAGS.has(tag)) {
                        const text = document.createTextNode(child.textContent);
                        node.replaceChild(text, child);
                        return;
                    }

                    // إزالة كل الـ attributes الغير مسموحة
                    const allowed = ALLOWED_ATTRS[tag] || [];
                    Array.from(child.attributes).forEach(attr => {
                        if (!allowed.includes(attr.name)) {
                            child.removeAttribute(attr.name);
                        }
                    });

                    // التحقق من أمان الروابط
                    if (tag === 'a') {
                        const href = child.getAttribute('href') || '';
                        if (!this._isSafeUrl(href)) child.removeAttribute('href');
                    }
                    if (tag === 'img') {
                        const src = child.getAttribute('src') || '';
                        if (!this._isSafeUrl(src)) child.removeAttribute('src');
                    }

                    // تحويل <p> لـ <div>
                    if (tag === 'p') {
                        const div = document.createElement('div');
                        while (child.firstChild) {
                            div.appendChild(child.firstChild);
                        }
                        node.replaceChild(div, child);
                        clean(div);
                        return;
                    }

                    clean(child);
                }
            });
        };

        clean(temp);

        // إزالة الـ divs الفارغة
        temp.querySelectorAll('div:empty, p:empty').forEach(el => el.remove());

        return temp.innerHTML;
    }

    _isSafeUrl(url) {
        if (!url) return false;
        if (url.startsWith('/') || url.startsWith('#')) return true;
        if (url.startsWith('mailto:')) return true;
        try {
            const parsed = new URL(url);
            return ['http:', 'https:'].includes(parsed.protocol);
        } catch {
            return false;
        }
    }

    // ─── Toolbar State ─────────────────────────────────────────────────────────
    _updateToolbarState() {
        const stateMap = {
            'bold':          () => document.queryCommandState('bold'),
            'italic':        () => document.queryCommandState('italic'),
            'underline':     () => document.queryCommandState('underline'),
            'strikethrough': () => document.queryCommandState('strikeThrough'),
            'ul':            () => document.queryCommandState('insertUnorderedList'),
            'ol':            () => document.queryCommandState('insertOrderedList'),
        };

        const blockValue = document.queryCommandValue('formatBlock').toLowerCase();
        const alignValue = document.queryCommandValue('justifyContent').toLowerCase();

        this.toolbar.querySelectorAll('.pro-editor-btn[data-toggle]').forEach(btn => {
            const action = btn.getAttribute('data-action');
            const value = btn.getAttribute('data-value');
            const id = btn.id.split('-').pop();

            let active = false;

            if (action === 'formatBlock' && value) {
                active = blockValue === value;
            } else if (stateMap[id]) {
                active = stateMap[id]();
            }

            btn.classList.toggle('is-active', active);
            btn.setAttribute('aria-pressed', active ? 'true' : 'false');
        });

        // Update alignment buttons
        this.toolbar.querySelectorAll('.pro-editor-btn[data-action^="justify"]').forEach(btn => {
            const action = btn.getAttribute('data-action');
            let active = false;

            if (action === 'justifyRight') active = alignValue === 'right';
            else if (action === 'justifyCenter') active = alignValue === 'center';
            else if (action === 'justifyLeft') active = alignValue === 'left';
            else if (action === 'justifyFull') active = alignValue === 'justify';

            btn.classList.toggle('is-active', active);
            btn.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
    }

    // ─── Update Font Size Display ──────────────────────────────────────────────
    _updateFontSizeDisplay() {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) {
            this._fontSizeSelect.value = '';
            return;
        }

        const range = selection.getRangeAt(0);
        const container = range.commonAncestorContainer;
        const element = container.nodeType === Node.TEXT_NODE ? container.parentElement : container;

        // Get computed font size
        const computedStyle = window.getComputedStyle(element);
        const fontSize = computedStyle.fontSize; // e.g., "14px"
        const fontSizeValue = parseInt(fontSize);

        // Find matching size in our list
        const matchingSize = ProfessionalHTMLEditor.FONT_SIZES.find(s => s.value === fontSizeValue);
        
        if (matchingSize) {
            this._fontSizeSelect.value = matchingSize.value;
        } else {
            this._fontSizeSelect.value = '';
        }
    }

    // ─── Word Count ────────────────────────────────────────────────────────────
    _updateWordCount() {
        const text = this.editorArea.innerText || '';
        const words = text.trim().split(/\s+/).filter(w => w.length > 0);
        const count = words.length;
        const charCount = text.length;
        this._wordCountEl.textContent = `${count} كلمة | ${charCount} حرف`;
    }

    // ─── Sync ──────────────────────────────────────────────────────────────────
    _syncToTextarea() {
        if (this.hiddenTextarea) {
            this.hiddenTextarea.value = this.editorArea.innerHTML;
        }
        if (this.textArea) {
            this.textArea.value = this.editorArea.innerHTML;
        }
    }

    _syncFromTextarea() {
        const html = this.textArea.value;
        const sanitized = this._sanitize(html);
        this.editorArea.innerHTML = sanitized;
        this._syncToTextarea();
        this._updateWordCount();
        this._bindAllTableEvents();
        this._bindImageEvents();
    }

    setContent(html) {
        if (this.editorArea) {
            this.editorArea.innerHTML = this._sanitize(html);
            this._syncToTextarea();
            this._updateWordCount();
            this._bindAllTableEvents();
            this._bindImageEvents();
        } else if (this.hiddenTextarea) {
            this.hiddenTextarea.value = html;
        }
    }

    // ─── Tab Switching ─────────────────────────────────────────────────────────
    _switchTab(tabName) {
        const tabs = this.container.querySelectorAll('.pro-editor-tab');
        const panels = this.container.querySelectorAll('.pro-editor-panel');

        tabs.forEach(tab => {
            const isActive = tab.textContent.includes(tabName === 'visual' ? 'محرر' : 'HTML');
            tab.classList.toggle('is-active', isActive);
            tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });

        panels.forEach(panel => {
            const isActive = (tabName === 'visual' && panel.id.includes('visual')) ||
                           (tabName === 'text' && panel.id.includes('text'));
            panel.classList.toggle('is-active', isActive);
        });

        // Sync content when switching
        if (tabName === 'text') {
            this._syncToTextarea();
            this.textArea.focus();
        } else {
            this._syncFromTextarea();
            this.editorArea.focus();
        }

        // Show/hide toolbar based on tab
        this.toolbar.style.display = tabName === 'visual' ? 'flex' : 'none';
    }

    // ─── Public API ────────────────────────────────────────────────────────────
    getContent() {
        return this._sanitize(this.editorArea.innerHTML);
    }

    setContent(html) {
        this.editorArea.innerHTML = this._sanitize(html);
        this._syncToTextarea();
        this._updateWordCount();
    }

    clear() {
        this.editorArea.innerHTML = '';
        this._syncToTextarea();
        this._updateWordCount();
    }

    // ─── Icon Picker ───────────────────────────────────────────────────────────
    static ICON_CATEGORIES = [
        {
            name: 'جامعات وأكاديمي',
            icons: [
                { id: 'graduation', label: 'قبعة التخرج', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5"/></svg>' },
                { id: 'university', label: 'مبنى جامعي', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7h20L12 2z"/><rect x="4" y="10" width="3" height="8"/><rect x="10.5" y="10" width="3" height="8"/><rect x="17" y="10" width="3" height="8"/><path d="M2 20h20"/><path d="M2 7h20"/></svg>' },
                { id: 'book-open', label: 'كتاب مفتوح', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>' },
                { id: 'book-closed', label: 'كتاب', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>' },
                { id: 'library', label: 'مكتبة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h2v16H3z"/><path d="M7 4h2v16H7z"/><path d="M11 4h2v16h-2z"/><path d="M15 4h2v12h-2z"/><path d="M19 4h2v16h-2z"/></svg>' },
                { id: 'certificate', label: 'شهادة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="14" rx="2"/><path d="M7 21l5-3 5 3v-4H7v4z"/><line x1="7" y1="8" x2="17" y2="8"/><line x1="7" y1="11" x2="13" y2="11"/></svg>' },
                { id: 'medal', label: 'ميدالية', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="15" r="5"/><path d="M8.21 13.89L7 2h10l-1.21 11.89"/><path d="M12 10v5"/></svg>' },
                { id: 'school', label: 'مدرسة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l7 4v4H5V6l7-4z"/><rect x="3" y="10" width="18" height="10"/><rect x="9" y="14" width="6" height="6"/><line x1="12" y1="2" x2="12" y2="5"/></svg>' },
                { id: 'pen-tool', label: 'قلم', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l7.586 7.586"/><circle cx="11" cy="11" r="2"/></svg>' },
                { id: 'microscope', label: 'مجهر', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0-1-13"/><path d="M9 14h1"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/></svg>' },
                { id: 'atom', label: 'ذرة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"/><path d="M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9-4.54-4.52-9.87-6.54-11.9-4.5-2.04 2.03-.02 7.36 4.5 11.9 4.54 4.52 9.87 6.54 11.9 4.5z"/><path d="M15.7 15.7c4.52-4.54 6.54-9.87 4.5-11.9-2.03-2.04-7.36-.02-11.9 4.5-4.52 4.54-6.54 9.87-4.5 11.9 2.03 2.04 7.36.02 11.9-4.5z"/></svg>' },
                { id: 'flask', label: 'دورق', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6"/><path d="M10 3v7.4a2 2 0 0 1-.5 1.3L4 19a2 2 0 0 0 1.5 3h13a2 2 0 0 0 1.5-3l-5.5-7.3a2 2 0 0 1-.5-1.3V3"/></svg>' },
                { id: 'notebook', label: 'دفتر', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 6h4"/><path d="M2 10h4"/><path d="M2 14h4"/><path d="M2 18h4"/><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="12" y1="6" x2="16" y2="6"/><line x1="12" y1="10" x2="16" y2="10"/></svg>' },
                { id: 'presentation', label: 'عرض تقديمي', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h20"/><rect x="4" y="3" width="16" height="12" rx="1"/><path d="M12 15v4"/><path d="M8 19h8"/></svg>' },
                { id: 'ruler', label: 'مسطرة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21.73 18l-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3z"/><line x1="12" y1="9" x2="12" y2="13"/></svg>' },
                { id: 'calculator', label: 'آلة حاسبة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="8.01" y2="10"/><line x1="12" y1="10" x2="12.01" y2="10"/><line x1="16" y1="10" x2="16.01" y2="10"/><line x1="8" y1="14" x2="8.01" y2="14"/><line x1="12" y1="14" x2="12.01" y2="14"/><line x1="16" y1="14" x2="16.01" y2="14"/><line x1="8" y1="18" x2="8.01" y2="18"/><line x1="12" y1="18" x2="12.01" y2="18"/><line x1="16" y1="18" x2="16.01" y2="18"/></svg>' },
                { id: 'globe-2', label: 'عالمي', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><line x1="2" y1="8" x2="22" y2="8"/><line x1="2" y1="16" x2="22" y2="16"/></svg>' },
            ]
        },
        {
            name: 'عام ومؤسسي',
            icons: [
                { id: 'globe', label: 'كرة أرضية', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>' },
                { id: 'map-pin', label: 'موقع', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>' },
                { id: 'calendar', label: 'تقويم', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>' },
                { id: 'clock', label: 'ساعة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' },
                { id: 'users', label: 'مجموعة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>' },
                { id: 'user', label: 'شخص', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' },
                { id: 'mail', label: 'بريد', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>' },
                { id: 'phone', label: 'هاتف', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>' },
                { id: 'star', label: 'نجمة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>' },
                { id: 'award', label: 'جائزة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/></svg>' },
                { id: 'target', label: 'هدف', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>' },
                { id: 'briefcase', label: 'حقيبة عمل', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>' },
            ]
        },
        {
            name: 'تعليم وبحث',
            icons: [
                { id: 'lightbulb', label: 'فكرة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A7 7 0 1 0 7.5 11.5c.76.76 1.23 1.52 1.41 2.5"/></svg>' },
                { id: 'clipboard', label: 'حافظة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/></svg>' },
                { id: 'file-text', label: 'مستند', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>' },
                { id: 'search', label: 'بحث', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>' },
                { id: 'bar-chart', label: 'رسم بياني', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>' },
                { id: 'trending-up', label: 'نمو', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>' },
                { id: 'layers', label: 'طبقات', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>' },
                { id: 'cpu', label: 'تقنية', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>' },
                { id: 'wifi', label: 'اتصال', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>' },
                { id: 'shield', label: 'درع', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>' },
                { id: 'heart', label: 'قلب', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>' },
                { id: 'check-circle', label: 'تم', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' },
            ]
        },
        {
            name: 'طب وصحة',
            icons: [
                { id: 'stethoscope', label: 'سماعة طبيب', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 6 6h.87a2 2 0 0 0 1.42-.59l.13-.12a2 2 0 0 0 .58-1.42V18"/><circle cx="17" cy="15" r="2"/></svg>' },
                { id: 'pill', label: 'حبة دواء', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.5 1.5l-8 8a4.95 4.95 0 0 0 7 7l8-8a4.95 4.95 0 0 0-7-7z"/><line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/></svg>' },
                { id: 'activity', label: 'نبض', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>' },
                { id: 'thermometer', label: 'ميزان حرارة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>' },
                { id: 'hospital', label: 'مستشفى', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 12h6"/><path d="M12 9v6"/></svg>' },
                { id: 'dna', label: 'حمض نووي', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 15c6.667-6 13.333 0 20-6"/><path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"/><path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"/><path d="M17 6l-2.5-2.5"/><path d="M14 8l-1-1"/><path d="M7 18l2.5 2.5"/><path d="M3.5 14.5l.5.5"/><path d="M20 9l.5.5"/><path d="M6.5 12.5l1 1"/><path d="M16.5 10.5l1 1"/></svg>' },
                { id: 'syringe', label: 'حقنة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2l4 4"/><path d="M17 7l3-3"/><path d="M19 9l-7 7-4-4 7-7"/><path d="M8 12l-4 4 4 4 4-4"/><path d="M2 22l2-2"/></svg>' },
                { id: 'eye-medical', label: 'عين', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>' },
                { id: 'brain', label: 'دماغ', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2z"/></svg>' },
                { id: 'tooth', label: 'سن', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5.5c-1.5-2-4-2.5-5.5-1S4 8 5.5 10c1 1.5 2 3.5 2 5.5 0 3 1 5.5 2.5 5.5s2-1.5 2-3.5c0-1 .5-1.5 1-1.5s1 .5 1 1.5c0 2 .5 3.5 2 3.5s2.5-2.5 2.5-5.5c0-2 1-4 2-5.5C22 8 22 5.5 20.5 4.5S15 3.5 12 5.5z"/></svg>' },
            ]
        },
        {
            name: 'هندسة وتقنية',
            icons: [
                { id: 'settings', label: 'إعدادات', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>' },
                { id: 'tool', label: 'أداة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>' },
                { id: 'zap', label: 'طاقة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>' },
                { id: 'database', label: 'قاعدة بيانات', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>' },
                { id: 'server', label: 'خادم', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>' },
                { id: 'code-2', label: 'كود', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>' },
                { id: 'terminal', label: 'طرفية', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>' },
                { id: 'monitor', label: 'شاشة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>' },
                { id: 'smartphone', label: 'جوال', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>' },
                { id: 'hard-drive', label: 'قرص صلب', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="12" x2="2" y2="12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/><line x1="6" y1="16" x2="6.01" y2="16"/><line x1="10" y1="16" x2="10.01" y2="16"/></svg>' },
                { id: 'cloud', label: 'سحابة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>' },
                { id: 'lock', label: 'قفل', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>' },
            ]
        },
        {
            name: 'أسهم واتجاهات',
            icons: [
                { id: 'arrow-right', label: 'سهم يمين', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>' },
                { id: 'arrow-left', label: 'سهم يسار', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>' },
                { id: 'arrow-up', label: 'سهم أعلى', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>' },
                { id: 'arrow-down', label: 'سهم أسفل', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>' },
                { id: 'chevron-right', label: 'شيفرون يمين', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>' },
                { id: 'chevron-left', label: 'شيفرون يسار', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>' },
                { id: 'refresh', label: 'تحديث', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>' },
                { id: 'external-link', label: 'رابط خارجي', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>' },
                { id: 'download', label: 'تحميل', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>' },
                { id: 'upload', label: 'رفع', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>' },
            ]
        },
        {
            name: 'أشكال ورموز',
            icons: [
                { id: 'circle', label: 'دائرة', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>' },
                { id: 'square', label: 'مربع', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>' },
                { id: 'triangle', label: 'مثلث', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>' },
                { id: 'hexagon', label: 'سداسي', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>' },
                { id: 'plus', label: 'زائد', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>' },
                { id: 'minus', label: 'ناقص', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>' },
                { id: 'x-mark', label: 'إكس', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' },
                { id: 'check', label: 'صح', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>' },
                { id: 'info', label: 'معلومات', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>' },
                { id: 'alert-triangle', label: 'تحذير', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>' },
                { id: 'flag', label: 'علم', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>' },
                { id: 'bookmark', label: 'إشارة مرجعية', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>' },
            ]
        },
    ];

    _insertIcon() {
        // حفظ الـ selection الحالي قبل فتح المودال
        const selection = window.getSelection();
        let savedRange = null;
        if (selection && selection.rangeCount > 0) {
            savedRange = selection.getRangeAt(0).cloneRange();
        }

        const overlay = document.createElement('div');
        overlay.className = 'pro-editor-modal-overlay';

        // بناء المودال
        let categoriesHTML = '';
        ProfessionalHTMLEditor.ICON_CATEGORIES.forEach((cat, catIdx) => {
            categoriesHTML += `
                <div class="pro-icon-category" data-category="${catIdx}">
                    <h4 class="pro-icon-category-title">${cat.name}</h4>
                    <div class="pro-icon-grid">
                        ${cat.icons.map(icon => `
                            <button type="button" class="pro-icon-item" data-icon-id="${icon.id}" title="${icon.label}" aria-label="${icon.label}">
                                <span class="pro-icon-preview">${icon.svg}</span>
                                <span class="pro-icon-label">${icon.label}</span>
                            </button>
                        `).join('')}
                    </div>
                </div>
            `;
        });

        overlay.innerHTML = `
            <div class="pro-editor-modal pro-icon-modal" role="dialog" aria-modal="true" aria-label="إدراج أيقونة">
                <div class="pro-editor-modal-header">
                    <span>إدراج أيقونة</span>
                    <button type="button" class="pro-modal-close" aria-label="إغلاق">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>
                <div class="pro-editor-modal-body pro-icon-modal-body">
                    <div class="pro-icon-search-wrapper">
                        <input type="text" class="pro-icon-search" placeholder="ابحث عن أيقونة..." dir="rtl" />
                    </div>
                    <div class="pro-icon-size-control">
                        <label class="pro-icon-size-label">الحجم:</label>
                        <select class="pro-icon-size-select">
                            <option value="16">صغير (16px)</option>
                            <option value="20">وسط (20px)</option>
                            <option value="24" selected>عادي (24px)</option>
                            <option value="32">كبير (32px)</option>
                            <option value="48">كبير جداً (48px)</option>
                            <option value="64">ضخم (64px)</option>
                        </select>
                        <label class="pro-icon-size-label">اللون:</label>
                        <input type="color" class="pro-icon-color-input" value="#0B2D4D" />
                    </div>
                    <div class="pro-icon-categories-container">
                        ${categoriesHTML}
                    </div>
                </div>
            </div>
        `;

        const close = () => overlay.remove();
        overlay.querySelector('.pro-modal-close').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
        overlay.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });

        // البحث
        const searchInput = overlay.querySelector('.pro-icon-search');
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.trim().toLowerCase();
            const items = overlay.querySelectorAll('.pro-icon-item');
            const categories = overlay.querySelectorAll('.pro-icon-category');

            items.forEach(item => {
                const label = item.getAttribute('title').toLowerCase();
                const id = item.getAttribute('data-icon-id').toLowerCase();
                const match = !query || label.includes(query) || id.includes(query);
                item.style.display = match ? '' : 'none';
            });

            // إخفاء الفئات الفارغة
            categories.forEach(cat => {
                const visibleItems = cat.querySelectorAll('.pro-icon-item:not([style*="display: none"])');
                cat.style.display = visibleItems.length > 0 ? '' : 'none';
            });
        });

        // إدراج الأيقونة عند النقر
        overlay.querySelectorAll('.pro-icon-item').forEach(item => {
            item.addEventListener('click', () => {
                const iconId = item.getAttribute('data-icon-id');
                const size = overlay.querySelector('.pro-icon-size-select').value;
                const color = overlay.querySelector('.pro-icon-color-input').value;

                // البحث عن الأيقونة
                let iconSvg = null;
                for (const cat of ProfessionalHTMLEditor.ICON_CATEGORIES) {
                    const found = cat.icons.find(i => i.id === iconId);
                    if (found) { iconSvg = found.svg; break; }
                }
                if (!iconSvg) return;

                // تعديل الـ SVG بالحجم واللون
                const parser = new DOMParser();
                const svgDoc = parser.parseFromString(iconSvg, 'image/svg+xml');
                const svgEl = svgDoc.querySelector('svg');
                svgEl.setAttribute('width', size);
                svgEl.setAttribute('height', size);
                svgEl.setAttribute('style', `display:inline-block;vertical-align:middle;color:${color};`);
                svgEl.setAttribute('stroke', color);

                // إنشاء span wrapper
                const wrapper = document.createElement('span');
                wrapper.className = 'pro-inserted-icon';
                wrapper.setAttribute('contenteditable', 'false');
                wrapper.style.display = 'inline-block';
                wrapper.style.verticalAlign = 'middle';
                wrapper.style.lineHeight = '0';
                wrapper.innerHTML = svgEl.outerHTML;

                // إدراج في المحرر
                this.editorArea.focus();
                if (savedRange) {
                    const sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(savedRange);
                }

                const sel = window.getSelection();
                if (sel && sel.rangeCount > 0) {
                    const range = sel.getRangeAt(0);
                    range.deleteContents();
                    range.insertNode(wrapper);
                    // وضع الكيرسر بعد الأيقونة
                    range.setStartAfter(wrapper);
                    range.collapse(true);
                    sel.removeAllRanges();
                    sel.addRange(range);
                } else {
                    this.editorArea.appendChild(wrapper);
                }

                this._syncToTextarea();
                close();
            });
        });

        document.body.appendChild(overlay);
        searchInput.focus();
    }

    // ─── Minimal/Compact Mode Toggle ─────────────────────────────────────────
    _toggleMinimalMode() {
        this._isMinimalMode = !this._isMinimalMode;
        this._updateMinimalModeUI();
    }

    _applyMinimalMode() {
        // تطبيق الوضع المصغر بدون toggle
        this._isMinimalMode = true;
        this._updateMinimalModeUI();
    }

    _updateMinimalModeUI() {
        this._compactBtn.classList.toggle('is-active', this._isMinimalMode);
        this._compactBtn.setAttribute('aria-pressed', this._isMinimalMode ? 'true' : 'false');
        this.toolbar.classList.toggle('is-minimal', this._isMinimalMode);

        // Toggle visibility of toolbar buttons and groups
        const allBtns = this.toolbar.querySelectorAll('.pro-editor-btn:not(.pro-editor-mode-btn):not(.pro-editor-compact-btn)');
        const allSeps = this.toolbar.querySelectorAll('.pro-editor-separator');
        const fontSizeSelect = this._fontSizeSelect;
        const lineHeightSelect = this._lineHeightSelect;
        const fontColorBtn = this._fontColorBtn;

        if (this._isMinimalMode) {
            // إخفاء كل الأزرار ما عدا الأساسية
            allBtns.forEach(btn => {
                const btnId = (btn.id || '').split('-').pop();
                if (ProfessionalHTMLEditor.MINIMAL_TOOLBAR_IDS.has(btnId)) {
                    btn.style.display = '';
                } else {
                    btn.style.display = 'none';
                }
            });

            // إخفاء ارتفاع السطر
            if (lineHeightSelect) lineHeightSelect.parentElement.style.display = 'none';

            // إظهار حجم الخط ولون الخط
            if (fontSizeSelect) fontSizeSelect.parentElement.style.display = '';
            if (fontColorBtn) fontColorBtn.parentElement.style.display = '';

            // إخفاء الفواصل الزائدة
            allSeps.forEach(sep => {
                const prev = sep.previousElementSibling;
                const next = sep.nextElementSibling;
                // إخفاء الفاصل لو المجموعة اللي قبله أو بعده مخفية
                const prevVisible = prev && prev.style.display !== 'none' && this._hasVisibleChildren(prev);
                const nextVisible = next && next.style.display !== 'none' && this._hasVisibleChildren(next);
                sep.style.display = (prevVisible && nextVisible) ? '' : 'none';
            });
        } else {
            // إظهار كل شيء
            allBtns.forEach(btn => btn.style.display = '');
            allSeps.forEach(sep => sep.style.display = '');
            if (fontSizeSelect) fontSizeSelect.parentElement.style.display = '';
            if (lineHeightSelect) lineHeightSelect.parentElement.style.display = '';
            if (fontColorBtn) fontColorBtn.parentElement.style.display = '';
        }
    }

    _hasVisibleChildren(el) {
        if (!el) return false;
        if (el.classList && el.classList.contains('pro-editor-toolbar-group')) {
            const children = el.querySelectorAll('.pro-editor-btn, select');
            return Array.from(children).some(c => c.style.display !== 'none');
        }
        return el.style.display !== 'none';
    }

    // ─── Mode Switching ────────────────────────────────────────────────────────
    _switchMode(mode) {
        const panels = this.container.querySelectorAll('.pro-editor-panel');

        panels.forEach(panel => {
            const isActive = panel.getAttribute('data-mode') === mode;
            panel.classList.toggle('is-active', isActive);
        });

        // Update mode button
        this._modeBtn.setAttribute('data-mode', mode);
        this._modeBtn.classList.toggle('is-active', mode === 'text');

        // Toggle beautify button visibility
        if (this._beautifyBtn) {
            this._beautifyBtn.style.display = mode === 'text' ? 'inline-flex' : 'none';
        }

        // Sync content when switching
        if (mode === 'text') {
            this._syncToTextarea();
            this.textArea.focus();
        } else {
            this._syncFromTextarea();
            this.editorArea.focus();
        }
    }

    _beautifyCode() {
        if (this._modeBtn.getAttribute('data-mode') !== 'text') return;
        const currentHTML = this.textArea.value;
        const formatted = this._beautifyHTML(currentHTML);
        this.textArea.value = formatted;
        this._syncFromTextarea();
    }

    _beautifyHTML(html) {
        var formatted = '';
        var reg = /(<[^>]+>)/g;
        var elements = html.replace(reg, '\r\n$1\r\n').split('\r\n');
        var indent = 0;
        var pad = '    '; // 4 spaces
        elements.forEach(function(el) {
            var elTrimmed = el.trim();
            if (!elTrimmed) return;
            
            // Check if it's a closing tag
            if (elTrimmed.match(/^<\/\w/)) {
                indent--;
            }
            
            // Add indentation
            var padding = '';
            for (var i = 0; i < indent; i++) {
                padding += pad;
            }
            
            formatted += padding + elTrimmed + '\r\n';
            
            // Check if it's an opening tag (and not self-closing or void)
            if (elTrimmed.match(/^<\w[^>]*[^\/]>$/) && !elTrimmed.match(/^<(br|hr|img|input|link|meta)/i)) {
                indent++;
            }
        });
        return formatted.trim();
    }
}


// ─── Django Widget Bootstrap ───────────────────────────────────────────────────
// Looks for <div class="pro-editor-mount"> elements injected by the Django template
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.pro-editor-mount').forEach(mount => {
        if (mount.dataset.initialized) return;
        mount.dataset.initialized = 'true';
        new ProfessionalHTMLEditor(mount);
    });
});

// Export for module environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProfessionalHTMLEditor;
}
