import uuid
import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, verbose_name="superuser status")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="E-mail")),
                ("full_name", models.CharField(max_length=200, verbose_name="Nome Completo")),
                ("cpf", models.CharField(blank=True, max_length=14, verbose_name="CPF")),
                ("phone", models.CharField(blank=True, max_length=20, verbose_name="Telefone")),
                ("role", models.CharField(
                    choices=[
                        ("super_admin", "Super Admin"),
                        ("admin", "Administrador"),
                        ("leiloeiro", "Leiloeiro"),
                        ("operador", "Operador de Pista"),
                        ("caixa", "Caixa/Financeiro"),
                        ("fiscal", "Fiscal/Contador"),
                        ("comprador", "Comprador"),
                    ],
                    default="operador",
                    max_length=30,
                    verbose_name="Perfil",
                )),
                ("mfa_enabled", models.BooleanField(default=False, verbose_name="MFA Ativado")),
                ("mfa_secret", models.CharField(blank=True, max_length=64, verbose_name="Segredo MFA")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("is_staff", models.BooleanField(default=False, verbose_name="Staff")),
                ("timezone", models.CharField(default="America/Sao_Paulo", max_length=50, verbose_name="Fuso horário")),
                ("avatar", models.ImageField(blank=True, null=True, upload_to="avatars/", verbose_name="Avatar")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                ("last_login_ip", models.GenericIPAddressField(blank=True, null=True, verbose_name="Último IP")),
                ("groups", models.ManyToManyField(
                    blank=True,
                    related_name="accounts_user_groups",
                    related_query_name="accounts_user",
                    to="auth.group",
                    verbose_name="groups",
                )),
                ("user_permissions", models.ManyToManyField(
                    blank=True,
                    related_name="accounts_user_permissions",
                    related_query_name="accounts_user",
                    to="auth.permission",
                    verbose_name="user permissions",
                )),
            ],
            options={
                "verbose_name": "Usuário",
                "verbose_name_plural": "Usuários",
                "ordering": ["full_name"],
            },
            managers=[
                ("objects", django.contrib.auth.models.BaseUserManager()),
            ],
        ),
    ]
