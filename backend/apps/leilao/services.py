"""Serviços de domínio do leilão — lógica de lances, abertura e fechamento."""
import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.leilao.models import Lance, SessaoLeilao
from apps.lotes.models import Lote

logger = logging.getLogger(__name__)


@transaction.atomic
def abrir_lote(lote_id: str, leiloeiro) -> SessaoLeilao:
    lote = Lote.objects.select_for_update().get(id=lote_id)

    if lote.status not in (Lote.STATUS_AGUARDANDO,):
        raise ValueError(f"Lote {lote.numero} não pode ser aberto (status: {lote.status})")

    # Fecha sessão anterior se existir
    SessaoLeilao.objects.filter(
        lote__evento=lote.evento,
        status=SessaoLeilao.STATUS_ATIVA,
    ).exclude(lote=lote).update(status=SessaoLeilao.STATUS_PAUSADA)

    sessao, _ = SessaoLeilao.objects.get_or_create(
        lote=lote,
        defaults={"leiloeiro": leiloeiro},
    )
    sessao.status = SessaoLeilao.STATUS_ATIVA
    sessao.leiloeiro = leiloeiro
    sessao.lance_corrente = lote.lance_inicial
    sessao.aberto_em = timezone.now()
    sessao.save()

    lote.status = Lote.STATUS_EM_LEILAO
    lote.lance_atual = lote.lance_inicial
    lote.save(update_fields=["status", "lance_atual"])

    logger.info("Lote %s aberto por %s", lote.numero, leiloeiro.email)
    return sessao


@transaction.atomic
def processar_lance(sessao_id: str, valor, arrematante_nome: str, registrado_por) -> dict:
    sessao = SessaoLeilao.objects.select_for_update().get(id=sessao_id, status=SessaoLeilao.STATUS_ATIVA)
    valor = Decimal(str(valor))

    if valor <= sessao.lance_corrente:
        raise ValueError(f"Valor {valor} deve ser maior que o lance atual {sessao.lance_corrente}")

    lance = Lance.objects.create(
        sessao=sessao,
        valor=valor,
        arrematante_nome_livre=arrematante_nome,
        registrado_por=registrado_por,
    )

    sessao.lance_corrente = valor
    sessao.arrematante_nome_livre = arrematante_nome
    sessao.save(update_fields=["lance_corrente", "arrematante_nome_livre"])

    sessao.lote.lance_atual = valor
    sessao.lote.save(update_fields=["lance_atual"])

    preco_kg = 0
    if sessao.lote.peso_total:
        preco_kg = round(float(valor) / float(sessao.lote.peso_total), 2)

    return {
        "sessao_id": sessao.id,
        "lance_id": lance.id,
        "valor": valor,
        "arrematante": arrematante_nome,
        "preco_kg": preco_kg,
    }


@transaction.atomic
def fechar_lote(sessao_id: str, encerrado_por) -> dict:
    sessao = SessaoLeilao.objects.select_for_update().get(id=sessao_id)

    tem_lance = sessao.lances.filter(cancelado=False).exists()

    if tem_lance:
        ultimo_lance = sessao.lances.filter(cancelado=False).order_by("-created_at").first()
        sessao.lote.status = Lote.STATUS_VENDIDO
        sessao.lote.save(update_fields=["status"])

        # Cria Venda no financeiro automaticamente (idempotente)
        from apps.financeiro.models import Venda
        venda, criada = Venda.objects.get_or_create(
            lote=sessao.lote,
            defaults={
                "arrematante_nome": sessao.arrematante_nome_livre,
                "valor_arrematacao": ultimo_lance.valor,
                "fechado_por": encerrado_por,
            },
        )
        if criada:
            venda.calcular_totais()

        resultado = {
            "vendido": True,
            "valor_final": ultimo_lance.valor,
            "arrematante": sessao.arrematante_nome_livre,
        }
    else:
        sessao.lote.status = Lote.STATUS_RETIRADO
        sessao.lote.save(update_fields=["status"])
        resultado = {"vendido": False}

    sessao.status = SessaoLeilao.STATUS_ENCERRADA
    sessao.encerrado_em = timezone.now()
    sessao.save(update_fields=["status", "encerrado_em"])

    logger.info("Lote %s fechado por %s — vendido: %s", sessao.lote.numero, encerrado_por.email, resultado["vendido"])
    return resultado
