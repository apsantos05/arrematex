"""Auditoria — middleware e model de log de ações críticas."""
import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Registro imutável de cada ação relevante no sistema."""

    ACAO_CREATE = "create"
    ACAO_UPDATE = "update"
    ACAO_DELETE = "delete"
    ACAO_LOGIN = "login"
    ACAO_LOGOUT = "logout"
    ACAO_LOGIN_FAIL = "login_fail"
    ACAO_EMITIR_NF = "emitir_nf"
    ACAO_CANCELAR_NF = "cancelar_nf"
    ACAO_FECHAR_VENDA = "fechar_venda"
    ACAO_ESTORNO = "estorno"
    ACAO_ENVIAR_CERT = "enviar_cert"
    ACAO_ALTERAR_ROLE = "alterar_role"
    ACAO_CHOICES = [
        (ACAO_CREATE, "Criação"),
        (ACAO_UPDATE, "Alteração"),
        (ACAO_DELETE, "Exclusão"),
        (ACAO_LOGIN, "Login"),
        (ACAO_LOGOUT, "Logout"),
        (ACAO_LOGIN_FAIL, "Tentativa de Login"),
        (ACAO_EMITIR_NF, "Emissão Fiscal"),
        (ACAO_CANCELAR_NF, "Cancelamento Fiscal"),
        (ACAO_FECHAR_VENDA, "Fechamento de Venda"),
        (ACAO_ESTORNO, "Estorno"),
        (ACAO_ENVIAR_CERT, "Upload Certificado"),
        (ACAO_ALTERAR_ROLE, "Alteração de Perfil"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    user_email = models.EmailField("E-mail (snap)", blank=True)
    acao = models.CharField("Ação", max_length=30, choices=ACAO_CHOICES)

    # Objeto afetado
    model_name = models.CharField("Model", max_length=100, blank=True)
    object_id = models.CharField("ID Objeto", max_length=100, blank=True)
    object_repr = models.CharField("Repr. Objeto", max_length=300, blank=True)

    # Diff de dados
    dados_antes = models.JSONField("Dados Antes", null=True, blank=True)
    dados_depois = models.JSONField("Dados Depois", null=True, blank=True)

    # Contexto de rede
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("User Agent", max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        ordering = ["-created_at"]
        # Garante que logs não sejam alterados via ORM padrão
        default_permissions = ("view",)

    def __str__(self):
        return f"{self.acao} por {self.user_email} em {self.created_at}"

    def save(self, *args, **kwargs):
        # Logs são imutáveis — nunca atualiza, apenas insere
        if self.pk:
            raise ValueError("AuditLog é imutável. Não pode ser alterado.")
        super().save(*args, **kwargs)
