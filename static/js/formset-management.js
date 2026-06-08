/**
 * Dynamic Formset Management
 * Handles adding and removing formset rows dynamically
 */

class FormsetManager {
    constructor(formsetPrefix, itemName = 'Item') {
        this.formsetPrefix = formsetPrefix;
        this.itemName = itemName;
        this.formsetContainer = document.querySelector(`[data-formset="${formsetPrefix}"]`);
        this.managementForm = document.querySelector(`#id_${formsetPrefix}-TOTAL_FORMS`);
        
        if (this.formsetContainer && this.managementForm) {
            this.init();
        }
    }

    init() {
        this.updateFormIndices();
        this.attachDeleteHandlers();
        this.attachAddHandler();
    }

    updateFormIndices() {
        const forms = this.formsetContainer.querySelectorAll('[data-form-index]');
        forms.forEach((form, index) => {
            form.setAttribute('data-form-index', index);
            this.updateFormFieldNames(form, index);
        });
    }

    updateFormFieldNames(form, index) {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            const name = input.getAttribute('name');
            if (name) {
                const newName = name.replace(
                    new RegExp(`${this.formsetPrefix}-\\d+-`),
                    `${this.formsetPrefix}-${index}-`
                );
                input.setAttribute('name', newName);
                
                // Update id as well
                const id = input.getAttribute('id');
                if (id) {
                    const newId = id.replace(
                        new RegExp(`id_${this.formsetPrefix}_\\d+_`),
                        `id_${this.formsetPrefix}_${index}_`
                    );
                    input.setAttribute('id', newId);
                }
            }
        });

        // Update labels
        const labels = form.querySelectorAll('label');
        labels.forEach(label => {
            const forAttr = label.getAttribute('for');
            if (forAttr) {
                const newFor = forAttr.replace(
                    new RegExp(`id_${this.formsetPrefix}_\\d+_`),
                    `id_${this.formsetPrefix}_${index}_`
                );
                label.setAttribute('for', newFor);
            }
        });
    }

    attachDeleteHandlers() {
        const deleteCheckboxes = this.formsetContainer.querySelectorAll('[name$="-DELETE"]');
        deleteCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const form = e.target.closest('[data-form-index]');
                if (e.target.checked) {
                    form.style.opacity = '0.5';
                    form.style.pointerEvents = 'none';
                } else {
                    form.style.opacity = '1';
                    form.style.pointerEvents = 'auto';
                }
            });
        });
    }

    attachAddHandler() {
        const addButton = document.querySelector(`[data-add-formset="${this.formsetPrefix}"]`);
        if (addButton) {
            addButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.addForm();
            });
        }
    }

    addForm() {
        const totalForms = parseInt(this.managementForm.value);
        const newIndex = totalForms;

        // Get the last form as template
        const lastForm = this.formsetContainer.querySelector('[data-form-index]:last-of-type');
        if (!lastForm) return;

        // Clone the last form
        const newForm = lastForm.cloneNode(true);
        newForm.setAttribute('data-form-index', newIndex);

        // Clear all input values
        const inputs = newForm.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (input.type === 'checkbox') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });

        // Update field names and ids
        this.updateFormFieldNames(newForm, newIndex);

        // Update counter in header
        const header = newForm.querySelector('h3');
        if (header) {
            header.textContent = `${this.itemName} #${newIndex + 1}`;
        }

        // Append to container
        this.formsetContainer.appendChild(newForm);

        // Update management form
        this.managementForm.value = newIndex + 1;

        // Attach handlers to new form
        this.attachDeleteHandlers();
    }

    removeForm(formElement) {
        const deleteCheckbox = formElement.querySelector('[name$="-DELETE"]');
        if (deleteCheckbox) {
            deleteCheckbox.checked = true;
            deleteCheckbox.dispatchEvent(new Event('change'));
        }
    }
}

// Initialize all formsets on page load
document.addEventListener('DOMContentLoaded', function() {
    // Find all formset containers and initialize them
    const formsetContainers = document.querySelectorAll('[data-formset]');
    window.formsetManagers = window.formsetManagers || {};
    formsetContainers.forEach(container => {
        const formsetPrefix = container.getAttribute('data-formset');
        const itemName = container.getAttribute('data-item-name') || 'Item';
        window.formsetManagers[formsetPrefix] = new FormsetManager(formsetPrefix, itemName);
    });
});
