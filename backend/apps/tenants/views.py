from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAdminUser

from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "schema_name", "name", "trade_name", "cnpj", "plan", "status", "created_at"]
        read_only_fields = ["id", "schema_name", "created_at"]


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [IsAdminUser]
    queryset = Tenant.objects.all()
