/**
 * Main JavaScript file
 * Global initialization and utilities
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Science Gates - Study in Malaysia');
    
    // Initialize formset management for dynamic forms
    initializeFormsets();
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
