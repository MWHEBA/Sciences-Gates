/* Reusable Relations Search-Select Component with Alpine.js */
document.addEventListener('alpine:init', () => {
    Alpine.data('relationsSelectComponent', (config) => ({
        fieldId: config.fieldId,
        fieldName: config.fieldName,
        placeholder: config.placeholder || 'ابحث واختر...',
        
        searchQuery: '',
        selectedItems: [], // Array of { id, name }
        allItems: [],      // Array of { id, name }
        activeIndex: -1,
        showDropdown: false,

        init() {
            // Find existing checkboxes from Django rendering
            const djangoContainer = this.$refs.djangoContainer;
            if (!djangoContainer) return;

            const checkboxes = djangoContainer.querySelectorAll('input[type="checkbox"]');
            
            // Populate initially selected items and all available choices
            checkboxes.forEach((cb) => {
                const labelText = cb.closest('label')?.textContent.trim() || '';
                const itemInfo = {
                    id: cb.value,
                    name: labelText || cb.value
                };

                this.allItems.push(itemInfo);

                if (cb.checked) {
                    this.selectedItems.push(itemInfo);
                }
            });
        },

        get filteredSuggestions() {
            const query = this.searchQuery.trim().toLowerCase();
            return this.allItems.filter(item => {
                // Not already selected
                const isSelected = this.selectedItems.some(selected => String(selected.id) === String(item.id));
                if (isSelected) return false;

                // Matches query
                if (!query) return true; // Show all if query is empty
                return item.name.toLowerCase().includes(query);
            });
        },

        isSelected(item) {
            return this.selectedItems.some(selected => String(selected.id) === String(item.id));
        },

        selectItem(item) {
            if (this.isSelected(item)) {
                this.closeDropdown();
                return;
            }

            this.selectedItems.push(item);
            this.syncCheckbox(item.id, true);
            this.searchQuery = '';
            this.showDropdown = false;
            this.activeIndex = -1;
            this.$refs.searchInput.focus();
        },

        removeItem(item) {
            this.selectedItems = this.selectedItems.filter(selected => String(selected.id) !== String(item.id));
            this.syncCheckbox(item.id, false);
            this.$refs.searchInput.focus();
        },

        syncCheckbox(itemId, isChecked) {
            const djangoContainer = this.$refs.djangoContainer;
            if (!djangoContainer) return;

            const checkbox = djangoContainer.querySelector(`input[type="checkbox"][value="${itemId}"]`);
            if (checkbox) {
                checkbox.checked = isChecked;
                // Dispatch change event so Django or other listeners are aware
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            }
        },

        highlightMatch(name) {
            if (!this.searchQuery.trim()) return name;
            const query = this.searchQuery.trim();
            const escapedQuery = query.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
            const regex = new RegExp(`(${escapedQuery})`, 'gi');
            return name.replace(regex, '<mark class="highlight-match">$1</mark>');
        },

        // Keyboard Navigation
        nextSuggestion() {
            const list = this.filteredSuggestions;
            if (!this.showDropdown || !list.length) return;
            this.activeIndex = (this.activeIndex + 1) % list.length;
        },

        prevSuggestion() {
            const list = this.filteredSuggestions;
            if (!this.showDropdown || !list.length) return;
            this.activeIndex = (this.activeIndex - 1 + list.length) % list.length;
        },

        selectActive() {
            const list = this.filteredSuggestions;
            if (this.showDropdown && this.activeIndex >= 0 && this.activeIndex < list.length) {
                this.selectItem(list[this.activeIndex]);
            }
        },

        handleBackspace() {
            if (this.searchQuery === '' && this.selectedItems.length > 0) {
                const lastItem = this.selectedItems[this.selectedItems.length - 1];
                this.removeItem(lastItem);
            }
        },

        closeDropdown() {
            this.showDropdown = false;
            this.activeIndex = -1;
        }
    }));
});
