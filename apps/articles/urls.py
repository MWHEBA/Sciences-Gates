"""
URL configuration for articles app.
"""
from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='list'),
    path('category/<str:slug>/', views.CategoryArticleListView.as_view(), name='category'),
    path('tag/<str:slug>/', views.TagArticleListView.as_view(), name='tag'),
    path('<str:slug>/', views.ArticleDetailView.as_view(), name='detail'),
]
