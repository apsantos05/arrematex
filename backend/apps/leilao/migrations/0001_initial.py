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
            name="SessaoLeilao",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(
                    choices=[("inativa", "Inativa"), ("ativa", "Ativa"), ("pausada", "Pausada"), ("encerrada", "Encerrada")],
                    default="inativa",
                    max_length=20,
                    verbose_name="Status",
                )),
                ("lance_corrente", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="Lance Corrente")),
                ("arrematante_nome_livre", models.CharField(blank=True, max_length=200, verbose_name="Nome Arrematante (livre)")),
                ("telao_ativo", models.BooleanField(default=False, verbose_name="Telão Ativo")),
                ("telao_mensagem", models.CharField(blank=True, max_length=300, verbose_name="Mensagem no Telão")),
                ("aberto_em", models.DateTimeField(blank=True, null=True, verbose_name="Aberto em")),
                ("encerrado_em", models.DateTimeField(blank=True, null=True, verbose_name="Encerrado em")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("lote", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="sessao_leilao", to="lotes.lote")),
                ("leiloeiro", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sessoes_conduzidas", to=settings.AUTH_USER_MODEL)),
                ("arrematante_atual", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sessoes_arrematando", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Sessão de Leilão", "verbose_name_plural": "Sessões de Leilão", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Lance",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("valor", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Valor (R$)")),
                ("arrematante_nome_livre", models.CharField(blank=True, max_length=200, verbose_name="Nome Livre")),
                ("origem", models.CharField(
                    choices=[("manual", "Manual"), ("teclado", "Teclado Leiloeiro"), ("app", "Aplicativo")],
                    default="manual",
                    max_length=20,
                    verbose_name="Origem",
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("cancelado", models.BooleanField(default=False, verbose_name="Cancelado")),
                ("cancelado_motivo", models.CharField(blank=True, max_length=300, verbose_name="Motivo Cancelamento")),
                ("sessao", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lances", to="leilao.sessaoleilao")),
                ("arrematante", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="lances_dados", to=settings.AUTH_USER_MODEL)),
                ("registrado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lances_registrados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Lance", "verbose_name_plural": "Lances", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ConfiguracaoTelao",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("layout", models.CharField(choices=[("classico", "Clássico"), ("moderno", "Moderno")], default="moderno", max_length=20, verbose_name="Layout")),
                ("mostrar_historico", models.BooleanField(default=True, verbose_name="Mostrar Histórico de Lances")),
                ("quantidade_historico", models.PositiveIntegerField(default=5, verbose_name="Qtd. Lances no Histórico")),
                ("logo_url", models.URLField(blank=True, verbose_name="URL Logo no Telão")),
                ("mensagem_padrao", models.CharField(blank=True, max_length=300, verbose_name="Mensagem Padrão")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Configuração do Telão"},
        ),
    ]
