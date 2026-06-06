import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("arrematex")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# ---------------------------------------------------------------------------
# Periodic tasks
# ---------------------------------------------------------------------------
app.conf.beat_schedule = {
    # Verifica validade de certificados a cada dia às 08h
    "check-cert-expiry": {
        "task": "apps.fiscal.tasks.check_certificate_expiry",
        "schedule": crontab(hour=8, minute=0),
    },
    # Processa NF-e em fila offline a cada 5 min
    "process-nfe-queue": {
        "task": "apps.fiscal.tasks.process_pending_nfe",
        "schedule": crontab(minute="*/5"),
    },
    # Sincroniza pesagens pendentes a cada 2 min
    "sync-scale-readings": {
        "task": "apps.balanca.tasks.sync_pending_readings",
        "schedule": crontab(minute="*/2"),
    },
    # Relatório diário de eventos às 23h50
    "daily-event-report": {
        "task": "apps.relatorios.tasks.generate_daily_summary",
        "schedule": crontab(hour=23, minute=50),
    },
    # Limpa tokens JWT expirados a cada hora
    "flush-expired-tokens": {
        "task": "apps.accounts.tasks.flush_expired_tokens",
        "schedule": crontab(minute=0),
    },
    # LGPD — purge dados por policy de retenção (diário 02h)
    "lgpd-data-retention": {
        "task": "apps.auditoria.tasks.enforce_retention_policy",
        "schedule": crontab(hour=2, minute=0),
    },
}
