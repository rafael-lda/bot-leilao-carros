"""Leilões vistos pela primeira vez (feature 005; data-delta.md §2.1; roadmap D-102).

Guarda quando cada leilão (evento) apareceu pela primeira vez para medir com quantos dias de antecedência o
leiloeiro anuncia. Os leilões da primeira leitura de um leiloeiro (semeadura) ficam marcados e não contam.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from bot_leilao.db.conexao import de_iso, para_iso


@dataclass(frozen=True)
class EventoVisto:
    leiloeiro_id: str
    evento_id: str
    rotulo: str | None
    pregao_em: datetime | None
    visto_primeiro_em: datetime
    na_semeadura: bool

    @property
    def antecedencia_dias(self) -> int | None:
        """Dias inteiros entre a primeira vez que o leilão foi visto e o pregão; None sem pregão ou na semeadura."""
        if self.pregao_em is None or self.na_semeadura:
            return None
        return (self.pregao_em - self.visto_primeiro_em).days

    @property
    def antecedencia_horas(self) -> float | None:
        if self.pregao_em is None or self.na_semeadura:
            return None
        return (self.pregao_em - self.visto_primeiro_em).total_seconds() / 3600


class RepositorioEventos:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def registrar(self, leiloeiro_id: str, evento_id: str, rotulo: str | None, pregao_em: datetime | None,
                  visto_em: datetime, na_semeadura: bool = False) -> bool:
        """Grava a primeira vez; as seguintes são ignoradas. Devolve True se o leilão é novo."""
        with self.con:
            cursor = self.con.execute(
                "INSERT OR IGNORE INTO evento_visto (leiloeiro_id, evento_id, rotulo, pregao_em, visto_primeiro_em,"
                " na_semeadura) VALUES (?, ?, ?, ?, ?, ?)",
                (leiloeiro_id, evento_id, rotulo, pregao_em.isoformat() if pregao_em else None, para_iso(visto_em),
                 int(na_semeadura)))
        return cursor.rowcount == 1

    def obter(self, leiloeiro_id: str, evento_id: str) -> EventoVisto | None:
        linha = self.con.execute("SELECT * FROM evento_visto WHERE leiloeiro_id = ? AND evento_id = ?",
                                 (leiloeiro_id, evento_id)).fetchone()
        if linha is None:
            return None
        return EventoVisto(leiloeiro_id=linha["leiloeiro_id"], evento_id=linha["evento_id"], rotulo=linha["rotulo"],
                           pregao_em=datetime.fromisoformat(linha["pregao_em"]) if linha["pregao_em"] else None,
                           visto_primeiro_em=de_iso(linha["visto_primeiro_em"]),
                           na_semeadura=bool(linha["na_semeadura"]))
