"""Normalizadores (parser-lotes RF-03 a RF-05, EC-03, EC-04)."""

from decimal import Decimal

import pytest

from bot_leilao.parsing.normalizadores import inteiro, link_absoluto, normalizar_anos, normalizar_km, normalizar_preco


@pytest.mark.parametrize("texto, esperado", [
    ("R$ 45.000,00", Decimal("45000.00")),
    ("R$ 12.500", Decimal("12500")),
    ("R$\xa01.234.567,89", Decimal("1234567.89")),
    ("45000", Decimal("45000")),
    ("Valor inicial: R$ 9.500,00", Decimal("9500.00")),
])
def test_preco(texto, esperado):
    assert normalizar_preco(texto) == esperado


@pytest.mark.parametrize("texto", ["Sob consulta", "A combinar", "", None, "R$ -"])
def test_preco_sem_valor_e_nulo(texto):
    assert normalizar_preco(texto) is None


@pytest.mark.parametrize("texto, esperado", [
    ("2018/2019", (2018, 2019)),
    ("SENTRA 20S FLEX - 2012/2013", (2012, 2013)),
    ("2018", (2018, 2018)),
    ("0000", (None, None)),
    ("", (None, None)),
    (None, (None, None)),
    ("1850/1851", (None, None)),
])
def test_anos(texto, esperado):
    assert normalizar_anos(texto) == esperado


def test_ano_de_modelo_invalido_nao_contamina_o_de_fabricacao():
    assert normalizar_anos("2018/0000") == (2018, None)


@pytest.mark.parametrize("texto, esperado", [
    ("228.227 Km", 228227),
    ("5.458 Km", 5458),
    ("80000 km", 80000),
    ("899.999 Km", 899999),
    ("", None),
    (None, None),
    ("placa final 1", None),
])
def test_quilometragem(texto, esperado):
    assert normalizar_km(texto) == esperado


@pytest.mark.parametrize("texto", ["0 Km", "0", "999.999 Km", "999999 km", "900.000 Km", "1.234.567 Km"])
def test_quilometragem_sentinela_vale_nao_informada(texto):
    """Leiloeiros preenchem 0 ou 999.999 quando a km não é conhecida (carro sem chave, bateria arriada...).
    Tratar como número real eliminaria o carro por engano (roadmap D-32)."""
    assert normalizar_km(texto) is None


@pytest.mark.parametrize("href, esperado", [
    ("/evento/anuncio/nissan-sentra-20s-flex-310800", "https://www.vipleiloes.com.br/evento/anuncio/nissan-sentra-20s-flex-310800"),
    ("https://outro.com.br/lote/1", "https://outro.com.br/lote/1"),
    ("lote/12345", "https://www.vipleiloes.com.br/lote/12345"),
    ("", None),
    (None, None),
    ("#", None),
    ("javascript:void(0)", None),
])
def test_link_absoluto(href, esperado):
    assert link_absoluto(href, "https://www.vipleiloes.com.br") == esperado


@pytest.mark.parametrize("texto, esperado", [("1 Lance", 1), ("23 Lances", 23), ("Lote: 21", 21), ("", None), (None, None)])
def test_inteiro(texto, esperado):
    assert inteiro(texto) == esperado


@pytest.mark.parametrize("texto, esperado", [
    ("13/13", (2013, 2013)),
    ("14/15", (2014, 2015)),
    (" 21/22 ", (2021, 2022)),
    ("98/99", (1998, 1999)),
    ("99/00", (1999, 2000)),
    ("26/27", (2026, 2027)),
    ("", (None, None)),
    (None, (None, None)),
    ("2013/2013", (None, None)),
    ("ab/cd", (None, None)),
])
def test_anos_dois_digitos_do_claudio_kuss(texto, esperado):
    """`AA/AA` (roadmap D-44): 20AA até o ano corrente + 1, senão 19AA. Ano corrente fixo em 2026."""
    from bot_leilao.parsing.normalizadores import anos_dois_digitos

    assert anos_dois_digitos(texto, ano_corrente=2026) == esperado


def test_valor_do_claudio_kuss():
    assert normalizar_preco("21.600,00") == Decimal("21600.00")
    assert normalizar_preco("") is None
