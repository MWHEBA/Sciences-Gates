"""
URL configuration for the dashboard app.
"""
from django.urls import path, include
from . import views
from apps.seo import views as seo_views

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.DashboardLoginView.as_view(), name='login'),
    path('logout/', views.DashboardLogoutView.as_view(), name='logout'),
    path('', views.DashboardHomeView.as_view(), name='home'),
    
    # User management (Super Admin only)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    
    # Redirect management (SEO Admin)
    path('redirects/', views.RedirectListView.as_view(), name='redirect_list'),
    path('redirects/create/', views.RedirectCreateView.as_view(), name='redirect_create'),
    path('redirects/<int:pk>/edit/', views.RedirectUpdateView.as_view(), name='redirect_edit'),
    path('redirects/<int:pk>/delete/', views.RedirectDeleteView.as_view(), name='redirect_delete'),
    
    # University management (Content Admin)
    path('universities/', views.UniversityListView.as_view(), name='university_list'),
    path('universities/create/', views.UniversityCreateView.as_view(), name='university_create'),
    path('universities/<int:pk>/edit/', views.UniversityUpdateView.as_view(), name='university_edit'),
    path('universities/<int:pk>/delete/', views.UniversityDeleteView.as_view(), name='university_delete'),
    path('universities/bulk-action/', views.UniversityBulkActionView.as_view(), name='university_bulk_action'),
    
    # Faculty management (Content Admin)
    path('universities/<int:university_id>/faculties/', views.FacultyListView.as_view(), name='faculty_list'),
    path('universities/<int:university_id>/faculties/create/', views.FacultyCreateView.as_view(), name='faculty_create'),
    path('faculties/<int:pk>/edit/', views.FacultyUpdateView.as_view(), name='faculty_edit'),
    path('faculties/<int:pk>/delete/', views.FacultyDeleteView.as_view(), name='faculty_delete'),
    
    # Institute management (Content Admin)
    path('institutes/', views.InstituteListView.as_view(), name='institute_list'),
    path('institutes/create/', views.InstituteCreateView.as_view(), name='institute_create'),
    path('institutes/<int:pk>/edit/', views.InstituteUpdateView.as_view(), name='institute_edit'),
    path('institutes/<int:pk>/delete/', views.InstituteDeleteView.as_view(), name='institute_delete'),
    path('institutes/bulk-action/', views.InstituteBulkActionView.as_view(), name='institute_bulk_action'),
    
    # Major management (Content Admin)
    path('majors/', views.MajorListView.as_view(), name='major_list'),
    path('majors/create/', views.MajorCreateView.as_view(), name='major_create'),
    path('majors/<int:pk>/edit/', views.MajorUpdateView.as_view(), name='major_edit'),
    path('majors/<int:pk>/delete/', views.MajorDeleteView.as_view(), name='major_delete'),
    path('majors/bulk-action/', views.MajorBulkActionView.as_view(), name='major_bulk_action'),
    
    # Category management (Content Admin)
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Tag management (Content Admin)
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('tags/create/', views.TagCreateView.as_view(), name='tag_create'),
    path('tags/<int:pk>/edit/', views.TagUpdateView.as_view(), name='tag_edit'),
    path('tags/<int:pk>/delete/', views.TagDeleteView.as_view(), name='tag_delete'),
    
    # Article management (Content Admin)
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('articles/create/', views.ArticleCreateView.as_view(), name='article_create'),
    path('articles/<int:pk>/edit/', views.ArticleUpdateView.as_view(), name='article_edit'),
    path('articles/<int:pk>/delete/', views.ArticleDeleteView.as_view(), name='article_delete'),
    path('articles/bulk-action/', views.ArticleBulkActionView.as_view(), name='article_bulk_action'),
    
    # Lead management (Content Admin)
    path('leads/', views.LeadListView.as_view(), name='lead_list'),
    path('leads/export/', views.LeadExportView.as_view(), name='lead_export'),
    path('leads/<int:pk>/', views.LeadDetailView.as_view(), name='lead_detail'),
    
    # SEO management (SEO Admin)
    path('seo/overview/', views.SEOOverviewView.as_view(), name='seo_overview'),
    path('seo/analyze/<str:content_type>/<int:pk>/', seo_views.dashboard_analyze_seo, name='seo_analyze'),
    path('seo/detail/<str:content_type>/<int:pk>/', seo_views.dashboard_seo_detail, name='seo_detail'),
    
    # Draft Preview System
    path('preview/article/<int:pk>/', views.PreviewArticleDetailView.as_view(), name='preview_article'),
    path('preview/university/<int:pk>/', views.PreviewUniversityDetailView.as_view(), name='preview_university'),
    path('preview/institute/<int:pk>/', views.PreviewInstituteDetailView.as_view(), name='preview_institute'),
    path('preview/major/<int:pk>/', views.PreviewMajorDetailView.as_view(), name='preview_major'),
    
    # General Settings (Super Admin)
    path('settings/', views.SiteSettingsUpdateView.as_view(), name='settings'),
    
    # Editor uploads
    path('editor/upload-image/', views.EditorImageUploadView.as_view(), name='editor_upload_image'),
    
    # Media library management
    path('media/', views.MediaLibraryView.as_view(), name='media_library'),
    path('media/find-by-url/', views.MediaFileFindByUrlView.as_view(), name='media_find_by_url'),
    path('media/bulk-delete/', views.MediaFileBulkDeleteView.as_view(), name='media_bulk_delete'),
    path('media/<int:pk>/update/', views.MediaFileUpdateView.as_view(), name='media_update'),
    path('media/<int:pk>/delete/', views.MediaFileDeleteView.as_view(), name='media_delete'),
    
    # WordPress Importer
    path('import/', include('apps.importer.urls')),
]
