(function() {
    // Initialize all phone inputs on DOMContentLoaded
    function initIntlPhone(wrapper) {
        var btn = wrapper.querySelector('.intl-phone-selected');
        var dropdown = wrapper.querySelector('.intl-phone-dropdown');
        var flagImg = wrapper.querySelector('.intl-phone-flag');
        var codeSpan = btn ? btn.querySelector('span') : null;
        
        var parent = wrapper.parentNode;
        var hiddenCode = parent.querySelector('input[name="country_code"]');
        var combined = parent.querySelector('input[name="phone"]');
        var phoneInput = wrapper.querySelector('.intl-phone-input');
        
        if (!btn || !dropdown || !flagImg || !codeSpan || !phoneInput) return;
        
        // Toggle dropdown
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Close other dropdowns first
            document.querySelectorAll('.intl-phone-dropdown--open').forEach(function(openDropdown) {
                if (openDropdown !== dropdown) {
                    openDropdown.classList.remove('intl-phone-dropdown--open');
                    var openBtn = openDropdown.parentNode.querySelector('.intl-phone-selected');
                    if (openBtn) openBtn.setAttribute('aria-expanded', 'false');
                }
            });
            
            var isOpen = dropdown.classList.contains('intl-phone-dropdown--open');
            dropdown.classList.toggle('intl-phone-dropdown--open');
            btn.setAttribute('aria-expanded', !isOpen);
            
            // Lazy load flags on first open
            if (!isOpen && !dropdown.dataset.loaded) {
                dropdown.querySelectorAll('img[data-src]').forEach(function(img) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                });
                dropdown.dataset.loaded = '1';
            }
            
            // Focus search input on open
            if (!isOpen) {
                var search = dropdown.querySelector('.intl-phone-search');
                if (search) setTimeout(function() { search.focus(); }, 50);
            }
        });
        
        // Search filter
        var searchInput = dropdown.querySelector('.intl-phone-search');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                var query = this.value.trim().toLowerCase();
                var items = dropdown.querySelectorAll('li[role="option"]');
                items.forEach(function(li) {
                    var name = li.querySelector('.intl-phone-name');
                    var dial = li.querySelector('.intl-phone-dial');
                    var text = (name ? name.textContent : '') + ' ' + (dial ? dial.textContent : '');
                    li.style.display = text.toLowerCase().indexOf(query) > -1 ? '' : 'none';
                });
            });
            searchInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') e.preventDefault();
            });
        }
        
        // Select option
        dropdown.addEventListener('click', function(e) {
            var li = e.target.closest('li[role="option"]');
            if (!li) return;
            var code = li.getAttribute('data-code');
            var flag = li.getAttribute('data-flag');
            var placeholder = li.getAttribute('data-placeholder');
            
            codeSpan.textContent = code;
            flagImg.src = 'https://flagcdn.com/w20/' + flag + '.png';
            if (hiddenCode) hiddenCode.value = code;
            if (placeholder) phoneInput.placeholder = placeholder;
            
            dropdown.classList.remove('intl-phone-dropdown--open');
            btn.setAttribute('aria-expanded', 'false');
        });
        
        // Restore combined phone number on page load (if edit/validation failure occurs)
        if (combined && combined.value) {
            var combinedVal = combined.value.trim();
            if (combinedVal) {
                var options = Array.from(dropdown.querySelectorAll('li[role="option"]'));
                // Sort by dial code length descending
                options.sort(function(a, b) {
                    return b.getAttribute('data-code').length - a.getAttribute('data-code').length;
                });
                
                var matchedOpt = null;
                for (var i = 0; i < options.length; i++) {
                    var code = options[i].getAttribute('data-code');
                    if (combinedVal.indexOf(code) === 0) {
                        matchedOpt = options[i];
                        break;
                    }
                }
                
                if (matchedOpt) {
                    var code = matchedOpt.getAttribute('data-code');
                    var flag = matchedOpt.getAttribute('data-flag');
                    var placeholder = matchedOpt.getAttribute('data-placeholder');
                    
                    codeSpan.textContent = code;
                    flagImg.src = 'https://flagcdn.com/w20/' + flag + '.png';
                    if (hiddenCode) hiddenCode.value = code;
                    if (placeholder) phoneInput.placeholder = placeholder;
                    
                    // Set the visible input to the rest of the phone number
                    phoneInput.value = combinedVal.substring(code.length);
                }
            }
        }
    }
    
    // Global listener to close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.intl-phone-select')) {
            document.querySelectorAll('.intl-phone-dropdown--open').forEach(function(dropdown) {
                dropdown.classList.remove('intl-phone-dropdown--open');
                var btn = dropdown.parentNode.querySelector('.intl-phone-selected');
                if (btn) btn.setAttribute('aria-expanded', 'false');
            });
        }
    });
    
    // Global listener to combine numbers on form submit
    document.addEventListener('submit', function(e) {
        var wrappers = e.target.querySelectorAll('.intl-phone-wrapper');
        wrappers.forEach(function(wrapper) {
            var parent = wrapper.parentNode;
            var hiddenCode = parent.querySelector('input[name="country_code"]');
            var combined = parent.querySelector('input[name="phone"]');
            var phoneInput = wrapper.querySelector('.intl-phone-input');
            
            if (phoneInput && combined && hiddenCode) {
                combined.value = hiddenCode.value + phoneInput.value.replace(/^0+/, '');
            }
        });
    });
    
    // Initialize on DOM ready
    function initAll() {
        var wrappers = document.querySelectorAll('.intl-phone-wrapper');
        wrappers.forEach(initIntlPhone);
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }
})();
