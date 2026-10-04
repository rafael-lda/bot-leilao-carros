"""Conexão SQLite e conversão de instantes (data-delta.md §2)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class ErroBanco(Exception):
    """Banco inacessível, corrompido ou com esquema desconhecido: a execução aborta sem notificar."""


def conectar(caminho: Path) -> sqlite3.Connection:
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(caminho, timeout=10.0)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("PRAGMA busy_timeout = 10000")
        con.execute("SELECT 1").fetchone()
        return con
    except (sqlite3.Error, OSError) as erro:
        raise ErroBanco(f"Banco {caminho} inacessível: {erro}") from erro


def para_iso(instante: datetime) -> str:
    """UTC com sufixo Z e milissegundos; recusa datetime sem fuso (RNF-04 do agendador)."""
    if instante.tzinfo is None:
        raise ValueError("instante sem fuso horário; use datetime aware")
    return instante.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def de_iso(texto: str) -> datetime:
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))
