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
