"""Tenant model — cada empresa é um schema PostgreSQL isolado."""
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Tenant(TenantMixin):
    """Empresa/cliente do SaaS."""

    PLAN_BASIC = "basic"
    PLAN_PROFESSIONAL = "professional"
    PLAN_ENTERPRISE = "enterprise"
    PLAN_CHOICES = [
        (PLAN_BASIC, "Básico"),
        (PLAN_PROFESSIONAL, "Profissional"),
        (PLAN_ENTERPRISE, "Enterprise"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_TRIAL = "trial"
    STATUS_SUSPENDED = "suspended"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Ativo"),
        (STATUS_TRIAL, "Trial"),
        (STATUS_SUSPENDED, "Suspenso"),
        (STATUS_CANCELLED, "Cancelado"),
    ]

    # Identificação
    name = models.CharField("Razão Social", max_length=200)
    trade_name = models.CharField("Nome Fantasia", max_length=200, blank=True)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    ie = models.CharField("Inscrição Estadual", max_length=30, blank=True)
    email = models.EmailField("E-mail")
    phone = models.CharField("Telefone", max_length=20, blank=True)

    # Endereço
    address_street = models.CharField("Logradouro", max_length=200, blank=True)
    address_number = models.CharField("Número", max_length=10, blank=True)
    address_complement = models.CharField("Complemento", max_length=100, blank=True)
    address_district = models.CharField("Bairro", max_length=100, blank=True)
    address_city = models.CharField("Cidade", max_length=100, blank=True)
    address_state = models.CharField("UF", max_length=2, blank=True)
    address_zipcode = models.CharField("CEP", max_length=9, blank=True)
    address_ibge_code = models.CharField("Código IBGE", max_length=7, blank=True)

    # Plano e status
    plan = models.CharField("Plano", max_length=20, choices=PLAN_CHOICES, default=PLAN_BASIC)
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_TRIAL)
    trial_ends_at = models.DateTimeField("Fim do Trial", null=True, blank=True)
    plan_expires_at = models.DateTimeField("Expiração do Plano", null=True, blank=True)

    # Limites por plano (sobrescritos pelo super admin)
    max_users = models.PositiveIntegerField("Máx. Usuários", default=5)
    max_events_per_month = models.PositiveIntegerField("Máx. Eventos/mês", default=4)
    max_lots_per_event = models.PositiveIntegerField("Máx. Lotes/evento", default=100)

    # White-label
    logo = models.ImageField("Logo", upload_to="tenants/logos/", null=True, blank=True)
    primary_color = models.CharField("Cor Primária", max_length=7, default="#f5a623")
    secondary_color = models.CharField("Cor Secundária", max_length=7, default="#1a1a2e")

    # Features habilitadas
    features_nfe = models.BooleanField("NF-e habilitado", default=False)
    features_nfse = models.BooleanField("NFS-e habilitado", default=False)
    features_balanca = models.BooleanField("Balança habilitado", default=False)
    features_mfa = models.BooleanField("MFA habilitado", default=False)

    # Auditoria
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    auto_create_schema = True

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self):
        return f"{self.trade_name or self.name} ({self.schema_name})"


class Domain(DomainMixin):
    """Domínio/subdomínio associado a um tenant."""

    class Meta:
        verbose_name = "Domínio"
        verbose_name_plural = "Domínios"
