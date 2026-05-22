/**
 * Image Upload — Drag & Drop Component
 * مكون رفع الصور بالسحب والإفلات
 * 
 * يعمل تلقائياً على أي عنصر بكلاس .image-upload-zone
 */
(function() {
    'use strict';

    function initImageUpload() {
        var zones = document.querySelectorAll('.image-upload-zone');

        zones.forEach(function(zone) {
            var inputId = zone.getAttribute('data-input-id');
            var input = zone.querySelector('input[type="file"]');
            var preview = zone.querySelector('.image-upload-preview');
            var previewImg = preview ? preview.querySelector('img') : null;
            var placeholder = zone.querySelector('.image-upload-placeholder');
            var filenameEl = zone.querySelector('.image-upload-filename');
            var filenameText = filenameEl ? filenameEl.querySelector('p') : null;

            if (!input) return;

            // فتح مربع اختيار الملف عند الضغط
            zone.addEventListener('click', function(e) {
                if (e.target === input) return;
                input.click();
            });

            // تغيير الملف
            input.addEventListener('change', function() {
                if (input.files && input.files[0]) {
                    handleFile(input.files[0]);
                }
            });

            // Drag & Drop Events
            zone.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.stopPropagation();
                zone.style.borderColor = 'var(--primary)';
                zone.style.backgroundColor = 'var(--primary-muted)';
            });

            zone.addEventListener('dragleave', function(e) {
                e.preventDefault();
                e.stopPropagation();
                zone.style.borderColor = 'var(--border)';
                zone.style.backgroundColor = '';
            });

            zone.addEventListener('drop', function(e) {
                e.preventDefault();
                e.stopPropagation();
                zone.style.borderColor = 'var(--border)';
                zone.style.backgroundColor = '';

                var files = e.dataTransfer.files;
                if (files && files[0]) {
                    // التحقق من نوع الملف
                    if (!files[0].type.startsWith('image/')) {
                        zone.style.borderColor = 'var(--danger)';
                        setTimeout(function() {
                            zone.style.borderColor = 'var(--border)';
                        }, 1500);
                        return;
                    }

                    // نقل الملف للـ input
                    var dataTransfer = new DataTransfer();
                    dataTransfer.items.add(files[0]);
                    input.files = dataTransfer.files;

                    handleFile(files[0]);
                }
            });

            function handleFile(file) {
                // عرض اسم الملف
                if (filenameText) {
                    filenameText.textContent = file.name;
                    filenameEl.style.display = 'block';
                }

                // عرض المعاينة
                if (file.type.startsWith('image/') && previewImg) {
                    var reader = new FileReader();
                    reader.onload = function(e) {
                        previewImg.src = e.target.result;
                        preview.style.display = 'block';
                        placeholder.style.display = 'none';
                    };
                    reader.readAsDataURL(file);
                }

                // تغيير شكل الـ zone
                zone.style.borderColor = 'var(--success)';
                zone.style.borderStyle = 'solid';
                setTimeout(function() {
                    zone.style.borderColor = 'var(--border)';
                    zone.style.borderStyle = 'dashed';
                }, 1500);
            }
        });
    }

    // تشغيل عند تحميل الصفحة
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initImageUpload);
    } else {
        initImageUpload();
    }
})();
