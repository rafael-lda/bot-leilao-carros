"""Funções de apoio importáveis pelos testes (`from apoio import ...`)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


def escrever(caminho: Path, texto: str) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def lote(**campos):
    """Cria um `Lote` com valores padrão plausíveis, sobrescritos por `campos`."""
    from bot_leilao.parsing.modelos import Lote

    padrao = dict(
        id_canonico="vip-leiloes:1",
        leiloeiro_id="vip-leiloes",
        busca_id="vip-leiloes:abc",
        link="https://www.vipleiloes.com.br/evento/anuncio/nissan-versa-1",
        coletado_em=datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc),
        numero_lote="1",
        titulo="Nissan Versa 1.6 SV",
        marca="nissan",
        modelo="versa 1.6 sv",
        ano_fabricacao=2017,
        ano_modelo=2018,
        lance_inicial=Decimal("30000"),
        lance_corrente=Decimal("41900"),
        quilometragem=80000,
        tipo_leilao="financiamento",
        situacao="Aberto para lances",
        retirado=False,
    )
    padrao.update(campos)
    return Lote(**padrao)


def alvo(**campos):
    """Cria um `VeiculoAlvo` (Versa 2018–2021, teto R$ 45.000) com sobrescritas."""
    from bot_leilao.config.veiculos import VeiculoAlvo

    padrao = dict(
        id="nissan-versa-2018-2021",
        marca="Nissan",
        modelo="Versa",
        ano_min=2018,
        ano_max=2021,
        preco_maximo=Decimal("45000"),
        tipos_leilao=("financiamento",),
        quilometragem_maxima=None,
        ativo=True,
    )
    padrao.update(campos)
    return VeiculoAlvo(**padrao)


# ---------------------------------------------------------------------------
# Ponta a ponta: Vip e Telegram falsos sobre um único transporte simulado.
# ---------------------------------------------------------------------------

import json as _json
import re as _re
import sqlite3 as _sqlite3
from datetime import timedelta as _timedelta

import httpx as _httpx

TOKEN_TESTE = "123456789:AAHsegredoDeTesteComTamanhoSuficiente_x"
CHAT_TESTE = 4242
FUSO_SP = timezone(_timedelta(hours=-3))
FIXTURES = Path(__file__).parent / "fixtures"

ALVO_VERSA = """\
veiculos:
  - marca: Nissan
    modelo: Versa
    ano_min: 2018
    ano_max: 2021
    preco_maximo: 45000
    tipos_leilao: [financiamento]
"""

LEILOEIRO_VIP = """\
leiloeiros:
  - nome: Vip Leilões
    base_url: https://www.vipleiloes.com.br
    estrategia_acesso: publico
    nivel_coleta: script
    buscas:
      - descricao: Ampla
        filtros:
          procedencia: 4
          monta: 1
"""


def pagina_vip(titulo="VERSA 1.6 SV - 2017/2018", anuncio="nissan-versa-16-sv-400001", valor_atual="R$ 41.900,00",
               valor_inicial="R$ 30.000,00", lances="3 Lances", situacao="Aberto para lances",
               km="228.227 Km") -> bytes:
    """Página real de 1 resultado do Vip, com o card trocado pelos valores pedidos."""
    html = (FIXTURES / "vip" / "busca_um_resultado.html").read_text(encoding="utf-8")
    trocas = [
        ("SENTRA 20S FLEX - 2012/2013", titulo),
        ("nissan-sentra-20s-flex-310800", anuncio),
        ('<span class="valor-atual">R$ 12.500,00</span>', f'<span class="valor-atual">{valor_atual}</span>'),
        ("Valor inicial: <b>R$ 12.500,00</b>", f"Valor inicial: <b>{valor_inicial}</b>"),
        ("<span>1 Lance</span>", f"<span>{lances}</span>"),
        ("Aberto para lances", situacao),
        ("228.227 Km", km),
    ]
    for antes, depois in trocas:
        assert antes in html, antes
        html = html.replace(antes, depois)
    return html.encode("utf-8")


def pagina_vazia() -> bytes:
    return (FIXTURES / "vip" / "busca_zero_resultados.html").read_bytes()


class CenarioE2E:
    """Raiz de execução completa com Vip e Telegram simulados.

    `vip`: bytes da página de busca, uma exceção httpx (classe) ou um status HTTP.
    `kuss`: `SiteKuss` que responde pelo host do Claudio Kuss (feature 002), ou None.
    `copart`: `SiteCopart` que responde pelo host da Copart (feature 003), ou None.
    `freitas`: `SiteFreitas` que responde pelo host do Freitas (feature 004), ou None.
    `apify`: `ApifySimulado` que responde pelo host da API do Apify (feature 005), ou None. Requisição direta ao
    host do Milan nunca deveria acontecer: fica em `chamadas_milan_locais` e recebe o desafio do Cloudflare.
    `telegram`: status HTTP das respostas do Telegram (200 = ok), ou uma exceção httpx (classe).
    """

    def __init__(self, raiz: Path, relogio, agora, alvos: str = ALVO_VERSA, leiloeiros: str = LEILOEIRO_VIP) -> None:
        from bot_leilao.orquestrador import Dependencias

        self.raiz = raiz
        self.relogio = relogio
        self.agora = agora
        escrever(raiz / "config" / "veiculos-alvo.yaml", alvos)
        escrever(raiz / "config" / "leiloeiros.yaml", leiloeiros)
        self.vip = pagina_vazia()
        self.kuss: "SiteKuss | None" = None
        self.copart: "SiteCopart | None" = None
        self.freitas: "SiteFreitas | None" = None
        self.apify: "ApifySimulado | None" = None
        self.fipe: "SiteFipe | None" = None     # feature 006
        self.mapas: "SiteMapas | None" = None   # feature 006
        self.telegram = 200
        self.mensagens: list[str] = []
        self.chamadas: list[_httpx.Request] = []
        self.ao_enviar = None
        self.transporte = _httpx.MockTransport(self._responder)
        self.deps = Dependencias(
            transporte_leiloeiros=self.transporte, transporte_telegram=self.transporte,
            transporte_apify=self.transporte,  # feature 005
            relogio=relogio.agora, dormir=relogio.dormir, agora=agora, fuso=FUSO_SP,
            environ={"TELEGRAM_BOT_TOKEN": TOKEN_TESTE, "TELEGRAM_CHAT_ID": str(CHAT_TESTE)},
        )
        self.deps.transporte_analise = self.transporte  # feature 006: FIPE e mapas

    def _falhar(self, alvo, request):
        if isinstance(alvo, int):
            return _httpx.Response(alvo, json={"ok": False, "description": f"status {alvo}"})
        raise alvo(f"falha simulada em {request.url}", request=request)

    def _responder(self, request: _httpx.Request) -> _httpx.Response:
        request.read()
        self.chamadas.append(request)
        if request.url.host == "api.telegram.org":
            if self.telegram != 200:
                return self._falhar(self.telegram, request)
            if self.ao_enviar:
                self.ao_enviar()
            self.mensagens.append(_json.loads(request.content)["text"])
            return _httpx.Response(200, json={"ok": True, "result": {"message_id": len(self.mensagens)}})
        if request.url.host == HOST_KUSS:
            assert self.kuss is not None, "o cenário não simula o Claudio Kuss"
            return self.kuss.responder(request)
        if request.url.host == HOST_COPART:
            assert self.copart is not None, "o cenário não simula a Copart"
            return self.copart.responder(request)
        if request.url.host == HOST_FREITAS:
            assert self.freitas is not None, "o cenário não simula o Freitas"
            return self.freitas.responder(request)
        if request.url.host == HOST_APIFY:
            assert self.apify is not None, "o cenário não simula o Apify"
            return self.apify.responder(request)
        if request.url.host == HOST_MILAN:
            return _httpx.Response(403, text="<title>Just a moment...</title><script src=/cdn-cgi/challenge-platform/>")
        if request.url.host in HOSTS_FIPE:
            assert self.fipe is not None, "o cenário não simula a FIPE"
            return self.fipe.responder(request)
        if request.url.host in HOSTS_MAPAS:
            assert self.mapas is not None, "o cenário não simula os mapas"
            return self.mapas.responder(request)
        if not isinstance(self.vip, bytes):
            return self._falhar(self.vip, request)
        if request.url.path == "/":
            return _httpx.Response(200, text="home", headers={"Set-Cookie": "__CBCanal=abc; Path=/"})
        return _httpx.Response(200, content=self.vip, headers={"Content-Type": "text/html; charset=utf-8"})

    def varrer(self, dry_run: bool = False, **opcoes):
        """`opcoes` vão direto ao orquestrador (ex.: `sem_pagos=True`, feature 005)."""
        from bot_leilao.orquestrador import varrer

        self.agora.avancar(minutes=5)
        return varrer(self.raiz, dry_run=dry_run, deps=self.deps, **opcoes)

    def relatorio(self) -> str:
        """Texto do relatório da última varredura real (1OUTPUT/*_varredura*.md)."""
        return sorted((self.raiz / "1OUTPUT").glob("*_varredura*.md"))[-1].read_text(encoding="utf-8")

    def lista(self) -> str:
        caminho = self.raiz / "1OUTPUT" / "lotes-a-monitorar.md"
        return caminho.read_text(encoding="utf-8") if caminho.exists() else ""

    def alertas(self) -> list[str]:
        return [m for m in self.mensagens if "Alerta do sistema" in m]

    @property
    def chamadas_milan_locais(self) -> list:
        """Requisições que saíram direto para o Milan, sem o Apify (feature 005): deve ficar vazia."""
        return [c for c in self.chamadas if c.url.host == HOST_MILAN]

    def com_token_apify(self, token: str = None) -> "CenarioE2E":
        self.deps.environ = {**self.deps.environ, "APIFY_TOKEN": token or TOKEN_APIFY_TESTE}
        return self

    @property
    def chamadas_vip(self) -> list:
        return [c for c in self.chamadas if c.url.host == "www.vipleiloes.com.br"]

    def banco(self) -> _sqlite3.Connection:
        con = _sqlite3.connect(self.raiz / "dados" / "bot-leilao.sqlite3")
        con.row_factory = _sqlite3.Row
        return con

    def execucoes(self) -> list:
        return self.banco().execute("SELECT * FROM execucao ORDER BY iniciado_em").fetchall()

    def notificados(self) -> list[str]:
        return [r[0] for r in self.banco().execute(
            "SELECT id_canonico FROM lote_conhecido WHERE origem = 'notificacao' ORDER BY id_canonico")]


# ---------------------------------------------------------------------------
# Claudio Kuss (feature 002): site simulado a partir das fixtures reais de 2026-10-10.
# ---------------------------------------------------------------------------

from urllib.parse import parse_qs as _parse_qs

FIXTURES_KUSS = FIXTURES / "claudio_kuss"
HOST_KUSS = "www.claudiokussleiloes.com.br"

LEILOEIRO_KUSS = """\
leiloeiros:
  - nome: Claudio Kuss Leilões
    base_url: https://www.claudiokussleiloes.com.br
    estrategia_acesso: publico
    nivel_coleta: script
    buscas:
      - descricao: Financeiras
        filtros:
          categoria: Veículos - Financeiras
"""

LEILOEIROS_VIP_E_KUSS = LEILOEIRO_VIP + LEILOEIRO_KUSS.removeprefix("leiloeiros:\n")

ALVO_FLUENCE = """\
veiculos:
  - marca: Renault
    modelo: Fluence
    ano_min: 2010
    ano_max: 2017
    preco_maximo: 46900
    tipos_leilao: [financiamento]
"""


def json_kuss(nome: str):
    return _json.loads((FIXTURES_KUSS / nome).read_text(encoding="utf-8"))


def bytes_json(dados) -> bytes:
    return _json.dumps(dados, ensure_ascii=False).encode("utf-8")


def agenda_kuss() -> bytes:
    """Agenda real: eventos 897 (13/10/2026 10:00) e 898 (20/10/2026 10:00), ambos "Veículos - Financeiras"."""
    return (FIXTURES_KUSS / "agenda.html").read_bytes()


def agenda_sem_financeiras() -> bytes:
    """Agenda com os mesmos blocos, mas de outra categoria."""
    html = agenda_kuss().decode("utf-8")
    assert "Veículos - Financeiras" in html
    return html.replace("Veículos - Financeiras", "Imóveis - Bancos").encode("utf-8")


def agenda_sem_blocos() -> bytes:
    """Agenda com layout novo: nenhum bloco de evento reconhecível."""
    html = agenda_kuss().decode("utf-8")
    return html.replace("relacao-foto/", "evento/").replace("panel-heading", "cabecalho-evento").encode("utf-8")


def lote_kuss(seq: str = "282622", bem: str = "IMP RENAULT/FLUENCE DYN 20A", ano: str = "13/13", valor: str = "",
              lote: str = "") -> dict:
    """Item de `op=P` no formato real (lotes_897_fluence.json)."""
    return {"seq": seq, "lote": lote, "bem": bem, "comb": "A/G", "ano": ano, "usuario": "", "valor": valor,
            "logo": "images/logo/logo_zrc.png", "foto": f"https://{HOST_KUSS}/fotos/1_2.jpg", "linkVideo": ""}


def detalhe_kuss(**campos) -> dict:
    """Detalhe `op=D` real do Fluence 282622 (sinistrado), com sobrescritas."""
    dados = json_kuss("detalhe_282622_sinistrado.json")
    dados.update(campos)
    return dados


class SiteKuss:
    """Claudio Kuss simulado: agenda, `op=Q`, `op=P` e `op=D`.

    `eventos`: evento -> lista de páginas (cada página, lista de itens de `op=P`).
    `qtde`: sobrescreve a quantidade informada por evento (para testar divergência).
    `detalhes`: seq -> dict, bytes, status HTTP ou classe de exceção httpx; ausente = detalhe sem observações.
    `falha`: status HTTP ou classe de exceção httpx para o site inteiro.
    `lances`: evento -> {seq: usuário} de `op=T` (feature 006); depois do pregão o site mostra "PRESENCIAL", um
    apelido ou vazio, e nunca o valor (verificado em 2026-10-15 no evento 897).
    """

    def __init__(self, agenda: bytes | None = None, eventos: dict | None = None, qtde: dict | None = None,
                 detalhes: dict | None = None, falha=None, lances: dict | None = None) -> None:
        self.lances = lances or {}
        self.agenda = agenda if agenda is not None else agenda_kuss()
        self.eventos = eventos if eventos is not None else {"897": [[lote_kuss()]], "898": []}
        self.qtde = qtde or {}
        self.detalhes = detalhes or {}
        self.falha = falha
        self.chamadas: list[tuple[str, dict]] = []

    def _resposta(self, item) -> _httpx.Response:
        if isinstance(item, (dict, list)):
            item = bytes_json(item)
        return _httpx.Response(200, content=item, headers={"Content-Type": "text/html; charset=UTF-8"})

    def responder(self, request: _httpx.Request) -> _httpx.Response:
        form = {k: v[0] for k, v in _parse_qs(request.content.decode("utf-8"), keep_blank_values=True).items()}
        self.chamadas.append((request.url.path, form))
        if self.falha is not None:
            if isinstance(self.falha, int):
                return _httpx.Response(self.falha, text="erro")
            raise self.falha(f"falha simulada em {request.url}", request=request)
        if request.url.path == "/proximos-leiloes":
            return self._resposta(self.agenda)
        if request.url.path == "/json_edital.php":
            paginas = self.eventos.get(form.get("leilaoID"), [])
            if form.get("op") == "Q":
                total = self.qtde.get(form["leilaoID"], sum(len(p) for p in paginas))
                return self._resposta({"qtde": total, "qtdePag": len(paginas)})
            if form.get("op") == "P":
                indice = int(form["pag"]) - 1
                return self._resposta(paginas[indice] if 0 <= indice < len(paginas) else [])
            if form.get("op") == "T":
                lances = self.lances.get(form.get("leilaoID"), {})
                corpo = {"qtde": len(lances), "atual": "0",
                         **{str(i): {"Q": seq, "U": usuario, "V": ""} for i, (seq, usuario) in enumerate(lances.items())}}
                return self._resposta(corpo)
        if request.url.path == "/json_lance_info_lote.php":
            item = self.detalhes.get(form.get("le_id"), detalhe_kuss(tblInformacoes="&nbsp;"))
            if isinstance(item, int):
                return _httpx.Response(item, text="erro")
            if isinstance(item, type):
                raise item(f"falha simulada em {request.url}", request=request)
            return self._resposta(item)
        return _httpx.Response(404, text="não encontrado")

    def chamadas_op(self, op: str) -> list[dict]:
        return [form for caminho, form in self.chamadas if form.get("op") == op]



# ---------------------------------------------------------------------------
# Copart (feature 003): busca pública em JSON simulada a partir das fixtures reais de 2026-10-11.
# ---------------------------------------------------------------------------

import copy as _copy

FIXTURES_COPART = FIXTURES / "copart"
HOST_COPART = "www.copart.com.br"

LEILOEIRO_COPART = """\
leiloeiros:
  - nome: Copart
    base_url: https://www.copart.com.br
    estrategia_acesso: publico
    nivel_coleta: script
    buscas:
      - descricao: Financiamento
        filtros:
          condicao: FINANCIAMENTO
"""

LEILOEIROS_VIP_E_COPART = LEILOEIRO_VIP + LEILOEIRO_COPART.removeprefix("leiloeiros:\n")

# Página de desafio do Imperva (formato das respostas do Incapsula): o bot nunca a resolve.
DESAFIO_IMPERVA = (b'<html><head><META NAME="robots" CONTENT="noindex,nofollow">'
                   b'<script src="/_Incapsula_Resource?SWJIYLWA=5074a744e2e3d891814e9a2dace20bd4"></script>'
                   b'</head><body>Request unsuccessful. Incapsula incident ID: 0-0</body></html>')


def json_copart(nome: str) -> dict:
    return _json.loads((FIXTURES_COPART / nome).read_text(encoding="utf-8"))


def lotes_copart_reais() -> list[dict]:
    """Lotes reais escolhidos (lotes_selecionados.json): Duster Oroch 1141180 com FIPE, lance e data; Versa 1176233
    aguardando classificação; Creta 1171215; Versa 1173591; um Compre Agora; um "LOCAL DO VENDEDOR"."""
    return json_copart("lotes_selecionados.json")["data"]["results"]["content"]


def lote_copart(ln: int = 1141180, **campos) -> dict:
    """Um lote real da Copart, com sobrescritas. `ln` de um lote real o usa como base; outro número usa o Duster
    Oroch 1141180 como base, trocando o número."""
    reais = {l["ln"]: l for l in lotes_copart_reais()}
    lote = _copy.deepcopy(reais.get(ln, reais[1141180]))
    lote.update(campos, ln=ln, lotNumberStr=str(ln))
    return lote


class SiteCopart:
    """Copart simulada: página da busca (GET) e busca JSON paginada (POST, formulário).

    `lotes`: lotes devolvidos, em ordem; `total`: sobrescreve `totalElements`; `paginas`: lista explícita de
    páginas (cada uma, lista de lotes), para simular repetição entre páginas; `desafio`: status (200 ou 403) da
    página de desafio do Imperva; `corpo`: bytes devolvidos no lugar do JSON; `falha`: status HTTP ou classe de
    exceção httpx para o site inteiro.
    """

    def __init__(self, lotes: list | None = None, total: int | None = None, paginas: list | None = None,
                 desafio: int | None = None, corpo: bytes | None = None, falha=None) -> None:
        self.lotes = lotes if lotes is not None else lotes_copart_reais()
        self.total = total
        self.paginas = paginas
        self.desafio = desafio
        self.corpo = corpo
        self.falha = falha
        self.chamadas: list[tuple[str, str, dict]] = []

    def responder(self, request: _httpx.Request) -> _httpx.Response:
        form = {k: v[0] for k, v in _parse_qs(request.content.decode("utf-8"), keep_blank_values=True).items()}
        self.chamadas.append((request.method, request.url.path, form))
        if self.falha is not None:
            if isinstance(self.falha, int):
                return _httpx.Response(self.falha, text="erro")
            raise self.falha(f"falha simulada em {request.url}", request=request)
        if self.desafio is not None:
            return _httpx.Response(self.desafio, content=DESAFIO_IMPERVA, headers={"Content-Type": "text/html"})
        if request.method == "GET" and request.url.path == "/vehicleFinderSearch":
            return _httpx.Response(200, text="<html><body>busca</body></html>", headers={"Content-Type": "text/html"})
        if request.method == "POST" and request.url.path == "/public/vehicleFinder/search":
            if self.corpo is not None:
                return _httpx.Response(200, content=self.corpo, headers={"Content-Type": "application/json"})
            pagina, tamanho = int(form.get("page", "0")), int(form.get("size", "10"))
            if self.paginas is not None:
                conteudo = self.paginas[pagina] if pagina < len(self.paginas) else []
                total = self.total if self.total is not None else sum(len(p) for p in self.paginas)
            else:
                conteudo = self.lotes[pagina * tamanho:(pagina + 1) * tamanho]
                total = self.total if self.total is not None else len(self.lotes)
            corpo = {"returnCode": 1, "returnCodeDesc": "Success", "data": {
                "query": {"query": ["*"], "page": pagina, "size": tamanho, "start": pagina * tamanho},
                "results": {"totalElements": total, "content": conteudo, "facetFields": []}}}
            return _httpx.Response(200, content=bytes_json(corpo),
                                   headers={"Content-Type": "application/json;charset=UTF-8"})
        return _httpx.Response(404, text="não encontrado")

    def buscas(self) -> list[dict]:
        return [form for metodo, caminho, form in self.chamadas if caminho == "/public/vehicleFinder/search"]


# ---------------------------------------------------------------------------
# Freitas Leiloeiro (feature 004): busca pública em HTML simulada a partir das fixtures reais de 2026-10-13.
# ---------------------------------------------------------------------------

import re as _re

FIXTURES_FREITAS = FIXTURES / "freitas"
HOST_FREITAS = "www.freitasleiloeiro.com.br"
INICIO_CARD = '<div class="col-md-4 col-6 mb-3">'
ERRO_CERTIFICADO = ("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer "
                    "certificate (_ssl.c:1081)")

LEILOEIRO_FREITAS = """\
leiloeiros:
  - nome: Freitas Leiloeiro
    base_url: https://www.freitasleiloeiro.com.br
    estrategia_acesso: publico
    nivel_coleta: script
    buscas:
      - descricao: Inteiros
        filtros:
          categoria: 1
          condicao: inteiros
"""

LEILOEIROS_VIP_E_FREITAS = LEILOEIRO_VIP + LEILOEIRO_FREITAS.removeprefix("leiloeiros:\n")


def cards_freitas_reais() -> dict[str, str]:
    """Cards reais escolhidos (cards_selecionados.html), por "leilão/lote": 8112/1 Duster CVT 23/24 com maior lance;
    8103/124 I/NISSAN SENTRA; 8103/3 HB20; 8112/12 sem etiqueta; 8111/700 em loteamento; 8103/57 M.BENZ;
    8103/9 só com lance inicial."""
    html = (FIXTURES_FREITAS / "cards_selecionados.html").read_text(encoding="utf-8")
    cards = {}
    for parte in html.split(INICIO_CARD)[1:]:
        chave = "/".join(_re.search(r"leilaoId=(\d+)&loteNumero=(\d+)", parte).groups())
        cards[chave] = INICIO_CARD + parte.rsplit("    </div>\n", 1)[0] if parte.rstrip().endswith("</div>") else INICIO_CARD + parte
    return cards


def card_freitas(base: str = "8112/1", lote: str | None = None, desc: str | None = None, valor: str | None = None,
                 etiqueta: str | None = None) -> str:
    """Um card real do Freitas com trocas: `lote` ("8112/50"), `desc` (descrição do veículo), `valor`
    ("R$ 40.000,00"), `etiqueta` ("" tira a FINANCEIRA)."""
    card = cards_freitas_reais()[base]
    if lote is not None:
        leilao, numero = lote.split("/")
        card = _re.sub(r"leilaoId=\d+&loteNumero=\d+", f"leilaoId={leilao}&loteNumero={numero}", card)
        card = _re.sub(r'(cardLote-lote">\s*)\S+', lambda m: m.group(1) + numero.zfill(3), card, count=1)
    if desc is not None:
        card = _re.sub(r'(cardLote-descVeic">\s*<span>)[^<]*', lambda m: m.group(1) + desc, card)
    if valor is not None:
        card = _re.sub(r'(cardLote-vlr">)[^<]*', lambda m: m.group(1) + " " + valor, card)
    if etiqueta is not None:
        card = _re.sub(r'(cardLote-details">\s*<span[^>]*>)[^<]*', lambda m: m.group(1) + etiqueta, card)
    return card


def detalhe_freitas(nome: str = "detalhe_8112_1.html") -> bytes:
    return (FIXTURES_FREITAS / nome).read_bytes()


class SiteFreitas:
    """Freitas simulado: `GET /Leiloes/PesquisarLotes` por `PageNumber`/`TopRows` sobre `cards` (até a mensagem de
    fim real), `GET /Leiloes/LoteDetalhes` por leilão e lote (`detalhes`: "8112-1" → bytes, status ou exceção;
    padrão: o detalhe real do 8112/1). `paginas` força páginas explícitas (lista de listas de cards);
    `bloqueio`: status com a página de bloqueio do firewall; `certificado_invalido`: simula a falha de verificação
    que acontece sem o intermediário; `corpo`: bytes no lugar da página de lotes. `status` e `maiores_lances`
    ("8103-3" → dict da mensagem / bytes) respondem `RetornarLoteStatus` e `RetornarMaiorLanceLote` (feature 006,
    resultado do pregão); lote ausente = 404."""

    def __init__(self, cards: list[str] | None = None, paginas: list | None = None, detalhes: dict | None = None,
                 bloqueio: int | None = None, certificado_invalido: bool = False, corpo: bytes | None = None,
                 status: dict | None = None, maiores_lances: dict | None = None) -> None:
        self.cards = cards if cards is not None else list(cards_freitas_reais().values())
        self.paginas = paginas
        self.detalhes = detalhes or {}
        self.bloqueio = bloqueio
        self.certificado_invalido = certificado_invalido
        self.corpo = corpo
        self.status = status or {}
        self.maiores_lances = maiores_lances or {}
        self.chamadas: list[tuple[str, dict]] = []

    def _html(self, conteudo) -> _httpx.Response:
        if isinstance(conteudo, str):
            conteudo = conteudo.encode("utf-8")
        return _httpx.Response(200, content=conteudo, headers={"Content-Type": "text/html; charset=utf-8"})

    def responder(self, request: _httpx.Request) -> _httpx.Response:
        params = dict(request.url.params)
        self.chamadas.append((request.url.path, params))
        if self.certificado_invalido:
            raise _httpx.ConnectError(ERRO_CERTIFICADO, request=request)
        if self.bloqueio is not None:
            return _httpx.Response(self.bloqueio, text="<html><title>Acesso Bloqueado</title>GoCache</html>")
        if request.url.path == "/Leiloes/PesquisarLotes":
            if self.corpo is not None:
                return self._html(self.corpo)
            pagina, tamanho = int(params.get("PageNumber", "1")), int(params.get("TopRows", "12"))
            if self.paginas is not None:
                fatia = self.paginas[pagina - 1] if pagina <= len(self.paginas) else []
            else:
                fatia = self.cards[(pagina - 1) * tamanho:pagina * tamanho]
            if not fatia:
                return self._html((FIXTURES_FREITAS / "lotes_fim.html").read_bytes())
            return self._html('\n\n    <div class="row">\n' + "".join(fatia) + "    </div>\n")
        if request.url.path == "/Leiloes/LoteDetalhes":
            item = self.detalhes.get(f"{params.get('leilaoId')}-{params.get('loteNumero')}", detalhe_freitas())
            if isinstance(item, int):
                return _httpx.Response(item, text="erro")
            if isinstance(item, type):
                raise item(f"falha simulada em {request.url}", request=request)
            return self._html(item)
        chave = f"{params.get('leilaoId')}-{params.get('loteNumero')}"
        if request.url.path == "/Leiloes/RetornarLoteStatus" and chave in self.status:
            return _httpx.Response(200, json={"success": True, "message": self.status[chave]})
        if request.url.path == "/Leiloes/RetornarMaiorLanceLote" and chave in self.maiores_lances:
            return self._html(self.maiores_lances[chave])
        return _httpx.Response(404, text="não encontrado")

    def buscas(self) -> list[dict]:
        return [p for caminho, p in self.chamadas if caminho == "/Leiloes/PesquisarLotes"]

    def detalhes_pedidos(self) -> list[str]:
        return [f"{p['leilaoId']}-{p['loteNumero']}" for caminho, p in self.chamadas if caminho == "/Leiloes/LoteDetalhes"]


# ---------------------------------------------------------------------------
# Milan e Apify (feature 005): respostas reais do ator de 2026-10-13 (tests/fixtures/milan/).
# ---------------------------------------------------------------------------

FIXTURES_MILAN = FIXTURES / "milan"
HOST_MILAN = "milanleiloes.com.br"
HOST_APIFY = "api.apify.com"
BASE_MILAN = "https://milanleiloes.com.br"
ATOR_PADRAO_TESTE = "neatrat/cloudflare-scraper"
CAMINHO_EXECUCAO = "/v2/acts/neatrat~cloudflare-scraper/run-sync-get-dataset-items"
TOKEN_APIFY_TESTE = "apify_api_SegredoDeTesteComTamanhoSuficiente123"

LEILOEIRO_MILAN = """\
leiloeiros:
  - nome: Milan Leilões
    base_url: https://milanleiloes.com.br
    estrategia_acesso: publico
    nivel_coleta: apify
    buscas:
      - descricao: Recuperados de financiamento
        filtros:
          descricao_contem: recuperados de financiamento
"""

LEILOEIROS_VIP_E_MILAN = LEILOEIRO_VIP + LEILOEIRO_MILAN.removeprefix("leiloeiros:\n")

# Casa com a página do Vip (Versa 2018), mas não com o Versa 2019 do catálogo real do Milan (lote 021).
ALVO_VERSA_2018 = ALVO_VERSA.replace("ano_max: 2021", "ano_max: 2018")

ALVO_CRETA = """\
veiculos:
  - marca: Hyundai
    modelo: Creta
    ano_min: 2017
    ano_max: 2022
    preco_maximo: 55000
    tipos_leilao: [financiamento]
"""


def item_milan(nome: str) -> dict:
    """Item do dataset do ator (dict com url, content, status, success...) de uma fixture do Milan."""
    (item,) = _json.loads((FIXTURES_MILAN / nome).read_text(encoding="utf-8"))
    return item


def html_milan(nome: str) -> bytes:
    """HTML renderizado (campo `content`) de uma fixture do Milan, como o `ClienteApify` entrega ao parser."""
    return item_milan(nome)["content"].encode("utf-8")


def lote_milan_com_lance(numero: str = "046", lance: str = "50.000,00") -> dict:
    """Página real do lote com o valor do lance atual trocado (o 046 real está sem lance: `R$ ---`)."""
    item = item_milan(f"lote_{numero}.json")
    html = item["content"]
    achado = _re.search(r"(<h4><span>R\$ </span>)([^<]+)(</h4>)", html)
    assert achado, "bloco do lance atual não encontrado na fixture"
    item["content"] = html[:achado.start(2)] + lance + html[achado.end(2):]
    return item


def agenda_milan_sem_financiamento() -> dict:
    item = item_milan("agenda.json")
    assert "RECUPERADOS DE FINANCIAMENTO" in item["content"]
    item["content"] = item["content"].replace("RECUPERADOS DE FINANCIAMENTO", "SUCATAS E SALVADOS")
    return item


def paginas_milan_reais() -> dict:
    """URL do site → item do ator, com as cinco páginas reais."""
    return {
        f"{BASE_MILAN}/agenda/veiculos": item_milan("agenda.json"),
        f"{BASE_MILAN}/leilao/15618/catalogo": item_milan("catalogo_15618.json"),
        f"{BASE_MILAN}/leilao/15618/lote/001": item_milan("lote_001.json"),
        f"{BASE_MILAN}/leilao/15618/lote/046": item_milan("lote_046.json"),
        f"{BASE_MILAN}/leilao/15618/lote/209": item_milan("lote_209.json"),
    }


ERROS_APIFY = {
    "token": (401, {"error": {"type": "user-or-token-not-found",
                              "message": "User was not found or authentication token is not valid"}}),
    "cota": (402, {"error": {"type": "not-enough-usage-to-run-paid-actor",
                             "message": "You have exceeded your monthly usage limit."}}),
    "tempo": (408, {"error": {"type": "run-timeout-exceeded", "message": "Actor run did not finish in time."}}),
    "plataforma": (503, {"error": {"type": "service-unavailable", "message": "Service unavailable"}}),
}


def item_desafio(url: str) -> dict:
    """O ator não passou do Cloudflare: devolve a própria página do desafio."""
    return {"url": url, "content": "<html><title>Just a moment...</title><div id=challenge-platform></div></html>",
            "status": 403, "success": False}


class ApifySimulado:
    """API do Apify simulada.

    `POST /v2/acts/<ator>/run-sync-get-dataset-items` devolve `[item]` da URL pedida, procurado em `paginas`
    (URL → dict do item, lista pronta, status HTTP, exceção httpx ou um dos nomes de `ERROS_APIFY`); URL
    ausente = 404 do site. `falha` força uma resposta para todas as execuções ("token", "cota", "tempo",
    "plataforma", "desafio", "vazio"). Cada execução soma `preco` ao uso do ciclo, lido em
    `GET /v2/users/me/limits` (`limites_falham` faz essa consulta responder 500).
    """

    def __init__(self, paginas: dict | None = None, falha: str | None = None, uso: float = 0.39, limite: float = 5.0,
                 preco: float = 0.08, fim_ciclo: str = "2026-10-17T23:59:59.999Z") -> None:
        self.paginas = paginas if paginas is not None else paginas_milan_reais()
        self.falha = falha
        self.uso = uso
        self.limite = limite
        self.preco = preco
        self.fim_ciclo = fim_ciclo
        self.limites_falham = False
        self.chamadas: list[_httpx.Request] = []

    def _erro(self, nome: str) -> _httpx.Response:
        status, corpo = ERROS_APIFY[nome]
        return _httpx.Response(status, json=corpo)

    def responder(self, request: _httpx.Request) -> _httpx.Response:
        self.chamadas.append(request)
        if request.url.path == "/v2/users/me/limits":
            if self.limites_falham:
                return _httpx.Response(500, json={"error": {"type": "internal-error"}})
            return _httpx.Response(200, json={"data": {
                "monthlyUsageCycle": {"startAt": "2026-09-18T00:00:00.000Z", "endAt": self.fim_ciclo},
                "limits": {"maxMonthlyUsageUsd": self.limite}, "current": {"monthlyUsageUsd": self.uso}}})
        if request.method != "POST" or not request.url.path.endswith("/run-sync-get-dataset-items"):
            return _httpx.Response(404, json={"error": {"type": "page-not-found"}})
        url = _json.loads(request.content)["url"]
        if self.falha in ERROS_APIFY:
            return self._erro(self.falha)
        self.uso += self.preco
        if self.falha == "desafio":
            return _httpx.Response(201, json=[item_desafio(url)])
        if self.falha == "vazio":
            return _httpx.Response(201, json=[])
        item = self.paginas.get(url)
        if item is None:
            item = {"url": url, "content": "<html>404</html>", "status": 404, "success": False}
        if isinstance(item, str):
            return self._erro(item)
        if isinstance(item, int):
            return _httpx.Response(item, json={"error": {"type": "simulado"}})
        if isinstance(item, type):
            raise item(f"falha simulada em {request.url}", request=request)
        return _httpx.Response(201, json=item if isinstance(item, list) else [item])

    def execucoes(self) -> list[_httpx.Request]:
        return [c for c in self.chamadas if c.url.path.endswith("/run-sync-get-dataset-items")]

    def urls_pedidas(self) -> list[str]:
        return [_json.loads(c.content)["url"] for c in self.execucoes()]


# ---------------------------------------------------------------------------
# Análise de lotes (feature 006): lista do Rafael, FIPE e mapas simulados a partir das respostas reais de 2026-10-15.
# ---------------------------------------------------------------------------

FIXTURES_ANALISE = FIXTURES / "analise"
HOST_PARALLELUM = "parallelum.com.br"
HOST_FIPE_OFICIAL = "veiculos.fipe.org.br"
HOSTS_FIPE = (HOST_PARALLELUM, HOST_FIPE_OFICIAL)
HOST_NOMINATIM = "nominatim.openstreetmap.org"
HOST_OSRM = "router.project-osrm.org"
HOSTS_MAPAS = (HOST_NOMINATIM, HOST_OSRM)


def lista_de_teste(raiz: Path) -> Path:
    """Copia a lista de 2026-10-15 (14 lotes) para `raiz/1OUTPUT/lotes-a-monitorar.md`."""
    destino = raiz / "1OUTPUT" / "lotes-a-monitorar.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes((FIXTURES_ANALISE / "lotes-a-monitorar.md").read_bytes())
    return destino


def _fipe_json(nome: str):
    return _json.loads((FIXTURES_ANALISE / "fipe" / nome).read_text(encoding="utf-8"))


class SiteFipe:
    """parallelum v2 e site oficial da FIPE simulados com as respostas reais (Nissan 43; Versa SL 7628 Aut., 7629 Mec.).

    `parallelum` / `oficial`: "ok", "fora" (503) ou "limite" (429, só a parallelum). `referencia`: mês de referência
    devolvido pelas duas (padrão: o das fixtures, outubro/2026, código 338). `oficial_bloqueios`: quantos pedidos ao
    site oficial levam 429 antes de ele voltar a responder (emenda D-123). `ConsultarModelosAtravesDoAno` responde com
    a lista real da Nissan 2019 flex; outros anos e combustíveis, lista vazia.
    """

    CODIGOS = {"023140-1": "7628", "023138-0": "7629"}

    def __init__(self, parallelum: str = "ok", oficial: str = "ok", referencia: tuple[str, str] | None = None,
                 oficial_bloqueios: int = 0) -> None:
        self.parallelum = parallelum
        self.oficial = oficial
        self.oficial_bloqueios = oficial_bloqueios
        self.referencia = referencia or ("338", "outubro/2026")
        self.chamadas: list[_httpx.Request] = []

    def _preco(self, modelo: str, ano: str) -> dict | None:
        caminho = FIXTURES_ANALISE / "fipe" / f"parallelum_price_{modelo}_{ano}.json"
        if not caminho.exists():
            return None
        preco = _json.loads(caminho.read_text(encoding="utf-8"))
        return {**preco, "referenceMonth": self.referencia[1].replace("/", " de ")}

    def _anos(self, modelo: str) -> list:
        caminho = FIXTURES_ANALISE / "fipe" / f"parallelum_years_{modelo}.json"
        return _json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else []

    def responder(self, request: _httpx.Request) -> _httpx.Response:
        self.chamadas.append(request)
        if request.url.host == HOST_PARALLELUM:
            return self._parallelum(request)
        return self._oficial(request)

    def _parallelum(self, request) -> _httpx.Response:
        if self.parallelum == "fora":
            return _httpx.Response(503, text="Service Unavailable")
        if self.parallelum == "limite":
            return _httpx.Response(429, json={"error": "rate limit"}, headers={"x-ratelimit-remaining": "0"})
        partes = request.url.path.removeprefix("/fipe/api/v2/").strip("/").split("/")
        nao = _httpx.Response(404, json={"error": "veículo não encontrado para a referência informada"})
        if partes == ["references"]:
            return _httpx.Response(200, json=[{"code": self.referencia[0], "month": self.referencia[1]}])
        if partes == ["cars", "brands"]:
            return _httpx.Response(200, json=_fipe_json("parallelum_brands.json"))
        if partes[:3] == ["cars", "brands", "43"]:
            if len(partes) == 4:
                return _httpx.Response(200, json=_fipe_json("parallelum_models_43.json"))
            if len(partes) == 6:
                return _httpx.Response(200, json=self._anos(partes[4]))
            if len(partes) == 7:
                preco = self._preco(partes[4], partes[6])
                return _httpx.Response(200, json=preco) if preco else nao
        if partes[:1] == ["cars"] and len(partes) >= 3 and partes[1] in self.CODIGOS:
            modelo = self.CODIGOS[partes[1]]
            if len(partes) == 3:
                return _httpx.Response(200, json=self._anos(modelo))
            preco = self._preco(modelo, partes[3])
            return _httpx.Response(200, json=preco) if preco else nao
        return nao

    def _oficial(self, request) -> _httpx.Response:
        if self.oficial == "fora":
            return _httpx.Response(503, text="Service Unavailable")
        if self.oficial_bloqueios > 0:
            self.oficial_bloqueios -= 1
            return _httpx.Response(429, text="Too Many Requests")
        dados = dict(_parse_qs(request.content.decode("utf-8"), keep_blank_values=True))
        campo = lambda nome: (dados.get(nome) or [""])[0]
        nada = _httpx.Response(200, json={"codigo": "0", "erro": "nadaencontrado"})
        acao = request.url.path.rsplit("/", 1)[-1]
        if acao == "ConsultarTabelaDeReferencia":
            return _httpx.Response(200, json=[{"Codigo": int(self.referencia[0]), "Mes": self.referencia[1] + " "}])
        if acao == "ConsultarMarcas":
            return _httpx.Response(200, json=_fipe_json("oficial_marcas.json"))
        if acao == "ConsultarModelos":
            return _httpx.Response(200, json=_fipe_json("oficial_modelos_43.json")) if campo("codigoMarca") == "43" \
                else _httpx.Response(200, json={"Modelos": [], "Anos": []})
        if acao == "ConsultarModelosAtravesDoAno":
            if (campo("codigoMarca"), campo("ano")) == ("43", "2019-5"):
                return _httpx.Response(200, json=_fipe_json("oficial_modelos_43_2019-5.json"))
            return _httpx.Response(200, json=[])
        if acao == "ConsultarAnoModelo":
            anos = self._anos(campo("codigoModelo"))
            return _httpx.Response(200, json=[{"Label": a["name"], "Value": a["code"]} for a in anos])
        if acao == "ConsultarValorComTodosParametros":
            modelo = self.CODIGOS.get(campo("modeloCodigoExterno")) or campo("codigoModelo")
            preco = self._preco(modelo, f"{campo('anoModelo')}-{campo('codigoTipoCombustivel')}")
            if preco is None:
                return nada
            return _httpx.Response(200, json={"Valor": preco["price"], "Marca": preco["brand"], "Modelo": preco["model"],
                                              "AnoModelo": preco["modelYear"], "Combustivel": preco["fuel"],
                                              "CodigoFipe": preco["codeFipe"], "MesReferencia": self.referencia[1]
                                              .replace("/", " de ") + " ", "TipoVeiculo": 1, "SiglaCombustivel": "F"})
        return _httpx.Response(404, text="não encontrado")

    def hosts_chamados(self) -> list[str]:
        return [c.url.host for c in self.chamadas]

    def pedidos(self, host: str) -> int:
        return sum(1 for c in self.chamadas if c.url.host == host)


class SiteMapas:
    """Nominatim (Londrina e Curitiba reais; outras cidades: lista vazia) e OSRM (rota real de 385 km).

    `nominatim` / `osrm`: "ok" ou "fora" (500).
    """

    def __init__(self, nominatim: str = "ok", osrm: str = "ok") -> None:
        self.nominatim = nominatim
        self.osrm = osrm
        self.chamadas: list[_httpx.Request] = []

    def responder(self, request: _httpx.Request) -> _httpx.Response:
        self.chamadas.append(request)
        if request.url.host == HOST_NOMINATIM:
            if self.nominatim == "fora":
                return _httpx.Response(500, text="erro")
            cidade = request.url.params.get("q", "").split(",")[0].strip().lower()
            arquivo = FIXTURES_ANALISE / "mapas" / f"nominatim_{cidade}.json"
            return _httpx.Response(200, json=_json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else [])
        if self.osrm == "fora":
            return _httpx.Response(500, json={"code": "Error"})
        return _httpx.Response(200, json=_json.loads((FIXTURES_ANALISE / "mapas" / "osrm_londrina_curitiba.json")
                                                     .read_text(encoding="utf-8")))

    def consultas_nominatim(self) -> list[str]:
        return [c.url.params.get("q", "") for c in self.chamadas if c.url.host == HOST_NOMINATIM]
