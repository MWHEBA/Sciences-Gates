"""
URL configuration for leads app.
"""
from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    path('submit/', views.LeadSubmitView.as_view(), name='submit'),
    path('thank-you/', views.thank_you_view, name='thank_you'),
]
