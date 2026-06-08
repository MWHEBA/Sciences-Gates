from django.urls import path
from . import views

urlpatterns = [
    path('', views.ImportPageView.as_view(), name='import_page'),
    path('fetch/', views.ImportFetchView.as_view(), name='import_fetch'),
]
