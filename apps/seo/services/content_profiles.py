from dataclasses import dataclass, field
from typing import Any


@dataclass
class BaseSEOProfile:
    content_selector: str = "[data-seo-content]"
    min_word_count: int = 300
    min_internal_links: int = 1
    expected_schemas: tuple[str, ...] = ()
    section_checks: list[dict[str, Any]] = field(default_factory=list)
    eeat_requires_author_date: bool = False


@dataclass
class ArticleSEOProfile(BaseSEOProfile):
    min_word_count: int = 500
    min_internal_links: int = 2
    expected_schemas: tuple[str, ...] = ("NewsArticle",)
    section_checks: list[dict[str, Any]] = field(default_factory=lambda: [
        {"key": "content", "label": "محتوى المقالة", "field_names": ["content"], "min_chars": 300},
    ])
    eeat_requires_author_date: bool = True


@dataclass
class UniversitySEOProfile(BaseSEOProfile):
    min_word_count: int = 600
    min_internal_links: int = 3
    expected_schemas: tuple[str, ...] = ("EducationalOrganization", "FAQPage")
    section_checks: list[dict[str, Any]] = field(default_factory=lambda: [
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
    ])


@dataclass
class InstituteSEOProfile(BaseSEOProfile):
    min_word_count: int = 400
    min_internal_links: int = 2
    expected_schemas: tuple[str, ...] = ("EducationalOrganization",)
    section_checks: list[dict[str, Any]] = field(default_factory=lambda: [
        {"key": "description", "label": "وصف المعهد", "field_names": ["description"], "min_chars": 100},
        {"key": "why_choose_us", "label": "لماذا تختار المعهد", "field_names": ["why_choose_us"], "min_chars": 100},
        {"key": "courses", "label": "الدورات", "field_names": ["courses"], "min_chars": 0, "is_relation": True},
    ])


@dataclass
class MajorSEOProfile(BaseSEOProfile):
    min_word_count: int = 300
    min_internal_links: int = 2
    expected_schemas: tuple[str, ...] = ("FAQPage",)
    section_checks: list[dict[str, Any]] = field(default_factory=lambda: [
        {"key": "description", "label": "وصف التخصص", "field_names": ["description"], "min_chars": 100},
        {
            "key": "career",
            "label": "فرص العمل أو مجالات التخصص",
            "field_names": ["career_opportunities", "why_study_section"],
            "min_chars": 80,
            "require_any": True,
        },
    ])


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
