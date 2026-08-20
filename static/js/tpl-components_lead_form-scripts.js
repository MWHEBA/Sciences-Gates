(function() {
    // Map of common timezones to 2-letter ISO country codes
    var TZ_COUNTRY_MAP = {
        'Africa/Cairo': 'eg',
        'Asia/Riyadh': 'sa',
        'Asia/Dubai': 'ae',
        'Asia/Kuwait': 'kw',
        'Asia/Qatar': 'qa',
        'Asia/Muscat': 'om',
        'Asia/Bahrain': 'bh',
        'Asia/Amman': 'jo',
        'Asia/Baghdad': 'iq',
        'Africa/Khartoum': 'sd',
        'Africa/Tripoli': 'ly',
        'Africa/Casablanca': 'ma',
        'Africa/Algiers': 'dz',
        'Africa/Tunis': 'tn',
        'Asia/Kuala_Lumpur': 'my',
        'Asia/Beirut': 'lb',
        'Asia/Damascus': 'sy',
        'Asia/Gaza': 'ps',
        'Asia/Hebron': 'ps',
        'Asia/Aden': 'ye',
        'Europe/London': 'gb',
        'America/New_York': 'us',
        'America/Chicago': 'us',
        'America/Los_Angeles': 'us',
        'America/Toronto': 'ca',
        'Europe/Paris': 'fr',
        'Europe/Berlin': 'de',
        'Europe/Istanbul': 'tr',
        'Asia/Istanbul': 'tr',
        'Asia/Jakarta': 'id',
        'Asia/Karachi': 'pk',
        'Asia/Kolkata': 'in',
        'Asia/Dhaka': 'bd',
        'Asia/Manila': 'ph'
    };

    function selectCountryByIso(wrapper, isoCode) {
        if (!wrapper || !isoCode) return false;
        var dropdown = wrapper.querySelector('.intl-phone-dropdown');
        var btn = wrapper.querySelector('.intl-phone-selected');
        var flagImg = wrapper.querySelector('.intl-phone-flag');
        var codeSpan = btn ? btn.querySelector('span') : null;
        var parent = wrapper.parentNode;
        var hiddenCode = (parent ? parent.querySelector('input[name="country_code"]') : null) || document.querySelector('input[name="country_code"]');
        var phoneInput = wrapper.querySelector('.intl-phone-input');

        if (!dropdown || !flagImg || !codeSpan || !phoneInput) return false;

        var targetIso = isoCode.toLowerCase();
        var opt = dropdown.querySelector('li[role="option"][data-flag="' + targetIso + '"]');
        if (!opt) return false;

        var code = opt.getAttribute('data-code');
        var flag = opt.getAttribute('data-flag');
        var placeholder = opt.getAttribute('data-placeholder');

        codeSpan.textContent = code;
        flagImg.src = 'https://flagcdn.com/w20/' + flag + '.png';
        if (hiddenCode) hiddenCode.value = code;
        if (placeholder) phoneInput.placeholder = placeholder;
        return true;
    }

    function detectBrowserCountry() {
        try {
            var tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
            if (tz && TZ_COUNTRY_MAP[tz]) {
                return TZ_COUNTRY_MAP[tz];
            }
        } catch(e) {}

        var langs = (navigator.languages && navigator.languages.length) ? navigator.languages : [navigator.language || ''];
        for (var i = 0; i < langs.length; i++) {
            if (!langs[i]) continue;
            var parts = langs[i].split('-');
            if (parts.length === 2 && parts[1].length === 2) {
                var c = parts[1].toLowerCase();
                if (c !== 'ar' && c !== 'en') {
                    return c;
                }
            }
        }
        return null;
    }

    function applyCountryToWrappers(wrappers, countryIso) {
        wrappers.forEach(function(wrapper) {
            if (wrapper.dataset.userSelected === 'true') return;
            selectCountryByIso(wrapper, countryIso);
        });
    }

    function fetchIpCountry(callback) {
        var controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
        var timeoutId = controller ? setTimeout(function() { controller.abort(); }, 2500) : null;

        fetch('https://get.geojs.io/v1/ip/country.json', { signal: controller ? controller.signal : undefined })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                if (timeoutId) clearTimeout(timeoutId);
                if (data && data.country) {
                    callback(data.country.toLowerCase());
                } else {
                    callback(null);
                }
            })
            .catch(function() {
                if (timeoutId) clearTimeout(timeoutId);
                fetch('https://ipapi.co/json/')
                    .then(function(res) { return res.json(); })
                    .then(function(data) {
                        if (data && data.country_code) {
                            callback(data.country_code.toLowerCase());
                        } else {
                            callback(null);
                        }
                    })
                    .catch(function() { callback(null); });
            });
    }

    function autoDetectAndSetCountry(wrappers) {
        if (!wrappers || !wrappers.length) return;

        var cached = null;
        try {
            cached = sessionStorage.getItem('user_detected_country');
        } catch(e) {}

        if (cached) {
            applyCountryToWrappers(wrappers, cached);
            return;
        }

        var localDetected = detectBrowserCountry();
        if (localDetected) {
            applyCountryToWrappers(wrappers, localDetected);
        }

        fetchIpCountry(function(ipCountry) {
            if (ipCountry) {
                try {
                    sessionStorage.setItem('user_detected_country', ipCountry);
                } catch(e) {}
                applyCountryToWrappers(wrappers, ipCountry);
            }
        });
    }

    // Initialize all phone inputs on DOMContentLoaded
    function initIntlPhone(wrapper) {
        var btn = wrapper.querySelector('.intl-phone-selected');
        var dropdown = wrapper.querySelector('.intl-phone-dropdown');
        var flagImg = wrapper.querySelector('.intl-phone-flag');
        var codeSpan = btn ? btn.querySelector('span') : null;
        
        var parent = wrapper.parentNode;
        var hiddenCode = (parent ? parent.querySelector('input[name="country_code"]') : null) || document.querySelector('input[name="country_code"]');
        var combined = (parent ? parent.querySelector('input[name="phone"]') : null) || document.querySelector('input[name="phone"]');
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

        // Mark user interaction when typing in input
        phoneInput.addEventListener('input', function() {
            wrapper.dataset.userSelected = 'true';
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
            wrapper.dataset.userSelected = 'true';
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
                    wrapper.dataset.userSelected = 'true';
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
    
    // Global listener to combine numbers on form submit and prevent double submit
    document.addEventListener('submit', function(e) {
        var form = e.target;
        if (form && form.method && form.method.toUpperCase() === 'POST') {
            if (form.dataset.submitting === 'true') {
                e.preventDefault();
                return false;
            }
            var submitBtns = form.querySelectorAll('button[type="submit"], input[type="submit"]');
            submitBtns.forEach(function(btn) {
                btn.style.pointerEvents = 'none';
                btn.style.opacity = '0.7';
                btn.style.cursor = 'wait';
            });
        }

        var wrappers = e.target.querySelectorAll('.intl-phone-wrapper');
        wrappers.forEach(function(wrapper) {
            var parent = wrapper.parentNode;
            var hiddenCode = (parent ? parent.querySelector('input[name="country_code"]') : null) || document.querySelector('input[name="country_code"]');
            var combined = (parent ? parent.querySelector('input[name="phone"]') : null) || document.querySelector('input[name="phone"]');
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
        autoDetectAndSetCountry(wrappers);
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }
})();
