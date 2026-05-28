/**
 * Main JavaScript file
 * Global initialization and utilities
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Science Gates - Study in Malaysia');
    
    // Initialize formset management for dynamic forms
    initializeFormsets();
    
    // Replicated Educate Template Header & Mobile Sidebar JS
    initializeHeaderActions();
    
    // Initialize YouTube Video Popups
    initializeVideoPopups();
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
            arrowBtn.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
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
            
            const embedUrl = getYouTubeEmbedUrl(videoUrl);
            
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
            closeBtn.innerHTML = '<i class="fa-solid fa-xmark"></i>';
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
            
            // Create iframe
            const iframe = document.createElement('iframe');
            iframe.src = embedUrl;
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
            iframe.allowFullscreen = true;
            
            modalContent.appendChild(closeBtn);
            modalContent.appendChild(iframe);
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

