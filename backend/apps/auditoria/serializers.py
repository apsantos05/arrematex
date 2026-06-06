from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    usuario_email = serializers.EmailField(source="usuario.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "acao", "descricao", "usuario", "usuario_email",
            "ip_address", "dados_antes", "dados_depois", "created_at",
        ]
        read_only_fields = fields
