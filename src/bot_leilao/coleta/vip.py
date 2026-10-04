"""Adaptador do Vip Leilões (interfaces/vip-pesquisa.md; roadmap D-10 a D-13, D-15)."""

from __future__ import annotations

import logging
import math
import re
from collections.abc import Mapping

from bs4 import BeautifulSoup

from bot_leilao.coleta.http import ClienteHTTP
from bot_leilao.coleta.modelos import Requisicao, ResultadoHTTP
from bot_leilao.coleta.registro import registrar_adaptador

log = logging.getLogger(__name__)

BASE = "https://www.vipleiloes.com.br"
TAMANHO_PAGINA = 12
CAMPOS_FIXOS = {"Filtro.OrdenarPor": "DataInicio", "Filtro.SelecaoVeiculos": "true"}
CABECALHOS_AJAX = {"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE}/pesquisa/index"}

# Chave no YAML → campo do formulário #formPost (observado em 2026-10-03).
MAPA_FILTROS = {
    "procedencia": "Filtro.Procedencia",
    "monta": "Filtro.Monta",
    "marca": "Filtro.Marca",
    "modelo": "Filtro.Modelo",
    "ano": "Filtro.Ano",
    "classificacao": "Filtro.Classificacao",
    "quilometragem_de": "Filtro.QuilometragemDe",
    "quilometragem_ate": "Filtro.QuilometragemAte",
    "valor_de": "Filtro.ValorDe",
    "valor_ate": "Filtro.ValorAte",
    "estado": "Filtro.LocalEstadoId",
    "financiavel": "Filtro.Financiavel",
    "texto": "Filtro.Texto",
}

# D-15: só a procedência 4 tem correspondência inequívoca no conjunto fechado de tipos_leilao.
TIPO_POR_PROCEDENCIA = {"4": "financiamento"}

_DIGITOS = re.compile(r"\d+")


def _valor_formulario(valor: object) -> str:
    if isinstance(valor, bool):
        return "true" if valor else "false"
    return str(valor)


def total_resultados(soup: BeautifulSoup) -> int | None:
    indicador = soup.select_one("#resultadosEncontrados")
    if indicador is None:
        return None
    achado = _DIGITOS.search(indicador.get_text())
    return int(achado.group()) if achado else None


class AdaptadorVip:
    leiloeiro_id = "vip-leiloes"

    def validar_filtros(self, filtros: Mapping) -> None:
        for chave, valor in filtros.items():
            if chave not in MAPA_FILTROS:
                raise ValueError(f"chave de filtro '{chave}' desconhecida para o Vip; aceitas: {', '.join(MAPA_FILTROS)}")
            if isinstance(valor, list):
                raise ValueError(f"o filtro '{chave}' não aceita lista: o formulário do Vip não tem múltipla escolha")

    def preparar_sessao(self, cliente: ClienteHTTP) -> ResultadoHTTP:
        """GET na home para obter o cookie de canal `__CBCanal` (D-10)."""
        return cliente.requisitar(Requisicao("GET", f"{BASE}/"))

    def montar_requisicao(self, filtros: Mapping, pagina: int) -> Requisicao:
        self.validar_filtros(filtros)
        dados = dict(CAMPOS_FIXOS)
        dados.update({MAPA_FILTROS[chave]: _valor_formulario(valor) for chave, valor in filtros.items()})
        if pagina == 1:
            url = f"{BASE}/pesquisa?handler=pesquisar"
        else:
            url = f"{BASE}/pesquisa?SortOrder=DataInicio&pageNumber={pagina}&handler=pesquisar"
        return Requisicao("POST", url, dados=dados, cabecalhos=dict(CABECALHOS_AJAX))

    def tem_proxima_pagina(self, conteudo: bytes, pagina: int) -> bool:
        """Link "Next" sem a classe `disabled`, com verificação cruzada pelo total (D-13)."""
        soup = BeautifulSoup(conteudo, "lxml")
        proximo = soup.select_one('.main-pagination a[aria-label="Next"]')
        tem = proximo is not None and "disabled" not in (proximo.find_parent("li") or {}).get("class", [])
        total = total_resultados(soup)
        if total is not None:
            esperadas = max(1, math.ceil(total / TAMANHO_PAGINA))
            if (not tem and pagina < esperadas) or (tem and pagina >= esperadas):
                log.warning("coleta  | Vip Leilões | paginação diverge do total: %d resultados indicam %d páginas, "
                            "mas a página %d %s próxima. Revise o adaptador.",
                            total, esperadas, pagina, "tem" if tem else "não tem")
        return tem

    def tipo_leilao_da_busca(self, filtros: Mapping) -> str | None:
        return TIPO_POR_PROCEDENCIA.get(str(filtros.get("procedencia")))


registrar_adaptador(AdaptadorVip())
