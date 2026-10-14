"""Adaptador do Milan Leilões (feature 005; interfaces/milan.md; roadmap D-93, D-94, D-97).

O site inteiro está atrás do Cloudflare: as páginas vêm pelo nível `apify` (o coletor carimba o nível). Uma busca
vira a sequência agenda (`/agenda/veiculos`) → catálogo (`/leilao/<id>/catalogo`) de cada leilão cujo card traz
o texto do filtro ("recuperados de financiamento"). O catálogo é lido em toda varredura (D-94): lotes são
inseridos depois de publicado. O lance atual vem da página do lote, só para os candidatos (enriquecimento).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup

from bot_leilao.coleta.modelos import Requisicao
from bot_leilao.coleta.registro import registrar_adaptador
from bot_leilao.texto import normalizar_texto

log = logging.getLogger(__name__)

BASE = "https://milanleiloes.com.br"
NOME = "Milan Leilões"
BRASILIA = timezone(timedelta(hours=-3))  # offset fixo, como nos outros leiloeiros (D-22)
FILTROS_ACEITOS = ("descricao_contem",)
MESES = {"JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6, "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10,
         "NOV": 11, "DEZ": 12}
_ID_LEILAO = re.compile(r"^/leilao/veiculos/(\d+)")
_DATA_AGENDA = re.compile(r"(\d{1,2}) de ([A-Za-zÇç]{3})\w* às (\d{1,2}):(\d{2})")
_DIAS_TOLERADOS = 60  # data sem ano mais de 60 dias no passado = ano seguinte


@dataclass(frozen=True)
class LeilaoAgenda:
    id: str
    rotulo: str
    pregao_em: datetime | None


def data_sem_ano(dia: int, mes: str, hora: int, minuto: int, referencia: datetime) -> datetime | None:
    """Data do Milan sem ano ("14 OUT 09:30"): o ano da referência, ou o seguinte se ficar muito no passado."""
    numero = MESES.get(mes.upper()[:3])
    if numero is None:
        return None
    local = referencia.astimezone(BRASILIA)
    data = datetime(local.year, numero, dia, hora, minuto, tzinfo=BRASILIA)
    if data < local - timedelta(days=_DIAS_TOLERADOS):
        data = data.replace(year=local.year + 1)
    return data


def ler_agenda(conteudo: bytes, referencia: datetime) -> list[LeilaoAgenda]:
    """Cards da agenda de veículos: `a[href^="/leilao/veiculos/"]`, com data e hora sem ano no texto."""
    soup = BeautifulSoup(conteudo, "lxml")
    leiloes, vistos = [], set()
    for card in soup.select('a[href^="/leilao/veiculos/"]'):
        achado = _ID_LEILAO.match(card.get("href", ""))
        if achado is None or achado.group(1) in vistos:
            continue
        vistos.add(achado.group(1))
        rotulo = " ".join(card.get_text(" ", strip=True).split())
        data = _DATA_AGENDA.search(rotulo)
        pregao = (data_sem_ano(int(data.group(1)), data.group(2), int(data.group(3)), int(data.group(4)), referencia)
                  if data else None)
        leiloes.append(LeilaoAgenda(id=achado.group(1), rotulo=rotulo, pregao_em=pregao))
    return leiloes


def agenda_reconhecida(conteudo: bytes) -> bool:
    """A agenda tem cards de leilão ou declara quantos encontrou ("0 leilões encontrados")."""
    return bool(ler_agenda(conteudo, datetime.now(BRASILIA))) or b"encontrado" in conteudo


class AdaptadorMilan:
    leiloeiro_id = "milan-leiloes"
    teto_paginas = 10  # agenda + catálogos; hoje 1 leilão de financiamento por vez

    def __init__(self) -> None:
        self.agora: Callable[[], datetime] = lambda: datetime.now(timezone.utc)  # o coletor troca pelo dele
        self._reiniciar("")

    def _reiniciar(self, filtro: str) -> None:
        self._filtro = filtro
        self._leiloes: list[LeilaoAgenda] = []
        self._indice = -1

    def validar_filtros(self, filtros: Mapping) -> None:
        for chave, valor in filtros.items():
            if chave not in FILTROS_ACEITOS:
                raise ValueError(f"chave de filtro '{chave}' desconhecida para o {NOME}; aceita: "
                                 f"{', '.join(FILTROS_ACEITOS)}")
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(f"o filtro 'descricao_contem' do {NOME} deve ser um texto, como "
                                 "'recuperados de financiamento'")

    def preparar_sessao(self, cliente) -> None:
        """Nenhuma: cada página vem inteira pelo Apify."""
        return None

    def tipo_leilao_da_busca(self, filtros: Mapping) -> str | None:
        return "financiamento" if "financiamento" in normalizar_texto(filtros.get("descricao_contem")) else None

    def montar_requisicao(self, filtros: Mapping, pagina: int) -> Requisicao:
        self.validar_filtros(filtros)
        if pagina == 1:
            self._reiniciar(filtros["descricao_contem"])
            return Requisicao("GET", f"{BASE}/agenda/veiculos", anotacoes={"tipo": "agenda"})
        leilao = self._leiloes[self._indice]
        return Requisicao("GET", f"{BASE}/leilao/{leilao.id}/catalogo",
                          anotacoes={"tipo": "catalogo", "evento": leilao.id, "pregao_em": leilao.pregao_em,
                                     "rotulo": leilao.rotulo})

    def tem_proxima_pagina(self, conteudo: bytes, pagina: int) -> bool:
        if pagina == 1:
            filtro = normalizar_texto(self._filtro)
            self._leiloes = [l for l in ler_agenda(conteudo, self.agora()) if filtro in normalizar_texto(l.rotulo)]
            if self._leiloes:
                log.info("coleta  | %s | %d leilão(ões) '%s': %s", NOME, len(self._leiloes), self._filtro,
                         ", ".join(f"{l.id} ({l.pregao_em:%d/%m %H:%M})" if l.pregao_em else l.id
                                   for l in self._leiloes))
            else:
                log.info("coleta  | %s | nenhum leilão '%s' na agenda", NOME, self._filtro)
        self._indice += 1
        return self._indice < len(self._leiloes)

    def requisicao_detalhe(self, lote) -> Requisicao | None:
        """Página do lote, de onde vem o lance atual (D-97), só para os candidatos."""
        return Requisicao("GET", lote.link) if lote.link else None


registrar_adaptador(AdaptadorMilan())
