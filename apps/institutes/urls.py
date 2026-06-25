"""
URL configuration for institutes app.
"""
from django.urls import path
from . import views

app_name = 'institutes'

urlpatterns = [
    path('', views.InstituteListView.as_view(), name='list'),
    path('type/<str:type>/', views.InstituteTypeListView.as_view(), name='type_list'),
    path('<str:slug>/', views.InstituteDetailView.as_view(), name='detail'),
]
