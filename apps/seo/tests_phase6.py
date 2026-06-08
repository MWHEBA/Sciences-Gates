"""
Phase 6 SEO Audit Tests.

Tests for:
- Duplicate H1 detection (DUPLICATE_H1)
- Heading hierarchy jump detection (HEADING_HIERARCHY_JUMP)
- Focus keyword density reporting (FOCUS_KEYWORD_DENSITY_LOW / HIGH / GOOD)
- Focus keyword in content body passed signal
"""
from django.test import TestCase

from apps.seo.services.scoring import SEOScoringEngine
from apps.seo.services.content_profiles import profile_for


def _make_engine(full_page_overrides=None, main_content_overrides=None, focus_keyword=""):
    """Helper: build a minimal SEOScoringEngine with provided overrides."""
    profile = profile_for("universities")

    full_page = {
        "title": "جامعة ماليزيا العالمية - بوابات العلوم",
        "meta_description": "وصف تعريفي واضح لجامعة ماليزيا العالمية يتجاوز مئة وعشرين حرفاً لضمان الجودة.",
        "canonical": "https://sciencesgates.com/universities/test/",
        "robots": "index, follow",
        "html_lang": "ar",
        "h1": "جامعة ماليزيا العالمية",
        "h1_tags": ["جامعة ماليزيا العالمية"],
        "og_title": "جامعة ماليزيا العالمية",
        "og_description": "وصف تعريفي واضح",
        "og_image": "https://sciencesgates.com/media/img.jpg",
        "schemas": [],
        "author_visible": False,
        "date_visible": False,
        "breadcrumb_present": True,
        "focus_keyword": focus_keyword,
    }

    main_content = {
        "selector_missing": False,
        "word_count": 500,
        "headings": [
            {"level": 2, "text": "عن الجامعة"},
            {"level": 3, "text": "الأقسام والكليات"},
        ],
        "links": [{"href": "/universities/", "text": "الجامعات"}],
        "image_warnings": [],
        "focus_keyword_count": 0,
    }

    if full_page_overrides:
        full_page.update(full_page_overrides)
    if main_content_overrides:
        main_content.update(main_content_overrides)

    model_checks = []
    schema_results = {"found": [], "issues": [], "passed": []}

    return SEOScoringEngine(full_page, main_content, model_checks, schema_results, profile)


# ─────────────────────────────────────────────────
# 1. Duplicate H1 Detection
# ─────────────────────────────────────────────────
class TestDuplicateH1Detection(TestCase):

    def test_single_h1_passes(self):
        """Single H1 should pass cleanly with 'single_h1' in passed checks."""
        engine = _make_engine()
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertNotIn("DUPLICATE_H1", codes)
        self.assertIn("single_h1", result["passed_checks"])

    def test_duplicate_h1_raises_warning(self):
        """Multiple H1 tags must trigger DUPLICATE_H1 warning."""
        engine = _make_engine(full_page_overrides={
            "h1_tags": ["العنوان الأول", "العنوان الثاني"]
        })
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertIn("DUPLICATE_H1", codes)
        self.assertNotIn("single_h1", result["passed_checks"])

    def test_duplicate_h1_is_warning_not_critical(self):
        """DUPLICATE_H1 must be a warning, not a critical issue."""
        engine = _make_engine(full_page_overrides={
            "h1_tags": ["عنوان أ", "عنوان ب", "عنوان ج"]
        })
        result = engine.evaluate()
        critical_codes = [c["code"] for c in result["critical_issues"]]
        warning_codes = [w["code"] for w in result["warnings"]]
        self.assertNotIn("DUPLICATE_H1", critical_codes)
        self.assertIn("DUPLICATE_H1", warning_codes)

    def test_no_h1_triggers_missing_h1_critical_not_duplicate(self):
        """Missing H1 must trigger MISSING_H1 critical, not DUPLICATE_H1."""
        engine = _make_engine(full_page_overrides={
            "h1": "",
            "h1_tags": [],
        })
        result = engine.evaluate()
        critical_codes = [c["code"] for c in result["critical_issues"]]
        warning_codes = [w["code"] for w in result["warnings"]]
        self.assertIn("MISSING_H1", critical_codes)
        self.assertNotIn("DUPLICATE_H1", warning_codes)


# ─────────────────────────────────────────────────
# 2. Heading Hierarchy Jump Detection
# ─────────────────────────────────────────────────
class TestHeadingHierarchyJumps(TestCase):

    def test_valid_hierarchy_passes(self):
        """H1 -> H2 -> H3 is a valid, sequential hierarchy."""
        engine = _make_engine(main_content_overrides={
            "headings": [
                {"level": 2, "text": "القسم الأول"},
                {"level": 3, "text": "تفاصيل القسم"},
            ]
        })
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertNotIn("HEADING_HIERARCHY_JUMP", codes)
        self.assertIn("heading_hierarchy_valid", result["passed_checks"])

    def test_h1_to_h3_jump_detected(self):
        """H1 -> H3 (skipping H2) should trigger HEADING_HIERARCHY_JUMP."""
        engine = _make_engine(main_content_overrides={
            "headings": [
                {"level": 3, "text": "قسم بلا H2 قبله"},
            ]
        })
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertIn("HEADING_HIERARCHY_JUMP", codes)

    def test_h2_to_h4_jump_detected(self):
        """H2 -> H4 (skipping H3) should trigger HEADING_HIERARCHY_JUMP."""
        engine = _make_engine(main_content_overrides={
            "headings": [
                {"level": 2, "text": "القسم الرئيسي"},
                {"level": 4, "text": "تفاصيل متقدمة بدون H3"},
            ]
        })
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertIn("HEADING_HIERARCHY_JUMP", codes)

    def test_hierarchy_jump_is_warning_not_critical(self):
        """HEADING_HIERARCHY_JUMP must be a warning, not a critical issue."""
        engine = _make_engine(main_content_overrides={
            "headings": [
                {"level": 2, "text": "قسم"},
                {"level": 4, "text": "قسم فرعي متقدم"},
            ]
        })
        result = engine.evaluate()
        critical_codes = [c["code"] for c in result["critical_issues"]]
        warning_codes = [w["code"] for w in result["warnings"]]
        self.assertNotIn("HEADING_HIERARCHY_JUMP", critical_codes)
        self.assertIn("HEADING_HIERARCHY_JUMP", warning_codes)

    def test_going_down_levels_is_valid(self):
        """H3 -> H2 (going back up/down) should not trigger a hierarchy jump warning."""
        engine = _make_engine(main_content_overrides={
            "headings": [
                {"level": 2, "text": "الفصل الأول"},
                {"level": 3, "text": "مبحث فرعي"},
                {"level": 2, "text": "الفصل الثاني"},
            ]
        })
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertNotIn("HEADING_HIERARCHY_JUMP", codes)

    def test_single_heading_no_hierarchy_check(self):
        """Only H1 in the page should not trigger any hierarchy check."""
        engine = _make_engine(main_content_overrides={"headings": []})
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertNotIn("HEADING_HIERARCHY_JUMP", codes)
        # heading_hierarchy_valid is only added when there are 2+ headings
        self.assertNotIn("heading_hierarchy_valid", result["passed_checks"])

    def test_jump_message_contains_heading_text(self):
        """The HEADING_HIERARCHY_JUMP warning message should include heading text details."""
        engine = _make_engine(main_content_overrides={
            "headings": [
                {"level": 2, "text": "الفصل الرئيسي"},
                {"level": 4, "text": "التفاصيل الخاصة"},
            ]
        })
        result = engine.evaluate()
        jump_warns = [w for w in result["warnings"] if w["code"] == "HEADING_HIERARCHY_JUMP"]
        self.assertTrue(len(jump_warns) == 1)
        self.assertIn("H2", jump_warns[0]["message"])
        self.assertIn("H4", jump_warns[0]["message"])


# ─────────────────────────────────────────────────
# 3. Focus Keyword Density Reporting
# ─────────────────────────────────────────────────
class TestKeywordDensityReporting(TestCase):

    def test_no_focus_keyword_skips_density_checks(self):
        """If focus_keyword is empty, no density warnings or passed signals."""
        engine = _make_engine(focus_keyword="")
        result = engine.evaluate()
        all_codes = [w["code"] for w in result["warnings"]] + result["passed_checks"]
        self.assertNotIn("FOCUS_KEYWORD_DENSITY_LOW", all_codes)
        self.assertNotIn("FOCUS_KEYWORD_DENSITY_HIGH", all_codes)
        self.assertNotIn("focus_keyword_density_good", all_codes)

    def test_keyword_density_good_range(self):
        """Keyword appearing at ~1% density should pass with 'focus_keyword_density_good'."""
        # 500 words, keyword appears 5 times -> density = 1.0%
        engine = _make_engine(
            focus_keyword="ماليزيا",
            main_content_overrides={"word_count": 500, "focus_keyword_count": 5}
        )
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertNotIn("FOCUS_KEYWORD_DENSITY_LOW", codes)
        self.assertNotIn("FOCUS_KEYWORD_DENSITY_HIGH", codes)
        self.assertIn("focus_keyword_density_good", result["passed_checks"])
        self.assertIn("focus_keyword_in_content", result["passed_checks"])

    def test_keyword_density_too_low_warning(self):
        """Keyword appearing at 0.2% should trigger FOCUS_KEYWORD_DENSITY_LOW."""
        # 500 words, keyword appears 1 time -> density = 0.2%
        engine = _make_engine(
            focus_keyword="ماليزيا",
            main_content_overrides={"word_count": 500, "focus_keyword_count": 1}
        )
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertIn("FOCUS_KEYWORD_DENSITY_LOW", codes)
        self.assertNotIn("focus_keyword_density_good", result["passed_checks"])

    def test_keyword_density_too_high_warning(self):
        """Keyword appearing at 4% should trigger FOCUS_KEYWORD_DENSITY_HIGH."""
        # 500 words, keyword appears 20 times -> density = 4.0%
        engine = _make_engine(
            focus_keyword="ماليزيا",
            main_content_overrides={"word_count": 500, "focus_keyword_count": 20}
        )
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertIn("FOCUS_KEYWORD_DENSITY_HIGH", codes)
        self.assertNotIn("focus_keyword_density_good", result["passed_checks"])

    def test_keyword_density_low_message_includes_keyword_and_counts(self):
        """FOCUS_KEYWORD_DENSITY_LOW message must include keyword name, count, and word count."""
        engine = _make_engine(
            focus_keyword="الجامعة",
            main_content_overrides={"word_count": 400, "focus_keyword_count": 1}
        )
        result = engine.evaluate()
        low_warns = [w for w in result["warnings"] if w["code"] == "FOCUS_KEYWORD_DENSITY_LOW"]
        self.assertTrue(len(low_warns) >= 1)
        msg = low_warns[0]["message"]
        self.assertIn("الجامعة", msg)
        self.assertIn("1", msg)   # count
        self.assertIn("400", msg) # word count

    def test_keyword_density_high_message_includes_keyword(self):
        """FOCUS_KEYWORD_DENSITY_HIGH message must include the keyword name."""
        engine = _make_engine(
            focus_keyword="دراسة",
            main_content_overrides={"word_count": 300, "focus_keyword_count": 15}
        )
        result = engine.evaluate()
        high_warns = [w for w in result["warnings"] if w["code"] == "FOCUS_KEYWORD_DENSITY_HIGH"]
        self.assertTrue(len(high_warns) >= 1)
        self.assertIn("دراسة", high_warns[0]["message"])

    def test_keyword_in_content_not_added_when_density_low(self):
        """'focus_keyword_in_content' should NOT be in passed when density is low."""
        engine = _make_engine(
            focus_keyword="ماليزيا",
            main_content_overrides={"word_count": 1000, "focus_keyword_count": 1}
        )
        result = engine.evaluate()
        self.assertNotIn("focus_keyword_in_content", result["passed_checks"])

    def test_keyword_boundary_exactly_at_0_5_percent(self):
        """Exactly 0.5% density should be treated as 'good' (boundary inclusion)."""
        # 200 words, 1 occurrence -> 0.5% exactly
        engine = _make_engine(
            focus_keyword="ماليزيا",
            main_content_overrides={"word_count": 200, "focus_keyword_count": 1}
        )
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertNotIn("FOCUS_KEYWORD_DENSITY_LOW", codes)
        self.assertIn("focus_keyword_density_good", result["passed_checks"])

    def test_keyword_boundary_exactly_at_2_5_percent(self):
        """Exactly 2.5% density should be treated as 'good' (boundary inclusion)."""
        # 200 words, 5 occurrences -> 2.5%
        engine = _make_engine(
            focus_keyword="ماليزيا",
            main_content_overrides={"word_count": 200, "focus_keyword_count": 5}
        )
        result = engine.evaluate()
        codes = [w["code"] for w in result["warnings"]]
        self.assertNotIn("FOCUS_KEYWORD_DENSITY_HIGH", codes)
        self.assertIn("focus_keyword_density_good", result["passed_checks"])
