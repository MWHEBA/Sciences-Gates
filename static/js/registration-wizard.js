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

    var form = document.getElementById('regWizardForm');

    // Combine inputs on form submit (other than phone which is handled by intl-phone.js)
    if (form) {
        form.addEventListener('submit', function (e) {
            // Combine other details into message
            var nationality = document.getElementById('reg_nationality').value;
            var level = document.getElementById('reg_level').value;
            var residence = document.getElementById('reg_residence').value;
            var address = document.getElementById('reg_address').value;
            var notes = document.getElementById('reg_notes').value;

            // Read entity details from hidden inputs
            var entityName = document.getElementById('reg_entity_name') ? document.getElementById('reg_entity_name').value : '';
            var entityType = document.getElementById('reg_entity_type') ? document.getElementById('reg_entity_type').value : 'منشأة';

            var combinedMsg = "طلب تسجيل جديد في " + entityType + ": " + entityName + "\n" +
                "--------------------------------------------------\n" +
                "الجنسية: " + nationality + "\n" +
                "المرحلة الدراسية: " + level + "\n" +
                "دولة الإقامة: " + residence + "\n" +
                "عنوان الإقامة: " + address + "\n" +
                "ملاحظات إضافية:\n" + (notes ? notes : "لا يوجد");

            document.getElementById('reg_combined_message').value = combinedMsg;
        });
    }
})();
