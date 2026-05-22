"""
Django mixins for automatic breadcrumb injection.

Mixins that automatically inject breadcrumbs into template context.
Views override get_breadcrumbs() to define the trail.
"""

from typing import List
from .breadcrumbs import Breadcrumb


class BreadcrumbMixin:
    """
    Mixin that automatically injects breadcrumbs into template context.
    
    Override get_breadcrumbs() in your view to define the trail.
    
    Usage:
        class UniversityDetailView(BreadcrumbMixin, DetailView):
            def get_breadcrumbs(self):
                return (BreadcrumbTrail()
                    .add_section('home')
                    .add_section('universities')
                    .current(self.object.name)
                    .build())
    """

    def get_breadcrumbs(self) -> List[Breadcrumb]:
        """
        Override this in your view to define the breadcrumb trail.
        
        Returns:
            List of Breadcrumb objects from BreadcrumbTrail.build()
        """
        return []

    def get_context_data(self, **kwargs):
        """Inject breadcrumbs into context."""
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context


class DashboardBreadcrumbMixin(BreadcrumbMixin):
    """
    Mixin for dashboard views with automatic breadcrumb injection.
    
    Same as BreadcrumbMixin but with dashboard-specific defaults.
    Currently identical to BreadcrumbMixin, but allows for future
    dashboard-specific behavior.
    """
    pass
