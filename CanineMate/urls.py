"""
URL configuration for CanineMate project.
"""

from django.contrib import admin
from django.urls import path, include
from home import views as home_views
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include("admin_app.urls")),
    path("", home_views.index_view, name="index"),
    path("home/", include("home.urls")),
    path("", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
    # Password reset confirm (used by reset email link)
    path(
        "accounts/password-reset/confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html",
            success_url="/accounts/password-reset/complete/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
