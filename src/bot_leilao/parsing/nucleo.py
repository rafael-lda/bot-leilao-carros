"""Núcleo do parsing (parser-lotes RF-01, RF-07 a RF-11, EC-02, EC-06, EC-10, EC-15; roadmap D-31)."""

from __future__ import annotations

import logging
from typing import Protocol

from bot_leilao.coleta.modelos import RespostaBruta, Veredito
from bot_leilao.parsing.modelos import ContextoParsing, ExtracaoPagina, Lote, ResultadoParsing

log = logging.getLogger(__name__)

CAMPOS_OBRIGATORIOS = ("marca", "modelo", "ano_modelo", "preco")
LIMITE_INCOMPLETOS = 0.30


class Parser(Protocol):
    def extrair(self, conteudo: bytes, contexto: ContextoParsing) -> ExtracaoPagina: ...


_PARSERS: dict[str, Parser] = {}


def registrar_parser(leiloeiro_id: str, parser: Parser) -> None:
    _PARSERS[leiloeiro_id] = parser


def obter_parser(leiloeiro_id: str) -> Parser:
    return _PARSERS[leiloeiro_id]


def parsers() -> dict[str, Parser]:
    return dict(_PARSERS)


def _incompleto(lote: Lote) -> bool:
    if lote.lance_corrente is None and lote.lance_inicial is None:
        return True
    return any(getattr(lote, campo) in (None, "") for campo in CAMPOS_OBRIGATORIOS if campo != "preco")


def processar(resposta: RespostaBruta, contexto: ContextoParsing, parser: Parser | None = None) -> ResultadoParsing:
    resultado = ResultadoParsing(busca_id=resposta.busca_id, leiloeiro_id=resposta.leiloeiro_id)
    if resposta.veredito is not Veredito.OK:
        return resultado

    resultado.tamanho_conteudo = sum(len(p.conteudo) for p in resposta.paginas)
    if resultado.tamanho_conteudo == 0:
        resultado.sem_conteudo = True
        log.warning("parser  | busca=%s | coletor entregou conteúdo vazio (não é quebra de parser)", resposta.busca_id)
        return resultado

    parser = parser or obter_parser(resposta.leiloeiro_id)
    extraidos: list[Lote] = []
    todas_vazias_declaradas = True
    try:
        for pagina in resposta.paginas:
            extracao = parser.extrair(pagina.conteudo, contexto)
            extraidos.extend(extracao.lotes)
            todas_vazias_declaradas = todas_vazias_declaradas and extracao.busca_vazia and not extracao.lotes
    except Exception as erro:  # noqa: BLE001 — RF-10: isola a busca
        log.exception("parser  | busca=%s | exceção no parser", resposta.busca_id)
        resultado.quebra_suspeita = True
        resultado.motivo_quebra = f"exceção no parser: {type(erro).__name__}: {erro}"
        return resultado

    vistos: set[str] = set()
    for lote in extraidos:
        if not lote.link or not lote.id_canonico:
            resultado.descartados += 1
            continue
        if lote.id_canonico in vistos:
            continue
        vistos.add(lote.id_canonico)
        resultado.lotes.append(lote)

    kb = max(1, round(resultado.tamanho_conteudo / 1024))
    if not extraidos:
        if todas_vazias_declaradas:
            log.info("parser  | busca=%s | nenhum resultado (busca vazia declarada pelo site)", resposta.busca_id)
        else:
            resultado.quebra_suspeita = True
            resultado.motivo_quebra = f"0 lotes extraídos de conteúdo com {kb} KB"
    elif resultado.lotes:
        incompletos = sum(_incompleto(l) for l in resultado.lotes)
        if incompletos / len(resultado.lotes) > LIMITE_INCOMPLETOS:
            resultado.quebra_suspeita = True
            resultado.motivo_quebra = (f"{incompletos} de {len(resultado.lotes)} lotes sem campo obrigatório "
                                       f"({', '.join(CAMPOS_OBRIGATORIOS)})")

    if resultado.quebra_suspeita:
        log.warning("parser  | busca=%s | QUEBRA SUSPEITA | %s", resposta.busca_id, resultado.motivo_quebra)
    else:
        log.info("parser  | busca=%s | %d lotes | %d descartados | ok", resposta.busca_id, len(resultado.lotes),
                 resultado.descartados)
    return resultado
