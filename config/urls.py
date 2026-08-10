"""
URL configuration for science_gates project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from apps.core.views import HomeView, AboutView, VisaTrackingView, LegacyUrlDetailView, PrivacyView, TermsView
from apps.seo.views import robots_txt, indexnow_key_view
from apps.seo.sitemaps import sitemaps
from apps.articles.views import AuthorDetailView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about-us/', AboutView.as_view(), name='about_us'),
    path('visa-tracking/', VisaTrackingView.as_view(), name='visa_tracking'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    path('terms/', TermsView.as_view(), name='terms'),
    # Canonical author bio URL — referenced in JSON-LD schema and article bylines
    path('author/<str:slug>/', AuthorDetailView.as_view(), name='author_detail'),

    path(settings.ADMIN_URL, admin.site.urls),
    path(settings.DASHBOARD_URL, include('apps.dashboard.urls')),
    path('universities/', include('apps.universities.urls')),
    path('institutes/', include('apps.institutes.urls')),
    path('majors/', include('apps.majors.urls')),
    path('articles/', include('apps.articles.urls')),
    path('leads/', include('apps.leads.urls')),
    path('search/', include('apps.search.urls')),
    path('robots.txt', robots_txt, name='robots_txt'),
    path(f'{getattr(settings, "INDEXNOW_KEY", "c7a8b9f0e1d2c3b4a5f6e7d8c9b0a1f2")}.txt', indexnow_key_view, name='indexnow_key'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    re_path(r'^(?P<slug>[^/]+)/$', LegacyUrlDetailView.as_view(), name='legacy_detail'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
