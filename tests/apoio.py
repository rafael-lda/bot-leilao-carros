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
