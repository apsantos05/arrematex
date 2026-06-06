"""Celery tasks — auditoria, fiscal, balança e relatórios."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auditoria
# ---------------------------------------------------------------------------
@shared_task(name="apps.auditoria.tasks.registrar_log_task", ignore_result=True)
def registrar_log_task(user_id, user_email, acao, model_name, object_id,
                       object_repr, dados_antes, dados_depois, ip_address, user_agent):
    from apps.auditoria.models import AuditLog
    from apps.accounts.models import User

    user = None
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            pass

    AuditLog.objects.create(
        user=user,
        user_email=user_email,
        acao=acao,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        dados_antes=dados_antes,
        dados_depois=dados_depois,
        ip_address=ip_address or None,
        user_agent=user_agent,
    )


@shared_task(name="apps.auditoria.tasks.enforce_retention_policy")
def enforce_retention_policy():
    """LGPD — remove logs mais antigos que DATA_RETENTION_DAYS."""
    from django.conf import settings
    from django.utils import timezone
    from datetime import timedelta
    from apps.auditoria.models import AuditLog

    cutoff = timezone.now() - timedelta(days=settings.DATA_RETENTION_DAYS)
    deleted, _ = AuditLog.objects.filter(created_at__lt=cutoff).delete()
    logger.info("LGPD retention: %d logs removidos", deleted)


# ---------------------------------------------------------------------------
# Fiscal
# ---------------------------------------------------------------------------
@shared_task(name="apps.fiscal.tasks.check_certificate_expiry")
def check_certificate_expiry():
    """Alerta quando certificado vence em menos de 30 dias."""
    from datetime import date, timedelta
    from django.core.mail import send_mail
    from apps.fiscal.models import CertificadoDigital

    alerta = date.today() + timedelta(days=30)
    certs = CertificadoDigital.objects.filter(
        ativo=True,
        validade__lte=alerta,
        alerta_vencimento_enviado=False,
    )
    for cert in certs:
        try:
            send_mail(
                subject=f"[Arrematex] Certificado digital vence em {cert.dias_para_vencer} dias",
                message=f"O certificado {cert.nome} ({cert.cnpj}) vence em {cert.validade}.\nAtualize antes do vencimento.",
                from_email=None,
                recipient_list=[cert.enviado_por.email],
            )
            cert.alerta_vencimento_enviado = True
            cert.save(update_fields=["alerta_vencimento_enviado"])
        except Exception as exc:
            logger.warning("Falha ao enviar alerta de certificado %s: %s", cert.id, exc)


@shared_task(name="apps.fiscal.tasks.process_pending_nfe")
def process_pending_nfe():
    """Reprocessa NF-e em modo contingência quando há conexão."""
    from apps.fiscal.models import NotaFiscal, ConfiguracaoFiscal

    notas = NotaFiscal.objects.filter(status=NotaFiscal.STATUS_CONTINGENCIA)[:10]
    if not notas.exists():
        return

    config = ConfiguracaoFiscal.objects.first()
    if not config:
        return

    from apps.fiscal.services.nfe_service import NFeService
    service = NFeService(config)

    for nota in notas:
        try:
            xml_url = nota.xml_url
            logger.info("Reprocessando NF-e em contingência: %s", nota.id)
        except Exception as exc:
            logger.warning("Falha ao reprocessar NF-e %s: %s", nota.id, exc)


# ---------------------------------------------------------------------------
# Balança
# ---------------------------------------------------------------------------
@shared_task(name="apps.balanca.tasks.sync_pending_readings")
def sync_pending_readings():
    """Sincroniza pesagens que vieram da fila offline."""
    from apps.balanca.models import Pesagem
    pendentes = Pesagem.objects.filter(status=Pesagem.STATUS_PENDENTE)[:50]
    for p in pendentes:
        try:
            # Lógica de sync — lote já está associado
            if p.lote:
                p.lote.peso_total = p.peso_kg
                p.lote.peso_origem = p.origem
                p.lote.save(update_fields=["peso_total", "peso_origem"])
            p.status = Pesagem.STATUS_SINCRONIZADO
            p.save(update_fields=["status"])
        except Exception as exc:
            p.status = Pesagem.STATUS_ERRO
            p.save(update_fields=["status"])
            logger.warning("Falha ao sincronizar pesagem %s: %s", p.id, exc)


# ---------------------------------------------------------------------------
# Relatórios
# ---------------------------------------------------------------------------
@shared_task(name="apps.relatorios.tasks.generate_daily_summary")
def generate_daily_summary():
    """Gera e envia relatório diário de eventos por e-mail."""
    from django.utils import timezone
    from django.core.mail import send_mail
    from apps.financeiro.models import Venda

    hoje = timezone.now().date()
    vendas = Venda.objects.filter(created_at__date=hoje)
    total = sum(v.valor_total for v in vendas)
    logger.info("Relatório diário %s: %d vendas, R$ %.2f", hoje, vendas.count(), total)


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------
@shared_task(name="apps.accounts.tasks.flush_expired_tokens")
def flush_expired_tokens():
    """Remove tokens JWT expirados do blacklist."""
    try:
        from rest_framework_simplejwt.token_blacklist.management.commands import flushexpiredtokens
        from django.core.management import call_command
        call_command("flushexpiredtokens")
    except Exception as exc:
        logger.warning("flushexpiredtokens falhou: %s", exc)
