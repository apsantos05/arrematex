"""
Serviço de certificado digital A1 (.pfx) — criptografia em repouso e assinatura XML.
"""
from __future__ import annotations

import base64
import logging
from datetime import date

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
from lxml import etree
from signxml import XMLSigner, methods

from apps.fiscal.models import CertificadoDigital

logger = logging.getLogger(__name__)


class CertificateService:
    """Gerencia upload seguro, descriptografia e assinatura XML com certificado A1."""

    def __init__(self, cert: CertificadoDigital):
        self.cert = cert

    # ------------------------------------------------------------------
    # Assinatura
    # ------------------------------------------------------------------
    def assinar_xml(self, xml_bytes: bytes) -> bytes:
        """Assina o XML com a chave privada do certificado."""
        cert_pem, key_pem = self._extrair_pem()
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha1",
            digest_algorithm="sha1",
        )
        root = etree.fromstring(xml_bytes)
        signed_root = signer.sign(root, key=key_pem, cert=cert_pem)
        return etree.tostring(signed_root, xml_declaration=True, encoding="unicode").encode()

    # ------------------------------------------------------------------
    # Upload seguro
    # ------------------------------------------------------------------
    @classmethod
    def salvar_certificado(
        cls,
        pfx_bytes: bytes,
        senha: str,
        usuario,
        nome: str = "Certificado A1",
    ) -> CertificadoDigital:
        """
        Valida, extrai metadados e armazena o .pfx cifrado com AES-256-GCM.
        A senha nunca é armazenada em texto plano.
        """
        try:
            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                pfx_bytes, senha.encode()
            )
        except Exception as exc:
            raise ValueError(f"Certificado inválido ou senha incorreta: {exc}") from exc

        # Extrai metadados
        subject = certificate.subject
        cnpj = cls._extrair_cnpj_do_cert(certificate)
        razao_social = subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
        validade = certificate.not_valid_after_utc.date()
        serial = str(certificate.serial_number)
        issuer = certificate.issuer.rfc4514_string()

        # Cifra o arquivo em repouso com AES-256-GCM
        arquivo_cifrado = cls._cifrar(pfx_bytes)

        cert_obj = CertificadoDigital.objects.create(
            nome=nome,
            tipo=CertificadoDigital.TIPO_A1,
            arquivo_cifrado=arquivo_cifrado,
            cnpj=cnpj,
            razao_social=razao_social,
            validade=validade,
            serial=serial,
            issuer=issuer[:300],
            enviado_por=usuario,
        )
        logger.info("Certificado %s armazenado com sucesso (válido até %s)", cnpj, validade)
        return cert_obj

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _extrair_pem(self):
        """Descriptografa arquivo e retorna (cert_pem_bytes, key_pem_bytes)."""
        pfx_bytes = self._decifrar(bytes(self.cert.arquivo_cifrado))
        # A senha não é armazenada; em produção, vem de um vault (ex: HashiCorp Vault ou AWS Secrets)
        # Aqui lê de variável de ambiente por tenant — simplificação segura para esse contexto
        senha = settings.CERT_ENCRYPTION_KEY.encode()[:32]
        private_key, certificate, _ = pkcs12.load_key_and_certificates(pfx_bytes, senha)

        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
        key_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
        return cert_pem, key_pem

    @staticmethod
    def _cifrar(data: bytes) -> bytes:
        """AES-256-GCM — gera nonce aleatório e prepende no resultado."""
        key = settings.CERT_ENCRYPTION_KEY.encode().ljust(32, b"\0")[:32]
        aesgcm = AESGCM(key)
        import os
        nonce = os.urandom(12)
        return nonce + aesgcm.encrypt(nonce, data, None)

    @staticmethod
    def _decifrar(data: bytes) -> bytes:
        key = settings.CERT_ENCRYPTION_KEY.encode().ljust(32, b"\0")[:32]
        aesgcm = AESGCM(key)
        nonce, ciphertext = data[:12], data[12:]
        return aesgcm.decrypt(nonce, ciphertext, None)

    @staticmethod
    def _extrair_cnpj_do_cert(certificate) -> str:
        """Tenta extrair CNPJ do campo OID 2.16.76.1.3.3 ou do Common Name."""
        try:
            for attr in certificate.subject:
                if "2.16.76.1.3.3" in str(attr.oid.dotted_string):
                    return attr.value
        except Exception:
            pass
        # fallback: primeiros 14 dígitos do Common Name
        cn = certificate.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
        digits = "".join(c for c in cn if c.isdigit())
        return digits[:14] if digits else ""
