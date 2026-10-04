"""Fixtures compartilhadas. Nenhum teste toca a rede (roadmap D-27)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

PASTA_FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def raiz(tmp_path: Path) -> Path:
    """Raiz de execução temporária com config/ e dados/ vazias."""
    (tmp_path / "config").mkdir()
    (tmp_path / "dados").mkdir()
    return tmp_path


@pytest.fixture
def caminho_banco(tmp_path: Path) -> Path:
    return tmp_path / "dados" / "bot-leilao.sqlite3"


@pytest.fixture
def ler_fixture() -> Callable[[str], bytes]:
    """Lê uma fixture por caminho relativo, ex.: ler_fixture("vip/busca_um_resultado.html")."""

    def ler(nome: str) -> bytes:
        return (PASTA_FIXTURES / nome).read_bytes()

    return ler


class RelogioFalso:
    """Relógio monotônico e `sleep` falsos: dormir avança o tempo sem esperar de verdade."""

    def __init__(self) -> None:
        self.t = 1000.0
        self.dormidas: list[float] = []

    def agora(self) -> float:
        return self.t

    def dormir(self, segundos: float) -> None:
        self.dormidas.append(segundos)
        self.t += max(0.0, segundos)


@pytest.fixture
def relogio() -> RelogioFalso:
    return RelogioFalso()


class TransporteRoteirizado:
    """`httpx.MockTransport` que registra as requisições e responde por função ou por fila.

    `respostas` pode ser uma função `request -> httpx.Response` (ou levantar exceção httpx),
    ou uma lista consumida em ordem, cujos itens são `httpx.Response` ou exceções.
    """

    def __init__(self, respostas) -> None:
        self.chamadas: list[httpx.Request] = []
        self._respostas = respostas
        self.transporte = httpx.MockTransport(self._tratar)

    def _tratar(self, request: httpx.Request) -> httpx.Response:
        request.read()
        self.chamadas.append(request)
        if callable(self._respostas):
            return self._respostas(request)
        item = self._respostas.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture
def roteiro() -> Callable[..., TransporteRoteirizado]:
    return TransporteRoteirizado


class AgoraFalso:
    """Relógio de parede falso (datetime aware em UTC), avançável."""

    def __init__(self, inicio: datetime | None = None) -> None:
        self.instante = inicio or datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.instante

    def avancar(self, **delta) -> None:
        self.instante += timedelta(**delta)


@pytest.fixture
def agora() -> AgoraFalso:
    return AgoraFalso()



@pytest.fixture
def cenario(raiz, relogio, agora):
    from apoio import CenarioE2E

    return CenarioE2E(raiz, relogio, agora)


@pytest.fixture(autouse=True)
def _logger_limpo():
    """`configurar_logs` desliga a propagação e põe handlers; cada teste começa e termina com o logger neutro."""
    import logging

    def limpar():
        logger = logging.getLogger("bot_leilao")
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        logger.propagate = True
        logger.setLevel(logging.NOTSET)

    limpar()
    yield
    limpar()
