"""
URL configuration for institutes app.
"""
from django.urls import path
from . import views

app_name = 'institutes'

urlpatterns = [
    path('', views.InstituteListView.as_view(), name='list'),
    path('type/<str:type>/', views.InstituteTypeListView.as_view(), name='type_list'),
    path('tag/<str:slug>/', views.TagInstituteListView.as_view(), name='tag'),
    path('<str:slug>/', views.InstituteDetailView.as_view(), name='detail'),
]
