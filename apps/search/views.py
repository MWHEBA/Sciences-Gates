"""
Search views for searching across content types.
"""
from django.shortcuts import render
from django.views.generic import FormView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse_lazy
from .forms import SearchForm, AdvancedSearchForm
from .utils import build_search_query, get_excerpt


class SearchView(FormView):
    """
    View for searching across University, Institute, Major, and Article models.
    
    Displays search results with pagination (20 items per page).
    Supports Arabic search queries.
    """
    form_class = SearchForm
    template_name = 'search/results.html'
    success_url = reverse_lazy('search:results')
    
    def get_context_data(self, **kwargs):
        """Add search results to context."""
        context = super().get_context_data(**kwargs)
        
        # Get search query from GET or POST
        query = self.request.GET.get('query', '') or self.request.POST.get('query', '')
        
        # Build filters from GET parameters
        filters = {
            'university_type': self.request.GET.get('university_type', ''),
            'institute_type': self.request.GET.get('institute_type', ''),
            'major_category': self.request.GET.get('major_category', ''),
            'study_language': self.request.GET.get('study_language', ''),
            'min_tuition': self.request.GET.get('min_tuition', ''),
            'max_tuition': self.request.GET.get('max_tuition', ''),
        }
        
        # Remove empty filters
        filters = {k: v for k, v in filters.items() if v}
        
        if query:
            # Build search results with filters
            results = build_search_query(query, filters)
            
            # Prepare paginated results
            all_results = []
            
            # Add universities with type label
            for uni in results['universities']:
                all_results.append({
                    'type': 'university',
                    'type_label': 'جامعة',
                    'name': uni['name'],
                    'slug': uni['slug'],
                    'excerpt': get_excerpt(uni['description']),
                    'url': f"/universities/{uni['slug']}/",
                })
            
            # Add institutes with type label
            for inst in results['institutes']:
                all_results.append({
                    'type': 'institute',
                    'type_label': 'معهد',
                    'name': inst['name'],
                    'slug': inst['slug'],
                    'excerpt': get_excerpt(inst['description']),
                    'url': f"/institutes/{inst['slug']}/",
                })
            
            # Add majors with type label
            for major in results['majors']:
                all_results.append({
                    'type': 'major',
                    'type_label': 'تخصص',
                    'name': major['name'],
                    'slug': major['slug'],
                    'excerpt': get_excerpt(major['description']),
                    'url': f"/majors/{major['slug']}/",
                })
            
            # Add articles with type label
            for article in results['articles']:
                all_results.append({
                    'type': 'article',
                    'type_label': 'مقالة',
                    'name': article['title'],
                    'slug': article['slug'],
                    'excerpt': get_excerpt(article['content']),
                    'category': article['category__name'],
                    'url': f"/articles/{article['slug']}/",
                })
            
            # Paginate results
            paginator = Paginator(all_results, 20)
            page = self.request.GET.get('page', 1)
            
            try:
                paginated_results = paginator.page(page)
            except PageNotAnInteger:
                paginated_results = paginator.page(1)
            except EmptyPage:
                paginated_results = paginator.page(paginator.num_pages)
            
            context['query'] = query
            context['results'] = paginated_results
            context['total_count'] = results['total_count']
            context['has_results'] = results['total_count'] > 0
            context['filters'] = filters
        else:
            context['query'] = ''
            context['results'] = None
            context['total_count'] = 0
            context['has_results'] = False
            context['filters'] = {}
        
        return context
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests with query parameter."""
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form))
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests and redirect to GET with query parameter."""
        form = self.get_form()
        if form.is_valid():
            query = form.cleaned_data['query']
            return self.render_to_response(self.get_context_data(form=form))
        return self.form_invalid(form)
