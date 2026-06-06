"""Utilitário para registrar AuditLog de forma segura."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def registrar_log(
    usuario=None,
    acao: str = "create",
    model_name: str = "",
    object_id: str = "",
    object_repr: str = "",
    dados_antes=None,
    dados_depois=None,
    ip: str = "",
    user_agent: str = "",
    user_email: str = "",
):
    """Insere AuditLog de forma assíncrona via Celery para não bloquear a request."""
    try:
        from apps.auditoria.tasks import registrar_log_task
        registrar_log_task.delay(
            user_id=str(usuario.id) if usuario else None,
            user_email=user_email or (usuario.email if usuario else ""),
            acao=acao,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            dados_antes=dados_antes,
            dados_depois=dados_depois,
            ip_address=ip,
            user_agent=user_agent,
        )
    except Exception as exc:
        logger.warning("Falha ao enfileirar AuditLog: %s", exc)
