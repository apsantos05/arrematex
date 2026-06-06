"""
Adapter pattern para integração com balanças.
Cada ProviderBalanca tem um tipo (http_rest, serial, tcp) que
mapeia para uma subclasse concreta de BalancaAdapter.
"""
import json
import socket
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BalancaAdapter(ABC):
    """Interface comum para todos os adaptadores de balança."""

    @abstractmethod
    def ler_peso(self) -> Optional[float]:
        """Retorna o peso atual em kg, ou None se indisponível."""
        ...

    @abstractmethod
    def testar_conexao(self) -> bool:
        ...


class HttpRestAdapter(BalancaAdapter):
    """Balança que expõe REST API (ex: balanças com módulo Wi-Fi)."""

    def __init__(self, config: dict):
        self.url = config.get("url", "")
        self.campo_peso = config.get("campo_peso", "peso")
        self.timeout = int(config.get("timeout", 5))

    def ler_peso(self) -> Optional[float]:
        try:
            import httpx
            r = httpx.get(self.url, timeout=self.timeout)
            data = r.json()
            return float(data[self.campo_peso])
        except Exception as exc:
            logger.warning("HttpRestAdapter.ler_peso falhou: %s", exc)
            return None

    def testar_conexao(self) -> bool:
        return self.ler_peso() is not None


class TcpAdapter(BalancaAdapter):
    """Balança que envia peso via TCP raw (ex: Toledo, Filizola)."""

    def __init__(self, config: dict):
        self.host = config.get("host", "127.0.0.1")
        self.port = int(config.get("port", 8008))
        self.timeout = int(config.get("timeout", 3))
        self.comando = config.get("comando", "P\r\n").encode()

    def ler_peso(self) -> Optional[float]:
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as s:
                s.sendall(self.comando)
                data = s.recv(64).decode("ascii", errors="ignore").strip()
                # Extrai números com ponto/vírgula
                import re
                m = re.search(r"[\d]+[.,][\d]+|[\d]+", data)
                if m:
                    return float(m.group().replace(",", "."))
        except Exception as exc:
            logger.warning("TcpAdapter.ler_peso falhou: %s", exc)
        return None

    def testar_conexao(self) -> bool:
        try:
            socket.create_connection((self.host, self.port), timeout=2).close()
            return True
        except Exception:
            return False


class SerialAdapter(BalancaAdapter):
    """Balança conectada por porta serial/RS-232/USB."""

    def __init__(self, config: dict):
        self.porta = config.get("porta", "/dev/ttyUSB0")
        self.baud = int(config.get("baud", 9600))
        self.timeout = int(config.get("timeout", 2))

    def ler_peso(self) -> Optional[float]:
        try:
            import serial  # pyserial
            import re
            with serial.Serial(self.porta, self.baud, timeout=self.timeout) as s:
                raw = s.readline().decode("ascii", errors="ignore").strip()
                m = re.search(r"[\d]+[.,][\d]+|[\d]+", raw)
                if m:
                    return float(m.group().replace(",", "."))
        except Exception as exc:
            logger.warning("SerialAdapter.ler_peso falhou: %s", exc)
        return None

    def testar_conexao(self) -> bool:
        try:
            import serial
            serial.Serial(self.porta, self.baud, timeout=1).close()
            return True
        except Exception:
            return False


# ── Factory ───────────────────────────────────────────────────────────────────
def get_adapter(provider) -> BalancaAdapter:
    """Retorna o adaptador correto dado um ProviderBalanca."""
    config = provider.config or {}
    tipo = provider.tipo
    if tipo == "http_rest":
        return HttpRestAdapter(config)
    if tipo == "tcp":
        return TcpAdapter(config)
    if tipo == "serial":
        return SerialAdapter(config)
    raise ValueError(f"Tipo de balança desconhecido: {tipo}")
