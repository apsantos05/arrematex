"""
Cliente SEFAZ — transmissão de NF-e via WebService por UF.
Suporta produção e homologação; trata contingência SVC-AN/SVC-RS.
"""
from __future__ import annotations

import logging
import ssl
from typing import Tuple

import requests
from django.conf import settings
from lxml import etree

from apps.fiscal.models import ConfiguracaoFiscal, NotaFiscal

logger = logging.getLogger(__name__)

# URLs de autorização por UF e ambiente
# Fonte: https://www.nfe.fazenda.gov.br/portal/webService.aspx
SEFAZ_URLS: dict[str, dict] = {
    # UF: {ambiente_1: url_producao, ambiente_2: url_homologacao}
    "SP": {
        "1": "https://nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx",
        "2": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx",
    },
    "MG": {
        "1": "https://nfe.fazenda.mg.gov.br/nfe2/services/NFeAutorizacao4",
        "2": "https://hnfe.fazenda.mg.gov.br/nfe2/services/NFeAutorizacao4",
    },
    "MT": {
        "1": "https://nfe.sefaz.mt.gov.br/nfews/v2/services/NfeAutorizacao4",
        "2": "https://homologacao.sefaz.mt.gov.br/nfews/v2/services/NfeAutorizacao4",
    },
    "MS": {
        "1": "https://nfe.fazenda.ms.gov.br/ws/NFeAutorizacao4",
        "2": "https://homologacao.nfe.fazenda.ms.gov.br/ws/NFeAutorizacao4",
    },
    "GO": {
        "1": "https://nfe.sefaz.go.gov.br/nfe/services/NFeAutorizacao4",
        "2": "https://homologacao.nfe.sefaz.go.gov.br/nfe/services/NFeAutorizacao4",
    },
    # SVCAN — contingência nacional (atende demais UF)
    "SVCAN": {
        "1": "https://nfe.svrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx",
        "2": "https://hom.nfe.svrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx",
    },
}


class SefazClient:
    """Envia NF-e para a SEFAZ da UF configurada."""

    NS = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"

    def __init__(self, config: ConfiguracaoFiscal):
        self.config = config
        from django_tenants.utils import get_tenant
        self.tenant = get_tenant()
        self.ambiente = config.nfe_ambiente
        self.uf = self.tenant.address_state or settings.SEFAZ_UF_PADRAO

    def transmitir(
        self, xml_signed: bytes, nota: NotaFiscal
    ) -> Tuple[bool, str, str, str, str]:
        """
        Transmite XML assinado para SEFAZ.
        Returns: (sucesso, codigo, motivo, chave_acesso, protocolo)
        """
        url = self._get_url()
        soap_body = self._montar_envelope(xml_signed)

        try:
            response = requests.post(
                url,
                data=soap_body,
                headers={"Content-Type": "application/soap+xml; charset=utf-8"},
                timeout=30,
                verify=True,
            )
            response.raise_for_status()
            return self._parsear_resposta(response.content)
        except requests.exceptions.RequestException as exc:
            logger.error("Erro de conexão com SEFAZ: %s", exc)
            # Sinaliza contingência
            raise ConnectionError(f"SEFAZ indisponível: {exc}") from exc

    # ------------------------------------------------------------------
    def _get_url(self, contingencia: bool = False) -> str:
        uf = "SVCAN" if contingencia else self.uf
        uf_urls = SEFAZ_URLS.get(uf, SEFAZ_URLS["SVCAN"])
        return uf_urls.get(self.ambiente, uf_urls["2"])

    def _montar_envelope(self, xml_nfe: bytes) -> bytes:
        envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <nfeAutorizacaoLote xmlns="{self.NS}">
      <nfeDadosMsg>
        <enviNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
          <idLote>1</idLote>
          <indSinc>1</indSinc>
          {xml_nfe.decode()}
        </enviNFe>
      </nfeDadosMsg>
    </nfeAutorizacaoLote>
  </soap12:Body>
</soap12:Envelope>"""
        return envelope.encode()

    def _parsear_resposta(self, content: bytes) -> Tuple[bool, str, str, str, str]:
        try:
            root = etree.fromstring(content)
            ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
            cstat = root.findtext(".//nfe:cStat", namespaces=ns, default="")
            xmotivo = root.findtext(".//nfe:xMotivo", namespaces=ns, default="")
            chave = root.findtext(".//nfe:chNFe", namespaces=ns, default="")
            protocolo = root.findtext(".//nfe:nProt", namespaces=ns, default="")
            # códigos 100 = autorizado, 150 = autorizado fora do prazo
            sucesso = cstat in ("100", "150")
            return sucesso, cstat, xmotivo, chave, protocolo
        except Exception as exc:
            logger.exception("Falha ao parsear resposta SEFAZ: %s", exc)
            return False, "999", str(exc), "", ""
