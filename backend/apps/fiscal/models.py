"""Models fiscais — NF-e, NFS-e, certificados digitais."""
import uuid

from django.conf import settings
from django.db import models


class CertificadoDigital(models.Model):
    """Certificado A1 (.pfx) do tenant para assinatura de documentos fiscais."""

    TIPO_A1 = "A1"
    TIPO_A3 = "A3"
    TIPO_CHOICES = [(TIPO_A1, "A1 (arquivo)"), (TIPO_A3, "A3 (token/smartcard)")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField("Descrição", max_length=200)
    tipo = models.CharField("Tipo", max_length=2, choices=TIPO_CHOICES, default=TIPO_A1)

    # A1 — arquivo criptografado em repouso (AES-256 via Fernet)
    arquivo_cifrado = models.BinaryField("Arquivo Cifrado (.pfx)", null=True, blank=True)
    # Nunca armazenar a senha em texto plano — usa vault ou env por tenant
    senha_hash = models.CharField("Hash da Senha", max_length=200, blank=True)

    # Informações do certificado (extraídas do .pfx)
    cnpj = models.CharField("CNPJ", max_length=18)
    razao_social = models.CharField("Razão Social", max_length=200)
    validade = models.DateField("Validade")
    serial = models.CharField("Serial", max_length=100, blank=True)
    issuer = models.CharField("Emissor", max_length=300, blank=True)

    ativo = models.BooleanField("Ativo", default=True)
    alerta_vencimento_enviado = models.BooleanField("Alerta Enviado", default=False)

    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="certificados_enviados",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Certificado Digital"
        verbose_name_plural = "Certificados Digitais"

    def __str__(self):
        return f"{self.nome} — {self.cnpj} (válido até {self.validade})"

    @property
    def dias_para_vencer(self):
        from django.utils import timezone
        delta = self.validade - timezone.now().date()
        return delta.days


class ConfiguracaoFiscal(models.Model):
    """Configurações fiscais do tenant — série, numeração, CSOSN, etc."""

    REGIME_SIMPLES = "1"
    REGIME_NORMAL = "3"
    REGIME_CHOICES = [("1", "Simples Nacional"), ("2", "Simples Nacional — excesso"), ("3", "Regime Normal")]

    certificado = models.ForeignKey(
        CertificadoDigital,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="configuracoes",
    )

    # NF-e
    nfe_serie = models.PositiveIntegerField("Série NF-e", default=1)
    nfe_ultimo_numero = models.PositiveIntegerField("Último Nº NF-e", default=0)
    nfe_ambiente = models.CharField("Ambiente NF-e", max_length=1, choices=[("1", "Produção"), ("2", "Homologação")], default="2")

    # NFS-e
    nfse_serie = models.CharField("Série NFS-e", max_length=10, blank=True)
    nfse_ultimo_numero = models.PositiveIntegerField("Último Nº NFS-e", default=0)

    # Tributação
    regime_tributario = models.CharField("Regime Tributário", max_length=1, choices=REGIME_CHOICES, default=REGIME_SIMPLES)
    csosn_padrao = models.CharField("CSOSN Padrão", max_length=4, default="400")
    cfop_padrao = models.CharField("CFOP Padrão", max_length=4, default="5104")
    cst_pis = models.CharField("CST PIS", max_length=3, default="07")
    cst_cofins = models.CharField("CST COFINS", max_length=3, default="07")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração Fiscal"


class NotaFiscal(models.Model):
    """Nota Fiscal Eletrônica (NF-e) ou de Serviço (NFS-e)."""

    TIPO_NFE = "NFe"
    TIPO_NFSE = "NFSe"
    TIPO_MDFE = "MDFe"
    TIPO_CHOICES = [(TIPO_NFE, "NF-e"), (TIPO_NFSE, "NFS-e"), (TIPO_MDFE, "MDF-e")]

    STATUS_RASCUNHO = "rascunho"
    STATUS_AGUARDANDO = "aguardando"
    STATUS_AUTORIZADA = "autorizada"
    STATUS_REJEITADA = "rejeitada"
    STATUS_CANCELADA = "cancelada"
    STATUS_CONTINGENCIA = "contingencia"
    STATUS_CHOICES = [
        (STATUS_RASCUNHO, "Rascunho"),
        (STATUS_AGUARDANDO, "Aguardando SEFAZ"),
        (STATUS_AUTORIZADA, "Autorizada"),
        (STATUS_REJEITADA, "Rejeitada"),
        (STATUS_CANCELADA, "Cancelada"),
        (STATUS_CONTINGENCIA, "Contingência"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venda = models.ForeignKey(
        "financeiro.Venda",
        on_delete=models.PROTECT,
        related_name="notas_fiscais",
        null=True,
        blank=True,
    )
    tipo = models.CharField("Tipo", max_length=5, choices=TIPO_CHOICES, default=TIPO_NFE)
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_RASCUNHO)

    # Numeração
    serie = models.PositiveIntegerField("Série")
    numero = models.PositiveIntegerField("Número")
    chave_acesso = models.CharField("Chave de Acesso", max_length=44, blank=True)
    protocolo = models.CharField("Protocolo", max_length=30, blank=True)

    # Datas
    data_emissao = models.DateTimeField("Data Emissão", null=True, blank=True)
    data_autorizacao = models.DateTimeField("Data Autorização", null=True, blank=True)

    # Valores
    valor_total = models.DecimalField("Valor Total", max_digits=12, decimal_places=2, default=0)
    valor_icms = models.DecimalField("ICMS", max_digits=10, decimal_places=2, default=0)

    # Armazenamento
    xml_url = models.URLField("URL XML", blank=True)
    danfe_url = models.URLField("URL DANFE", blank=True)
    xml_cancelamento_url = models.URLField("URL XML Cancelamento", blank=True)

    # Retorno SEFAZ
    retorno_codigo = models.CharField("Cód. Retorno", max_length=10, blank=True)
    retorno_motivo = models.TextField("Motivo Retorno", blank=True)

    # Modo contingência
    modo_contingencia = models.BooleanField("Modo Contingência", default=False)
    justificativa_contingencia = models.TextField("Justificativa Contingência", blank=True)

    # Auditoria
    emitido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="notas_emitidas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
        ordering = ["-data_emissao"]

    def __str__(self):
        return f"{self.tipo} {self.serie}/{self.numero} — {self.status}"


class LogTransmissaoFiscal(models.Model):
    """Log imutável de cada transmissão à SEFAZ."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nota = models.ForeignKey(NotaFiscal, on_delete=models.PROTECT, related_name="logs_transmissao")
    operacao = models.CharField("Operação", max_length=50)  # emissao, cancelamento, inutilizacao
    xml_enviado_hash = models.CharField("Hash XML Enviado", max_length=64)
    resposta_codigo = models.CharField("Código", max_length=10)
    resposta_motivo = models.TextField("Motivo")
    sucesso = models.BooleanField("Sucesso")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de Transmissão Fiscal"
        ordering = ["-created_at"]
