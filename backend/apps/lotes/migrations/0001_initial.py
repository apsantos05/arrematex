import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Categoria",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=100, verbose_name="Nome")),
                ("descricao", models.TextField(blank=True, verbose_name="Descrição")),
            ],
            options={"verbose_name": "Categoria", "verbose_name_plural": "Categorias", "ordering": ["nome"]},
        ),
        migrations.CreateModel(
            name="Vendedor",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=200, verbose_name="Nome")),
                ("cpf_cnpj", models.CharField(max_length=18, verbose_name="CPF/CNPJ")),
                ("telefone", models.CharField(blank=True, max_length=20, verbose_name="Telefone")),
                ("email", models.EmailField(blank=True, verbose_name="E-mail")),
                ("cidade", models.CharField(blank=True, max_length=100, verbose_name="Cidade")),
                ("estado", models.CharField(blank=True, max_length=2, verbose_name="UF")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Vendedor", "verbose_name_plural": "Vendedores", "ordering": ["nome"]},
        ),
        migrations.CreateModel(
            name="Evento",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=200, verbose_name="Nome do Evento")),
                ("data", models.DateField(verbose_name="Data")),
                ("local", models.CharField(blank=True, max_length=200, verbose_name="Local")),
                ("status", models.CharField(
                    choices=[("agendado", "Agendado"), ("aberto", "Aberto"), ("encerrado", "Encerrado")],
                    default="agendado",
                    max_length=20,
                    verbose_name="Status",
                )),
                ("descricao", models.TextField(blank=True, verbose_name="Descrição")),
                ("criado_por", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="eventos_criados",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Evento", "verbose_name_plural": "Eventos", "ordering": ["-data"]},
        ),
        migrations.CreateModel(
            name="Lote",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("numero", models.PositiveIntegerField(verbose_name="Nº do Lote")),
                ("descricao", models.CharField(max_length=300, verbose_name="Descrição")),
                ("quantidade", models.PositiveIntegerField(verbose_name="Quantidade")),
                ("peso_total", models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Peso Total (kg)")),
                ("peso_origem", models.CharField(
                    choices=[("manual", "Manual"), ("balanca_api", "Balança API"), ("balanca_local", "Balança Local")],
                    default="manual",
                    max_length=20,
                    verbose_name="Origem do Peso",
                )),
                ("lance_inicial", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Lance Inicial (R$)")),
                ("incremento", models.DecimalField(decimal_places=2, default=50, max_digits=10, verbose_name="Incremento Padrão (R$)")),
                ("lance_atual", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Lance Atual (R$)")),
                ("condicao_pagamento", models.CharField(
                    choices=[("a_vista", "À Vista"), ("30_dias", "30 Dias"), ("60_dias", "60 Dias"), ("90_dias", "90 Dias"), ("parcelado", "Parcelado")],
                    default="a_vista",
                    max_length=20,
                    verbose_name="Condição de Pagamento",
                )),
                ("status", models.CharField(
                    choices=[("aguardando", "Aguardando"), ("em_leilao", "Em Leilão"), ("vendido", "Vendido"), ("retirado", "Retirado")],
                    default="aguardando",
                    max_length=20,
                    verbose_name="Status",
                )),
                ("documentos", models.JSONField(blank=True, default=dict, verbose_name="Documentos Adicionais")),
                ("evento", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lotes", to="lotes.evento")),
                ("categoria", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="lotes.categoria")),
                ("vendedor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="lotes.vendedor")),
                ("cadastrado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lotes_cadastrados", to=settings.AUTH_USER_MODEL)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Lote",
                "verbose_name_plural": "Lotes",
                "ordering": ["evento", "numero"],
                "unique_together": {("evento", "numero")},
            },
        ),
    ]
