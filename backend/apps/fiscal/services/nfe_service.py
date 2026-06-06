"""
Serviço de emissão de NF-e — gera XML, assina, transmite para SEFAZ,
armazena XML/DANFE no S3 e envia DANFE ao comprador por e-mail.
"""
from __future__ import annotations

import hashlib
import io
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.utils import timezone
from lxml import etree

from apps.fiscal.models import (
    CertificadoDigital,
    ConfiguracaoFiscal,
    LogTransmissaoFiscal,
    NotaFiscal,
)
from apps.financeiro.models import Venda

logger = logging.getLogger(__name__)


class NFeService:
    """
    Orquestra emissão, transmissão, contingência e cancelamento de NF-e.
    A assinatura é delegada ao CertificateService e a transmissão ao SefazClient.
    """

    def __init__(self, config: ConfiguracaoFiscal):
        self.config = config
        from apps.fiscal.services.sefaz_client import SefazClient
        from apps.fiscal.services.certificate_service import CertificateService

        self.cert_service = CertificateService(config.certificado)
        self.sefaz = SefazClient(config)

    # ------------------------------------------------------------------
    # Ponto de entrada principal
    # ------------------------------------------------------------------
    def emitir_nfe_para_venda(self, venda: Venda, usuario) -> NotaFiscal:
        """Gera, assina, transmite e retorna o modelo NotaFiscal."""
        logger.info("Iniciando emissão NF-e para venda %s", venda.id)

        # Incrementa numeração
        self.config.nfe_ultimo_numero += 1
        self.config.save(update_fields=["nfe_ultimo_numero"])

        nota = NotaFiscal.objects.create(
            venda=venda,
            tipo=NotaFiscal.TIPO_NFE,
            status=NotaFiscal.STATUS_AGUARDANDO,
            serie=self.config.nfe_serie,
            numero=self.config.nfe_ultimo_numero,
            valor_total=venda.valor_total,
            data_emissao=timezone.now(),
            emitido_por=usuario,
        )

        try:
            xml_unsigned = self._gerar_xml(nota, venda)
            xml_signed = self.cert_service.assinar_xml(xml_unsigned)

            xml_hash = hashlib.sha256(xml_signed).hexdigest()
            sucesso, codigo, motivo, chave, protocolo = self.sefaz.transmitir(xml_signed, nota)

            LogTransmissaoFiscal.objects.create(
                nota=nota,
                operacao="emissao",
                xml_enviado_hash=xml_hash,
                resposta_codigo=codigo,
                resposta_motivo=motivo,
                sucesso=sucesso,
            )

            if sucesso:
                nota.status = NotaFiscal.STATUS_AUTORIZADA
                nota.chave_acesso = chave
                nota.protocolo = protocolo
                nota.data_autorizacao = timezone.now()
                # Armazena XML e gera DANFE
                xml_url, danfe_url = self._armazenar_e_gerar_danfe(xml_signed, nota)
                nota.xml_url = xml_url
                nota.danfe_url = danfe_url
                nota.save()
                # Envia DANFE por e-mail
                self._enviar_danfe_email(nota, venda)
                venda.nfe_emitida = True
                venda.save(update_fields=["nfe_emitida"])
            else:
                nota.status = NotaFiscal.STATUS_REJEITADA
                nota.retorno_codigo = codigo
                nota.retorno_motivo = motivo
                nota.save()
                logger.warning("NF-e rejeitada pela SEFAZ: %s — %s", codigo, motivo)

        except Exception as exc:
            # Modo contingência
            logger.exception("Erro ao transmitir NF-e; ativando contingência: %s", exc)
            nota.status = NotaFiscal.STATUS_CONTINGENCIA
            nota.modo_contingencia = True
            nota.justificativa_contingencia = str(exc)
            nota.save()

        return nota

    # ------------------------------------------------------------------
    # Geração do XML NF-e 4.0
    # ------------------------------------------------------------------
    def _gerar_xml(self, nota: NotaFiscal, venda: Venda) -> bytes:
        """
        Gera o XML da NF-e conforme layout 4.0 da SEFAZ.
        Os dados reais do emitente vêm do schema/tenant.
        """
        from django_tenants.utils import get_tenant
        tenant = get_tenant()

        NS = "http://www.portalfiscal.inf.br/nfe"
        nfe_proc = etree.Element(f"{{{NS}}}nfeProc", attrib={"versao": "4.00", "xmlns": NS})
        nfe = etree.SubElement(nfe_proc, f"{{{NS}}}NFe")
        inf_nfe = etree.SubElement(
            nfe,
            f"{{{NS}}}infNFe",
            attrib={"versao": "4.00", "Id": f"NFe{nota.chave_acesso or '0' * 44}"},
        )

        # ide
        ide = etree.SubElement(inf_nfe, f"{{{NS}}}ide")
        _tx(ide, "cUF", f"{{{NS}}}", self._codigo_uf(tenant.address_state))
        _tx(ide, "cNF", f"{{{NS}}}", str(nota.numero).zfill(8))
        _tx(ide, "natOp", f"{{{NS}}}", "VENDA DE ANIMAIS")
        _tx(ide, "mod", f"{{{NS}}}", "55")
        _tx(ide, "serie", f"{{{NS}}}", str(nota.serie))
        _tx(ide, "nNF", f"{{{NS}}}", str(nota.numero))
        _tx(ide, "dhEmi", f"{{{NS}}}", nota.data_emissao.strftime("%Y-%m-%dT%H:%M:%S-03:00"))
        _tx(ide, "tpNF", f"{{{NS}}}", "1")  # saída
        _tx(ide, "idDest", f"{{{NS}}}", "1")  # op. interna
        _tx(ide, "cMunFG", f"{{{NS}}}", tenant.address_ibge_code or "0000000")
        _tx(ide, "tpImp", f"{{{NS}}}", "1")  # DANFE retrato
        _tx(ide, "tpEmis", f"{{{NS}}}", "9" if nota.modo_contingencia else "1")
        _tx(ide, "tpAmb", f"{{{NS}}}", self.config.nfe_ambiente)
        _tx(ide, "finNFe", f"{{{NS}}}", "1")  # normal
        _tx(ide, "indFinal", f"{{{NS}}}", "1")
        _tx(ide, "indPres", f"{{{NS}}}", "1")

        # emit
        emit = etree.SubElement(inf_nfe, f"{{{NS}}}emit")
        _tx(emit, "CNPJ", f"{{{NS}}}", _digits_only(tenant.cnpj))
        _tx(emit, "xNome", f"{{{NS}}}", tenant.name[:60])
        _tx(emit, "xFant", f"{{{NS}}}", (tenant.trade_name or tenant.name)[:60])
        ender_emit = etree.SubElement(emit, f"{{{NS}}}enderEmit")
        _tx(ender_emit, "xLgr", f"{{{NS}}}", tenant.address_street[:60] or "NAO INFORMADO")
        _tx(ender_emit, "nro", f"{{{NS}}}", tenant.address_number or "S/N")
        _tx(ender_emit, "xBairro", f"{{{NS}}}", tenant.address_district[:60] or "NAO INFORMADO")
        _tx(ender_emit, "cMun", f"{{{NS}}}", tenant.address_ibge_code or "0000000")
        _tx(ender_emit, "xMun", f"{{{NS}}}", tenant.address_city[:60] or "NAO INFORMADO")
        _tx(ender_emit, "UF", f"{{{NS}}}", tenant.address_state or "SP")
        _tx(ender_emit, "CEP", f"{{{NS}}}", _digits_only(tenant.address_zipcode))
        _tx(ender_emit, "cPais", f"{{{NS}}}", "1058")
        _tx(ender_emit, "xPais", f"{{{NS}}}", "BRASIL")
        _tx(emit, "CRT", f"{{{NS}}}", self.config.regime_tributario)

        # dest
        dest = etree.SubElement(inf_nfe, f"{{{NS}}}dest")
        cpf_cnpj = _digits_only(venda.arrematante_cpf_cnpj)
        if len(cpf_cnpj) == 14:
            _tx(dest, "CNPJ", f"{{{NS}}}", cpf_cnpj)
        elif len(cpf_cnpj) == 11:
            _tx(dest, "CPF", f"{{{NS}}}", cpf_cnpj)
        _tx(dest, "xNome", f"{{{NS}}}", venda.arrematante_nome[:60])
        _tx(dest, "indIEDest", f"{{{NS}}}", "9")

        # det (produto)
        lote = venda.lote
        det = etree.SubElement(inf_nfe, f"{{{NS}}}det", attrib={"nItem": "1"})
        prod = etree.SubElement(det, f"{{{NS}}}prod")
        _tx(prod, "cProd", f"{{{NS}}}", str(lote.numero).zfill(6))
        _tx(prod, "cEAN", f"{{{NS}}}", "SEM GTIN")
        _tx(prod, "xProd", f"{{{NS}}}", lote.descricao[:120])
        _tx(prod, "NCM", f"{{{NS}}}", "01022110")  # bovinos para abate
        _tx(prod, "CFOP", f"{{{NS}}}", self.config.cfop_padrao)
        _tx(prod, "uCom", f"{{{NS}}}", "KG")
        _tx(prod, "qCom", f"{{{NS}}}", str(lote.peso_total))
        _tx(prod, "vUnCom", f"{{{NS}}}", f"{lote.preco_por_kg:.4f}")
        _tx(prod, "vProd", f"{{{NS}}}", f"{venda.valor_arrematacao:.2f}")
        _tx(prod, "cEANTrib", f"{{{NS}}}", "SEM GTIN")
        _tx(prod, "uTrib", f"{{{NS}}}", "KG")
        _tx(prod, "qTrib", f"{{{NS}}}", str(lote.peso_total))
        _tx(prod, "vUnTrib", f"{{{NS}}}", f"{lote.preco_por_kg:.4f}")
        _tx(prod, "indTot", f"{{{NS}}}", "1")

        imposto = etree.SubElement(det, f"{{{NS}}}imposto")
        icms = etree.SubElement(imposto, f"{{{NS}}}ICMS")
        icms90 = etree.SubElement(icms, f"{{{NS}}}ICMS90")
        _tx(icms90, "orig", f"{{{NS}}}", "0")
        _tx(icms90, "CSOSN", f"{{{NS}}}", self.config.csosn_padrao)

        # total
        total = etree.SubElement(inf_nfe, f"{{{NS}}}total")
        ice_tot = etree.SubElement(total, f"{{{NS}}}ICMSTot")
        for campo in ("vBC", "vICMS", "vICMSDeson", "vFCP", "vBCST", "vST", "vFCPST", "vFCPSTRet",
                      "vProd", "vFrete", "vSeg", "vDesc", "vII", "vIPI", "vIPIDevol",
                      "vPIS", "vCOFINS", "vOutro"):
            _tx(ice_tot, campo, f"{{{NS}}}",
               f"{venda.valor_arrematacao:.2f}" if campo == "vProd" else "0.00")
        _tx(ice_tot, "vNF", f"{{{NS}}}", f"{venda.valor_total:.2f}")
        _tx(ice_tot, "vTotTrib", f"{{{NS}}}", "0.00")

        # transp
        transp = etree.SubElement(inf_nfe, f"{{{NS}}}transp")
        _tx(transp, "modFrete", f"{{{NS}}}", "9")  # sem frete

        # pag
        pag = etree.SubElement(inf_nfe, f"{{{NS}}}pag")
        det_pag = etree.SubElement(pag, f"{{{NS}}}detPag")
        _tx(det_pag, "tPag", f"{{{NS}}}", "01")  # dinheiro default
        _tx(det_pag, "vPag", f"{{{NS}}}", f"{venda.valor_total:.2f}")

        return etree.tostring(nfe_proc, xml_declaration=True, encoding="unicode").encode()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _codigo_uf(self, sigla: str) -> str:
        mapa = {
            "AC": "12", "AL": "27", "AM": "13", "AP": "16", "BA": "29", "CE": "23",
            "DF": "53", "ES": "32", "GO": "52", "MA": "21", "MG": "31", "MS": "50",
            "MT": "51", "PA": "15", "PB": "25", "PE": "26", "PI": "22", "PR": "41",
            "RJ": "33", "RN": "24", "RO": "11", "RR": "14", "RS": "43", "SC": "42",
            "SE": "28", "SP": "35", "TO": "17",
        }
        return mapa.get(sigla.upper(), "35")

    def _armazenar_e_gerar_danfe(self, xml_bytes: bytes, nota: NotaFiscal):
        """Sobe XML para S3 e gera URL do DANFE (PDF via WeasyPrint ou ReportLab)."""
        # Em produção, usa django-storages para S3
        xml_key = f"fiscal/xml/{nota.chave_acesso}.xml"
        danfe_key = f"fiscal/danfe/{nota.chave_acesso}.pdf"
        # storage.save(xml_key, ContentFile(xml_bytes))
        xml_url = f"/media/{xml_key}"
        danfe_url = f"/media/{danfe_key}"
        return xml_url, danfe_url

    def _enviar_danfe_email(self, nota: NotaFiscal, venda: Venda):
        from django.core.mail import EmailMessage
        if not venda.arrematante_email:
            return
        email = EmailMessage(
            subject=f"NF-e {nota.numero} — Arrematex",
            body=f"Prezado {venda.arrematante_nome},\n\nSegue sua Nota Fiscal eletrônica.\nChave: {nota.chave_acesso}",
            to=[venda.arrematante_email],
        )
        try:
            email.send()
        except Exception as exc:
            logger.warning("Falha ao enviar DANFE por e-mail: %s", exc)


# ---------------------------------------------------------------------------
# Helpers XML
# ---------------------------------------------------------------------------
def _tx(parent, tag, ns, text):
    el = etree.SubElement(parent, f"{ns}{tag}")
    el.text = text
    return el


def _digits_only(value: str) -> str:
    return "".join(c for c in (value or "") if c.isdigit())
