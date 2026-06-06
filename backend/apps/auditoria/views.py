"""
Auditoria — read-only ViewSet para admins consultarem logs imutáveis.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["acao", "usuario"]
    search_fields = ["descricao", "ip_address"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if not self.request.user.is_admin:
            return AuditLog.objects.none()
        return AuditLog.objects.select_related("usuario").all()
