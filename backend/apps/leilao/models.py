"""Models do módulo de leilão — lances, sessão, telão."""
import uuid

from django.conf import settings
from django.db import models

from apps.lotes.models import Lote


class SessaoLeilao(models.Model):
    """Sessão ativa de leilão — controla estado do painel do leiloeiro."""

    STATUS_INATIVA = "inativa"
    STATUS_ATIVA = "ativa"
    STATUS_PAUSADA = "pausada"
    STATUS_ENCERRADA = "encerrada"
    STATUS_CHOICES = [
        (STATUS_INATIVA, "Inativa"),
        (STATUS_ATIVA, "Ativa"),
        (STATUS_PAUSADA, "Pausada"),
        (STATUS_ENCERRADA, "Encerrada"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lote = models.OneToOneField(Lote, on_delete=models.PROTECT, related_name="sessao_leilao")
    leiloeiro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sessoes_conduzidas",
    )
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_INATIVA)

    lance_corrente = models.DecimalField("Lance Corrente", max_digits=12, decimal_places=2, null=True, blank=True)
    arrematante_atual = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessoes_arrematando",
    )
    arrematante_nome_livre = models.CharField("Nome Arrematante (livre)", max_length=200, blank=True)

    # Controle de telão
    telao_ativo = models.BooleanField("Telão Ativo", default=False)
    telao_mensagem = models.CharField("Mensagem no Telão", max_length=300, blank=True)

    aberto_em = models.DateTimeField("Aberto em", null=True, blank=True)
    encerrado_em = models.DateTimeField("Encerrado em", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sessão de Leilão"
        verbose_name_plural = "Sessões de Leilão"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sessão {self.lote} — {self.status}"


class Lance(models.Model):
    """Registro individual de lance durante leilão."""

    ORIGEM_MANUAL = "manual"
    ORIGEM_TECLADO = "teclado"
    ORIGEM_APP = "app"
    ORIGEM_CHOICES = [
        (ORIGEM_MANUAL, "Manual"),
        (ORIGEM_TECLADO, "Teclado Leiloeiro"),
        (ORIGEM_APP, "Aplicativo"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sessao = models.ForeignKey(SessaoLeilao, on_delete=models.PROTECT, related_name="lances")
    valor = models.DecimalField("Valor (R$)", max_digits=12, decimal_places=2)
    arrematante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lances_dados",
    )
    arrematante_nome_livre = models.CharField("Nome Livre", max_length=200, blank=True)
    origem = models.CharField("Origem", max_length=20, choices=ORIGEM_CHOICES, default=ORIGEM_MANUAL)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="lances_registrados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cancelado = models.BooleanField("Cancelado", default=False)
    cancelado_motivo = models.CharField("Motivo Cancelamento", max_length=300, blank=True)

    class Meta:
        verbose_name = "Lance"
        verbose_name_plural = "Lances"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Lance R$ {self.valor} — {self.sessao.lote}"


class ConfiguracaoTelao(models.Model):
    """Configuração global do telão por tenant."""

    LAYOUT_CLASSICO = "classico"
    LAYOUT_MODERNO = "moderno"
    LAYOUT_CHOICES = [
        (LAYOUT_CLASSICO, "Clássico"),
        (LAYOUT_MODERNO, "Moderno"),
    ]

    layout = models.CharField("Layout", max_length=20, choices=LAYOUT_CHOICES, default=LAYOUT_MODERNO)
    mostrar_historico = models.BooleanField("Mostrar Histórico de Lances", default=True)
    quantidade_historico = models.PositiveIntegerField("Qtd. Lances no Histórico", default=5)
    logo_url = models.URLField("URL Logo no Telão", blank=True)
    mensagem_padrao = models.CharField("Mensagem Padrão", max_length=300, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração do Telão"
