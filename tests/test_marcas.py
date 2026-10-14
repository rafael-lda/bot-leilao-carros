"""Tabela comum de sinônimos de marca (parser-lotes v1.1 RF-12, EC-14; roadmap D-28)."""

import logging

import pytest

from bot_leilao.parsing.marcas import MARCAS_CONHECIDAS, SINONIMOS, marca_canonica


@pytest.mark.parametrize("bruta, canonica", [
    ("MMC", "mitsubishi"),
    ("mmc", "mitsubishi"),
    ("GM", "chevrolet"),
    ("VW", "volkswagen"),
    ("MITSUBISHI", "mitsubishi"),
    ("Citroën", "citroen"),
    ("NISSAN", "nissan"),
])
def test_traduz_para_o_nome_canonico(bruta, canonica):
    assert marca_canonica(bruta) == canonica


def test_sinonimos_minimos_do_vip():
    assert {"mmc": "mitsubishi", "gm": "chevrolet", "vw": "volkswagen"}.items() <= SINONIMOS.items()


def test_canonicos_sao_marcas_conhecidas():
    assert set(SINONIMOS.values()) <= MARCAS_CONHECIDAS
    assert {"nissan", "toyota", "fiat", "honda", "renault"} <= MARCAS_CONHECIDAS


def test_parser_pode_ampliar_a_tabela():
    assert marca_canonica("CHEV", extras={"chev": "chevrolet"}) == "chevrolet"


def test_marca_desconhecida_passa_como_veio_e_e_registrada(caplog):
    with caplog.at_level(logging.INFO, logger="bot_leilao"):
        assert marca_canonica("Marca Nova Qualquer") == "marca nova qualquer"
    assert any("marca nova qualquer" in r.getMessage() for r in caplog.records)


def test_marca_vazia_e_nula():
    assert marca_canonica(None) is None
    assert marca_canonica("  ") is None


@pytest.mark.parametrize("bruta, canonica", [
    ("CHEV", "chevrolet"),
    ("CAOACHERY", "caoa chery"),
    ("M BENZ", "mercedes-benz"),
    ("LR", "land rover"),
    ("M.BENZ", "mercedes-benz"),   # Freitas, 2026-10-13
])
def test_grafias_do_claudio_kuss(bruta, canonica, caplog):
    """Censo de 391 lotes do Claudio Kuss, 2026-10-10 (roadmap D-42)."""
    with caplog.at_level(logging.INFO, logger="bot_leilao"):
        assert marca_canonica(bruta) == canonica
    assert "fora da tabela" not in caplog.text


@pytest.mark.parametrize("bruta, canonica", [("M-BENZ", "mercedes-benz"), ("CINTROEN", "citroen")])
def test_grafias_do_milan(bruta, canonica, caplog):
    """Feature 005 (D-95): `I/M-BENZ A200` e o erro de digitação `CINTROEN C3` do catálogo de 2026-10-13."""
    assert marca_canonica(bruta) == canonica
    assert "fora da tabela" not in caplog.text


def test_jaguar_e_marca_conhecida():
    assert "jaguar" in MARCAS_CONHECIDAS
