"""
Models financeiros — vendas, recebimentos e comissões.
Pagamentos são registrados manualmente pelo caixa (sem gateway online).
"""
import uuid

from django.conf import settings
from django.db import models

from apps.lotes.models import Lote


class Venda(models.Model):
    """Registro de venda de lote arrematado."""

    STATUS_PENDENTE = "pendente"
    STATUS_PAGO = "pago"
    STATUS_PARCIAL = "parcial"
    STATUS_CANCELADO = "cancelado"
    STATUS_CHOICES = [
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_PAGO, "Pago"),
        (STATUS_PARCIAL, "Parcial"),
        (STATUS_CANCELADO, "Cancelado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lote = models.OneToOneField(Lote, on_delete=models.PROTECT, related_name="venda")

    # Arrematante
    arrematante_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="compras",
    )
    arrematante_nome = models.CharField("Nome Arrematante", max_length=200)
    arrematante_cpf_cnpj = models.CharField("CPF/CNPJ Arrematante", max_length=18, blank=True)
    arrematante_email = models.EmailField("E-mail Arrematante", blank=True)

    # Valores
    valor_arrematacao = models.DecimalField("Valor de Arrematação", max_digits=12, decimal_places=2)
    comissao_percentual = models.DecimalField("Comissão (%)", max_digits=5, decimal_places=2, default=5)
    comissao_valor = models.DecimalField("Valor Comissão", max_digits=12, decimal_places=2, default=0)
    taxas = models.DecimalField("Taxas Adicionais", max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField("Valor Total", max_digits=12, decimal_places=2, default=0)
    valor_pago = models.DecimalField("Valor Pago", max_digits=12, decimal_places=2, default=0)

    # Status
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    condicao_pagamento = models.CharField("Condição de Pagamento", max_length=50, blank=True)

    # Fiscal
    nfe_emitida = models.BooleanField("NF-e Emitida", default=False)
    nfse_emitida = models.BooleanField("NFS-e Emitida", default=False)

    # Auditoria
    fechado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vendas_fechadas",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Venda {self.lote} — {self.arrematante_nome}"

    def calcular_totais(self):
        self.comissao_valor = self.valor_arrematacao * (self.comissao_percentual / 100)
        self.valor_total = self.valor_arrematacao + self.comissao_valor + self.taxas
        self.save(update_fields=["comissao_valor", "valor_total"])


class Recebimento(models.Model):
    """
    Recebimento manual registrado pelo caixa.
    Não há gateway — o operador informa forma e valor recebido.
    """

    FORMA_DINHEIRO = "dinheiro"
    FORMA_PIX = "pix"
    FORMA_TRANSFERENCIA = "transferencia"
    FORMA_CHEQUE = "cheque"
    FORMA_DEBITO = "debito"
    FORMA_CREDITO = "credito"
    FORMA_CHOICES = [
        (FORMA_DINHEIRO, "Dinheiro"),
        (FORMA_PIX, "PIX"),
        (FORMA_TRANSFERENCIA, "Transferência Bancária"),
        (FORMA_CHEQUE, "Cheque"),
        (FORMA_DEBITO, "Cartão de Débito"),
        (FORMA_CREDITO, "Cartão de Crédito"),
    ]

    STATUS_CONFIRMADO = "confirmado"
    STATUS_ESTORNADO = "estornado"
    STATUS_CHOICES = [
        (STATUS_CONFIRMADO, "Confirmado"),
        (STATUS_ESTORNADO, "Estornado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venda = models.ForeignKey(Venda, on_delete=models.PROTECT, related_name="recebimentos")
    forma = models.CharField("Forma de Pagamento", max_length=20, choices=FORMA_CHOICES)
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMADO)

    valor = models.DecimalField("Valor Recebido (R$)", max_digits=12, decimal_places=2)
    vencimento = models.DateField("Vencimento / Data Prevista", null=True, blank=True)
    pago_em = models.DateField("Data do Recebimento", null=True, blank=True)

    # Comprovante / observações
    observacao = models.CharField("Observação", max_length=500, blank=True)
    comprovante = models.FileField("Comprovante", upload_to="financeiro/comprovantes/", null=True, blank=True)

    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recebimentos_registrados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Recebimento"
        verbose_name_plural = "Recebimentos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_forma_display()} R$ {self.valor} — {self.status}"


class Estorno(models.Model):
    """Registro de estorno de recebimento manual."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recebimento = models.ForeignKey(Recebimento, on_delete=models.PROTECT, related_name="estornos")
    valor = models.DecimalField("Valor Estornado", max_digits=12, decimal_places=2)
    motivo = models.TextField("Motivo")
    realizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Estorno"
        verbose_name_plural = "Estornos"
