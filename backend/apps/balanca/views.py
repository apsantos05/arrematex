"""
Balança — views para listar providers e pesagens.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import ProviderBalanca, Pesagem
from .serializers import ProviderBalancaSerializer, PesagemSerializer


class BalancaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProviderBalancaSerializer
    filter_backends = [filters.OrderingFilter]

    def get_queryset(self):
        return ProviderBalanca.objects.all()


class PesagemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PesagemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["lote__numero", "origem", "status"]
    ordering = ["-leitura_timestamp"]

    def get_queryset(self):
        return Pesagem.objects.select_related("lote", "provider").all()
