"""
SEO views for robots.txt and dashboard analyzer endpoints.
"""
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.contenttypes.models import ContentType

from apps.seo.models import SEOAnalysisDetail
from apps.seo.services import AnalyzerError, PageSEOAnalyzer


@require_http_methods(["GET"])
def robots_txt(request):
    robots_content = """# Science Gates Platform - robots.txt
# Generated for search engine optimization

User-agent: *
Allow: /
Disallow: /admin/
Disallow: /dashboard/
Disallow: /api/
Disallow: /static/
Disallow: /media/
Disallow: /*.json$
Disallow: /?*
Disallow: /*?*

# Specific rules for search engines
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

# Crawl delay (in seconds)
Crawl-delay: 1

# Sitemap location
Sitemap: {sitemap_url}
""".format(
        sitemap_url=request.build_absolute_uri('/sitemap.xml')
    )
    return HttpResponse(robots_content, content_type='text/plain')


def _is_super_admin(request):
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and hasattr(user, "profile") and user.profile.is_super_admin)


def _json_error(code, message, status):
    return JsonResponse({"status": "error", "code": code, "message": message}, status=status)


@require_http_methods(["POST"])
def dashboard_analyze_seo(request, content_type, pk):
    if not _is_super_admin(request):
        return _json_error("UNAUTHORIZED", "غير مصرح لك بتنفيذ التحليل.", 403)

    analyzer = PageSEOAnalyzer()
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
            "seo_score": obj.seo_score,
            "seo_grade": obj.seo_grade,
            "seo_critical_count": obj.seo_critical_count,
            "seo_warning_count": obj.seo_warning_count,
            "seo_last_analysis": obj.seo_last_analysis.isoformat() if obj.seo_last_analysis else None,
        }
    )


@require_http_methods(["GET"])
def dashboard_seo_detail(request, content_type, pk):
    if not _is_super_admin(request):
        return _json_error("UNAUTHORIZED", "غير مصرح لك بعرض تفاصيل التحليل.", 403)

    analyzer = PageSEOAnalyzer()
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
