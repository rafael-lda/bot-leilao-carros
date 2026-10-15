"""Leitura de um lote pelo acesso do bot (feature 006; roadmap D-110; RF-07).

Mesmo cliente, mesmo nível e mesma conduta da varredura (5 s por host; Apify no Milan). Por leiloeiro:
Vip, página do anúncio; Claudio Kuss, detalhe JSON (evento e sequência do link `/lance/<evento>/0/<seq>`);
Copart, busca JSON pelo número do lote (a página de detalhe é barrada pelo Imperva); Freitas e Milan, detalhe pelo
link. Devolve os campos que o parser do leiloeiro já sabe ler e o texto limpo, para o agente julgar.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone

from bs4 import BeautifulSoup

import bot_leilao.coleta.claudio_kuss  # noqa: F401 — registram adaptadores e parsers
import bot_leilao.coleta.copart  # noqa: F401
import bot_leilao.coleta.freitas  # noqa: F401
import bot_leilao.coleta.milan  # noqa: F401
import bot_leilao.coleta.vip  # noqa: F401
import bot_leilao.parsing.claudio_kuss  # noqa: F401
import bot_leilao.parsing.copart  # noqa: F401
import bot_leilao.parsing.freitas  # noqa: F401
import bot_leilao.parsing.milan  # noqa: F401
import bot_leilao.parsing.vip  # noqa: F401
from bot_leilao.coleta import registro
from bot_leilao.coleta.copart import BASE as BASE_COPART
from bot_leilao.coleta.copart import CABECALHOS_AJAX as CABECALHOS_COPART
from bot_leilao.coleta.modelos import Requisicao
from bot_leilao.parsing import nucleo
from bot_leilao.parsing.modelos import ContextoParsing, Lote

LIMITE_TEXTO = 8000
CUSTO_PAGINA_APIFY_USD = 0.08   # medido na feature 005 (interfaces/apify.md)
_LINK_KUSS = re.compile(r"/lance/(\d+)/\d+/(\d+)")
_CAMBIO_VIP = re.compile(r"Câmbio\s+(Automático|Automatico|Automatizado|Manual|CVT)", re.IGNORECASE)
_KM_VIP = re.compile(r"\bKM\s+([\d.]+)")
CAMPOS = ("lance_corrente", "lance_inicial", "observacoes", "patio", "cambio", "placa_parcial", "retirado",
          "despesas_adm", "quilometragem", "situacao", "pregao_em", "fipe")


class ErroPagina(Exception):
    """Leiloeiro desconhecido ou falha de acesso: a skill deixa o lote "a confirmar"."""


def _texto_html(conteudo: bytes) -> str:
    soup = BeautifulSoup(conteudo, "lxml")
    for bloco in soup(["script", "style", "noscript", "svg"]):
        bloco.decompose()
    return " ".join(soup.get_text(" ").split())[:LIMITE_TEXTO]


def _texto_json(dados) -> str:
    """Campos de texto de um JSON (detalhe do Kuss, item da Copart), um por linha."""
    if isinstance(dados, dict):
        partes = [f"{k}: {v}" for k, v in dados.items() if isinstance(v, (str, int, float)) and str(v).strip()]
        return "\n".join(partes)[:LIMITE_TEXTO]
    return json.dumps(dados, ensure_ascii=False)[:LIMITE_TEXTO]


def _campos(lote: Lote) -> dict:
    return {c: getattr(lote, c) for c in CAMPOS if getattr(lote, c) not in (None, "", False)}


def _cambio(texto: str) -> str | None:
    achado = _CAMBIO_VIP.search(texto)
    if achado is None:
        return None
    valor = achado.group(1).lower()
    return "CVT" if valor == "cvt" else ("manual" if valor == "manual" else "automático")


def ler_pagina(id_canonico: str, link: str, cliente, niveis: Mapping[str, str] | None = None) -> dict:
    leiloeiro = id_canonico.split(":", 1)[0]
    if leiloeiro not in registro.adaptadores():
        raise ErroPagina(f"leiloeiro desconhecido: {leiloeiro}")
    nivel = (niveis or {}).get(leiloeiro, "script")
    lote = Lote(id_canonico=id_canonico, leiloeiro_id=leiloeiro, busca_id="analise", link=link,
                coletado_em=datetime.now(timezone.utc))

    def buscar(requisicao: Requisicao) -> bytes:
        resultado = cliente.requisitar(replace(requisicao, nivel=nivel))
        if not resultado.ok:
            raise ErroPagina(f"falha de acesso ao {leiloeiro}: {resultado.motivo or resultado.veredito.value}")
        return resultado.conteudo or b""

    if leiloeiro == "vip-leiloes":
        texto = _texto_html(buscar(Requisicao("GET", link)))
        campos = {"cambio": _cambio(texto)}
        km = _KM_VIP.search(texto)
        if km:
            campos["quilometragem"] = int(km.group(1).replace(".", ""))
        campos = {k: v for k, v in campos.items() if v is not None}
    elif leiloeiro == "copart":
        numero = id_canonico.split(":", 1)[1]
        conteudo = buscar(Requisicao("POST", f"{BASE_COPART}/public/vehicleFinder/search",
                                     dados={"query": numero, "page": "0", "size": "10", "start": "0"},
                                     cabecalhos=dict(CABECALHOS_COPART)))
        contexto = ContextoParsing(leiloeiro_id=leiloeiro, busca_id="analise", base_url=BASE_COPART,
                                   coletado_em=lote.coletado_em)
        achados = [l for l in nucleo.obter_parser(leiloeiro).extrair(conteudo, contexto).lotes
                   if l.id_canonico == id_canonico]
        if not achados:
            raise ErroPagina(f"o lote {numero} não apareceu na busca da Copart (vendido ou retirado?)")
        itens = json.loads(conteudo)["data"]["results"]["content"]
        item = next((i for i in itens if str(i.get("ln")) == numero), {})
        campos, texto = _campos(achados[0]), _texto_json(item)
    else:
        if leiloeiro == "claudio-kuss-leiloes":
            achado = _LINK_KUSS.search(link)
            if achado is None:
                raise ErroPagina(f"link do Claudio Kuss sem evento e sequência: {link}")
            lote.evento_id = achado.group(1)
            lote.id_canonico = f"{leiloeiro}:{achado.group(2)}"
        requisicao = registro.obter_adaptador(leiloeiro).requisicao_detalhe(lote)
        if requisicao is None:
            raise ErroPagina(f"o {leiloeiro} não tem página de detalhe para {id_canonico}")
        conteudo = buscar(requisicao)
        nucleo.obter_parser(leiloeiro).aplicar_detalhe(lote, conteudo)
        campos = _campos(lote)
        try:
            texto = _texto_json(json.loads(conteudo))
        except ValueError:
            texto = _texto_html(conteudo)
    return {"leiloeiro": leiloeiro, "nivel": nivel, "pago": nivel != "script",
            "custo_estimado_usd": CUSTO_PAGINA_APIFY_USD if nivel == "apify" else 0.0,
            "campos": campos, "texto": texto}
