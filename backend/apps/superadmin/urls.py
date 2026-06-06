from django.urls import path
from .views import TenantListView

urlpatterns = [
    path("tenants/", TenantListView.as_view(), name="superadmin-tenants"),
]
