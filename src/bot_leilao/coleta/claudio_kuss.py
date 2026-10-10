"""Adaptador do Claudio Kuss Leilões (feature 002; interfaces/claudio-kuss.md; roadmap D-33 a D-40, D-47, D-48).

O Kuss organiza os lotes em eventos com data marcada. Uma busca vira a sequência de páginas:
agenda (`/proximos-leiloes`) → para cada evento da categoria, quantidade (`op=Q`) e páginas de
10 lotes (`op=P`). O adaptador guarda um cursor; o coletor percorre uma busca por vez, em ordem.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup

from bot_leilao.coleta.modelos import Requisicao
from bot_leilao.coleta.registro import registrar_adaptador
from bot_leilao.texto import normalizar_texto

log = logging.getLogger(__name__)

BASE = "https://www.claudiokussleiloes.com.br"
NOME = "Claudio Kuss Leilões"
# Horário de Brasília, sem horário de verão desde 2019. Offset fixo: o Windows não traz a base de fusos do zoneinfo.
FUSO = timezone(timedelta(hours=-3))
FILTROS_ACEITOS = ("categoria",)

_ID_EVENTO = re.compile(r"relacao-foto/(\d+)")
_DATA_HORA = re.compile(r"(\d{2})/(\d{2})/(\d{4})\D+(\d{1,2}):(\d{2})")


@dataclass(frozen=True)
class Evento:
    id: str
    rotulo: str
    pregao_em: datetime | None


def ler_agenda(conteudo: bytes) -> list[Evento]:
    """Blocos de evento da agenda: rótulo no cabeçalho, data no corpo, id no link `relacao-foto/<id>`."""
    soup = BeautifulSoup(conteudo, "lxml")
    eventos: list[Evento] = []
    for bloco in soup.select("div.panel"):
        cabecalho = bloco.select_one(".panel-heading")
        link = bloco.select_one('a[href*="relacao-foto/"]')
        if cabecalho is None or link is None:
            continue
        achado_id = _ID_EVENTO.search(link.get("href", ""))
        if achado_id is None:
            continue
        data = bloco.select_one(".panel-body h2")
        achado_data = _DATA_HORA.search(data.get_text(" ", strip=True)) if data else None
        pregao = None
        if achado_data:
            dia, mes, ano, hora, minuto = map(int, achado_data.groups())
            pregao = datetime(ano, mes, dia, hora, minuto, tzinfo=FUSO)
        eventos.append(Evento(id=achado_id.group(1), rotulo=" ".join(cabecalho.get_text(" ", strip=True).split()),
                              pregao_em=pregao))
    return eventos


def _cabecalhos(referer: str) -> dict:
    return {"X-Requested-With": "XMLHttpRequest", "Referer": referer}


def _json(conteudo: bytes):
    try:
        return json.loads(conteudo)
    except ValueError:
        return None


class AdaptadorClaudioKuss:
    leiloeiro_id = "claudio-kuss-leiloes"
    teto_paginas = 120  # D-47: ~43 páginas com 2 eventos; 120 páginas a 5 s = 10 min

    def __init__(self) -> None:
        self._reiniciar("")

    def _reiniciar(self, categoria: str) -> None:
        self._categoria = categoria
        self._eventos: list[Evento] = []
        self._indice = 0
        self._pagina = 0          # 0: a próxima requisição do evento é a quantidade (op=Q)
        self._qtde = 0
        self._qtde_paginas = 0
        self._lidos = 0

    def validar_filtros(self, filtros: Mapping) -> None:
        for chave, valor in filtros.items():
            if chave not in FILTROS_ACEITOS:
                raise ValueError(f"chave de filtro '{chave}' desconhecida para o {NOME}; aceita: "
                                 f"{', '.join(FILTROS_ACEITOS)}")
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(f"o filtro 'categoria' do {NOME} deve ser um texto, como 'Veículos - Financeiras'")

    def preparar_sessao(self, cliente) -> None:
        """O Kuss não exige cookie nem página de entrada."""
        return None

    def tipo_leilao_da_busca(self, filtros: Mapping) -> str | None:
        return "financiamento" if "financeiras" in normalizar_texto(filtros.get("categoria")) else None  # D-39

    # --- Sequência de páginas (D-34, D-35) ---------------------------------------------------

    def montar_requisicao(self, filtros: Mapping, pagina: int) -> Requisicao:
        self.validar_filtros(filtros)
        if pagina == 1:
            self._reiniciar(filtros["categoria"])
            return Requisicao("GET", f"{BASE}/proximos-leiloes",
                              anotacoes={"tipo": "agenda", "categoria": filtros["categoria"]})
        evento = self._eventos[self._indice]
        anotacoes = {"evento": evento.id, "pregao_em": evento.pregao_em}
        cabecalhos = _cabecalhos(f"{BASE}/relacao-foto/{evento.id}")
        if self._pagina == 0:
            return Requisicao("POST", f"{BASE}/json_edital.php", dados={"op": "Q", "leilaoID": evento.id, "pesq": ""},
                              cabecalhos=cabecalhos, anotacoes={"tipo": "quantidade", **anotacoes})
        return Requisicao("POST", f"{BASE}/json_edital.php",
                          dados={"leilaoID": evento.id, "op": "P", "pag": str(self._pagina), "loteado": "", "pesq": ""},
                          cabecalhos=cabecalhos, anotacoes={"tipo": "lotes", **anotacoes})

    def tem_proxima_pagina(self, conteudo: bytes, pagina: int) -> bool:
        if pagina == 1:
            categoria = normalizar_texto(self._categoria)
            self._eventos = [e for e in ler_agenda(conteudo) if categoria in normalizar_texto(e.rotulo)]
            if self._eventos:
                log.info("coleta  | %s | %d evento(s) '%s': %s", NOME, len(self._eventos), self._categoria,
                         ", ".join(f"{e.id} ({e.pregao_em:%d/%m %H:%M})" if e.pregao_em else e.id
                                   for e in self._eventos))
            return bool(self._eventos)
        if self._pagina == 0:
            return self._apos_quantidade(conteudo)
        return self._apos_lotes(conteudo)

    def _apos_quantidade(self, conteudo: bytes) -> bool:
        dados = _json(conteudo)
        try:
            self._qtde, self._qtde_paginas = int(dados["qtde"]), int(dados["qtdePag"])
        except (TypeError, KeyError, ValueError):
            # Formato inesperado: o parser acusa a quebra nesta mesma página; aqui só seguimos adiante.
            return self._proximo_evento()
        self._lidos = 0
        if self._qtde > 0 and self._qtde_paginas > 0:
            self._pagina = 1
            return True
        return self._proximo_evento()

    def _apos_lotes(self, conteudo: bytes) -> bool:
        itens = _json(conteudo)
        lidos = len(itens) if isinstance(itens, list) else 0
        self._lidos += lidos
        if lidos and self._pagina < self._qtde_paginas:
            self._pagina += 1
            return True
        if self._lidos != self._qtde:  # D-36: aviso, não falha (lote pode sair da lista no meio da leitura)
            log.warning("coleta  | %s | evento %s: o site informou %d lote(s) e foram lidos %d; "
                        "se repetir, revise o adaptador", NOME, self._eventos[self._indice].id, self._qtde, self._lidos)
        return self._proximo_evento()

    def _proximo_evento(self) -> bool:
        self._indice += 1
        self._pagina = 0
        return self._indice < len(self._eventos)

    # --- Detalhe do lote, só para os novos (D-48) --------------------------------------------

    def requisicao_detalhe(self, lote) -> Requisicao | None:
        if not lote.evento_id or not lote.id_canonico or ":" not in lote.id_canonico:
            return None
        seq = lote.id_canonico.split(":", 1)[1]
        return Requisicao("POST", f"{BASE}/json_lance_info_lote.php",
                          dados={"op": "D", "leilaoID": lote.evento_id, "le_id": seq, "loteado": "N"},
                          cabecalhos=_cabecalhos(f"{BASE}/lance/{lote.evento_id}/0/{seq}"))


registrar_adaptador(AdaptadorClaudioKuss())
