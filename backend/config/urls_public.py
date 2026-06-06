"""
URLs acessíveis no schema público (tenant management).
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/tenants/", include("apps.tenants.urls")),
    path("api/v1/superadmin/", include("apps.superadmin.urls")),
    # Dev convenience: auth endpoints also accessible from public schema
    path("api/v1/", include("config.urls_tenant")),
]
