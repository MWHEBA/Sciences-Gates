import json
import logging
import requests
from django.conf import settings
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def sanitize_html(html_content: str) -> str:
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    allowed_tags = {'p', 'br', 'strong', 'b', 'em', 'i', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()
        else:
            tag.attrs = {}
    return str(soup)

class GeminiServiceError(Exception):
    """Base exception for Gemini Service."""
    pass

class GeminiService:
    """Service client for calling the Gemini API to rewrite and restructure majors."""

    def __init__(self, api_key=None):
        self.api_key = api_key or getattr(settings, 'GEMINI_API_KEY', '').strip()
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
        self.session = requests.Session()
        
        # Mask and print key for verification in runserver logs
        masked_key = f"{self.api_key[:6]}...{self.api_key[-4:]}" if len(self.api_key) > 10 else "EMPTY"
        print(f"[GeminiService] Initialized with API key: {masked_key}")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search_competitor(self, major_name: str) -> str | None:
        """
        Queries competitor WordPress search using ChatGPT-User User-Agent,
        and returns the first article URL if found.
        """
        # Clean the major name to get a high-quality search term
        query = major_name
        for prefix in ["دراسة تخصص", "دراسة", "تخصص"]:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
        
        # Split by separators
        query = query.split('|')[0].split('-')[0].split('–')[0].split('—')[0].split(':')[0].strip()
        
        # Remove common noise words/suffixes (especially "malaysia" which matches generic articles)
        noise_words = [
            "في ماليزيا",
            "ماليزيا",
            "تكاليف",
            "الرسوم",
            "الجامعات",
            "شروط",
            "قبول",
            "سنة",
            "عام",
            "2026",
            "2025",
            "2024"
        ]
        for nw in noise_words:
            query = query.replace(nw, "").strip()
            
        # Clean up any extra spaces
        query = " ".join(query.split())
        
        if not query:
            return None
            
        search_url = "https://your-uni.com/"
        params = {"s": query}
        headers = {
            'User-Agent': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ChatGPT-User/1.0; +http://openai.com/bot)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ar,en;q=0.5',
            'Connection': 'keep-alive'
        }
        
        try:
            logger.info(f"Searching competitor for term: '{query}'")
            resp = self.session.get(search_url, params=params, headers=headers, timeout=12)
            if resp.ok:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Locate main content container to avoid matching sidebar or footer articles
                content_container = soup.find(id='content') or soup.find('main') or soup.find(class_='site-main') or soup
                
                # Check article tags inside main container
                articles = content_container.find_all('article')
                for art in articles:
                    title_link = art.find('a', href=True)
                    headers_tags = art.find_all(['h1', 'h2', 'h3'])
                    for h in headers_tags:
                        a_tag = h.find('a', href=True)
                        if a_tag:
                            title_link = a_tag
                            break
                    
                    if title_link:
                        url = title_link['href']
                        if 'your-uni.com' in url and not any(x in url for x in ['/category/', '/tag/', '/author/', '/page/', '/wp-content/']):
                            logger.info(f"Found competitor URL match: '{url}'")
                            return url
                            
                # Fallback: check any link in the content area inside the main container
                for a in content_container.find_all('a', href=True):
                    url = a['href']
                    if 'your-uni.com' in url and not any(x in url for x in ['/category/', '/tag/', '/author/', '/page/', '/wp-content/', '/contact-us/']) and url != 'https://your-uni.com/' and url != 'https://your-uni.com':
                        logger.info(f"Fallback matched competitor link: '{url}'")
                        return url
        except Exception as e:
            logger.error(f"Error searching competitor for '{query}': {e}", exc_info=True)
            
        return None

    def fetch_competitor_content(self, url: str) -> str | None:
        """
        Fetches competitor URL with ChatGPT-User User-Agent,
        extracts the container content and converts it to a clean Markdown-like structure
        to optimize token count and API performance.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ChatGPT-User/1.0; +http://openai.com/bot)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ar,en;q=0.5',
            'Connection': 'keep-alive'
        }
        
        try:
            logger.info(f"Fetching competitor content from URL: '{url}'")
            resp = self.session.get(url, headers=headers, timeout=12)
            if resp.ok:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Locate elementor or entry-content or postContent container
                container = soup.find(class_='elementor') or soup.find(class_='entry-content') or soup.find(class_='postContent') or soup.find('article')
                if not container:
                    container = soup.body if soup.body else soup
                
                # Decompose unwanted elements
                for tag in container.find_all(['script', 'style', 'noscript', 'iframe', 'svg', 'header', 'footer', 'nav']):
                    tag.decompose()
                
                markdown_lines = []
                # Find all headings, paragraphs, lists, and tables
                for el in container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'table']):
                    # Skip if element is inside header or footer or nav
                    if el.find_parent(['header', 'footer', 'nav']):
                        continue
                        
                    text = el.get_text().strip()
                    if not text:
                        continue
                        
                    if el.name.startswith('h'):
                        level = int(el.name[1])
                        markdown_lines.append(f"\n{'#' * level} {text}\n")
                    elif el.name == 'p':
                        markdown_lines.append(f"\n{text}\n")
                    elif el.name == 'li':
                        markdown_lines.append(f"- {text}")
                    elif el.name == 'table':
                        rows = []
                        for tr in el.find_all('tr'):
                            cells = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                            if any(cells):
                                rows.append(" | ".join(cells))
                        if rows:
                            markdown_lines.append("\n\n" + "\n".join(rows) + "\n\n")
                            
                cleaned_text = "".join(markdown_lines).strip()
                if cleaned_text:
                    logger.info(f"Successfully cleaned competitor page content. Length: {len(cleaned_text)} chars.")
                    return cleaned_text
        except Exception as e:
            logger.error(f"Error fetching competitor content from '{url}': {e}", exc_info=True)
            
        return None

    def build_prompt(self, mapped_data: dict, competitor_html: str = None) -> str:
        """
        Compiles the full prompt text containing the old website content,
        competitor content, and style guidelines for manual or automatic AI execution.
        """
        import json
        
        # Get list of all available universities in the database
        try:
            from apps.universities.models import University
            univs = list(University.objects.all().values_list('name', flat=True))
            univs_list = "\n- ".join(univs)
        except Exception:
            univs_list = ""

        raw_input = {
            "name": mapped_data['form_initial'].get('name', ''),
            "description": mapped_data['form_initial'].get('description', ''),
            "why_study_section": mapped_data['form_initial'].get('why_study_section', ''),
            "how_to_apply_section": mapped_data['form_initial'].get('how_to_apply_section', ''),
            "career_opportunities": mapped_data['form_initial'].get('career_opportunities', ''),
            "study_duration": mapped_data['form_initial'].get('study_duration', ''),
            "bachelor_duration": mapped_data['form_initial'].get('bachelor_duration', ''),
            "master_duration": mapped_data['form_initial'].get('master_duration', ''),
            "phd_duration": mapped_data['form_initial'].get('phd_duration', ''),
            "study_language": mapped_data['form_initial'].get('study_language', ''),
            "practical_training": mapped_data['form_initial'].get('practical_training', ''),
            "subjects_tables": mapped_data.get('subjects_tables', []),
            "salary_tables": mapped_data.get('salary_tables', []),
            "faqs_data": mapped_data.get('faqs_data', []),
            "countries_tables": mapped_data.get('countries_tables', []),
            "best_universities": mapped_data.get('best_universities', []),
            "cheap_universities": mapped_data.get('cheap_universities', []),
            "seo": mapped_data.get('seo', {})
        }

        prompt = (
            "You are a professional educational advisor and content writer for 'Sciences Gates' (بوابات العلوم), "
            "an agency that helps international students apply to universities in Malaysia.\n"
            "Your task is to populate the fields of a new Major model in our database by doing a precise, "
            "field-by-field extraction and synthesis. Do NOT write or modify any SEO meta fields (such as Yoast meta title, "
            "meta description, or focus keywords) as they are preserved verbatim from the old site.\n\n"
            "You must review and populate the following fields and tables one by one:\n"
            "1. 'name': Clean Arabic name of the major (e.g. change 'دراسة تخصص هندسة البرمجيات في ماليزيا' to 'هندسة البرمجيات').\n"
            "2. 'bachelor_duration', 'master_duration', 'phd_duration': Study duration in Malaysia for each degree level (e.g. '4 سنوات', 'سنتان'). If a degree level is not applicable to this major (e.g. pre-university/foundation), leave it blank.\n"
            "3. 'study_language': Language of instruction in Malaysia (e.g. 'اللغة الإنجليزية', 'اللغة العربية').\n"
            "4. 'practical_training': Practical training/internship details (e.g. 'متاح في السنة الأخيرة').\n"
            "5. 'career_opportunities': Career options and roles for graduates, formatted in neat HTML.\n"
            "6. 'description': Detailed description of the major, formatted in HTML.\n"
            "7. 'why_study_section': Reasons to study this major, formatted in HTML.\n"
            "8. 'how_to_apply_section': Detailed application steps, formatted in HTML.\n"
            "9. 'subjects_tables': Academic years and subjects studied (subjects should be comma-separated in Arabic and English).\n"
            "10. 'salary_tables': Jobs and average monthly salaries in Malaysia (e.g. '3,000 - 8,000 رنجت ماليزي').\n"
            "11. 'faqs_data': FAQ questions and answers about this major in Malaysia.\n"
            "12. 'countries_tables': Comparison of study costs, study durations, and living costs between Malaysia and other popular study destinations (e.g. Germany, UK, USA, Turkey).\n"
            "13. 'tuition_fees': A list of tables detailing tuition fees for this major at top Malaysian universities. Each table contains a 'title', a list of 'headers' (usually ['الجامعة', 'البرنامج', 'الرسوم السنوية']), and a list of 'rows' (representing each university's data).\n"
            "14. 'best_universities': List of the best universities in Malaysia offering this major. You MUST select and output university names chosen exactly from the list of available universities in our database below:\n"
            f"- {univs_list}\n\n"
            "15. 'cheap_universities': List of cheap or economical universities in Malaysia offering this major. You MUST select and output university names chosen exactly from the list of available universities in our database below:\n"
            f"- {univs_list}\n\n"
            "Style Guidelines:\n"
            "- Tone: Calm, minimal, elegant, professional, and clear Arabic. No promotional hype, fluff, or exaggeration.\n"
            "- Readability: Prioritize readability with balanced whitespace and consistent typography.\n"
            "- Formatting: Use clean HTML tags (such as <p>, <br>, <strong>, <ul>, <li>). Do NOT use inline styles, alignment styles, or hex/rgb colors.\n\n"
            "CRITICAL SEARCH AND GROUNDING RULES:\n"
            "1. Primarily use the old website content and the competitor's page content provided below.\n"
            "2. Merge the information, avoiding repetition, and prioritize the competitor's figures if there is any conflict in numerical data.\n"
            "3. If any field or table information (such as course subjects, salary in Malaysia, study durations, or practical training details) is missing or incomplete in BOTH provided sources, you MUST search for the exact, accurate, and up-to-date information for this major in Malaysia, and fill in the field accurately.\n"
            "4. Make sure that 100% of the fields are filled with accurate, precise, and 100% correct information. Do not use placeholders or generic values.\n\n"
        )

        prompt += (
            "Here is the old website content (JSON format):\n"
            f"{json.dumps(raw_input, ensure_ascii=False, indent=2)}\n\n"
        )

        if competitor_html:
            prompt += (
                "Here is the competitor's webpage content (Markdown/Clean Text):\n"
                f"{competitor_html}\n\n"
            )

        prompt += (
            "Please output the result as a raw JSON object containing the fields: "
            "name, description, why_study_section, how_to_apply_section, career_opportunities, "
            "bachelor_duration, master_duration, phd_duration, study_language, practical_training, "
            "subjects_tables (array of objects with academic_year, subjects, track_name), "
            "salary_tables (array of objects with job_title, job_description, average_monthly_salary), "
            "faqs_data (array of objects with question, answer), "
            "countries_tables (array of objects with destination, study_duration, annual_fees, living_cost), "
            "tuition_fees (array of objects with title, headers (array of strings), rows (array of arrays of strings)), "
            "best_universities (array of strings containing university names matching the database exactly), "
            "cheap_universities (array of strings containing university names matching the database exactly).\n"
        )
        return prompt

    def rewrite_major(self, mapped_data: dict, competitor_html: str = None, job_id=None) -> dict:
        """
        Calls Gemini API to rewrite the major content, optionally merging competitor's content
        and restructuring tables/FAQs according to the new website style guidelines.
        """
        if not self.is_configured():
            logger.warning("Gemini API Key is not configured. Skipping AI rewrite.")
            return mapped_data

        url = f"{self.endpoint}?key={self.api_key}"
        headers = {
            'Content-Type': 'application/json',
        }

        # Compile prompt and store it in mapped_data
        prompt = self.build_prompt(mapped_data, competitor_html)
        mapped_data['compiled_prompt'] = prompt

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "name": {
                    "type": "STRING",
                    "description": "Cleaned Arabic name of the major, e.g., 'الهندسة الميكانيكية'."
                },
                "description": {
                    "type": "STRING",
                    "description": "Rewritten Arabic description of the major in HTML format (using <p>, <br>, <strong>, etc. No inline styles)."
                },
                "why_study_section": {
                    "type": "STRING",
                    "description": "Rewritten 'Why study' section in HTML format."
                },
                "how_to_apply_section": {
                    "type": "STRING",
                    "description": "Rewritten 'How to apply' section in HTML format."
                },
                "career_opportunities": {
                    "type": "STRING",
                    "description": "Rewritten 'Career opportunities' section in HTML format."
                },
                "bachelor_duration": {
                    "type": "STRING",
                    "description": "Normalized duration for Bachelor's degree (e.g. '4 سنوات'). Leave empty if not applicable."
                },
                "master_duration": {
                    "type": "STRING",
                    "description": "Normalized duration for Master's degree (e.g. 'سنتان' or '1-2 سنوات'). Leave empty if not applicable."
                },
                "phd_duration": {
                    "type": "STRING",
                    "description": "Normalized duration for PhD degree (e.g. '3-4 سنوات'). Leave empty if not applicable."
                },
                "study_language": {
                    "type": "STRING",
                    "description": "Language of study (e.g. 'اللغة الإنجليزية')."
                },
                "practical_training": {
                    "type": "STRING",
                    "description": "Practical training details (e.g. 'متاح في السنة الأخيرة')."
                },
                "subjects_tables": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "academic_year": {
                                "type": "STRING",
                                "description": "Academic year (e.g. 'السنة الأولى')."
                            },
                            "subjects": {
                                "type": "STRING",
                                "description": "Comma-separated subjects in Arabic and English."
                            },
                            "track_name": {
                                "type": "STRING",
                                "description": "Track name if any (e.g. 'العام')."
                            }
                        },
                        "required": ["academic_year", "subjects"]
                    }
                },
                "salary_tables": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "job_title": {
                                "type": "STRING",
                                "description": "Job title in Arabic (e.g. 'مهندس ميكانيكي')."
                            },
                            "job_description": {
                                "type": "STRING",
                                "description": "Brief description of the job role."
                            },
                            "average_monthly_salary": {
                                "type": "STRING",
                                "description": "Monthly salary range (e.g. '3,000 - 8,000 رنجت ماليزي')."
                            }
                        },
                        "required": ["job_title", "average_monthly_salary"]
                    }
                },
                "faqs_data": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "question": {
                                "type": "STRING",
                                "description": "FAQ question."
                            },
                            "answer": {
                                "type": "STRING",
                                "description": "FAQ answer."
                            }
                        },
                        "required": ["question", "answer"]
                    }
                }
            },
            "required": [
                "name", "description", "why_study_section", "how_to_apply_section", "career_opportunities",
                "bachelor_duration", "master_duration", "phd_duration", "study_language", "practical_training",
                "subjects_tables", "salary_tables", "faqs_data"
            ]
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "tools": [
                {
                    "google_search_retrieval": {}
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": response_schema,
                "temperature": 0.2
            }
        }

        try:
            logger.info(f"Calling Gemini API to rewrite major '{mapped_data['form_initial'].get('name', '')}'...")
            if job_id:
                from apps.importer.models import ImportJob
                ImportJob.objects.filter(id=job_id).update(progress=80, status_message="جاري صياغة المحتوى والبحث على الإنترنت للمعلومات الناقصة...")
                
            response = self.session.post(url, headers=headers, json=payload, timeout=45)
            
            if not response.ok:
                raise GeminiServiceError(f"Gemini API returned status code {response.status_code}: {response.text}")
            
            resp_data = response.json()
            # Extract JSON output text
            text_out = resp_data['candidates'][0]['content']['parts'][0]['text']
            ai_data = json.loads(text_out)
            
            if job_id:
                from apps.importer.models import ImportJob
                ImportJob.objects.filter(id=job_id).update(progress=92, status_message="تمت الصياغة بنجاح، جاري تنظيف وتنسيق الأكواد...")
            
            # Map the AI rewritten fields back to the mapped_data dict structure
            mapped_data['form_initial']['name'] = ai_data.get('name', mapped_data['form_initial']['name'])
            mapped_data['form_initial']['description'] = sanitize_html(ai_data.get('description', mapped_data['form_initial'].get('description', '')))
            mapped_data['form_initial']['why_study_section'] = sanitize_html(ai_data.get('why_study_section', mapped_data['form_initial'].get('why_study_section', '')))
            mapped_data['form_initial']['how_to_apply_section'] = sanitize_html(ai_data.get('how_to_apply_section', mapped_data['form_initial'].get('how_to_apply_section', '')))
            mapped_data['form_initial']['career_opportunities'] = sanitize_html(ai_data.get('career_opportunities', mapped_data['form_initial'].get('career_opportunities', '')))
            
            mapped_data['form_initial']['bachelor_duration'] = ai_data.get('bachelor_duration', mapped_data['form_initial'].get('bachelor_duration', ''))
            mapped_data['form_initial']['master_duration'] = ai_data.get('master_duration', mapped_data['form_initial'].get('master_duration', ''))
            mapped_data['form_initial']['phd_duration'] = ai_data.get('phd_duration', mapped_data['form_initial'].get('phd_duration', ''))
            
            # Set general study_duration to bachelor_duration as a fallback if not set
            b_dur = ai_data.get('bachelor_duration', '')
            if b_dur:
                mapped_data['form_initial']['study_duration'] = b_dur
            
            mapped_data['form_initial']['study_language'] = ai_data.get('study_language', mapped_data['form_initial'].get('study_language', ''))
            mapped_data['form_initial']['practical_training'] = ai_data.get('practical_training', mapped_data['form_initial'].get('practical_training', ''))
            
            # Update Related tables
            mapped_data['subjects_tables'] = ai_data.get('subjects_tables', mapped_data.get('subjects_tables', []))
            mapped_data['salary_tables'] = ai_data.get('salary_tables', mapped_data.get('salary_tables', []))
            mapped_data['faqs_data'] = ai_data.get('faqs_data', mapped_data.get('faqs_data', []))
            
            logger.info("Successfully completed AI rewrite and schema mapping.")
            
        except Exception as e:
            logger.error(f"Error during Gemini AI rewrite: {e}", exc_info=True)
            err_msg = str(e)
            is_auth_or_quota = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "400" in err_msg or "API_KEY_INVALID" in err_msg
            
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                friendly_err = "انتهت حصة الاستخدام المتاحة لمفتاح Gemini API (Quota Exceeded). يرجى تفعيل الدفع أو شحن الرصيد في حساب Google AI Studio."
            elif "400" in err_msg or "API_KEY_INVALID" in err_msg:
                friendly_err = "مفتاح Gemini API المستخدم غير صالح أو منتهي الصلاحية."
            elif "timeout" in err_msg.lower():
                friendly_err = "انتهت مهلة الاتصال بخادم Gemini API."
            else:
                friendly_err = f"حدث خطأ غير متوقع أثناء الاتصال بالذكاء الاصطناعي ({err_msg})"
            
            if is_auth_or_quota:
                raise Exception(friendly_err)
                
            # Add friendly warning to warnings so it shows up in the UI
            mapped_data.setdefault('image_warnings', []).append(
                f"تنبيه: فشل دمج وتطوير المحتوى بالذكاء الاصطناعي بسبب: {friendly_err} (تم استيراد محتوى الموقع القديم بنجاح بنسخته الأصلية دون تعديل)."
            )
            
        return mapped_data
