"""
URL configuration for science_gates project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from apps.core.views import HomeView
from apps.seo.views import robots_txt
from apps.seo.sitemaps import sitemaps

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('dashboard/', include('apps.dashboard.urls')),
    path('universities/', include('apps.universities.urls')),
    path('institutes/', include('apps.institutes.urls')),
    path('majors/', include('apps.majors.urls')),
    path('articles/', include('apps.articles.urls')),
    path('leads/', include('apps.leads.urls')),
    path('search/', include('apps.search.urls')),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
