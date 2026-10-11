"""Adaptador do Claudio Kuss (feature 002; interfaces/claudio-kuss.md; roadmap D-34 a D-40, D-47, D-48)."""

import logging
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from apoio import SiteKuss, agenda_kuss, agenda_sem_financeiras, lote, lote_kuss
from bot_leilao.coleta.claudio_kuss import BASE, AdaptadorClaudioKuss, Evento, ler_agenda
from bot_leilao.coleta.registro import obter_adaptador

FILTROS = {"categoria": "Veículos - Financeiras"}
BRASILIA = timezone(timedelta(hours=-3))
PREGAO_897 = datetime(2026, 10, 13, 10, 0, tzinfo=BRASILIA)
PREGAO_898 = datetime(2026, 10, 20, 10, 0, tzinfo=BRASILIA)


def _lotes(n, inicio=0):
    return [lote_kuss(seq=str(280000 + inicio + i)) for i in range(n)]


def _percorrer(adaptador, site, filtros=FILTROS):
    """Faz o papel do coletor: monta a requisição, obtém a resposta do site simulado e pergunta pela próxima."""
    requisicoes, numero = [], 1
    while True:
        requisicao = adaptador.montar_requisicao(filtros, numero)
        requisicoes.append(requisicao)
        resposta = site.responder(httpx.Request(requisicao.metodo, requisicao.url, data=requisicao.dados,
                                                headers=requisicao.cabecalhos))
        if not adaptador.tem_proxima_pagina(resposta.content, numero):
            return requisicoes
        numero += 1


def _roteiro(requisicoes):
    """Resumo legível da sequência: 'agenda', 'Q 897', 'P 897 1'..."""
    saida = []
    for r in requisicoes:
        if r.url.endswith("/proximos-leiloes"):
            saida.append("agenda")
        elif r.dados["op"] == "Q":
            saida.append(f"Q {r.dados['leilaoID']}")
        else:
            saida.append(f"P {r.dados['leilaoID']} {r.dados['pag']}")
    return saida


# --- Agenda ---------------------------------------------------------------------------------

def test_ler_agenda_real():
    assert ler_agenda(agenda_kuss()) == [
        Evento(id="897", rotulo="Leilão Presencial / Online - Veículos - Financeiras", pregao_em=PREGAO_897,
               local="Curitiba - PR"),
        Evento(id="898", rotulo="Leilão Presencial / Online - Veículos - Financeiras", pregao_em=PREGAO_898,
               local="Curitiba - PR"),
    ]


def test_ler_agenda_sem_blocos_devolve_lista_vazia():
    assert ler_agenda(b"<html><body><h1>Agenda de Leil\xc3\xb5es</h1></body></html>") == []


# --- Cadastro e sessão ----------------------------------------------------------------------

def test_registrado_pelo_id_do_leiloeiro():
    adaptador = obter_adaptador("claudio-kuss-leiloes")
    assert isinstance(adaptador, AdaptadorClaudioKuss)
    assert adaptador.teto_paginas == 120


def test_so_aceita_o_filtro_categoria():
    adaptador = AdaptadorClaudioKuss()
    adaptador.validar_filtros(FILTROS)
    with pytest.raises(ValueError, match="Claudio Kuss"):
        adaptador.validar_filtros({"categoria": "Veículos - Financeiras", "marca": "Renault"})
    with pytest.raises(ValueError, match="categoria"):
        adaptador.validar_filtros({"categoria": ["a", "b"]})


def test_nao_precisa_de_sessao():
    assert AdaptadorClaudioKuss().preparar_sessao(None) is None


def test_tipo_de_leilao_pela_categoria():
    adaptador = AdaptadorClaudioKuss()
    assert adaptador.tipo_leilao_da_busca(FILTROS) == "financiamento"
    assert adaptador.tipo_leilao_da_busca({"categoria": "Imóveis - Bancos"}) is None


# --- Sequência de páginas -------------------------------------------------------------------

def test_pagina_1_e_a_agenda():
    requisicao = AdaptadorClaudioKuss().montar_requisicao(FILTROS, 1)
    assert (requisicao.metodo, requisicao.url) == ("GET", f"{BASE}/proximos-leiloes")
    assert requisicao.anotacoes == {"tipo": "agenda", "categoria": "Veículos - Financeiras"}


def test_percorre_quantidade_e_paginas_de_cada_evento():
    site = SiteKuss(eventos={"897": [_lotes(10), _lotes(3, 10)], "898": [_lotes(4, 20)]})
    requisicoes = _percorrer(AdaptadorClaudioKuss(), site)
    assert _roteiro(requisicoes) == ["agenda", "Q 897", "P 897 1", "P 897 2", "Q 898", "P 898 1"]


def test_corpo_cabecalhos_e_anotacoes_das_requisicoes_json():
    site = SiteKuss(eventos={"897": [_lotes(1)], "898": []})
    _, quantidade, pagina, _ = _percorrer(AdaptadorClaudioKuss(), site)
    assert quantidade.metodo == pagina.metodo == "POST"
    assert quantidade.url == pagina.url == f"{BASE}/json_edital.php"
    assert quantidade.dados == {"op": "Q", "leilaoID": "897", "pesq": ""}
    assert pagina.dados == {"leilaoID": "897", "op": "P", "pag": "1", "loteado": "", "pesq": ""}
    assert pagina.cabecalhos == {"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE}/relacao-foto/897"}
    assert quantidade.anotacoes == {"tipo": "quantidade", "evento": "897", "pregao_em": PREGAO_897,
                                    "patio": "Curitiba - PR"}
    assert pagina.anotacoes == {"tipo": "lotes", "evento": "897", "pregao_em": PREGAO_897, "patio": "Curitiba - PR"}


def test_evento_sem_lotes_nao_pede_paginas():
    site = SiteKuss(eventos={"897": [], "898": [_lotes(2)]})
    assert _roteiro(_percorrer(AdaptadorClaudioKuss(), site)) == ["agenda", "Q 897", "Q 898", "P 898 1"]


def test_sem_evento_da_categoria_para_na_agenda():
    site = SiteKuss(agenda=agenda_sem_financeiras())
    assert _roteiro(_percorrer(AdaptadorClaudioKuss(), site)) == ["agenda"]


def test_categoria_comparada_sem_acento_e_sem_caixa():
    site = SiteKuss(eventos={"897": [_lotes(1)], "898": []})
    requisicoes = _percorrer(AdaptadorClaudioKuss(), site, {"categoria": "veiculos - FINANCEIRAS"})
    assert _roteiro(requisicoes) == ["agenda", "Q 897", "P 897 1", "Q 898"]


# --- Conferência de total e detalhe (D-36, D-48) --------------------------------------------

def test_total_lido_diferente_do_informado_vai_para_o_log(caplog):
    site = SiteKuss(eventos={"897": [_lotes(10), _lotes(3, 10)], "898": []}, qtde={"897": 15})
    with caplog.at_level(logging.WARNING, logger="bot_leilao"):
        _percorrer(AdaptadorClaudioKuss(), site)
    assert "evento 897" in caplog.text
    assert "15" in caplog.text and "13" in caplog.text


def test_total_conferido_sem_aviso(caplog):
    site = SiteKuss(eventos={"897": [_lotes(10), _lotes(3, 10)], "898": []})
    with caplog.at_level(logging.WARNING, logger="bot_leilao"):
        _percorrer(AdaptadorClaudioKuss(), site)
    assert caplog.text == ""


def test_pagina_vazia_antes_do_fim_encerra_o_evento(caplog):
    site = SiteKuss(eventos={"897": [_lotes(10), [], _lotes(3, 10)], "898": [_lotes(1, 30)]})
    with caplog.at_level(logging.WARNING, logger="bot_leilao"):
        requisicoes = _percorrer(AdaptadorClaudioKuss(), site)
    assert _roteiro(requisicoes) == ["agenda", "Q 897", "P 897 1", "P 897 2", "Q 898", "P 898 1"]
    assert "evento 897" in caplog.text


def test_cursor_recomeca_a_cada_busca():
    site = SiteKuss(eventos={"897": [_lotes(2)], "898": [_lotes(1, 5)]})
    adaptador = AdaptadorClaudioKuss()
    primeira = _roteiro(_percorrer(adaptador, site))
    assert _roteiro(_percorrer(adaptador, site)) == primeira


def test_requisicao_do_detalhe():
    candidato = lote(id_canonico="claudio-kuss-leiloes:282622", leiloeiro_id="claudio-kuss-leiloes",
                     evento_id="897")
    requisicao = AdaptadorClaudioKuss().requisicao_detalhe(candidato)
    assert (requisicao.metodo, requisicao.url) == ("POST", f"{BASE}/json_lance_info_lote.php")
    assert requisicao.dados == {"op": "D", "leilaoID": "897", "le_id": "282622", "loteado": "N"}
    assert requisicao.cabecalhos == {"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE}/lance/897/0/282622"}


def test_sem_evento_nao_ha_detalhe():
    candidato = lote(id_canonico="claudio-kuss-leiloes:282622", leiloeiro_id="claudio-kuss-leiloes")
    assert AdaptadorClaudioKuss().requisicao_detalhe(candidato) is None


# --- Feature 003: pátio do evento (D-70) -----------------------------------------------------------

def test_agenda_traz_o_local_do_evento():
    assert [e.local for e in ler_agenda(agenda_kuss())] == ["Curitiba - PR", "Curitiba - PR"]


def test_anotacoes_das_paginas_levam_o_patio():
    site = SiteKuss(eventos={"897": [_lotes(1)], "898": []})
    _, quantidade, pagina, _ = _percorrer(AdaptadorClaudioKuss(), site)
    assert quantidade.anotacoes["patio"] == pagina.anotacoes["patio"] == "Curitiba - PR"
