/**
 * Lazy Loading Module
 * Lightweight helper to apply fade-in transitions for native lazy loading
 */

class LazyLoadingManager {
    constructor() {
        this.init();
    }

    init() {
        // Handle images already in the DOM and completed (or cached)
        const checkExisting = () => {
            const images = document.querySelectorAll('img[loading="lazy"]');
            images.forEach(img => {
                if (img.complete) {
                    img.classList.add('lazy-loaded');
                }
            });
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', checkExisting);
        } else {
            checkExisting();
        }

        // Capture load/error events globally to support dynamically added images (AJAX/Alpine.js)
        // Since load/error events do not bubble, we must use the capturing phase (third parameter = true)
        document.addEventListener('load', (event) => {
            const target = event.target;
            if (target.tagName === 'IMG' && target.getAttribute('loading') === 'lazy') {
                target.classList.add('lazy-loaded');
            }
        }, true);

        document.addEventListener('error', (event) => {
            const target = event.target;
            if (target.tagName === 'IMG' && target.getAttribute('loading') === 'lazy') {
                target.classList.add('lazy-error');
            }
        }, true);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    new LazyLoadingManager();
});

// Fallback functions to prevent breaking references
function reinitializeLazyLoading() {
    new LazyLoadingManager();
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = LazyLoadingManager;
}
