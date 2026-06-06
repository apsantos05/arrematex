"""Middleware de auditoria — captura IP e user agent em ações HTTP críticas."""
import logging

logger = logging.getLogger(__name__)

AUDITORIA_PATHS = ("/api/v1/fiscal/", "/api/v1/financeiro/", "/api/v1/auth/")


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Anexa IP e UA ao request para uso nas views
        request._audit_ip = self._get_ip(request)
        request._audit_ua = request.META.get("HTTP_USER_AGENT", "")[:500]
        return response

    @staticmethod
    def _get_ip(request) -> str:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
