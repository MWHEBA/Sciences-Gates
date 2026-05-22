"""
Breadcrumb unified object and registry.

This module provides:
- SECTION_URLS: Single source of truth for all breadcrumb URLs
- Breadcrumb: Canonical dataclass for breadcrumb items
- BreadcrumbTrail: Builder for validated breadcrumb trails
"""

from dataclasses import dataclass
from typing import Optional, List
from django.urls import reverse, NoReverseMatch


# Layer 1 — URL Registry
# Single source of truth for all breadcrumb URLs
# If a URL changes in urls.py, update it here once
SECTION_URLS = {
    # Public sections
    'home':         ('الرئيسية',   'home'),
    'universities': ('الجامعات',   'universities:list'),
    'institutes':   ('المعاهد',    'institutes:list'),
    'majors':       ('التخصصات',   'majors:list'),
    'articles':     ('المقالات',   'articles:list'),
    
    # Dashboard sections
    'dashboard':    ('لوحة التحكم', 'dashboard:home'),
    'dash_universities': ('الجامعات', 'dashboard:university_list'),
    'dash_institutes':   ('المعاهد',  'dashboard:institute_list'),
    'dash_majors':       ('التخصصات', 'dashboard:major_list'),
    'dash_articles':     ('المقالات', 'dashboard:article_list'),
    'dash_faculties':    ('الكليات',  'dashboard:faculty_list'),
}


# Layer 2 — Breadcrumb Object
@dataclass
class Breadcrumb:
    """
    Canonical breadcrumb item with validation.
    
    Attributes:
        name: Display text (required, non-empty)
        url: Link URL (None for current page)
    """
    name: str
    url: Optional[str] = None

    def __post_init__(self):
        """Validate breadcrumb on creation."""
        if not self.name or not self.name.strip():
            raise ValueError("Breadcrumb name cannot be empty")

    def is_current(self) -> bool:
        """Check if this is the current page (no URL)."""
        return self.url is None

    def to_dict(self) -> dict:
        """Convert to dict for template rendering."""
        return {'name': self.name, 'url': self.url}

    def to_schema_dict(self) -> dict:
        """Convert to dict for JSON-LD schema."""
        return {'name': self.name, 'url': self.url}


class BreadcrumbTrail:
    """
    Builder for validated, immutable breadcrumb trails.
    
    The last item should always be the current page (url=None).
    
    Usage:
        trail = (BreadcrumbTrail()
            .add_section('home')
            .add_section('universities')
            .current('University Name')
            .build())
    """

    def __init__(self):
        """Initialize empty trail."""
        self._items: List[Breadcrumb] = []

    def add_section(self, section_key: str) -> 'BreadcrumbTrail':
        """
        Add a predefined section from SECTION_URLS registry.
        
        Args:
            section_key: Key in SECTION_URLS dict
            
        Returns:
            self for method chaining
            
        Raises:
            KeyError: If section_key not in SECTION_URLS
        """
        if section_key not in SECTION_URLS:
            raise KeyError(
                f"Unknown section key: '{section_key}'. "
                f"Available keys: {', '.join(SECTION_URLS.keys())}"
            )
        
        name, url_name = SECTION_URLS[section_key]
        try:
            url = reverse(url_name)
        except NoReverseMatch:
            # Fallback to home if URL name not found
            url = '/'
        
        self._items.append(Breadcrumb(name=name, url=url))
        return self

    def add(self, name: str, url: Optional[str] = None) -> 'BreadcrumbTrail':
        """
        Add a custom item (not from registry).
        
        Args:
            name: Display text
            url: Link URL (None for current page)
            
        Returns:
            self for method chaining
        """
        self._items.append(Breadcrumb(name=name, url=url))
        return self

    def current(self, name: str) -> 'BreadcrumbTrail':
        """
        Add the current page (no URL). Should be the last item.
        
        Args:
            name: Display text for current page
            
        Returns:
            self for method chaining
        """
        self._items.append(Breadcrumb(name=name, url=None))
        return self

    def build(self) -> List[Breadcrumb]:
        """
        Return the validated trail.
        
        Returns:
            List of Breadcrumb objects
            
        Raises:
            ValueError: If trail is empty
        """
        if not self._items:
            raise ValueError(
                "BreadcrumbTrail is empty. "
                "Call add_section(), add(), or current() first."
            )
        return list(self._items)

    @staticmethod
    def from_legacy(legacy_data) -> 'BreadcrumbTrail':
        """
        Convert legacy breadcrumb format to BreadcrumbTrail.
        
        Supports:
        - List of tuples: [('name', '/url/'), ('current', None)]
        - List of dicts: [{'name': 'x', 'url': '/x/'}, {'title': 'y', 'url': None}]
        
        Args:
            legacy_data: Old breadcrumb format
            
        Returns:
            BreadcrumbTrail instance
        """
        trail = BreadcrumbTrail()
        
        if not legacy_data:
            return trail
        
        for item in legacy_data:
            if isinstance(item, tuple):
                # Tuple format: (name, url)
                name, url = item
                trail.add(name, url)
            elif isinstance(item, dict):
                # Dict format: {'name': '...', 'url': '...'} or {'title': '...', 'url': '...'}
                name = item.get('name') or item.get('title', '')
                url = item.get('url')
                trail.add(name, url)
            else:
                raise ValueError(f"Unsupported breadcrumb format: {type(item)}")
        
        return trail
