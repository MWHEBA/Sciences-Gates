"""
URL configuration for majors app.
"""
from django.urls import path
from . import views

app_name = 'majors'

urlpatterns = [
    path('', views.MajorListView.as_view(), name='list'),
    path('category/<str:category>/', views.MajorCategoryListView.as_view(), name='category_list'),
    path('<slug:slug>/', views.MajorDetailView.as_view(), name='detail'),
]
