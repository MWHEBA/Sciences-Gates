import json
from django.core.management.base import BaseCommand
from apps.universities.models import University
from apps.majors.models import Major
from apps.articles.models import Article
from apps.institutes.models import Institute
from apps.seo.services.page_analyzer import sanitize_synonyms, normalize_text


class Command(BaseCommand):
    help = (
        "Sanitizes and normalizes keyphrase_synonyms across models (University, Major, Article, Institute). "
        "Deduplicates synonyms, excludes focus keywords, enforces max synonyms & word count limits, "
        "and converts legacy comma-separated values to clean JSON arrays."
    )

    TARGET_MODELS = {
        'university': (University, 'name'),
        'major': (Major, 'name'),
        'article': (Article, 'title'),
        'institute': (Institute, 'name'),
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Apply changes to the database. If omitted, runs in preview / dry-run mode.'
        )
        parser.add_argument(
            '--model',
            type=str,
            default=None,
            help='Filter to a specific model: university, major, article, institute.'
        )
        parser.add_argument(
            '--ids',
            type=str,
            default=None,
            help='Comma-separated list of primary keys to target (e.g., --ids=322,339).'
        )
        parser.add_argument(
            '--max-synonyms',
            type=int,
            default=5,
            help='Maximum number of synonyms allowed per record (default: 5).'
        )
        parser.add_argument(
            '--max-words',
            type=int,
            default=7,
            help='Maximum words per synonym (default: 7).'
        )
        parser.add_argument(
            '--max-length',
            type=int,
            default=255,
            help='Maximum length in characters for the stored JSON array (default: 255).'
        )
        parser.add_argument(
            '--include-whitespace',
            action='store_true',
            help='Also update records that only differ by JSON whitespace formatting.'
        )

    def safe_write(self, msg, style_func=None):
        encoding = getattr(self.stdout, 'encoding', None) or 'utf-8'
        try:
            safe_msg = msg.encode(encoding, errors='replace').decode(encoding)
        except Exception:
            safe_msg = msg
        if style_func:
            self.stdout.write(style_func(safe_msg))
        else:
            self.stdout.write(safe_msg)

    def handle(self, *args, **options):
        apply_changes = options.get('apply', False)
        model_filter = (options.get('model') or '').strip().lower()
        ids_filter = options.get('ids')
        max_synonyms = options.get('max_synonyms', 5)
        max_words = options.get('max_words', 7)
        max_length = options.get('max_length', 255)
        include_whitespace = options.get('include_whitespace', False)

        target_ids = None
        if ids_filter:
            try:
                target_ids = [int(i.strip()) for i in ids_filter.split(',') if i.strip()]
            except ValueError:
                self.stderr.write(self.style.ERROR(f"Invalid --ids value: {ids_filter}. Expected integers."))
                return

        models_to_process = {}
        if model_filter:
            if model_filter in self.TARGET_MODELS:
                models_to_process[model_filter] = self.TARGET_MODELS[model_filter]
            else:
                self.stderr.write(
                    self.style.ERROR(
                        f"Unknown model '{model_filter}'. Available: {', '.join(self.TARGET_MODELS.keys())}"
                    )
                )
                return
        else:
            models_to_process = self.TARGET_MODELS

        mode_str = "APPLY (WRITING TO DATABASE)" if apply_changes else "DRY-RUN (PREVIEW ONLY)"
        self.safe_write(f"=== SEO Synonyms Sanitizer [{mode_str}] ===", self.style.MIGRATE_HEADING)
        self.safe_write(
            f"Config: max_synonyms={max_synonyms}, max_words={max_words}, max_length={max_length}\n"
        )

        grand_total_inspected = 0
        grand_total_modified = 0

        for model_key, (model_cls, name_field) in models_to_process.items():
            qs = model_cls.objects.exclude(keyphrase_synonyms='').exclude(keyphrase_synonyms__isnull=True)
            if target_ids is not None:
                qs = qs.filter(pk__in=target_ids)

            total_count = qs.count()
            grand_total_inspected += total_count
            modified_records = []

            self.safe_write(f"\n--- Checking {model_cls.__name__} (Found {total_count} with synonyms) ---", self.style.WARNING)

            for obj in qs.order_by('pk'):
                raw_syns = obj.keyphrase_synonyms or ''
                focus_kw = getattr(obj, 'focus_keyword', '') or ''
                obj_name = getattr(obj, name_field, f"#{obj.pk}")

                clean_json, clean_list = sanitize_synonyms(
                    raw_syns,
                    focus_keyword=focus_kw,
                    max_synonyms=max_synonyms,
                    max_words=max_words,
                    max_length=max_length
                )

                if clean_json != raw_syns:
                    reasons = []
                    orig_items = []
                    is_legacy_string = False
                    try:
                        p = json.loads(raw_syns)
                        if isinstance(p, list):
                            orig_items = [str(s).strip() for s in p if str(s).strip()]
                        elif isinstance(p, str):
                            orig_items = [s.strip() for s in p.replace('،', ',').split(',') if s.strip()]
                            is_legacy_string = True
                    except Exception:
                        orig_items = [s.strip() for s in raw_syns.replace('،', ',').split(',') if s.strip()]
                        is_legacy_string = True

                    if is_legacy_string:
                        reasons.append("converted legacy comma-separated text to JSON array")

                    norm_kw = normalize_text(focus_kw)
                    norm_orig = [normalize_text(s) for s in orig_items]

                    # Check if focus keyword was removed
                    if norm_kw and any(ns == norm_kw for ns in norm_orig):
                        reasons.append("removed focus keyword from synonyms")

                    # Check duplicates in original
                    if len(norm_orig) != len(set(norm_orig)):
                        reasons.append("removed duplicate synonyms")

                    # Check long phrases removed
                    long_phrases = [s for s in orig_items if len(normalize_text(s).split()) > max_words]
                    if long_phrases:
                        reasons.append(f"removed {len(long_phrases)} phrases >{max_words} words")

                    # Check truncated > max_synonyms
                    unique_valid = []
                    seen_test = {norm_kw} if norm_kw else set()
                    for s in orig_items:
                        ns = normalize_text(s)
                        if ns and ns not in seen_test and len(ns.split()) <= max_words:
                            seen_test.add(ns)
                            unique_valid.append(s)
                    if len(unique_valid) > max_synonyms:
                        reasons.append(f"truncated {len(unique_valid) - max_synonyms} synonyms over limit ({max_synonyms})")

                    is_semantic_change = any(r != "reformatted JSON whitespace" for r in reasons)
                    if not is_semantic_change and not include_whitespace:
                        continue

                    reasons_str = ", ".join(reasons) if reasons else "normalized / cleaned"

                    modified_records.append({
                        'id': obj.pk,
                        'name': obj_name,
                        'kw': focus_kw,
                        'before': raw_syns,
                        'after': clean_json,
                        'after_list': clean_list,
                        'reasons': reasons_str,
                        'instance': obj,
                    })

            grand_total_modified += len(modified_records)

            if not modified_records:
                self.safe_write(f"  All {total_count} records are already clean!", self.style.SUCCESS)
            else:
                self.safe_write(f"  Needs sanitization: {len(modified_records)} / {total_count} records:")
                for item in modified_records:
                    self.safe_write(
                        f"    [#{item['id']}] {item['name']}\n"
                        f"      Focus KW: '{item['kw']}'\n"
                        f"      Original: {item['before']}\n"
                        f"      Cleaned:  {item['after']}\n"
                        f"      Note:     {item['reasons']}"
                    )

                    if apply_changes:
                        item['instance'].keyphrase_synonyms = item['after']
                        item['instance'].save(update_fields=['keyphrase_synonyms'])

        self.safe_write("\n=== Summary ===", self.style.MIGRATE_HEADING)
        self.safe_write(f"Total Inspected: {grand_total_inspected}")
        self.safe_write(f"Total Modified:  {grand_total_modified}")

        if apply_changes:
            self.safe_write(f"\n[SUCCESS] Successfully sanitized and updated {grand_total_modified} records in the database!", self.style.SUCCESS)
        else:
            self.safe_write(f"\n[DRY-RUN] Preview complete. No records were modified in database.", self.style.NOTICE)
            self.safe_write("Run with '--apply' to execute these changes.", self.style.NOTICE)

