"""
Superadmin views — listagem e gestão de tenants.
Acesso restrito: only IsAdminUser (Django staff).
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from apps.tenants.models import Tenant


class TenantListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        tenants = Tenant.objects.values(
            "id", "name", "schema_name", "plano", "status",
            "cnpj", "created_on",
        )
        return Response(list(tenants))
