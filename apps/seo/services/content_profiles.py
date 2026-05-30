from dataclasses import dataclass, field
from typing import Any


@dataclass
class BaseSEOProfile:
    content_selector: str = "[data-seo-content]"
    min_word_count: int = 300
    min_internal_links: int = 1
    expected_schemas: tuple[str, ...] = ()
    section_checks: list[dict[str, Any]] = field(default_factory=list)


class ArticleSEOProfile(BaseSEOProfile):
    min_word_count = 500
    min_internal_links = 2
    expected_schemas = ("NewsArticle",)
    section_checks = [
        {"key": "content", "label": "محتوى المقالة", "field_names": ["content"], "min_chars": 300},
    ]


class UniversitySEOProfile(BaseSEOProfile):
    min_word_count = 600
    min_internal_links = 3
    expected_schemas = ("EducationalOrganization", "FAQPage")
    section_checks = [
        {"key": "description", "label": "وصف الجامعة", "field_names": ["description"], "min_chars": 150},
        {
            "key": "admission",
            "label": "شروط القبول",
            "field_names": [
                "admission_requirements_bachelor",
                "admission_requirements_master",
                "admission_requirements_phd",
            ],
            "min_chars": 100,
            "require_any": True,
        },
        {"key": "faculties", "label": "الكليات والبرامج", "field_names": ["faculties"], "min_chars": 0, "is_relation": True},
        {"key": "faqs", "label": "الأسئلة الشائعة", "field_names": ["faqs"], "min_chars": 0, "is_relation": True},
    ]


class InstituteSEOProfile(BaseSEOProfile):
    min_word_count = 400
    min_internal_links = 2
    expected_schemas = ("EducationalOrganization",)
    section_checks = [
        {"key": "description", "label": "وصف المعهد", "field_names": ["description"], "min_chars": 100},
        {"key": "registration", "label": "شروط التسجيل", "field_names": ["registration_requirements"], "min_chars": 80},
        {"key": "courses", "label": "الدورات", "field_names": ["courses"], "min_chars": 0, "is_relation": True},
    ]


class MajorSEOProfile(BaseSEOProfile):
    min_word_count = 300
    min_internal_links = 2
    expected_schemas = ("FAQPage",)
    section_checks = [
        {"key": "description", "label": "وصف التخصص", "field_names": ["description"], "min_chars": 100},
        {
            "key": "career",
            "label": "فرص العمل أو مجالات التخصص",
            "field_names": ["career_opportunities", "why_study_section"],
            "min_chars": 80,
            "require_any": True,
        },
    ]


def profile_for(content_type: str) -> BaseSEOProfile:
    key = content_type.strip().lower()
    mapping = {
        "article": ArticleSEOProfile(),
        "articles": ArticleSEOProfile(),
        "university": UniversitySEOProfile(),
        "universities": UniversitySEOProfile(),
        "institute": InstituteSEOProfile(),
        "institutes": InstituteSEOProfile(),
        "major": MajorSEOProfile(),
        "majors": MajorSEOProfile(),
    }
    if key not in mapping:
        raise KeyError(key)
    return mapping[key]
