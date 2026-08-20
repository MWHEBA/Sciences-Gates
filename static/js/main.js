/**
 * Main JavaScript file
 * Global initialization and utilities
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize formset management for dynamic forms
    initializeFormsets();
    
    // Replicated Educate Template Header & Mobile Sidebar JS
    initializeHeaderActions();
    
    // Initialize YouTube Video Popups
    initializeVideoPopups();

    // Initialize floating buttons behavior (fade on idle, show on scroll)
    initializeFloatingButtons();

    // Initialize clickable table rows
    initializeTableRedirects();

    // Initialize global auto-slugify for creation forms
    initializeAutoSlugify();

    // Initialize CSRF Multi-Tab Sync, Double-Submit Lock, & Draft Auto-Save
    initializeCsrfAndFormSync();
    initializeFormDraftAutoSave();
    initializeFormSubmitLock();
});

/**
 * Initialize all formsets on the page
 */
function initializeFormsets() {
    // Find all formset containers and initialize them
    const formsetContainers = document.querySelectorAll('[data-formset]');
    formsetContainers.forEach(container => {
        const formsetPrefix = container.getAttribute('data-formset');
        const itemName = container.getAttribute('data-item-name') || 'Item';
        new FormsetManager(formsetPrefix, itemName);
    });
}

/**
 * Initialize header sticky and off-canvas sidebar menu
 */
function initializeHeaderActions() {
    const headerSticky = document.getElementById('header-sticky');
    const menuBarBtn = document.getElementById('mobile-menu-btn');
    const offcanvasArea = document.querySelector('.it-offcanvas-area');
    const offcanvas = document.querySelector('.itoffcanvas');
    const closeBtn = document.querySelector('.close-btn');
    const bodyOverlay = document.querySelector('.body-overlay');
    const desktopMenu = document.querySelector('.it-menu-content');
    const mobileMenu = document.querySelector('.it-menu-mobile');

    // 1. الهيدر المثبت (Sticky Header)
    if (headerSticky) {
        window.addEventListener('scroll', function() {
            if (window.scrollY >= 400) {
                headerSticky.classList.remove('header-sticky-out');
                headerSticky.classList.add('header-sticky');
            } else if (window.scrollY < 100) {
                // لو قربنا من فوق خالص، بنشيل الكلاسين فوراً عشان نمنع تداخل الهيدر المثبت مع الهيدر الطبيعي
                headerSticky.classList.remove('header-sticky');
                headerSticky.classList.remove('header-sticky-out');
            } else {
                // لما السكرول يرجع لفوق ويبقى بين 100 و 400، بنشغل تأثير الاختفاء التدريجي
                if (headerSticky.classList.contains('header-sticky')) {
                    headerSticky.classList.remove('header-sticky');
                    headerSticky.classList.add('header-sticky-out');
                    
                    // بنشيل كلاس الاختفاء بعد ما الأنيميشن يخلص (950 مللي ثانية)
                    setTimeout(function() {
                        // بنتأكد إننا مارجعناش عملنا سكرول لتحت تاني في الوقت ده
                        if (window.scrollY < 400) {
                            headerSticky.classList.remove('header-sticky-out');
                        }
                    }, 950);
                }
            }
        });
    }

    // 2. Populate Mobile Menu with Dropdown Toggle Logic
    if (desktopMenu && mobileMenu) {
        mobileMenu.innerHTML = desktopMenu.outerHTML;
        
        // Add dropdown toggle buttons for mobile menu submenus
        const hasDropdownLinks = mobileMenu.querySelectorAll('.has-dropdown > a');
        hasDropdownLinks.forEach(link => {
            const arrowBtn = document.createElement('button');
            arrowBtn.type = 'button';
            arrowBtn.className = 'dropdown-toggle-btn';
            arrowBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"></path></svg>';
            link.appendChild(arrowBtn);
            
            arrowBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const parentLi = link.parentElement;
                const submenu = parentLi.querySelector('.it-submenu');
                
                arrowBtn.classList.toggle('dropdown-opened');
                link.classList.toggle('expanded');
                parentLi.classList.toggle('dropdown-opened');
                
                if (submenu) {
                    if (submenu.style.display === 'block') {
                        submenu.style.display = 'none';
                    } else {
                        submenu.style.display = 'block';
                    }
                }
            });
        });
    }

    // 3. Mobile Canvas Toggles
    if (menuBarBtn && offcanvas && bodyOverlay) {
        menuBarBtn.addEventListener('click', function(e) {
            e.preventDefault();
            offcanvas.classList.add('opened');
            bodyOverlay.classList.add('apply');
            if (offcanvasArea) offcanvasArea.classList.add('opened');
        });
    }

    const closeMenu = function() {
        if (offcanvas) offcanvas.classList.remove('opened');
        if (bodyOverlay) bodyOverlay.classList.remove('apply');
        if (offcanvasArea) offcanvasArea.classList.remove('opened');
    };

    if (closeBtn) {
        closeBtn.addEventListener('click', closeMenu);
    }
    if (bodyOverlay) {
        bodyOverlay.addEventListener('click', closeMenu);
    }

    // 4. Language Dropdown Toggle
    const langDropdown = document.getElementById('it-header-2-lang');
    if (langDropdown) {
        langDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
            langDropdown.classList.toggle('open');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!langDropdown.contains(e.target)) {
                langDropdown.classList.remove('open');
            }
        });
    }
}

/**
 * Extract YouTube Embed URL from standard watch links
 */
function getYouTubeEmbedUrl(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    if (match && match[2].length === 11) {
        return 'https://www.youtube.com/embed/' + match[2] + '?autoplay=1';
    }
    return url;
}

/**
 * Initialize YouTube Video Popup Modals in Vanilla JS
 */
function initializeVideoPopups() {
    const videoLinks = document.querySelectorAll('.popup-video');
    videoLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const videoUrl = link.getAttribute('href');
            if (!videoUrl) return;
            
            const isLocalVideo = videoUrl.endsWith('.mp4') || videoUrl.includes('.mp4');
            
            // Create modal overlay
            const modalOverlay = document.createElement('div');
            modalOverlay.className = 'video-modal-overlay';
            modalOverlay.style.position = 'fixed';
            modalOverlay.style.top = '0';
            modalOverlay.style.left = '0';
            modalOverlay.style.width = '100%';
            modalOverlay.style.height = '100%';
            modalOverlay.style.backgroundColor = 'rgba(11, 45, 77, 0.85)';
            modalOverlay.style.display = 'flex';
            modalOverlay.style.alignItems = 'center';
            modalOverlay.style.justifyContent = 'center';
            modalOverlay.style.zIndex = '1000000';
            modalOverlay.style.opacity = '0';
            modalOverlay.style.transition = 'opacity 0.3s ease';
            
            // Create modal content container
            const modalContent = document.createElement('div');
            modalContent.className = 'video-modal-content';
            modalContent.style.position = 'relative';
            modalContent.style.width = '90%';
            modalContent.style.maxWidth = '800px';
            modalContent.style.aspectRatio = '16/9';
            modalContent.style.backgroundColor = '#000';
            modalContent.style.borderRadius = '8px';
            modalContent.style.overflow = 'hidden';
            modalContent.style.boxShadow = '0 20px 50px rgba(0, 0, 0, 0.5)';
            
            // Create close button (positioned left for RTL compatibility)
            const closeBtn = document.createElement('button');
            closeBtn.type = 'button';
            closeBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
            closeBtn.style.position = 'absolute';
            closeBtn.style.top = '-40px';
            closeBtn.style.left = '0';
            closeBtn.style.background = 'none';
            closeBtn.style.border = 'none';
            closeBtn.style.color = '#fff';
            closeBtn.style.fontSize = '24px';
            closeBtn.style.cursor = 'pointer';
            closeBtn.style.outline = 'none';
            closeBtn.setAttribute('aria-label', 'إغلاق الفيديو');
            
            // Create media element
            let mediaElement;
            if (isLocalVideo) {
                mediaElement = document.createElement('video');
                mediaElement.src = videoUrl;
                mediaElement.controls = true;
                mediaElement.autoplay = true;
                mediaElement.style.width = '100%';
                mediaElement.style.height = '100%';
                mediaElement.style.outline = 'none';
            } else {
                const embedUrl = getYouTubeEmbedUrl(videoUrl);
                mediaElement = document.createElement('iframe');
                mediaElement.src = embedUrl;
                mediaElement.style.width = '100%';
                mediaElement.style.height = '100%';
                mediaElement.style.border = 'none';
                mediaElement.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
                mediaElement.allowFullscreen = true;
            }
            
            modalContent.appendChild(closeBtn);
            modalContent.appendChild(mediaElement);
            modalOverlay.appendChild(modalContent);
            document.body.appendChild(modalOverlay);
            
            // Fade in transition
            setTimeout(() => {
                modalOverlay.style.opacity = '1';
            }, 10);
            
            // Prevent body scrolling
            document.body.style.overflow = 'hidden';
            
            const closeModal = function() {
                modalOverlay.style.opacity = '0';
                setTimeout(() => {
                    modalOverlay.remove();
                    document.body.style.overflow = '';
                }, 300);
            };
            
            closeBtn.addEventListener('click', closeModal);
            modalOverlay.addEventListener('click', function(event) {
                if (event.target === modalOverlay) {
                    closeModal();
                }
            });
            
            // ESC key support
            const escListener = function(event) {
                if (event.key === 'Escape') {
                    closeModal();
                    document.removeEventListener('keydown', escListener);
                }
            };
            document.addEventListener('keydown', escListener);
        });
    });
}

/**
 * Initialize global floating buttons behaviour (WhatsApp, Admin Dashboard, Admin Edit, Reg button)
 * Handles auto-hide on scroll idle and show on scroll/hover.
 */
function initializeFloatingButtons() {
    var floats = document.querySelectorAll('.reg-float-btn, .whatsapp-widget, .admin-dashboard-float, .admin-edit-float');
    if (floats.length === 0) return;

    var scrollTimeout = null;
    var isHovered = false;

    floats.forEach(function (el) {
        el.addEventListener('mouseenter', function () {
            isHovered = true;
            showFloats();
        });
        el.addEventListener('mouseleave', function () {
            isHovered = false;
            resetScrollTimeout();
        });
    });

    function showFloats() {
        floats.forEach(function (el) {
            el.classList.remove('floating-hide');
        });
        if (scrollTimeout) clearTimeout(scrollTimeout);
    }

    function hideFloats() {
        if (isHovered) return;

        // Do not hide if modal is open (Alpine data check)
        var alpineData = document.querySelector('.detail-page-container')?.__x?.$data;
        var regModalOpen = alpineData ? alpineData.openRegModal : false;

        // Check if WhatsApp popup is open
        var waWidget = document.querySelector('.whatsapp-widget');
        var waOpen = waWidget && waWidget.__x && waWidget.__x.$data ? waWidget.__x.$data.open : false;

        if (regModalOpen || waOpen) return;

        floats.forEach(function (el) {
            el.classList.add('floating-hide');
        });
    }

    function resetScrollTimeout() {
        if (scrollTimeout) clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(hideFloats, 4000); // hide after 4 seconds of scroll pause
    }

    window.addEventListener('scroll', function () {
        showFloats();
        resetScrollTimeout();
    }, { passive: true });

    // Initialize timeout on load
    resetScrollTimeout();
}

/**
 * Make table rows with data-row-url clickable, avoiding conflict with action buttons
 */
function initializeTableRedirects() {
    document.addEventListener('click', function(e) {
        // Find if the click or any of its parent elements is a TR with data-row-url
        const row = e.target.closest('tr[data-row-url]');
        if (!row) return;

        // Check if the click target or any of its parents is an interactive element (button, link, input, select, etc.)
        const isInteractive = e.target.closest('a, button, input, select, textarea, [role="button"], .no-redirect');
        
        // If the click is inside an interactive element, let the default behavior happen
        if (isInteractive && isInteractive !== row) {
            return;
        }

        const url = row.getAttribute('data-row-url');
        if (url && url !== '#') {
            window.location.href = url;
        }
    });
}

/**
 * Automatically populates the Slug field based on Title or Name inputs.
 * Runs only on creation forms (form#main-form without data-object-id).
 * Protects manual user edits by disabling auto-fill once the slug is modified,
 * unless the slug field is cleared completely.
 */
function initializeAutoSlugify() {
    const slugInput = document.getElementById('id_slug');
    if (!slugInput) return; // No slug field on this page

    // Check if we are in Edit mode
    const formElement = document.getElementById('main-form') || document.querySelector('form');
    const isEditMode = formElement ? formElement.hasAttribute('data-object-id') : false;
    if (isEditMode) return; // Do not auto-generate slugs when editing existing items (SEO preservation)

    // Find the source field (either 'title' or 'name')
    const sourceInput = document.getElementById('id_name') || document.getElementById('id_title');
    if (!sourceInput) return;

    // Helper to generate a slug (supporting both Arabic and English text)
    const slugify = (text) => {
        return text.trim()
            .toLowerCase()
            .replace(/[^\w\s\u0621-\u064A\u0660-\u0669-]/g, '')
            .replace(/[\s_]+/g, '-')
            .replace(/-+/g, '-');
    };

    // Track the last auto-generated slug to avoid overwriting manual changes
    let lastAutoGeneratedSlug = '';

    sourceInput.addEventListener('input', function() {
        const currentSlug = slugInput.value;
        // Only update if the slug is currently empty OR matches the last auto-generated value
        if (!currentSlug || currentSlug === lastAutoGeneratedSlug) {
            lastAutoGeneratedSlug = slugify(this.value);
            slugInput.value = lastAutoGeneratedSlug;
        }
    });
}

/**
 * Synchronizes the hidden csrfmiddlewaretoken input with the current document.cookie value
 * right before form submission and upon page restore from bfcache (iOS Safari/Chrome),
 * preventing multi-tab and cached CSRF token mismatches.
 */
function syncAllFormsCsrf() {
    const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
    if (cookieMatch && cookieMatch[1]) {
        const liveCsrfToken = cookieMatch[1];
        document.querySelectorAll('input[name="csrfmiddlewaretoken"]').forEach(input => {
            if (input.value !== liveCsrfToken) {
                input.value = liveCsrfToken;
            }
        });
    }
}

function unlockAllSubmitButtons() {
    document.querySelectorAll('form').forEach(f => {
        f.removeAttribute('data-submitting');
    });
    document.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(btn => {
        btn.disabled = false;
        btn.style.pointerEvents = '';
        btn.style.opacity = '';
        btn.style.cursor = '';
        btn.classList.remove('is-loading');
        const originalText = btn.getAttribute('data-original-text');
        if (originalText) {
            btn.innerHTML = originalText;
        }
    });
}

function initializeCsrfAndFormSync() {
    // Sync CSRF on form submit
    document.addEventListener('submit', function(e) {
        syncAllFormsCsrf();
    }, true);

    // Sync CSRF proactively when user interacts with any form field
    document.addEventListener('focusin', function(e) {
        if (e.target && e.target.closest && e.target.closest('form')) {
            syncAllFormsCsrf();
        }
    });

    // Handle iOS WebKit Back-Forward Cache (bfcache) and tab unfreezing
    window.addEventListener('pageshow', function(event) {
        syncAllFormsCsrf();
        unlockAllSubmitButtons();
    });
}

/**
 * Auto-saves public form input drafts to LocalStorage as the student types,
 * and auto-restores data if the browser reloads or disconnects mid-submission.
 */
function initializeFormDraftAutoSave() {
    const publicForms = document.querySelectorAll('form[action*="leads/submit"], form:not([action*="dashboard"]):not([action*="admin"])');
    publicForms.forEach(form => {
        // Build unique storage key based on form path
        const formKey = 'sg_lead_draft_' + window.location.pathname.split('/').join('_');
        const inputs = form.querySelectorAll('input[name="name"], input[name="email"], input[name="phone"], textarea[name="message"]');
        
        // Restore draft if present
        try {
            const savedDraft = localStorage.getItem(formKey);
            if (savedDraft) {
                const data = JSON.parse(savedDraft);
                inputs.forEach(input => {
                    if (data[input.name] && !input.value) {
                        input.value = data[input.name];
                    }
                });
            }
        } catch (e) {
            console.warn('Could not read form draft:', e);
        }

        // Save inputs on change
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                try {
                    const currentDraft = JSON.parse(localStorage.getItem(formKey) || '{}');
                    currentDraft[input.name] = input.value;
                    localStorage.setItem(formKey, JSON.stringify(currentDraft));
                } catch (e) {}
            });
        });

        // Clear draft on successful submission
        form.addEventListener('submit', function() {
            try {
                localStorage.removeItem(formKey);
            } catch (e) {}
        });
    });
}

/**
 * Prevents double-submissions on 100% of forms across the public site and dashboard
 * using global document-level delegation that captures dynamic, modal, and static forms
 * without using button.disabled during dispatch which cancels WebKit/Safari submissions.
 */
function initializeFormSubmitLock() {
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (!form || form.tagName.toLowerCase() !== 'form') return;

        // Ignore GET search/filter forms from locking
        if (form.method && form.method.toUpperCase() === 'GET') return;

        // If form is already submitting, block duplicate submission immediately
        if (form.dataset.submitting === 'true') {
            e.preventDefault();
            return false;
        }

        form.dataset.submitting = 'true';

        const submitBtns = form.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitBtns.forEach(btn => {
            if (!btn.hasAttribute('data-original-text')) {
                btn.setAttribute('data-original-text', btn.innerHTML || btn.value);
            }
            btn.style.pointerEvents = 'none';
            btn.style.opacity = '0.7';
            btn.style.cursor = 'wait';
        });
    }, false);
}

