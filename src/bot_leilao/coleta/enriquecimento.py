"""Enriquecimento dos lotes novos pelo detalhe do leiloeiro (feature 002; roadmap D-48, D-49).

Roda depois da filtragem e antes do digest, só para os lotes que vão ser avisados. Um leiloeiro
participa quando o adaptador tem `requisicao_detalhe(lote)` e o parser tem `aplicar_detalhe(lote,
conteudo)`; os demais (Vip) passam sem nenhuma requisição.

Feature 005: a requisição do detalhe sai pelo nível do leiloeiro (D-87), e o lote é conferido de novo contra o alvo
depois do detalhe (D-98): o Milan só traz o lance atual na página do lote.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace

from bot_leilao.coleta.http import ClienteHTTP
from bot_leilao.filtro.motor import Candidato, casa

log = logging.getLogger(__name__)


@dataclass
class ResultadoEnriquecimento:
    novos: list[Candidato] = field(default_factory=list)   # os que seguem para o aviso
    detalhados: int = 0
    retirados: int = 0
    sucatas: int = 0
    falhas: int = 0
    acima_do_teto: int = 0   # feature 005: deixou de casar com o alvo depois do detalhe (D-98)


def enriquecer(candidatos: Sequence[Candidato], cliente: ClienteHTTP, adaptadores: Mapping[str, object],
               parsers: Mapping[str, object], niveis: Mapping[str, str] | None = None) -> ResultadoEnriquecimento:
    """`niveis`: leiloeiro → `nivel_coleta`; ausente = `script`."""
    niveis = niveis or {}
    resultado = ResultadoEnriquecimento()
    for candidato in candidatos:
        lote = candidato.lote
        montar = getattr(adaptadores.get(lote.leiloeiro_id), "requisicao_detalhe", None)
        aplicar = getattr(parsers.get(lote.leiloeiro_id), "aplicar_detalhe", None)
        requisicao = montar(lote) if montar and aplicar else None
        if requisicao is None:
            resultado.novos.append(candidato)
            continue
        requisicao = replace(requisicao, nivel=niveis.get(lote.leiloeiro_id, "script"))
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
        if lote.situacao == "sucata":  # documento baixado (D-43): fora de "só conservado"
            resultado.sucatas += 1
            log.info("enriq   | %s | sucata segundo o detalhe; não será avisado", lote.id_canonico)
            continue
        if not casa(lote, candidato.alvo):  # D-98: ex.: o lance do detalhe passou do teto
            resultado.acima_do_teto += 1
            log.info("enriq   | %s | deixou de casar com o alvo %s depois do detalhe (preço %s, teto %s); "
                     "não será avisado", lote.id_canonico, candidato.alvo.id, candidato.preco, candidato.alvo.preco_maximo)
            continue
        resultado.novos.append(candidato)
    return resultado
