from django.urls import path
from . import views

urlpatterns = [
    path('', views.ImportPageView.as_view(), name='import_page'),
    path('fetch/', views.ImportFetchView.as_view(), name='import_fetch'),
    path('bulk-save/', views.ImportBulkSaveAPIView.as_view(), name='import_bulk_save'),
    path('save-draft/', views.ImportSaveDraftView.as_view(), name='import_save_draft'),
    path('status/<uuid:job_id>/', views.ImportJobStatusView.as_view(), name='import_job_status'),
]
