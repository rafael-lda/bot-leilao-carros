"""Parser do Freitas Leiloeiro (feature 004; interfaces/freitas.md; roadmap D-76 a D-82).

Cada card traz: número do lote, link do detalhe, data e hora do pregão, descrição
"MARCA/MODELO, AA/AA, PLACA: X__-___0, COMBUSTÍVEL, COR", valor com o rótulo ("Maior lance" ou "Lance Inicial"),
a etiqueta de origem ("FINANCEIRA") e o estado ("ABERTO PARA LANCES" ou "EM LOTEAMENTO").
"""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from bs4 import BeautifulSoup, Comment, Tag

from bot_leilao.parsing.marcas import marca_canonica
from bot_leilao.parsing.modelos import ContextoParsing, ExtracaoPagina, Lote
from bot_leilao.parsing.normalizadores import anos_dois_digitos, normalizar_preco
from bot_leilao.parsing.nucleo import registrar_parser
from bot_leilao.texto import normalizar_texto

log = logging.getLogger(__name__)

LEILOEIRO_ID = "freitas-leiloeiro"
BRASILIA = timezone(timedelta(hours=-3))  # offset fixo, como nos outros leiloeiros
MENSAGEM_FIM = "Nenhum lote localizado"
_ID_LOTE = re.compile(r"leilaoId=(\d+)&loteNumero=(\d+)")
_DATA_HORA = re.compile(r"(\d{2})/(\d{2})/(\d{4})\D+(\d{1,2}):(\d{2})")
_IMPORTADO = re.compile(r"^I/", re.IGNORECASE)
_PATIO = re.compile(r"Visitação/Retirada:\s*(.*?)/\s*([A-Z]{2})\b")
_DESPESA = re.compile(r"Despesas (operacionais|de logística) no valor de (R\$\s*[\d.,]+)")


def _texto(no: Tag | None) -> str:
    return " ".join(no.get_text(" ", strip=True).split()) if no is not None else ""


def _marca_e_modelo(bem: str) -> tuple[str | None, str | None]:
    """D-79: tira o "I/" de importado; divide na barra, senão a primeira palavra é a marca."""
    resto = _IMPORTADO.sub("", bem.strip())
    if "/" in resto:
        marca, _, modelo = resto.partition("/")
    else:
        marca, _, modelo = resto.partition(" ")
    return marca.strip() or None, modelo.strip() or None


class ParserFreitas:
    def extrair(self, conteudo: bytes, contexto: ContextoParsing) -> ExtracaoPagina:
        soup = BeautifulSoup(conteudo, "lxml")
        cards = soup.select("div.cardlote")
        if not cards:
            if MENSAGEM_FIM in soup.get_text():
                return ExtracaoPagina(lotes=[], busca_vazia=True)
            raise ValueError("página do Freitas sem cards e sem a mensagem de fim")
        lotes, em_loteamento = [], 0
        for card in cards:
            if "EM LOTEAMENTO" in _texto(card.select_one(".cardLote-btn")).upper():
                em_loteamento += 1   # D-77 / RN-10: número provisório, entra quando for loteado
                continue
            lotes.append(self._lote(card, contexto))
        if em_loteamento:
            log.info("parser  | busca=%s | %d lote(s) em loteamento ignorado(s) até ganharem número definitivo",
                     contexto.busca_id, em_loteamento)
        return ExtracaoPagina(lotes=lotes, busca_vazia=not lotes)

    def _lote(self, card: Tag, contexto: ContextoParsing) -> Lote:
        link = card.select_one('a[href*="LoteDetalhes"]')
        achado = _ID_LOTE.search(html.unescape(link["href"])) if link else None
        if not achado:
            raise ValueError("card do Freitas sem link do lote")
        leilao, numero = achado.groups()
        partes = [p.strip() for p in _texto(card.select_one(".cardLote-descVeic")).split(", ")]
        if len(partes) != 5 or not partes[2].upper().startswith("PLACA:"):
            raise ValueError(f"descrição fora do formato no lote {leilao}/{numero}: {partes!r}")
        bem, ano, placa = partes[0], partes[1], partes[2].split(":", 1)[1].strip()
        marca, modelo = _marca_e_modelo(bem)
        fabricacao, ano_modelo = anos_dois_digitos(ano, contexto.coletado_em.year)
        valor = normalizar_preco(_texto(card.select_one(".cardLote-vlr")) or None)
        rotulo = normalizar_texto(_texto(card.select_one(".cardLote-lance")))
        data = _DATA_HORA.search(_texto(card.select_one(".cardLote-data")))
        etiqueta = _texto(card.select_one(".cardLote-details")).upper()
        return Lote(
            id_canonico=f"{LEILOEIRO_ID}:{leilao}-{numero}",                            # D-78
            leiloeiro_id=contexto.leiloeiro_id,
            busca_id=contexto.busca_id,
            link=f"{contexto.base_url}/Leiloes/LoteDetalhes?leilaoId={leilao}&loteNumero={numero}",
            coletado_em=contexto.coletado_em,
            numero_lote=_texto(card.select_one(".cardLote-lote")) or None,
            titulo=bem,
            marca=marca_canonica(marca) if marca else None,
            modelo=normalizar_texto(modelo) or None,
            ano_fabricacao=fabricacao,
            ano_modelo=ano_modelo,
            lance_corrente=valor if rotulo.startswith("maior lance") else None,       # D-80
            lance_inicial=valor if rotulo.startswith("lance inicial") else None,
            pregao_em=datetime(int(data.group(3)), int(data.group(2)), int(data.group(1)), int(data.group(4)),
                               int(data.group(5)), tzinfo=BRASILIA) if data else None,  # D-81
            placa_parcial=placa or None,
            tipo_leilao="financiamento" if etiqueta == "FINANCEIRA" else None,         # D-76
        )

    def aplicar_detalhe(self, lote: Lote, conteudo: bytes) -> None:
        """D-82: pátio de "Visitação/Retirada", despesas operacionais (+ logística) e selos do lote."""
        soup = BeautifulSoup(conteudo, "lxml")
        for comentario in soup.find_all(string=lambda s: isinstance(s, Comment)):  # o site comenta código Razor
            comentario.extract()
        for bloco in soup(["script", "style"]):
            bloco.decompose()
        texto = " ".join(soup.get_text(" ").split())
        patio = _PATIO.search(texto)
        despesas = {tipo: normalizar_preco(valor) for tipo, valor in _DESPESA.findall(texto)}
        if not patio and not despesas:
            raise ValueError("detalhe do Freitas sem pátio nem despesas")
        if patio:
            lote.patio = f"{patio.group(1).split(' - ')[-1].strip()} - {patio.group(2)}"
        if despesas:
            lote.despesas_adm = sum(despesas.values(), Decimal(0))
        selos = [s for s in (_texto(span) for span in soup.select("span.fw-bolder.text-success")) if s]
        observacoes = list(selos)
        if "de logística" in despesas:
            observacoes.append(f"Despesas: operacionais {self._reais(despesas.get('operacionais'))} + logística "
                               f"{self._reais(despesas['de logística'])}")
        lote.observacoes = " · ".join(observacoes) or None
        lote.retirado = lote.retirado or "RETIRADO" in texto.upper().split("MAIOR LANCE:", 1)[-1][:60]
        lote.detalhe_lido = True

    @staticmethod
    def _reais(valor: Decimal | None) -> str:
        return "R$ ?" if valor is None else "R$ " + f"{int(valor):,}".replace(",", ".")


registrar_parser(LEILOEIRO_ID, ParserFreitas())
