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
        self.telegram = 200
        self.mensagens: list[str] = []
        self.chamadas: list[_httpx.Request] = []
        self.ao_enviar = None
        self.transporte = _httpx.MockTransport(self._responder)
        self.deps = Dependencias(
            transporte_leiloeiros=self.transporte, transporte_telegram=self.transporte,
            relogio=relogio.agora, dormir=relogio.dormir, agora=agora, fuso=FUSO_SP,
            environ={"TELEGRAM_BOT_TOKEN": TOKEN_TESTE, "TELEGRAM_CHAT_ID": str(CHAT_TESTE)},
        )

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
        if not isinstance(self.vip, bytes):
            return self._falhar(self.vip, request)
        if request.url.path == "/":
            return _httpx.Response(200, text="home", headers={"Set-Cookie": "__CBCanal=abc; Path=/"})
        return _httpx.Response(200, content=self.vip, headers={"Content-Type": "text/html; charset=utf-8"})

    def varrer(self, dry_run: bool = False):
        from bot_leilao.orquestrador import varrer

        self.agora.avancar(minutes=5)
        return varrer(self.raiz, dry_run=dry_run, deps=self.deps)

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
    """

    def __init__(self, agenda: bytes | None = None, eventos: dict | None = None, qtde: dict | None = None,
                 detalhes: dict | None = None, falha=None) -> None:
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
