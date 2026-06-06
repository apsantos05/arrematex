from rest_framework import serializers
from .models import ProviderBalanca, Pesagem


class ProviderBalancaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderBalanca
        fields = ["id", "nome", "tipo", "ativo", "created_at"]
        read_only_fields = ["id", "created_at"]


class PesagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pesagem
        fields = [
            "id", "lote", "provider", "peso_kg", "origem", "status",
            "device_id", "leitura_timestamp", "dados_brutos", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
