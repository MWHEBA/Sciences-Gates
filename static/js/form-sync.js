/**
 * Form Sync Helper — Synchronize HTML Editors before form submission
 * 
 * This script ensures that all CustomHTMLEditorWidget instances
 * sync their content to hidden textareas before form submission.
 * 
 * Problem: When a form with HTML editors is submitted, the editors
 * may not have synced their content to the hidden textareas yet,
 * causing validation errors like "This field is required".
 * 
 * Solution: Listen for form submission and force sync all editors.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all forms on the page
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Find all editor mounts on this form
            const editors = form.querySelectorAll('.pro-editor-mount');
            
            console.log(`[Form Sync] Found ${editors.length} editors on form`);
            
            editors.forEach((editorMount, index) => {
                // Find the hidden textarea that carries the value
                const hiddenTextarea = editorMount.querySelector('textarea[style*="display: none"]');
                
                if (hiddenTextarea) {
                    // Find the editor area (contentEditable div)
                    const editorArea = editorMount.querySelector('.pro-editor-content');
                    
                    if (editorArea) {
                        // Sync the editor content to the hidden textarea
                        const content = editorArea.innerHTML;
                        hiddenTextarea.value = content;
                        
                        const fieldName = hiddenTextarea.getAttribute('data-name') || 
                                        editorMount.getAttribute('data-field-name');
                        
                        console.log(`[Form Sync] Editor ${index}: field="${fieldName}", content_length=${content.length}`);
                        
                        // Verify the textarea has a name attribute
                        if (!hiddenTextarea.name) {
                            hiddenTextarea.name = fieldName;
                            console.log(`[Form Sync] Set name attribute to: ${fieldName}`);
                        }
                    } else {
                        console.warn(`[Form Sync] No editor area found for editor ${index}`);
                    }
                } else {
                    console.warn(`[Form Sync] No hidden textarea found for editor ${index}`);
                }
            });
        });
    });
    
    // Also sync on blur to ensure content is saved
    document.addEventListener('blur', function(e) {
        if (e.target && e.target.classList && e.target.classList.contains('pro-editor-content')) {
            const editorMount = e.target.closest('.pro-editor-mount');
            if (editorMount) {
                const hiddenTextarea = editorMount.querySelector('textarea[style*="display: none"]');
                if (hiddenTextarea) {
                    hiddenTextarea.value = e.target.innerHTML;
                    console.log(`[Form Sync] Synced on blur: ${hiddenTextarea.name}`);
                }
            }
        }
    }, true);
    
    // Also sync periodically to ensure content is always saved
    setInterval(function() {
        const editors = document.querySelectorAll('.pro-editor-mount');
        editors.forEach(editorMount => {
            const hiddenTextarea = editorMount.querySelector('textarea[style*="display: none"]');
            const editorArea = editorMount.querySelector('.pro-editor-content');
            
            if (hiddenTextarea && editorArea) {
                hiddenTextarea.value = editorArea.innerHTML;
            }
        });
    }, 5000); // Sync every 5 seconds
});
