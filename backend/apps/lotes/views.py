"""Views de Lotes e Eventos — CRUD completo com filtros."""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.lotes.models import Categoria, Evento, Lote, Vendedor
from apps.auditoria.utils import registrar_log


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------
class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"


class VendedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendedor
        fields = "__all__"


class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = "__all__"
        read_only_fields = ["id", "criado_por", "created_at", "updated_at"]


class LoteSerializer(serializers.ModelSerializer):
    preco_por_kg = serializers.ReadOnlyField()
    categoria_nome = serializers.CharField(source="categoria.nome", read_only=True)
    vendedor_nome = serializers.CharField(source="vendedor.nome", read_only=True)

    class Meta:
        model = Lote
        fields = "__all__"
        read_only_fields = ["id", "cadastrado_por", "created_at", "updated_at", "lance_atual"]


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------
class EventoViewSet(ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["nome", "local"]
    ordering_fields = ["data", "created_at"]

    def perform_create(self, serializer):
        evento = serializer.save(criado_por=self.request.user)
        registrar_log(self.request.user, "create", "Evento", str(evento.id), str(evento))

    def perform_update(self, serializer):
        evento = serializer.save()
        registrar_log(self.request.user, "update", "Evento", str(evento.id), str(evento))


class LoteViewSet(ModelViewSet):
    queryset = Lote.objects.select_related("evento", "categoria", "vendedor").all()
    serializer_class = LoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["evento", "status", "categoria"]
    search_fields = ["descricao", "numero"]
    ordering_fields = ["numero", "created_at"]

    def perform_create(self, serializer):
        lote = serializer.save(cadastrado_por=self.request.user, lance_atual=serializer.validated_data["lance_inicial"])
        registrar_log(self.request.user, "create", "Lote", str(lote.id), str(lote))

    def perform_destroy(self, instance):
        if instance.status != Lote.STATUS_AGUARDANDO:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Apenas lotes aguardando podem ser excluídos.")
        registrar_log(self.request.user, "delete", "Lote", str(instance.id), str(instance))
        instance.delete()
