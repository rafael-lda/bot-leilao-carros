"""Parser do Vip Leilões (interfaces/vip-pesquisa.md §3; roadmap D-14 a D-16, D-28, D-31)."""

from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup, Tag

from bot_leilao.parsing.marcas import marca_canonica
from bot_leilao.parsing.modelos import ContextoParsing, ExtracaoPagina, Lote
from bot_leilao.parsing.normalizadores import inteiro, link_absoluto, normalizar_anos, normalizar_km, normalizar_preco
from bot_leilao.parsing.nucleo import registrar_parser
from bot_leilao.texto import normalizar_texto

log = logging.getLogger(__name__)

LEILOEIRO_ID = "vip-leiloes"
SITUACAO_ABERTA = "aberto para lances"
_ID_ANUNCIO = re.compile(r"-(\d+)/?(?:[?#].*)?$")
_TOTAL = re.compile(r"\d+")


def _texto(no: Tag | None) -> str | None:
    if no is None:
        return None
    texto = " ".join(no.get_text(" ", strip=True).split())
    return texto or None


def _numero_do_lote(card: Tag) -> str | None:
    rotulo = card.find("strong", string=re.compile(r"Lote:"))
    if rotulo is None or rotulo.next_sibling is None:
        return None
    return str(rotulo.next_sibling).strip() or None


def _local(card: Tag) -> str | None:
    rotulo = card.find("strong", string=re.compile(r"Local:"))
    if rotulo is None or rotulo.next_sibling is None:
        return None
    return str(rotulo.next_sibling).strip() or None


def _lance_inicial(card: Tag) -> str | None:
    for rotulo in card.select(".anc-lel"):
        if "inicial" in rotulo.get_text().lower():
            return _texto(rotulo.find("b")) or _texto(rotulo)
    return None


class ParserVip:
    def extrair(self, conteudo: bytes, contexto: ContextoParsing) -> ExtracaoPagina:
        soup = BeautifulSoup(conteudo, "lxml")
        indicador = soup.select_one("#resultadosEncontrados")
        total = None
        if indicador is not None:
            achado = _TOTAL.search(indicador.get_text())
            total = int(achado.group()) if achado else None
        aviso_vazio = _texto(soup.select_one("div.filter-wait"))
        busca_vazia = total == 0 or (aviso_vazio is not None and "nenhum lote encontrado" in aviso_vazio.lower())

        lotes = [self._lote(card, contexto) for card in soup.select("div.card-anuncio")]
        return ExtracaoPagina(lotes=lotes, busca_vazia=busca_vazia and not lotes, total_informado=total)

    def _lote(self, card: Tag, contexto: ContextoParsing) -> Lote:
        ancora = card.select_one("a.crd-status") or card.select_one("a.anc-body")
        href = ancora.get("href") if ancora is not None else None
        link = link_absoluto(href, contexto.base_url)
        achado_id = _ID_ANUNCIO.search(href or "")
        id_canonico = f"{LEILOEIRO_ID}:{achado_id.group(1)}" if achado_id else None

        titulo_bruto = _texto(card.select_one(".anc-title h1")) or ""
        modelo_bruto, _, anos_bruto = titulo_bruto.rpartition(" - ")
        if not modelo_bruto:
            modelo_bruto, anos_bruto = titulo_bruto, ""
        ano_fabricacao, ano_modelo = normalizar_anos(anos_bruto)

        infos = [_texto(s) or "" for s in card.select(".anc-info span")]
        marca = marca_canonica(infos[0]) if infos and infos[0] else None
        km = next((normalizar_km(i) for i in infos if i.lower().endswith("km")), None)

        lances = inteiro(_texto(card.select_one(".anc-lanc")))
        valor_atual = normalizar_preco(_texto(card.select_one(".valor-atual")))
        lance_inicial = normalizar_preco(_lance_inicial(card))
        lance_corrente = None if lances == 0 else valor_atual

        situacao = _texto(card.select_one(".situacao"))
        classes = " ".join(card.get("class", []))
        retirado = "retirad" in normalizar_texto(situacao) or "retirad" in classes.lower()
        if not retirado and normalizar_texto(situacao) != SITUACAO_ABERTA:
            log.info("parser  | Vip Leilões | situação não reconhecida em %s: %r", id_canonico, situacao)

        modelo_exibicao = modelo_bruto.strip().title()
        titulo = f"{marca.title()} {modelo_exibicao}" if marca else modelo_exibicao
        inicio = " ".join(filter(None, [_texto(card.select_one(".anc-start")), _texto(card.select_one(".anc-hour"))]))
        descricao = " | ".join(filter(None, [
            titulo_bruto,
            f"Local: {_local(card)}" if _local(card) else None,
            _texto(card.select_one(".anc-lanc")),
            inicio or None,
            situacao,
        ]))

        return Lote(
            id_canonico=id_canonico,
            leiloeiro_id=contexto.leiloeiro_id,
            busca_id=contexto.busca_id,
            link=link,
            coletado_em=contexto.coletado_em,
            numero_lote=_numero_do_lote(card),
            titulo=titulo or None,
            marca=marca,
            modelo=normalizar_texto(modelo_bruto) or None,
            ano_fabricacao=ano_fabricacao,
            ano_modelo=ano_modelo,
            lance_inicial=lance_inicial,
            lance_corrente=lance_corrente,
            quilometragem=km,
            descricao=descricao or None,
            tipo_leilao=contexto.tipo_leilao,
            situacao=situacao,
            retirado=retirado,
        )


registrar_parser(LEILOEIRO_ID, ParserVip())
