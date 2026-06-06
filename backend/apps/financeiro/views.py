"""Views do financeiro — vendas, recebimentos, relatório de caixa."""
from decimal import Decimal

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.financeiro.models import Estorno, Recebimento, Venda
from apps.auditoria.utils import registrar_log


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------
class VendaSerializer(serializers.ModelSerializer):
    valor_em_aberto = serializers.SerializerMethodField()
    comprador_nome = serializers.CharField(source="arrematante_nome", read_only=True)
    lote_numero = serializers.IntegerField(source="lote.numero", read_only=True)
    lote_descricao = serializers.CharField(source="lote.descricao", read_only=True)

    class Meta:
        model = Venda
        fields = "__all__"
        read_only_fields = ["id", "fechado_por", "created_at", "updated_at",
                            "comissao_valor", "valor_total", "valor_pago"]

    def get_valor_em_aberto(self, obj):
        return max(Decimal("0"), obj.valor_total - obj.valor_pago)


class RecebimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recebimento
        fields = "__all__"
        read_only_fields = ["id", "registrado_por", "created_at", "updated_at"]


class EstornoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estorno
        fields = "__all__"
        read_only_fields = ["id", "realizado_por", "created_at"]


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------
class VendaViewSet(ModelViewSet):
    queryset = Venda.objects.select_related("lote", "fechado_por").all()
    serializer_class = VendaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "nfe_emitida"]
    search_fields = ["arrematante_nome", "arrematante_cpf_cnpj"]
    ordering_fields = ["created_at", "valor_total"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def perform_create(self, serializer):
        venda = serializer.save(fechado_por=self.request.user)
        venda.calcular_totais()
        registrar_log(self.request.user, "fechar_venda", "Venda", str(venda.id), str(venda))


class RecebimentoViewSet(ModelViewSet):
    queryset = Recebimento.objects.select_related("venda").all()
    serializer_class = RecebimentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["venda", "forma", "status"]
    ordering_fields = ["created_at", "valor"]

    def perform_create(self, serializer):
        recebimento = serializer.save(registrado_por=self.request.user)
        # Atualiza valor pago na venda
        venda = recebimento.venda
        total_pago = sum(
            r.valor for r in venda.recebimentos.filter(status=Recebimento.STATUS_CONFIRMADO)
        )
        venda.valor_pago = total_pago
        if total_pago >= venda.valor_total:
            venda.status = Venda.STATUS_PAGO
        elif total_pago > 0:
            venda.status = Venda.STATUS_PARCIAL
        venda.save(update_fields=["valor_pago", "status"])
        registrar_log(self.request.user, "create", "Recebimento", str(recebimento.id),
                      f"R$ {recebimento.valor} — {recebimento.forma}")


class EstornoView(APIView):
    """Estorna um recebimento específico."""
    permission_classes = [IsAuthenticated]

    def post(self, request, recebimento_id):
        if not request.user.is_admin:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            recebimento = Recebimento.objects.get(id=recebimento_id)
        except Recebimento.DoesNotExist:
            return Response({"detail": "Recebimento não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        motivo = request.data.get("motivo", "")
        if not motivo:
            return Response({"detail": "Motivo é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        Estorno.objects.create(
            cobranca=recebimento,
            valor=recebimento.valor,
            motivo=motivo,
            realizado_por=request.user,
        )
        recebimento.status = Recebimento.STATUS_ESTORNADO
        recebimento.save(update_fields=["status"])

        # Recalcula valor pago na venda
        venda = recebimento.venda
        total_pago = sum(r.valor for r in venda.recebimentos.filter(status=Recebimento.STATUS_CONFIRMADO))
        venda.valor_pago = total_pago
        if total_pago >= venda.valor_total:
            venda.status = Venda.STATUS_PAGO
        elif total_pago > 0:
            venda.status = Venda.STATUS_PARCIAL
        else:
            venda.status = Venda.STATUS_PENDENTE
        venda.save(update_fields=["valor_pago", "status"])

        registrar_log(request.user, "estorno", "Recebimento", str(recebimento.id), motivo)
        return Response({"detail": "Estorno registrado."})
