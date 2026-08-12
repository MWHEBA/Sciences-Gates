/**
 * Cloudflare Turnstile Unified Explicit Render & Lifecycle Handler
 * مدير ومراقب ويدجت Turnstile لكافة النماذج بالموقع
 */

(function () {
    'use strict';

    window.turnstileWidgets = window.turnstileWidgets || {};

    /**
     * Callback function executed when Cloudflare Turnstile API script is loaded.
     */
    window.onloadTurnstileCallback = function () {
        // Auto-render all visible containers on page load
        renderAllVisibleTurnstiles();
    };

    /**
     * Render Turnstile widget explicitly for a specific container element or selector.
     * @param {HTMLElement|string} target Container element or CSS selector
     * @returns {string|null} Widget ID or null
     */
    window.renderTurnstileWidget = function (target) {
        if (typeof window.turnstile === 'undefined') {
            markTurnstileBlocked();
            return null;
        }

        var container = typeof target === 'string' ? document.querySelector(target) : target;
        if (!container) return null;

        var sitekey = container.getAttribute('data-sitekey') || window.TURNSTILE_SITE_KEY;
        if (!sitekey) return null;

        var containerId = container.id || ('turnstile-' + Math.random().toString(36).substring(2, 9));
        container.id = containerId;

        // Avoid re-rendering if already initialized and element has child iframe
        if (window.turnstileWidgets[containerId] !== undefined && container.children.length > 0) {
            return window.turnstileWidgets[containerId];
        }

        try {
            var widgetId = window.turnstile.render('#' + containerId, {
                sitekey: sitekey,
                theme: container.getAttribute('data-theme') || 'light',
                callback: function (token) {
                    var form = container.closest('form');
                    if (form) {
                        var errP = form.querySelector('.turnstile-error-msg');
                        if (errP) errP.style.display = 'none';
                        var submitBtn = form.querySelector('button[type="submit"]');
                        if (submitBtn) submitBtn.disabled = false;
                    }
                },
                'error-callback': function () {
                    console.warn('Turnstile widget error on container:', containerId);
                },
                'expired-callback': function () {
                    if (window.turnstileWidgets[containerId] !== undefined) {
                        window.turnstile.reset(window.turnstileWidgets[containerId]);
                    }
                }
            });
            window.turnstileWidgets[containerId] = widgetId;
            return widgetId;
        } catch (e) {
            console.error('Error rendering Turnstile widget:', e);
            return null;
        }
    };

    /**
     * Render all visible turnstile containers in document.
     */
    function renderAllVisibleTurnstiles() {
        var containers = document.querySelectorAll('.cf-turnstile-explicit, [data-turnstile-container]');
        containers.forEach(function (container) {
            // Only render if container is currently visible (not inside display:none parent)
            if (container.offsetWidth > 0 || container.offsetHeight > 0 || container.getClientRects().length > 0) {
                window.renderTurnstileWidget(container);
            }
        });
    }

    /**
     * Helper to render modal Turnstile explicitly when modal step 2 becomes active.
     */
    window.renderTurnstileModal = function () {
        setTimeout(function () {
            var modalContainers = document.querySelectorAll('.reg-modal-content .cf-turnstile-explicit, #regWizardForm .cf-turnstile-explicit');
            modalContainers.forEach(function (container) {
                window.renderTurnstileWidget(container);
            });
        }, 100);
    };

    /**
     * Reset Turnstile widget inside a form or by container ID.
     * @param {HTMLElement|string} target 
     */
    window.resetTurnstile = function (target) {
        if (typeof window.turnstile === 'undefined') return;
        var container = typeof target === 'string' ? document.querySelector(target) : target;
        if (!container && target && target.querySelector) {
            container = target.querySelector('.cf-turnstile-explicit, [data-turnstile-container]');
        }
        if (container && container.id && window.turnstileWidgets[container.id] !== undefined) {
            try {
                window.turnstile.reset(window.turnstileWidgets[container.id]);
            } catch (e) {
                console.warn('Could not reset turnstile widget:', e);
            }
        }
    };

    /**
     * Mark all forms with turnstile_blocked input if script fails to load (AdBlocker detection).
     */
    function markTurnstileBlocked() {
        document.querySelectorAll('form').forEach(function (form) {
            if (!form.querySelector('input[name="turnstile_blocked"]')) {
                var input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'turnstile_blocked';
                input.value = '1';
                form.appendChild(input);
            }
        });
    }

    // Detect if script failed to load after 4 seconds
    window.addEventListener('DOMContentLoaded', function () {
        setTimeout(function () {
            if (typeof window.turnstile === 'undefined') {
                markTurnstileBlocked();
            } else {
                renderAllVisibleTurnstiles();
            }
        }, 1500);
    });

})();
