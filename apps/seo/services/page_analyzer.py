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
        synonyms_str = getattr(obj, "keyphrase_synonyms", "").strip()
        
        synonyms_list = []
        if synonyms_str:
            import json
            try:
                parsed = json.loads(synonyms_str)
                if isinstance(parsed, list):
                    synonyms_list = [s.strip() for s in parsed if s.strip()]
                elif isinstance(parsed, str):
                    synonyms_list = [s.strip() for s in parsed.replace("،", ",").split(",") if s.strip()]
            except json.JSONDecodeError:
                synonyms_list = [s.strip() for s in synonyms_str.replace("،", ",").split(",") if s.strip()]


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

            if focus_kw:
                norm_focus_kw = normalize_text(focus_kw)
                if norm_focus_kw:
                    keyword_count = len(re.findall(re.escape(norm_focus_kw), norm_clean_text))

            for syn in synonyms_list:
                norm_syn = normalize_text(syn)
                if norm_syn:
                    syn_count = len(re.findall(re.escape(norm_syn), norm_clean_text))
                    synonyms_counts[syn] = syn_count

        main_content["focus_keyword_count"] = keyword_count
        main_content["synonyms_counts"] = synonyms_counts

        model_checks = ModelAwareChecker().run(obj, profile)
        schema_results = SchemaValidator().validate(full_page.get("schemas", []), profile.expected_schemas)
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
