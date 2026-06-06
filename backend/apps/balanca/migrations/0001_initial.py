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
            name="ProviderBalanca",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=100, verbose_name="Nome")),
                ("tipo", models.CharField(choices=[("http_rest", "HTTP REST"), ("serial", "Serial/USB"), ("tcp", "TCP/IP")], default="http_rest", max_length=20, verbose_name="Tipo")),
                ("status", models.CharField(choices=[("ativo", "Ativo"), ("inativo", "Inativo")], default="ativo", max_length=10, verbose_name="Status")),
                ("config", models.JSONField(default=dict, verbose_name="Configuração de Conexão")),
                ("device_id", models.CharField(blank=True, max_length=100, verbose_name="ID do Dispositivo")),
                ("descricao", models.TextField(blank=True, verbose_name="Descrição")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Provedor de Balança", "verbose_name_plural": "Provedores de Balança"},
        ),
        migrations.CreateModel(
            name="Pesagem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("peso_kg", models.DecimalField(decimal_places=3, max_digits=10, verbose_name="Peso (kg)")),
                ("origem", models.CharField(choices=[("manual", "Manual"), ("balanca_api", "Balança API"), ("balanca_local", "Balança Local"), ("offline_queue", "Fila Offline")], default="manual", max_length=20, verbose_name="Origem")),
                ("status", models.CharField(choices=[("pendente", "Pendente Sincronização"), ("sincronizado", "Sincronizado"), ("erro", "Erro")], default="sincronizado", max_length=20, verbose_name="Status Sync")),
                ("device_id", models.CharField(blank=True, max_length=100, verbose_name="Device ID")),
                ("leitura_timestamp", models.DateTimeField(verbose_name="Timestamp da Leitura")),
                ("dados_brutos", models.JSONField(blank=True, default=dict, verbose_name="Dados Brutos")),
                ("lote", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pesagens", to="lotes.lote")),
                ("provider", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pesagens", to="balanca.providerbalanca")),
                ("registrado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pesagens_registradas", to=settings.AUTH_USER_MODEL)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Pesagem", "verbose_name_plural": "Pesagens", "ordering": ["-leitura_timestamp"]},
        ),
    ]
