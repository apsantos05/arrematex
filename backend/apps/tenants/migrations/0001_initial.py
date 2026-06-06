from django.db import migrations, models
import django_tenants.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("schema_name", models.CharField(db_index=True, max_length=63, unique=True)),
                ("name", models.CharField(max_length=200, verbose_name="Razão Social")),
                ("trade_name", models.CharField(blank=True, max_length=200, verbose_name="Nome Fantasia")),
                ("cnpj", models.CharField(max_length=18, unique=True, verbose_name="CNPJ")),
                ("ie", models.CharField(blank=True, max_length=30, verbose_name="Inscrição Estadual")),
                ("email", models.EmailField(verbose_name="E-mail")),
                ("phone", models.CharField(blank=True, max_length=20, verbose_name="Telefone")),
                ("address_street", models.CharField(blank=True, max_length=200, verbose_name="Logradouro")),
                ("address_number", models.CharField(blank=True, max_length=10, verbose_name="Número")),
                ("address_complement", models.CharField(blank=True, max_length=100, verbose_name="Complemento")),
                ("address_district", models.CharField(blank=True, max_length=100, verbose_name="Bairro")),
                ("address_city", models.CharField(blank=True, max_length=100, verbose_name="Cidade")),
                ("address_state", models.CharField(blank=True, max_length=2, verbose_name="UF")),
                ("address_zipcode", models.CharField(blank=True, max_length=9, verbose_name="CEP")),
                ("address_ibge_code", models.CharField(blank=True, max_length=7, verbose_name="Código IBGE")),
                ("plan", models.CharField(
                    choices=[("basic", "Básico"), ("professional", "Profissional"), ("enterprise", "Enterprise")],
                    default="basic",
                    max_length=20,
                    verbose_name="Plano",
                )),
                ("status", models.CharField(
                    choices=[("active", "Ativo"), ("trial", "Trial"), ("suspended", "Suspenso"), ("cancelled", "Cancelado")],
                    default="trial",
                    max_length=20,
                    verbose_name="Status",
                )),
                ("trial_ends_at", models.DateTimeField(blank=True, null=True, verbose_name="Fim do Trial")),
                ("plan_expires_at", models.DateTimeField(blank=True, null=True, verbose_name="Expiração do Plano")),
                ("max_users", models.PositiveIntegerField(default=5, verbose_name="Máx. Usuários")),
                ("max_events_per_month", models.PositiveIntegerField(default=4, verbose_name="Máx. Eventos/mês")),
                ("max_lots_per_event", models.PositiveIntegerField(default=100, verbose_name="Máx. Lotes/evento")),
                ("logo", models.ImageField(blank=True, null=True, upload_to="tenants/logos/", verbose_name="Logo")),
                ("primary_color", models.CharField(default="#f5a623", max_length=7, verbose_name="Cor Primária")),
                ("secondary_color", models.CharField(default="#1a1a2e", max_length=7, verbose_name="Cor Secundária")),
                ("features_nfe", models.BooleanField(default=False, verbose_name="NF-e habilitado")),
                ("features_nfse", models.BooleanField(default=False, verbose_name="NFS-e habilitado")),
                ("features_balanca", models.BooleanField(default=False, verbose_name="Balança habilitado")),
                ("features_mfa", models.BooleanField(default=False, verbose_name="MFA habilitado")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={"verbose_name": "Tenant", "verbose_name_plural": "Tenants"},
        ),
        migrations.CreateModel(
            name="Domain",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("domain", models.CharField(db_index=True, max_length=253, unique=True)),
                ("is_primary", models.BooleanField(db_index=True, default=True)),
                ("tenant", models.ForeignKey(
                    on_delete=models.CASCADE,
                    related_name="domains",
                    to="tenants.tenant",
                )),
            ],
            options={"verbose_name": "Domínio", "verbose_name_plural": "Domínios"},
        ),
    ]
