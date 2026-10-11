"""Adaptador da Copart Brasil (feature 003; interfaces/copart-busca.md; roadmap D-53 a D-59).

A busca pública é a mesma que a página `/vehicleFinderSearch` usa: `POST /public/vehicleFinder/search`,
em formulário, devolvendo JSON. Sem ordenação explícita a Copart repete e omite lotes entre páginas
(medido em 2026-10-11: 36 de 1.506), por isso toda requisição pede `sort=lot_number asc`.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping

from bot_leilao.coleta.modelos import Requisicao, ResultadoHTTP
from bot_leilao.coleta.registro import registrar_adaptador

log = logging.getLogger(__name__)

BASE = "https://www.copart.com.br"
NOME = "Copart"
TAMANHO_PAGINA = 100
CABECALHOS_AJAX = {"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest",
                   "Origin": BASE, "Referer": f"{BASE}/vehicleFinderSearch"}

# Chaves de faceta que o próprio site devolve (2026-10-11).
FILTROS_ACEITOS = ("condicao", "categoria", "marca", "modelo", "patioveiculo", "patioleilao", "anomodelo",
                   "classificacaodano", "tipodocumento", "condicaofuncionamento", "chaves", "blindado", "tipovenda",
                   "dataleilao")


def _valores(valor) -> list[str]:
    return [str(v) for v in valor] if isinstance(valor, list) else [str(valor)]


class AdaptadorCopart:
    leiloeiro_id = "copart"
    teto_paginas = 40  # D-59: hoje são 16 páginas de 100 lotes

    def __init__(self) -> None:
        self._reiniciar()

    def _reiniciar(self) -> None:
        self._lidos = 0
        self._vistos: set[int] = set()

    def validar_filtros(self, filtros: Mapping) -> None:
        for chave, valor in filtros.items():
            if chave not in FILTROS_ACEITOS:
                raise ValueError(f"chave de filtro '{chave}' desconhecida para a {NOME}; aceitas: "
                                 f"{', '.join(FILTROS_ACEITOS)}")
            if not all(str(v).strip() for v in _valores(valor)):
                raise ValueError(f"o filtro '{chave}' da {NOME} não aceita valor vazio")

    def preparar_sessao(self, cliente) -> ResultadoHTTP:
        """Abre a página da busca, como um navegador, para obter os cookies do Imperva (D-56)."""
        return cliente.requisitar(Requisicao("GET", f"{BASE}/vehicleFinderSearch"))

    def montar_requisicao(self, filtros: Mapping, pagina: int) -> Requisicao:
        self.validar_filtros(filtros)
        if pagina == 1:
            self._reiniciar()
        dados = {"query": "*"}
        for chave, valor in filtros.items():
            dados[f"filter[{chave}]"] = ",".join(f'{chave}:"{v}"' for v in _valores(valor))
        indice = pagina - 1
        dados.update({"sort": "lot_number asc", "page": str(indice), "size": str(TAMANHO_PAGINA),
                      "start": str(indice * TAMANHO_PAGINA)})
        return Requisicao("POST", f"{BASE}/public/vehicleFinder/search", dados=dados, cabecalhos=dict(CABECALHOS_AJAX))

    def tem_proxima_pagina(self, conteudo: bytes, pagina: int) -> bool:
        """Próxima enquanto faltar lote para o total; avisa repetição entre páginas (D-55)."""
        try:
            resultados = json.loads(conteudo)["data"]["results"]
            total, lotes = int(resultados["totalElements"]), list(resultados["content"])
        except (ValueError, KeyError, TypeError):
            return False  # formato inesperado: o parser acusa a quebra nesta mesma página
        repetidos = sorted({l.get("ln") for l in lotes} & self._vistos)
        if repetidos:
            log.warning("coleta  | %s | lote(s) repetido(s) entre páginas: %s; a ordenação da busca mudou?",
                        NOME, ", ".join(map(str, repetidos[:10])))
        self._vistos.update(l.get("ln") for l in lotes)
        self._lidos += len(lotes)
        if lotes and self._lidos < total:
            return True
        if self._lidos != total:
            log.warning("coleta  | %s | o site informou %d lote(s) e foram lidos %d; se repetir, revise o adaptador",
                        NOME, total, self._lidos)
        return False

    def tipo_leilao_da_busca(self, filtros: Mapping) -> str | None:
        """D-58: só a condição FINANCIAMENTO tem correspondência inequívoca."""
        valores = {v.strip().upper() for v in _valores(filtros.get("condicao", []))}
        return "financiamento" if valores == {"FINANCIAMENTO"} else None


registrar_adaptador(AdaptadorCopart())
