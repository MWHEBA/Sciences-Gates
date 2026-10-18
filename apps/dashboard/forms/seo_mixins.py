from apps.seo.services.page_analyzer import sanitize_synonyms


class SEOSynonymsSanitizerMixin:
    """
    Mixin to auto-sanitize keyphrase_synonyms:
    - Deduplicate synonyms using Arabic text normalization.
    - Exclude the focus keyword if present in synonyms.
    - Restrict maximum number of synonyms to 5.
    - Restrict maximum words per synonym to 7 words.
    - Enforce 255 char field limit cleanly.
    - Serializes output cleanly as JSON array.
    """
    def clean(self):
        cleaned_data = super().clean()
        focus_kw = str(cleaned_data.get('focus_keyword') or '').strip()
        synonyms_raw = str(cleaned_data.get('keyphrase_synonyms') or '').strip()

        json_str, _ = sanitize_synonyms(
            synonyms_raw,
            focus_keyword=focus_kw,
            max_synonyms=5,
            max_words=7,
            max_length=255
        )
        cleaned_data['keyphrase_synonyms'] = json_str
        return cleaned_data

