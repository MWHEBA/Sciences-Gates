class SchemaValidator:
    REQUIRED = {
        "EducationalOrganization": ["name", "url"],
        "NewsArticle": ["headline", "datePublished", "author"],
        "FAQPage": ["mainEntity"],
        "BreadcrumbList": ["itemListElement"],
    }

    def validate(self, schemas, expected_types):
        issues = []
        passed = []
        found = []

        for schema in schemas:
            if not schema.get("valid_json"):
                issues.append({"code": "INVALID_SCHEMA_JSON", "message": f"JSON-LD غير صالح: {schema.get('error', '')}"})
                continue

            obj = schema.get("parsed") or {}
            schema_type = obj.get("@type")
            if isinstance(schema_type, list):
                schema_type = schema_type[0] if schema_type else None
            if not schema_type:
                continue

            found.append(schema_type)
            for prop in self.REQUIRED.get(schema_type, []):
                if not obj.get(prop):
                    issues.append({"code": "SCHEMA_MISSING_PROP", "message": f"Schema {schema_type} يفتقد الخاصية: {prop}"})
                else:
                    passed.append(f"{schema_type}.{prop}")

            if schema_type == "FAQPage":
                entities = obj.get("mainEntity", []) or []
                if not entities:
                    issues.append({"code": "FAQPAGE_EMPTY", "message": "FAQPage.mainEntity فارغ."})
                for idx, entity in enumerate(entities):
                    answer = (entity.get("acceptedAnswer") or {}).get("text", "")
                    if not answer:
                        issues.append({"code": "FAQ_MISSING_ANSWER", "message": f"السؤال رقم {idx + 1} في FAQPage ليس له إجابة."})

        for expected in expected_types:
            if expected not in found:
                issues.append({"code": f"MISSING_SCHEMA_{expected.upper()}", "message": f"Schema مطلوب غير موجود: {expected}"})

        return {"issues": issues, "passed": passed, "found": found}
