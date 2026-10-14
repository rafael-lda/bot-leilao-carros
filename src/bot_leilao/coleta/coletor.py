"""Coletor de lotes (coletor-lotes v1.1 RF-01, RF-05, RF-07, RF-10 a RF-15; RF-18 da feature)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import datetime, timezone

from bot_leilao.coleta.http import ClienteHTTP
from bot_leilao.coleta.modelos import Adaptador, Pagina, Requisicao, RespostaBruta, ResultadoHTTP, Veredito
from bot_leilao.config.leiloeiros import Busca, Leiloeiro

log = logging.getLogger(__name__)


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class _ClienteNoNivel:
    """Cliente entregue ao adaptador na preparação de sessão: carimba o nível do leiloeiro (feature 005, D-87)."""

    def __init__(self, cliente, nivel: str) -> None:
        self._cliente = cliente
        self._nivel = nivel

    def requisitar(self, requisicao: Requisicao) -> ResultadoHTTP:
        return self._cliente.requisitar(replace(requisicao, nivel=self._nivel))

    @property
    def cookies(self):
        return self._cliente.cookies


class Coletor:
    def __init__(
        self,
        cliente: ClienteHTTP,
        adaptadores: Mapping[str, Adaptador],
        *,
        teto_paginas: int = 50,
        relogio: Callable[[], float] = time.monotonic,
        agora: Callable[[], datetime] = _agora_utc,
    ) -> None:
        self.cliente = cliente
        self.adaptadores = adaptadores
        self.teto_paginas = teto_paginas
        self.relogio = relogio
        self.agora = agora

    def coletar(self, leiloeiros: Sequence[Leiloeiro]) -> list[RespostaBruta]:
        respostas: list[RespostaBruta] = []
        for leiloeiro in leiloeiros:
            if leiloeiro.ativo:
                respostas.extend(self._coletar_leiloeiro(leiloeiro))
        return respostas

    def _coletar_leiloeiro(self, leiloeiro: Leiloeiro) -> list[RespostaBruta]:
        adaptador = self.adaptadores[leiloeiro.id]
        if hasattr(adaptador, "agora"):  # feature 005: datas sem ano (Milan) seguem o relógio da varredura
            adaptador.agora = self.agora
        inicio, momento = self.relogio(), self.agora()
        try:
            preparo = adaptador.preparar_sessao(_ClienteNoNivel(self.cliente, leiloeiro.nivel_coleta))
        except Exception as erro:  # noqa: BLE001 — isola bug de adaptador (RF-05)
            log.exception("coleta  | %s | erro interno ao preparar a sessão", leiloeiro.nome)
            return [self._falha(busca, leiloeiro, momento, inicio, Veredito.FALHA_REDE, None, 0,
                                f"preparacao_sessao: erro_interno: {erro}") for busca in leiloeiro.buscas]
        if preparo is not None and not preparo.ok:
            log.warning("coleta  | %s | preparação de sessão falhou: %s", leiloeiro.nome, preparo.motivo)
            return [self._falha(busca, leiloeiro, momento, inicio, preparo.veredito, preparo.status_http,
                                preparo.tentativas, f"preparacao_sessao: {preparo.motivo}") for busca in leiloeiro.buscas]
        if preparo is not None:
            log.info("coleta  | %s | preparando sessão: ok (%d cookie(s))", leiloeiro.nome, len(self.cliente.cookies))
        return [self._coletar_busca(leiloeiro, adaptador, busca) for busca in leiloeiro.buscas]

    def _falha(self, busca: Busca, leiloeiro: Leiloeiro, iniciado_em: datetime, inicio: float, veredito: Veredito,
               status: int | None, tentativas: int, motivo: str) -> RespostaBruta:
        return RespostaBruta(busca_id=busca.id, leiloeiro_id=leiloeiro.id, iniciado_em=iniciado_em,
                             duracao_ms=int((self.relogio() - inicio) * 1000), status_http=status, paginas=[],
                             nivel_usado=leiloeiro.nivel_coleta, tentativas=tentativas, veredito=veredito,
                             motivo=motivo)

    def _coletar_busca(self, leiloeiro: Leiloeiro, adaptador: Adaptador, busca: Busca) -> RespostaBruta:
        inicio, momento = self.relogio(), self.agora()
        paginas: list[Pagina] = []
        tentativas_max = 0
        status = None
        numero = 1
        teto = getattr(adaptador, "teto_paginas", self.teto_paginas)  # D-47 da feature 002
        try:
            while True:
                if numero > teto:
                    log.warning("coleta  | %s | busca=%s | teto de %d páginas atingido; revise o adaptador",
                                leiloeiro.nome, busca.id, teto)
                    return self._falha(busca, leiloeiro, momento, inicio, Veredito.FALHA_REDE, status,
                                       tentativas_max, "teto_paginas")
                requisicao = replace(adaptador.montar_requisicao(busca.filtros, numero), nivel=leiloeiro.nivel_coleta)
                resultado = self.cliente.requisitar(requisicao)
                tentativas_max = max(tentativas_max, resultado.tentativas)
                status = resultado.status_http
                if not resultado.ok:
                    log.warning("coleta  | %s | busca=%s | pág %d | %s | %s", leiloeiro.nome, busca.id, numero,
                                resultado.veredito.value.upper(), resultado.motivo)
                    return self._falha(busca, leiloeiro, momento, inicio, resultado.veredito, status,
                                       tentativas_max, f"pagina {numero}: {resultado.motivo}")
                maximo = (self.cliente.tentativas_de(leiloeiro.nivel_coleta) if hasattr(self.cliente, "tentativas_de")
                          else self.cliente.tentativas)
                log.info("coleta  | %s | busca=%s | pág %d | %s | %s | tentativa %d/%d | ok", leiloeiro.nome, busca.id,
                         numero, leiloeiro.nivel_coleta, status, resultado.tentativas, maximo)
                paginas.append(Pagina(numero=numero, metodo=requisicao.metodo, url=resultado.url,
                                      conteudo=resultado.conteudo or b"", anotacoes=dict(requisicao.anotacoes or {})))
                if not adaptador.tem_proxima_pagina(resultado.conteudo or b"", numero):
                    break
                numero += 1
        except Exception as erro:  # noqa: BLE001 — isola bug de adaptador (RF-05)
            log.exception("coleta  | %s | busca=%s | erro interno", leiloeiro.nome, busca.id)
            return self._falha(busca, leiloeiro, momento, inicio, Veredito.FALHA_REDE, status, tentativas_max,
                               f"erro_interno: {erro}")

        log.info("coleta  | %s | busca=%s | %d página(s) | ok", leiloeiro.nome, busca.id, len(paginas))
        return RespostaBruta(busca_id=busca.id, leiloeiro_id=leiloeiro.id, iniciado_em=momento,
                             duracao_ms=int((self.relogio() - inicio) * 1000), status_http=status, paginas=paginas,
                             nivel_usado=leiloeiro.nivel_coleta, tentativas=tentativas_max, veredito=Veredito.OK)
