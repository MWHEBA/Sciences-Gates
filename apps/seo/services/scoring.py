class SEOScoringEngine:
    def __init__(self, full_page, main_content, model_checks, schema_results, profile):
        self.full_page = full_page
        self.main_content = main_content
        self.model_checks = model_checks
        self.schema_results = schema_results
        self.profile = profile

        self.categories = {
            "meta_indexability": {"earned": 0, "max": 25},
            "content_completeness": {"earned": 0, "max": 25},
            "eeat_signals": {"earned": 0, "max": 20},
            "schema_quality": {"earned": 0, "max": 20},
            "media_links": {"earned": 0, "max": 10},
        }
        self.critical_issues = []
        self.warnings = []
        self.passed = []

    def evaluate(self):
        self._check_meta_indexability()
        self._check_content()
        self._check_eeat()
        self._check_schema()
        self._check_media_links()

        score = sum(x["earned"] for x in self.categories.values())
        grade = "good" if score >= 85 else ("needs_improvement" if score >= 60 else "critical")
        return {
            "score": score,
            "grade": grade,
            "categories": self.categories,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "passed_checks": self.passed,
            "critical_count": len(self.critical_issues),
            "warning_count": len(self.warnings),
            "passed_count": len(self.passed),
        }

    def _check_meta_indexability(self):
        earned = 0
        title = self.full_page.get("title", "")
        desc = self.full_page.get("meta_description", "")
        robots = (self.full_page.get("robots", "") or "").lower()

        if title:
            earned += 10 if 40 <= len(title) <= 60 else 5
            self.passed.append("title")
        else:
            self.critical_issues.append({"code": "MISSING_TITLE", "message": "عنوان الصفحة مفقود."})

        if desc:
            earned += 10 if 120 <= len(desc) <= 160 else 5
            self.passed.append("meta_description")
        else:
            self.warnings.append({"code": "MISSING_META_DESCRIPTION", "message": "الوصف التعريفي مفقود."})

        canonical = self.full_page.get("canonical", "")
        if canonical:
            earned += 3
            self.passed.append("canonical")
        if robots and "noindex" not in robots:
            earned += 2
            self.passed.append("indexable")
        elif "noindex" in robots:
            earned = 0
            self.critical_issues.append({"code": "NOINDEX_SET", "message": "الصفحة مضبوطة على noindex."})

        self.categories["meta_indexability"]["earned"] = min(25, earned)

    def _check_content(self):
        earned = 0
        if self.main_content.get("selector_missing"):
            self.critical_issues.append({"code": "MISSING_CONTENT_SELECTOR", "message": "لم يتم العثور على [data-seo-content]."})
            self.categories["content_completeness"]["earned"] = 0
            return

        if self.main_content.get("word_count", 0) >= self.profile.min_word_count:
            earned += 10
            self.passed.append("word_count")
        else:
            self.warnings.append({"code": "LOW_WORD_COUNT", "message": "عدد الكلمات أقل من المطلوب."})

        model_points = 15
        checks = self.model_checks or []
        if checks:
            pass_count = len([c for c in checks if c.get("status") == "pass"])
            warn_count = len([c for c in checks if c.get("status") == "warning"])
            total = len(checks)
            earned += int(model_points * ((pass_count + (warn_count * 0.5)) / max(total, 1)))
            for item in checks:
                if item["status"] == "fail":
                    self.warnings.append({"code": f"SECTION_FAIL_{item['key'].upper()}", "message": item["message"]})
                elif item["status"] == "warning":
                    self.warnings.append({"code": f"SECTION_WARN_{item['key'].upper()}", "message": item["message"]})
                else:
                    self.passed.append(f"section_{item['key']}")

        self.categories["content_completeness"]["earned"] = min(25, earned)

    def _check_eeat(self):
        earned = 0
        if self.full_page.get("h1"):
            earned += 5
        else:
            self.critical_issues.append({"code": "MISSING_H1", "message": "لا يوجد H1 في الصفحة."})

        if self.full_page.get("author_visible"):
            earned += 4
        if self.full_page.get("date_visible"):
            earned += 4
        if self.full_page.get("html_lang"):
            earned += 4
        else:
            self.warnings.append({"code": "MISSING_HTML_LANG", "message": "وسم html لا يحتوي lang."})
        if self.full_page.get("breadcrumb_present"):
            earned += 3

        self.categories["eeat_signals"]["earned"] = min(20, earned)

    def _check_schema(self):
        earned = 0
        found = self.schema_results.get("found", [])
        issues = self.schema_results.get("issues", [])

        if found:
            earned += 5
        if not any(issue["code"] == "INVALID_SCHEMA_JSON" for issue in issues):
            earned += 5
        else:
            self.warnings.extend(issues)

        required_issues = [x for x in issues if x["code"] in {"SCHEMA_MISSING_PROP", "FAQPAGE_EMPTY", "FAQ_MISSING_ANSWER"}]
        if required_issues:
            self.warnings.extend(required_issues)
            earned += max(0, 10 - (2 * len(required_issues)))
        else:
            earned += 10

        for issue in issues:
            if issue["code"].startswith("MISSING_SCHEMA_"):
                self.warnings.append(issue)

        self.categories["schema_quality"]["earned"] = min(20, max(0, earned))

    def _check_media_links(self):
        earned = 0
        image_warnings = self.main_content.get("image_warnings", [])
        if image_warnings:
            self.warnings.extend(image_warnings)
        else:
            earned += 5

        internal_links = [x for x in self.main_content.get("links", []) if x.get("href", "").startswith("/")]
        if len(internal_links) >= self.profile.min_internal_links:
            earned += 3
        else:
            self.warnings.append({"code": "LOW_INTERNAL_LINKS", "message": "عدد الروابط الداخلية أقل من المطلوب."})

        if self.full_page.get("og_image"):
            earned += 2
        else:
            self.warnings.append({"code": "MISSING_OG_IMAGE", "message": "صورة OG غير موجودة."})

        self.categories["media_links"]["earned"] = min(10, earned)
