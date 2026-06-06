"""
Leilão — views REST para SessaoLeilao e ConfiguracaoTelao.
Ações de lance e controle do leilão acontecem via WebSocket (consumers.py).
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers as drf_serializers

from .models import SessaoLeilao, ConfiguracaoTelao
from .services import abrir_lote, fechar_lote


# ── Serializers inline ────────────────────────────────────────────────────────
class SessaoSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = SessaoLeilao
        fields = [
            "id", "lote", "leiloeiro", "lance_inicial", "lance_atual",
            "arrematante_nome", "telao_ativo", "telao_mensagem",
            "status", "aberto_em", "fechado_em",
        ]
        read_only_fields = ["id", "aberto_em", "fechado_em"]


class TelaoConfigSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = ConfiguracaoTelao
        fields = ["id", "evento", "titulo", "logo_url", "cor_primaria", "mostrar_historico"]


# ── ViewSets ──────────────────────────────────────────────────────────────────
class SessaoLeilaoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SessaoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ["-aberto_em"]

    def get_queryset(self):
        return SessaoLeilao.objects.select_related("lote", "leiloeiro").all()


class LeilaoViewSet(viewsets.ModelViewSet):
    """ConfiguracaoTelao CRUD."""
    serializer_class = TelaoConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ConfiguracaoTelao.objects.all()
