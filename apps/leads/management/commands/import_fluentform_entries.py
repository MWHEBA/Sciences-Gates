import os
import json
import csv
import re
import logging
from urllib.parse import unquote
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.leads.models import Lead, LeadType, LeadStatus

logger = logging.getLogger(__name__)


def parse_date(date_str):
    if not date_str:
        return None
    date_str = str(date_str).strip()
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y',
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            return dt
        except ValueError:
            continue
    return None


def fix_latin1_utf8(s):
    if not s:
        return ""
    try:
        return s.encode('latin1').decode('utf-8', errors='ignore')
    except Exception:
        return s


def clean_text(text):
    if not text:
        return ""
    text = fix_latin1_utf8(str(text))
    # Remove control characters except normal space
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


class Command(BaseCommand):
    help = "Import form entries (Fluent Forms or Elementor Forms Submissions) from SQL/JSON/CSV into Django Lead model (>= date)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help="Path to form entries file (.sql, .json, or .csv)"
        )
        parser.add_argument(
            '--since',
            type=str,
            default='2025-01-01',
            help="Filter submissions created on or after this date (YYYY-MM-DD). Default: 2025-01-01"
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Run simulation without saving changes to database."
        )

    def handle(self, *args, **options):
        file_path = options['file']
        since_str = options['since']
        dry_run = options['dry_run']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        since_date = parse_date(since_str)
        if not since_date:
            self.stdout.write(self.style.ERROR(f"Invalid --since date format: {since_str}"))
            return

        self.stdout.write(self.style.SUCCESS(f"=== Form Submissions Importer ==="))
        self.stdout.write(f"File: {file_path}")
        self.stdout.write(f"Filter entries >= {since_date.strftime('%Y-%m-%d')}")
        self.stdout.write(f"Mode: {'SIMULATION (DRY-RUN)' if dry_run else 'LIVE IMPORT'}\n")

        entries = self.load_file(file_path)
        if not entries:
            self.stdout.write(self.style.WARNING("No entries found in file."))
            return

        # Disconnect email notification signal during historical import
        try:
            from django.db.models.signals import post_save
            from apps.leads.signals import send_lead_notification_email
            post_save.disconnect(send_lead_notification_email, sender=Lead)
        except Exception:
            pass

        imported_count = 0
        skipped_date_count = 0
        skipped_duplicate_count = 0
        error_count = 0

        for idx, item in enumerate(entries, start=1):
            try:
                entry_data, raw_created_at, form_id = self.normalize_entry(item)
                
                created_at_dt = parse_date(raw_created_at)
                if created_at_dt and created_at_dt < since_date:
                    skipped_date_count += 1
                    continue

                lead_data = self.extract_lead_fields(entry_data, form_id)
                if not lead_data.get('name') and not lead_data.get('phone') and not lead_data.get('email'):
                    # Empty or invalid record
                    error_count += 1
                    continue

                # Check duplicate by email/phone & created_at date
                if self.is_duplicate(lead_data, created_at_dt):
                    skipped_duplicate_count += 1
                    continue

                if not dry_run:
                    with transaction.atomic():
                        lead = Lead.objects.create(**lead_data)
                        if created_at_dt:
                            Lead.objects.filter(pk=lead.pk).update(created_at=created_at_dt)

                imported_count += 1
                name_display = lead_data.get('name') or lead_data.get('phone') or 'N/A'
                dt_display = created_at_dt.strftime('%Y-%m-%d %H:%M') if created_at_dt else 'N/A'
                phone_display = lead_data.get('phone', '')
                self.stdout.write(self.style.SUCCESS(
                    f"[{idx}] Imported: {name_display} | Email: {lead_data['email']} | Phone: {phone_display} | Date: {dt_display}"
                ))

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"[{idx}] Error importing entry: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"\n=== Summary ===\n"
            f"Total evaluated: {len(entries)}\n"
            f"Imported successfully: {imported_count}\n"
            f"Skipped (Before {since_str}): {skipped_date_count}\n"
            f"Skipped (Duplicates): {skipped_duplicate_count}\n"
            f"Errors / Invalid: {error_count}\n"
        ))

    def load_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get('data') or data.get('entries') or [data]
        elif ext == '.csv':
            entries = []
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entries.append(row)
            return entries
        elif ext == '.sql':
            return self.parse_sql_dump(file_path)
        return []

    def parse_sql_dump(self, file_path):
        lines = []
        try:
            with open(file_path, 'r', encoding='latin1') as f:
                lines = f.readlines()
        except Exception:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

        entries = []

        # Check if Elementor Submissions exist in SQL dump
        has_elementor = any('e_submissions' in l for l in lines)
        if has_elementor:
            entries.extend(self.parse_elementor_sql(lines))

        # Check if Fluent Forms Submissions exist in SQL dump
        has_fluent = any('fluentform_submissions' in l for l in lines)
        if has_fluent:
            entries.extend(self.parse_fluentform_sql(lines))

        return entries

    def parse_elementor_sql(self, lines):
        def extract_tuples(table_keyword):
            block_lines = []
            in_table = False
            for line in lines:
                if f'INSERT INTO `{table_keyword}`' in line or f'INSERT INTO {table_keyword}' in line or (table_keyword in line and 'INSERT INTO' in line):
                    in_table = True
                    block_lines.append(line)
                    continue
                if in_table:
                    block_lines.append(line)
                    if line.strip().endswith(';'):
                        break
            text = "".join(block_lines)
            
            raw_tuples = []
            current_tuple = []
            in_paren = False
            in_quote = False
            esc = False
            
            for char in text:
                if not in_paren:
                    if char == '(':
                        in_paren = True
                        current_tuple = []
                else:
                    if esc:
                        current_tuple.append(char)
                        esc = False
                    elif char == '\\':
                        current_tuple.append(char)
                        esc = True
                    elif char == "'" and not in_quote:
                        in_quote = True
                        current_tuple.append(char)
                    elif char == "'" and in_quote:
                        in_quote = False
                        current_tuple.append(char)
                    elif char == ')' and not in_quote:
                        in_paren = False
                        raw_tuples.append("".join(current_tuple))
                        current_tuple = []
                    else:
                        current_tuple.append(char)
            return raw_tuples

        def parse_row(row_str):
            vals = []
            curr = []
            in_quote = False
            esc = False
            for char in row_str:
                if esc:
                    curr.append(char)
                    esc = False
                elif char == '\\':
                    esc = True
                elif char == "'":
                    in_quote = not in_quote
                elif char == ',' and not in_quote:
                    vals.append("".join(curr).strip().strip("'"))
                    curr = []
                else:
                    curr.append(char)
            if curr:
                vals.append("".join(curr).strip().strip("'"))
            return vals

        # Find matching table prefix for e_submissions
        prefix_match = None
        for l in lines:
            m = re.search(r"INSERT INTO [`'\"]?(\w*e_submissions)[`'\"]?", l)
            if m:
                prefix_match = m.group(1)
                break

        if not prefix_match:
            return []

        sub_tuples = extract_tuples(prefix_match)
        values_tableName = prefix_match + "_values"
        val_tuples = extract_tuples(values_tableName)

        submissions = {}
        for t_str in sub_tuples:
            row = parse_row(t_str)
            if len(row) >= 10:
                sub_id = int(row[0]) if row[0].isdigit() else None
                if not sub_id:
                    continue

                dates = [val for val in row if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', val)]
                created_at = dates[0] if dates else None

                referer = row[5] if len(row) > 5 else ''
                referer_title = fix_latin1_utf8(row[6]) if len(row) > 6 else ''
                form_name = fix_latin1_utf8(row[3]) if len(row) > 3 else ''

                submissions[sub_id] = {
                    'sub_id': sub_id,
                    'created_at': created_at,
                    'referer': referer,
                    'referer_title': referer_title,
                    'form_name': form_name,
                    'fields': {}
                }

        for t_str in val_tuples:
            row = parse_row(t_str)
            if len(row) >= 4 and row[1].isdigit():
                sub_id = int(row[1])
                key = row[2]
                val = row[3]
                if sub_id in submissions:
                    submissions[sub_id]['fields'][key] = val

        results = []
        for sub_id, data in submissions.items():
            f = data['fields']
            name = clean_text(f.get('name') or f.get('full_name') or f.get('first_name') or '')
            email = clean_text(f.get('email') or '')
            phone_code = clean_text(f.get('field_1038854') or '')
            phone_num = clean_text(f.get('field_015824b') or f.get('phone') or f.get('mobile') or '')
            phone = f"{phone_code} {phone_num}".strip()

            nationality = clean_text(f.get('field_737452') or f.get('nationality') or '')
            residence_country = clean_text(f.get('field_7587458') or f.get('residence_country') or f.get('country') or '')
            study_level = clean_text(f.get('field_737451e') or f.get('study_level') or '')
            address = clean_text(f.get('field_609de28') or f.get('address') or '')
            message = clean_text(f.get('message') or f.get('description') or '')

            results.append({
                'name': name,
                'email': email,
                'phone': phone,
                'nationality': nationality,
                'residence_country': residence_country,
                'study_level': study_level,
                'address': address,
                'message': message,
                'source_url': data['referer'],
                'referer_title': data['referer_title'],
                'form_name': data['form_name'],
                'created_at': data['created_at'],
            })

        return results

    def parse_fluentform_sql(self, lines):
        # Fallback parser for fluentform_submissions in SQL dump
        insert_pattern = re.compile(r"INSERT\s+INTO\s+[`'\"]?\w*fluentform_submissions[`'\"]?\s*\(([^)]+)\)\s*VALUES\s*(.+?);", re.IGNORECASE | re.DOTALL)
        content = "".join(lines)
        entries = []
        for match in insert_pattern.finditer(content):
            columns = [c.strip(" `'\":") for c in match.group(1).split(',')]
            rows_raw = re.findall(r"\((?>'[^']*'|[^)])+\)", match.group(2))
            for row_str in rows_raw:
                row_str = row_str.strip('(), ')
                vals = [v.strip().strip("'") for v in row_str.split("','")]
                if len(vals) == len(columns):
                    entries.append(dict(zip(columns, vals)))
        return entries

    def normalize_entry(self, item):
        raw_created_at = None
        form_id = None
        entry_data = {}

        if isinstance(item, dict):
            raw_created_at = item.get('created_at') or item.get('date_created') or item.get('created')
            form_id = item.get('form_id')

            response = item.get('response') or item.get('user_inputs') or item.get('fields')
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except Exception:
                    response = {}

            if isinstance(response, dict):
                entry_data = {**response, **item}
            else:
                entry_data = item

        return entry_data, raw_created_at, form_id

    def extract_lead_fields(self, data, form_id=None):
        names = data.get('names') or data.get('name') or data.get('full_name') or ''
        first_name = ''
        last_name = ''
        if isinstance(names, dict):
            first_name = clean_text(names.get('first_name', ''))
            last_name = clean_text(names.get('last_name', ''))
            name = f"{first_name} {last_name}".strip()
        elif isinstance(names, str):
            name = clean_text(names)
        else:
            first_name = clean_text(data.get('first_name') or '')
            last_name = clean_text(data.get('last_name') or '')
            name = f"{first_name} {last_name}".strip()

        if not name:
            name = "بدون اسم"

        phone = clean_text(data.get('phone') or data.get('mobile') or data.get('phone_number') or '')
        email = clean_text(data.get('email') or data.get('user_email') or '')

        nationality = clean_text(data.get('nationality') or data.get('dropdown_1') or data.get('input_text') or '')
        residence_country = clean_text(data.get('residence_country') or data.get('dropdown') or data.get('country') or '')
        study_level = clean_text(data.get('study_level') or data.get('dropdown_2') or '')
        address = clean_text(data.get('address') or '')
        institution_name = clean_text(data.get('hidden') or data.get('university') or data.get('institution_name') or '')
        message = clean_text(data.get('message') or data.get('description') or data.get('notes') or '')

        form_id_str = str(form_id) if form_id else ''
        form_name_str = str(data.get('form_name') or '').lower()
        source_page_str = str(data.get('source_url') or data.get('source_page') or '').lower()
        
        referer_title_str = str(data.get('referer_title') or '').lower()
        source_url_unquoted = unquote(str(data.get('source_url') or '')).lower()

        # Precise Split Rule:
        # REGISTRATION: if student selected a study_level OR came from /register/ OR title has 'سجل'
        if study_level or 'register' in source_url_unquoted or 'university-registration' in source_url_unquoted or 'سجل' in referer_title_str:
            lead_type = LeadType.REGISTRATION
        else:
            lead_type = LeadType.CONTACT

        source_page = clean_text(data.get('source_url') or data.get('source_page') or data.get('_wp_http_referer') or '')
        referrer = clean_text(data.get('referrer') or '')

        return {
            'lead_type': lead_type,
            'name': name,
            'email': email,
            'phone': phone,
            'message': message,
            'nationality': nationality,
            'institution_name': institution_name,
            'residence_country': residence_country,
            'study_level': study_level,
            'address': address,
            'source_page': source_page,
            'referrer': referrer,
            'status': LeadStatus.NEW,
        }

    def is_duplicate(self, lead_data, created_at_dt):
        qs = Lead.objects.all()
        if lead_data.get('email'):
            qs_email = qs.filter(email=lead_data['email'])
            if created_at_dt:
                qs_email = qs_email.filter(created_at__date=created_at_dt.date())
            if qs_email.exists():
                return True
        if lead_data.get('phone'):
            qs_phone = qs.filter(phone=lead_data['phone'])
            if created_at_dt:
                qs_phone = qs_phone.filter(created_at__date=created_at_dt.date())
            if qs_phone.exists():
                return True
        return False
