"""
Search utilities for building search queries using Django ORM Q objects and Full Text Search.
"""
from django.db.models import Q
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article

import re

# Arabic Stop Words
ARABIC_STOP_WORDS = {
    'في', 'من', 'على', 'عن', 'إلى', 'مع', 'أو', 'هو', 'هي', 'أن', 'أن', 'و',
    'ثم', 'ثم', 'يا', 'هذا', 'هذه', 'ذلك', 'التي', 'الذي', 'الذين', 'لكن',
    'كان', 'كانت', 'يكون', 'حتى', 'غير', 'كل', 'بعض', 'بين', 'عند', 'بعد',
    'قبل', 'منذ', 'لقد', 'قد', 'إن', 'انه', 'إنها', 'انها', 'كما', 'مثل'
}


def normalize_arabic(text):
    """
    Normalize Arabic text for search.
    - Converts English to lowercase.
    - Removes Arabic diacritics (tashkeel).
    - Normalizes Alef forms to bare Alef (أ, إ, آ -> ا).
    - Normalizes Teh Marbuta to Heh (ة -> ه).
    - Normalizes Yeh/Maksura to Yeh (ى -> ي).
    - Strips 'ال' prefix from Arabic words if the word is long enough.
    """
    if not text:
        return ""
    
    text = text.strip().lower()
    
    # Remove Arabic diacritics
    tashkeel = re.compile(r'[\u064B-\u0652\u0640]')
    text = tashkeel.sub('', text)
    
    # Normalize Arabic letters
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    
    # Strip 'ال' prefix only if word is long enough to prevent false positives on roots
    words = []
    for word in text.split():
        if word.startswith('ال') and len(word) >= 5:
            word = word[2:]
        words.append(word)
        
    return ' '.join(words)


def get_db_search_variations(word):
    """
    Generate common Arabic spelling variations of a word for database Q search.
    Includes prefix-based variation for typo tolerance on words of length >= 5.
    """
    if not word:
        return []
    
    variations = {word}
    
    # Remove 'ال' prefix if word is long enough
    has_al = False
    cleaned_word = word
    if word.startswith('ال') and len(word) >= 5:
        cleaned_word = word[2:]
        variations.add(cleaned_word)
        has_al = True
        
    # Generate variations for the base word
    base_variations = {cleaned_word}
    
    # 1. Alef at start
    if cleaned_word.startswith(('ا', 'أ', 'إ', 'آ')):
        suffix = cleaned_word[1:]
        for prefix in ('ا', 'أ', 'إ', 'آ'):
            base_variations.add(prefix + suffix)
            
    # 2. Teh Marbuta / Heh at end
    temp_vars = list(base_variations)
    for v in temp_vars:
        if v.endswith(('ة', 'ه')):
            prefix = v[:-1]
            for suffix in ('ة', 'ه'):
                base_variations.add(prefix + suffix)
                
    # 3. Yeh / Alef Maksura at end
    temp_vars = list(base_variations)
    for v in temp_vars:
        if v.endswith(('ي', 'ى')):
            prefix = v[:-1]
            for suffix in ('ي', 'ى'):
                base_variations.add(prefix + suffix)

    # 4. Generate prefix of length 4 for typo tolerance (only if the cleaned word has length >= 5)
    # This enables matching "البرمجبات" to "البرمجيات" by searching for "برمج" in the DB.
    if len(cleaned_word) >= 5:
        prefix_4 = cleaned_word[:4]
        base_variations.add(prefix_4)
        if prefix_4.startswith(('ا', 'أ', 'إ', 'آ')):
            suffix = prefix_4[1:]
            for p in ('ا', 'أ', 'إ', 'آ'):
                base_variations.add(p + suffix)

    # Add all base variations, and if original word had 'ال', add them with 'ال' prefix too
    for bv in list(base_variations):
        variations.add(bv)
        if has_al:
            variations.add('ال' + bv)
            
    return list(variations)


def edit_distance(s1, s2):
    """
    Calculate the Levenshtein distance between two strings.
    """
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]


def word_similarity(w1, w2):
    """
    Calculate similarity between two normalized words.
    Returns a float between 0.0 and 1.0.
    """
    dist = edit_distance(w1, w2)
    max_len = max(len(w1), len(w2))
    if max_len == 0:
        return 1.0
    return 1.0 - (dist / max_len)


def score_text(text, query_words, weight=1.0, fuzzy=True):
    """
    Score a text against query words.
    - exact word match: 100 * weight
    - substring match: 60 * weight
    - fuzzy match: 40 * similarity * weight (if fuzzy=True)
    """
    if not text:
        return 0
        
    norm_text = normalize_arabic(text)
    if not norm_text:
        return 0
        
    text_words = norm_text.split()
    score = 0
    
    for q_word in query_words:
        if not q_word:
            continue
            
        # 1. Exact match in text words
        if q_word in text_words:
            score += 100 * weight
            continue
            
        # 2. Substring match
        if q_word in norm_text:
            score += 60 * weight
            continue
            
        # 3. Fuzzy match (only if fuzzy=True)
        if fuzzy:
            for t_word in text_words:
                if abs(len(q_word) - len(t_word)) <= 2 and len(q_word) >= 3 and len(t_word) >= 3:
                    sim = word_similarity(q_word, t_word)
                    if sim >= 0.75:
                        score += (40 * sim) * weight
                        break
                        
    return score


def build_search_query(query_string, filters=None):
    """
    Build a smart search query across University, Institute, Major, and Article models.
    
    Uses database-level broad Q-filtering followed by Python-based scoring and ranking.
    """
    if not query_string or not query_string.strip():
        return {
            'universities': [],
            'institutes': [],
            'majors': [],
            'articles': [],
            'total_count': 0,
        }
    
    filters = filters or {}
    query_string = query_string.strip()
    
    # 1. Normalize query and extract search terms (excluding stop words)
    words = [re.sub(r'[^\w\s]', '', w).strip() for w in query_string.split()]
    words = [w for w in words if w]
    
    query_words = [normalize_arabic(w) for w in words if normalize_arabic(w) not in ARABIC_STOP_WORDS]
    if not query_words:
        query_words = [normalize_arabic(w) for w in words]
        
    # 2. Get variations for database icontains query
    db_terms = []
    for w in words:
        if w not in ARABIC_STOP_WORDS:
            db_terms.extend(get_db_search_variations(w))
            
    if not db_terms:
        for w in words:
            db_terms.extend(get_db_search_variations(w))
            
    db_terms = list(dict.fromkeys(db_terms))
    
    # 3. Fetch candidates from database using OR queries on the generated terms
    # Universities
    uni_q = Q()
    for term in db_terms:
        uni_q |= Q(name__icontains=term) | Q(slug__icontains=term) | Q(description__icontains=term)
        
    universities = University.objects.filter(uni_q, publish_status='published')
    
    if filters.get('university_type'):
        universities = universities.filter(university_type=filters['university_type'])
    if filters.get('min_tuition'):
        universities = universities.filter(tuition_fees__gte=filters['min_tuition'])
    if filters.get('max_tuition'):
        universities = universities.filter(tuition_fees__lte=filters['max_tuition'])
        
    universities = list(universities.prefetch_related('related_majors', 'related_articles'))
    
    # Institutes
    inst_q = Q()
    for term in db_terms:
        inst_q |= Q(name__icontains=term) | Q(slug__icontains=term) | Q(description__icontains=term)
        
    institutes = Institute.objects.filter(inst_q, publish_status='published')
    
    if filters.get('institute_type'):
        institutes = institutes.filter(institute_type=filters['institute_type'])
        
    institutes = list(institutes.prefetch_related('related_articles'))
    
    # Majors
    major_q = Q()
    for term in db_terms:
        major_q |= Q(name__icontains=term) | Q(slug__icontains=term) | Q(description__icontains=term)
        
    majors = Major.objects.filter(major_q, publish_status='published')
    
    if filters.get('major_category'):
        from apps.majors.models import MajorCategory
        try:
            target_cat = MajorCategory.objects.get(slug=filters['major_category'])
            majors = majors.filter(category=target_cat)
        except MajorCategory.DoesNotExist:
            majors = majors.none()
            
    if filters.get('study_language'):
        majors = majors.filter(study_language=filters['study_language'])
        
    majors = list(majors.prefetch_related('best_universities', 'cheap_universities', 'related_articles'))
    
    # Articles
    art_q = Q()
    for term in db_terms:
        art_q |= Q(title__icontains=term) | Q(slug__icontains=term) | Q(content__icontains=term)
        
    articles = Article.objects.filter(art_q, publish_status='published')
    articles = list(articles.select_related('category', 'author').prefetch_related(
        'tags', 'related_universities', 'related_institutes', 'related_majors'
    ))
    
    # 4. Calculate search scores and sort/rank
    scored_universities = []
    for uni in universities:
        score = 0
        score += score_text(uni.name, query_words, weight=3.0, fuzzy=True)
        score += score_text(uni.location, query_words, weight=1.5, fuzzy=True)
        score += score_text(uni.slug, query_words, weight=1.0, fuzzy=True)
        score += score_text(uni.description, query_words, weight=1.0, fuzzy=False)
        if score > 0:
            scored_universities.append((score, uni))
            
    scored_institutes = []
    for inst in institutes:
        score = 0
        score += score_text(inst.name, query_words, weight=3.0, fuzzy=True)
        score += score_text(inst.slug, query_words, weight=1.0, fuzzy=True)
        score += score_text(inst.description, query_words, weight=1.0, fuzzy=False)
        if score > 0:
            scored_institutes.append((score, inst))
            
    scored_majors = []
    for major in majors:
        score = 0
        score += score_text(major.name, query_words, weight=3.0, fuzzy=True)
        score += score_text(major.slug, query_words, weight=1.0, fuzzy=True)
        score += score_text(major.description, query_words, weight=1.0, fuzzy=False)
        if score > 0:
            scored_majors.append((score, major))
            
    scored_articles = []
    for article in articles:
        score = 0
        score += score_text(article.title, query_words, weight=3.0, fuzzy=True)
        score += score_text(article.slug, query_words, weight=1.0, fuzzy=True)
        score += score_text(article.content, query_words, weight=1.0, fuzzy=False)
        if score > 0:
            scored_articles.append((score, article))
            
    # Sort and pick top 20
    scored_universities.sort(key=lambda x: x[0], reverse=True)
    scored_institutes.sort(key=lambda x: x[0], reverse=True)
    scored_majors.sort(key=lambda x: x[0], reverse=True)
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    
    top_universities = [uni for _, uni in scored_universities[:20]]
    top_institutes = [inst for _, inst in scored_institutes[:20]]
    top_majors = [major for _, major in scored_majors[:20]]
    top_articles = [art for _, art in scored_articles[:20]]
    
    total_count = len(scored_universities) + len(scored_institutes) + len(scored_majors) + len(scored_articles)
    
    return {
        'universities': top_universities,
        'institutes': top_institutes,
        'majors': top_majors,
        'articles': top_articles,
        'total_count': total_count,
    }


def get_excerpt(text, max_length=150):
    """
    Get an excerpt from text, truncating at word boundary.
    """
    if not text:
        return ''
    
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        return truncated[:last_space] + '...'
    
    return truncated + '...'
