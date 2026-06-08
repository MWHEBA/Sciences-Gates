class SchemaValidator:
    REQUIRED = {
        "EducationalOrganization": ["name", "url"],
        "NewsArticle": ["headline", "datePublished", "author"],
        "FAQPage": ["mainEntity"],
        "BreadcrumbList": ["itemListElement"],
    }

    RECOMMENDED = {
        "EducationalOrganization": ["address", "telephone", "logo", "sameAs"],
    }

    def validate(self, schemas, expected_types):
        issues = []
        passed = []
        found = []

        for schema in schemas:
            # Handle broken JSON-LD
            if not schema.get("valid_json"):
                issues.append({
                    "code": "INVALID_SCHEMA_JSON",
                    "message": f"خطأ هيكلي في مخطط الـ JSON-LD: {schema.get('error', '')}"
                })
                continue

            obj = schema.get("parsed") or {}
            self._validate_object(obj, issues, passed, found)

        # Check for missing expected schemas
        for expected in expected_types:
            if expected not in found:
                issues.append({
                    "code": f"MISSING_SCHEMA_{expected.upper()}",
                    "message": f"المخطط المنظم (Schema Markup) من نوع '{expected}' مطلوب ومفقود."
                })

        return {"issues": issues, "passed": passed, "found": found}

    def _validate_object(self, obj, issues, passed, found):
        if not isinstance(obj, dict):
            return

        # Check @context validation
        context = obj.get("@context")
        if context:
            context_str = str(context).lower().strip()
            if "schema.org" not in context_str:
                issues.append({
                    "code": "INVALID_SCHEMA_CONTEXT",
                    "message": f"سياق المخطط (schema context) غير صالح أو غير موثق: {context}"
                })
            else:
                passed.append("@context")

        # Handle @graph patterns recursively (common in modern SEO plugins)
        if "@graph" in obj:
            graph = obj["@graph"]
            if isinstance(graph, list):
                for node in graph:
                    self._validate_object(node, issues, passed, found)
            return

        # Extract and support @type as list or string
        schema_types = obj.get("@type")
        if not schema_types:
            return

        if isinstance(schema_types, str):
            schema_types = [schema_types]
        elif not isinstance(schema_types, list):
            return

        for schema_type in schema_types:
            if not isinstance(schema_type, str):
                continue

            found.append(schema_type)

            # Validate required properties (cause warnings/deductions)
            for prop in self.REQUIRED.get(schema_type, []):
                val = obj.get(prop)
                if val is None or (isinstance(val, list) and not val) or (isinstance(val, str) and not val.strip()):
                    issues.append({
                        "code": "SCHEMA_MISSING_PROP",
                        "message": f"المخطط المنظم {schema_type} يفتقد الخاصية المطلوبة: {prop}."
                    })
                else:
                    passed.append(f"{schema_type}.{prop}")

            # Validate recommended properties (soft warnings, no scoring deduction)
            for prop in self.RECOMMENDED.get(schema_type, []):
                val = obj.get(prop)
                if val is None or (isinstance(val, list) and not val) or (isinstance(val, str) and not val.strip()):
                    issues.append({
                        "code": "SCHEMA_RECOMMENDED_PROP_MISSING",
                        "message": f"يوصى بوجود الخاصية '{prop}' في مخطط {schema_type} لتحسين نتائج البحث المحلية."
                    })
                else:
                    passed.append(f"{schema_type}.{prop}")

            # BreadcrumbList ListItem structure validation
            if schema_type == "BreadcrumbList":
                items = obj.get("itemListElement", [])
                if isinstance(items, list) and items:
                    for idx, item in enumerate(items):
                        if not isinstance(item, dict):
                            continue
                        item_type = item.get("@type")
                        if item_type != "ListItem":
                            issues.append({
                                "code": "BREADCRUMB_INVALID_ITEM",
                                "message": f"العنصر رقم {idx + 1} في BreadcrumbList ليس ListItem صالح."
                            })
                        if not item.get("position"):
                            issues.append({
                                "code": "BREADCRUMB_MISSING_POSITION",
                                "message": f"العنصر رقم {idx + 1} في BreadcrumbList يفتقد الترتيب (position)."
                            })
                        if not item.get("name"):
                            issues.append({
                                "code": "BREADCRUMB_MISSING_NAME",
                                "message": f"العنصر رقم {idx + 1} في BreadcrumbList يفتقد الاسم (name)."
                            })
                        if not item.get("item"):
                            issues.append({
                                "code": "BREADCRUMB_MISSING_ITEM",
                                "message": f"العنصر رقم {idx + 1} في BreadcrumbList يفتقد الرابط (item)."
                            })

            # FAQPage answers text length validation
            if schema_type == "FAQPage":
                entities = obj.get("mainEntity", []) or []
                if not isinstance(entities, list) or not entities:
                    issues.append({
                        "code": "FAQPAGE_EMPTY",
                        "message": "العنصر الرئيسي mainEntity في FAQPage فارغ أو غير صالح."
                    })
                else:
                    for idx, entity in enumerate(entities):
                        if not isinstance(entity, dict):
                            continue
                        question = entity.get("name", "").strip()
                        answer_obj = entity.get("acceptedAnswer") or {}
                        answer = answer_obj.get("text", "").strip() if isinstance(answer_obj, dict) else ""

                        if not question:
                            issues.append({
                                "code": "FAQ_MISSING_QUESTION",
                                "message": f"السؤال رقم {idx + 1} في FAQPage فارغ."
                            })
                        if not answer:
                            issues.append({
                                "code": "FAQ_MISSING_ANSWER",
                                "message": f"السؤال رقم {idx + 1} في FAQPage ليس له إجابة."
                            })
                        elif len(answer) < 10:
                            issues.append({
                                "code": "FAQ_SHORT_ANSWER",
                                "message": f"إجابة السؤال رقم {idx + 1} في FAQPage قصيرة جداً (أقل من 10 أحرف)."
                            })
