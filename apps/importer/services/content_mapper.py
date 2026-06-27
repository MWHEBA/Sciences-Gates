import re
from django.utils.text import slugify

CITY_MAP = {
    # kl (Kuala Lumpur)
    'كوالالمبور': 'kl',
    'كوالالامبور': 'kl',
    'كوالا لمبور': 'kl',
    'kuala lumpur': 'kl',
    'kl': 'kl',
    
    # selangor (Selangor)
    'سيلانجور': 'selangor',
    'سيلانغور': 'selangor',
    'selangor': 'selangor',
    'سردانج': 'selangor',
    'سردانغ': 'selangor',
    'سيردانغ': 'selangor',
    'serdang': 'selangor',
    'شاه علم': 'selangor',
    'shah alam': 'selangor',
    'سوبانج': 'selangor',
    'سوبانغ': 'selangor',
    'subang': 'selangor',
    'سوبانج جايا': 'selangor',
    'سوبانغ جايا': 'selangor',
    'subang jaya': 'selangor',
    'بانجي': 'selangor',
    'بانغي': 'selangor',
    'bangi': 'selangor',
    'كاجانج': 'selangor',
    'كاجانغ': 'selangor',
    'kajang': 'selangor',
    'سيمينيه': 'selangor',
    'semenyih': 'selangor',
    'كلانج': 'selangor',
    'كلانغ': 'selangor',
    'klang': 'selangor',
    'بيتالينج جايا': 'selangor',
    'بيتالينغ جايا': 'selangor',
    'petaling jaya': 'selangor',
    'pj': 'selangor',
    'سري كيمبانجان': 'selangor',
    'سري كيمبانغان': 'selangor',
    'seri kembangan': 'selangor',
    'سونغاي لونغ': 'selangor',
    'sungai long': 'selangor',
    'صنواي': 'selangor',
    'sunway': 'selangor',
    'بندر صنواي': 'selangor',
    'bandar sunway': 'selangor',
    'دامانسارا': 'selangor',
    'دمنسارا': 'selangor',
    'damansara': 'selangor',
    'غومباك': 'selangor',
    'جومباك': 'selangor',
    'gombak': 'selangor',
    'سوجانا بوترا': 'selangor',
    'saujana putra': 'selangor',
    'saujana': 'selangor',
    'jenjarom': 'selangor',
    'جينجاروم': 'selangor',
    
    # penang (Penang)
    'بينانج': 'penang',
    'بينانغ': 'penang',
    'penang': 'penang',
    'جورج تاون': 'penang',
    'georgetown': 'penang',
    'george town': 'penang',
    
    # putrajaya (Putrajaya)
    'بوتراجايا': 'putrajaya',
    'بتروجايا': 'putrajaya',
    'putrajaya': 'putrajaya',
    
    # cyberjaya (Cyberjaya)
    'سايبرجايا': 'cyberjaya',
    'cyberjaya': 'cyberjaya',
    
    # johor (Johor)
    'جوهر': 'johor',
    'جوهور': 'johor',
    'johor': 'johor',
    'سكوداي': 'johor',
    'اسكوداي': 'johor',
    'skudai': 'johor',
    'جوهر بهرو': 'johor',
    'جوهور بارو': 'johor',
    'johor bahru': 'johor',
    'jb': 'johor',
    'باتو باهات': 'johor',
    'batu pahat': 'johor',
    
    # kedah (Kedah)
    'قدح': 'kedah',
    'kedah': 'kedah',
    'ألو سيتار': 'kedah',
    'alor setar': 'kedah',
    'سينتوت': 'kedah',
    'سينتوك': 'kedah',
    'sintok': 'kedah',
    
    # kelantan (Kelantan)
    'كلنتان': 'kelantan',
    'kelantan': 'kelantan',
    'كوت بهرو': 'kelantan',
    'kota bharu': 'kelantan',
    
    # melaka (Melaka)
    'ملقا': 'melaka',
    'ملكا': 'melaka',
    'ملاكا': 'melaka',
    'melaka': 'melaka',
    'malacca': 'melaka',
    
    # negeri-sembilan (Negeri Sembilan)
    'نيجري سمبيلان': 'negeri-sembilan',
    'negeri sembilan': 'negeri-sembilan',
    'نيلاي': 'negeri-sembilan',
    'nilai': 'negeri-sembilan',
    
    # pahang (Pahang)
    'باهانغ': 'pahang',
    'باهانج': 'pahang',
    'pahang': 'pahang',
    'كونتان': 'pahang',
    'kuantan': 'pahang',
    
    # perak (Perak)
    'بيرق': 'perak',
    'perak': 'perak',
    'إيبوه': 'perak',
    'ipoh': 'perak',
    'كامبار': 'perak',
    'kampar': 'perak',
    'سري اسكندر': 'perak',
    'seri iskandar': 'perak',
    
    # perlis (Perlis)
    'برليس': 'perlis',
    'perlis': 'perlis',
    'أراو': 'perlis',
    'arau': 'perlis',
    
    # sabah (Sabah)
    'صباح': 'sabah',
    'sabah': 'sabah',
    'كوتا كينابالو': 'sabah',
    'kota kinabalu': 'sabah',
    
    # sarawak (Sarawak)
    'سراوق': 'sarawak',
    'ساراواك': 'sarawak',
    'sarawak': 'sarawak',
    'كوتشينغ': 'sarawak',
    'kuching': 'sarawak',
    'ساماراهان': 'sarawak',
    'samarahan': 'sarawak',
    
    # terengganu (Terengganu)
    'ترينجانو': 'terengganu',
    'ترينغانو': 'terengganu',
    'terengganu': 'terengganu',
    'كوالا ترينجانو': 'terengganu',
    'kuala terengganu': 'terengganu',
    'لابوان': 'labuan',
    'labuan': 'labuan',
}

class ContentMapper:
    """Maps WordPress importer JSON payload into the Sciences Gates Django schema."""

    def map_data(self, wp_data: dict, downloaded_images: dict, image_warnings: list) -> dict:
        content_type = wp_data.get('content_type', 'university')
        
        # 1. Map City
        city_raw = wp_data.get('city_raw', '')
        city_slug, city_confidence = self._detect_city_smart(wp_data)

        # 2. Extract values and confidence levels from WP fields structure
        wp_fields = wp_data.get('fields', {})
        
        import urllib.parse
        form_initial = {
            'name': self._clean_importer_name(wp_data.get('name', '')),
            'slug': urllib.parse.unquote(wp_data.get('slug', '')),
            'video_url': wp_data.get('video_url', ''),
            'is_legacy': True,
        }
        
        confidence = {
            'name': 'high',
            'slug': 'high',
            'video_url': 'high' if wp_data.get('video_url') else 'none',
        }

        # Transfer generic mapped fields
        for field_name, field_struct in wp_fields.items():
            form_initial[field_name] = field_struct.get('value', '')
            confidence[field_name] = field_struct.get('confidence', 'none')

        # Add content-type specific defaults
        if content_type == 'university':
            form_initial['university_type'] = wp_data.get('sub_type', 'private')
            form_initial['city'] = city_slug
            confidence['university_type'] = 'high'
            confidence['city'] = city_confidence
            
            # Split combined admission requirements if they are inside the bachelor field
            bachelor_req = form_initial.get('admission_requirements_bachelor', '')
            if bachelor_req:
                split_req = self._split_admission_requirements(bachelor_req)
                if split_req['master'] or split_req['phd']:
                    form_initial['admission_requirements_bachelor'] = split_req['bachelor']
                    
                    # Always overwrite master requirements if we found split requirements for it
                    if split_req['master']:
                        form_initial['admission_requirements_master'] = split_req['master']
                        confidence['admission_requirements_master'] = confidence.get('admission_requirements_bachelor', 'medium')
                        
                    # Always overwrite phd requirements if we found split requirements for it
                    if split_req['phd']:
                        form_initial['admission_requirements_phd'] = split_req['phd']
                        confidence['admission_requirements_phd'] = confidence.get('admission_requirements_bachelor', 'medium')
        elif content_type == 'institute':
            form_initial['institute_type'] = wp_data.get('sub_type', 'academic')
            confidence['institute_type'] = 'high'
        elif content_type == 'major':
            form_initial['major_category'] = wp_data.get('major_category', 'science')
            confidence['major_category'] = 'high'

        # 3. Clean and Truncate SEO Fields
        seo_data = wp_data.get('seo', {})
        
        # We clean them and trim length
        meta_title = seo_data.get('meta_title', '')
        meta_desc = seo_data.get('meta_description', '')
        
        form_initial['meta_title'] = meta_title[:150]
        form_initial['meta_description'] = meta_desc[:160]
        form_initial['focus_keyword'] = seo_data.get('focus_keyword', '')[:100]
        form_initial['keyphrase_synonyms'] = seo_data.get('keyphrase_synonyms', '')[:255]
        form_initial['canonical_url'] = seo_data.get('canonical_url', '')
        form_initial['robots_index'] = seo_data.get('robots_index', True)
        form_initial['robots_follow'] = seo_data.get('robots_follow', True)
        form_initial['sitemap_include'] = True
        
        form_initial['og_title'] = seo_data.get('og_title', meta_title)[:150]
        form_initial['og_description'] = seo_data.get('og_description', meta_desc)[:160]

        # SEO confidence mirrors Yoast source
        seo_fields = ['meta_title', 'meta_description', 'focus_keyword', 'keyphrase_synonyms', 'canonical_url', 'og_title', 'og_description']
        for sf in seo_fields:
            confidence[sf] = 'high' if form_initial.get(sf) else 'none'

        # 4. Process Tags (Ensure they exist and collect their IDs)
        wp_tags = wp_data.get('tags', [])
        tag_ids = []
        if wp_tags:
            from apps.articles.models import Tag
            for tag_name in wp_tags:
                tag_name = tag_name.strip()
                if tag_name:
                    # Check if tag already exists by name (case-insensitive)
                    tag = Tag.objects.filter(name__iexact=tag_name).first()
                    if not tag:
                        base_slug = slugify(tag_name, allow_unicode=True)
                        if not base_slug:
                            base_slug = "tag"
                        
                        slug = base_slug
                        counter = 1
                        while Tag.objects.filter(slug=slug).exists():
                            slug = f"{base_slug}-{counter}"
                            counter += 1
                        
                        tag = Tag.objects.create(name=tag_name, slug=slug)
                    
                    tag_ids.append(tag.id)

        form_initial['tags'] = tag_ids
        confidence['tags'] = 'high' if tag_ids else 'none'

        # 5. Attach Downloaded Images Paths & Hidden Input Fields
        image_paths = {}
        entity_name = form_initial.get('name', '')
        
        for img_type, media_file in downloaded_images.items():
            if media_file:
                image_paths[img_type] = '/media/' + media_file.file.name
                
                # Determine alt field name
                if img_type == 'logo':
                    alt_field = 'logo_alt'
                elif img_type == 'main_image':
                    alt_field = 'main_image_alt'
                elif img_type == 'featured_image':
                    alt_field = 'featured_image_alt'
                else:
                    alt_field = ''
                
                if alt_field:
                    # Use real alt text from WordPress if available
                    if media_file.alt_text and media_file.alt_text.strip():
                        form_initial[alt_field] = media_file.alt_text.strip()
                        confidence[alt_field] = 'high'
                    else:
                        # Auto-generate simple fallback when empty
                        if img_type == 'logo':
                            form_initial[alt_field] = f"شعار {entity_name}" if entity_name else ""
                        elif img_type == 'main_image':
                            form_initial[alt_field] = entity_name if entity_name else ""
                        elif img_type == 'featured_image':
                            form_initial[alt_field] = entity_name if entity_name else ""
                        
                        # Mark confidence as 'generated' for auto-generated alt text
                        confidence[alt_field] = 'generated' if form_initial.get(alt_field) else 'none'
            else:
                image_paths[img_type] = ''

        # Apply justify alignment to specific fields if they exist
        justify_fields = [
            'description',
            'location',
            'admission_requirements_bachelor',
            'admission_requirements_master',
            'admission_requirements_phd'
        ]
        for field in justify_fields:
            if field in form_initial and form_initial[field]:
                form_initial[field] = self._apply_justify(form_initial[field])

        # Prepare redirect target
        from apps.universities.models import University
        from apps.institutes.models import Institute
        from apps.majors.models import Major
        from apps.articles.models import Article

        target_slug = form_initial.get('slug', '').strip()
        
        try:
            if content_type == 'university':
                existing_obj = University.objects.filter(slug=target_slug).first()
                if existing_obj:
                    redirect_url = f'/dashboard/universities/{existing_obj.id}/edit/'
                else:
                    redirect_url = '/dashboard/universities/create/'
            elif content_type == 'institute':
                existing_obj = Institute.objects.filter(slug=target_slug).first()
                if existing_obj:
                    redirect_url = f'/dashboard/institutes/{existing_obj.id}/edit/'
                else:
                    redirect_url = '/dashboard/institutes/create/'
            elif content_type == 'major':
                existing_obj = Major.objects.filter(slug=target_slug).first()
                if existing_obj:
                    redirect_url = f'/dashboard/majors/{existing_obj.id}/edit/'
                else:
                    redirect_url = '/dashboard/majors/create/'
            elif content_type == 'article':
                existing_obj = Article.objects.filter(slug=target_slug).first()
                if existing_obj:
                    redirect_url = f'/dashboard/articles/{existing_obj.id}/edit/'
                else:
                    redirect_url = '/dashboard/articles/create/'
            else:
                redirect_url = '/dashboard/universities/create/'
        except (Exception, AssertionError):
            # Fallback to create view if database queries are forbidden/fail (e.g. in SimpleTestCase)
            if content_type == 'university':
                redirect_url = '/dashboard/universities/create/'
            elif content_type == 'institute':
                redirect_url = '/dashboard/institutes/create/'
            elif content_type == 'major':
                redirect_url = '/dashboard/majors/create/'
            elif content_type == 'article':
                redirect_url = '/dashboard/articles/create/'
            else:
                redirect_url = '/dashboard/universities/create/'

        # Prepare final output structure
        return {
            'form_initial': form_initial,
            'confidence': confidence,
            'faculties_data': wp_data.get('faculties', []),
            'faculties_raw_html': wp_data.get('faculties_raw_html', ''),
            'faqs_data': wp_data.get('faqs', []),
            'faqs_raw_html': wp_data.get('faqs_raw_html', ''),
            'subjects_tables': wp_data.get('subjects_tables', []),
            'salary_tables': wp_data.get('salary_tables', []),
            'countries_tables': wp_data.get('countries_tables', []),
            'image_paths': image_paths,
            'image_warnings': image_warnings,
            'content_type': content_type,
            'city_raw': city_raw,
            'redirect_url': redirect_url,
        }

    def _map_city(self, city_raw: str) -> tuple:
        if not city_raw:
            return '', 'none'
        
        city_raw_clean = city_raw.strip().lower()
        
        # Check exact matches
        if city_raw_clean in CITY_MAP:
            return CITY_MAP[city_raw_clean], 'high'
            
        # Check partial contains matches
        for kw, slug in CITY_MAP.items():
            if kw in city_raw_clean or city_raw_clean in kw:
                return slug, 'high'
                
        return '', 'none'

    def _detect_city_smart(self, wp_data: dict) -> tuple:
        """
        Smart city detection matching keywords from the location paragraph.
        """
        location_html = wp_data.get('fields', {}).get('location', {}).get('value', '')
        
        def normalize_arabic(text):
            text = re.sub(r'[أإآا]', 'ا', text)
            text = re.sub(r'ة', 'ه', text)
            text = re.sub(r'ى', 'ي', text)
            text = re.sub(r'بينانغ', 'بينانج', text)
            text = re.sub(r'بینانغ', 'بينانج', text)
            text = re.sub(r'بینانج', 'بينانج', text)
            return text

        def find_word_in_text(word_norm, text_norm):
            # Enforce word boundary check (Arabic letters and English words)
            pattern = r'(?<![^\W_])' + re.escape(word_norm) + r'(?![^\W_])'
            match = re.search(pattern, text_norm)
            if match:
                return match.start()
            return -1

        # Check location field text first, finding the keyword that appears EARLIEST
        if location_html:
            clean_loc = re.sub(r'<[^>]+>', ' ', location_html).lower()
            clean_loc_norm = normalize_arabic(clean_loc)
            
            earliest_idx = float('inf')
            best_slug = None
            
            for kw, slug in CITY_MAP.items():
                kw_norm = normalize_arabic(kw.lower())
                idx = find_word_in_text(kw_norm, clean_loc_norm)
                if idx != -1 and idx < earliest_idx:
                    earliest_idx = idx
                    best_slug = slug
            if best_slug:
                return best_slug, 'high'
                
        # Fallback to city_raw from WP
        city_raw = wp_data.get('city_raw', '')
        if city_raw:
            city_slug, city_confidence = self._map_city(city_raw)
            if city_slug:
                return city_slug, 'medium'
                
        return 'kl', 'none'


    def _split_admission_requirements(self, html_content: str) -> dict:
        """
        Splits combined admission requirements HTML into Bachelor's, Master's, and PhD stages.
        Preserves all HTML tags and formatting, removing stage headers and intro text.
        """
        if not html_content:
            return {'bachelor': '', 'master': '', 'phd': ''}

        # Match opening and closing tags for block level elements (h1-h6, p, div)
        tag_rx = re.compile(r'<(h[1-6]|p|div)\b[^>]*>(.*?)</\1>', re.IGNORECASE | re.DOTALL)
        
        matches = []
        for match in tag_rx.finditer(html_content):
            full_tag = match.group(0)
            inner_content = match.group(2)
            # Remove inner HTML tags to get clean plain text
            clean_text = re.sub(r'<[^>]+>', '', inner_content).strip()
            
            # Header tags must be reasonably short to avoid matching full description paragraphs
            if len(clean_text) < 80:
                clean_text_lower = clean_text.lower()
                
                # Exclude keywords that specify subheaders (e.g. language requirements, academic requirements)
                exclude_keywords = ['لغة', 'language', 'أكاديمية', 'academic', 'سنوات', 'duration', 'رسوم', 'fees']
                if any(kw in clean_text_lower for kw in exclude_keywords):
                    continue
                
                has_bachelor = any(kw in clean_text_lower for kw in ['بكالوريوس', 'bachelor'])
                has_master = any(kw in clean_text_lower for kw in ['ماجستير', 'master'])
                has_phd = any(kw in clean_text_lower for kw in ['دكتوراه', 'phd', 'doctorate'])
                
                if has_bachelor or has_master or has_phd:
                    # Semantic keywords indicating it's a section header, or if it's very short (just the name)
                    header_keywords = ['برنامج', 'شروط', 'قبول', 'متطلبات', 'مرحلة', 'دراسة', 
                                       'program', 'admission', 'requirements', 'study', 'degree', 'course']
                    is_short_or_has_kw = len(clean_text) < 35 or any(kw in clean_text_lower for kw in header_keywords)
                    
                    if is_short_or_has_kw:
                        if has_phd:
                            stage = 'phd'
                        elif has_master:
                            stage = 'master'
                        else:
                            stage = 'bachelor'
                            
                        matches.append({
                            'start': match.start(),
                            'end': match.end(),
                            'stage': stage,
                            'text': clean_text
                        })

        # Remove nested/overlapping matches (e.g. <div><h3>Header</h3></div>)
        filtered_matches = []
        last_end = -1
        for match in sorted(matches, key=lambda x: x['start']):
            if match['start'] >= last_end:
                filtered_matches.append(match)
                last_end = match['end']

        if not filtered_matches:
            return {'bachelor': html_content, 'master': '', 'phd': ''}

        result = {'bachelor': '', 'master': '', 'phd': ''}
        
        # Identify if we have a bachelor header in matches
        has_bachelor_header = any(m['stage'] == 'bachelor' for m in filtered_matches)
        
        # Handle content before the first header
        first_header_start = filtered_matches[0]['start']
        pre_content = self._strip_html_content(html_content[:first_header_start])
        
        if pre_content and not has_bachelor_header:
            # If no bachelor header is present, the pre-content is the bachelor section
            result['bachelor'] = pre_content

        # Process each match and extract content between them
        for idx, match in enumerate(filtered_matches):
            stage = match['stage']
            start_pos = match['end']
            end_pos = filtered_matches[idx+1]['start'] if idx + 1 < len(filtered_matches) else len(html_content)
            
            content = self._strip_html_content(html_content[start_pos:end_pos])
            
            if result[stage]:
                result[stage] += "\n" + content
            else:
                result[stage] = content
        return result

    def _strip_html_content(self, html: str) -> str:
        """
        Strips leading/trailing whitespaces, empty HTML tags (<p></p>, <p>&nbsp;</p>, etc.),
        breaks (<br/>), and non-breaking spaces (&nbsp;) repeatedly.
        """
        if not html:
            return ""
        
        while True:
            original = html
            html = html.strip()
            
            # Strip leading empty elements
            html = re.sub(r'^(?:<p>\s*(?:&nbsp;)*\s*</p>|<div[^>]*>\s*</div>|<br\s*/?>|&nbsp;|\s)+', '', html, flags=re.IGNORECASE)
            # Strip trailing empty elements
            html = re.sub(r'(?:<p>\s*(?:&nbsp;)*\s*</p>|<div[^>]*>\s*</div>|<br\s*/?>|&nbsp;|\s)+$', '', html, flags=re.IGNORECASE)
            
            if html == original:
                break
                
        return html

    def _clean_importer_name(self, name: str) -> str:
        """
        Cleans the institutional/major name by taking everything before the first separator
        (|, -, –, —, :).
        Strips trailing and leading whitespaces, and removes dates/years if present.
        """
        if not name:
            return ""
        
        # Replace common dash variants and colon with a standard character to split easily
        normalized = name.replace('–', '|').replace('—', '|').replace('-', '|').replace(':', '|')
        if "|" in normalized:
            name = normalized.split("|", 1)[0].strip()
        else:
            name = name.strip()
            
        # Remove date/year patterns (e.g. 2024, 2023-2024, (2024), ٢٠٢٤, etc.)
        # Order matters: check ranges first, then single years.
        year_range_western = r'(?:19|20)\d{2}\s*[-/]\s*(?:(?:19|20)\d{2}|\d{2})'
        year_range_eastern = r'(?:[١٢][٩٠][٠-٩]{2})\s*[-/]\s*(?:(?:[١٢][٩٠][٠-٩]{2})|[٠-٩]{2})'
        single_year_western = r'(?:19|20)\d{2}'
        single_year_eastern = r'(?:[١٢][٩٠][٠-٩]{2})'
        
        date_pat = f"(?:{year_range_western}|{year_range_eastern}|{single_year_western}|{single_year_eastern})"
        
        # Matches (2024), [2024], {2024}, etc.
        pattern_with_parens = (
            r"\([\s]*" + date_pat + r"[\s]*\)|" +
            r"\{[\s]*" + date_pat + r"[\s]*\}|" +
            r"\[[\s]*" + date_pat + r"[\s]*\]"
        )
        
        # Combined pattern with optional prefix words like "سنة" or "عام" or "لعام"
        combined_pattern = r"(?:سنة|عام|لعام|year|for year)?\s*(?:" + pattern_with_parens + "|" + date_pat + ")"
        
        # Remove the date/year
        cleaned = re.sub(combined_pattern, "", name)
        
        # Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Clean up empty/stray parentheses or brackets or dashes that might be left over
        cleaned = cleaned.strip()
        cleaned = re.sub(r'^[-–—:|]+|[-–—:|]+$', '', cleaned)
        
        return cleaned.strip()

    def _apply_justify(self, html_content: str) -> str:
        """
        Wraps HTML content in a div with text-align: justify; styling.
        """
        if not html_content or not html_content.strip():
            return html_content
        
        # Avoid wrapping if it is already wrapped or has justify styling
        if 'text-align: justify' in html_content or 'text-align:justify' in html_content:
            return html_content
            
        return f'<div style="text-align: justify;">{html_content}</div>'




