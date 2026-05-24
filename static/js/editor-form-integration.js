/**
 * Editor Form Integration — Ensure HTML Editors sync before form submission
 * 
 * This script integrates with the ProfessionalHTMLEditor class to ensure
 * that all editor content is properly synced to form fields before submission.
 */

(function() {
    'use strict';
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initEditorFormIntegration);
    } else {
        initEditorFormIntegration();
    }
    
    function initEditorFormIntegration() {
        console.log('[Editor Form Integration] Initializing...');
        
        // Find all forms
        const forms = document.querySelectorAll('form');
        
        forms.forEach((form, formIndex) => {
            console.log(`[Editor Form Integration] Processing form ${formIndex}`);
            
            // Listen for form submission
            form.addEventListener('submit', function(e) {
                console.log('[Editor Form Integration] Form submission detected');
                
                // Find all editor mounts in this form
                const editorMounts = form.querySelectorAll('.pro-editor-mount');
                console.log(`[Editor Form Integration] Found ${editorMounts.length} editor mounts`);
                
                editorMounts.forEach((mount, mountIndex) => {
                    // Get the editor area
                    const editorArea = mount.querySelector('.pro-editor-content');
                    
                    if (!editorArea) {
                        console.warn(`[Editor Form Integration] No editor area found in mount ${mountIndex}`);
                        return;
                    }
                    
                    // Get the field name
                    const fieldName = mount.getAttribute('data-field-name');
                    console.log(`[Editor Form Integration] Mount ${mountIndex}: field="${fieldName}"`);
                    
                    if (!fieldName) {
                        console.warn(`[Editor Form Integration] No field name found in mount ${mountIndex}`);
                        return;
                    }
                    
                    // Get the content
                    const content = editorArea.innerHTML;
                    console.log(`[Editor Form Integration] Content length: ${content.length}`);
                    
                    // Find the hidden textarea
                    const hiddenTextarea = mount.querySelector('textarea[style*="display: none"]');
                    
                    if (hiddenTextarea) {
                        // Update the hidden textarea
                        hiddenTextarea.value = content;
                        hiddenTextarea.name = fieldName;
                        console.log(`[Editor Form Integration] Updated hidden textarea: ${fieldName}`);
                    } else {
                        console.warn(`[Editor Form Integration] No hidden textarea found in mount ${mountIndex}`);
                    }
                    
                    // Also find any form field with the same name and update it
                    const formField = form.querySelector(`textarea[name="${fieldName}"]`);
                    if (formField && formField !== hiddenTextarea) {
                        formField.value = content;
                        console.log(`[Editor Form Integration] Updated form field: ${fieldName}`);
                    }
                });
            }, false);
        });
        
        // Also set up periodic syncing to ensure content is always saved
        setInterval(syncAllEditors, 3000);
    }
    
    function syncAllEditors() {
        const editorMounts = document.querySelectorAll('.pro-editor-mount');
        
        editorMounts.forEach(mount => {
            const editorArea = mount.querySelector('.pro-editor-content');
            const hiddenTextarea = mount.querySelector('textarea[style*="display: none"]');
            
            if (editorArea && hiddenTextarea) {
                const content = editorArea.innerHTML;
                if (hiddenTextarea.value !== content) {
                    hiddenTextarea.value = content;
                    console.log(`[Editor Form Integration] Periodic sync: ${hiddenTextarea.name}`);
                }
            }
        });
    }
})();
