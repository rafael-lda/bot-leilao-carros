"""Trava de execução por arquivo exclusivo (RF-15; agendador-observabilidade RF-02, EC-01; roadmap D-07)."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bot_leilao.db.conexao import de_iso, para_iso

log = logging.getLogger(__name__)


class TravaOcupada(Exception):
    """Outra execução detém a trava."""


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Trava:
    def __init__(self, caminho: Path, orfa_apos: timedelta = timedelta(hours=2),
                 agora: Callable[[], datetime] = _agora_utc) -> None:
        self.caminho = caminho
        self.orfa_apos = orfa_apos
        self.agora = agora
        self.orfa_liberada = False
        self._minha = False

    def _criar(self) -> bool:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        try:
            descritor = os.open(self.caminho, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            json.dump({"pid": os.getpid(), "adquirida_em": para_iso(self.agora())}, arquivo)
        self._minha = True
        return True

    def _e_orfa(self) -> bool:
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            adquirida = de_iso(dados["adquirida_em"])
        except (OSError, ValueError, KeyError, TypeError):
            return True
        return self.agora() - adquirida > self.orfa_apos

    def adquirir(self) -> bool:
        if self._criar():
            return True
        if not self._e_orfa():
            return False
        log.warning("exec    | trava órfã encontrada em %s (mais de %s); liberando", self.caminho, self.orfa_apos)
        try:
            self.caminho.unlink()
        except FileNotFoundError:
            pass
        if self._criar():
            self.orfa_liberada = True
            return True
        return False

    def liberar(self) -> None:
        if self._minha:
            try:
                self.caminho.unlink()
            except FileNotFoundError:
                pass
            self._minha = False

    def __enter__(self) -> "Trava":
        if not self.adquirir():
            raise TravaOcupada(f"Outra varredura está em andamento ({self.caminho}).")
        return self

    def __exit__(self, *_exc) -> None:
        self.liberar()
