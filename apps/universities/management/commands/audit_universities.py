"""
Management command to audit university data migration from WordPress to Django.
Compares WP API data with Django database records and generates detailed HTML reports.
"""
import os
import re
import html
import difflib
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.universities.models import University, Faculty, Program, UniversityFAQ
from apps.importer.services.wp_client import WPImporterClient

class Command(BaseCommand):
    help = 'Audit university data migration by comparing WP API data with local Django database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            help='Audit a specific university by its WordPress slug'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Audit all universities currently in the Django database'
        )
        parser.add_argument(
            '--mismatch-only',
            action='store_true',
            help='Only generate reports and summary for universities with less than 100% match score'
        )

    def safe_write(self, msg, style=None):
        """Write to stdout handling terminal encoding issues."""
        if style:
            msg = style(msg)
        try:
            self.stdout.write(msg)
        except UnicodeEncodeError:
            encoding = getattr(self.stdout, 'encoding', 'utf-8') or 'utf-8'
            safe_msg = msg.encode(encoding, errors='replace').decode(encoding)
            self.stdout.write(safe_msg)

    def scrape_rendered_page(self, slug):
        """Scrape the rendered HTML of a university page from the live site."""
        import requests
        import urllib.parse
        from bs4 import BeautifulSoup
        
        url = f"https://science.mwheba.co.uk/{urllib.parse.quote(slug)}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=25)
        except Exception as e:
            raise Exception(f"Failed to connect to live site: {e}")
            
        if resp.status_code == 404:
            raise Exception("صفحة الجامعة غير موجودة على الموقع الجديد (404 Not Found).")
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # 1. About
        about_html = ""
        about_title = soup.find('h2', class_='detail-section-title', string=lambda s: s and 'عن الجامعة' in s)
        if about_title:
            about_section = about_title.find_parent('section')
            about_content = about_section.find('div', class_='detail-section-content') if about_section else None
            about_html = about_content.decode_contents().strip() if about_content else ""
            
        # 2. Location
        loc_html = ""
        loc_title = soup.find('h2', class_='detail-section-title', string=lambda s: s and 'موقع الجامعة' in s)
        if loc_title:
            loc_section = loc_title.find_parent('section')
            loc_content = loc_section.find('div', class_='detail-section-content') if loc_section else None
            loc_html = loc_content.decode_contents().strip() if loc_content else ""

        # 3. Website
        website_link = ""
        sidebar_label = soup.find('dt', class_='detail-sidebar-label', string=lambda s: s and 'الموقع الرسمي' in s)
        if sidebar_label:
            sibling_val = sidebar_label.find_next_sibling('dd', class_='detail-sidebar-value')
            if sibling_val:
                link = sibling_val.find('a')
                if link and link.get('href'):
                    website_link = link.get('href').strip()

        # 4. Admission Requirements
        admission_section = soup.find('section', class_='detail-section--admission')
        bachelor_html, master_html, phd_html = "", "", ""
        if admission_section:
            bachelor_div = admission_section.find('div', attrs={'x-show': lambda v: v and 'bachelor' in v})
            master_div = admission_section.find('div', attrs={'x-show': lambda v: v and 'master' in v})
            phd_div = admission_section.find('div', attrs={'x-show': lambda v: v and 'phd' in v})
            
            bachelor_html = bachelor_div.decode_contents().strip() if bachelor_div else ""
            master_html = master_div.decode_contents().strip() if master_div else ""
            phd_html = phd_div.decode_contents().strip() if phd_div else ""

        # 5. Faculties & Programs
        fac_accordion = soup.find('div', class_='detail-faculties-accordion')
        faculties = []
        if fac_accordion:
            fac_items = fac_accordion.find_all('div', class_='detail-faculty-item')
            for item in fac_items:
                name_span = item.find('span', class_='detail-faculty-name')
                fac_name = name_span.get_text().strip() if name_span else ""
                
                programs = []
                table = item.find('table', class_='detail-table')
                if table:
                    tbody = table.find('tbody')
                    rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 3:
                            prog_name = cols[0].get_text().strip()
                            prog_dur = cols[1].get_text().strip()
                            prog_fee = cols[2].get_text().strip()
                            programs.append({
                                'name': prog_name,
                                'duration': prog_dur,
                                'tuition_fees': prog_fee
                            })
                faculties.append({
                    'name': fac_name,
                    'programs': programs
                })

        # 6. FAQs
        faq_accordion = soup.find('div', class_='detail-faq-accordion')
        faqs = []
        if faq_accordion:
            faq_items = faq_accordion.find_all('div', class_='detail-faq-item')
            for item in faq_items:
                q_span = item.find('span', class_='detail-faq-question')
                question = q_span.get_text().strip() if q_span else ""
                
                ans_div = item.find('div', class_='detail-faq-answer')
                answer = ans_div.decode_contents().strip() if ans_div else ""
                
                faqs.append({
                    'question': question,
                    'answer': answer
                })

        return {
            'description': about_html,
            'location': loc_html,
            'website': website_link,
            'admission_requirements_bachelor': bachelor_html,
            'admission_requirements_master': master_html,
            'admission_requirements_phd': phd_html,
            'faculties': faculties,
            'faqs': faqs
        }

    def handle(self, *args, **options):
        slug = options.get('slug')
        audit_all = options.get('all')
        mismatch_only = options.get('mismatch_only')

        if not slug and not audit_all:
            self.safe_write('Error: You must specify --slug <slug> or --all', self.style.ERROR)
            return

        client = WPImporterClient()
        universities_to_audit = []

        if slug:
            db_uni = University.objects.filter(slug=slug).first()
            if not db_uni:
                self.safe_write(f"University with slug '{slug}' not found in database.", self.style.ERROR)
                return
            universities_to_audit.append(db_uni)
        else:
            universities_to_audit = list(University.objects.all())
            if not universities_to_audit:
                self.safe_write("No universities found in database to audit.", self.style.WARNING)
                return

        self.safe_write(f"Starting audit for {len(universities_to_audit)} university/universities...", self.style.SUCCESS)

        # Create output directory for reports
        output_dir = os.path.join(settings.BASE_DIR, 'audit_reports')
        os.makedirs(output_dir, exist_ok=True)

        overall_results = []

        for index, db_uni in enumerate(universities_to_audit):
            self.safe_write(f"[{index+1}/{len(universities_to_audit)}] Auditing: {db_uni.name} ({db_uni.slug})", self.style.NOTICE)
            
            try:
                # 1. Fetch WordPress data
                wp_data = client.fetch(db_uni.slug)
            except Exception as e:
                self.safe_write(f"  Failed to fetch WP data: {e}", self.style.ERROR)
                overall_results.append({
                    'name': db_uni.name,
                    'slug': db_uni.slug,
                    'success': False,
                    'error': f"Failed to fetch WP data: {e}"
                })
                continue

            try:
                # 2. Fetch live rendered HTML data from the live website
                scraped_data = self.scrape_rendered_page(db_uni.slug)
                scraped_data['slug'] = db_uni.slug
                scraped_data['name'] = db_uni.name
            except Exception as e:
                self.safe_write(f"  Failed to scrape live HTML: {e}", self.style.ERROR)
                overall_results.append({
                    'name': db_uni.name,
                    'slug': db_uni.slug,
                    'success': False,
                    'error': f"Failed to fetch or parse live HTML: {e}"
                })
                continue

            # Run comparison
            audit_result = self.compare_university(scraped_data, wp_data)
            
            report_path = os.path.join(output_dir, f"audit_{db_uni.slug}.html")
            
            if mismatch_only and audit_result.get('success') and audit_result.get('overall_score') == 100.0:
                self.safe_write(f"  Skipping (100% Match).", self.style.SUCCESS)
                # Remove detailed report if it exists
                if os.path.exists(report_path):
                    try:
                        os.remove(report_path)
                    except OSError:
                        pass
                continue

            overall_results.append(audit_result)

            # Generate individual report
            self.generate_html_report(audit_result, report_path)
            self.safe_write(f"  Report generated: audit_reports/audit_{db_uni.slug}.html", self.style.SUCCESS)

        # Generate index report if auditing all
        if audit_all:
            index_path = os.path.join(output_dir, "overall_audit_report.html")
            self.generate_overall_report(overall_results, index_path)
            self.safe_write("Overall summary report generated: audit_reports/overall_audit_report.html", self.style.SUCCESS)
    def compare_university(self, scraped_data, wp_data):
        """Compare scraped live HTML data with WP JSON data."""
        wp_fields = wp_data.get('fields', {})
        
        # 1. Compare description (عن الجامعة)
        wp_desc = wp_fields.get('description', {}).get('value', '')
        desc_diff_orig, desc_diff_mig, desc_similarity = self.diff_text_fields(wp_desc, scraped_data['description'])

        # 2. Compare location (موقع الجامعة)
        wp_loc = wp_fields.get('location', {}).get('value', '')
        loc_diff_orig, loc_diff_mig, loc_similarity = self.diff_text_fields(wp_loc, scraped_data['location'])

        # 3. Compare website official link
        wp_site = wp_data.get('website', '')  # Fallback check
        if not wp_site and 'website' in wp_fields:
            wp_site = wp_fields.get('website', {}).get('value', '')
        
        site_match = (wp_site == scraped_data['website'])
        site_similarity = 100.0 if site_match else 0.0

        # 4. Compare Admission Requirements
        wp_req_bachelor = wp_fields.get('admission_requirements_bachelor', {}).get('value', '')
        wp_req_master = wp_fields.get('admission_requirements_master', {}).get('value', '')
        wp_req_phd = wp_fields.get('admission_requirements_phd', {}).get('value', '')

        # Fallback to general requirements check if split ones are empty
        if not wp_req_bachelor and not wp_req_master and not wp_req_phd:
            wp_req_bachelor = wp_fields.get('admission_requirements', {}).get('value', '')

        # Split combined WP requirements using ContentMapper logic so we compare corresponding stages
        from apps.importer.services.content_mapper import ContentMapper
        mapper = ContentMapper()
        if wp_req_bachelor:
            split_req = mapper._split_admission_requirements(wp_req_bachelor)
            if split_req['master'] or split_req['phd']:
                wp_req_bachelor = split_req['bachelor']
                if split_req['master']:
                    wp_req_master = split_req['master']
                if split_req['phd']:
                    wp_req_phd = split_req['phd']

        bachelor_diff_orig, bachelor_diff_mig, bachelor_similarity = self.diff_text_fields(wp_req_bachelor, scraped_data['admission_requirements_bachelor'])
        master_diff_orig, master_diff_mig, master_similarity = self.diff_text_fields(wp_req_master, scraped_data['admission_requirements_master'])
        phd_diff_orig, phd_diff_mig, phd_similarity = self.diff_text_fields(wp_req_phd, scraped_data['admission_requirements_phd'])

        # 5. Compare Faculties & Programs
        wp_faculties = wp_data.get('faculties', [])
        faculties_audit = self.compare_faculties_and_programs(scraped_data['faculties'], wp_faculties)

        # 6. Compare FAQs
        wp_faqs = wp_data.get('faqs', [])
        faqs_audit = self.compare_faqs(scraped_data['faqs'], wp_faqs)

        # Calculate overall score
        scores = [
            desc_similarity,
            bachelor_similarity if wp_req_bachelor or scraped_data['admission_requirements_bachelor'] else 100.0,
            master_similarity if wp_req_master or scraped_data['admission_requirements_master'] else 100.0,
            phd_similarity if wp_req_phd or scraped_data['admission_requirements_phd'] else 100.0,
            faculties_audit['similarity_score'],
            faqs_audit['similarity_score'],
            site_similarity
        ]
        if wp_loc or scraped_data['location']:
            scores.append(loc_similarity)
            
        overall_score = sum(scores) / len(scores)

        return {
            'name': wp_data.get('title', {}).get('rendered', '') or scraped_data.get('name', ''),
            'slug': scraped_data.get('slug', ''),
            'success': True,
            'overall_score': round(overall_score, 2),
            
            # Fields comparisons
            'description': {
                'title': 'عن الجامعة',
                'original': wp_desc,
                'migrated': scraped_data['description'],
                'diff_orig': desc_diff_orig,
                'diff_mig': desc_diff_mig,
                'similarity': round(desc_similarity, 2)
            },
            'location': {
                'title': 'موقع الجامعة',
                'original': wp_loc,
                'migrated': scraped_data['location'],
                'diff_orig': loc_diff_orig,
                'diff_mig': loc_diff_mig,
                'similarity': round(loc_similarity, 2)
            },
            'website': {
                'title': 'الموقع الرسمي للجامعة',
                'original': wp_site,
                'migrated': scraped_data['website'],
                'match': site_match,
                'similarity': site_similarity
            },
            'admission_bachelor': {
                'title': 'شروط القبول - بكالوريوس',
                'original': wp_req_bachelor,
                'migrated': scraped_data['admission_requirements_bachelor'],
                'diff_orig': bachelor_diff_orig,
                'diff_mig': bachelor_diff_mig,
                'similarity': round(bachelor_similarity, 2)
            },
            'admission_master': {
                'title': 'شروط القبول - ماجستير',
                'original': wp_req_master,
                'migrated': scraped_data['admission_requirements_master'],
                'diff_orig': master_diff_orig,
                'diff_mig': master_diff_mig,
                'similarity': round(master_similarity, 2)
            },
            'admission_phd': {
                'title': 'شروط القبول - دكتوراه',
                'original': wp_req_phd,
                'migrated': scraped_data['admission_requirements_phd'],
                'diff_orig': phd_diff_orig,
                'diff_mig': phd_diff_mig,
                'similarity': round(phd_similarity, 2)
            },
            'faculties': faculties_audit,
            'faqs': faqs_audit
        }

    def normalize_text(self, text):
        """Clean and normalize Arabic text for comparison."""
        if not text:
            return ""
        # Convert HTML to plain text
        soup = BeautifulSoup(text, 'html.parser')
        plain = soup.get_text()
        
        # Unescape HTML entities
        plain = html.unescape(plain)
        
        # Normalize Arabic characters
        plain = re.sub(r'[أإآا]', 'ا', plain)
        plain = re.sub(r'ة', 'ه', plain)
        plain = re.sub(r'ى', 'ي', plain)
        
        # Clean extra spacing/newlines
        plain = re.sub(r'\s+', ' ', plain)
        return plain.strip()

    def clean_html_for_display(self, text):
        """Extract clean plain text but keep minimal formatting for display in diffs."""
        if not text:
            return ""
        soup = BeautifulSoup(text, 'html.parser')
        # Replace line breaks or blocks with space/newlines for diff cleanliness
        for br in soup.find_all("br"):
            br.replace_with("\n")
        for p in soup.find_all(["p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"]):
            p.append("\n")
        plain = soup.get_text()
        plain = html.unescape(plain)
        # Normalize multiple spaces, but preserve newlines
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in plain.split('\n')]
        return "\n".join([l for l in lines if l])

    def diff_text_fields(self, original_html, migrated_html):
        """Compare two rich text fields and return diffs & similarity percentage."""
        if not original_html and not migrated_html:
            return "", "", 100.0
            
        orig_clean = self.clean_html_for_display(original_html)
        mig_clean = self.clean_html_for_display(migrated_html)
        
        # Normalize for similarity score calculation
        orig_norm = self.normalize_text(original_html)
        mig_norm = self.normalize_text(migrated_html)
        
        if not orig_norm and not mig_norm:
            return "", "", 100.0
            
        # Calculate similarity score on normalized texts
        matcher = difflib.SequenceMatcher(None, orig_norm.split(), mig_norm.split())
        similarity = matcher.ratio() * 100

        # Generate visual word diff on clean texts
        orig_words = orig_clean.split()
        mig_words = mig_clean.split()
        
        word_matcher = difflib.SequenceMatcher(None, orig_words, mig_words)
        
        diff_orig = []
        diff_mig = []
        
        for tag, i1, i2, j1, j2 in word_matcher.get_opcodes():
            if tag == 'equal':
                chunk = " ".join(orig_words[i1:i2])
                diff_orig.append(chunk)
                diff_mig.append(chunk)
            elif tag == 'replace':
                diff_orig.append(f'<del class="diff-del">{" ".join(orig_words[i1:i2])}</del>')
                diff_mig.append(f'<ins class="diff-ins">{" ".join(mig_words[j1:j2])}</ins>')
            elif tag == 'delete':
                diff_orig.append(f'<del class="diff-del">{" ".join(orig_words[i1:i2])}</del>')
            elif tag == 'insert':
                diff_mig.append(f'<ins class="diff-ins">{" ".join(mig_words[j1:j2])}</ins>')
                
        return " ".join(diff_orig), " ".join(diff_mig), similarity

    def compare_faculties_and_programs(self, scraped_faculties, wp_faculties):
        """Compare faculties and programs between WP and scraped site data."""
        missing_faculties = []
        extra_faculties = []
        matched_faculties = []
        
        # Normalize and map scraped faculties
        scraped_fac_map = {}
        for sf in scraped_faculties:
            norm_name = self.normalize_text(sf['name'])
            scraped_fac_map[norm_name] = sf

        wp_fac_names_norm = set()

        for wf in wp_faculties:
            wf_name = wf.get('name', '').strip()
            wf_norm = self.normalize_text(wf_name)
            wp_fac_names_norm.add(wf_norm)
            
            scraped_fac = scraped_fac_map.get(wf_norm)
            if not scraped_fac:
                # Try soft match using difflib
                best_match = None
                best_ratio = 0
                for sf_norm, sf_obj in scraped_fac_map.items():
                    ratio = difflib.SequenceMatcher(None, wf_norm, sf_norm).ratio()
                    if ratio > 0.8 and ratio > best_ratio:
                        best_ratio = ratio
                        best_match = sf_obj
                        
                if best_match:
                    scraped_fac = best_match
            
            if scraped_fac:
                # Compare programs within this faculty
                prog_comparison = self.compare_programs(scraped_fac.get('programs', []), wf.get('programs', []))
                matched_faculties.append({
                    'name': wf_name,
                    'db_name': scraped_fac['name'],
                    'programs': prog_comparison,
                    'score': prog_comparison['similarity_score']
                })
            else:
                missing_faculties.append({
                    'name': wf_name,
                    'program_count': len(wf.get('programs', []))
                })

        # Find extra faculties in scraped that are not in WP
        for sf_norm, sf_obj in scraped_fac_map.items():
            if sf_norm not in wp_fac_names_norm:
                soft_matched = False
                for mf in matched_faculties:
                    if mf['db_name'] == sf_obj['name']:
                        soft_matched = True
                        break
                if not soft_matched:
                    extra_faculties.append({
                        'name': sf_obj['name'],
                        'program_count': len(sf_obj.get('programs', []))
                    })

        # Calculate score
        total_items = len(wp_faculties)
        if total_items == 0:
            similarity_score = 100.0 if not scraped_faculties else 0.0
        else:
            matched_score = sum(f['score'] for f in matched_faculties)
            similarity_score = matched_score / total_items

        return {
            'similarity_score': round(similarity_score, 2),
            'matched': matched_faculties,
            'missing': missing_faculties,
            'extra': extra_faculties,
            'wp_count': len(wp_faculties),
            'db_count': len(scraped_faculties)
        }

    def compare_programs(self, scraped_programs, wp_programs):
        """Compare programs of a faculty between WP and scraped page."""
        scraped_prog_map = {self.normalize_text(sp['name']): sp for sp in scraped_programs}
        
        missing_programs = []
        extra_programs = []
        matched_programs = []
        
        wp_prog_names_norm = set()
        
        for wp in wp_programs:
            wp_name = wp.get('name', '').strip()
            wp_norm = self.normalize_text(wp_name)
            wp_prog_names_norm.add(wp_norm)
            
            scraped_prog = scraped_prog_map.get(wp_norm)
            if not scraped_prog:
                # Soft match
                best_match = None
                best_ratio = 0
                for sp_norm, sp_obj in scraped_prog_map.items():
                    ratio = difflib.SequenceMatcher(None, wp_norm, sp_norm).ratio()
                    if ratio > 0.85 and ratio > best_ratio:
                        best_ratio = ratio
                        best_match = sp_obj
                if best_match:
                    scraped_prog = best_match
            
            if scraped_prog:
                # Compare duration and fees
                wp_dur = wp.get('duration', '').strip()
                wp_fee = wp.get('tuition_fees', '').strip()
                
                dur_match = self.normalize_text(wp_dur) == self.normalize_text(scraped_prog['duration'])
                fee_match = self.normalize_text(wp_fee) == self.normalize_text(scraped_prog['tuition_fees'])
                
                matched_programs.append({
                    'name': wp_name,
                    'db_name': scraped_prog['name'],
                    'wp_duration': wp_dur,
                    'db_duration': scraped_prog['duration'],
                    'wp_fees': wp_fee,
                    'db_fees': scraped_prog['tuition_fees'],
                    'duration_match': dur_match,
                    'fees_match': fee_match
                })
            else:
                missing_programs.append({
                    'name': wp_name,
                    'duration': wp.get('duration', ''),
                    'fees': wp.get('tuition_fees', '')
                })

        for sp_norm, sp_obj in scraped_prog_map.items():
            if sp_norm not in wp_prog_names_norm:
                soft_matched = False
                for mp in matched_programs:
                    if mp['db_name'] == sp_obj['name']:
                        soft_matched = True
                        break
                if not soft_matched:
                    extra_programs.append({
                        'name': sp_obj['name'],
                        'duration': sp_obj['duration'],
                        'fees': sp_obj['tuition_fees']
                    })

        # Calculate faculty match score
        total_wp_programs = len(wp_programs)
        if total_wp_programs == 0:
            similarity_score = 100.0 if not scraped_programs else 0.0
        else:
            match_points = 0
            for mp in matched_programs:
                # 0.6 for name match, 0.2 for duration match, 0.2 for fee match
                points = 0.6
                if mp['duration_match']:
                    points += 0.2
                if mp['fees_match']:
                    points += 0.2
                match_points += points
            similarity_score = (match_points / total_wp_programs) * 100

        return {
            'similarity_score': round(similarity_score, 2),
            'matched': matched_programs,
            'missing': missing_programs,
            'extra': extra_programs,
            'wp_count': len(wp_programs),
            'db_count': len(scraped_programs)
        }

    def compare_faqs(self, scraped_faqs, wp_faqs):
        """Compare FAQs between WP and scraped page."""
        scraped_faq_map = {self.normalize_text(sf['question']): sf for sf in scraped_faqs}
        
        missing_faqs = []
        extra_faqs = []
        matched_faqs = []
        
        wp_faq_qs_norm = set()
        
        for wf in wp_faqs:
            q_text = wf.get('question', '').strip()
            q_norm = self.normalize_text(q_text)
            wp_faq_qs_norm.add(q_norm)
            
            scraped_faq = scraped_faq_map.get(q_norm)
            if not scraped_faq:
                # Try soft match question
                best_match = None
                best_ratio = 0
                for sf_norm, sf_obj in scraped_faq_map.items():
                    ratio = difflib.SequenceMatcher(None, q_norm, sf_norm).ratio()
                    if ratio > 0.8 and ratio > best_ratio:
                        best_ratio = ratio
                        best_match = sf_obj
                if best_match:
                    scraped_faq = best_match
            
            if scraped_faq:
                # Compare answers
                ans_similarity = difflib.SequenceMatcher(
                    None, 
                    self.normalize_text(wf.get('answer', '')).split(), 
                    self.normalize_text(scraped_faq.get('answer', '')).split()
                ).ratio() * 100
                
                # Word diff of answer
                ans_diff_orig, ans_diff_mig, _ = self.diff_text_fields(wf.get('answer', ''), scraped_faq.get('answer', ''))
                
                matched_faqs.append({
                    'question': q_text,
                    'db_question': scraped_faq['question'],
                    'wp_answer': wf.get('answer', ''),
                    'db_answer': scraped_faq['answer'],
                    'diff_orig': ans_diff_orig,
                    'diff_mig': ans_diff_mig,
                    'similarity': round(ans_similarity, 2)
                })
            else:
                missing_faqs.append({
                    'question': q_text,
                    'answer': wf.get('answer', '')
                })

        for sf_norm, sf_obj in scraped_faq_map.items():
            if sf_norm not in wp_faq_qs_norm:
                soft_matched = False
                for mf in matched_faqs:
                    if mf['db_question'] == sf_obj['question']:
                        soft_matched = True
                        break
                if not soft_matched:
                    extra_faqs.append({
                        'question': sf_obj['question'],
                        'answer': sf_obj['answer']
                    })

        # Calculate score
        total_wp_faqs = len(wp_faqs)
        if total_wp_faqs == 0:
            similarity_score = 100.0 if not scraped_faqs else 0.0
        else:
            total_faq_score = sum(f['similarity'] for f in matched_faqs)
            similarity_score = total_faq_score / total_wp_faqs

        return {
            'similarity_score': round(similarity_score, 2),
            'matched': matched_faqs,
            'missing': missing_faqs,
            'extra': extra_faqs,
            'wp_count': len(wp_faqs),
            'db_count': len(scraped_faqs)
        }

    def generate_html_report(self, result, file_path):
        """Compile a premium side-by-side audit report for a university."""
        html_template = self.get_report_html_template()
        # Compile result values into the template
        rendered_html = self.render_template_manually(html_template, result)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)

    def generate_overall_report(self, results, file_path):
        """Compile a premium index report of all audited universities."""
        html_template = self.get_overall_report_template()
        rendered_html = self.render_overall_template_manually(html_template, results)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)

    def render_template_manually(self, template_str, r):
        """Simple template rendering by replacing placeholders to keep script dependency-free."""
        # Replace basic fields
        template_str = template_str.replace("{{ university_name }}", r['name'])
        template_str = template_str.replace("{{ slug }}", r['slug'])
        template_str = template_str.replace("{{ overall_score }}", str(r['overall_score']))
        
        # Set overall badge class
        score = r['overall_score']
        if score >= 95:
            badge_cls, status_txt = "badge-success", "مطابق تماماً"
        elif score >= 80:
            badge_cls, status_txt = "badge-warning", "مطابق جزئياً"
        else:
            badge_cls, status_txt = "badge-danger", "مخالف/ثغرات"
            
        template_str = template_str.replace("{{ status_badge_class }}", badge_cls)
        template_str = template_str.replace("{{ status_text }}", status_txt)

        # 1. Text Diffs blocks
        text_fields = ['description', 'location', 'admission_bachelor', 'admission_master', 'admission_phd']
        for field in text_fields:
            field_data = r.get(field, {})
            title = field_data.get('title', '')
            sim = field_data.get('similarity', 0.0)
            
            if sim >= 95:
                f_badge = "badge-success"
            elif sim >= 80:
                f_badge = "badge-warning"
            else:
                f_badge = "badge-danger"
                
            orig_diff = field_data.get('diff_orig', '<i>لا يوجد محتوى في الموقع الأصلي</i>') or '<i>لا يوجد محتوى</i>'
            mig_diff = field_data.get('diff_mig', '<i>لا يوجد محتوى في الموقع الجديد</i>') or '<i>لا يوجد محتوى</i>'
            
            # Format diff lines to HTML line breaks
            orig_diff = orig_diff.replace('\n', '<br>')
            mig_diff = mig_diff.replace('\n', '<br>')

            block = f"""
            <div class="card">
                <div class="card-header">
                    <span class="card-title">{title}</span>
                    <span class="badge {f_badge}">{sim}% تطابق</span>
                </div>
                <div class="card-body">
                    <div class="diff-container">
                        <div class="diff-pane">
                            <div class="diff-pane-title">الموقع الأصلي (sciencesgates.com)</div>
                            <div class="diff-pane-content">{orig_diff}</div>
                        </div>
                        <div class="diff-pane">
                            <div class="diff-pane-title">الموقع الجديد (science.mwheba.co.uk)</div>
                            <div class="diff-pane-content">{mig_diff}</div>
                        </div>
                    </div>
                </div>
            </div>
            """
            template_str = template_str.replace(f"{{{{ {field}_diff_block }}}}", block)

        # Website
        web_data = r.get('website', {})
        wp_val = web_data.get('original', '')
        db_val = web_data.get('migrated', '')
        
        if not wp_val and not db_val:
            web_match = "غير محدد في الطرفين"
            web_badge = "badge-warning"
        elif web_data.get('match'):
            web_match = "متطابق"
            web_badge = "badge-success"
        else:
            web_match = "غير متطابق"
            web_badge = "badge-danger"
        web_block = f"""
        <div class="card">
            <div class="card-header">
                <span class="card-title">الموقع الإلكتروني الرسمي</span>
                <span class="badge {web_badge}">{web_match}</span>
            </div>
            <div class="card-body">
                <table class="audit-table">
                    <thead>
                        <tr>
                            <th>الموقع الأصلي</th>
                            <th>الموقع الجديد</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><a href="{web_data.get('original') or '#'}" target="_blank">{web_data.get('original') or 'غير متوفر'}</a></td>
                            <td><a href="{web_data.get('migrated') or '#'}" target="_blank">{web_data.get('migrated') or 'غير متوفر'}</a></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        """
        template_str = template_str.replace("{{ website_block }}", web_block)

        # 2. Faculties & Programs Block
        facs_data = r.get('faculties', {})
        fac_badge = "badge-success" if facs_data.get('similarity_score', 0) >= 95 else ("badge-warning" if facs_data.get('similarity_score', 0) >= 80 else "badge-danger")
        
        fac_html = f"""
        <div class="card">
            <div class="card-header">
                <span class="card-title">الكليات والبرامج الأكاديمية</span>
                <span class="badge {fac_badge}">{facs_data.get('similarity_score')}% تطابق</span>
            </div>
            <div class="card-body">
                <div class="summary-stats">
                    <div>عدد الكليات في الأصلي: <strong>{facs_data.get('wp_count')}</strong></div>
                    <div>عدد الكليات في الجديد: <strong>{facs_data.get('db_count')}</strong></div>
                </div>
        """
        
        # Display missing faculties
        if facs_data.get('missing'):
            fac_html += """
            <div class="alert alert-danger">
                <strong>كليات مفقودة تماماً في الموقع الجديد:</strong>
                <ul>
            """
            for mf in facs_data['missing']:
                fac_html += f"<li>{mf['name']} ({mf['program_count']} برامج)</li>"
            fac_html += "</ul></div>"

        # Display extra faculties
        if facs_data.get('extra'):
            fac_html += """
            <div class="alert alert-warning">
                <strong>كليات إضافية (موجودة في الجديد فقط):</strong>
                <ul>
            """
            for ef in facs_data['extra']:
                fac_html += f"<li>{ef['name']} ({ef['program_count']} برامج)</li>"
            fac_html += "</ul></div>"

        # Matched faculties details
        for f in facs_data.get('matched', []):
            f_score = f['score']
            sub_badge = "badge-success" if f_score >= 95 else ("badge-warning" if f_score >= 80 else "badge-danger")
            
            fac_html += f"""
            <div class="faculty-audit-item">
                <div class="faculty-audit-header">
                    <span>الكلية: {f['name']}</span>
                    <span class="badge {sub_badge}">{f_score}% تطابق البرامج</span>
                </div>
            """
            
            progs = f['programs']
            
            if progs.get('missing'):
                fac_html += """
                <div class="alert alert-danger" style="margin: 8px 16px;">
                    <strong>برامج مفقودة في هذه الكلية:</strong>
                    <ul>
                """
                for mp in progs['missing']:
                    fac_html += f"<li>{mp['name']} (مدة الدراسة: {mp['duration']}, الرسوم: {mp['fees']})</li>"
                fac_html += "</ul></div>"
                
            if progs.get('extra'):
                fac_html += """
                <div class="alert alert-warning" style="margin: 8px 16px;">
                    <strong>برامج إضافية في الجديد فقط:</strong>
                    <ul>
                """
                for ep in progs['extra']:
                    fac_html += f"<li>{ep['name']} (مدة الدراسة: {ep['duration']}, الرسوم: {ep['fees']})</li>"
                fac_html += "</ul></div>"

            # Programs comparison table
            if progs.get('matched'):
                fac_html += """
                <table class="audit-table" style="margin-top: 8px;">
                    <thead>
                        <tr>
                            <th>البرنامج (الأصلي vs الجديد)</th>
                            <th>مدة الدراسة (الأصلي)</th>
                            <th>مدة الدراسة (الجديد)</th>
                            <th>الرسوم (الأصلي)</th>
                            <th>الرسوم (الجديد)</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for p in progs['matched']:
                    dur_cls = "" if p['duration_match'] else "mismatch-cell"
                    fee_cls = "" if p['fees_match'] else "mismatch-cell"
                    
                    prog_name_disp = p['name']
                    if p['name'] != p['db_name']:
                        prog_name_disp = f"{p['name']} <br><small style='color: var(--text-muted);'>الاسم في الجديد: {p['db_name']}</small>"
                        
                    fac_html += f"""
                    <tr>
                        <td>{prog_name_disp}</td>
                        <td class="{dur_cls}">{p['wp_duration']}</td>
                        <td class="{dur_cls}">{p['db_duration']}</td>
                        <td class="{fee_cls}">{p['wp_fees']}</td>
                        <td class="{fee_cls}">{p['db_fees']}</td>
                    </tr>
                    """
                fac_html += "</tbody></table>"
                
            fac_html += "</div>"
            
        fac_html += "</div></div>"
        template_str = template_str.replace("{{ faculties_block }}", fac_html)

        # 3. FAQs Block
        faqs_data = r.get('faqs', {})
        faq_badge = "badge-success" if faqs_data.get('similarity_score', 0) >= 95 else ("badge-warning" if faqs_data.get('similarity_score', 0) >= 80 else "badge-danger")
        
        faq_html = f"""
        <div class="card">
            <div class="card-header">
                <span class="card-title">الأسئلة الشائعة FAQ</span>
                <span class="badge {faq_badge}">{faqs_data.get('similarity_score')}% تطابق</span>
            </div>
            <div class="card-body">
                <div class="summary-stats">
                    <div>عدد الأسئلة في الأصلي: <strong>{faqs_data.get('wp_count')}</strong></div>
                    <div>عدد الأسئلة في الجديد: <strong>{faqs_data.get('db_count')}</strong></div>
                </div>
        """
        
        if faqs_data.get('missing'):
            faq_html += """
            <div class="alert alert-danger">
                <strong>أسئلة مفقودة في الجديد:</strong>
                <ul>
            """
            for mf in faqs_data['missing']:
                faq_html += f"<li>{mf['question']}</li>"
            faq_html += "</ul></div>"
            
        if faqs_data.get('extra'):
            faq_html += """
            <div class="alert alert-warning">
                <strong>أسئلة إضافية في الجديد:</strong>
                <ul>
            """
            for ef in faqs_data['extra']:
                faq_html += f"<li>{ef['question']}</li>"
            faq_html += "</ul></div>"

        for f in faqs_data.get('matched', []):
            f_sim = f['similarity']
            f_sub_badge = "badge-success" if f_sim >= 95 else ("badge-warning" if f_sim >= 80 else "badge-danger")
            
            faq_orig_diff_html = f['diff_orig'].replace('\n', '<br>') if f.get('diff_orig') else ''
            faq_mig_diff_html = f['diff_mig'].replace('\n', '<br>') if f.get('diff_mig') else ''
            
            faq_html += f"""
            <div class="faq-audit-item">
                <div class="faq-audit-header">
                    <span>سؤال: {f['question']}</span>
                    <span class="badge {f_sub_badge}">{f_sim}% تطابق الإجابة</span>
                </div>
                <div class="diff-container" style="margin-top: 8px;">
                    <div class="diff-pane">
                        <div class="diff-pane-title">الإجابة الأصلية</div>
                        <div class="diff-pane-content">{faq_orig_diff_html}</div>
                    </div>
                    <div class="diff-pane">
                        <div class="diff-pane-title">الإجابة الجديدة</div>
                        <div class="diff-pane-content">{faq_mig_diff_html}</div>
                    </div>
                </div>
            </div>
            """
            
        faq_html += "</div></div>"
        template_str = template_str.replace("{{ faqs_block }}", faq_html)
        
        return template_str

    def render_overall_template_manually(self, template_str, results):
        """Render index page template."""
        # Calculate summary stats
        total = len(results)
        successful = sum(1 for r in results if r.get('success'))
        failed = total - successful
        
        avg_score = 0.0
        if successful > 0:
            avg_score = sum(r['overall_score'] for r in results if r.get('success')) / successful
            
        template_str = template_str.replace("{{ total }}", str(total))
        template_str = template_str.replace("{{ successful }}", str(successful))
        template_str = template_str.replace("{{ failed }}", str(failed))
        template_str = template_str.replace("{{ avg_score }}", str(round(avg_score, 2)))
        
        # Build table rows
        rows_html = ""
        for idx, r in enumerate(results):
            if r.get('success'):
                score = r['overall_score']
                if score >= 95:
                    status_badge = '<span class="badge badge-success">مطابق تماماً</span>'
                elif score >= 80:
                    status_badge = '<span class="badge badge-warning">تطابق جزئي</span>'
                else:
                    status_badge = '<span class="badge badge-danger">بحاجة لمراجعة</span>'
                    
                score_disp = f"<strong>{score}%</strong>"
                report_link = f'<a href="audit_{r["slug"]}.html" class="btn btn-sm">عرض التقرير التفصيلي</a>'
                
                rows_html += f"""
                <tr>
                    <td>{idx+1}</td>
                    <td>{r['name']}</td>
                    <td><code>{r['slug']}</code></td>
                    <td>{score_disp}</td>
                    <td>{status_badge}</td>
                    <td>{report_link}</td>
                </tr>
                """
            else:
                rows_html += f"""
                <tr class="error-row">
                    <td>{idx+1}</td>
                    <td>{r['name']}</td>
                    <td><code>{r['slug']}</code></td>
                    <td>N/A</td>
                    <td><span class="badge badge-danger">فشل الجلب</span></td>
                    <td class="text-danger"><small>{r.get('error', 'خطأ غير معروف')}</small></td>
                </tr>
                """
                
        template_str = template_str.replace("{{ table_rows }}", rows_html)
        return template_str

    def get_report_html_template(self):
        """Premium HTML layout template for side-by-side university audit reports."""
        return """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير تدقيق ومطابقة: {{ university_name }}</title>
    <style>
        :root {
            --primary-color: #0f172a;
            --primary-light: #1e293b;
            --success-color: #16a34a;
            --success-bg: #f0fdf4;
            --danger-color: #dc2626;
            --danger-bg: #fef2f2;
            --warning-color: #d97706;
            --warning-bg: #fffbeb;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --border-color: #e2e8f0;
            --text-color: #334155;
            --text-muted: #64748b;
        }

        body {
            font-family: system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            margin: 0;
            padding: 24px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }

        .header-title h1 {
            font-size: 24px;
            margin: 0 0 8px 0;
            color: var(--primary-color);
        }

        .header-title p {
            margin: 0;
            color: var(--text-muted);
            font-size: 14px;
        }

        .score-container {
            text-align: left;
        }

        .score-value {
            font-size: 32px;
            font-weight: bold;
            color: var(--primary-color);
        }

        .badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 600;
        }

        .badge-success {
            background-color: var(--success-bg);
            color: var(--success-color);
            border: 1px solid var(--success-color);
        }

        .badge-warning {
            background-color: var(--warning-bg);
            color: var(--warning-color);
            border: 1px solid var(--warning-color);
        }

        .badge-danger {
            background-color: var(--danger-bg);
            color: var(--danger-color);
            border: 1px solid var(--danger-color);
        }

        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            overflow: hidden;
        }

        .card-header {
            background-color: #ffffff;
            border-bottom: 1px solid var(--border-color);
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-size: 18px;
            font-weight: bold;
            color: var(--primary-color);
        }

        .card-body {
            padding: 20px;
        }

        .diff-container {
            display: flex;
            gap: 20px;
        }

        .diff-pane {
            flex: 1;
            background-color: #fafafa;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 16px;
            font-size: 15px;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .diff-pane-title {
            font-weight: bold;
            color: var(--primary-light);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
            margin-bottom: 12px;
            font-size: 13px;
            text-transform: uppercase;
        }

        .diff-del {
            background-color: #fee2e2;
            color: #991b1b;
            text-decoration: line-through;
            padding: 2px 4px;
            border-radius: 2px;
        }

        .diff-ins {
            background-color: #dcfce7;
            color: #166534;
            padding: 2px 4px;
            border-radius: 2px;
        }

        .audit-table {
            width: 100%;
            border-collapse: collapse;
            text-align: right;
            margin: 16px 0;
        }

        .audit-table th {
            background-color: var(--bg-color);
            color: var(--primary-color);
            padding: 12px;
            font-weight: 600;
            border-bottom: 2px solid var(--border-color);
        }

        .audit-table td {
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
            font-size: 14px;
        }

        .mismatch-cell {
            background-color: var(--danger-bg);
            color: var(--danger-color);
            font-weight: 600;
        }

        .alert {
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 16px;
            font-size: 14px;
        }

        .alert-danger {
            background-color: var(--danger-bg);
            color: var(--danger-color);
            border: 1px solid var(--danger-color);
        }

        .alert-warning {
            background-color: var(--warning-bg);
            color: var(--warning-color);
            border: 1px solid var(--warning-color);
        }

        .faculty-audit-item, .faq-audit-item {
            border: 1px solid var(--border-color);
            border-radius: 6px;
            margin-bottom: 16px;
            background-color: #ffffff;
            overflow: hidden;
        }

        .faculty-audit-header, .faq-audit-header {
            background-color: var(--bg-color);
            padding: 12px 16px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
        }

        .summary-stats {
            display: flex;
            gap: 24px;
            margin-bottom: 16px;
            font-size: 14px;
        }

        .btn-back {
            display: inline-block;
            margin-bottom: 16px;
            padding: 8px 16px;
            background-color: var(--primary-color);
            color: #ffffff;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
        }

        .btn-back:hover {
            background-color: var(--primary-light);
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="overall_audit_report.html" class="btn-back">← العودة للتقرير العام</a>
        
        <div class="header">
            <div class="header-title">
                <h1>تقرير تدقيق ومطابقة البيانات لجامعة</h1>
                <h2>{{ university_name }}</h2>
                <p>الرابط (Slug): <code>{{ slug }}</code></p>
            </div>
            <div class="score-container">
                <div class="score-value">{{ overall_score }}%</div>
                <div class="badge {{ status_badge_class }}">{{ status_text }}</div>
            </div>
        </div>

        {{ website_block }}
        
        {{ description_diff_block }}
        
        {{ location_diff_block }}
        
        {{ admission_bachelor_diff_block }}
        
        {{ admission_master_diff_block }}
        
        {{ admission_phd_diff_block }}
        
        {{ faculties_block }}
        
        {{ faqs_block }}
    </div>
</body>
</html>
"""

    def get_overall_report_template(self):
        """Premium HTML index layout template for overall audit reports."""
        return """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ملخص تدقيق ومطابقة الجامعات المستوردة</title>
    <style>
        :root {
            --primary-color: #0f172a;
            --primary-light: #1e293b;
            --success-color: #16a34a;
            --success-bg: #f0fdf4;
            --danger-color: #dc2626;
            --danger-bg: #fef2f2;
            --warning-color: #d97706;
            --warning-bg: #fffbeb;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --border-color: #e2e8f0;
            --text-color: #334155;
            --text-muted: #64748b;
        }

        body {
            font-family: system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            margin: 0;
            padding: 24px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        h1 {
            color: var(--primary-color);
            font-size: 26px;
            margin-bottom: 8px;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 12px;
        }

        p.subtitle {
            color: var(--text-muted);
            font-size: 15px;
            margin-top: 0;
            margin-bottom: 24px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }

        .stat-num {
            font-size: 36px;
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 4px;
        }

        .stat-label {
            font-size: 14px;
            color: var(--text-muted);
        }

        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            overflow: hidden;
        }

        .audit-table {
            width: 100%;
            border-collapse: collapse;
            text-align: right;
        }

        .audit-table th {
            background-color: #fafafa;
            color: var(--primary-color);
            padding: 14px;
            font-weight: 600;
            border-bottom: 2px solid var(--border-color);
            font-size: 15px;
        }

        .audit-table td {
            padding: 14px;
            border-bottom: 1px solid var(--border-color);
            font-size: 14px;
        }

        .audit-table tbody tr:hover {
            background-color: #fcfcfc;
        }

        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }

        .badge-success {
            background-color: var(--success-bg);
            color: var(--success-color);
            border: 1px solid var(--success-color);
        }

        .badge-warning {
            background-color: var(--warning-bg);
            color: var(--warning-color);
            border: 1px solid var(--warning-color);
        }

        .badge-danger {
            background-color: var(--danger-bg);
            color: var(--danger-color);
            border: 1px solid var(--danger-color);
        }

        .btn {
            display: inline-block;
            padding: 6px 12px;
            background-color: var(--primary-color);
            color: #ffffff;
            text-decoration: none;
            border-radius: 4px;
            font-size: 13px;
        }

        .btn:hover {
            background-color: var(--primary-light);
        }

        .error-row {
            background-color: var(--danger-bg);
        }
        
        .text-danger {
            color: var(--danger-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>ملخص تدقيق ومطابقة الجامعات المستوردة</h1>
        <p class="subtitle">تتم هذه العملية بمقارنة قواعد البيانات المستوردة محلياً بالبيانات الحية على WordPress لتأكيد دقة النقل 100%.</p>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-num">{{ total }}</div>
                <div class="stat-label">إجمالي الجامعات</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">{{ successful }}</div>
                <div class="stat-label">تم التحقق منها بنجاح</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">{{ failed }}</div>
                <div class="stat-label">فشلت مقارنتها (رابط خاطئ أو شبكة)</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">{{ avg_score }}%</div>
                <div class="stat-label">متوسط نسبة تطابق المحتوى</div>
            </div>
        </div>

        <div class="card">
            <table class="audit-table">
                <thead>
                    <tr>
                        <th style="width: 50px;">#</th>
                        <th>اسم الجامعة</th>
                        <th>الرمز التعريفي (Slug)</th>
                        <th>نسبة التطابق</th>
                        <th>الحالة</th>
                        <th>التقرير التفصيلي</th>
                    </tr>
                </thead>
                <tbody>
                    {{ table_rows }}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
