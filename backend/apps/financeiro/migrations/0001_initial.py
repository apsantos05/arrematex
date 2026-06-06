import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("lotes", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Venda",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("arrematante_nome", models.CharField(max_length=200, verbose_name="Nome Arrematante")),
                ("arrematante_cpf_cnpj", models.CharField(blank=True, max_length=18, verbose_name="CPF/CNPJ Arrematante")),
                ("arrematante_email", models.EmailField(blank=True, verbose_name="E-mail Arrematante")),
                ("valor_arrematacao", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Valor de Arrematação")),
                ("comissao_percentual", models.DecimalField(decimal_places=2, default=5, max_digits=5, verbose_name="Comissão (%)")),
                ("comissao_valor", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Valor Comissão")),
                ("taxas", models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Taxas Adicionais")),
                ("valor_total", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Valor Total")),
                ("valor_pago", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Valor Pago")),
                ("status", models.CharField(
                    choices=[("pendente", "Pendente"), ("pago", "Pago"), ("parcial", "Parcial"), ("cancelado", "Cancelado")],
                    default="pendente",
                    max_length=20,
                    verbose_name="Status",
                )),
                ("condicao_pagamento", models.CharField(blank=True, max_length=50, verbose_name="Condição de Pagamento")),
                ("nfe_emitida", models.BooleanField(default=False, verbose_name="NF-e Emitida")),
                ("nfse_emitida", models.BooleanField(default=False, verbose_name="NFS-e Emitida")),
                ("lote", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="venda", to="lotes.lote")),
                ("arrematante_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="compras", to=settings.AUTH_USER_MODEL)),
                ("fechado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vendas_fechadas", to=settings.AUTH_USER_MODEL)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Venda", "verbose_name_plural": "Vendas", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Recebimento",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("forma", models.CharField(
                    choices=[("dinheiro", "Dinheiro"), ("pix", "PIX"), ("transferencia", "Transferência Bancária"), ("cheque", "Cheque"), ("debito", "Cartão de Débito"), ("credito", "Cartão de Crédito")],
                    max_length=20,
                    verbose_name="Forma de Pagamento",
                )),
                ("status", models.CharField(
                    choices=[("confirmado", "Confirmado"), ("estornado", "Estornado")],
                    default="confirmado",
                    max_length=20,
                    verbose_name="Status",
                )),
                ("valor", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Valor Recebido (R$)")),
                ("vencimento", models.DateField(blank=True, null=True, verbose_name="Vencimento / Data Prevista")),
                ("pago_em", models.DateField(blank=True, null=True, verbose_name="Data do Recebimento")),
                ("observacao", models.CharField(blank=True, max_length=500, verbose_name="Observação")),
                ("comprovante", models.FileField(blank=True, null=True, upload_to="financeiro/comprovantes/", verbose_name="Comprovante")),
                ("venda", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="recebimentos", to="financeiro.venda")),
                ("registrado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="recebimentos_registrados", to=settings.AUTH_USER_MODEL)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Recebimento", "verbose_name_plural": "Recebimentos", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Estorno",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("valor", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Valor Estornado")),
                ("motivo", models.TextField(verbose_name="Motivo")),
                ("recebimento", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="estornos", to="financeiro.recebimento")),
                ("realizado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Estorno", "verbose_name_plural": "Estornos"},
        ),
    ]
