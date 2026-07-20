"""
HTML sanitization utilities.
Consolidated and redirected to apps.html_editor.sanitizer to remove duplication.
"""
from apps.html_editor.sanitizer import (
    sanitize_html,
    sanitize_article_html,
    get_safe_html,
    _is_safe_url,
    ALLOWED_TAGS,
    ALLOWED_ATTRIBUTES,
    ALLOWED_STYLES,
    ALLOWED_PROTOCOLS
)
