import re

class ModelAwareChecker:
    """Validates DB fields/relations based on profile section rules."""

    def _strip_html(self, text):
        if not text:
            return ""
        clean = re.compile(r'<[^>]+>')
        return clean.sub(' ', text).strip()

    def run(self, content_obj, profile):
        results = []
        for rule in profile.section_checks:
            results.append(self._check_rule(content_obj, rule))

        # Check image alt fields if the entity has the corresponding image field and it is populated
        alt_fields = [
            ('logo', 'logo_alt', 'النص البديل للشعار'),
            ('main_image', 'main_image_alt', 'النص البديل للصورة الرئيسية'),
            ('featured_image', 'featured_image_alt', 'النص البديل للصورة المميزة'),
        ]
        for img_field, alt_field, label in alt_fields:
            if hasattr(content_obj, img_field) and getattr(content_obj, img_field):
                alt_value = str(getattr(content_obj, alt_field, '') or '').strip()
                if not alt_value:
                    results.append({
                        "key": alt_field,
                        "status": "fail",
                        "label": label,
                        "message": f"{label}: النص البديل مفقود للـ SEO."
                    })
                elif len(alt_value) < 5:
                    results.append({
                        "key": alt_field,
                        "status": "warning",
                        "label": label,
                        "message": f"{label}: النص البديل قصير جداً ({len(alt_value)} حرف). الحد الأدنى 5 أحرف وصفية."
                    })
                else:
                    results.append({
                        "key": alt_field,
                        "status": "pass",
                        "label": label,
                        "message": f"{label}: مكتمل."
                    })
        return results

    def _check_rule(self, obj, rule):
        key = rule["key"]
        label = rule["label"]
        min_chars = rule.get("min_chars", 0)
        is_relation = rule.get("is_relation", False)
        require_any = rule.get("require_any", False)

        if is_relation:
            relation_name = rule["field_names"][0]
            manager = getattr(obj, relation_name, None)
            count = manager.count() if manager is not None else 0
            if count <= 0:
                return {"key": key, "status": "fail", "label": label, "message": f"{label}: لا توجد بيانات مرتبطة."}
            return {"key": key, "status": "pass", "label": label, "message": f"{label}: {count} عناصر."}

        # Extract values and clean HTML
        values = [str(getattr(obj, field_name, "") or "") for field_name in rule.get("field_names", [])]
        cleaned_values = [self._strip_html(val) for val in values]

        if require_any:
            # Check if at least one field is non-empty and meets min_chars
            # Zip values and cleaned_values to find the one with the maximum cleaned length
            zipped = list(zip(values, cleaned_values))
            best_val, best_cleaned = max(zipped, key=lambda x: len(x[1]), default=("", ""))

            if not best_cleaned:
                return {"key": key, "status": "fail", "label": label, "message": f"{label}: الحقول المطلوبة فارغة."}

            if len(best_cleaned) < min_chars:
                return {
                    "key": key,
                    "status": "warning",
                    "label": label,
                    "message": f"{label}: المحتوى قصير ({len(best_cleaned)} حرف). الحد الأدنى {min_chars}.",
                }
        else:
            val = values[0] if values else ""
            cleaned_val = cleaned_values[0] if cleaned_values else ""

            if not cleaned_val:
                return {"key": key, "status": "fail", "label": label, "message": f"{label}: الحقل فارغ."}
            if len(cleaned_val) < min_chars:
                return {
                    "key": key,
                    "status": "warning",
                    "label": label,
                    "message": f"{label}: المحتوى قصير ({len(cleaned_val)} حرف). الحد الأدنى {min_chars}.",
                }

        return {"key": key, "status": "pass", "label": label, "message": f"{label}: مكتمل."}
