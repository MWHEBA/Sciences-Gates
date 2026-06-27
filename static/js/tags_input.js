/* Reusable Tags Input Component with Alpine.js */
document.addEventListener('alpine:init', () => {
    Alpine.data('tagsInputComponent', (config) => ({
        fieldId: config.fieldId,
        fieldName: config.fieldName,
        searchUrl: config.searchUrl,
        createUrl: config.createUrl,
        
        searchQuery: '',
        selectedTags: [],
        suggestions: [],
        activeIndex: -1,
        showDropdown: false,
        exactMatchExists: false,
        debounceTimer: null,

        init() {
            // Find existing checkboxes from Django rendering
            const djangoContainer = this.$refs.djangoContainer;
            if (!djangoContainer) return;

            const checkboxes = djangoContainer.querySelectorAll('input[type="checkbox"]');
            
            // Populate initially selected tags and initial list
            checkboxes.forEach((cb) => {
                const labelText = cb.closest('label')?.textContent.trim() || '';
                const tagInfo = {
                    id: cb.value,
                    name: labelText || cb.value
                };

                if (cb.checked) {
                    this.selectedTags.push(tagInfo);
                }
            });
        },

        syncFromCheckboxes() {
            const djangoContainer = this.$refs.djangoContainer;
            if (!djangoContainer) return;

            const checkboxes = djangoContainer.querySelectorAll('input[type="checkbox"]');
            const newSelected = [];
            checkboxes.forEach((cb) => {
                if (cb.checked) {
                    const labelText = cb.closest('label')?.textContent.trim() || '';
                    newSelected.push({
                        id: cb.value,
                        name: labelText || cb.value
                    });
                }
            });
            this.selectedTags = newSelected;
        },

        onInput() {
            clearTimeout(this.debounceTimer);
            this.activeIndex = -1;

            const query = this.searchQuery.trim();
            if (!query) {
                this.suggestions = [];
                this.showDropdown = false;
                this.exactMatchExists = false;
                return;
            }

            // Debounce the API search call
            this.debounceTimer = setTimeout(() => {
                this.searchTags(query);
            }, 250);
        },

        async searchTags(query) {
            try {
                const response = await fetch(`${this.searchUrl}?q=${encodeURIComponent(query)}`);
                if (!response.ok) throw new Error('Search failed');
                
                const data = await response.json();
                this.suggestions = data.results || [];
                
                // Check if exact match already exists in database results
                this.exactMatchExists = this.suggestions.some(
                    s => s.name.toLowerCase() === query.toLowerCase()
                );
                
                this.showDropdown = true;
            } catch (error) {
                console.error('Error searching tags:', error);
            }
        },

        isSelected(tag) {
            return this.selectedTags.some(t => String(t.id) === String(tag.id));
        },

        selectTag(tag) {
            if (this.isSelected(tag)) {
                this.closeDropdown();
                return;
            }

            this.selectedTags.push(tag);
            this.syncCheckbox(tag.id, tag.name, true);
            this.searchQuery = '';
            this.suggestions = [];
            this.showDropdown = false;
            this.exactMatchExists = false;
            this.$refs.searchInput.focus();
        },

        removeTag(tag) {
            this.selectedTags = this.selectedTags.filter(t => String(t.id) !== String(tag.id));
            this.syncCheckbox(tag.id, tag.name, false);
            this.$refs.searchInput.focus();
        },

        syncCheckbox(tagId, tagName, isChecked) {
            const djangoContainer = this.$refs.djangoContainer;
            if (!djangoContainer) return;

            // Find existing checkbox
            let checkbox = djangoContainer.querySelector(`input[type="checkbox"][value="${tagId}"]`);

            if (!checkbox && isChecked) {
                // If it doesn't exist and we want to select it, create it dynamically
                const wrapper = document.createElement('div');
                wrapper.className = 'hidden';
                
                const label = document.createElement('label');
                checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.name = this.fieldName;
                checkbox.value = tagId;
                checkbox.checked = true;
                checkbox.id = `id_${this.fieldName}_dynamically_added_${tagId}`;
                
                label.appendChild(checkbox);
                label.appendChild(document.createTextNode(` ${tagName}`));
                wrapper.appendChild(label);
                
                djangoContainer.appendChild(wrapper);
            } else if (checkbox) {
                // Update checked status
                checkbox.checked = isChecked;
            }
        },

        async createNewTag() {
            const name = this.searchQuery.trim();
            if (!name) return;

            // Get CSRF Token
            let csrfToken = '';
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfInput) {
                csrfToken = csrfInput.value;
            }

            try {
                const response = await fetch(this.createUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ name: name })
                });

                if (!response.ok) throw new Error('Tag creation failed');
                
                const data = await response.json();
                if (data.success) {
                    const newTag = { id: data.id, name: data.name };
                    this.selectTag(newTag);
                } else {
                    alert(data.error || 'حدث خطأ أثناء إنشاء الوسم.');
                }
            } catch (error) {
                console.error('Error creating tag:', error);
                alert('عذراً، فشل إنشاء الوسم الجديد.');
            }
        },

        // Keyboard Navigation
        nextSuggestion() {
            if (!this.showDropdown || !this.suggestions.length) return;
            this.activeIndex = (this.activeIndex + 1) % this.suggestions.length;
        },

        prevSuggestion() {
            if (!this.showDropdown || !this.suggestions.length) return;
            this.activeIndex = (this.activeIndex - 1 + this.suggestions.length) % this.suggestions.length;
        },

        selectActiveOrCreate() {
            if (this.showDropdown && this.activeIndex >= 0 && this.activeIndex < this.suggestions.length) {
                this.selectTag(this.suggestions[this.activeIndex]);
            } else if (this.searchQuery.trim().length > 0 && !this.exactMatchExists) {
                this.createNewTag();
            }
        },

        handleBackspace(e) {
            if (this.searchQuery === '' && this.selectedTags.length > 0) {
                const lastTag = this.selectedTags[this.selectedTags.length - 1];
                this.removeTag(lastTag);
            }
        },

        closeDropdown() {
            this.showDropdown = false;
            this.activeIndex = -1;
        }
    }));
});
