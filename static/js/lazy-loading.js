/**
 * Lazy Loading Module
 * Implements intersection observer for below-fold images
 * Provides fallback for browsers without native lazy loading support
 */

class LazyLoadingManager {
    constructor() {
        this.imageSelector = 'img[loading="lazy"]';
        this.placeholderClass = 'lazy-placeholder';
        this.loadedClass = 'lazy-loaded';
        this.errorClass = 'lazy-error';
        this.init();
    }

    /**
     * Initialize lazy loading
     */
    init() {
        // Check if browser supports native lazy loading
        if ('loading' in HTMLImageElement.prototype) {
            // Native lazy loading is supported, no need for intersection observer
            this.setupNativeLazyLoading();
        } else {
            // Use intersection observer as fallback
            this.setupIntersectionObserver();
        }
    }

    /**
     * Setup native lazy loading with error handling
     */
    setupNativeLazyLoading() {
        const images = document.querySelectorAll(this.imageSelector);
        images.forEach(img => {
            this.setupImageErrorHandling(img);
            this.addPlaceholder(img);
        });
    }

    /**
     * Setup intersection observer for lazy loading
     */
    setupIntersectionObserver() {
        const options = {
            root: null,
            rootMargin: '50px', // Start loading 50px before image enters viewport
            threshold: 0.01
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadImage(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, options);

        const images = document.querySelectorAll(this.imageSelector);
        images.forEach(img => {
            this.addPlaceholder(img);
            observer.observe(img);
        });
    }

    /**
     * Load image and handle errors
     */
    loadImage(img) {
        const src = img.getAttribute('data-src') || img.getAttribute('src');
        const srcset = img.getAttribute('data-srcset');

        if (!src) return;

        // Create a new image to preload
        const tempImg = new Image();

        tempImg.onload = () => {
            img.src = src;
            if (srcset) {
                img.srcset = srcset;
            }
            img.classList.add(this.loadedClass);
            img.classList.remove(this.placeholderClass);
            this.removePlaceholder(img);
        };

        tempImg.onerror = () => {
            img.classList.add(this.errorClass);
            this.removePlaceholder(img);
        };

        tempImg.src = src;
    }

    /**
     * Add placeholder to image
     */
    addPlaceholder(img) {
        // Only add placeholder if image doesn't have one already
        if (img.parentElement && img.parentElement.classList.contains(this.placeholderClass)) {
            return;
        }

        // Create placeholder element
        const placeholder = document.createElement('div');
        placeholder.className = `${this.placeholderClass} bg-gray-200 animate-pulse`;
        placeholder.style.width = img.width || '100%';
        placeholder.style.height = img.height || 'auto';
        placeholder.style.aspectRatio = img.getAttribute('data-aspect-ratio') || 'auto';

        // Insert placeholder before image
        img.parentElement?.insertBefore(placeholder, img);
        img.classList.add(this.placeholderClass);
    }

    /**
     * Remove placeholder from image
     */
    removePlaceholder(img) {
        const placeholder = img.parentElement?.querySelector(`.${this.placeholderClass}`);
        if (placeholder && placeholder !== img) {
            placeholder.remove();
        }
    }

    /**
     * Setup error handling for images
     */
    setupImageErrorHandling(img) {
        img.addEventListener('error', () => {
            img.classList.add(this.errorClass);
            this.removePlaceholder(img);
            // Optionally show a fallback image or message
            console.warn('Failed to load image:', img.src);
        });

        img.addEventListener('load', () => {
            img.classList.add(this.loadedClass);
            this.removePlaceholder(img);
        });
    }
}

/**
 * Initialize lazy loading when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    new LazyLoadingManager();
});

/**
 * Re-initialize lazy loading for dynamically added images
 * Useful for AJAX-loaded content
 */
function reinitializeLazyLoading() {
    new LazyLoadingManager();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LazyLoadingManager;
}
