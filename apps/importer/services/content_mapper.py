import re
from django.utils.text import slugify

CITY_MAP = {
    # kl (Kuala Lumpur)
    'كوالالمبور': ('kl', 'kl'),
    'كوالالامبور': ('kl', 'kl'),
    'كوالا لمبور': ('kl', 'kl'),
    'kuala lumpur': ('kl', 'kl'),
    'kl': ('kl', 'kl'),
    
    # selangor (Selangor)
    'سيلانجور': ('selangor', 'other-selangor'),
    'سيلانغور': ('selangor', 'other-selangor'),
    'selangor': ('selangor', 'other-selangor'),
    'سردانج': ('selangor', 'serdang'),
    'سردانغ': ('selangor', 'serdang'),
    'سيردانغ': ('selangor', 'serdang'),
    'serdang': ('selangor', 'serdang'),
    'شاه علم': ('selangor', 'shah-alam'),
    'shah alam': ('selangor', 'shah-alam'),
    'سوبانج': ('selangor', 'subang-jaya'),
    'سوبانغ': ('selangor', 'subang-jaya'),
    'subang': ('selangor', 'subang-jaya'),
    'سوبانج جايا': ('selangor', 'subang-jaya'),
    'سوبانغ جايا': ('selangor', 'subang-jaya'),
    'subang jaya': ('selangor', 'subang-jaya'),
    'بانجي': ('selangor', 'bangi'),
    'بانغي': ('selangor', 'bangi'),
    'bangi': ('selangor', 'bangi'),
    'كاجانج': ('selangor', 'kajang'),
    'كاجانغ': ('selangor', 'kajang'),
    'kajang': ('selangor', 'kajang'),
    'سيمينيه': ('selangor', 'semenyih'),
    'semenyih': ('selangor', 'semenyih'),
    'كلانج': ('selangor', 'klang'),
    'كلانغ': ('selangor', 'klang'),
    'klang': ('selangor', 'klang'),
    'بيتالينج جايا': ('selangor', 'petaling-jaya'),
    'بيتالينغ جايا': ('selangor', 'petaling-jaya'),
    'petaling jaya': ('selangor', 'petaling-jaya'),
    'pj': ('selangor', 'petaling-jaya'),
    'سري كيمبانجان': ('selangor', 'seri-kembangan'),
    'سري كيمبانغان': ('selangor', 'seri-kembangan'),
    'seri kembangan': ('selangor', 'seri-kembangan'),
    'سونغاي لونغ': ('selangor', 'sungai-long'),
    'sungai long': ('selangor', 'sungai-long'),
    'صنواي': ('selangor', 'bandar-sunway'),
    'sunway': ('selangor', 'bandar-sunway'),
    'بندر صنواي': ('selangor', 'bandar-sunway'),
    'bandar sunway': ('selangor', 'bandar-sunway'),
    'دامانسارا': ('selangor', 'damansara'),
    'دمنسارا': ('selangor', 'damansara'),
    'damansara': ('selangor', 'damansara'),
    'غومباك': ('selangor', 'gombak'),
    'جومباك': ('selangor', 'gombak'),
    'gombak': ('selangor', 'gombak'),
    'سوجانا بوترا': ('selangor', 'saujana-putra'),
    'saujana putra': ('selangor', 'saujana-putra'),
    'saujana': ('selangor', 'saujana-putra'),
    'jenjarom': ('selangor', 'jenjarom'),
    'جينجاروم': ('selangor', 'jenjarom'),
    
    # penang (Penang)
    'بينانج': ('penang', 'other-penang'),
    'بينانغ': ('penang', 'other-penang'),
    'penang': ('penang', 'other-penang'),
    'جورج تاون': ('penang', 'georgetown'),
    'georgetown': ('penang', 'georgetown'),
    'george town': ('penang', 'georgetown'),
    
    # putrajaya (Putrajaya)
    'بوتراجايا': ('putrajaya', 'putrajaya'),
    'بتروجايا': ('putrajaya', 'putrajaya'),
    'putrajaya': ('putrajaya', 'putrajaya'),
    
    # cyberjaya (Cyberjaya) - mapped under Selangor
    'سايبرجايا': ('selangor', 'cyberjaya'),
    'cyberjaya': ('selangor', 'cyberjaya'),
    
    # johor (Johor)
    'جوهر': ('johor', 'other-johor'),
    'جوهور': ('johor', 'other-johor'),
    'johor': ('johor', 'other-johor'),
    'سكوداي': ('johor', 'skudai'),
    'اسكوداي': ('johor', 'skudai'),
    'skudai': ('johor', 'skudai'),
    'جوهر بهرو': ('johor', 'johor-bahru'),
    'جوهور بارو': ('johor', 'johor-bahru'),
    'johor bahru': ('johor', 'johor-bahru'),
    'jb': ('johor', 'johor-bahru'),
    'باتو باهات': ('johor', 'batu-pahat'),
    'batu pahat': ('johor', 'batu-pahat'),
    
    # kedah (Kedah)
    'قدح': ('kedah', 'other-kedah'),
    'kedah': ('kedah', 'other-kedah'),
    'ألو سيتار': ('kedah', 'alor-setar'),
    'alor setar': ('kedah', 'alor-setar'),
    'سينتوت': ('kedah', 'sintok'),
    'سينتوك': ('kedah', 'sintok'),
    'sintok': ('kedah', 'sintok'),
    
    # kelantan (Kelantan)
    'كلنتان': ('kelantan', 'other-kelantan'),
    'kelantan': ('kelantan', 'other-kelantan'),
    'كوت بهرو': ('kelantan', 'kota-bharu'),
    'kota bharu': ('kelantan', 'kota-bharu'),
    
    # melaka (Melaka)
    'ملقا': ('melaka', 'melaka'),
    'ملكا': ('melaka', 'melaka'),
    'ملاكا': ('melaka', 'melaka'),
    'melaka': ('melaka', 'melaka'),
    'malacca': ('melaka', 'melaka'),
    
    # negeri-sembilan (Negeri Sembilan)
    'نيجري سمبيلان': ('negeri-sembilan', 'other-negeri-sembilan'),
    'negeri sembilan': ('negeri-sembilan', 'other-negeri-sembilan'),
    'نيلاي': ('negeri-sembilan', 'nilai'),
    'nilai': ('negeri-sembilan', 'nilai'),
    
    # pahang (Pahang)
    'باهانغ': ('pahang', 'other-pahang'),
    'باهانج': ('pahang', 'other-pahang'),
    'pahang': ('pahang', 'other-pahang'),
    'كونتان': ('pahang', 'kuantan'),
    'kuantan': ('pahang', 'kuantan'),
    
    # perak (Perak)
    'بيرق': ('perak', 'other-perak'),
    'perak': ('perak', 'other-perak'),
    'إيبوه': ('perak', 'ipoh'),
    'ipoh': ('perak', 'ipoh'),
    'كامبار': ('perak', 'kampar'),
    'kampar': ('perak', 'kampar'),
    'سري اسكندر': ('perak', 'seri-iskandar'),
    'seri iskandar': ('perak', 'seri-iskandar'),
    
    # perlis (Perlis)
    'برليس': ('perlis', 'other-perlis'),
    'perlis': ('perlis', 'other-perlis'),
    'أراو': ('perlis', 'kangar'),
    'arau': ('perlis', 'kangar'),
    
    # sabah (Sabah)
    'صباح': ('sabah', 'other-sabah'),
    'sabah': ('sabah', 'other-sabah'),
    'كوتا كينابالو': ('sabah', 'kota-kinabalu'),
    'kota kinabalu': ('sabah', 'kota-kinabalu'),
    
    # sarawak (Sarawak)
    'سراوق': ('sarawak', 'other-sarawak'),
    'ساراواك': ('sarawak', 'other-sarawak'),
    'sarawak': ('sarawak', 'other-sarawak'),
    'كوتشينغ': ('sarawak', 'kuching'),
    'kuching': ('sarawak', 'kuching'),
    'ساماراهان': ('sarawak', 'kuching'),
    'samarahan': ('sarawak', 'kuching'),
    
    # terengganu (Terengganu)
    'ترينجانو': ('terengganu', 'other-terengganu'),
    'ترينغانو': ('terengganu', 'other-terengganu'),
    'terengganu': ('terengganu', 'other-terengganu'),
    'كوالا ترينجانو': ('terengganu', 'kuala-terengganu'),
    'kuala terengganu': ('terengganu', 'kuala-terengganu'),
    'لابوان': ('labuan', 'labuan'),
    'labuan': ('labuan', 'labuan'),
}

class ContentMapper:
    """Maps WordPress importer JSON payload into the Sciences Gates Django schema."""

    def map_data(self, wp_data: dict, downloaded_images: dict, image_warnings: list) -> dict:
        content_type = wp_data.get('content_type', 'university')
        
        # 1. Map City
        city_raw = wp_data.get('city_raw', '')
        (state_slug, city_slug), city_confidence = self._detect_city_smart(wp_data)

        # 2. Extract values and confidence levels from WP fields structure
        wp_fields = wp_data.get('fields', {})
        
        import urllib.parse
        form_initial = {
            'name': self._clean_importer_name(wp_data.get('name', '')),
            'slug': urllib.parse.unquote(wp_data.get('slug', '')),
            'video_url': wp_data.get('video_url', ''),
            'is_legacy': False,
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
            form_initial['state'] = state_slug
            form_initial['city'] = city_slug
            form_initial['one_time_fees'] = []
            confidence['university_type'] = 'high'
            confidence['state'] = city_confidence
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
            form_initial['state'] = state_slug
            form_initial['city'] = city_slug
            confidence['state'] = city_confidence
            confidence['city'] = city_confidence
        elif content_type == 'major':
            form_initial['major_category'] = wp_data.get('major_category', 'science')
            confidence['major_category'] = 'high'
        elif content_type == 'article':
            # Map title and content for articles
            form_initial['title'] = form_initial.get('name', '')
            confidence['title'] = confidence.get('name', 'high')
            
            # WP maps article content into 'description' field under university/institute mapping
            description_val = form_initial.get('description', '')
            content_val = form_initial.get('content', '')
            
            raw_content = content_val or description_val
            
            if raw_content:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(raw_content, 'html.parser')
                
                # 1. Clean boilerplate call-to-action/social links at the end
                has_boilerplate = 'إذا كنت مهتم' in raw_content or 'تابعونا' in raw_content
                if has_boilerplate:
                    block_tags = {'p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section', 'article', 'pre', 'blockquote', 'table', 'tr', 'td', 'ul', 'ol'}
                    
                    target_node = None
                    for element in soup.find_all(string=re.compile(r"(إذا كنت مهتم|تابعونا)")):
                        curr = element
                        while curr and curr.parent:
                            if curr.name in block_tags or curr.parent.name is None:
                                break
                            curr = curr.parent
                        target_node = curr
                        if target_node:
                            break
                            
                    if target_node:
                        siblings_to_remove = []
                        curr = target_node
                        while curr:
                            siblings_to_remove.append(curr)
                            curr = curr.next_sibling
                            
                        for sibling in siblings_to_remove:
                            if hasattr(sibling, 'decompose'):
                                sibling.decompose()
                                
                # 2. Clean empty lines / empty paragraphs
                for tag in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    text = tag.get_text(strip=True)
                    text = text.replace('\xa0', '').replace('&nbsp;', '').strip()
                    if not text and not tag.find(['img', 'iframe', 'table', 'ul', 'ol', 'li']):
                        tag.decompose()
                        
                # 3. Standardize tables: convert first row of any table to proper thead/th if it doesn't already have a header
                for table in soup.find_all('table'):
                    # Skip if the table already has a thead or th elements
                    if table.find('thead') or table.find('th'):
                        continue
                        
                    rows = table.find_all('tr')
                    if rows:
                        first_row = rows[0]
                        tds = first_row.find_all('td')
                        if tds:
                            thead = soup.new_tag('thead')
                            table.insert(0, thead)
                            thead.append(first_row)
                            for td in tds:
                                th = soup.new_tag('th')
                                for child in list(td.contents):
                                    th.append(child)
                                td.replace_with(th)
                                
                # 4. Format "البرامج المعتمدة" column as bullets if separated by commas
                for table in soup.find_all('table'):
                    headers = table.find_all('th')
                    prog_col_idx = -1
                    for idx, th in enumerate(headers):
                        th_text = th.get_text().strip()
                        if "البرامج" in th_text:
                            prog_col_idx = idx
                            break
                            
                    if prog_col_idx != -1:
                        rows = table.find_all('tr')
                        for row in rows[1:]:
                            cells = row.find_all('td')
                            if len(cells) > prog_col_idx:
                                cell = cells[prog_col_idx]
                                text = cell.get_text().strip()
                                items = [item.strip() for item in re.split(r'[،,]', text) if item.strip()]
                                if len(items) > 1:
                                    ul = soup.new_tag('ul')
                                    for item in items:
                                        li = soup.new_tag('li')
                                        li.string = item
                                        ul.append(li)
                                    cell.clear()
                                    cell.append(ul)
                                    
                # 5. Strip inline font-size and font-family styles from all elements
                for el in soup.find_all(style=True):
                    style_str = el['style']
                    props = [p.strip() for p in style_str.split(';') if p.strip()]
                    new_props = []
                    for prop in props:
                        if ':' in prop:
                            name, val = prop.split(':', 1)
                            if name.strip().lower() not in ('font-size', 'font-family'):
                                new_props.append(prop)
                    if new_props:
                        el['style'] = '; '.join(new_props) + ';'
                    else:
                        del el['style']
                        
                # 6. Replace #0000ff (pure blue) with var(--primary) in inline styles and font tags
                for el in soup.find_all(style=True):
                    style_str = el['style']
                    new_style = re.sub(r'#0000ff', 'var(--primary)', style_str, flags=re.IGNORECASE)
                    new_style = re.sub(r'rgb\(\s*0\s*,\s*0\s*,\s*255\s*\)', 'var(--primary)', new_style, flags=re.IGNORECASE)
                    if new_style != style_str:
                        el['style'] = new_style

                for font in soup.find_all('font', color=True):
                    if font['color'].strip().lower() in ('#0000ff', 'blue'):
                        font['style'] = font.get('style', '') + '; color: var(--primary);'
                        del font['color']
                        
                raw_content = str(soup)
            
            form_initial['content'] = raw_content
            confidence['content'] = confidence.get('content', confidence.get('description', 'medium'))

            # Resolve Category ForeignKey
            wp_categories = wp_data.get('categories', [])
            if wp_categories:
                from apps.articles.models import Category
                matched_cat = None
                for cat_name in wp_categories:
                    cat_name = cat_name.strip()
                    if cat_name:
                        matched_cat = Category.objects.filter(name__iexact=cat_name).first()
                        if matched_cat:
                            break
                
                if not matched_cat and wp_categories:
                    first_cat_name = wp_categories[0].strip()
                    if first_cat_name:
                        cat_slug = slugify(first_cat_name, allow_unicode=True)
                        if not cat_slug:
                            cat_slug = "category"
                        
                        unique_slug = cat_slug
                        counter = 1
                        while Category.objects.filter(slug=unique_slug).exists():
                            unique_slug = f"{cat_slug}-{counter}"
                            counter += 1
                        
                        matched_cat = Category.objects.create(name=first_cat_name, slug=unique_slug)
                
                if matched_cat:
                    form_initial['category'] = matched_cat.id
                    confidence['category'] = 'high'


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
            'introduction',
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

        courses_data = []
        faqs_data = wp_data.get('faqs', [])

        if content_type == 'institute':
            courses_by_duration = {}
            faq_list = []
            
            # Start with standard faqs
            for faq in wp_data.get('faqs', []):
                faq_list.append({
                    'question': faq.get('question', ''),
                    'answer': faq.get('answer', ''),
                })
                
            for item in wp_data.get('faculties', []):
                name = item.get('name', '').strip()
                programs = item.get('programs', [])
                
                # Check if it's an FAQ item
                is_faq = '؟' in name or '?' in name or (
                    len(programs) == 1 and 
                    programs[0].get('duration') == 'غير محدد' and 
                    programs[0].get('tuition_fees') == 'غير محدد'
                )
                
                if is_faq:
                    ans = programs[0].get('name', '').strip() if programs else ''
                    faq_list.append({
                        'question': name,
                        'answer': ans,
                    })
                else:
                    # It's a courses table
                    lower_name = name.lower()
                    currency = 'usd'
                    if any(x in lower_name for x in ['myr', 'rm', 'رنجت', 'ماليزي']):
                        currency = 'myr'
                    elif any(x in lower_name for x in ['sar', 'ريال', 'سعودي']):
                        currency = 'sar'
                    elif any(x in lower_name for x in ['usd', 'دولار', '$']):
                        currency = 'usd'
                        
                    for prog in programs:
                        dur = prog.get('name', '').strip()
                        fee_val = prog.get('duration', '').strip()
                        visa_val = prog.get('tuition_fees', '').strip()
                        section = prog.get('section', '').strip()
                        
                        if not dur:
                            continue
                            
                        # Clean fee_val (extract digits, commas, dots)
                        cleaned_fee = re.sub(r'[^\d\.,]', '', fee_val).strip()
                        if not cleaned_fee:
                            cleaned_fee = fee_val
                            
                        # Detect course_type based on section name
                        course_type = 'undefined'
                        sec_lower = section.lower()
                        if any(x in sec_lower for x in ['6 ساعات', '6 hours', '٦ ساعات']):
                            course_type = 'super_intensive'
                        elif any(x in sec_lower for x in ['مكثف', 'intensive', '5 ساعات', '5 hours', '٥ ساعات']):
                            course_type = 'intensive'
                        elif any(x in sec_lower for x in ['عادي', 'regular', '4 ساعات', '4 hours', '٤ ساعات']):
                            course_type = 'regular'
                            
                        # Use a tuple key of (duration, course_type) to support multiple course types
                        key = (dur, course_type)
                        if key not in courses_by_duration:
                            courses_by_duration[key] = {
                                'duration': dur,
                                'course_type': course_type,
                                'fees_myr': '',
                                'fees_usd': '',
                                'fees_sar': '',
                                'visa_duration': '',
                            }
                            
                        if currency == 'myr':
                            courses_by_duration[key]['fees_myr'] = cleaned_fee
                        elif currency == 'usd':
                            courses_by_duration[key]['fees_usd'] = cleaned_fee
                        elif currency == 'sar':
                            courses_by_duration[key]['fees_sar'] = cleaned_fee
                            
                        if visa_val and visa_val != 'غير محدد':
                            courses_by_duration[key]['visa_duration'] = visa_val
            
            # Fill missing fees_myr with USD estimation (approx. 1 USD = 4.7 MYR)
            for key, c_info in courses_by_duration.items():
                if not c_info['fees_myr'] and c_info['fees_usd']:
                    try:
                        usd_val = float(c_info['fees_usd'].replace(',', ''))
                        c_info['fees_myr'] = f"{int(usd_val * 4.7):,}"
                    except ValueError:
                        pass
                        
            courses_data = list(courses_by_duration.values())
            faqs_data = faq_list

        # Prepare final output structure
        return {
            'form_initial': form_initial,
            'confidence': confidence,
            'faculties_data': wp_data.get('faculties', []),
            'faculties_raw_html': wp_data.get('faculties_raw_html', ''),
            'faqs_data': faqs_data,
            'faqs_raw_html': wp_data.get('faqs_raw_html', ''),
            'subjects_tables': wp_data.get('subjects_tables', []),
            'salary_tables': wp_data.get('salary_tables', []),
            'countries_tables': wp_data.get('countries_tables', []),
            'courses_data': courses_data,
            'image_paths': image_paths,
            'image_warnings': image_warnings,
            'content_type': content_type,
            'city_raw': city_raw,
            'redirect_url': redirect_url,
            'created_at': wp_data.get('created_at'),
        }

    def _map_city(self, city_raw: str) -> tuple:
        if not city_raw:
            return ('', ''), 'none'
        
        city_raw_clean = city_raw.strip().lower()
        
        # Check exact matches
        if city_raw_clean in CITY_MAP:
            return CITY_MAP[city_raw_clean], 'high'
            
        # Check partial contains matches
        for kw, slug_pair in CITY_MAP.items():
            if kw in city_raw_clean or city_raw_clean in kw:
                return slug_pair, 'high'
                
        return ('', ''), 'none'

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
            if city_slug[0]:
                return city_slug, 'medium'
                
        return ('kl', 'kl'), 'none'


    def _split_admission_requirements(self, html_content: str) -> dict:
        """
        Splits combined admission requirements HTML into Bachelor's, Master's, and PhD stages.
        Uses h3 headers as primary markers, with a regex-based keyword splitting fallback.
        """
        if not html_content:
            return {'bachelor': '', 'master': '', 'phd': ''}

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all h3 elements
        h3s = soup.find_all('h3')
        
        # Check if we have valid stage h3 tags
        stages = {}
        for h3 in h3s:
            text = h3.get_text().lower()
            if 'بكالوريوس' in text or 'bachelor' in text:
                stages['bachelor'] = h3
            elif 'ماجستير' in text or 'master' in text:
                stages['master'] = h3
            elif 'دكتوراه' in text or 'phd' in text or 'doctorate' in text:
                stages['phd'] = h3
                
        # If we have at least master or phd headers, split by inserting comment markers
        if 'master' in stages or 'phd' in stages or 'bachelor' in stages:
            for h3 in h3s:
                text = h3.get_text().lower()
                if 'بكالوريوس' in text or 'bachelor' in text:
                    h3.replace_with(soup.new_string('<!-- STAGE_BACHELOR -->'))
                elif 'ماجستير' in text or 'master' in text:
                    h3.replace_with(soup.new_string('<!-- STAGE_MASTER -->'))
                elif 'دكتوراه' in text or 'phd' in text or 'doctorate' in text:
                    h3.replace_with(soup.new_string('<!-- STAGE_PHD -->'))
            
            modified_html = str(soup)
            
            pos_bachelor = modified_html.find('<!-- STAGE_BACHELOR -->')
            pos_master = modified_html.find('<!-- STAGE_MASTER -->')
            pos_phd = modified_html.find('<!-- STAGE_PHD -->')
            
            markers = []
            if pos_bachelor != -1:
                markers.append((pos_bachelor, 'bachelor', len('<!-- STAGE_BACHELOR -->')))
            if pos_master != -1:
                markers.append((pos_master, 'master', len('<!-- STAGE_MASTER -->')))
            if pos_phd != -1:
                markers.append((pos_phd, 'phd', len('<!-- STAGE_PHD -->')))
                
            markers.sort(key=lambda x: x[0])
            
            if markers:
                result = {'bachelor': '', 'master': '', 'phd': ''}
                first_pos, first_stage, first_len = markers[0]
                intro_content = modified_html[:first_pos].strip()
                
                # Prepend intro content to bachelor stage by default
                if intro_content:
                    result['bachelor'] = intro_content
                    
                current_pos = first_pos + first_len
                active_stage = first_stage
                
                for idx in range(1, len(markers)):
                    next_pos, next_stage, next_len = markers[idx]
                    segment = modified_html[current_pos:next_pos]
                    
                    if result[active_stage]:
                        result[active_stage] += segment
                    else:
                        result[active_stage] = segment
                        
                    current_pos = next_pos + next_len
                    active_stage = next_stage
                    
                segment = modified_html[current_pos:]
                if result[active_stage]:
                    result[active_stage] += segment
                else:
                    result[active_stage] = segment
                    
                for stage in result:
                    result[stage] = self._strip_html_content(result[stage])
                    
                return result

        # Fallback to the original regex block-level splitter
        return self._split_admission_requirements_fallback(html_content)

    def _split_admission_requirements_fallback(self, html_content: str) -> dict:
        """Original regex keyword splitter fallback."""
        # Match opening and closing tags for block level elements (h1-h6, p, div)
        tag_rx = re.compile(r'<(h[1-6]|p|div)\b[^>]*>(.*?)</\1>', re.IGNORECASE | re.DOTALL)
        
        matches = []
        for match in tag_rx.finditer(html_content):
            full_tag = match.group(0)
            inner_content = match.group(2)
            clean_text = re.sub(r'<[^>]+>', '', inner_content).strip()
            
            if len(clean_text) < 80:
                clean_text_lower = clean_text.lower()
                exclude_keywords = ['لغة', 'language', 'أكاديمية', 'academic', 'سنوات', 'duration', 'رسوم', 'fees']
                if any(kw in clean_text_lower for kw in exclude_keywords):
                    continue
                
                has_bachelor = any(kw in clean_text_lower for kw in ['بكالوريوس', 'bachelor'])
                has_master = any(kw in clean_text_lower for kw in ['ماجستير', 'master'])
                has_phd = any(kw in clean_text_lower for kw in ['دكتوراه', 'phd', 'doctorate'])
                
                if has_bachelor or has_master or has_phd:
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

        filtered_matches = []
        last_end = -1
        for match in sorted(matches, key=lambda x: x['start']):
            if match['start'] >= last_end:
                filtered_matches.append(match)
                last_end = match['end']

        if not filtered_matches:
            return {'bachelor': html_content, 'master': '', 'phd': ''}

        result = {'bachelor': '', 'master': '', 'phd': ''}
        has_bachelor_header = any(m['stage'] == 'bachelor' for m in filtered_matches)
        first_header_start = filtered_matches[0]['start']
        pre_content = self._strip_html_content(html_content[:first_header_start])
        
        if pre_content and not has_bachelor_header:
            result['bachelor'] = pre_content

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




