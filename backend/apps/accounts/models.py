"""User model com RBAC por tenant."""
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("E-mail é obrigatório.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.ROLE_ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Usuário do sistema — escoped por tenant schema."""

    ROLE_SUPER_ADMIN = "super_admin"
    ROLE_ADMIN = "admin"
    ROLE_LEILOEIRO = "leiloeiro"
    ROLE_OPERADOR = "operador"
    ROLE_CAIXA = "caixa"
    ROLE_FISCAL = "fiscal"
    ROLE_COMPRADOR = "comprador"

    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, "Super Admin"),
        (ROLE_ADMIN, "Administrador"),
        (ROLE_LEILOEIRO, "Leiloeiro"),
        (ROLE_OPERADOR, "Operador de Pista"),
        (ROLE_CAIXA, "Caixa/Financeiro"),
        (ROLE_FISCAL, "Fiscal/Contador"),
        (ROLE_COMPRADOR, "Comprador"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("E-mail", unique=True)
    full_name = models.CharField("Nome Completo", max_length=200)
    cpf = models.CharField("CPF", max_length=14, blank=True)
    phone = models.CharField("Telefone", max_length=20, blank=True)
    role = models.CharField("Perfil", max_length=30, choices=ROLE_CHOICES, default=ROLE_OPERADOR)

    # MFA (TOTP)
    mfa_enabled = models.BooleanField("MFA Ativado", default=False)
    mfa_secret = models.CharField("Segredo MFA", max_length=64, blank=True)

    # Status
    is_active = models.BooleanField("Ativo", default=True)
    is_staff = models.BooleanField("Staff", default=False)

    # Configurações
    timezone = models.CharField("Fuso horário", max_length=50, default="America/Sao_Paulo")
    avatar = models.ImageField("Avatar", upload_to="avatars/", null=True, blank=True)

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)
    last_login_ip = models.GenericIPAddressField("Último IP", null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def is_admin(self):
        return self.role in (self.ROLE_SUPER_ADMIN, self.ROLE_ADMIN)

    @property
    def can_manage_auction(self):
        return self.role in (self.ROLE_SUPER_ADMIN, self.ROLE_ADMIN, self.ROLE_LEILOEIRO)

    @property
    def can_manage_fiscal(self):
        return self.role in (self.ROLE_SUPER_ADMIN, self.ROLE_ADMIN, self.ROLE_FISCAL, self.ROLE_CAIXA)
