"""Leitura de um lote pelo acesso do bot (feature 006; roadmap D-110; RF-07).

Mesmo cliente, mesmo nível e mesma conduta da varredura (5 s por host; Apify no Milan). Por leiloeiro:
Vip, página do anúncio; Claudio Kuss, detalhe JSON (evento e sequência do link `/lance/<evento>/0/<seq>`);
Copart, busca JSON pelo número do lote (a página de detalhe é barrada pelo Imperva); Freitas e Milan, detalhe pelo
link. Devolve os campos que o parser do leiloeiro já sabe ler e o texto limpo, para o agente julgar.

Emenda de 2026-10-15 (RF-14, D-120): quando o site mostra que o pregão acabou, `campos["resultado"]` diz o que ele
divulga, por leiloeiro (ver `.claude/skills/analisar-lotes/references/resultados-por-leiloeiro.md`). Apelido de quem
deu lance nunca sai daqui.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from decimal import Decimal
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
from bot_leilao.coleta.claudio_kuss import BASE as BASE_KUSS
from bot_leilao.coleta.copart import BASE as BASE_COPART
from bot_leilao.coleta.copart import CABECALHOS_AJAX as CABECALHOS_COPART
from bot_leilao.coleta.freitas import BASE as BASE_FREITAS
from bot_leilao.coleta.modelos import Requisicao
from bot_leilao.parsing import nucleo
from bot_leilao.parsing.modelos import ContextoParsing, Lote
from bot_leilao.parsing.normalizadores import normalizar_preco

LIMITE_TEXTO = 8000
CUSTO_PAGINA_APIFY_USD = 0.08   # medido na feature 005 (interfaces/apify.md)
_LINK_KUSS = re.compile(r"/lance/(\d+)/\d+/(\d+)")
_CAMBIO_VIP = re.compile(r"Câmbio\s+(Automático|Automatico|Automatizado|Manual|CVT)", re.IGNORECASE)
_KM_VIP = re.compile(r"\bKM\s+([\d.]+)")
_LINK_FREITAS = re.compile(r"leilaoId=(\d+)&loteNumero=(\d+)")
_MAIOR_LANCE_FREITAS = re.compile(r'id="hdMaiorLance"\s+value="([\d.,]+)"')
# Situações que ainda recebem lance; qualquer outra, mostrada pelo site, é o fim do pregão.
_EM_ABERTO = ("RECEBENDO", "ABERTO", "BREVE", "LOTEAMENTO", "AGUARDANDO", "ANDAMENTO", "PREGÃO")
FORA_DA_BUSCA_COPART = ("saiu da busca pública da Copart (pregão encerrado: vendido, condicional ou retirado); "
                        "resultado não divulgado sem login")
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


def _em_aberto(situacao: str) -> bool:
    return any(p in situacao.upper() for p in _EM_ABERTO)


def _reais(valor: Decimal) -> str:
    return "R$ " + f"{int(valor):,}".replace(",", ".")


def _final(situacao: str, lance: Decimal | None, rotulo: str, sem_valor: str = "valor não divulgado pelo site") -> str:
    return f"{situacao.strip().lower()}; " + (f"{rotulo} {_reais(lance)}" if lance else sem_valor)


def _vip(conteudo: bytes, campos: dict) -> None:
    """Vip: situação (`div.detan-situation`) e valor (`div.offer-value h2`). Depois do pregão o anúncio continua no
    ar com a situação final (ex.: "Condicional negada") e o último lance."""
    soup = BeautifulSoup(conteudo, "lxml")
    caixa, valor = soup.select_one("div.detan-situation"), soup.select_one("div.offer-value h2")
    situacao = caixa.get_text(" ", strip=True) if caixa else ""
    lance = normalizar_preco(valor.get_text(" ", strip=True) if valor else None) or None
    classe = " ".join(caixa.get("class", [])) if caixa else ""
    if situacao and not _em_aberto(situacao + " " + classe):
        campos["resultado"] = _final(situacao, lance, "último lance")
    elif lance:
        campos["lance_corrente"] = lance


def _freitas(cliente, nivel: str, link: str, campos: dict) -> None:
    """Freitas: status (`RetornarLoteStatus`, JSON) e maior lance (`RetornarMaiorLanceLote`), as mesmas chamadas
    públicas que a página faz a cada 5 s. Falha nelas não derruba a leitura do lote."""
    achado = _LINK_FREITAS.search(link)
    if achado is None:
        return
    consulta = f"leilaoId={achado.group(1)}&loteNumero={achado.group(2)}"
    cabecalhos = {"X-Requested-With": "XMLHttpRequest", "Referer": link}
    status = cliente.requisitar(Requisicao("GET", f"{BASE_FREITAS}/Leiloes/RetornarLoteStatus?{consulta}",
                                           cabecalhos=cabecalhos, nivel=nivel))
    try:
        mensagem = json.loads(status.conteudo)["message"] if status.ok else {}
    except (ValueError, KeyError, TypeError):
        mensagem = {}
    situacao = str(mensagem.get("nome") or "") if isinstance(mensagem, dict) else ""
    maior = cliente.requisitar(Requisicao(
        "GET", f"{BASE_FREITAS}/Leiloes/RetornarMaiorLanceLote?{consulta}&modeloRecebePropostas=False",
        cabecalhos=cabecalhos, nivel=nivel))
    valor = _MAIOR_LANCE_FREITAS.search((maior.conteudo or b"").decode("utf-8", "replace")) if maior.ok else None
    lance = Decimal(valor.group(1).replace(".", "").replace(",", ".")) if valor else None
    lance = lance or None
    if situacao and mensagem.get("recebeLance") is not True and not _em_aberto(situacao):
        campos["resultado"] = _final(situacao, lance, "maior lance", "sem lance" if valor else "valor não lido")
    elif lance:
        campos["lance_corrente"] = lance


def _milan(conteudo: bytes, campos: dict) -> None:
    """Milan: etiqueta de estado do lote. Depois do pregão vira VENDIDO, CONDICIONAL etc. e o lance some ("R$ ---")."""
    estado = BeautifulSoup(conteudo, "lxml").select_one('div[id^="estado_lote_tag_estadoLote"]')
    situacao = estado.get_text(" ", strip=True) if estado else ""
    if situacao and not _em_aberto(situacao):
        campos["resultado"] = _final(situacao, campos.get("lance_corrente"), "lance")


def _resultado_kuss(cliente, nivel: str, evento: str, seq: str) -> str | None:
    """Último lance do lote no evento (`op=T`). Depois do pregão o Kuss mostra só quem deu o último lance
    ("PRESENCIAL" ou o apelido de quem deu online) e nunca o valor (evento 897, 2026-10-15). O apelido não sai daqui."""
    resultado = cliente.requisitar(Requisicao(
        "POST", f"{BASE_KUSS}/json_edital.php", dados={"op": "T", "leilaoID": evento, "loteado": "S"}, nivel=nivel,
        cabecalhos={"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE_KUSS}/relacao-foto/{evento}"}))
    if not resultado.ok:
        return None
    try:
        dados = json.loads(resultado.conteudo)
    except ValueError:
        return None
    item = next((v for v in dados.values() if isinstance(v, dict) and str(v.get("Q")) == seq), None)
    if item is None:
        return None
    usuario, valor = str(item.get("U") or "").strip(), str(item.get("V") or "").strip()
    if not usuario:
        return "sem lance"
    quem = "presencial" if usuario.upper() == "PRESENCIAL" else "online"
    return f"último lance {quem}; " + (f"R$ {valor}" if valor else "valor não divulgado pelo site")


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
        conteudo = buscar(Requisicao("GET", link))
        texto = _texto_html(conteudo)
        campos = {"cambio": _cambio(texto)}
        km = _KM_VIP.search(texto)
        if km:
            campos["quilometragem"] = int(km.group(1).replace(".", ""))
        campos = {k: v for k, v in campos.items() if v is not None}
        _vip(conteudo, campos)
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
            return {"leiloeiro": leiloeiro, "nivel": nivel, "pago": nivel != "script",
                    "custo_estimado_usd": CUSTO_PAGINA_APIFY_USD if nivel == "apify" else 0.0,
                    "campos": {"resultado": FORA_DA_BUSCA_COPART}, "texto": ""}
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
        if leiloeiro == "claudio-kuss-leiloes":
            resultado = _resultado_kuss(cliente, nivel, lote.evento_id, lote.id_canonico.split(":", 1)[1])
            if resultado:
                campos["resultado"] = resultado
        elif leiloeiro == "freitas-leiloeiro":
            _freitas(cliente, nivel, link, campos)
        elif leiloeiro == "milan-leiloes":
            _milan(conteudo, campos)
        try:
            texto = _texto_json(json.loads(conteudo))
        except ValueError:
            texto = _texto_html(conteudo)
    return {"leiloeiro": leiloeiro, "nivel": nivel, "pago": nivel != "script",
            "custo_estimado_usd": CUSTO_PAGINA_APIFY_USD if nivel == "apify" else 0.0,
            "campos": campos, "texto": texto}
