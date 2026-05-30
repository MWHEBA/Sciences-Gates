class ModelAwareChecker:
    """Validates DB fields/relations based on profile section rules."""

    def run(self, content_obj, profile):
        results = []
        for rule in profile.section_checks:
            results.append(self._check_rule(content_obj, rule))
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

        values = [str(getattr(obj, field_name, "") or "").strip() for field_name in rule.get("field_names", [])]
        value = max(values, key=len, default="") if require_any else (values[0] if values else "")

        if not value:
            return {"key": key, "status": "fail", "label": label, "message": f"{label}: الحقل فارغ."}
        if len(value) < min_chars:
            return {
                "key": key,
                "status": "warning",
                "label": label,
                "message": f"{label}: المحتوى قصير ({len(value)} حرف). الحد الأدنى {min_chars}.",
            }
        return {"key": key, "status": "pass", "label": label, "message": f"{label}: مكتمل."}
