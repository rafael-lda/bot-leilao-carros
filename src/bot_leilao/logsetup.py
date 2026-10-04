"""Logs no console e em arquivo, com mascaramento de segredos (RN-08, roadmap D-26)."""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterable
from logging.handlers import RotatingFileHandler
from pathlib import Path

MASCARA = "***"
TAMANHO_MINIMO_SEGREDO = 4
FORMATO = "%(asctime)s %(levelname)-7s %(message)s"


def mascarar(texto: str, segredos: Iterable[str]) -> str:
    """Troca cada segredo (com pelo menos 4 caracteres) por `***`."""
    for segredo in sorted({s for s in segredos if s and len(s) >= TAMANHO_MINIMO_SEGREDO}, key=len, reverse=True):
        texto = texto.replace(segredo, MASCARA)
    return texto


class FiltroSegredos(logging.Filter):
    """Mascara segredos na mensagem formatada e no rastreamento de exceção.

    Fica nos handlers, e não nos loggers, para valer também para registros
    propagados de bibliotecas de terceiros.
    """

    def __init__(self, segredos: Iterable[str] = ()) -> None:
        super().__init__()
        self._segredos: set[str] = set()
        self.adicionar(segredos)

    def adicionar(self, valores: Iterable[str]) -> None:
        self._segredos.update(v for v in valores if v)

    def filter(self, record: logging.LogRecord) -> bool:
        if not self._segredos:
            return True
        record.msg = mascarar(record.getMessage(), self._segredos)
        record.args = None
        if record.exc_info:
            texto = logging.Formatter().formatException(record.exc_info)
            record.exc_text = mascarar(texto, self._segredos)
            record.exc_info = None
        elif record.exc_text:
            record.exc_text = mascarar(record.exc_text, self._segredos)
        if record.stack_info:
            record.stack_info = mascarar(record.stack_info, self._segredos)
        return True


def configurar_logs(pasta_logs: Path | None, segredos: Iterable[str] = (), nivel: int = logging.INFO) -> FiltroSegredos:
    """Configura o logger `bot_leilao` e devolve o filtro, para acrescentar segredos depois."""
    filtro = FiltroSegredos(segredos)
    formatador = logging.Formatter(FORMATO, datefmt="%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger("bot_leilao")
    for antigo in list(logger.handlers):
        antigo.close()
        logger.removeHandler(antigo)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if pasta_logs is not None:
        pasta_logs.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(pasta_logs / "bot-leilao.log", maxBytes=1_000_000, backupCount=5,
                                            encoding="utf-8"))
    for handler in handlers:
        handler.setFormatter(formatador)
        handler.addFilter(filtro)
        logger.addHandler(handler)
    logger.setLevel(nivel)
    logger.propagate = False
    return filtro
