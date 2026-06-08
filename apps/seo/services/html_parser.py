import json
import re
import html
from bs4 import BeautifulSoup


class SEOHTMLParser:
    def __init__(self, html_content: str, selector: str):
        self.html = html_content or ""
        self.selector = selector
        self.soup = BeautifulSoup(self.html, "html.parser")

    def extract_full_page_data(self):
        # 1. Extract title
        title_tag = self.soup.find("title")
        title = ""
        if title_tag:
            title = " ".join(title_tag.get_text().split())

        # 2. Extract meta description
        meta_desc_tag = (
            self.soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)}) or
            self.soup.find("meta", attrs={"property": re.compile(r"^description$", re.I)})
        )
        meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

        # 3. Extract canonical link
        canonical_tag = self.soup.find("link", attrs={"rel": re.compile(r"^canonical$", re.I)})
        canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

        # 4. Extract robots
        robots_tag = self.soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
        robots = robots_tag.get("content", "").strip() if robots_tag else ""

        # 5. Extract html lang
        html_tag = self.soup.find("html")
        html_lang = html_tag.get("lang", "").strip() if html_tag else ""

        # 6. Extract H1 tag (first and full list)
        h1_tags = [h.get_text().strip() for h in self.soup.find_all("h1")]
        h1_first = h1_tags[0] if h1_tags else ""

        # 7. Extract OG tags
        og_title_tag = self.soup.find("meta", attrs={"property": re.compile(r"^og:title$", re.I)})
        og_title = og_title_tag.get("content", "").strip() if og_title_tag else ""

        og_desc_tag = self.soup.find("meta", attrs={"property": re.compile(r"^og:description$", re.I)})
        og_description = og_desc_tag.get("content", "").strip() if og_desc_tag else ""

        og_image_tag = self.soup.find("meta", attrs={"property": re.compile(r"^og:image$", re.I)})
        og_image = og_image_tag.get("content", "").strip() if og_image_tag else ""

        # 8. Extract schemas
        schemas = []
        for script in self.soup.find_all("script", type=re.compile(r"^application/ld\+json$", re.I)):
            raw = script.string or ""
            raw = raw.strip()
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
                schemas.append({"raw": raw, "valid_json": True, "parsed": parsed})
            except json.JSONDecodeError as exc:
                schemas.append({"raw": raw, "valid_json": False, "error": str(exc), "parsed": None})

        # 9. Extract author visible (exact word boundary class checking)
        author_visible = False
        for tag in self.soup.find_all(class_=True):
            classes = tag.get("class", [])
            if "author" in classes:
                author_visible = True
                break

        # 10. Extract date visible (exact word boundary class checking)
        date_visible = bool(self.soup.find("time"))
        if not date_visible:
            for tag in self.soup.find_all(class_=True):
                classes = tag.get("class", [])
                if "date" in classes:
                    date_visible = True
                    break

        # 11. Extract breadcrumb present
        # Detect breadcrumb HTML globally (it lives outside data-seo-content by design)
        breadcrumb_present = False
        # Check aria-label in English or Arabic
        if self.soup.find(attrs={"aria-label": re.compile(r"breadcrumb|مسار\s+التنقل|مسار التنقل", re.I)}):
            breadcrumb_present = True
        # Fallback: check class name contains breadcrumb
        if not breadcrumb_present:
            for tag in self.soup.find_all(class_=True):
                classes = tag.get("class", [])
                if "breadcrumb" in classes:
                    breadcrumb_present = True
                    break
        # Fallback: check for BreadcrumbList schema in page
        if not breadcrumb_present:
            for script in self.soup.find_all("script", type=re.compile(r"application/ld\+json", re.I)):
                raw = (script.string or "").strip()
                if "BreadcrumbList" in raw:
                    breadcrumb_present = True
                    break

        return {
            "title": title,
            "meta_description": meta_description,
            "canonical": canonical,
            "robots": robots,
            "html_lang": html_lang,
            "h1": h1_first,
            "h1_tags": h1_tags,  # full list for Phase 6 validation
            "og_title": og_title,
            "og_description": og_description,
            "og_image": og_image,
            "schemas": schemas,
            "author_visible": author_visible,
            "date_visible": date_visible,
            "breadcrumb_present": breadcrumb_present,
        }

    def extract_main_content_data(self):
        # Locate the node matching selector (data-seo-content)
        content_node = self.soup.select_one(self.selector)
        selector_missing = False
        if not content_node:
            content_node = self.soup.find("body")
            selector_missing = True

        if not content_node:
            return {
                "selector_missing": True,
                "word_count": 0,
                "headings": [],
                "links": [],
                "image_warnings": [],
            }

        # Clone node to avoid mutating original document structure
        node_copy = BeautifulSoup(str(content_node), "html.parser")

        # Decompose elements to exclude from content text extraction
        for tag in node_copy.find_all(["script", "style", "noscript", "svg", "template"]):
            tag.decompose()

        # Decompose elements with data-seo-ignore attribute
        for tag in node_copy.find_all(attrs={"data-seo-ignore": True}):
            tag.decompose()

        # Extract images
        images = node_copy.find_all("img")
        image_warnings = []
        for img in images:
            alt = img.get("alt")
            if alt is None:
                image_warnings.append({"code": "MISSING_ALT", "message": "صورة بدون alt."})
                continue
            alt_text = alt.strip()
            if alt_text == "":
                aria_hidden = img.get("aria-hidden") == "true"
                role_presentation = img.get("role") == "presentation"
                if not (aria_hidden or role_presentation):
                    image_warnings.append({"code": "EMPTY_ALT_NON_DECORATIVE", "message": "alt فارغ لصورة غير decorative."})

        # Extract headings
        headings = []
        seen_headings = set()  # Track seen heading text to avoid duplicates
        for tag in node_copy.find_all(["h2", "h3", "h4"]):
            level = int(tag.name[1])
            text = " ".join(tag.get_text().split())
            if text:
                # Create a unique key for deduplication (level + text)
                heading_key = f"{level}:{text}"
                if heading_key not in seen_headings:
                    headings.append({"level": level, "text": text})
                    seen_headings.add(heading_key)

        # Extract links
        links = []
        for tag in node_copy.find_all("a", href=True):
            href = tag.get("href", "").strip()
            text = " ".join(tag.get_text().split())
            links.append({"href": href, "text": text})

        # Extract text content for word counting
        raw_text = node_copy.get_text()
        clean_text = html.unescape(raw_text)
        # Using punctuation-aware word segmenting (matches unicode alphanumeric)
        words = [w for w in re.findall(r'\w+', clean_text) if w]

        return {
            "selector_missing": selector_missing,
            "word_count": len(words),
            "headings": headings,
            "links": links,
            "image_warnings": image_warnings,
        }
