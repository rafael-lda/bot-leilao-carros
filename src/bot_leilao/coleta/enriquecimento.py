"""Enriquecimento dos lotes novos pelo detalhe do leiloeiro (feature 002; roadmap D-48, D-49).

Roda depois da filtragem e antes do digest, só para os lotes que vão ser avisados. Um leiloeiro
participa quando o adaptador tem `requisicao_detalhe(lote)` e o parser tem `aplicar_detalhe(lote,
conteudo)`; os demais (Vip) passam sem nenhuma requisição.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from bot_leilao.coleta.http import ClienteHTTP
from bot_leilao.filtro.motor import Candidato

log = logging.getLogger(__name__)


@dataclass
class ResultadoEnriquecimento:
    novos: list[Candidato] = field(default_factory=list)   # os que seguem para o aviso
    detalhados: int = 0
    retirados: int = 0
    falhas: int = 0


def enriquecer(candidatos: Sequence[Candidato], cliente: ClienteHTTP, adaptadores: Mapping[str, object],
               parsers: Mapping[str, object]) -> ResultadoEnriquecimento:
    resultado = ResultadoEnriquecimento()
    for candidato in candidatos:
        lote = candidato.lote
        montar = getattr(adaptadores.get(lote.leiloeiro_id), "requisicao_detalhe", None)
        aplicar = getattr(parsers.get(lote.leiloeiro_id), "aplicar_detalhe", None)
        requisicao = montar(lote) if montar and aplicar else None
        if requisicao is None:
            resultado.novos.append(candidato)
            continue
        try:
            resposta = cliente.requisitar(requisicao)
            if not resposta.ok:
                raise RuntimeError(f"{resposta.veredito.value}: {resposta.motivo}")
            aplicar(lote, resposta.conteudo or b"")
        except Exception as erro:  # noqa: BLE001 — D-49: avisar sem observações é melhor que perder o lote
            lote.detalhe_lido = False
            resultado.falhas += 1
            resultado.novos.append(candidato)
            log.warning("enriq   | %s | detalhe não lido, o lote segue sem observações: %s", lote.id_canonico, erro)
            continue
        resultado.detalhados += 1
        if lote.retirado:
            resultado.retirados += 1
            log.info("enriq   | %s | retirado segundo o detalhe; não será avisado", lote.id_canonico)
            continue
        resultado.novos.append(candidato)
    return resultado
