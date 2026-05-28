(function () {

        // Validation for step 1
        window.validateStep1 = function () {
            var name = document.getElementById('reg_name').value.trim();
            var phone = document.getElementById('reg_phone').value.trim();
            var nationality = document.getElementById('reg_nationality').value;

            if (!name) {
                alert('يرجى إدخال اسم الطالب الكامل.');
                return false;
            }
            if (!phone) {
                alert('يرجى إدخال رقم الهاتف.');
                return false;
            }
            if (!nationality) {
                alert('يرجى اختيار الجنسية.');
                return false;
            }
            return true;
        };

        // Custom phone country selector for modal
        var wrapper = document.getElementById('regPhoneSelect');
        var btn = document.getElementById('regPhoneBtn');
        var dropdown = document.getElementById('regPhoneDropdown');
        var flagImg = document.getElementById('regPhoneFlag');
        var codeSpan = document.getElementById('regPhoneCode');
        var hiddenCode = document.getElementById('reg_country_code');
        var form = document.getElementById('regWizardForm');

        if (wrapper && btn && dropdown && flagImg && codeSpan && hiddenCode) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                var isOpen = dropdown.classList.contains('intl-phone-dropdown--open');
                dropdown.classList.toggle('intl-phone-dropdown--open');
                btn.setAttribute('aria-expanded', !isOpen);
                if (!isOpen && !dropdown.dataset.loaded) {
                    dropdown.querySelectorAll('img[data-src]').forEach(function (img) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    });
                    dropdown.dataset.loaded = '1';
                }
                if (!isOpen) {
                    var search = document.getElementById('regPhoneSearch');
                    if (search) setTimeout(function () { search.focus(); }, 50);
                }
            });
        }

        var searchInput = document.getElementById('regPhoneSearch');
        if (searchInput) {
            searchInput.addEventListener('input', function () {
                var query = this.value.trim().toLowerCase();
                var items = dropdown.querySelectorAll('li[role="option"]');
                items.forEach(function (li) {
                    var name = li.querySelector('.intl-phone-name');
                    var dial = li.querySelector('.intl-phone-dial');
                    var text = (name ? name.textContent : '') + ' ' + (dial ? dial.textContent : '');
                    li.style.display = text.toLowerCase().indexOf(query) > -1 ? '' : 'none';
                });
            });
            searchInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') e.preventDefault();
            });
        }

        if (dropdown) dropdown.addEventListener('click', function (e) {
            var li = e.target.closest('li[role="option"]');
            if (!li) return;
            var code = li.getAttribute('data-code');
            var flag = li.getAttribute('data-flag');
            var placeholder = li.getAttribute('data-placeholder');
            codeSpan.textContent = code;
            flagImg.src = 'https://flagcdn.com/w20/' + flag + '.png';
            if (hiddenCode) hiddenCode.value = code;
            var phoneInput = document.getElementById('reg_phone');
            if (phoneInput && placeholder) phoneInput.placeholder = placeholder;
            dropdown.classList.remove('intl-phone-dropdown--open');
            if (btn) btn.setAttribute('aria-expanded', 'false');
        });

        document.addEventListener('click', function (e) {
            if (wrapper && !wrapper.contains(e.target)) {
                dropdown.classList.remove('intl-phone-dropdown--open');
                if (btn) btn.setAttribute('aria-expanded', 'false');
            }
        });

        // Combine inputs on form submit
        if (form) {
            form.addEventListener('submit', function (e) {
                // Combined phone
                var number = document.getElementById('reg_phone');
                var combined = document.getElementById('reg_phone_combined');
                if (number && combined && hiddenCode) {
                    combined.value = hiddenCode.value + number.value.replace(/^0+/, '');
                }

                // Combine other details into message
                var nationality = document.getElementById('reg_nationality').value;
                var level = document.getElementById('reg_level').value;
                var residence = document.getElementById('reg_residence').value;
                var address = document.getElementById('reg_address').value;
                var notes = document.getElementById('reg_notes').value;

                var combinedMsg = "طلب تسجيل جديد في جامعة: {{ university.name }}\n" +
                    "--------------------------------------------------\n" +
                    "الجنسية: " + nationality + "\n" +
                    "المرحلة الدراسية: " + level + "\n" +
                    "دولة الإقامة: " + residence + "\n" +
                    "عنوان الإقامة: " + address + "\n" +
                    "ملاحظات إضافية:\n" + (notes ? notes : "لا يوجد");

                document.getElementById('reg_combined_message').value = combinedMsg;
            });
        }

        // Floating buttons auto-hide on scroll inactivity
        window.addEventListener('load', function () {
            var floats = document.querySelectorAll('.reg-float-btn, .whatsapp-widget, .admin-dashboard-float, .admin-edit-float');
            if (floats.length === 0) return;

            var scrollTimeout = null;
            var isHovered = false;

            floats.forEach(function (el) {
                el.addEventListener('mouseenter', function () {
                    isHovered = true;
                    showFloats();
                });
                el.addEventListener('mouseleave', function () {
                    isHovered = false;
                    resetScrollTimeout();
                });
            });

            function showFloats() {
                floats.forEach(function (el) {
                    el.classList.remove('floating-hide');
                });
                if (scrollTimeout) clearTimeout(scrollTimeout);
            }

            function hideFloats() {
                if (isHovered) return;

                // Do not hide if modal is open
                var alpineData = document.querySelector('.detail-page-container')?.__x?.$data;
                var regModalOpen = alpineData ? alpineData.openRegModal : false;

                // Check if WhatsApp popup is open
                var waWidget = document.querySelector('.whatsapp-widget');
                var waOpen = waWidget && waWidget.__x && waWidget.__x.$data ? waWidget.__x.$data.open : false;

                if (regModalOpen || waOpen) return;

                floats.forEach(function (el) {
                    el.classList.add('floating-hide');
                });
            }

            function resetScrollTimeout() {
                if (scrollTimeout) clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(hideFloats, 2500); // hide after 2.5 seconds of scroll pause
            }

            window.addEventListener('scroll', function () {
                showFloats();
                resetScrollTimeout();
            }, { passive: true });

            // Initialize timeout on load
            resetScrollTimeout();
        });
    })();
