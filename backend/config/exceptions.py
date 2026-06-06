"""Custom exception handler — returns consistent JSON for all errors."""
import logging

from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, Http404):
        return Response(
            {"detail": "Recurso não encontrado.", "code": "not_found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if response is not None:
        error_data = {
            "detail": response.data.get("detail", str(exc)) if isinstance(response.data, dict) else response.data,
            "code": getattr(exc, "default_code", "error"),
            "status_code": response.status_code,
        }

        if isinstance(response.data, dict) and "non_field_errors" not in response.data:
            field_errors = {k: v for k, v in response.data.items() if k not in ("detail", "code")}
            if field_errors:
                error_data["errors"] = field_errors

        response.data = error_data
        return response

    logger.exception("Unhandled exception", exc_info=exc)
    return Response(
        {"detail": "Erro interno do servidor.", "code": "server_error"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
