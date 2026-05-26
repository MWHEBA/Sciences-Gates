"""
URL configuration for universities app.
"""
from django.urls import path, re_path
from . import views

app_name = 'universities'

urlpatterns = [
    path('', views.UniversityListView.as_view(), name='list'),
    path('type/<str:type>/', views.UniversityTypeListView.as_view(), name='type_list'),
    re_path(r'^(?P<slug>[\w-]+)/$', views.UniversityDetailView.as_view(), name='detail'),
]
