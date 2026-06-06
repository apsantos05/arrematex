"""Models da balança — arquitetura Adapter/Provider para integração futura."""
import uuid

from django.conf import settings
from django.db import models


class ProviderBalanca(models.Model):
    """Configuração de um provedor de API de balança."""

    TIPO_HTTP_REST = "http_rest"
    TIPO_SERIAL = "serial"
    TIPO_TCP = "tcp"
    TIPO_CHOICES = [
        (TIPO_HTTP_REST, "HTTP REST"),
        (TIPO_SERIAL, "Serial/USB"),
        (TIPO_TCP, "TCP/IP"),
    ]

    STATUS_ATIVO = "ativo"
    STATUS_INATIVO = "inativo"
    STATUS_CHOICES = [(STATUS_ATIVO, "Ativo"), (STATUS_INATIVO, "Inativo")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField("Nome", max_length=100)
    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_CHOICES, default=TIPO_HTTP_REST)
    status = models.CharField("Status", max_length=10, choices=STATUS_CHOICES, default=STATUS_ATIVO)

    # Configuração de conexão (formato depende do tipo)
    config = models.JSONField("Configuração de Conexão", default=dict)
    # Ex HTTP: {"base_url": "http://...", "api_key": "...", "timeout": 5}
    # Ex TCP:  {"host": "192.168.0.10", "port": 4001}

    device_id = models.CharField("ID do Dispositivo", max_length=100, blank=True)
    descricao = models.TextField("Descrição", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Provedor de Balança"
        verbose_name_plural = "Provedores de Balança"

    def __str__(self):
        return f"{self.nome} ({self.tipo})"


class Pesagem(models.Model):
    """Registro de pesagem — manual ou via API de balança."""

    ORIGEM_MANUAL = "manual"
    ORIGEM_API = "balanca_api"
    ORIGEM_LOCAL = "balanca_local"
    ORIGEM_OFFLINE_QUEUE = "offline_queue"
    ORIGEM_CHOICES = [
        (ORIGEM_MANUAL, "Manual"),
        (ORIGEM_API, "Balança API"),
        (ORIGEM_LOCAL, "Balança Local"),
        (ORIGEM_OFFLINE_QUEUE, "Fila Offline"),
    ]

    STATUS_PENDENTE = "pendente"
    STATUS_SINCRONIZADO = "sincronizado"
    STATUS_ERRO = "erro"
    STATUS_CHOICES = [
        (STATUS_PENDENTE, "Pendente Sincronização"),
        (STATUS_SINCRONIZADO, "Sincronizado"),
        (STATUS_ERRO, "Erro"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lote = models.ForeignKey(
        "lotes.Lote",
        on_delete=models.PROTECT,
        related_name="pesagens",
        null=True,
        blank=True,
    )
    provider = models.ForeignKey(
        ProviderBalanca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pesagens",
    )

    peso_kg = models.DecimalField("Peso (kg)", max_digits=10, decimal_places=3)
    origem = models.CharField("Origem", max_length=20, choices=ORIGEM_CHOICES, default=ORIGEM_MANUAL)
    status = models.CharField("Status Sync", max_length=20, choices=STATUS_CHOICES, default=STATUS_SINCRONIZADO)

    # Rastreabilidade
    device_id = models.CharField("Device ID", max_length=100, blank=True)
    leitura_timestamp = models.DateTimeField("Timestamp da Leitura")
    dados_brutos = models.JSONField("Dados Brutos", default=dict, blank=True)

    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pesagens_registradas",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pesagem"
        verbose_name_plural = "Pesagens"
        ordering = ["-leitura_timestamp"]

    def __str__(self):
        return f"{self.peso_kg} kg — {self.origem} — {self.leitura_timestamp}"
