(function() {
    var wrapper = document.getElementById('intlPhoneSelect');
    if (!wrapper) return;
    
    var btn = document.getElementById('intlPhoneBtn');
    var dropdown = document.getElementById('intlPhoneDropdown');
    var flagImg = document.getElementById('intlPhoneFlag');
    var codeSpan = document.getElementById('intlPhoneCode');
    var hiddenCode = document.getElementById('id_country_code');
    var form = wrapper.closest('form');
    
    btn.addEventListener('click', function() {
        var isOpen = dropdown.classList.contains('intl-phone-dropdown--open');
        dropdown.classList.toggle('intl-phone-dropdown--open');
        btn.setAttribute('aria-expanded', !isOpen);
        if (!isOpen && !dropdown.dataset.loaded) {
            dropdown.querySelectorAll('img[data-src]').forEach(function(img) {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
            });
            dropdown.dataset.loaded = '1';
        }
        if (!isOpen) {
            var search = document.getElementById('intlPhoneSearch');
            if (search) setTimeout(function() { search.focus(); }, 50);
        }
    });
    
    var searchInput = document.getElementById('intlPhoneSearch');
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
    
    dropdown.addEventListener('click', function(e) {
        var li = e.target.closest('li[role="option"]');
        if (!li) return;
        var code = li.getAttribute('data-code');
        var flag = li.getAttribute('data-flag');
        var placeholder = li.getAttribute('data-placeholder');
        codeSpan.textContent = code;
        flagImg.src = 'https://flagcdn.com/w20/' + flag + '.png';
        hiddenCode.value = code;
        var phoneInput = document.getElementById('id_phone');
        if (phoneInput && placeholder) phoneInput.placeholder = placeholder;
        dropdown.classList.remove('intl-phone-dropdown--open');
        btn.setAttribute('aria-expanded', 'false');
    });
    
    document.addEventListener('click', function(e) {
        if (!wrapper.contains(e.target)) {
            dropdown.classList.remove('intl-phone-dropdown--open');
            btn.setAttribute('aria-expanded', 'false');
        }
    });
    
    if (form) {
        form.addEventListener('submit', function() {
            var number = document.getElementById('id_phone');
            var combined = document.getElementById('id_phone_combined');
            if (number && combined && hiddenCode) {
                combined.value = hiddenCode.value + number.value.replace(/^0+/, '');
            }
        });
    }
})();
