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

    def _get_service(self):
        """Build and cache the GSC API service object."""
        if self._service:
            return self._service

        if not self.is_connected():
            return None

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            scopes = ["https://www.googleapis.com/auth/webmasters.readonly"]
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
        """Return (start_date, end_date) strings for the last N days (GSC lags ~3 days)."""
        end = date.today() - timedelta(days=3)
        start = end - timedelta(days=days - 1)
        return start.isoformat(), end.isoformat()

    def _query(self, days: int, dimensions: list, row_limit: int = 25,
               dimension_filter: dict | None = None) -> list:
        """Execute a GSC searchAnalytics.query call."""
        service = self._get_service()
        if not service:
            return []

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
            return []

    # ───────────────────────────── Public API ─────────────────────────────

    def get_summary(self, days: int = 28) -> dict:
        """
        Return site-level totals: clicks, impressions, avg CTR, avg position.
        بيجيب إجمالي الـ clicks والـ impressions وmتوسط الـ CTR والمركز.
        """
        cache_key = f"{CACHE_PREFIX}summary_{days}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

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
        }
        cache.set(cache_key, result, CACHE_TTL)
        return result

    def get_top_pages(self, days: int = 28, limit: int = 10) -> list:
        """
        Return top pages sorted by clicks descending.
        أعلى صفحات بالـ clicks مع رابط التعديل في الداشبورد.
        """
        cache_key = f"{CACHE_PREFIX}top_pages_{days}_{limit}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        rows = self._query(days, dimensions=["page"], row_limit=limit)
        result = []
        for row in rows:
            url = row["keys"][0]
            result.append(
                {
                    "url": url,
                    "path": url.replace(self._site_url.rstrip("/"), "") or "/",
                    "clicks": int(row.get("clicks", 0)),
                    "impressions": int(row.get("impressions", 0)),
                    "ctr": round(row.get("ctr", 0) * 100, 1),
                    "position": round(row.get("position", 0), 1),
                }
            )

        cache.set(cache_key, result, CACHE_TTL)
        return result

    def get_top_queries(self, days: int = 28, limit: int = 10) -> list:
        """
        Return top search queries sorted by clicks descending.
        أعلى كلمات مفتاحية بالـ clicks.
        """
        cache_key = f"{CACHE_PREFIX}top_queries_{days}_{limit}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        rows = self._query(days, dimensions=["query"], row_limit=limit)
        result = []
        for row in rows:
            result.append(
                {
                    "query": row["keys"][0],
                    "clicks": int(row.get("clicks", 0)),
                    "impressions": int(row.get("impressions", 0)),
                    "ctr": round(row.get("ctr", 0) * 100, 1),
                    "position": round(row.get("position", 0), 1),
                }
            )

        cache.set(cache_key, result, CACHE_TTL)
        return result

    def get_quick_wins(self, days: int = 28) -> list:
        """
        Return pages ranking in positions 6–15 with decent impressions.
        ده القلب — يكشف الصفحات اللي قريبة من الـ Top 5 وتحتاج دفعة صغيرة.
        """
        cache_key = f"{CACHE_PREFIX}quick_wins_{days}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        rows = self._query(days, dimensions=["page"], row_limit=50)
        result = []
        for row in rows:
            pos = row.get("position", 0)
            impressions = int(row.get("impressions", 0))
            # مراكز 6-15 مع حد أدنى 50 ظهور عشان تكون البيانات ذات معنى
            if 6 <= pos <= 15 and impressions >= 50:
                url = row["keys"][0]
                result.append(
                    {
                        "url": url,
                        "path": url.replace(self._site_url.rstrip("/"), "") or "/",
                        "clicks": int(row.get("clicks", 0)),
                        "impressions": impressions,
                        "ctr": round(row.get("ctr", 0) * 100, 1),
                        "position": round(pos, 1),
                    }
                )

        # ترتيب: الأكثر ظهوراً أولاً (أعلى فرصة)
        result.sort(key=lambda x: x["impressions"], reverse=True)
        result = result[:10]

        cache.set(cache_key, result, CACHE_TTL)
        return result

    def get_clicks_trend(self, days: int = 28) -> list:
        """
        Return daily clicks for sparkline chart.
        بيانات يومية للـ clicks لرسم خط الاتجاه.
        """
        cache_key = f"{CACHE_PREFIX}clicks_trend_{days}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        rows = self._query(days, dimensions=["date"], row_limit=days)
        result = [
            {
                "date": row["keys"][0],
                "clicks": int(row.get("clicks", 0)),
                "impressions": int(row.get("impressions", 0)),
            }
            for row in sorted(rows, key=lambda r: r["keys"][0])
        ]

        cache.set(cache_key, result, CACHE_TTL)
        return result
