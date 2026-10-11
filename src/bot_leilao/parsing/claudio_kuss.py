"""Parser do Claudio Kuss Leilões (feature 002; interfaces/claudio-kuss.md; roadmap D-38, D-41 a D-46, D-50, D-52).

Lê as três páginas da busca, distinguidas pela anotação `tipo` (agenda, quantidade, lotes),
e o detalhe do lote, usado só no enriquecimento dos lotes novos.
"""

from __future__ import annotations

import html
import json
import logging
import re

from bot_leilao.coleta.claudio_kuss import ler_agenda
from bot_leilao.parsing.marcas import marca_canonica
from bot_leilao.parsing.modelos import ContextoParsing, ExtracaoPagina, Lote
from bot_leilao.parsing.normalizadores import anos_dois_digitos, normalizar_preco
from bot_leilao.parsing.nucleo import registrar_parser
from bot_leilao.texto import normalizar_texto

log = logging.getLogger(__name__)

LEILOEIRO_ID = "claudio-kuss-leiloes"
_IMPORTADO = re.compile(r"^IMP\s+", re.IGNORECASE)
_SUCATA = re.compile(r"^SUCATA\b", re.IGNORECASE)
SITUACAO_SUCATA = "sucata"


def _limpo(valor: object) -> str | None:
    """Decodifica entidades HTML (`&nbsp;`, `&amp;`) e colapsa espaços; vazio vira None."""
    texto = " ".join(html.unescape(str(valor or "")).replace("\xa0", " ").split())
    return texto or None


class ParserClaudioKuss:
    # D-46: antes do pregão quase nenhum lote tem valor; preço ausente não é sinal de quebra.
    preco_obrigatorio = False

    def extrair(self, conteudo: bytes, contexto: ContextoParsing) -> ExtracaoPagina:
        tipo = contexto.pagina.get("tipo")
        if tipo == "agenda":
            # D-41: a agenda nunca traz lotes. Reconhecida = vazia; sem nenhum bloco = layout novo (quebra).
            return ExtracaoPagina(lotes=[], busca_vazia=bool(ler_agenda(conteudo)))
        if tipo == "quantidade":
            dados = json.loads(conteudo)
            qtde = int(dados["qtde"])
            return ExtracaoPagina(lotes=[], busca_vazia=qtde == 0, total_informado=qtde)
        if tipo == "lotes":
            return self._lotes(conteudo, contexto)
        raise ValueError(f"página do {LEILOEIRO_ID} sem tipo conhecido: {tipo!r}")

    def _lotes(self, conteudo: bytes, contexto: ContextoParsing) -> ExtracaoPagina:
        itens = json.loads(conteudo)
        if not isinstance(itens, list):
            raise ValueError(f"esperava uma lista de lotes, veio {type(itens).__name__}")
        lotes, sucatas = [], 0
        for item in itens:
            bem = str(item["bem"]).strip()
            if _SUCATA.match(bem):  # D-43; o JSON de 2026-10-10 não traz o prefixo (só a lista HTML), ver aplicar_detalhe
                sucatas += 1
                continue
            lotes.append(self._lote(item, bem, contexto))
        if sucatas:
            log.info("parser  | busca=%s | %d lote(s) de sucata ignorado(s)", contexto.busca_id, sucatas)
        return ExtracaoPagina(lotes=lotes, busca_vazia=not lotes)

    def _lote(self, item: dict, bem: str, contexto: ContextoParsing) -> Lote:
        seq = str(item["seq"]).strip()
        if not seq:
            raise ValueError("lote sem seq")
        evento = contexto.pagina["evento"]
        marca_bruta, _, modelo = bem.partition("/")
        tem_marca = bool(modelo)
        fabricacao, ano_modelo = anos_dois_digitos(item.get("ano"), contexto.coletado_em.year)
        return Lote(
            id_canonico=f"{LEILOEIRO_ID}:{seq}",                         # D-38: seq é global no site
            leiloeiro_id=contexto.leiloeiro_id,
            busca_id=contexto.busca_id,
            link=f"{contexto.base_url}/lance/{evento}/0/{seq}",
            coletado_em=contexto.coletado_em,
            numero_lote=(str(item.get("lote") or "").strip() or None),  # vazio até o loteamento
            titulo=bem,
            marca=marca_canonica(_IMPORTADO.sub("", marca_bruta.strip())) if tem_marca else None,
            modelo=(normalizar_texto(modelo) or None) if tem_marca else None,
            ano_fabricacao=fabricacao,
            ano_modelo=ano_modelo,
            lance_corrente=normalizar_preco(item.get("valor") or None),
            tipo_leilao=contexto.tipo_leilao,
            retirado=bem.upper() == "RETIRADO",
            evento_id=evento,
            pregao_em=contexto.pagina.get("pregao_em"),
            patio=contexto.pagina.get("patio"),
        )

    def aplicar_detalhe(self, lote: Lote, conteudo: bytes) -> None:
        """Preenche o lote com o detalhe `op=D` (D-50). O texto padrão `tblTxtInfo` nunca entra (D-52)."""
        dados = json.loads(conteudo)
        if not isinstance(dados, dict):
            raise ValueError(f"esperava o detalhe do lote, veio {type(dados).__name__}")
        lote.observacoes = _limpo(dados.get("tblInformacoes"))
        lote.despesas_adm = normalizar_preco(_limpo(dados.get("tblDespAdm")))
        lote.placa_parcial = _limpo(dados.get("tblPlaca"))
        lote.local_documento = _limpo(dados.get("tblTransf"))
        lote.retirado = lote.retirado or str(dados.get("retirado", "")).strip().upper() == "S"
        # D-43 revisto no coding: no JSON a sucata só aparece no detalhe ("SUCATA SEM DOCUMENTOS - BAIXADO
        # JUNTO AO DETRAN...", e `tblTransf` = "SUCATA"). Documento baixado: o carro não volta a circular.
        if _SUCATA.match(lote.observacoes or "") or normalizar_texto(lote.local_documento) == "sucata":
            lote.situacao = SITUACAO_SUCATA
        lote.detalhe_lido = True


registrar_parser(LEILOEIRO_ID, ParserClaudioKuss())
