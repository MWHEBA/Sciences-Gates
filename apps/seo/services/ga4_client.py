"""
Google Analytics 4 Data API Client.
يتصل بـ Google Analytics 4 Data API لجلب التقارير وإحصائيات الزوار.
"""
import logging
from datetime import datetime, date, timedelta
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class GA4APIError(Exception):
    """Exception class for Google Analytics API failures."""
    pass

class GA4Client:
    """
    Client for Google Analytics 4 Data API.
    """
    def __init__(self):
        self._service = None
        # Get Property ID from SiteSettings (will be loaded at query time or passed in)
        self._property_id = None
        self._credentials_dict = getattr(settings, "GSC_CREDENTIALS_DICT", None)

    def _handle_api_error(self, exc) -> str:
        """Parse raw Google API exceptions and return a user-friendly Arabic error message."""
        error_msg = str(exc)
        
        # Check if it is a googleapiclient HttpError
        from googleapiclient.errors import HttpError
        if isinstance(exc, HttpError):
            try:
                import json
                content = json.loads(exc.content.decode('utf-8'))
                g_error = content.get('error', {})
                message = g_error.get('message', '')
                status = g_error.get('status', '')
                
                # Dynamic project id
                project_id = self._credentials_dict.get('project_id', '') if self._credentials_dict else ''
                
                # Check for specific known issues
                if 'SERVICE_DISABLED' in error_msg or 'has not been used' in message:
                    link = f"https://console.developers.google.com/apis/api/analyticsdata.googleapis.com/overview?project={project_id}" if project_id else "https://console.developers.google.com/"
                    return (
                        "يجب تفعيل Google Analytics Data API في حساب Google Cloud الخاص بك أولاً. "
                        f"يرجى الضغط على الرابط التالي لتفعيلها: {link}"
                    )
                
                if status == 'PERMISSION_DENIED' or 'does not have' in message.lower() or 'permission' in message.lower():
                    return (
                        "حساب الخدمة (Service Account) لا يملك صلاحية للوصول إلى هذه الخاصية. "
                        "يرجى التأكد من إضافة البريد الخاص بحساب الخدمة كـ Viewer (مُشاهد) في إعدادات Google Analytics الخاص بك."
                    )
                
                if message:
                    return f"خطأ من Google Analytics: {message}"
            except Exception:
                pass
                
        # Fallback for connection/other errors
        if "invalid_grant" in error_msg or "credential" in error_msg.lower():
            return "خطأ في مصادقة بيانات الاعتماد. يرجى التحقق من صحة ملف credentials الخاص بالـ Service Account."
            
        if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            return "فشل الاتصال بخوادم Google Analytics بسبب مشكلة في الشبكة. يرجى المحاولة مرة أخرى لاحقاً."

        return f"فشل الاتصال بـ Google API: {error_msg}"

    def is_configured(self) -> bool:
        """Check if service account credentials are set in environment."""
        return bool(self._credentials_dict)

    def _get_service(self):
        """Build and cache the GA4 Data API service."""
        if self._service:
            return self._service

        if not self._credentials_dict:
            raise GA4APIError("لم يتم العثور على إعدادات Service Account (GOOGLE_SERVICE_ACCOUNT_JSON_STRING).")

        try:
            creds = service_account.Credentials.from_service_account_info(
                self._credentials_dict,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
            self._service = build("analyticsdata", "v1beta", credentials=creds)
            return self._service
        except Exception as exc:
            logger.error("Failed to build GA4 Service: %s", exc)
            raise GA4APIError(f"خطأ أثناء الاتصال بـ Google API: {str(exc)}")

    def _get_start_date(self, days: int) -> str:
        """Get date string for N days ago."""
        dt = date.today() - timedelta(days=days)
        return dt.strftime("%Y-%m-%d")

    def get_realtime_active_users(self, property_id: str) -> int:
        """
        Fetch active users in the last 30 minutes.
        """
        if not property_id:
            raise GA4APIError("Property ID غير معرّف.")
            
        service = self._get_service()
        body = {
            "metrics": [{"name": "activeUsers"}]
        }
        try:
            response = service.properties().runRealtimeReport(
                property=f"properties/{property_id}",
                body=body
            ).execute()
            
            # Parse response
            rows = response.get("rows", [])
            if rows:
                val = rows[0].get("metricValues", [{}])[0].get("value", "0")
                return int(val)
            return 0
        except Exception as exc:
            logger.error("get_realtime_active_users failed: %s", exc)
            raise GA4APIError(self._handle_api_error(exc))

    def fetch_all_reports(self, property_id: str, days: int) -> dict:
        """
        Fetch historical reports in 2 batches for maximum performance and quota safety.
        """
        if not property_id:
            raise GA4APIError("Property ID غير معرّف.")

        service = self._get_service()
        start_date_str = self._get_start_date(days)
        
        # Batch 1: Primary analytics reports (Summary, Daily Trend, Top Pages, Traffic Sources, Countries)
        batch_body_1 = {
            "requests": [
                # 0. Summary
                {
                    "dateRanges": [{"startDate": start_date_str, "endDate": "today"}],
                    "metrics": [
                        {"name": "activeUsers"},
                        {"name": "newUsers"},
                        {"name": "sessions"},
                        {"name": "averageSessionDuration"}
                    ]
                },
                # 1. Daily Trend
                {
                    "dateRanges": [{"startDate": start_date_str, "endDate": "today"}],
                    "dimensions": [{"name": "date"}],
                    "metrics": [
                        {"name": "activeUsers"},
                        {"name": "sessions"}
                    ],
                    "orderBys": [{"dimension": {"dimensionName": "date"}, "desc": False}]
                },
                # 2. Top Pages
                {
                    "dateRanges": [{"startDate": start_date_str, "endDate": "today"}],
                    "dimensions": [{"name": "pagePath"}, {"name": "pageTitle"}],
                    "metrics": [
                        {"name": "activeUsers"},
                        {"name": "screenPageViews"},
                        {"name": "sessions"},
                        {"name": "userEngagementDuration"}
                    ],
                    "limit": 15
                },
                # 3. Traffic Sources
                {
                    "dateRanges": [{"startDate": start_date_str, "endDate": "today"}],
                    "dimensions": [{"name": "sessionSourceMedium"}],
                    "metrics": [
                        {"name": "activeUsers"},
                        {"name": "sessions"}
                    ],
                    "limit": 10
                },
                # 4. Countries
                {
                    "dateRanges": [{"startDate": start_date_str, "endDate": "today"}],
                    "dimensions": [{"name": "country"}],
                    "metrics": [
                        {"name": "activeUsers"},
                        {"name": "sessions"}
                    ],
                    "limit": 10
                }
            ]
        }

        # Batch 2: Tech specs & events (Devices, Browsers, Operating Systems, Events/Conversions)
        batch_body_2 = {
            "requests": [
                # 0. Devices
                {
                    "dateRanges": [{"startDate": start_date_str, "endDate": "today"}],
                    "dimensions": [{"name": "deviceCategory"}],
                    "metrics": [{"name": "activeUsers"}],
                    "limit": 5
                },
                # 1. Browsers
                {
                    "dateRanges": [{"startDate": start_date_str, "endDate": "today"}],
                    "dimensions": [{"name": "browser"}],
                    "metrics": [{"name": "activeUsers"}],
                    "limit": 5
                },
                # 2. Operating Systems
                {
                    "dateRanges": [{"startDate": start_date_str, "endDate": "today"}],
                    "dimensions": [{"name": "operatingSystem"}],
                    "metrics": [{"name": "activeUsers"}],
                    "limit": 5
                },
                # 3. Events & Conversions
                {
                    "dateRanges": [{"startDate": start_date_str, "endDate": "today"}],
                    "dimensions": [{"name": "eventName"}],
                    "metrics": [
                        {"name": "eventCount"},
                        {"name": "conversions"}
                    ],
                    "limit": 10
                }
            ]
        }

        try:
            # 1. Execute Batch 1
            batch_resp_1 = service.properties().batchRunReports(
                property=f"properties/{property_id}",
                body=batch_body_1
            ).execute()

            # 2. Execute Batch 2
            batch_resp_2 = service.properties().batchRunReports(
                property=f"properties/{property_id}",
                body=batch_body_2
            ).execute()

            reports_1 = batch_resp_1.get("reports", [])
            reports_2 = batch_resp_2.get("reports", [])
            if len(reports_1) < 5 or len(reports_2) < 4:
                raise GA4APIError("لم ترجع خوادم Google العدد المتوقع من التقارير.")

            # Parse reports
            summary = self._parse_summary(reports_1[0])
            daily_trend = self._parse_daily_trend(reports_1[1], days)
            top_pages = self._parse_top_pages(reports_1[2])
            traffic_sources = self._parse_traffic_sources(reports_1[3])
            countries = self._parse_countries(reports_1[4])
            
            devices = self._parse_devices(reports_2[0])
            browsers = self._parse_browsers(reports_2[1])
            operating_systems = self._parse_os(reports_2[2])
            events = self._parse_events(reports_2[3])

            return {
                "summary": summary,
                "daily_trend": daily_trend,
                "top_pages": top_pages,
                "traffic_sources": traffic_sources,
                "countries": countries,
                "devices": devices,
                "browsers": browsers,
                "operating_systems": operating_systems,
                "events": events
            }
        except Exception as exc:
            logger.error("fetch_all_reports failed: %s", exc)
            raise GA4APIError(self._handle_api_error(exc))

    def _parse_summary(self, report) -> dict:
        """Parse summary metrics row."""
        rows = report.get("rows", [])
        if not rows:
            return {"active_users": 0, "new_users": 0, "sessions": 0, "avg_session_duration": "0:00"}
        
        vals = rows[0].get("metricValues", [])
        active_users = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
        new_users = int(vals[1].get("value", 0)) if len(vals) > 1 else 0
        sessions = int(vals[2].get("value", 0)) if len(vals) > 2 else 0
        
        avg_dur_sec = float(vals[3].get("value", 0)) if len(vals) > 3 else 0
        minutes = int(avg_dur_sec // 60)
        seconds = int(avg_dur_sec % 60)
        avg_session_duration = f"{minutes}:{seconds:02d}"

        return {
            "active_users": active_users,
            "new_users": new_users,
            "sessions": sessions,
            "avg_session_duration": avg_session_duration
        }

    def _parse_daily_trend(self, report, days: int) -> list:
        """Parse daily trend and perform Zero-Filling."""
        rows = report.get("rows", [])
        
        # Build dictionary of existing data
        data_by_date = {}
        for row in rows:
            raw_date = row.get("dimensionValues", [{}])[0].get("value", "")
            vals = row.get("metricValues", [])
            active_users = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
            sessions = int(vals[1].get("value", 0)) if len(vals) > 1 else 0
            
            if len(raw_date) == 8: # YYYYMMDD
                try:
                    dt = datetime.strptime(raw_date, "%Y%m%d").date()
                    data_by_date[dt] = {"active_users": active_users, "sessions": sessions}
                except ValueError:
                    pass

        # Zero-filling loop
        daily_trend = []
        months_ar = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'مايو', 6: 'يونيو',
            7: 'يوليو', 8: 'أغسطس', 9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }
        
        for i in range(days + 1):
            curr_date = date.today() - timedelta(days=(days - i))
            day_data = data_by_date.get(curr_date, {"active_users": 0, "sessions": 0})
            
            friendly_date = f"{curr_date.day} {months_ar[curr_date.month]}"
            
            daily_trend.append({
                "date": curr_date.strftime("%Y-%m-%d"),
                "label": friendly_date,
                "active_users": day_data["active_users"],
                "sessions": day_data["sessions"]
            })
            
        return daily_trend

    def _format_duration(self, seconds_str) -> str:
        """Parse seconds string and return MM:SS duration."""
        try:
            seconds = int(float(seconds_str))
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:02d}:{secs:02d}"
        except (ValueError, TypeError):
            return "00:00"

    def _parse_top_pages(self, report) -> list:
        """Parse top visited pages report."""
        rows = report.get("rows", [])
        result = []
        for row in rows:
            dims = row.get("dimensionValues", [])
            vals = row.get("metricValues", [])
            
            path = dims[0].get("value", "") if len(dims) > 0 else ""
            title = dims[1].get("value", "") if len(dims) > 1 else ""
            title = title.replace("(not set)", "--")
            if not title.strip():
                title = "--"
            active_users = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
            views = int(vals[1].get("value", 0)) if len(vals) > 1 else 0
            sessions = int(vals[2].get("value", 0)) if len(vals) > 2 else 0
            
            # Calculate average engagement time (total_engagement / active_users)
            total_engagement_sec = float(vals[3].get("value", 0)) if len(vals) > 3 else 0
            avg_engagement_sec = (total_engagement_sec / active_users) if active_users > 0 else 0
            
            engagement_time = self._format_duration(avg_engagement_sec)
            
            result.append({
                "path": path,
                "title": title,
                "active_users": active_users,
                "views": views,
                "sessions": sessions,
                "engagement_time": engagement_time
            })
        return result

    def _parse_traffic_sources(self, report) -> list:
        """Parse traffic sources."""
        rows = report.get("rows", [])
        result = []
        for row in rows:
            dims = row.get("dimensionValues", [])
            vals = row.get("metricValues", [])
            
            source = dims[0].get("value", "direct / none") if len(dims) > 0 else "direct / none"
            source = source.replace("(not set)", "--")
            active_users = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
            sessions = int(vals[1].get("value", 0)) if len(vals) > 1 else 0
            
            result.append({
                "source": source,
                "active_users": active_users,
                "sessions": sessions
            })
        return result

    def _parse_countries(self, report) -> list:
        """Parse top countries."""
        rows = report.get("rows", [])
        result = []
        
        country_map = {
            "egypt": "مصر",
            "saudi arabia": "السعودية",
            "turkey": "تركيا",
            "syria": "سوريا",
            "jordan": "الأردن",
            "iraq": "العراق",
            "yemen": "اليمن",
            "palestine": "فلسطين",
            "united arab emirates": "الإمارات",
            "kuwait": "الكويت",
            "qatar": "قطر",
            "oman": "عُمان",
            "bahrain": "البحرين",
            "lebanon": "لبنان",
            "libya": "ليبيا",
            "sudan": "السودان",
            "algeria": "الجزائر",
            "morocco": "المغرب",
            "tunisia": "تونس",
            "germany": "ألمانيا",
            "united states": "الولايات المتحدة",
            "united kingdom": "المملكة المتحدة",
            "sweden": "السويد",
            "france": "فرنسا",
            "canada": "كندا",
            "russia": "روسيا",
            "ukraine": "أوكرانيا",
            "netherlands": "هولندا",
            "belgium": "بلجيكا",
            "italy": "إيطاليا",
            "spain": "إسبانيا",
            "malaysia": "ماليزيا",
            "indonesia": "إندونيسيا",
            "china": "الصين",
            "japan": "اليابان",
            "south korea": "كوريا الجنوبية",
            "india": "الهند",
            "pakistan": "باكستان",
            "iran": "إيران",
            "cyprus": "قبرص",
            "greece": "اليونان",
            "austria": "النمسا",
            "switzerland": "سويسرا",
            "australia": "أستراليا",
            "somalia": "الصومال",
            "mauritania": "موريتانيا",
            "djibouti": "جيبوتي",
        }
        
        for row in rows:
            dims = row.get("dimensionValues", [])
            vals = row.get("metricValues", [])
            
            country = dims[0].get("value", "Unknown") if len(dims) > 0 else "Unknown"
            country = country.replace("(not set)", "--")
            if country == "Unknown":
                country = "--"
            else:
                country_lower = country.lower().strip()
                country = country_map.get(country_lower, country)
                
            active_users = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
            sessions = int(vals[1].get("value", 0)) if len(vals) > 1 else 0
            
            result.append({
                "country": country,
                "active_users": active_users,
                "sessions": sessions
            })
        return result

    def _parse_devices(self, report) -> list:
        """Parse device breakdown."""
        rows = report.get("rows", [])
        result = []
        total_users = 0
        for row in rows:
            vals = row.get("metricValues", [])
            active_users = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
            total_users += active_users

        for row in rows:
            dims = row.get("dimensionValues", [])
            vals = row.get("metricValues", [])
            
            device = dims[0].get("value", "Desktop") if len(dims) > 0 else "Desktop"
            active_users = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
            
            # Map default device strings to Arabic
            device_ar = "كمبيوتر"
            if device.lower() == "mobile":
                device_ar = "موبايل"
            elif device.lower() == "tablet":
                device_ar = "تابلت"
            elif device.lower() == "smart tv":
                device_ar = "شاشة ذكية"

            percentage = round((active_users / total_users) * 100) if total_users > 0 else 0

            result.append({
                "device": device,
                "device_ar": device_ar,
                "active_users": active_users,
                "percentage": percentage
            })
        return result

    def _parse_browsers(self, report) -> list:
        """Parse browser breakdown."""
        rows = report.get("rows", [])
        result = []
        total_users = 0
        for row in rows:
            vals = row.get("metricValues", [])
            active_users = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
            total_users += active_users

        for row in rows:
            dims = row.get("dimensionValues", [])
            vals = row.get("metricValues", [])
            
            browser = dims[0].get("value", "Unknown") if len(dims) > 0 else "Unknown"
            browser = browser.replace("(not set)", "--")
            active_users = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
            percentage = round((active_users / total_users) * 100) if total_users > 0 else 0
            
            result.append({
                "browser": browser,
                "active_users": active_users,
                "percentage": percentage
            })
        return result

    def _parse_os(self, report) -> list:
        """Parse operating system breakdown."""
        rows = report.get("rows", [])
        result = []
        total_users = 0
        for row in rows:
            vals = row.get("metricValues", [])
            active_users = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
            total_users += active_users

        for row in rows:
            dims = row.get("dimensionValues", [])
            vals = row.get("metricValues", [])
            
            os_name = dims[0].get("value", "Unknown") if len(dims) > 0 else "Unknown"
            os_name = os_name.replace("(not set)", "--")
            active_users = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
            percentage = round((active_users / total_users) * 100) if total_users > 0 else 0
            
            # Map friendly names
            os_friendly = os_name
            if os_name.lower() == "macintosh":
                os_friendly = "macOS"
            
            result.append({
                "os": os_friendly,
                "active_users": active_users,
                "percentage": percentage
            })
        return result

    def _parse_events(self, report) -> list:
        """Parse events and conversions."""
        rows = report.get("rows", [])
        result = []
        
        event_map = {
            "page_view": "مشاهدة الصفحات",
            "session_start": "زيارات جديدة للموقع",
            "first_visit": "مستخدمين لأول مرة",
            "user_engagement": "تفاعل الزوار مع الصفحات",
            "click": "نقرات على روابط خارجية",
            "contact_lead_submit": "طلبات تواصل مرسلة",
            "whatsapp_click": "نقرات واتساب التفاعلية",
            "view_item": "عرض تفاصيل جامعة/كلية",
            "search": "عمليات البحث في الموقع",
            "scroll": "التمرير وقراءة المقالات",
        }
        
        for row in rows:
            dims = row.get("dimensionValues", [])
            vals = row.get("metricValues", [])
            
            event_name = dims[0].get("value", "Unknown") if len(dims) > 0 else "Unknown"
            event_name = event_name.replace("(not set)", "--")
            
            # Translation and fallback formatting
            event_friendly = event_map.get(event_name.lower().strip())
            if not event_friendly:
                if event_name == "--" or event_name == "Unknown":
                    event_friendly = "--"
                else:
                    event_friendly = event_name.replace("_", " ").title()
                    
            event_count = int(vals[0].get("value", 0)) if len(vals) > 0 else 0
            conversions = int(vals[1].get("value", 0)) if len(vals) > 1 else 0
            
            result.append({
                "event_name": event_name,
                "event_friendly": event_friendly,
                "event_count": event_count,
                "conversions": conversions
            })
        return result
