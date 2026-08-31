"""
Tests for Yoast SEO Premium Keyphrase Synonyms functionality.
"""
from django.test import TestCase

from apps.seo.services.scoring import SEOScoringEngine
from apps.seo.services.content_profiles import profile_for


def _make_engine(full_page_overrides=None, main_content_overrides=None, focus_keyword="", keyphrase_synonyms=""):
    """Helper: build an SEOScoringEngine with synonyms and overrides."""
    profile = profile_for("universities")

    full_page = {
        "title": "جامعة ماليزيا العالمية - شركة بوابات العلوم",
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
        "keyphrase_synonyms": keyphrase_synonyms,
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
        "synonyms_counts": {},
        "intro_text": "هذه هي المقدمة الافتراضية للصفحة.",
        "image_alts": ["صورة لشعار الجامعة"],
    }

    if full_page_overrides:
        full_page.update(full_page_overrides)
    if main_content_overrides:
        main_content.update(main_content_overrides)

    model_checks = []
    schema_results = {"found": [], "issues": [], "passed": []}

    return SEOScoringEngine(full_page, main_content, model_checks, schema_results, profile)


class TestArabicTextNormalization(TestCase):
    """Verify that Arabic text normalization handles various common forms and diacritics."""

    def test_normalization_helper(self):
        engine = _make_engine()
        # Alef normalization
        self.assertEqual(engine._normalize("أحمد"), "احمد")
        self.assertEqual(engine._normalize("إسلام"), "اسلام")
        self.assertEqual(engine._normalize("آمال"), "امال")
        # Teh Marbuta normalization
        self.assertEqual(engine._normalize("جامعة"), "جامعه")
        self.assertEqual(engine._normalize("مدرسة"), "مدرسه")
        # Yeh and Alef Maksura normalization
        self.assertEqual(engine._normalize("على"), "علي")
        self.assertEqual(engine._normalize("في"), "في")
        # Diacritics stripping
        self.assertEqual(engine._normalize("دِرَاسَةٌ"), "دراسه")
        self.assertEqual(engine._normalize("الجامِعَةُ"), "الجامعه")

    def test_is_match_cases(self):
        engine = _make_engine()
        syns = ["التعليم في ماليزيا", "الدراسه بالخارج"]
        
        # Exact match
        self.assertTrue(engine._is_match("دليل التعليم في ماليزيا بالتفصيل", "دراسة", syns))
        # Normalized Arabic match (Teh Marbuta & Alef)
        self.assertTrue(engine._is_match("دليل الدراسه بالخارج", "دراسة", syns))
        self.assertTrue(engine._is_match("التعليم فى ماليزيا", "دراسة", syns))
        
        # Fail cases
        self.assertFalse(engine._is_match("دراسة الهندسة في أمريكا", "دراسة في ماليزيا", syns))


class TestSynonymsContentChecks(TestCase):
    """Verify synonyms match in title, description, H1, intro, subheadings, and image alts."""

    def test_title_match_via_synonym(self):
        # Focus keyword is 'دراسة في ماليزيا' but title contains synonym 'جامعات ماليزيا'
        engine = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="جامعات ماليزيا، التعليم في ماليزيا",
            full_page_overrides={"title": "أفضل جامعات ماليزيا المعترف بها"}
        )
        result = engine.evaluate()
        self.assertIn("focus_keyword_in_title", result["passed_checks"])
        self.assertNotIn("FOCUS_KEYWORD_MISSING_TITLE", [w["code"] for w in result["warnings"]])

    def test_description_match_via_synonym(self):
        engine = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="التعليم في ماليزيا",
            full_page_overrides={"meta_description": "كل المعلومات عن التعليم في ماليزيا وتكلفة المعيشة."}
        )
        result = engine.evaluate()
        self.assertIn("focus_keyword_in_description", result["passed_checks"])
        self.assertNotIn("FOCUS_KEYWORD_MISSING_DESCRIPTION", [w["code"] for w in result["warnings"]])

    def test_h1_match_via_synonym(self):
        engine = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="جامعات ماليزيا",
            full_page_overrides={"h1": "دليلك الشامل حول جامعات ماليزيا الممتازة"}
        )
        result = engine.evaluate()
        self.assertIn("focus_keyword_in_h1", result["passed_checks"])
        self.assertNotIn("FOCUS_KEYWORD_MISSING_H1", [w["code"] for w in result["warnings"]])

    def test_intro_match_via_synonym(self):
        # Match in intro text
        engine = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="التعليم في ماليزيا",
            main_content_overrides={"intro_text": "نقدم لكم في هذا المقال دليلاً حول التعليم في ماليزيا وشروط القبول."}
        )
        result = engine.evaluate()
        self.assertIn("focus_keyword_in_introduction", result["passed_checks"])
        self.assertNotIn("FOCUS_KEYWORD_MISSING_INTRO", [w["code"] for w in result["warnings"]])

        # Miss in intro text
        engine_miss = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="التعليم في ماليزيا",
            main_content_overrides={"intro_text": "مرحباً بكم في موقعنا."}
        )
        result_miss = engine_miss.evaluate()
        self.assertNotIn("focus_keyword_in_introduction", result_miss["passed_checks"])
        self.assertIn("FOCUS_KEYWORD_MISSING_INTRO", [w["code"] for w in result_miss["warnings"]])

    def test_subheadings_match_via_synonym(self):
        # Match in subheadings
        engine = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="جامعات ماليزيا",
            main_content_overrides={
                "headings": [
                    {"level": 2, "text": "تاريخ التعليم"},
                    {"level": 3, "text": "تكاليف جامعات ماليزيا"},
                ]
            }
        )
        result = engine.evaluate()
        self.assertIn("focus_keyword_in_subheadings", result["passed_checks"])
        self.assertNotIn("FOCUS_KEYWORD_MISSING_SUBHEADINGS", [w["code"] for w in result["warnings"]])

        # Miss in subheadings
        engine_miss = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="جامعات ماليزيا",
            main_content_overrides={
                "headings": [
                    {"level": 2, "text": "تاريخ التعليم"},
                    {"level": 3, "text": "المعيشة في كوالالمبور"},
                ]
            }
        )
        result_miss = engine_miss.evaluate()
        self.assertNotIn("focus_keyword_in_subheadings", result_miss["passed_checks"])
        self.assertIn("FOCUS_KEYWORD_MISSING_SUBHEADINGS", [w["code"] for w in result_miss["warnings"]])

    def test_image_alts_match_via_synonym(self):
        # Match in image alts
        engine = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="جامعات ماليزيا",
            main_content_overrides={"image_alts": ["صورة توضح جامعات ماليزيا"]}
        )
        result = engine.evaluate()
        self.assertIn("focus_keyword_in_alt", result["passed_checks"])
        self.assertNotIn("FOCUS_KEYWORD_MISSING_ALT", [w["code"] for w in result["warnings"]])

        # Miss in image alts
        engine_miss = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="جامعات ماليزيا",
            main_content_overrides={"image_alts": ["صورة لشخص يدرس"]}
        )
        result_miss = engine_miss.evaluate()
        self.assertNotIn("focus_keyword_in_alt", result_miss["passed_checks"])
        self.assertIn("FOCUS_KEYWORD_MISSING_ALT", [w["code"] for w in result_miss["warnings"]])


class TestSynonymsDensityCalculations(TestCase):
    """Verify that focus keyword + synonyms counts are summed to determine combined density."""

    def test_density_in_good_range(self):
        # 500 words. Focus keyword appears 1 time (0.2%). Synonym 'جامعات ماليزيا' appears 4 times (0.8%).
        # Combined count = 5 -> combined density = 1.0% (Good)
        engine = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="جامعات ماليزيا، التعليم في ماليزيا",
            main_content_overrides={
                "word_count": 500,
                "focus_keyword_count": 1,
                "synonyms_counts": {"جامعات ماليزيا": 4, "التعليم في ماليزيا": 0}
            }
        )
        result = engine.evaluate()
        self.assertIn("focus_keyword_density_good", result["passed_checks"])
        self.assertIn("focus_keyword_in_content", result["passed_checks"])
        self.assertNotIn("FOCUS_KEYWORD_DENSITY_LOW", [w["code"] for w in result["warnings"]])
        self.assertNotIn("FOCUS_KEYWORD_DENSITY_HIGH", [w["code"] for w in result["warnings"]])

    def test_density_too_low(self):
        # 500 words. Combined count = 1 -> combined density = 0.2% (Too low)
        engine = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="جامعات ماليزيا",
            main_content_overrides={
                "word_count": 500,
                "focus_keyword_count": 0,
                "synonyms_counts": {"جامعات ماليزيا": 1}
            }
        )
        result = engine.evaluate()
        self.assertNotIn("focus_keyword_density_good", result["passed_checks"])
        self.assertIn("FOCUS_KEYWORD_DENSITY_LOW", [w["code"] for w in result["warnings"]])
        # The low density message should mention counts
        low_msg = [w["message"] for w in result["warnings"] if w["code"] == "FOCUS_KEYWORD_DENSITY_LOW"][0]
        self.assertIn("1", low_msg)
        self.assertIn("500", low_msg)

    def test_density_too_high(self):
        # 200 words. Focus keyword = 4 times. Synonym = 4 times. Total = 8 -> 4.0% (Too high)
        engine = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="جامعات ماليزيا",
            main_content_overrides={
                "word_count": 200,
                "focus_keyword_count": 4,
                "synonyms_counts": {"جامعات ماليزيا": 4}
            }
        )
        result = engine.evaluate()
        self.assertNotIn("focus_keyword_density_good", result["passed_checks"])
        self.assertIn("FOCUS_KEYWORD_DENSITY_HIGH", [w["code"] for w in result["warnings"]])


class TestJSONSynonyms(TestCase):
    """Verify that synonyms stored as JSON arrays are handled correctly."""

    def test_json_array_matching(self):
        import json
        syns_json = json.dumps(["جامعات ماليزيا", "التعليم في ماليزيا"])
        engine = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms=syns_json,
            full_page_overrides={"title": "أفضل جامعات ماليزيا المعترف بها"}
        )
        result = engine.evaluate()
        self.assertIn("focus_keyword_in_title", result["passed_checks"])

    def test_json_fallback_to_comma_separated(self):
        # Plain comma-separated text (legacy/fallback)
        engine = _make_engine(
            focus_keyword="دراسة في ماليزيا",
            keyphrase_synonyms="جامعات ماليزيا، التعليم في ماليزيا",
            full_page_overrides={"title": "أفضل جامعات ماليزيا المعترف بها"}
        )
        result = engine.evaluate()
        self.assertIn("focus_keyword_in_title", result["passed_checks"])

