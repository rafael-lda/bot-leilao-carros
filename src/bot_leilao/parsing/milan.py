"""Parser do Milan Leilões (feature 005; interfaces/milan.md §2 a §4; roadmap D-95 a D-97).

Páginas da busca, distinguidas pela anotação `tipo`: a agenda (sem lotes) e o catálogo de cada leilão, com todos
os lotes numa página (km, câmbio, avisos em vermelho, comitente; lance inicial em alguns). O lance atual vem da
página do lote (`aplicar_detalhe`), lida só para os candidatos pelo enriquecimento.
"""

from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup, Tag

from bot_leilao.coleta.milan import agenda_reconhecida, data_sem_ano
from bot_leilao.parsing.marcas import MARCAS_CONHECIDAS, marca_canonica
from bot_leilao.parsing.modelos import ContextoParsing, ExtracaoPagina, Lote
from bot_leilao.parsing.normalizadores import normalizar_preco
from bot_leilao.parsing.nucleo import registrar_parser
from bot_leilao.texto import normalizar_texto

log = logging.getLogger(__name__)

LEILOEIRO_ID = "milan-leiloes"
SITUACAO_SUCATA = "sucata"
_NUMERO = re.compile(r"Lote\s+(\S+)")
_ANOS = re.compile(r"\bANO (\d{4})/(\d{4})")
_INICIO = re.compile(r"Início:\s*(\d{1,2})\s+([A-Za-zÇç]{3})\w*\s+(\d{1,2}):(\d{2})")
_KM = re.compile(r"\bKM:\s*([\d.]+)")
_IPVA = re.compile(r"IPVA \d{4} PAGO")
_COMITENTE = re.compile(r"\(([^()]+)\)\.?\s*$")
_CIDADE_UF = re.compile(r",\s*([^,]+?)\s+-\s+([A-Z]{2})\b")
_IMPORTADO = re.compile(r"^(I/)+", re.IGNORECASE)
_PLACA = re.compile(r"Final Placa\s+(\w+)", re.IGNORECASE)


def _texto(no: Tag | None) -> str:
    return " ".join(no.get_text(" ", strip=True).split()) if no is not None else ""


def _cambio(texto: str) -> str | None:
    """Câmbio pelo que o Milan escreve: AUTOMATICO, CAMBIO MANUAL, CVT (só a lista de itens, não os avisos)."""
    alto = normalizar_texto(texto).upper()
    if "AUTOMATIC" in alto:
        return "automático"
    if re.search(r"\bCVT\b", alto):
        return "CVT"
    if re.search(r"\bMANUAL\b", alto):
        return "manual"
    return None


def _marca_e_modelo(titulo: str) -> tuple[str | None, str | None]:
    """D-95: tira o `I/` (repetido em `I/I/TOYOTA`); marca de duas palavras quando conhecida (LAND ROVER)."""
    resto = _IMPORTADO.sub("", titulo.split(" ANO ")[0]).strip()
    palavras = resto.split()
    if not palavras:
        return None, None
    quantas = 2 if len(palavras) > 1 and normalizar_texto(" ".join(palavras[:2])) in MARCAS_CONHECIDAS else 1
    return " ".join(palavras[:quantas]), " ".join(palavras[quantas:]) or None


def _primeira_linha(paragrafo: Tag | None) -> str:
    """O texto do parágrafo até a primeira quebra: "KM: 22, COM AR, COM DIREÇÃO, COM SOM, AUTOMATICO"."""
    if paragrafo is None:
        return ""
    partes = []
    for filho in paragrafo.children:
        if isinstance(filho, Tag) and filho.name == "br":
            break
        partes.append(filho.get_text(" ") if isinstance(filho, Tag) else str(filho))
    return " ".join("".join(partes).split())


class ParserMilan:
    # O catálogo não traz o lance atual: preço ausente não é sinal de quebra (como D-46 do Kuss).
    preco_obrigatorio = False

    def extrair(self, conteudo: bytes, contexto: ContextoParsing) -> ExtracaoPagina:
        tipo = contexto.pagina.get("tipo")
        if tipo == "agenda":
            if not agenda_reconhecida(conteudo):
                raise ValueError("agenda do Milan sem cards de leilão e sem a contagem de leilões")
            return ExtracaoPagina(lotes=[], busca_vazia=True)
        if tipo == "catalogo":
            return self._catalogo(conteudo, contexto)
        raise ValueError(f"página do {LEILOEIRO_ID} sem tipo conhecido: {tipo!r}")

    # --- Catálogo -----------------------------------------------------------------------------

    def _catalogo(self, conteudo: bytes, contexto: ContextoParsing) -> ExtracaoPagina:
        soup = BeautifulSoup(conteudo, "lxml")
        cards = [c for c in soup.select("div.card") if _NUMERO.search(_texto(c.select_one("span.badge")))]
        inicio = _INICIO.search(soup.get_text(" "))
        if not cards:
            if inicio is None:
                raise ValueError("catálogo do Milan sem cards de lote e sem o cabeçalho 'Início:'")
            return ExtracaoPagina(lotes=[], busca_vazia=True)
        pregao = contexto.pagina.get("pregao_em")
        if inicio:
            pregao = data_sem_ano(int(inicio.group(1)), inicio.group(2), int(inicio.group(3)), int(inicio.group(4)),
                                  contexto.coletado_em) or pregao
        patio = self._patio(soup)
        lotes, outros = [], 0
        for card in cards:
            lote = self._lote(card, contexto, pregao, patio)
            if lote is None:
                outros += 1
            else:
                lotes.append(lote)
        if outros:
            log.info("parser  | busca=%s | %d lote(s) que não são veículos (materiais e equipamentos) descartado(s)",
                     contexto.busca_id, outros)
        return ExtracaoPagina(lotes=lotes, busca_vazia=not lotes)

    @staticmethod
    def _patio(soup: BeautifulSoup) -> str | None:
        """D-96: "Cidade - UF" do local do leilão; se o cabeçalho não traz, a do endereço do Milan no rodapé."""
        for fonte in (soup.select_one('[class^="header_leilao_info"]'), soup.find("footer")):
            achado = _CIDADE_UF.search(_texto(fonte))
            if achado:
                return f"{achado.group(1).strip()} - {achado.group(2)}"
        return None

    def _lote(self, card: Tag, contexto: ContextoParsing, pregao, patio) -> Lote | None:
        numero = _NUMERO.search(_texto(card.select_one("span.badge"))).group(1)
        titulo = _texto(card.select_one("h5.card-title"))
        anos = _ANOS.search(titulo)
        if anos is None:
            return None  # materiais, equipamentos, peças
        evento = str(contexto.pagina.get("evento") or "")
        paragrafo = card.select_one("p.card-text")
        descricao = _texto(paragrafo)
        marca, modelo = _marca_e_modelo(titulo)
        km = _KM.search(descricao)
        avisos = list(dict.fromkeys(t for t in (_texto(e) for e in card.select('[style*="color:red"]')) if t))
        observacoes = avisos + _IPVA.findall(descricao)[:1]
        comitente = _COMITENTE.search(descricao)
        if comitente:
            observacoes.append(f"Comitente {comitente.group(1).strip()}")
        return Lote(
            id_canonico=f"{LEILOEIRO_ID}:{evento}-{numero}",
            leiloeiro_id=contexto.leiloeiro_id,
            busca_id=contexto.busca_id,
            link=f"{contexto.base_url}/leilao/{evento}/lote/{numero}",
            coletado_em=contexto.coletado_em,
            numero_lote=numero,
            titulo=titulo,
            marca=marca_canonica(marca) if marca else None,
            modelo=normalizar_texto(modelo) or None,
            ano_fabricacao=int(anos.group(1)),
            ano_modelo=int(anos.group(2)),
            lance_inicial=normalizar_preco(_texto(card.select_one('[id^="card_lote_lanceMinimo"]')) or None),
            quilometragem=int(km.group(1).replace(".", "")) if km else None,
            tipo_leilao=contexto.tipo_leilao,                       # RN-02: herança do leilão escolhido
            situacao=SITUACAO_SUCATA if "(SUCATA)" in titulo.upper() else None,
            evento_id=evento or None,
            pregao_em=pregao,
            observacoes=" · ".join(observacoes) or None,
            patio=patio,
            cambio=_cambio(_primeira_linha(paragrafo)),
        )

    # --- Página do lote (D-97) ------------------------------------------------------------------

    def aplicar_detalhe(self, lote: Lote, conteudo: bytes) -> None:
        soup = BeautifulSoup(conteudo, "lxml")
        bloco = soup.select_one('div[class^="leilao_lote_lanceAtual"]')
        estado = _texto(soup.select_one('div[id^="estado_lote_tag_estadoLote"]'))
        if bloco is None and not estado:
            raise ValueError("página do lote do Milan sem o bloco de lance e sem o estado")
        if bloco is not None:
            atual = normalizar_preco(_texto(bloco.select_one("h4")) or None)
            if atual is not None:
                lote.lance_corrente = atual
        inicial = normalizar_preco(_texto(soup.select_one('p[id^="card_lote_lanceMinimo"]')) or None)
        if inicial is not None:
            lote.lance_inicial = inicial
        lote.retirado = lote.retirado or "RETIRADO" in estado.upper()
        for etiqueta in (_texto(li) for li in soup.select('ul[class^="leilao_lote_tagsVeiculo"] li')):
            placa = _PLACA.search(etiqueta)
            if placa:
                lote.placa_parcial = f"final {placa.group(1)}"
            elif lote.cambio is None:
                lote.cambio = _cambio(etiqueta)
        lote.detalhe_lido = True


registrar_parser(LEILOEIRO_ID, ParserMilan())
