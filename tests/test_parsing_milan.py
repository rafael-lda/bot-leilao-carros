"""Parser do Milan Leilões com as páginas reais de 2026-10-13 (feature 005; interfaces/milan.md; D-95 a D-97)."""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from apoio import BASE_MILAN, agenda_milan_sem_financiamento, html_milan, lote, lote_milan_com_lance
from bot_leilao.parsing import nucleo
from bot_leilao.parsing.milan import ParserMilan
from bot_leilao.parsing.modelos import ContextoParsing

BRASILIA = timezone(timedelta(hours=-3))
COLETADO = datetime(2026, 10, 14, 1, 0, tzinfo=timezone.utc)
PREGAO = datetime(2026, 10, 14, 9, 30, tzinfo=BRASILIA)


def _contexto(**pagina):
    return ContextoParsing(leiloeiro_id="milan-leiloes", busca_id="milan-leiloes:financiamento",
                           base_url=BASE_MILAN, coletado_em=COLETADO, tipo_leilao="financiamento",
                           pagina=pagina or {"tipo": "catalogo", "evento": "15618", "pregao_em": PREGAO})


@pytest.fixture(scope="module")
def catalogo():
    extracao = ParserMilan().extrair(html_milan("catalogo_15618.json"), _contexto())
    return {l.numero_lote: l for l in extracao.lotes}


def test_registrado_e_sem_preco_obrigatorio():
    assert isinstance(nucleo.obter_parser("milan-leiloes"), ParserMilan)
    assert ParserMilan.preco_obrigatorio is False, "o catálogo não traz o lance atual"


def test_so_os_veiculos_do_catalogo_e_os_materiais_contados_no_log(caplog):
    with caplog.at_level(logging.INFO, logger="bot_leilao"):
        extracao = ParserMilan().extrair(html_milan("catalogo_15618.json"), _contexto())
    assert len(extracao.lotes) == 243
    assert not extracao.busca_vazia
    assert "11" in caplog.text and "materia" in caplog.text.lower()


def test_creta_046_completo(catalogo):
    creta = catalogo["046"]
    assert creta.id_canonico == "milan-leiloes:15618-046"
    assert creta.link == f"{BASE_MILAN}/leilao/15618/lote/046"
    assert creta.leiloeiro_id == "milan-leiloes"
    assert creta.titulo == "HYUNDAI CRETA ACTION 1.6 FLEX 4P ANO 2022/2022"
    assert (creta.marca, creta.modelo) == ("hyundai", "creta action 1.6 flex 4p")
    assert (creta.ano_fabricacao, creta.ano_modelo) == (2022, 2022)
    assert creta.quilometragem == 99020
    assert creta.cambio == "automático"
    assert creta.observacoes == "IPVA 2026 PAGO · Comitente Banco Honda"
    assert creta.tipo_leilao == "financiamento"
    assert creta.evento_id == "15618"
    assert creta.pregao_em == PREGAO
    assert creta.patio == "São Paulo - SP"
    assert creta.lance_inicial is None and creta.lance_corrente is None


def test_aviso_em_vermelho_e_lance_inicial(catalogo):
    duster = catalogo["209"]
    assert duster.observacoes == "VEÍCULO COM CÂMBIO DANDO TRANCO · IPVA 2026 PAGO · Comitente Grupo Safra"
    assert duster.lance_inicial == Decimal("21500")
    assert duster.cambio == "automático", "o 'CÂMBIO' do aviso não confunde a leitura do câmbio"
    assert catalogo["011"].observacoes == "VEÍCULO NÃO FUNCIONA, MOTOR VIRA MAS NÃO PEGA · Comitente FORD"


def test_cambio_manual(catalogo):
    assert catalogo["028"].cambio == "manual"
    assert catalogo["028"].quilometragem == 213973


@pytest.mark.parametrize("numero, marca, modelo", [
    ("007", "toyota", "hilux cd srx a 4fd diesel 4p"),          # I/I/ repetido
    ("039", "land rover", "evoque p240 se 2.0 gasolina 4p"),    # marca de duas palavras
    ("017", "mercedes-benz", "a200 sd hi gasolina 4p"),         # I/M-BENZ
    ("194", "citroen", "c3 excl 1.4 flex 4p"),                  # CINTROEN, erro de digitação do site
    ("001", "ford", "ranger xls 2.2 4x4 cd diesel 4p"),
])
def test_marca_e_modelo(catalogo, numero, marca, modelo):
    assert (catalogo[numero].marca, catalogo[numero].modelo) == (marca, modelo)


def test_lote_com_sufixo_e_sucata(catalogo):
    assert catalogo["015A"].id_canonico == "milan-leiloes:15618-015A"
    cruze = catalogo["074A"]
    assert cruze.situacao == "sucata"
    assert cruze.quilometragem is None


def test_agenda_reconhecida_e_pagina_vazia_de_lotes():
    extracao = ParserMilan().extrair(html_milan("agenda.json"), _contexto(tipo="agenda"))
    assert extracao.lotes == [] and extracao.busca_vazia
    sem = agenda_milan_sem_financiamento()["content"].encode("utf-8")
    assert ParserMilan().extrair(sem, _contexto(tipo="agenda")).busca_vazia


def test_agenda_irreconhecivel_e_quebra():
    with pytest.raises(ValueError):
        ParserMilan().extrair(b"<html><body>layout novo</body></html>", _contexto(tipo="agenda"))


def test_catalogo_sem_cards_e_sem_cabecalho_e_quebra():
    with pytest.raises(ValueError):
        ParserMilan().extrair(b"<html><body>layout novo</body></html>", _contexto())


# --- Detalhe do lote (D-97) ---------------------------------------------------------------------


def _detalhar(nome_ou_item, **campos):
    alvo = lote(id_canonico="milan-leiloes:15618-001", leiloeiro_id="milan-leiloes", lance_inicial=None,
                lance_corrente=None, cambio=None, placa_parcial=None, **campos)
    conteudo = html_milan(nome_ou_item) if isinstance(nome_ou_item, str) else nome_ou_item["content"].encode("utf-8")
    ParserMilan().aplicar_detalhe(alvo, conteudo)
    return alvo


def test_detalhe_com_lance_atual_placa_e_cambio():
    ranger = _detalhar("lote_001.json")
    assert ranger.lance_corrente == Decimal("66200")
    assert ranger.lance_inicial is None
    assert ranger.placa_parcial == "final 6"
    assert ranger.cambio == "automático"
    assert ranger.detalhe_lido is True
    assert ranger.retirado is False


def test_detalhe_sem_lance_continua_sem_preco():
    creta = _detalhar("lote_046.json")
    assert creta.lance_corrente is None and creta.lance_inicial is None
    assert creta.placa_parcial == "final 1"


def test_detalhe_com_lance_inicial_e_atual():
    duster = _detalhar("lote_209.json")
    assert duster.lance_inicial == Decimal("21500")
    assert duster.lance_corrente == Decimal("22400")


def test_detalhe_com_lance_trocado_na_amostra():
    assert _detalhar(lote_milan_com_lance("046", "50.000,00")).lance_corrente == Decimal("50000")


def test_detalhe_nao_sobrescreve_cambio_do_catalogo():
    assert _detalhar("lote_001.json", cambio="manual").cambio == "manual"


def test_detalhe_retirado():
    item = lote_milan_com_lance("046", "---")
    item["content"] = item["content"].replace("RECEBENDO LANCES", "RETIRADO")
    assert _detalhar(item).retirado is True


def test_detalhe_irreconhecivel_e_erro():
    with pytest.raises(ValueError):
        ParserMilan().aplicar_detalhe(lote(), b"<html><body>layout novo</body></html>")
