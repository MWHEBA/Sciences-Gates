import requests
from django.conf import settings

class WPImporterError(Exception):
    """Base exception class for WordPress importer."""
    pass

class WPConnectionError(WPImporterError):
    """Raised when there is a connection issue with the old site."""
    pass

class WPAuthError(WPImporterError):
    """Raised when the authorization secret key is incorrect."""
    pass

class WPNotFoundError(WPImporterError):
    """Raised when the requested slug is not found on the old site."""
    pass


class WPImporterClient:
    """Client for fetching structured content from the old WordPress site."""

    def fetch(self, slug: str) -> dict:
        base_url = getattr(settings, 'WP_IMPORTER_BASE_URL', '').strip().rstrip('/')
        secret_key = getattr(settings, 'WP_IMPORTER_SECRET_KEY', '').strip()
        timeout = getattr(settings, 'WP_IMPORTER_TIMEOUT', 30)

        if not base_url:
            raise WPConnectionError("إعدادات رابط موقع ووردبريس (WP_IMPORTER_BASE_URL) غير مكتملة.")

        url = f"{base_url}/wp-json/sg/v1/import"
        headers = {
            'Authorization': f'Bearer {secret_key}',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        params = {
            'slug': slug,
            'token': secret_key
        }

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        except requests.exceptions.ConnectionError:
            raise WPConnectionError("الموقع القديم غير متاح حالياً أو تعذر الاتصال بالسيرفر.")
        except requests.exceptions.Timeout:
            raise WPConnectionError("انتهت مهلة الاتصال بالموقع القديم.")
        except requests.exceptions.RequestException as e:
            raise WPConnectionError(f"خطأ في الاتصال بالشبكة: {str(e)}")

        if resp.status_code == 401:
            raise WPAuthError("مفتاح الاتصال غير صحيح. يرجى مراجعة إعدادات الأمان.")
        if resp.status_code == 404:
            raise WPNotFoundError("المقال غير موجود في الموقع القديم.")
        if not resp.ok:
            raise WPConnectionError(f"خطأ غير متوقع من الموقع القديم: {resp.status_code}")

        try:
            return resp.json()
        except ValueError:
            raise WPConnectionError("استقبل السيرفر استجابة غير صالحة (ليست JSON) من الموقع القديم.")
