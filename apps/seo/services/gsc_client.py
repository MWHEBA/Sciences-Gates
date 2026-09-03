"""
Google Search Console API Client.
يتكلم مع GSC API ويجيب البيانات مع caching لتقليل الـ requests.
"""
import json
import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 60 * 6  # 6 ساعات
CACHE_PREFIX = "gsc_"


class GSCAPIError(Exception):
    """Custom exception raised for Google Search Console API failures."""
    pass


class GSCClient:
    """
    Client for Google Search Console API.
    يتعامل مع GSC API ويوفر دوال جاهزة لأهم البيانات.
    """

    def __init__(self):
        self._service = None
        self._site_url = getattr(settings, "GSC_SITE_URL", "https://sciencesgates.com/")
        self._credentials_path = getattr(settings, "GOOGLE_SERVICE_ACCOUNT_JSON", None)

    def is_connected(self) -> bool:
        """Check if GSC credentials are configured."""
        if getattr(settings, "GSC_CREDENTIALS_DICT", None):
            return True
        if not self._credentials_path:
            return False
        try:
            import os
            return os.path.exists(self._credentials_path)
        except Exception:
            return False

    def submit_sitemap(self) -> dict:
        """Submit the sitemap.xml to Google Search Console."""
        service = self._get_service()
        if not service:
            raise GSCAPIError("GSC API Service not available. Check credentials.")

        # Domain Property parsing:
        # If the property starts with 'sc-domain:', format the feedpath as a proper HTTPS URL.
        site_url = self._site_url
        if site_url.startswith('sc-domain:'):
            domain = site_url.replace('sc-domain:', '').strip('/')
            sitemap_url = f"https://{domain}/sitemap.xml"
        else:
            base_url = site_url if site_url.endswith('/') else f"{site_url}/"
            sitemap_url = f"{base_url}sitemap.xml"

        try:
            return service.sitemaps().submit(
                siteUrl=self._site_url,
                feedpath=sitemap_url
            ).execute()
        except Exception as exc:
            logger.error("GSC: Failed to submit sitemap: %s", exc)
            raise GSCAPIError(f"فشل في إرسال خريطة الموقع لمحرك بحث جوجل: {str(exc)}")

    def _get_service(self):
        """Build and cache the GSC API service object."""
        if self._service:
            return self._service

        if not self.is_connected():
            return None

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            scopes = ["https://www.googleapis.com/auth/webmasters"]
            credentials_dict = getattr(settings, "GSC_CREDENTIALS_DICT", None)
            if credentials_dict:
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict, scopes=scopes
                )
            else:
                credentials = service_account.Credentials.from_service_account_file(
                    self._credentials_path, scopes=scopes
                )
            self._service = build("searchconsole", "v1", credentials=credentials)
            return self._service
        except Exception as exc:
            logger.warning("GSC: Failed to build service: %s", exc)
            return None

    def _date_range(self, days: int) -> tuple[str, str]:
        """Return (start_date, end_date) strings for the last N days (GSC lags ~2 days)."""
        end = date.today() - timedelta(days=2)
        start = end - timedelta(days=days - 1)
        return start.isoformat(), end.isoformat()

    def _query(self, days: int, dimensions: list, row_limit: int = 25,
               dimension_filter: getattr(__import__('typing'), 'Optional')[dict] = None) -> list:
        """Execute a GSC searchAnalytics.query call."""
        service = self._get_service()
        if not service:
            raise GSCAPIError("GSC API Service not available. Check credentials.")

        start_date, end_date = self._date_range(days)
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions,
            "rowLimit": row_limit,
        }
        if dimension_filter:
            body["dimensionFilterGroups"] = [dimension_filter]

        try:
            response = (
                service.searchanalytics()
                .query(siteUrl=self._site_url, body=body)
                .execute()
            )
            return response.get("rows", [])
        except Exception as exc:
            logger.warning("GSC query error: %s", exc)
            raise GSCAPIError(f"GSC API query failed: {exc}") from exc

    # ───────────────────────────── Public API ─────────────────────────────

    def get_summary(self, days: int = 28) -> dict:
        """
        Return site-level totals: clicks, impressions, avg CTR, avg position.
        """
        cache_key = f"{CACHE_PREFIX}summary_{days}"
        fallback_cache_key = f"{cache_key}_fallback"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            rows = self._query(days, dimensions=["date"], row_limit=200)

            total_clicks = sum(r.get("clicks", 0) for r in rows)
            total_impressions = sum(r.get("impressions", 0) for r in rows)
            total_ctr = (total_clicks / total_impressions * 100) if total_impressions else 0
            avg_position = (
                sum(r.get("position", 0) * r.get("impressions", 0) for r in rows)
                / total_impressions
                if total_impressions
                else 0
            )

            result = {
                "total_clicks": int(total_clicks),
                "total_impressions": int(total_impressions),
                "avg_ctr": round(total_ctr, 1),
                "avg_position": round(avg_position, 1),
                "days": days,
                "is_stale": False,
            }
            cache.set(cache_key, result, CACHE_TTL)
            cache.set(fallback_cache_key, result, 60 * 60 * 24 * 7)
            return result
        except Exception as exc:
            logger.warning("get_summary failed: %s. Trying fallback cache...", exc)
            fallback_data = cache.get(fallback_cache_key)
            if fallback_data is not None:
                fallback_data["is_stale"] = True
                return fallback_data
            return {
                "total_clicks": 0,
                "total_impressions": 0,
                "avg_ctr": 0.0,
                "avg_position": 0.0,
                "days": days,
                "is_stale": True,
                "error": str(exc),
            }

    def get_bracketted_pages(self, days: int = 28) -> dict:
        """
        Return pages categorized into 5 disjoint brackets based on their ranking position.
        """
        cache_key = f"{CACHE_PREFIX}bracketted_pages_{days}"
        fallback_cache_key = f"{cache_key}_fallback"

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            # 1. Query pages to get exact average positions, clicks, and impressions
            rows_page = self._query(days, dimensions=["page"], row_limit=2000)

            # 2. Query country positions for mapping
            rows_country = self._query(days, dimensions=["page", "country"], row_limit=10000)
            country_positions = {}
            for r in rows_country:
                keys = r.get("keys", [])
                if len(keys) < 2:
                    continue
                url = keys[0]
                country = keys[1].upper()
                country_positions[(url, country)] = float(r.get("position", 0))

            # 3. Query top queries per page
            rows_query = self._query(days, dimensions=["page", "query"], row_limit=10000)
            page_top_queries = {}
            for row in rows_query:
                keys = row.get("keys", [])
                if len(keys) < 2:
                    continue
                url = keys[0]
                query = keys[1]
                if url not in page_top_queries:
                    page_top_queries[url] = query

            result = {
                "winners": [],
                "quick_wins": [],
                "growth": [],
                "low_visibility": [],
                "weak": [],
                "broken": [],
                "is_stale": False,
            }

            for r in rows_page:
                url = r["keys"][0]
                clicks = int(r.get("clicks", 0))
                impressions = int(r.get("impressions", 0))
                position = float(r.get("position", 0))
                ctr = round(r.get("ctr", 0) * 100, 1)

                clean_site = self._site_url.replace("sc-domain:", "")
                if not clean_site.startswith("http"):
                    clean_site = "https://" + clean_site
                path = url.replace(clean_site.rstrip("/"), "") or "/"
                
                info = resolve_path_info(path, self._site_url)

                sau_pos = country_positions.get((url, "SAU"), None)
                egy_pos = country_positions.get((url, "EGY"), None)
                top_query = page_top_queries.get(url, None)

                page_data = {
                    "url": url,
                    "path": path,
                    "title": info["title"],
                    "type": info["type"],
                    "type_label": info["type_label"],
                    "clicks": clicks,
                    "impressions": impressions,
                    "ctr": ctr,
                    "position": round(position, 1),
                    "sau_position": round(sau_pos, 1) if sau_pos is not None else None,
                    "egy_position": round(egy_pos, 1) if egy_pos is not None else None,
                    "top_query": top_query,
                }

                # Check for dynamic 404 pages (cross-referencing with Django models) in-memory
                # If path starts with any of the content detail prefixes but resolved to type 'page',
                # it means the database object is missing (deleted or unpublished).
                is_content_prefix = any(path.startswith(pref) for pref in ['/articles/', '/universities/', '/institutes/', '/majors/'])
                if is_content_prefix and info['type'] == 'page':
                    page_data["type_label"] = "جوجل كونسول ⚠️"
                    page_data["is_gsc_error"] = True
                    result["broken"].append(page_data)
                    continue

                # Decision Tree classification (disjoint brackets)
                if clicks == 0 and impressions < 15:
                    result["weak"].append(page_data)
                elif position <= 5.0:
                    result["winners"].append(page_data)
                elif 5.0 < position <= 15.0:
                    result["quick_wins"].append(page_data)
                elif 15.0 < position <= 30.0:
                    result["growth"].append(page_data)
                else:
                    result["low_visibility"].append(page_data)

            # Sort brackets by clicks descending, then impressions descending (except weak which sorts by impressions descending)
            for key in ["winners", "quick_wins", "growth", "low_visibility", "broken"]:
                result[key].sort(key=lambda x: (x["clicks"], x["impressions"]), reverse=True)
            result["weak"].sort(key=lambda x: x["impressions"], reverse=True)

            # Keep only the top 15 pages in performance categories (and top 50 for broken 404s) to avoid bloating HTML
            for key in ["winners", "quick_wins", "growth", "low_visibility", "weak"]:
                result[key] = result[key][:15]
            result["broken"] = result["broken"][:50]

            cache.set(cache_key, result, CACHE_TTL)
            cache.set(fallback_cache_key, result, 60 * 60 * 24 * 7)
            return result
        except Exception as exc:
            logger.warning("get_bracketted_pages failed: %s. Trying fallback cache...", exc)
            fallback_data = cache.get(fallback_cache_key)
            if fallback_data is not None:
                fallback_data["is_stale"] = True
                return fallback_data
            return {
                "winners": [],
                "quick_wins": [],
                "growth": [],
                "low_visibility": [],
                "weak": [],
                "broken": [],
                "is_stale": True,
                "error": str(exc),
            }

    def get_top_queries(self, days: int = 28, limit: int = 10) -> dict:
        """
        Return top search queries sorted by clicks descending.
        أعلى كلمات مفتاحية بالـ clicks.
        """
        cache_key = f"{CACHE_PREFIX}top_queries_{days}_{limit}"
        fallback_cache_key = f"{cache_key}_fallback"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            rows = self._query(days, dimensions=["query"], row_limit=limit)
            result_list = []
            for row in rows:
                result_list.append(
                    {
                        "query": row["keys"][0],
                        "clicks": int(row.get("clicks", 0)),
                        "impressions": int(row.get("impressions", 0)),
                        "ctr": round(row.get("ctr", 0) * 100, 1),
                        "position": round(row.get("position", 0), 1),
                    }
                )
            result = {
                "queries": result_list,
                "is_stale": False,
            }
            cache.set(cache_key, result, CACHE_TTL)
            cache.set(fallback_cache_key, result, 60 * 60 * 24 * 7)
            return result
        except Exception as exc:
            logger.warning("get_top_queries failed: %s. Trying fallback cache...", exc)
            fallback_data = cache.get(fallback_cache_key)
            if fallback_data is not None:
                fallback_data["is_stale"] = True
                return fallback_data
            return {
                "queries": [],
                "is_stale": True,
                "error": str(exc),
            }

    def get_cannibalized_keywords(self, days: int = 28) -> dict:
        """
        Identify keyword cannibalization where multiple pages compete for the same query.
        """
        cache_key = f"{CACHE_PREFIX}cannibalized_keywords_{days}"
        fallback_cache_key = f"{cache_key}_fallback"

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            # Query query + page (GSC returns them sorted by clicks/impressions descending)
            rows = self._query(days, dimensions=["query", "page"], row_limit=10000)

            query_pages = {}
            for r in rows:
                keys = r.get("keys", [])
                if len(keys) < 2:
                    continue
                query = keys[0]
                url = keys[1]
                clicks = int(r.get("clicks", 0))
                impressions = int(r.get("impressions", 0))
                position = float(r.get("position", 0))

                if query not in query_pages:
                    query_pages[query] = []
                query_pages[query].append({
                    "url": url,
                    "clicks": clicks,
                    "impressions": impressions,
                    "position": round(position, 1)
                })

            cannibalized = []
            for query, pages in query_pages.items():
                if len(pages) > 1:
                    # Clean site URL for display paths
                    clean_site = self._site_url.replace("sc-domain:", "")
                    if not clean_site.startswith("http"):
                        clean_site = "https://" + clean_site

                    # Apply smart threshold:
                    # 1. Total impressions for query >= 20
                    total_impressions = sum(p["impressions"] for p in pages)
                    total_clicks = sum(p["clicks"] for p in pages)
                    
                    if total_impressions < 20:
                        continue

                    # 2. At least two competing pages must have impressions >= 5
                    valid_pages = []
                    for p in pages:
                        if p["impressions"] >= 5:
                            p["path"] = p["url"].replace(clean_site.rstrip("/"), "") or "/"
                            p["title"] = resolve_path_info(p["path"], self._site_url)["title"]
                            valid_pages.append(p)
                    
                    if len(valid_pages) < 2:
                        continue

                    # Sort pages by clicks descending, then impressions descending
                    valid_pages.sort(key=lambda x: (x["clicks"], x["impressions"]), reverse=True)

                    cannibalized.append({
                        "query": query,
                        "total_clicks": total_clicks,
                        "total_impressions": total_impressions,
                        "pages": valid_pages
                    })

            # Sort by total impressions descending (most critical keyword issues first)
            cannibalized.sort(key=lambda x: x["total_impressions"], reverse=True)
            
            result = {
                "keywords": cannibalized[:20],  # limit to top 20 issues
                "is_stale": False,
            }
            cache.set(cache_key, result, CACHE_TTL)
            cache.set(fallback_cache_key, result, 60 * 60 * 24 * 7)
            return result
        except Exception as exc:
            logger.warning("get_cannibalized_keywords failed: %s. Trying fallback cache...", exc)
            fallback_data = cache.get(fallback_cache_key)
            if fallback_data is not None:
                fallback_data["is_stale"] = True
                return fallback_data
            return {
                "keywords": [],
                "is_stale": True,
                "error": str(exc),
            }

    def get_clicks_trend(self, days: int = 28) -> dict:
        """
        Return daily clicks for sparkline chart.
        بيانات يومية للـ clicks لرسم خط الاتجاه.
        """
        cache_key = f"{CACHE_PREFIX}clicks_trend_{days}"
        fallback_cache_key = f"{cache_key}_fallback"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            rows = self._query(days, dimensions=["date"], row_limit=days)
            result_list = [
                {
                    "date": row["keys"][0],
                    "clicks": int(row.get("clicks", 0)),
                    "impressions": int(row.get("impressions", 0)),
                }
                for row in sorted(rows, key=lambda r: r["keys"][0])
            ]
            result = {
                "trend": result_list,
                "is_stale": False,
            }
            cache.set(cache_key, result, CACHE_TTL)
            cache.set(fallback_cache_key, result, 60 * 60 * 24 * 7)
            return result
        except Exception as exc:
            logger.warning("get_clicks_trend failed: %s. Trying fallback cache...", exc)
            fallback_data = cache.get(fallback_cache_key)
            if fallback_data is not None:
                fallback_data["is_stale"] = True
                return fallback_data
            return {
                "trend": [],
                "is_stale": True,
                "error": str(exc),
            }


def resolve_path_info(path, site_url=None):
    """
    Resolves a URL path to its corresponding title/name and type label.
    Returns a dict with {'title': ..., 'type': ..., 'type_label': ...}.
    """
    import urllib.parse
    from django.urls import resolve, Resolver404

    info = {
        'title': path,
        'type': 'page',
        'type_label': 'صفحة'
    }

    try:
        path = urllib.parse.unquote(path)
        if site_url:
            clean_site_url = site_url.replace("sc-domain:", "")
            if not clean_site_url.startswith("http"):
                clean_site_url = "https://" + clean_site_url
            path = path.replace(clean_site_url.rstrip("/"), "")

        if not path.startswith('/'):
            path = '/' + path

        # Remove query parameters if any
        if '?' in path:
            path = path.split('?')[0]

        parts = [p for p in path.strip('/').split('/') if p]
        fallback_title = parts[-1] if parts else "الرئيسية"
        if fallback_title:
            clean_fallback = fallback_title.replace('-', ' ').strip()
            if clean_fallback:
                info['title'] = clean_fallback

        resolved = None
        for test_path in (path, path + '/'):
            if resolved:
                break
            try:
                resolved = resolve(test_path)
            except Resolver404:
                continue
            except Exception:
                break

        if resolved:
            url_name = resolved.url_name
            namespaces = resolved.namespaces
            kwargs = resolved.kwargs
            full_name = f"{namespaces[0]}:{url_name}" if namespaces else url_name

            static_titles = {
                'home': ('الرئيسية', 'page', 'صفحة'),
                'about_us': ('من نحن', 'page', 'صفحة'),
                'visa_tracking': ('تتبع التأشيرة', 'page', 'صفحة'),
                'articles:list': ('المقالات', 'list', 'قائمة'),
                'universities:list': ('الجامعات', 'list', 'قائمة'),
                'institutes:list': ('المعاهد', 'list', 'قائمة'),
                'majors:list': ('التخصصات', 'list', 'قائمة'),
            }
            if full_name in static_titles:
                t, tp, tl = static_titles[full_name]
                info['title'] = t
                info['type'] = tp
                info['type_label'] = tl
                return info

            # Category or Tag views
            category_slug = kwargs.get('category') or kwargs.get('slug')
            if full_name == 'majors:category_list' and category_slug:
                from apps.majors.models import MajorCategory
                name = MajorCategory.objects.filter(slug=category_slug).values_list('name', flat=True).first()
                if name:
                    info['title'] = name
                    info['type'] = 'category'
                    info['type_label'] = 'تصنيف تخصصات'
                    return info

            if full_name == 'articles:category' and category_slug:
                from apps.articles.models import Category
                name = Category.objects.filter(slug=category_slug).values_list('name', flat=True).first()
                if name:
                    info['title'] = name
                    info['type'] = 'category'
                    info['type_label'] = 'تصنيف مقالات'
                    return info

            if full_name == 'articles:tag' and category_slug:
                from apps.articles.models import Tag
                name = Tag.objects.filter(slug=category_slug).values_list('name', flat=True).first()
                if name:
                    info['title'] = name
                    info['type'] = 'tag'
                    info['type_label'] = 'وسم'
                    return info

            type_val = kwargs.get('type')
            if full_name == 'universities:type_list' and type_val:
                type_titles = {
                    'public': 'الجامعات الحكومية',
                    'private': 'الجامعات الخاصة',
                }
                info['title'] = type_titles.get(type_val, type_val)
                info['type'] = 'list'
                info['type_label'] = 'قائمة'
                return info

            slug = kwargs.get('slug')
            if slug:
                from apps.articles.models import Article
                from apps.universities.models import University
                from apps.institutes.models import Institute
                from apps.majors.models import Major

                if full_name == 'articles:detail':
                    title = Article.objects.filter(slug=slug).values_list('title', flat=True).first()
                    if title:
                        info['title'] = title
                        info['type'] = 'article'
                        info['type_label'] = 'مقال'
                        return info
                elif full_name == 'universities:detail':
                    name = University.objects.filter(slug=slug).values_list('name', flat=True).first()
                    if name:
                        info['title'] = name
                        info['type'] = 'university'
                        info['type_label'] = 'جامعة'
                        return info
                elif full_name == 'institutes:detail':
                    name = Institute.objects.filter(slug=slug).values_list('name', flat=True).first()
                    if name:
                        info['title'] = name
                        info['type'] = 'institute'
                        info['type_label'] = 'معهد'
                        return info
                elif full_name == 'majors:detail':
                    name = Major.objects.filter(slug=slug).values_list('name', flat=True).first()
                    if name:
                        info['title'] = name
                        info['type'] = 'major'
                        info['type_label'] = 'تخصص'
                        return info
                elif full_name == 'legacy_detail':
                    name = University.objects.filter(slug=slug).values_list('name', flat=True).first()
                    if name:
                        info['title'] = name
                        info['type'] = 'university'
                        info['type_label'] = 'جامعة'
                        return info
                    name = Institute.objects.filter(slug=slug).values_list('name', flat=True).first()
                    if name:
                        info['title'] = name
                        info['type'] = 'institute'
                        info['type_label'] = 'معهد'
                        return info
                    name = Major.objects.filter(slug=slug).values_list('name', flat=True).first()
                    if name:
                        info['title'] = name
                        info['type'] = 'major'
                        info['type_label'] = 'تخصص'
                        return info
                    title = Article.objects.filter(slug=slug).values_list('title', flat=True).first()
                    if title:
                        info['title'] = title
                        info['type'] = 'article'
                        info['type_label'] = 'مقال'
                        return info
    except Exception as e:
        logger.warning("Error resolving path info for %s: %s", path, e)

    if info['type'] == 'page' and fallback_title:
        slug = fallback_title
        try:
            from apps.articles.models import Article
            from apps.universities.models import University
            from apps.institutes.models import Institute
            from apps.majors.models import Major

            def normalize_slug(s):
                if not s:
                    return ""
                s = s.replace('-', '')
                s = s.replace('ة', 'ه').replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ى', 'ي')
                return s.strip().lower()

            normalized_target = normalize_slug(slug)
            if normalized_target:
                for name, db_slug in University.objects.values_list('name', 'slug'):
                    norm = normalize_slug(db_slug)
                    if normalized_target in norm or norm in normalized_target:
                        info['title'] = name
                        info['type'] = 'university'
                        info['type_label'] = 'جامعة'
                        return info

                for name, db_slug in Institute.objects.values_list('name', 'slug'):
                    norm = normalize_slug(db_slug)
                    if normalized_target in norm or norm in normalized_target:
                        info['title'] = name
                        info['type'] = 'institute'
                        info['type_label'] = 'معهد'
                        return info

                for name, db_slug in Major.objects.values_list('name', 'slug'):
                    norm = normalize_slug(db_slug)
                    if normalized_target in norm or norm in normalized_target:
                        info['title'] = name
                        info['type'] = 'major'
                        info['type_label'] = 'تخصص'
                        return info

                for title, db_slug in Article.objects.values_list('title', 'slug'):
                    norm = normalize_slug(db_slug)
                    if normalized_target in norm or norm in normalized_target:
                        info['title'] = title
                        info['type'] = 'article'
                        info['type_label'] = 'مقال'
                        return info
        except Exception as e:
            logger.warning("Error in fuzzy resolution for slug %s: %s", slug, e)

    return info


def get_title_for_path(path, site_url=None):
    """
    Resolves a URL path to a corresponding model title/name.
    """
    return resolve_path_info(path, site_url)['title']
