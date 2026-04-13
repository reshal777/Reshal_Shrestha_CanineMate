"""
URL configuration for CanineMate project.
"""

from django.contrib import admin
from django.urls import path, include
from home import views as home_views
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include("admin_app.urls")),
    path("", home_views.index_view, name="index"),
    path("home/", include("home.urls")),
    path("", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
