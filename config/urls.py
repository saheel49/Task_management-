"""
Task Manager URL Configuration

The `urlpatterns` list routes URLs to views.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.users.views import CustomPasswordResetView
from apps.web.sitemaps import StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap(),
}

handler404 = "apps.web.views.page_not_found"
handler403 = "django.views.defaults.permission_denied"
handler500 = "apps.web.views.server_error"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("accounts/password/reset/", CustomPasswordResetView.as_view(), name="account_reset_password"),
    path("accounts/", include("allauth.urls")),
    # Users
    path("users/", include("apps.users.urls")),
    # Dashboard
    path("dashboard/", include("apps.dashboard.urls")),
    # Website
    path("", include("apps.web.urls")),
    # Celery Progress
    path("celery-progress/", include("celery_progress.urls")),
    # API Schema
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # Tasks
    path("tasks/", include("tasks.urls")),
]

# Serve uploaded media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Browser reload
if "django_browser_reload.middleware.BrowserReloadMiddleware" in settings.MIDDLEWARE:
    urlpatterns.insert(
        0,
        path("__reload__/", include("django_browser_reload.urls")),
    )

# Debug toolbar
if settings.ENABLE_DEBUG_TOOLBAR:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
