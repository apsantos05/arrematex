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
            name="AuditLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user_email", models.EmailField(blank=True, verbose_name="E-mail (snap)")),
                ("acao", models.CharField(
                    choices=[
                        ("create", "Criação"), ("update", "Alteração"), ("delete", "Exclusão"),
                        ("login", "Login"), ("logout", "Logout"), ("login_fail", "Tentativa de Login"),
                        ("emitir_nf", "Emissão Fiscal"), ("cancelar_nf", "Cancelamento Fiscal"),
                        ("fechar_venda", "Fechamento de Venda"), ("estorno", "Estorno"),
                        ("enviar_cert", "Upload Certificado"), ("alterar_role", "Alteração de Perfil"),
                    ],
                    max_length=30,
                    verbose_name="Ação",
                )),
                ("model_name", models.CharField(blank=True, max_length=100, verbose_name="Model")),
                ("object_id", models.CharField(blank=True, max_length=100, verbose_name="ID Objeto")),
                ("object_repr", models.CharField(blank=True, max_length=300, verbose_name="Repr. Objeto")),
                ("dados_antes", models.JSONField(blank=True, null=True, verbose_name="Dados Antes")),
                ("dados_depois", models.JSONField(blank=True, null=True, verbose_name="Dados Depois")),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True, verbose_name="IP")),
                ("user_agent", models.CharField(blank=True, max_length=500, verbose_name="User Agent")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Log de Auditoria",
                "verbose_name_plural": "Logs de Auditoria",
                "ordering": ["-created_at"],
                "default_permissions": ("view",),
            },
        ),
    ]
