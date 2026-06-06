"""
JWT Auth Middleware for Django Channels WebSocket connections.
Reads ?token=<JWT> from the query string and sets scope["user"].
Also resolves the tenant schema from the Host header.
"""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _get_user(token_key: str, schema_name: str):
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
    from django_tenants.utils import schema_context

    try:
        with schema_context(schema_name):
            payload = AccessToken(token_key)
            user_id = payload["user_id"]
            from apps.accounts.models import User
            user = User.objects.get(id=user_id)
            # Store the resolved schema so consumers can use it
            user._ws_schema = schema_name
            return user
    except (TokenError, InvalidToken, Exception):
        return AnonymousUser()


def _resolve_schema(headers: list) -> str:
    """Return schema_name from Host header (mirrors TenantMainMiddleware logic)."""
    host = ""
    for name, value in headers:
        if name == b"host":
            host = value.decode().split(":")[0]
            break

    if not host:
        return "dev"

    try:
        from apps.tenants.models import Domain
        domain_obj = Domain.objects.select_related("tenant").get(domain=host)
        return domain_obj.tenant.schema_name
    except Exception:
        # Fallback to 'dev' for local development
        return "dev"


class JWTAuthMiddleware:
    """Wraps inner ASGI app, injecting scope['user'] from JWT query param."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            qs = scope.get("query_string", b"").decode()
            params = parse_qs(qs)
            token_list = params.get("token", [])

            schema_name = await database_sync_to_async(_resolve_schema)(scope.get("headers", []))
            scope["_tenant_schema"] = schema_name

            if token_list:
                scope["user"] = await _get_user(token_list[0], schema_name)
            else:
                scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
