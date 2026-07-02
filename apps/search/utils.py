"""
Search utilities for building search queries using Django ORM Q objects and Full Text Search.
"""
from django.db.models import Q
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article

# Try to import Full Text Search components (PostgreSQL only)
try:
    from django.db.models import SearchVector, SearchRank, SearchQuery
    HAS_FTS = True
except ImportError:
    HAS_FTS = False


def build_search_query(query_string, filters=None):
    """
    Build a search query across University, Institute, Major, and Article models.
    
    Uses PostgreSQL Full Text Search if available, otherwise falls back to icontains.
    
    Searches in the following fields:
    - University: name, slug, description
    - Institute: name, slug, description
    - Major: name, slug, description
    - Article: title, slug, content
    
    Args:
        query_string (str): The search query string
        filters (dict): Optional filters for advanced search
        
    Returns:
        dict: A dictionary containing search results for each content type
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
    query = query_string.strip()
    
    # Try to use Full Text Search if available
    use_fts = False
    search_query = None
    if HAS_FTS:
        try:
            search_query = SearchQuery(query, search_type='websearch')
            use_fts = True
        except:
            use_fts = False
    
    # Search Universities
    if use_fts and search_query:
        search_vector = SearchVector('name', weight='A') + SearchVector('description', weight='B')
        universities = University.objects.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(
            search=search_query,
            publish_status='published'
        ).order_by('-rank')
    else:
        universities = University.objects.filter(
            Q(name__icontains=query) |
            Q(slug__icontains=query) |
            Q(description__icontains=query),
            publish_status='published'
        ).order_by('name')
    
    # Apply university type filter
    if filters.get('university_type'):
        universities = universities.filter(university_type=filters['university_type'])
    
    # Apply tuition filter
    if filters.get('min_tuition'):
        universities = universities.filter(tuition_fees__gte=filters['min_tuition'])
    if filters.get('max_tuition'):
        universities = universities.filter(tuition_fees__lte=filters['max_tuition'])
    
    universities = universities.prefetch_related(
        'related_majors',
        'related_articles'
    )[:20]
    
    # Search Institutes
    if use_fts and search_query:
        search_vector = SearchVector('name', weight='A') + SearchVector('description', weight='B')
        institutes = Institute.objects.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(
            search=search_query,
            publish_status='published'
        ).order_by('-rank')
    else:
        institutes = Institute.objects.filter(
            Q(name__icontains=query) |
            Q(slug__icontains=query) |
            Q(description__icontains=query),
            publish_status='published'
        ).order_by('name')
    
    # Apply institute type filter
    if filters.get('institute_type'):
        institutes = institutes.filter(institute_type=filters['institute_type'])
    
    institutes = institutes.prefetch_related(
        'related_articles'
    )[:20]
    
    # Search Majors
    if use_fts and search_query:
        search_vector = SearchVector('name', weight='A') + SearchVector('description', weight='B')
        majors = Major.objects.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(
            search=search_query,
            publish_status='published'
        ).order_by('-rank')
    else:
        majors = Major.objects.filter(
            Q(name__icontains=query) |
            Q(slug__icontains=query) |
            Q(description__icontains=query),
            publish_status='published'
        ).order_by('name')
    
    # Apply major category filter
    if filters.get('major_category'):
        from apps.majors.models import MajorCategory
        try:
            target_cat = MajorCategory.objects.get(slug=filters['major_category'])
            majors = majors.filter(category=target_cat)
        except MajorCategory.DoesNotExist:
            majors = majors.none()
    
    # Apply language filter
    if filters.get('study_language'):
        majors = majors.filter(study_language=filters['study_language'])
    
    # Apply tuition filter
    if filters.get('min_tuition'):
        majors = majors.filter(tuition_fees__gte=filters['min_tuition'])
    if filters.get('max_tuition'):
        majors = majors.filter(tuition_fees__lte=filters['max_tuition'])
    
    majors = majors.prefetch_related(
        'best_universities',
        'cheap_universities',
        'related_articles'
    )[:20]
    
    # Search Articles
    if use_fts and search_query:
        search_vector = SearchVector('title', weight='A') + SearchVector('content', weight='B')
        articles = Article.objects.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(
            search=search_query,
            publish_status='published'
        ).order_by('-rank')
    else:
        articles = Article.objects.filter(
            Q(title__icontains=query) |
            Q(slug__icontains=query) |
            Q(content__icontains=query),
            publish_status='published'
        ).order_by('-created_at')
    
    articles = articles.select_related(
        'category', 'author'
    ).prefetch_related(
        'tags',
        'related_universities',
        'related_institutes',
        'related_majors'
    )[:20]
    
    # Calculate total count
    total_count = len(universities) + len(institutes) + len(majors) + len(articles)
    
    return {
        'universities': list(universities),
        'institutes': list(institutes),
        'majors': list(majors),
        'articles': list(articles),
        'total_count': total_count,
    }


def get_excerpt(text, max_length=150):
    """
    Get an excerpt from text, truncating at word boundary.
    
    Args:
        text (str): The text to excerpt
        max_length (int): Maximum length of excerpt
        
    Returns:
        str: The excerpt with ellipsis if truncated
    """
    if not text:
        return ''
    
    if len(text) <= max_length:
        return text
    
    # Truncate at max_length and find last space
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        return truncated[:last_space] + '...'
    
    return truncated + '...'
