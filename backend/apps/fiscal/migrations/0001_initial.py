import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("financeiro", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CertificadoDigital",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=200, verbose_name="Descrição")),
                ("tipo", models.CharField(choices=[("A1", "A1 (arquivo)"), ("A3", "A3 (token/smartcard)")], default="A1", max_length=2, verbose_name="Tipo")),
                ("arquivo_cifrado", models.BinaryField(blank=True, null=True, verbose_name="Arquivo Cifrado (.pfx)")),
                ("senha_hash", models.CharField(blank=True, max_length=200, verbose_name="Hash da Senha")),
                ("cnpj", models.CharField(max_length=18, verbose_name="CNPJ")),
                ("razao_social", models.CharField(max_length=200, verbose_name="Razão Social")),
                ("validade", models.DateField(verbose_name="Validade")),
                ("serial", models.CharField(blank=True, max_length=100, verbose_name="Serial")),
                ("issuer", models.CharField(blank=True, max_length=300, verbose_name="Emissor")),
                ("ativo", models.BooleanField(default=True, verbose_name="Ativo")),
                ("alerta_vencimento_enviado", models.BooleanField(default=False, verbose_name="Alerta Enviado")),
                ("enviado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="certificados_enviados", to=settings.AUTH_USER_MODEL)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Certificado Digital", "verbose_name_plural": "Certificados Digitais"},
        ),
        migrations.CreateModel(
            name="ConfiguracaoFiscal",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nfe_serie", models.PositiveIntegerField(default=1, verbose_name="Série NF-e")),
                ("nfe_ultimo_numero", models.PositiveIntegerField(default=0, verbose_name="Último Nº NF-e")),
                ("nfe_ambiente", models.CharField(choices=[("1", "Produção"), ("2", "Homologação")], default="2", max_length=1, verbose_name="Ambiente NF-e")),
                ("nfse_serie", models.CharField(blank=True, max_length=10, verbose_name="Série NFS-e")),
                ("nfse_ultimo_numero", models.PositiveIntegerField(default=0, verbose_name="Último Nº NFS-e")),
                ("regime_tributario", models.CharField(choices=[("1", "Simples Nacional"), ("2", "Simples Nacional — excesso"), ("3", "Regime Normal")], default="1", max_length=1, verbose_name="Regime Tributário")),
                ("csosn_padrao", models.CharField(default="400", max_length=4, verbose_name="CSOSN Padrão")),
                ("cfop_padrao", models.CharField(default="5104", max_length=4, verbose_name="CFOP Padrão")),
                ("cst_pis", models.CharField(default="07", max_length=3, verbose_name="CST PIS")),
                ("cst_cofins", models.CharField(default="07", max_length=3, verbose_name="CST COFINS")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("certificado", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="configuracoes", to="fiscal.certificadodigital")),
            ],
            options={"verbose_name": "Configuração Fiscal"},
        ),
        migrations.CreateModel(
            name="NotaFiscal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tipo", models.CharField(choices=[("NFe", "NF-e"), ("NFSe", "NFS-e"), ("MDFe", "MDF-e")], default="NFe", max_length=5, verbose_name="Tipo")),
                ("status", models.CharField(
                    choices=[("rascunho", "Rascunho"), ("aguardando", "Aguardando SEFAZ"), ("autorizada", "Autorizada"), ("rejeitada", "Rejeitada"), ("cancelada", "Cancelada"), ("contingencia", "Contingência")],
                    default="rascunho",
                    max_length=20,
                    verbose_name="Status",
                )),
                ("serie", models.PositiveIntegerField(verbose_name="Série")),
                ("numero", models.PositiveIntegerField(verbose_name="Número")),
                ("chave_acesso", models.CharField(blank=True, max_length=44, verbose_name="Chave de Acesso")),
                ("protocolo", models.CharField(blank=True, max_length=30, verbose_name="Protocolo")),
                ("data_emissao", models.DateTimeField(blank=True, null=True, verbose_name="Data Emissão")),
                ("data_autorizacao", models.DateTimeField(blank=True, null=True, verbose_name="Data Autorização")),
                ("valor_total", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Valor Total")),
                ("valor_icms", models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="ICMS")),
                ("xml_url", models.URLField(blank=True, verbose_name="URL XML")),
                ("danfe_url", models.URLField(blank=True, verbose_name="URL DANFE")),
                ("xml_cancelamento_url", models.URLField(blank=True, verbose_name="URL XML Cancelamento")),
                ("retorno_codigo", models.CharField(blank=True, max_length=10, verbose_name="Cód. Retorno")),
                ("retorno_motivo", models.TextField(blank=True, verbose_name="Motivo Retorno")),
                ("modo_contingencia", models.BooleanField(default=False, verbose_name="Modo Contingência")),
                ("justificativa_contingencia", models.TextField(blank=True, verbose_name="Justificativa Contingência")),
                ("venda", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="notas_fiscais", to="financeiro.venda")),
                ("emitido_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="notas_emitidas", to=settings.AUTH_USER_MODEL)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Nota Fiscal", "verbose_name_plural": "Notas Fiscais", "ordering": ["-data_emissao"]},
        ),
        migrations.CreateModel(
            name="LogTransmissaoFiscal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("operacao", models.CharField(max_length=50, verbose_name="Operação")),
                ("xml_enviado_hash", models.CharField(max_length=64, verbose_name="Hash XML Enviado")),
                ("resposta_codigo", models.CharField(max_length=10, verbose_name="Código")),
                ("resposta_motivo", models.TextField(verbose_name="Motivo")),
                ("sucesso", models.BooleanField(verbose_name="Sucesso")),
                ("nota", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="logs_transmissao", to="fiscal.notafiscal")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Log de Transmissão Fiscal", "ordering": ["-created_at"]},
        ),
    ]
