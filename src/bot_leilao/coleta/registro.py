"""Registro de adaptadores de coleta por leiloeiro (coletor-lotes RF-12)."""

from __future__ import annotations

from bot_leilao.coleta.modelos import Adaptador

_ADAPTADORES: dict[str, Adaptador] = {}


def registrar_adaptador(adaptador: Adaptador) -> None:
    _ADAPTADORES[adaptador.leiloeiro_id] = adaptador


def obter_adaptador(leiloeiro_id: str) -> Adaptador:
    return _ADAPTADORES[leiloeiro_id]


def adaptadores() -> dict[str, Adaptador]:
    return dict(_ADAPTADORES)


def nomes_adaptadores() -> list[str]:
    return sorted(_ADAPTADORES)
