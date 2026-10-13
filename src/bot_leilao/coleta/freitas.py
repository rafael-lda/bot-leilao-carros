"""Adaptador do Freitas Leiloeiro (feature 004; interfaces/freitas.md; roadmap D-74 a D-78, D-82).

A busca pública é a que a página de veículos chama: `GET /Leiloes/PesquisarLotes`, que devolve HTML parcial com um
card por lote. O fim é a mensagem "Nenhum lote localizado": a paginação só para nela, nunca por página menor
(se o site passar a limitar o tamanho da página, parar cedo perderia lotes em silêncio).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from urllib.parse import urlencode

from bot_leilao.coleta.modelos import Requisicao
from bot_leilao.coleta.registro import registrar_adaptador

log = logging.getLogger(__name__)

BASE = "https://www.freitasleiloeiro.com.br"
NOME = "Freitas Leiloeiro"
TOP_ROWS = 200
MENSAGEM_FIM = b"Nenhum lote localizado"
CABECALHOS_AJAX = {"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE}/Leiloes/Pesquisar?query=&categoria=1"}

# Chave no YAML → parâmetro da busca (D-75). Os demais parâmetros vão sem filtro.
MAPA_FILTROS = {
    "categoria": "Categoria",
    "condicao": "Condicao",
    "tipo_lote": "TipoLoteId",
    "patio": "PatioId",
    "estado": "Estado",
    "cidade": "Cidade",
    "ano_modelo_min": "AnoModeloMin",
    "ano_modelo_max": "AnoModeloMax",
}
PARAMETROS_PADRAO = {"Nome": "", "Categoria": "1", "TipoLoteId": "0", "FaixaValor": "0", "Condicao": "0",
                     "PatioId": "0", "AnoModeloMin": "0", "AnoModeloMax": "0", "ArCondicionado": "false",
                     "DirecaoAssistida": "false", "Tag": "", "Estado": "", "Cidade": "", "ClienteSclId": "0"}

_ID_LOTE = re.compile(rb"leilaoId=(\d+)&(?:amp;)?loteNumero=(\d+)")
_CARD = b'<div class="cardlote">'


class AdaptadorFreitas:
    leiloeiro_id = "freitas-leiloeiro"

    def __init__(self) -> None:
        self._vistos: set[str] = set()

    def validar_filtros(self, filtros: Mapping) -> None:
        for chave, valor in filtros.items():
            if chave not in MAPA_FILTROS:
                raise ValueError(f"chave de filtro '{chave}' desconhecida para o {NOME}; aceitas: "
                                 f"{', '.join(MAPA_FILTROS)}")
            if isinstance(valor, list):
                raise ValueError(f"o filtro '{chave}' do {NOME} não aceita lista")

    def preparar_sessao(self, cliente) -> None:
        """Nenhuma: a busca responde sem cookie nem login."""
        return None

    def montar_requisicao(self, filtros: Mapping, pagina: int) -> Requisicao:
        self.validar_filtros(filtros)
        if pagina == 1:
            self._vistos = set()
        parametros = dict(PARAMETROS_PADRAO)
        parametros.update({MAPA_FILTROS[chave]: str(valor) for chave, valor in filtros.items()})
        parametros.update({"PageNumber": str(pagina), "TopRows": str(TOP_ROWS)})
        return Requisicao("GET", f"{BASE}/Leiloes/PesquisarLotes?{urlencode(parametros)}",
                          cabecalhos=dict(CABECALHOS_AJAX))

    def tem_proxima_pagina(self, conteudo: bytes, pagina: int) -> bool:
        if MENSAGEM_FIM in conteudo:
            return False
        if _CARD not in conteudo:
            return False  # sem cards e sem a mensagem de fim: o parser acusa a quebra nesta página
        ids = []
        for card in conteudo.split(_CARD)[1:]:
            achado = _ID_LOTE.search(card)
            if achado:
                ids.append(f"{achado.group(1).decode()}-{achado.group(2).decode()}")
        repetidos = sorted(set(ids) & self._vistos)
        if repetidos:
            log.warning("coleta  | %s | lote(s) repetido(s) entre páginas: %s; a ordenação da busca mudou?",
                        NOME, ", ".join(repetidos[:10]))
        self._vistos.update(ids)
        return True

    def tipo_leilao_da_busca(self, filtros: Mapping) -> str | None:
        """Só para a checagem de coerência entre alvos e buscas: o tipo real vem da etiqueta de cada lote (D-76)."""
        return "financiamento"

    def requisicao_detalhe(self, lote) -> Requisicao | None:
        """Detalhe do lote (pátio, despesas, selos), pelo link do próprio lote (D-82)."""
        return Requisicao("GET", lote.link) if lote.link else None


registrar_adaptador(AdaptadorFreitas())
