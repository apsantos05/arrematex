"""
Relatórios — views que agregam dados do tenant atual.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth
from apps.financeiro.models import Venda
from apps.lotes.models import Lote, Evento


class ResumoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_eventos = Evento.objects.count()
        lotes_vendidos = Lote.objects.filter(status="vendido").count()
        faturamento = Venda.objects.aggregate(total=Sum("valor_total"))["total"] or 0
        ticket_medio = Venda.objects.aggregate(avg=Avg("valor_total"))["avg"] or 0

        mensal = (
            Venda.objects
            .annotate(mes=TruncMonth("created_at"))
            .values("mes")
            .annotate(valor=Sum("valor_total"))
            .order_by("mes")
        )

        return Response({
            "total_eventos": total_eventos,
            "lotes_vendidos": lotes_vendidos,
            "faturamento": float(faturamento),
            "ticket_medio": float(ticket_medio),
            "faturamento_mensal": [
                {"mes": item["mes"].strftime("%b/%Y"), "valor": float(item["valor"])}
                for item in mensal
            ],
        })


class VendasRelatorioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        vendas = (
            Venda.objects
            .select_related("lote__evento")
            .order_by("-created_at")[:100]
        )
        data = [
            {
                "id": str(v.id),
                "comprador": v.comprador_nome,
                "lote": v.lote.numero if v.lote else None,
                "valor_total": str(v.valor_total),
                "status": v.status,
                "data": v.created_at.strftime("%d/%m/%Y"),
            }
            for v in vendas
        ]
        return Response(data)


class LotesRelatorioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lotes = Lote.objects.select_related("evento", "categoria").order_by("-created_at")[:200]
        data = [
            {
                "id": str(l.id),
                "numero": l.numero,
                "descricao": l.descricao,
                "evento": l.evento.nome if l.evento else None,
                "categoria": l.categoria.nome if l.categoria else None,
                "peso_total": str(l.peso_total),
                "lance_inicial": str(l.lance_inicial),
                "status": l.status,
            }
            for l in lotes
        ]
        return Response(data)
