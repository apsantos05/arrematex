"""Models de Lotes — cadastro de animais para leilão."""
import uuid

from django.conf import settings
from django.db import models


class Categoria(models.Model):
    """Categoria de animal (Bovino, Equino, etc.)."""
    nome = models.CharField("Nome", max_length=100)
    descricao = models.TextField("Descrição", blank=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Vendedor(models.Model):
    """Consignante / proprietário dos animais."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField("Nome", max_length=200)
    cpf_cnpj = models.CharField("CPF/CNPJ", max_length=18)
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField("E-mail", blank=True)
    cidade = models.CharField("Cidade", max_length=100, blank=True)
    estado = models.CharField("UF", max_length=2, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vendedor"
        verbose_name_plural = "Vendedores"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Evento(models.Model):
    """Evento / dia de leilão."""
    STATUS_AGENDADO = "agendado"
    STATUS_ABERTO = "aberto"
    STATUS_ENCERRADO = "encerrado"
    STATUS_CHOICES = [
        (STATUS_AGENDADO, "Agendado"),
        (STATUS_ABERTO, "Aberto"),
        (STATUS_ENCERRADO, "Encerrado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField("Nome do Evento", max_length=200)
    data = models.DateField("Data")
    hora_inicio = models.TimeField("Hora de Início", null=True, blank=True)
    local = models.CharField("Local", max_length=200, blank=True)
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_AGENDADO)
    descricao = models.TextField("Descrição", blank=True)

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eventos_criados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.nome} — {self.data}"


class Lote(models.Model):
    """Lote de animais cadastrado para um evento de leilão."""

    STATUS_AGUARDANDO = "aguardando"
    STATUS_EM_LEILAO = "em_leilao"
    STATUS_VENDIDO = "vendido"
    STATUS_RETIRADO = "retirado"
    STATUS_CHOICES = [
        (STATUS_AGUARDANDO, "Aguardando"),
        (STATUS_EM_LEILAO, "Em Leilão"),
        (STATUS_VENDIDO, "Vendido"),
        (STATUS_RETIRADO, "Retirado"),
    ]

    PAGAMENTO_A_VISTA = "a_vista"
    PAGAMENTO_30 = "30_dias"
    PAGAMENTO_60 = "60_dias"
    PAGAMENTO_90 = "90_dias"
    PAGAMENTO_PARCELADO = "parcelado"
    PAGAMENTO_CHOICES = [
        (PAGAMENTO_A_VISTA, "À Vista"),
        (PAGAMENTO_30, "30 Dias"),
        (PAGAMENTO_60, "60 Dias"),
        (PAGAMENTO_90, "90 Dias"),
        (PAGAMENTO_PARCELADO, "Parcelado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evento = models.ForeignKey(Evento, on_delete=models.PROTECT, related_name="lotes")
    numero = models.PositiveIntegerField("Nº do Lote")
    descricao = models.CharField("Descrição", max_length=300)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, null=True, blank=True)
    vendedor = models.ForeignKey(Vendedor, on_delete=models.PROTECT, null=True, blank=True)

    # Animais
    quantidade = models.PositiveIntegerField("Quantidade")
    peso_total = models.DecimalField("Peso Total (kg)", max_digits=10, decimal_places=2, default=0)
    peso_origem = models.CharField(
        "Origem do Peso",
        max_length=20,
        choices=[("manual", "Manual"), ("balanca_api", "Balança API"), ("balanca_local", "Balança Local")],
        default="manual",
    )

    # Financeiro
    lance_inicial = models.DecimalField("Lance Inicial (R$)", max_digits=12, decimal_places=2)
    incremento = models.DecimalField("Incremento Padrão (R$)", max_digits=10, decimal_places=2, default=50)
    lance_atual = models.DecimalField("Lance Atual (R$)", max_digits=12, decimal_places=2, default=0)
    condicao_pagamento = models.CharField("Condição de Pagamento", max_length=20, choices=PAGAMENTO_CHOICES, default=PAGAMENTO_A_VISTA)

    # Status
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_AGUARDANDO)

    # Documentos
    documentos = models.JSONField("Documentos Adicionais", default=dict, blank=True)

    # Auditoria
    cadastrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="lotes_cadastrados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        unique_together = ("evento", "numero")
        ordering = ["evento", "numero"]

    def __str__(self):
        return f"Lote {self.numero} — {self.descricao}"

    @property
    def preco_por_kg(self):
        if self.peso_total and self.lance_atual:
            return round(float(self.lance_atual) / float(self.peso_total), 2)
        return 0
