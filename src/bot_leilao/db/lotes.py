"""Lotes conhecidos e buscas semeadas (motor-filtros; data-delta.md §2.1 e §2.2)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from bot_leilao.db.conexao import para_iso

_LOTE_CONSULTA = 500  # abaixo do limite de parâmetros do SQLite


@dataclass
class RegistroLote:
    id_canonico: str
    leiloeiro_id: str
    busca_id: str
    alvo_id: str
    origem: str  # 'notificacao' | 'semeadura'
    preco_na_notificacao: Decimal | None
    lance_inicial: Decimal | None
    link: str
    registrado_em: datetime


def _numero(valor: Decimal | None) -> str | None:
    return None if valor is None else str(valor)


class RepositorioLotes:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def conhecidos(self, ids: Iterable[str]) -> set[str]:
        lista = list(dict.fromkeys(ids))
        achados: set[str] = set()
        for inicio in range(0, len(lista), _LOTE_CONSULTA):
            fatia = lista[inicio:inicio + _LOTE_CONSULTA]
            marcadores = ",".join("?" * len(fatia))
            achados.update(r[0] for r in self.con.execute(
                f"SELECT id_canonico FROM lote_conhecido WHERE id_canonico IN ({marcadores})", fatia))
        return achados

    def registrar(self, registros: Iterable[RegistroLote]) -> int:
        """Grava numa transação única; id já existente é ignorado (motor EC-09). Devolve quantos entraram.

        `ON CONFLICT DO NOTHING`, e não `INSERT OR IGNORE`: este também engoliria violações de CHECK.
        """
        linhas = [(r.id_canonico, r.leiloeiro_id, r.busca_id, r.alvo_id, r.origem, _numero(r.preco_na_notificacao),
                   _numero(r.lance_inicial), r.link, para_iso(r.registrado_em)) for r in registros]
        antes = self.con.total_changes
        with self.con:
            self.con.executemany(
                "INSERT INTO lote_conhecido (id_canonico, leiloeiro_id, busca_id, alvo_id, origem,"
                " preco_na_notificacao, lance_inicial, link, registrado_em) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT (id_canonico) DO NOTHING",
                linhas)
        return self.con.total_changes - antes

    def busca_semeada(self, busca_id: str) -> bool:
        return self.con.execute("SELECT 1 FROM busca_semeada WHERE busca_id = ?", (busca_id,)).fetchone() is not None

    def marcar_semeada(self, busca_id: str, execucao_id: str, quando: datetime) -> None:
        with self.con:
            self.con.execute("INSERT INTO busca_semeada (busca_id, semeada_em, execucao_id) VALUES (?, ?, ?)"
                             " ON CONFLICT (busca_id) DO NOTHING",
                             (busca_id, para_iso(quando), execucao_id))

    def total(self) -> int:
        return self.con.execute("SELECT COUNT(*) FROM lote_conhecido").fetchone()[0]
