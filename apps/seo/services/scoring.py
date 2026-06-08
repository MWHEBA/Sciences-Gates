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
        self._check_heading_structure()
        self._check_schema()
        self._check_media_links()
        self._check_focus_keyword()

        score = sum(x["earned"] for x in self.categories.values())
        
        # Strict grading: Critical issues completely block "Good" grade. Good threshold is now 90.
        if score >= 90 and len(self.critical_issues) == 0:
            grade = "good"
        elif score >= 60:
            grade = "needs_improvement"
        else:
            grade = "critical"

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
        title = (self.full_page.get("title", "") or "").strip()
        desc = (self.full_page.get("meta_description", "") or "").strip()
        robots = (self.full_page.get("robots", "") or "").lower()

        # Check title
        if title:
            earned += 10 if 40 <= len(title) <= 60 else 5
            self.passed.append("title")
        else:
            self.critical_issues.append({"code": "MISSING_TITLE", "message": "عنوان الصفحة مفقود أو فارغ."})

        # Check description
        if desc:
            earned += 10 if 120 <= len(desc) <= 160 else 5
            self.passed.append("meta_description")
        else:
            self.warnings.append({"code": "MISSING_META_DESCRIPTION", "message": "الوصف التعريفي مفقود أو فارغ."})

        # Check canonical URL validity
        canonical = (self.full_page.get("canonical", "") or "").strip()
        if canonical and (canonical.startswith("http") or canonical.startswith("/")):
            earned += 3
            self.passed.append("canonical")
        else:
            self.warnings.append({"code": "INVALID_CANONICAL", "message": "الرابط الأساسي (canonical) غير موجود أو غير صالح."})

        # Check robots indexability
        if robots:
            if "noindex" in robots:
                earned = 0
                self.critical_issues.append({"code": "NOINDEX_SET", "message": "الصفحة مضبوطة على noindex مما يمنع محركات البحث من فهرستها."})
            elif "nofollow" in robots:
                # nofollow blocks links crawl. Deduct points and raise warning.
                earned += 1
                self.warnings.append({"code": "NOFOLLOW_SET", "message": "الصفحة مضبوطة على nofollow مما يمنع محركات البحث من تتبع الروابط."})
            else:
                earned += 2
                self.passed.append("indexable")
        else:
            # Default is indexable
            earned += 2

        self.categories["meta_indexability"]["earned"] = min(25, earned)

    def _check_content(self):
        earned = 0
        if self.main_content.get("selector_missing"):
            self.critical_issues.append({"code": "MISSING_CONTENT_SELECTOR", "message": "لم يتم العثور على عنصر المحتوى [data-seo-content]."})
            self.categories["content_completeness"]["earned"] = 0
            return

        if self.main_content.get("word_count", 0) >= self.profile.min_word_count:
            earned += 10
            self.passed.append("word_count")
        else:
            self.warnings.append({"code": "LOW_WORD_COUNT", "message": f"عدد الكلمات أقل من الحد الأدنى المطلوب ({self.main_content.get('word_count')} من {self.profile.min_word_count} كلمة)."})

        model_points = 15
        checks = self.model_checks or []
        if checks:
            pass_count = len([c for c in checks if c.get("status") == "pass"])
            warn_count = len([c for c in checks if c.get("status") == "warning"])
            total = len(checks)
            # Use round() instead of int() to avoid truncation loss
            earned += round(model_points * ((pass_count + (warn_count * 0.5)) / max(total, 1)))
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
        h1 = (self.full_page.get("h1", "") or "").strip()
        lang = (self.full_page.get("html_lang", "") or "").lower().strip()
        breadcrumb = self.full_page.get("breadcrumb_present", False)

        # Check H1
        if h1:
            pass
        else:
            self.critical_issues.append({"code": "MISSING_H1", "message": "لا يوجد عنوان رئيسي H1 في الصفحة."})

        # Check html lang value correctness
        if not lang:
            self.warnings.append({"code": "MISSING_HTML_LANG", "message": "وسم html لا يحتوي على لغة (lang)."})
        elif not (lang.startswith("ar") or lang.startswith("en")):
            self.warnings.append({"code": "INVALID_HTML_LANG", "message": f"لغة الصفحة المحددة غير صالحة أو غير مدعومة: {lang}."})

        # Check breadcrumbs
        if not breadcrumb:
            self.warnings.append({"code": "MISSING_BREADCRUMB", "message": "مسار التنقل (Breadcrumbs) غير موجود في الصفحة."})

        # Profile-aware EEAT scoring
        if getattr(self.profile, "eeat_requires_author_date", False):
            # Editorial profile (articles)
            if h1:
                earned += 5
            if self.full_page.get("author_visible"):
                earned += 4
            else:
                self.warnings.append({"code": "MISSING_AUTHOR", "message": "اسم كاتب المقال غير ظاهر في الصفحة."})
            
            if self.full_page.get("date_visible"):
                earned += 4
            else:
                self.warnings.append({"code": "MISSING_PUBLISH_DATE", "message": "تاريخ نشر المقال غير ظاهر في الصفحة."})
            
            if lang and (lang.startswith("ar") or lang.startswith("en")):
                earned += 4
            if breadcrumb:
                earned += 3
        else:
            # Corporate / Organization profile (universities, institutes, majors)
            # Reallocate the 8 author/date points: H1 gets +2, Lang gets +3, Breadcrumb gets +3
            if h1:
                earned += 7
            if lang and (lang.startswith("ar") or lang.startswith("en")):
                earned += 7
            if breadcrumb:
                earned += 6

        self.categories["eeat_signals"]["earned"] = min(20, earned)

    def _check_heading_structure(self):
        """Audit heading hierarchy: detect duplicate H1 and level jumps (e.g. H2 -> H4)."""
        # Duplicate H1 detection
        h1_tags = self.full_page.get("h1_tags", [])
        if len(h1_tags) > 1:
            self.warnings.append({
                "code": "DUPLICATE_H1",
                "message": f"تم اكتشاف {len(h1_tags)} وسوم H1 في الصفحة. يجب أن تحتوي الصفحة على H1 واحد فقط."
            })
        elif h1_tags:
            self.passed.append("single_h1")

        # Heading hierarchy jump detection
        # Build full ordered heading list: H1 (from full_page) + H2..H4 (from main_content)
        h1_text = (self.full_page.get("h1", "") or "").strip()
        section_headings = self.main_content.get("headings", [])  # [{level, text}, ...]

        all_headings = []
        if h1_text:
            all_headings.append({"level": 1, "text": h1_text})
        all_headings.extend(section_headings)

        if len(all_headings) >= 2:
            jump_details = []
            for i in range(1, len(all_headings)):
                prev_level = all_headings[i - 1]["level"]
                curr_level = all_headings[i]["level"]
                # A jump is when level increases by more than 1 (e.g. H2 -> H4)
                if curr_level > prev_level + 1:
                    jump_details.append(
                        f"H{prev_level} ({all_headings[i-1]['text'][:30]}) -> H{curr_level} ({all_headings[i]['text'][:30]})"
                    )
            if jump_details:
                self.warnings.append({
                    "code": "HEADING_HIERARCHY_JUMP",
                    "message": f"تسلسل العناوين يحتوي على قفزات غير صحيحة: {'; '.join(jump_details)}. يجب أن يكون التسلسل متدرجاً (H1 > H2 > H3)."
                })
            else:
                if len(all_headings) > 1:
                    self.passed.append("heading_hierarchy_valid")

    def _check_schema(self):
        found = self.schema_results.get("found", [])
        issues = self.schema_results.get("issues", [])

        # Check for completely broken JSON-LD
        invalid_json_issues = [i for i in issues if i["code"] == "INVALID_SCHEMA_JSON"]
        if invalid_json_issues:
            self.critical_issues.extend(invalid_json_issues)
            self.categories["schema_quality"]["earned"] = 0
            return

        earned = 0
        if found:
            earned += 5

        # Check required/missing schema property issues (these deduct points)
        required_issues = [x for x in issues if x["code"] in {"SCHEMA_MISSING_PROP", "FAQPAGE_EMPTY", "FAQ_MISSING_ANSWER"}]
        if required_issues:
            self.warnings.extend(required_issues)
            earned += max(0, 15 - (3 * len(required_issues)))
        else:
            if found:
                earned += 15

        # All other issues (like missing recommended fields or listItem checks) are warnings
        other_issues = [
            x for x in issues 
            if x["code"] not in {"SCHEMA_MISSING_PROP", "FAQPAGE_EMPTY", "FAQ_MISSING_ANSWER", "INVALID_SCHEMA_JSON"} 
            and not x["code"].startswith("MISSING_SCHEMA_")
        ]
        self.warnings.extend(other_issues)

        # Check for missing expected schemas
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

        # Validate OG image URL structure
        og_image = (self.full_page.get("og_image", "") or "").strip()
        if og_image and (og_image.startswith("http") or og_image.startswith("/") or og_image.startswith("media/")):
            earned += 2
            self.passed.append("og_image")
        else:
            self.warnings.append({"code": "MISSING_OG_IMAGE", "message": "صورة المشاركة (og:image) مفقودة أو غير صالحة."})

        self.categories["media_links"]["earned"] = min(10, earned)

    def _check_focus_keyword(self):
        focus_kw = (self.full_page.get("focus_keyword", "") or "").strip().lower()
        if not focus_kw:
            return

        title = (self.full_page.get("title", "") or "").strip().lower()
        desc = (self.full_page.get("meta_description", "") or "").strip().lower()
        h1 = (self.full_page.get("h1", "") or "").strip().lower()

        # Deduct score from specific categories if focus keyword is missing from critical zones
        title_deduction = 0
        desc_deduction = 0
        h1_deduction = 0
        density_deduction = 0

        # 1. Check in Title
        if focus_kw in title:
            self.passed.append("focus_keyword_in_title")
        else:
            title_deduction = 2
            self.warnings.append({
                "code": "FOCUS_KEYWORD_MISSING_TITLE",
                "message": f"الكلمة المفتاحية الرئيسية '{focus_kw}' غير موجودة في عنوان الصفحة (Title)."
            })

        # 2. Check in Meta Description
        if focus_kw in desc:
            self.passed.append("focus_keyword_in_description")
        else:
            desc_deduction = 2
            self.warnings.append({
                "code": "FOCUS_KEYWORD_MISSING_DESCRIPTION",
                "message": f"الكلمة المفتاحية الرئيسية '{focus_kw}' غير موجودة في الوصف التعريفي (Meta Description)."
            })

        # 3. Check in H1
        if focus_kw in h1:
            self.passed.append("focus_keyword_in_h1")
        else:
            h1_deduction = 2
            self.warnings.append({
                "code": "FOCUS_KEYWORD_MISSING_H1",
                "message": f"الكلمة المفتاحية الرئيسية '{focus_kw}' غير موجودة في العنوان الرئيسي (H1)."
            })

        # 4. Check Density in Content (purified text)
        word_count = self.main_content.get("word_count", 0)
        kw_count = self.main_content.get("focus_keyword_count", 0)
        density = (kw_count / word_count * 100) if word_count > 0 else 0

        if word_count > 0:
            if 0.5 <= density <= 2.5:
                self.passed.append("focus_keyword_density_good")
                # Also confirm keyword appears in content body
                if kw_count > 0:
                    self.passed.append("focus_keyword_in_content")
            elif density < 0.5:
                density_deduction = 2
                self.warnings.append({
                    "code": "FOCUS_KEYWORD_DENSITY_LOW",
                    "message": (
                        f"كثافة الكلمة المفتاحية '{focus_kw}' منخفضة جداً ({density:.2f}%). "
                        f"عدد الظهور: {kw_count} مرة في {word_count} كلمة. "
                        f"يوصى بنسبة 0.5% إلى 2.5%."
                    )
                })
            else:
                density_deduction = 1
                self.warnings.append({
                    "code": "FOCUS_KEYWORD_DENSITY_HIGH",
                    "message": (
                        f"كثافة الكلمة المفتاحية '{focus_kw}' مرتفعة جداً ({density:.2f}%). "
                        f"عدد الظهور: {kw_count} مرة في {word_count} كلمة. "
                        f"قد يُعدّ حشواً للكلمات المفتاحية (Keyword Stuffing)."
                    )
                })

        # Apply deductions
        if title_deduction or desc_deduction:
            orig = self.categories["meta_indexability"]["earned"]
            self.categories["meta_indexability"]["earned"] = max(0, orig - (title_deduction + desc_deduction))

        if h1_deduction:
            orig = self.categories["eeat_signals"]["earned"]
            self.categories["eeat_signals"]["earned"] = max(0, orig - h1_deduction)

        if density_deduction:
            orig = self.categories["content_completeness"]["earned"]
            self.categories["content_completeness"]["earned"] = max(0, orig - density_deduction)
