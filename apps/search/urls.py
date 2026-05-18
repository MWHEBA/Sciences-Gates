"""
URL configuration for the search app.
"""
from django.urls import path
from .views import SearchView

app_name = 'search'

urlpatterns = [
    path('', SearchView.as_view(), name='results'),
]
