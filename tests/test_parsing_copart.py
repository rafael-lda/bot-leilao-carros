"""Parser da Copart (feature 003; interfaces/copart-busca.md; roadmap D-61 a D-67)."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from apoio import FIXTURES_COPART, bytes_json, json_copart, lote_copart
from bot_leilao.parsing.copart import ParserCopart
from bot_leilao.parsing.modelos import ContextoParsing
from bot_leilao.parsing.nucleo import obter_parser

BASE = "https://www.copart.com.br"
BRASILIA = timezone(timedelta(hours=-3))
COLETADO = datetime(2026, 10, 11, 15, 0, tzinfo=timezone.utc)
CTX = ContextoParsing(leiloeiro_id="copart", busca_id="copart:abc", base_url=BASE, coletado_em=COLETADO,
                      tipo_leilao="financiamento")
parser = ParserCopart()


def _envelope(lotes, total=None, **extra):
    corpo = {"returnCode": 1, "returnCodeDesc": "Success",
             "data": {"query": {}, "results": {"totalElements": len(lotes) if total is None else total,
                                               "content": lotes, "facetFields": []}}}
    corpo.update(extra)
    return bytes_json(corpo)


def _um(**campos):
    (lido,) = parser.extrair(_envelope([lote_copart(**campos)]), CTX).lotes
    return lido


def _selecionados():
    return {l.id_canonico: l for l in parser.extrair((FIXTURES_COPART / "lotes_selecionados.json").read_bytes(),
                                                     CTX).lotes}


def test_registrado_e_sem_preco_obrigatorio():
    assert isinstance(obter_parser("copart"), ParserCopart)
    assert ParserCopart.preco_obrigatorio is False


def test_duster_oroch_real_com_todos_os_campos():
    oroch = _selecionados()["copart:1141180"]
    assert oroch.link == f"{BASE}/lotDetail/1141180"
    assert (oroch.leiloeiro_id, oroch.busca_id, oroch.coletado_em) == ("copart", "copart:abc", COLETADO)
    assert oroch.titulo == "RENAULT DUSTER OROCH 1.6 16V SCE"
    assert (oroch.marca, oroch.modelo) == ("renault", "duster oroch")
    assert oroch.ano_modelo == 2022
    assert oroch.lance_corrente == Decimal("36000")
    assert oroch.lance_inicial is None
    assert oroch.fipe == Decimal("80266.00")
    assert oroch.pregao_em == datetime(2026, 10, 15, 8, 30, tzinfo=BRASILIA), "ad em UTC: 11:30 UTC = 08:30 BRT"
    assert oroch.patio == "VITÓRIA DE SANTO ANTÃO - PE"
    assert oroch.tipo_leilao == "financiamento"
    assert oroch.quilometragem is None
    assert oroch.observacoes == ("PEQUENOS AMASSADOS · Documento NORMAL · Motor dá partida e engrena · "
                                 "Comitente AYMORE CFI")


def test_versa_aguardando_classificacao():
    versa = _selecionados()["copart:1176233"]
    assert (versa.marca, versa.modelo, versa.ano_modelo) == ("nissan", "versa", 2019)
    assert (versa.lance_corrente, versa.fipe, versa.pregao_em) == (None, None, None)
    assert versa.patio == "CAMPO GRANDE - MS"
    assert versa.observacoes == ("NÃO AVALIÁVEL · Aguardando classificação da Copart (data, FIPE e lance a definir) · "
                                 "Motor dá partida e engrena")


def test_compre_agora_usa_o_preco_fixo():
    territory = _selecionados()["copart:1070535"]
    assert territory.lance_corrente == Decimal("141659.00")
    assert territory.pregao_em is None, '"Copart Select" não é data'
    assert territory.observacoes.startswith("Compre Agora · ")


def test_local_do_vendedor_fica_como_veio():
    assert _selecionados()["copart:1062081"].patio == "LOCAL DO VENDEDOR"


def test_chassi_nunca_vira_fipe():
    lido = _um(la=0, fv="9BGXH80005C183447")
    assert lido.fipe is None


def test_cadastro_de_quem_deu_lance_nunca_e_lido():
    lido = _um(currentHighBidder=123456789)
    assert "123456789" not in repr(lido)


def test_monta_aparece_quando_classificada():
    lido = _um(damageClassification="Média Monta", stt="RECUPERÁVEL")
    assert "Documento RECUPERÁVEL · Média Monta" in lido.observacoes


@pytest.mark.parametrize("ad", ["", "Copart Select", "data ruim"])
def test_data_invalida_ou_ausente_e_nula(ad):
    assert _um(ad=ad).pregao_em is None


def test_pagina_real_com_100_lotes():
    extracao = parser.extrair((FIXTURES_COPART / "busca_pag00.json").read_bytes(), CTX)
    assert len(extracao.lotes) == 100
    assert extracao.total_informado == 1506
    assert extracao.busca_vazia is False
    assert all(l.id_canonico.startswith("copart:") and l.link for l in extracao.lotes)


def test_ultima_pagina_real():
    assert len(parser.extrair((FIXTURES_COPART / "busca_ultima.json").read_bytes(), CTX).lotes) == 6


def test_zero_resultados_e_busca_vazia():
    extracao = parser.extrair((FIXTURES_COPART / "busca_zero.json").read_bytes(), CTX)
    assert (extracao.lotes, extracao.busca_vazia, extracao.total_informado) == ([], True, 0)


@pytest.mark.parametrize("conteudo", [
    b"<html>erro</html>",
    bytes_json({"returnCode": 0, "returnCodeDesc": "Erro", "data": {}}),
    bytes_json({"returnCode": 1, "data": {}}),
    _envelope([{"mkn": "FIAT", "lm": "UNO"}]),
])
def test_formato_inesperado_levanta(conteudo):
    with pytest.raises(Exception):
        parser.extrair(conteudo, CTX)


def test_marca_por_sinonimo():
    assert _um(mkn="MERCEDES BENZ", lm="CLASSE A").marca == "mercedes-benz"
