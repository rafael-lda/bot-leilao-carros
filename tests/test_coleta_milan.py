"""Adaptador do Milan Leilões (feature 005; interfaces/milan.md; roadmap D-93, D-94, D-97)."""

from datetime import datetime, timedelta, timezone

import pytest

from apoio import BASE_MILAN, agenda_milan_sem_financiamento, html_milan, lote
from bot_leilao.coleta import registro
from bot_leilao.coleta.milan import AdaptadorMilan, ler_agenda

BRASILIA = timezone(timedelta(hours=-3))
FILTROS = {"descricao_contem": "recuperados de financiamento"}
REFERENCIA = datetime(2026, 10, 13, 22, 0, tzinfo=BRASILIA)


@pytest.fixture
def adaptador():
    adaptador = AdaptadorMilan()
    adaptador.agora = lambda: REFERENCIA
    return adaptador


def test_registrado_como_milan_leiloes():
    assert isinstance(registro.obter_adaptador("milan-leiloes"), AdaptadorMilan)


def test_agenda_real_com_dois_leiloes_e_data_sem_ano():
    leiloes = ler_agenda(html_milan("agenda.json"), REFERENCIA)
    assert [l.id for l in leiloes] == ["15595", "15618"]
    judicial, financiamento = leiloes
    assert "Leilão Judicial" in judicial.rotulo
    assert "RECUPERADOS DE FINANCIAMENTO" in financiamento.rotulo
    assert financiamento.pregao_em == datetime(2026, 10, 14, 9, 30, tzinfo=BRASILIA)
    assert judicial.pregao_em == datetime(2026, 10, 9, 14, 0, tzinfo=BRASILIA)


def test_data_de_janeiro_vista_em_dezembro_cai_no_ano_seguinte():
    html = html_milan("agenda.json").decode("utf-8").replace("14 de OUT", "05 de JAN").encode("utf-8")
    leiloes = ler_agenda(html, datetime(2026, 12, 20, 8, 0, tzinfo=BRASILIA))
    assert leiloes[1].pregao_em == datetime(2027, 1, 5, 9, 30, tzinfo=BRASILIA)


def test_filtros_aceitos(adaptador):
    adaptador.validar_filtros(FILTROS)
    with pytest.raises(ValueError, match="Milan"):
        adaptador.validar_filtros({"categoria": "Veículos"})
    with pytest.raises(ValueError, match="descricao_contem"):
        adaptador.validar_filtros({"descricao_contem": "  "})


def test_sem_preparacao_de_sessao_e_tipo_financiamento(adaptador):
    assert adaptador.preparar_sessao(object()) is None
    assert adaptador.tipo_leilao_da_busca(FILTROS) == "financiamento"
    assert adaptador.teto_paginas == 10


def test_agenda_e_depois_o_catalogo_do_leilao_de_financiamento(adaptador):
    primeira = adaptador.montar_requisicao(FILTROS, 1)
    assert (primeira.metodo, primeira.url, primeira.dados) == ("GET", f"{BASE_MILAN}/agenda/veiculos", None)
    assert primeira.anotacoes == {"tipo": "agenda"}

    assert adaptador.tem_proxima_pagina(html_milan("agenda.json"), 1) is True
    segunda = adaptador.montar_requisicao(FILTROS, 2)
    assert (segunda.metodo, segunda.url) == ("GET", f"{BASE_MILAN}/leilao/15618/catalogo")
    assert segunda.anotacoes["tipo"] == "catalogo"
    assert segunda.anotacoes["evento"] == "15618"
    assert segunda.anotacoes["pregao_em"] == datetime(2026, 10, 14, 9, 30, tzinfo=BRASILIA)
    assert "RECUPERADOS DE FINANCIAMENTO" in segunda.anotacoes["rotulo"]

    assert adaptador.tem_proxima_pagina(html_milan("catalogo_15618.json"), 2) is False


def test_agenda_sem_leilao_de_financiamento_encerra_a_busca(adaptador):
    adaptador.montar_requisicao(FILTROS, 1)
    agenda = agenda_milan_sem_financiamento()["content"].encode("utf-8")
    assert adaptador.tem_proxima_pagina(agenda, 1) is False


def test_dois_leiloes_escolhidos_viram_dois_catalogos(adaptador):
    adaptador.montar_requisicao(FILTROS, 1)
    agenda = html_milan("agenda.json").decode("utf-8").replace("Leilão Judicial", "RECUPERADOS DE FINANCIAMENTO")
    assert adaptador.tem_proxima_pagina(agenda.encode("utf-8"), 1)
    assert adaptador.montar_requisicao(FILTROS, 2).url == f"{BASE_MILAN}/leilao/15595/catalogo"
    assert adaptador.tem_proxima_pagina(b"catalogo", 2) is True
    assert adaptador.montar_requisicao(FILTROS, 3).url == f"{BASE_MILAN}/leilao/15618/catalogo"
    assert adaptador.tem_proxima_pagina(b"catalogo", 3) is False


def test_nova_busca_recomeca_pela_agenda(adaptador):
    adaptador.montar_requisicao(FILTROS, 1)
    adaptador.tem_proxima_pagina(html_milan("agenda.json"), 1)
    assert adaptador.montar_requisicao(FILTROS, 1).url == f"{BASE_MILAN}/agenda/veiculos"


def test_detalhe_pelo_link_do_lote(adaptador):
    link = f"{BASE_MILAN}/leilao/15618/lote/046"
    requisicao = adaptador.requisicao_detalhe(lote(id_canonico="milan-leiloes:15618-046", link=link))
    assert (requisicao.metodo, requisicao.url) == ("GET", link)
    assert adaptador.requisicao_detalhe(lote(link=None)) is None
