import json
import re


class SEOHTMLParser:
    def __init__(self, html_content: str, selector: str):
        self.html = html_content or ""
        self.selector = selector

    def extract_full_page_data(self):
        return {
            "title": self._extract_title(),
            "meta_description": self._extract_meta("description"),
            "canonical": self._extract_canonical(),
            "robots": self._extract_meta("robots"),
            "html_lang": self._extract_html_lang(),
            "h1": self._extract_first_tag_text("h1"),
            "og_title": self._extract_meta("og:title", prop=True),
            "og_description": self._extract_meta("og:description", prop=True),
            "og_image": self._extract_meta("og:image", prop=True),
            "schemas": self._extract_schemas(),
            "author_visible": bool(re.search(r'class=["\'][^"\']*author[^"\']*["\']', self.html, re.I)),
            "date_visible": bool(re.search(r'<time\b', self.html, re.I) or re.search(r'class=["\'][^"\']*date[^"\']*["\']', self.html, re.I)),
            "breadcrumb_present": bool(re.search(r'aria-label=["\'][^"\']*breadcrumb[^"\']*["\']', self.html, re.I) or re.search(r'class=["\'][^"\']*breadcrumb[^"\']*["\']', self.html, re.I)),
        }

    def extract_main_content_data(self):
        segment = self._extract_data_seo_content_segment()
        if not segment:
            return {
                "selector_missing": True,
                "word_count": 0,
                "headings": [],
                "links": [],
                "image_warnings": [],
            }

        segment = self._remove_data_seo_ignore_blocks(segment)

        images = re.findall(r'<img\b[^>]*>', segment, re.I)
        image_warnings = []
        for img in images:
            alt_match = re.search(r'\balt=["\']([^"\']*)["\']', img, re.I)
            if not alt_match:
                image_warnings.append({"code": "MISSING_ALT", "message": "صورة بدون alt."})
                continue
            alt_text = alt_match.group(1).strip()
            if alt_text == "":
                aria_hidden = re.search(r'\baria-hidden=["\']true["\']', img, re.I)
                role_presentation = re.search(r'\brole=["\']presentation["\']', img, re.I)
                if not (aria_hidden or role_presentation):
                    image_warnings.append({"code": "EMPTY_ALT_NON_DECORATIVE", "message": "alt فارغ لصورة غير decorative."})

        headings = []
        for level in (2, 3, 4):
            for m in re.finditer(rf'<h{level}\b[^>]*>(.*?)</h{level}>', segment, re.I | re.S):
                text = self._strip_tags(m.group(1)).strip()
                if text:
                    headings.append({"level": level, "text": text})

        links = []
        for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', segment, re.I | re.S):
            links.append({"href": m.group(1).strip(), "text": self._strip_tags(m.group(2)).strip()})

        text = self._strip_tags(segment)
        words = [w for w in re.split(r'\s+', text) if w]

        return {
            "selector_missing": False,
            "word_count": len(words),
            "headings": headings,
            "links": links,
            "image_warnings": image_warnings,
        }

    def _extract_title(self):
        m = re.search(r'<title\b[^>]*>(.*?)</title>', self.html, re.I | re.S)
        return self._strip_tags(m.group(1)).strip() if m else ""

    def _extract_html_lang(self):
        m = re.search(r'<html\b[^>]*\blang=["\']([^"\']+)["\']', self.html, re.I)
        return m.group(1).strip() if m else ""

    def _extract_meta(self, name, prop=False):
        attr = 'property' if prop else 'name'
        pattern = rf'<meta\b[^>]*\b{attr}=["\']{re.escape(name)}["\'][^>]*\bcontent=["\']([^"\']*)["\'][^>]*>'
        m = re.search(pattern, self.html, re.I)
        return m.group(1).strip() if m else ""

    def _extract_canonical(self):
        m = re.search(r'<link\b[^>]*\brel=["\']canonical["\'][^>]*\bhref=["\']([^"\']*)["\'][^>]*>', self.html, re.I)
        return m.group(1).strip() if m else ""

    def _extract_first_tag_text(self, tag):
        m = re.search(rf'<{tag}\b[^>]*>(.*?)</{tag}>', self.html, re.I | re.S)
        return self._strip_tags(m.group(1)).strip() if m else ""

    def _extract_schemas(self):
        out = []
        for m in re.finditer(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', self.html, re.I | re.S):
            raw = m.group(1).strip()
            try:
                parsed = json.loads(raw)
                out.append({"raw": raw, "valid_json": True, "parsed": parsed})
            except json.JSONDecodeError as exc:
                out.append({"raw": raw, "valid_json": False, "error": str(exc), "parsed": None})
        return out

    def _extract_data_seo_content_segment(self):
        open_match = re.search(r'<([a-zA-Z0-9]+)\b[^>]*\bdata-seo-content\b[^>]*>', self.html, re.I)
        if not open_match:
            return ""
        tag = open_match.group(1)
        start = open_match.start()
        end = self._find_matching_tag_end(self.html, tag, open_match.end())
        return self.html[start:end] if end > start else ""

    def _remove_data_seo_ignore_blocks(self, html):
        while True:
            m = re.search(r'<([a-zA-Z0-9]+)\b[^>]*\bdata-seo-ignore\b[^>]*>', html, re.I)
            if not m:
                break
            tag = m.group(1)
            end = self._find_matching_tag_end(html, tag, m.end())
            if end <= m.start():
                break
            html = html[:m.start()] + html[end:]
        return html

    def _find_matching_tag_end(self, content, tag, from_idx):
        open_pat = re.compile(rf'<{tag}\b[^>]*>', re.I)
        close_pat = re.compile(rf'</{tag}>', re.I)

        depth = 1
        idx = from_idx
        while idx < len(content):
            next_open = open_pat.search(content, idx)
            next_close = close_pat.search(content, idx)
            if not next_close:
                return len(content)
            if next_open and next_open.start() < next_close.start():
                depth += 1
                idx = next_open.end()
            else:
                depth -= 1
                idx = next_close.end()
                if depth == 0:
                    return idx
        return len(content)

    @staticmethod
    def _strip_tags(value):
        return re.sub(r'<[^>]+>', ' ', value or '')
