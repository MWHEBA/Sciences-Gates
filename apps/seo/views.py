"""
SEO views for robots.txt and dashboard analyzer endpoints.
"""
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.contenttypes.models import ContentType
from django.views.static import serve
from django.conf import settings
import os

from apps.seo.models import SEOAnalysisDetail
from apps.seo.services import AnalyzerError, PageSEOAnalyzer


@require_http_methods(["GET"])
def robots_txt(request):
    """
    Serve robots.txt file dynamically to ensure admin and dashboard URLs
    reflect any changes in settings.ADMIN_URL and settings.DASHBOARD_URL.
    """
    admin_url = settings.ADMIN_URL.strip('/')
    dashboard_url = settings.DASHBOARD_URL.strip('/')
    
    robots_content = """# robots.txt for Science Gates - Study in Malaysia
# Generated dynamically for Search Engine Optimization

User-agent: *
Allow: /
Disallow: /{admin_url}/
Disallow: /{dashboard_url}/
Disallow: /api/
Disallow: /*.json$
Disallow: /*?*page=
Disallow: /*&

# Crawl delay and disallow rules for main search engines
User-agent: Googlebot
Allow: /
Disallow: /{admin_url}/
Disallow: /{dashboard_url}/
Disallow: /api/
Disallow: /*.json$
Disallow: /*?*page=
Disallow: /*&
Crawl-delay: 1

User-agent: Bingbot
Allow: /
Crawl-delay: 1

# Block AI crawlers from scraping content
User-agent: GPTBot
Disallow: /

User-agent: ChatGPT-User
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: anthropic-ai
Disallow: /

User-agent: Claude-Web
Disallow: /

# Sitemap
Sitemap: {sitemap_url}
""".format(
        admin_url=admin_url,
        dashboard_url=dashboard_url,
        sitemap_url=request.build_absolute_uri('/sitemap.xml')
    )
    return HttpResponse(robots_content, content_type='text/plain')


from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import resolve, reverse


class PreviewPageSEOAnalyzer(PageSEOAnalyzer):
    def __init__(self, is_preview_mode=False):
        super().__init__()
        self.is_preview_mode = is_preview_mode

    def _render_object_html(self, *, content_type: str, obj, user, host: str, secure: bool):
        if not self.is_preview_mode:
            return super()._render_object_html(
                content_type=content_type, obj=obj, user=user, host=host, secure=secure
            )

        # Unified singular mapping
        mapping = {
            "articles": "article",
            "universities": "university",
            "institutes": "institute",
            "majors": "major",
        }
        key = mapping.get(content_type.lower().strip(), content_type.lower().strip())
        if key.endswith("s") and key != "universities":
            key = key[:-1]

        url = reverse(f"dashboard:preview_{key}", kwargs={"pk": obj.pk})

        request = self.factory.get(
            url,
            secure=secure,
            HTTP_HOST=host,
            SERVER_NAME=host,
            SERVER_PORT="443" if secure else "80",
        )
        request.user = user if user is not None else AnonymousUser()

        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        # Resolve preview view dynamically to avoid circular import dependency
        match = resolve(url)
        response = match.func(request, **match.kwargs)

        if getattr(response, "status_code", 200) >= 400:
            raise AnalyzerError(f"failed_rendering_status_{response.status_code}")

        if hasattr(response, "render"):
            response.render()

        content = response.content.decode("utf-8", errors="replace")
        # Only raise error if testserver is generated but host was NOT testserver
        if host != "testserver" and "testserver" in content:
            raise AnalyzerError("rendered_html_uses_testserver")
        return content


def _is_authorized_analyzer(request):
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated and hasattr(user, "profile")):
        return False
    profile = user.profile
    return bool(profile.is_content_admin or profile.is_super_admin)


def _json_error(code, message, status):
    return JsonResponse({"status": "error", "code": code, "message": message}, status=status)


@require_http_methods(["POST"])
def dashboard_analyze_seo(request, content_type, pk):
    if not _is_authorized_analyzer(request):
        return _json_error("UNAUTHORIZED", "غير مصرح لك بتنفيذ التحليل.", 403)

    is_preview_mode = request.GET.get("preview") == "1"
    analyzer = PreviewPageSEOAnalyzer(is_preview_mode=is_preview_mode)
    try:
        obj = analyzer.get_object(content_type, pk)
    except KeyError:
        return _json_error("INVALID_CONTENT_TYPE", "نوع المحتوى غير صالح.", 400)

    if obj is None:
        return _json_error("OBJECT_NOT_FOUND", "العنصر المطلوب غير موجود.", 404)

    try:
        score, report = analyzer.analyze(
            content_type=content_type,
            obj=obj,
            user=request.user,
            host=request.get_host(),
            secure=request.is_secure(),
        )
    except AnalyzerError as exc:
        if str(exc) == "rendered_html_uses_testserver":
            return _json_error("FAILED_DRAFT_RENDERING", "فشل توليد الصفحة بمعاملات host/protocol الصحيحة.", 500)
        return _json_error("FAILED_DRAFT_RENDERING", "فشل توليد صفحة المعاينة للمسودة.", 500)

    if report.get("main_content", {}).get("selector_missing"):
        return _json_error("MISSING_CONTENT_SELECTOR", "لم يتم العثور على [data-seo-content] في الصفحة.", 422)

    if is_preview_mode:
        return JsonResponse(
            {
                "status": "success",
                "source": "preview",
                "seo_score": score["score"],
                "seo_grade": score["grade"],
                "seo_critical_count": score["critical_count"],
                "seo_warning_count": score["warning_count"],
                "seo_last_analysis": timezone.now().isoformat(),
                "report": report,
            }
        )

    obj.seo_score = score["score"]
    obj.seo_grade = score["grade"]
    obj.seo_critical_count = score["critical_count"]
    obj.seo_warning_count = score["warning_count"]
    obj.seo_last_analysis = timezone.now()
    obj.save(update_fields=["seo_score", "seo_grade", "seo_critical_count", "seo_warning_count", "seo_last_analysis"])

    ct = ContentType.objects.get_for_model(obj.__class__)
    detail_obj, _ = SEOAnalysisDetail.objects.get_or_create(content_type=ct, object_id=obj.pk)
    detail_obj.analysis_report_json = report
    detail_obj.save(update_fields=["analysis_report_json", "updated_at"])

    return JsonResponse(
        {
            "status": "success",
            "source": "published",
            "seo_score": obj.seo_score,
            "seo_grade": obj.seo_grade,
            "seo_critical_count": obj.seo_critical_count,
            "seo_warning_count": obj.seo_warning_count,
            "seo_last_analysis": obj.seo_last_analysis.isoformat() if obj.seo_last_analysis else None,
        }
    )


@require_http_methods(["GET"])
def dashboard_seo_detail(request, content_type, pk):
    if not _is_authorized_analyzer(request):
        return _json_error("UNAUTHORIZED", "غير مصرح لك بعرض تفاصيل التحليل.", 403)

    analyzer = PreviewPageSEOAnalyzer()
    try:
        obj = analyzer.get_object(content_type, pk)
    except KeyError:
        return _json_error("INVALID_CONTENT_TYPE", "نوع المحتوى غير صالح.", 400)

    if obj is None:
        return _json_error("OBJECT_NOT_FOUND", "العنصر المطلوب غير موجود.", 404)

    detail_obj = SEOAnalysisDetail.objects.filter(
        content_type__app_label=obj._meta.app_label,
        content_type__model=obj._meta.model_name,
        object_id=obj.pk,
    ).first()

    if not detail_obj:
        return _json_error("ANALYSIS_NOT_FOUND", "لا توجد تفاصيل تحليل محفوظة لهذا العنصر.", 404)

    report = detail_obj.analysis_report_json or {}
    payload = {
        "status": "success",
        "score_summary": report.get("score_summary", {}),
        "critical_issues": report.get("critical_issues", []),
        "warnings": report.get("warnings", []),
        "heading_tree": report.get("heading_tree", []),
        "serp_preview": report.get("serp_preview", {}),
        "schema_status": report.get("schema_status", {}),
        "categories": report.get("categories", {}),
    }
    return JsonResponse(payload)
