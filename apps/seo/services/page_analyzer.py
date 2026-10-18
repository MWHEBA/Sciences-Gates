from dataclasses import dataclass

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.urls import reverse

from apps.articles.models import Article
from apps.articles.views import ArticleDetailView
from apps.institutes.models import Institute
from apps.institutes.views import InstituteDetailView
from apps.majors.models import Major
from apps.majors.views import MajorDetailView
from apps.universities.models import University
from apps.universities.views import UniversityDetailView

from .content_profiles import profile_for
from .html_parser import SEOHTMLParser
from .model_checks import ModelAwareChecker
from .schema_validator import SchemaValidator
from .scoring import SEOScoringEngine
import re

def normalize_text(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    replacements = {
        'أ': 'ا',
        'إ': 'ا',
        'آ': 'ا',
        'ة': 'ه',
        'ى': 'ي',
    }
    for src, dest in replacements.items():
        text = text.replace(src, dest)
    diacritics = re.compile(r'[\u064b-\u0652]')
    text = diacritics.sub('', text)
    return text


def sanitize_synonyms(synonyms_raw, focus_keyword="", max_synonyms=5, max_words=7, max_length=255):
    """
    Sanitizes raw synonyms (string, JSON list, or comma-separated):
    - Parses input into a list of strings.
    - Excludes focus keyword (using normalize_text).
    - Deduplicates synonyms (using normalize_text).
    - Filters out synonyms exceeding max_words.
    - Limits total count to max_synonyms.
    - Ensures serialized JSON does not exceed max_length.
    Returns (json_str, cleaned_list).
    """
    if not synonyms_raw:
        return "", []

    import json
    synonyms_list = []
    if isinstance(synonyms_raw, list):
        synonyms_list = [str(s).strip() for s in synonyms_raw if str(s).strip()]
    elif isinstance(synonyms_raw, str):
        synonyms_raw_str = synonyms_raw.strip()
        if not synonyms_raw_str:
            return "", []
        try:
            parsed = json.loads(synonyms_raw_str)
            if isinstance(parsed, list):
                synonyms_list = [str(s).strip() for s in parsed if str(s).strip()]
            elif isinstance(parsed, str):
                synonyms_list = [s.strip() for s in parsed.replace('،', ',').split(',') if s.strip()]
        except (json.JSONDecodeError, ValueError):
            synonyms_list = [s.strip() for s in synonyms_raw_str.replace('،', ',').split(',') if s.strip()]
    else:
        return "", []

    norm_focus_kw = normalize_text(focus_keyword) if focus_keyword else ""
    cleaned_synonyms = []
    seen_norm = set()
    if norm_focus_kw:
        seen_norm.add(norm_focus_kw)

    for syn in synonyms_list:
        norm_syn = normalize_text(syn)
        if not norm_syn or norm_syn in seen_norm:
            continue
        if max_words and len(norm_syn.split()) > max_words:
            continue
        seen_norm.add(norm_syn)
        cleaned_synonyms.append(syn)
        if max_synonyms and len(cleaned_synonyms) >= max_synonyms:
            break

    if not cleaned_synonyms:
        return "", []

    json_str = json.dumps(cleaned_synonyms, ensure_ascii=False)
    if max_length and len(json_str) > max_length:
        while cleaned_synonyms and len(json.dumps(cleaned_synonyms, ensure_ascii=False)) > max_length:
            cleaned_synonyms.pop()
        json_str = json.dumps(cleaned_synonyms, ensure_ascii=False) if cleaned_synonyms else ""

    return (json_str if cleaned_synonyms else ""), cleaned_synonyms


@dataclass
class ContentConfig:
    model: type
    view_class: type
    kwargs_builder: callable


CONTENT_MAP = {
    "article": ContentConfig(Article, ArticleDetailView, lambda obj: {"slug": obj.slug}),
    "articles": ContentConfig(Article, ArticleDetailView, lambda obj: {"slug": obj.slug}),
    "university": ContentConfig(University, UniversityDetailView, lambda obj: {"slug": obj.slug}),
    "universities": ContentConfig(University, UniversityDetailView, lambda obj: {"slug": obj.slug}),
    "institute": ContentConfig(Institute, InstituteDetailView, lambda obj: {"slug": obj.slug}),
    "institutes": ContentConfig(Institute, InstituteDetailView, lambda obj: {"slug": obj.slug}),
    "major": ContentConfig(Major, MajorDetailView, lambda obj: {"slug": obj.slug}),
    "majors": ContentConfig(Major, MajorDetailView, lambda obj: {"slug": obj.slug}),
}


class AnalyzerError(Exception):
    pass


class PageSEOAnalyzer:
    def __init__(self):
        self.factory = RequestFactory()

    def get_object(self, content_type: str, pk: int):
        key = content_type.lower().strip()
        if key not in CONTENT_MAP:
            raise KeyError(key)
        model = CONTENT_MAP[key].model
        return model.objects.filter(pk=pk).first()

    def analyze(self, *, content_type: str, obj, user, host: str, secure: bool):
        key = content_type.lower().strip()
        if key not in CONTENT_MAP:
            raise KeyError(key)

        profile = profile_for(key)
        html = self._render_object_html(content_type=key, obj=obj, user=user, host=host, secure=secure)

        parser = SEOHTMLParser(html, profile.content_selector)
        full_page = parser.extract_full_page_data()
        full_page["focus_keyword"] = getattr(obj, "focus_keyword", "")
        full_page["keyphrase_synonyms"] = getattr(obj, "keyphrase_synonyms", "")
        main_content = parser.extract_main_content_data()

        # Count occurrences of focus keyword and synonyms in purified main content text
        focus_kw = getattr(obj, "focus_keyword", "").strip()
        norm_focus_kw = normalize_text(focus_kw) if focus_kw else ""
        synonyms_str = getattr(obj, "keyphrase_synonyms", "").strip()
        _, cleaned_synonyms = sanitize_synonyms(
            synonyms_str,
            focus_keyword=focus_kw,
            max_synonyms=5,
            max_words=7
        )

        keyword_count = 0
        synonyms_counts = {}

        from bs4 import BeautifulSoup
        import html as html_lib
        content_soup = BeautifulSoup(html, "html.parser")
        content_node = content_soup.select_one(profile.content_selector) or content_soup.find("body")
        if content_node:
            node_copy = BeautifulSoup(str(content_node), "html.parser")
            for tag in node_copy.find_all(["script", "style", "noscript", "svg", "template"]):
                tag.decompose()
            for tag in node_copy.find_all(attrs={"data-seo-ignore": True}):
                tag.decompose()
            clean_text = html_lib.unescape(node_copy.get_text())
            norm_clean_text = normalize_text(clean_text)

            occupied_spans = []

            def overlaps_any(start, end, spans):
                return any(max(start, s_start) < min(end, s_end) for s_start, s_end in spans)

            # 1. Match focus keyword with Arabic prefixes and word boundary suffix
            if norm_focus_kw:
                kw_pattern = re.compile(r'(?:(?<=^)|(?<=\s)|(?<=[^\w])|(?<=[وفكل]))' + re.escape(norm_focus_kw) + r'(?!\w)')
                for m in kw_pattern.finditer(norm_clean_text):
                    occupied_spans.append(m.span())
                    keyword_count += 1

            # 2. Match synonyms without overlapping already occupied keyword or prior synonym spans
            for syn in cleaned_synonyms:
                norm_syn = normalize_text(syn)
                syn_count = 0
                syn_pattern = re.compile(r'(?:(?<=^)|(?<=\s)|(?<=[^\w])|(?<=[وفكل]))' + re.escape(norm_syn) + r'(?!\w)')
                for m in syn_pattern.finditer(norm_clean_text):
                    start, end = m.span()
                    if not overlaps_any(start, end, occupied_spans):
                        occupied_spans.append((start, end))
                        syn_count += 1
                synonyms_counts[syn] = syn_count

        main_content["focus_keyword_count"] = keyword_count
        main_content["synonyms_counts"] = synonyms_counts

        # Ensure model-level alt text fields are included in image_alts
        if "image_alts" not in main_content:
            main_content["image_alts"] = []
        for alt_field in ("main_image_alt", "featured_image_alt", "logo_alt"):
            val = str(getattr(obj, alt_field, "") or "").strip()
            if val and val not in main_content["image_alts"]:
                main_content["image_alts"].append(val)

        model_checks = ModelAwareChecker().run(obj, profile)
        
        # Dynamically expect FAQPage schema if entity has associated FAQs
        expected_schemas = list(profile.expected_schemas)
        has_faqs = False
        if hasattr(obj, "faqs"):
            try:
                has_faqs = obj.faqs.exists()
            except Exception:
                has_faqs = bool(getattr(obj, "faqs", None))

        if has_faqs and "FAQPage" not in expected_schemas:
            expected_schemas.append("FAQPage")

        schema_results = SchemaValidator().validate(full_page.get("schemas", []), tuple(expected_schemas))
        score = SEOScoringEngine(full_page, main_content, model_checks, schema_results, profile).evaluate()

        report = {
            "score_summary": {
                "score": score["score"],
                "grade": score["grade"],
                "critical_count": score["critical_count"],
                "warning_count": score["warning_count"],
                "passed_count": score["passed_count"],
            },
            "critical_issues": score["critical_issues"],
            "warnings": score["warnings"],
            "passed_checks": score["passed_checks"],
            "heading_tree": [{"level": 1, "text": full_page.get("h1", "")}] + main_content.get("headings", []),
            "serp_preview": {
                "title": full_page.get("title", ""),
                "description": full_page.get("meta_description", ""),
                "url": full_page.get("canonical", ""),
            },
            "schema_status": {
                "detected_types": schema_results.get("found", []),
                "valid_json": not any(i["code"] == "INVALID_SCHEMA_JSON" for i in schema_results.get("issues", [])),
            },
            "categories": score.get("categories", {}),
            "main_content": {
                "selector_missing": main_content.get("selector_missing", False),
                "word_count": main_content.get("word_count", 0),
            },
        }
        return score, report

    def _render_object_html(self, *, content_type: str, obj, user, host: str, secure: bool):
        config = CONTENT_MAP[content_type]
        kwargs = config.kwargs_builder(obj)
        
        # Unified singular lookup
        mapping = {
            "articles": "article",
            "universities": "university",
            "institutes": "institute",
            "majors": "major",
        }
        singular = mapping.get(content_type.lower().strip(), content_type.lower().strip())
        namespace = "universities" if singular == "university" else f"{singular}s"
        url = reverse(f"{namespace}:detail", kwargs=kwargs)

        request = self.factory.get(
            f"{url}?preview=1",
            secure=secure,
            HTTP_HOST=host,
            SERVER_NAME=host,
            SERVER_PORT="443" if secure else "80",
        )
        request.user = user if user is not None else AnonymousUser()

        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        view = config.view_class.as_view()
        response = view(request, **kwargs)

        if getattr(response, "status_code", 200) >= 400:
            raise AnalyzerError(f"failed_rendering_status_{response.status_code}")

        if hasattr(response, "render"):
            response.render()

        content = response.content.decode("utf-8", errors="replace")
        # Only raise error if testserver is generated but host was NOT testserver
        if host != "testserver" and "testserver" in content:
            raise AnalyzerError("rendered_html_uses_testserver")
        return content
