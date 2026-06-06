"""
WebSocket consumers — leilão em tempo real e telão TV.
Canal: leilao_{evento_id}  — leiloeiro + operadores
Canal: telao_{evento_id}   — display público (TV)
"""
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

logger = logging.getLogger(__name__)


class LeilaoConsumer(AsyncWebsocketConsumer):
    """
    Canal privado do leiloeiro/operadores.
    Requer autenticação JWT no handshake via query param ?token=...
    """

    @property
    def _schema(self):
        return self.scope.get("_tenant_schema", "dev")

    async def connect(self):
        self.evento_id = self.scope["url_route"]["kwargs"]["evento_id"]
        self.group = f"leilao_{self.evento_id}"

        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        if not user.can_manage_auction:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        logger.info("WS leilao: %s conectado ao evento %s (schema=%s)", user.email, self.evento_id, self._schema)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data):
        """Recebe ações do leiloeiro e processa."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get("action")
        user = self.scope["user"]

        if action == "novo_lance":
            await self._processar_lance(data, user)
        elif action == "abrir_lote":
            await self._abrir_lote(data, user)
        elif action == "fechar_lote":
            await self._fechar_lote(data, user)
        elif action == "atualizar_telao":
            await self._atualizar_telao(data, user)
        elif action == "enviar_mensagem_telao":
            await self._enviar_mensagem_telao(data, user)

    # ------------------------------------------------------------------
    # Handlers de ação
    # ------------------------------------------------------------------
    async def _processar_lance(self, data, user):
        from apps.leilao.services import processar_lance
        from django_tenants.utils import schema_context

        def _run():
            with schema_context(self._schema):
                return processar_lance(
                    sessao_id=data["sessao_id"],
                    valor=data["valor"],
                    arrematante_nome=data.get("arrematante_nome", ""),
                    registrado_por=user,
                )

        resultado = await database_sync_to_async(_run)()
        payload = {
            "type": "lance_registrado",
            "sessao_id": str(resultado["sessao_id"]),
            "valor": str(resultado["valor"]),
            "arrematante": resultado["arrematante"],
            "preco_kg": str(resultado["preco_kg"]),
            "timestamp": timezone.now().isoformat(),
        }
        await self.channel_layer.group_send(self.group, {"type": "broadcast", "payload": payload})
        await self.channel_layer.group_send(
            f"telao_{self.evento_id}", {"type": "broadcast", "payload": {**payload, "type": "atualizar_lance"}}
        )

    async def _abrir_lote(self, data, user):
        from apps.leilao.services import abrir_lote
        from django_tenants.utils import schema_context

        def _run():
            with schema_context(self._schema):
                return abrir_lote(lote_id=data["lote_id"], leiloeiro=user)

        sessao = await database_sync_to_async(_run)()
        payload = {
            "type": "lote_aberto",
            "sessao_id": str(sessao.id),
            "lote_id": str(sessao.lote_id),
            "lote_numero": sessao.lote.numero,
            "lote_descricao": sessao.lote.descricao,
            "lote_peso": str(sessao.lote.peso_total),
            "lance_inicial": str(sessao.lote.lance_inicial),
            "timestamp": timezone.now().isoformat(),
        }
        await self.channel_layer.group_send(self.group, {"type": "broadcast", "payload": payload})
        await self.channel_layer.group_send(
            f"telao_{self.evento_id}", {"type": "broadcast", "payload": {**payload, "type": "lote_aberto"}}
        )

    async def _fechar_lote(self, data, user):
        from apps.leilao.services import fechar_lote
        from django_tenants.utils import schema_context

        def _run():
            with schema_context(self._schema):
                return fechar_lote(sessao_id=data["sessao_id"], encerrado_por=user)

        resultado = await database_sync_to_async(_run)()
        payload = {
            "type": "lote_fechado",
            "sessao_id": data["sessao_id"],
            "vendido": resultado["vendido"],
            "valor_final": str(resultado.get("valor_final", 0)),
            "arrematante": resultado.get("arrematante", ""),
            "timestamp": timezone.now().isoformat(),
        }
        await self.channel_layer.group_send(self.group, {"type": "broadcast", "payload": payload})
        await self.channel_layer.group_send(
            f"telao_{self.evento_id}", {"type": "broadcast", "payload": {**payload, "type": "lote_fechado"}}
        )

    async def _atualizar_telao(self, data, user):
        if not user.is_admin:
            return
        await self.channel_layer.group_send(
            f"telao_{self.evento_id}",
            {"type": "broadcast", "payload": {**data, "type": "atualizar_telao"}},
        )

    async def _enviar_mensagem_telao(self, data, user):
        if not user.is_admin:
            return
        await self.channel_layer.group_send(
            f"telao_{self.evento_id}",
            {"type": "broadcast", "payload": {"type": "mensagem_telao", "mensagem": data.get("mensagem", "")}},
        )

    # ------------------------------------------------------------------
    # Broadcast handler
    # ------------------------------------------------------------------
    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event["payload"]))


class TelaoConsumer(AsyncWebsocketConsumer):
    """
    Canal público do telão TV — somente leitura, sem autenticação.
    Recebe atualizações do LeilaoConsumer via channel layer.
    """

    async def connect(self):
        self.evento_id = self.scope["url_route"]["kwargs"]["evento_id"]
        self.group = f"telao_{self.evento_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data):
        # Telão é somente leitura — ignora mensagens recebidas
        pass

    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event["payload"]))



class LeilaoConsumer(AsyncWebsocketConsumer):
    """
    Canal privado do leiloeiro/operadores.
    Requer autenticação JWT no handshake via query param ?token=...
    """

    async def connect(self):
        self.evento_id = self.scope["url_route"]["kwargs"]["evento_id"]
        self.group = f"leilao_{self.evento_id}"

        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        if not user.can_manage_auction:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        logger.info("WS leilao: %s conectado ao evento %s", user.email, self.evento_id)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data):
        """Recebe ações do leiloeiro e processa."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get("action")
        user = self.scope["user"]

        if action == "novo_lance":
            await self._processar_lance(data, user)
        elif action == "abrir_lote":
            await self._abrir_lote(data, user)
        elif action == "fechar_lote":
            await self._fechar_lote(data, user)
        elif action == "get_estado":
            await self._get_estado()
        elif action == "atualizar_telao":
            await self._atualizar_telao(data, user)
        elif action == "enviar_mensagem_telao":
            await self._enviar_mensagem_telao(data, user)

    # ------------------------------------------------------------------
    # Handlers de ação
    # ------------------------------------------------------------------
    async def _processar_lance(self, data, user):
        from apps.leilao.services import processar_lance
        from django_tenants.utils import schema_context
        schema = self.scope.get("_tenant_schema", "dev")
        def _run():
            with schema_context(schema):
                return processar_lance(
                    sessao_id=data["sessao_id"],
                    valor=data["valor"],
                    arrematante_nome=data.get("arrematante_nome", ""),
                    registrado_por=user,
                )
        resultado = await database_sync_to_async(_run)()
        payload = {
            "type": "lance_registrado",
            "sessao_id": str(resultado["sessao_id"]),
            "valor": str(resultado["valor"]),
            "arrematante": resultado["arrematante"],
            "preco_kg": str(resultado["preco_kg"]),
            "timestamp": timezone.now().isoformat(),
        }
        # Broadcast para o grupo do leilão
        await self.channel_layer.group_send(self.group, {"type": "broadcast", "payload": payload})
        # Atualiza telão
        await self.channel_layer.group_send(
            f"telao_{self.evento_id}", {"type": "broadcast", "payload": {**payload, "type": "atualizar_lance"}}
        )

    async def _abrir_lote(self, data, user):
        from apps.leilao.services import abrir_lote
        from django_tenants.utils import schema_context
        schema = self.scope.get("_tenant_schema", "dev")
        def _run():
            with schema_context(schema):
                sessao = abrir_lote(lote_id=data["lote_id"], leiloeiro=user)
                lances_qs = list(
                    sessao.lances.filter(cancelado=False)
                    .order_by("-created_at")[:10]
                    .values("valor", "arrematante_nome_livre", "created_at")
                )
                peso = float(sessao.lote.peso_total) if sessao.lote.peso_total else 0
                return {
                    "id": str(sessao.id),
                    "lote_id": str(sessao.lote_id),
                    "lote_numero": sessao.lote.numero,
                    "lote_descricao": sessao.lote.descricao,
                    "lote_peso": str(sessao.lote.peso_total),
                    "lance_inicial": str(sessao.lote.lance_inicial),
                    "lance_corrente": str(sessao.lance_corrente) if sessao.lance_corrente else None,
                    "lances": [
                        {
                            "valor": str(l["valor"]),
                            "arrematante": l["arrematante_nome_livre"],
                            "preco_kg": str(round(float(l["valor"]) / peso, 2)) if peso else "0",
                            "timestamp": l["created_at"].isoformat(),
                        }
                        for l in lances_qs
                    ],
                }
        info = await database_sync_to_async(_run)()
        payload = {
            "type": "lote_aberto",
            "sessao_id": info["id"],
            "lote_id": info["lote_id"],
            "lote_numero": info["lote_numero"],
            "lote_descricao": info["lote_descricao"],
            "lote_peso": info["lote_peso"],
            "lance_inicial": info["lance_inicial"],
            "lance_corrente": info["lance_corrente"],
            "lances": info["lances"],
            "timestamp": timezone.now().isoformat(),
        }
        await self.channel_layer.group_send(self.group, {"type": "broadcast", "payload": payload})
        await self.channel_layer.group_send(
            f"telao_{self.evento_id}", {"type": "broadcast", "payload": {**payload, "type": "lote_aberto"}}
        )

    async def _fechar_lote(self, data, user):
        from apps.leilao.services import fechar_lote
        from django_tenants.utils import schema_context
        schema = self.scope.get("_tenant_schema", "dev")
        def _run():
            with schema_context(schema):
                return fechar_lote(sessao_id=data["sessao_id"], encerrado_por=user)
        resultado = await database_sync_to_async(_run)()
        payload = {
            "type": "lote_fechado",
            "sessao_id": data["sessao_id"],
            "vendido": resultado["vendido"],
            "valor_final": str(resultado.get("valor_final", 0)),
            "arrematante": resultado.get("arrematante", ""),
            "timestamp": timezone.now().isoformat(),
        }
        await self.channel_layer.group_send(self.group, {"type": "broadcast", "payload": payload})
        await self.channel_layer.group_send(
            f"telao_{self.evento_id}", {"type": "broadcast", "payload": {**payload, "type": "lote_fechado"}}
        )

    async def _get_estado(self):
        """Retorna estado atual da sessão ativa para reconexão/reload."""
        from apps.leilao.models import SessaoLeilao
        from django_tenants.utils import schema_context
        schema = self.scope.get("_tenant_schema", "dev")

        def _run():
            with schema_context(schema):
                try:
                    sessao = SessaoLeilao.objects.select_related("lote").get(
                        lote__evento_id=self.evento_id,
                        status=SessaoLeilao.STATUS_ATIVA,
                    )
                    lances_qs = list(
                        sessao.lances.filter(cancelado=False)
                        .order_by("-created_at")[:10]
                        .values("valor", "arrematante_nome_livre", "created_at")
                    )
                    peso = float(sessao.lote.peso_total) if sessao.lote.peso_total else 0
                    return {
                        "sessao_id": str(sessao.id),
                        "lote_id": str(sessao.lote_id),
                        "lote_numero": sessao.lote.numero,
                        "lote_descricao": sessao.lote.descricao,
                        "lote_peso": str(sessao.lote.peso_total),
                        "lance_inicial": str(sessao.lote.lance_inicial),
                        "lance_corrente": str(sessao.lance_corrente) if sessao.lance_corrente else None,
                        "lances": [
                            {
                                "valor": str(l["valor"]),
                                "arrematante": l["arrematante_nome_livre"],
                                "preco_kg": str(round(float(l["valor"]) / peso, 2)) if peso else "0",
                                "timestamp": l["created_at"].isoformat(),
                            }
                            for l in lances_qs
                        ],
                    }
                except SessaoLeilao.DoesNotExist:
                    return None

        info = await database_sync_to_async(_run)()
        if info:
            await self.send(text_data=json.dumps({"type": "estado_atual", **info}))

    async def _atualizar_telao(self, data, user):
        if not user.is_admin:
            return
        await self.channel_layer.group_send(
            f"telao_{self.evento_id}",
            {"type": "broadcast", "payload": {**data, "type": "atualizar_telao"}},
        )

    async def _enviar_mensagem_telao(self, data, user):
        if not user.is_admin:
            return
        await self.channel_layer.group_send(
            f"telao_{self.evento_id}",
            {"type": "broadcast", "payload": {"type": "mensagem_telao", "mensagem": data.get("mensagem", "")}},
        )

    # ------------------------------------------------------------------
    # Broadcast handler
    # ------------------------------------------------------------------
    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event["payload"]))


class TelaoConsumer(AsyncWebsocketConsumer):
    """
    Canal público do telão TV — somente leitura, sem autenticação.
    Recebe atualizações do LeilaoConsumer via channel layer.
    """

    async def connect(self):
        self.evento_id = self.scope["url_route"]["kwargs"]["evento_id"]
        self.group = f"telao_{self.evento_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data):
        # Telão é somente leitura — ignora mensagens recebidas
        pass

    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
