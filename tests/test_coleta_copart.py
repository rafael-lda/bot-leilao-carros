"""Adaptador da Copart (feature 003; interfaces/copart-busca.md; roadmap D-53 a D-59)."""

import logging
from urllib.parse import parse_qs

import httpx
import pytest

from apoio import SiteCopart, lote_copart
from bot_leilao.coleta.copart import BASE, AdaptadorCopart
from bot_leilao.coleta.registro import obter_adaptador

FILTROS = {"condicao": "FINANCIAMENTO"}


def _lotes(n, inicio=1000):
    return [lote_copart(ln=inicio + i) for i in range(n)]


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


def test_registrado_pelo_id_do_leiloeiro():
    adaptador = obter_adaptador("copart")
    assert isinstance(adaptador, AdaptadorCopart)
    assert adaptador.teto_paginas == 40


def test_filtros_aceitos_e_chave_desconhecida():
    adaptador = AdaptadorCopart()
    adaptador.validar_filtros({"condicao": "FINANCIAMENTO", "patioveiculo": "Curitiba - PR", "categoria": ["Motos"]})
    with pytest.raises(ValueError, match="Copart"):
        adaptador.validar_filtros({"condicao": "FINANCIAMENTO", "procedencia": 4})


def test_preparar_sessao_abre_a_pagina_da_busca(roteiro, relogio):
    from bot_leilao.coleta.http import ClienteHTTP

    transp = roteiro(lambda r: httpx.Response(200, text="<html>busca</html>"))
    cliente = ClienteHTTP(transp.transporte, relogio=relogio.agora, dormir=relogio.dormir)
    assert AdaptadorCopart().preparar_sessao(cliente).ok
    (chamada,) = transp.chamadas
    assert (chamada.method, str(chamada.url)) == ("GET", f"{BASE}/vehicleFinderSearch")


def test_requisicao_da_primeira_pagina():
    requisicao = AdaptadorCopart().montar_requisicao(FILTROS, 1)
    assert (requisicao.metodo, requisicao.url) == ("POST", f"{BASE}/public/vehicleFinder/search")
    assert requisicao.dados == {"query": "*", "filter[condicao]": 'condicao:"FINANCIAMENTO"', "sort": "lot_number asc",
                                "page": "0", "size": "100", "start": "0"}
    assert requisicao.cabecalhos == {"Accept": "application/json, text/javascript, */*; q=0.01",
                                     "X-Requested-With": "XMLHttpRequest", "Origin": BASE,
                                     "Referer": f"{BASE}/vehicleFinderSearch"}


def test_varios_valores_da_mesma_chave_sao_unidos_por_virgula():
    dados = AdaptadorCopart().montar_requisicao({"condicao": ["FINANCIAMENTO", "USO NORMAL"]}, 1).dados
    assert dados["filter[condicao]"] == 'condicao:"FINANCIAMENTO",condicao:"USO NORMAL"'


def test_percorre_todas_as_paginas_ate_o_total():
    site = SiteCopart(lotes=_lotes(250))
    requisicoes = _percorrer(AdaptadorCopart(), site)
    assert [(r.dados["page"], r.dados["start"]) for r in requisicoes] == [("0", "0"), ("1", "100"), ("2", "200")]


def test_total_multiplo_de_100_nao_pede_pagina_vazia():
    site = SiteCopart(lotes=_lotes(200))
    assert len(_percorrer(AdaptadorCopart(), site)) == 2


def test_pagina_vazia_antes_do_total_encerra_com_aviso(caplog):
    site = SiteCopart(lotes=_lotes(150), total=400)
    with caplog.at_level(logging.WARNING, logger="bot_leilao"):
        assert len(_percorrer(AdaptadorCopart(), site)) == 3
    assert "400" in caplog.text and "150" in caplog.text


def test_zero_resultados_e_uma_pagina_so():
    assert len(_percorrer(AdaptadorCopart(), SiteCopart(lotes=[]))) == 1


def test_lote_repetido_entre_paginas_gera_aviso(caplog):
    """D-55: sem ordenação estável a Copart repete e omite lotes com o total certo (2026-10-11)."""
    pagina1 = _lotes(100)
    pagina2 = [pagina1[5]] + _lotes(49, inicio=5000)
    site = SiteCopart(paginas=[pagina1, pagina2])
    with caplog.at_level(logging.WARNING, logger="bot_leilao"):
        _percorrer(AdaptadorCopart(), site)
    assert "repetid" in caplog.text
    assert "1005" in caplog.text


def test_cursor_recomeca_a_cada_busca(caplog):
    site = SiteCopart(lotes=_lotes(120))
    adaptador = AdaptadorCopart()
    _percorrer(adaptador, site)
    with caplog.at_level(logging.WARNING, logger="bot_leilao"):
        assert len(_percorrer(adaptador, site)) == 2
    assert caplog.text == "", "a segunda busca não acusa repetição dos lotes da primeira"


def test_tipo_de_leilao_pela_condicao():
    adaptador = AdaptadorCopart()
    assert adaptador.tipo_leilao_da_busca(FILTROS) == "financiamento"
    assert adaptador.tipo_leilao_da_busca({"condicao": "COLISÃO"}) is None


def test_corpo_vai_como_formulario():
    requisicao = AdaptadorCopart().montar_requisicao(FILTROS, 2)
    enviado = httpx.Request("POST", requisicao.url, data=requisicao.dados)
    form = {k: v[0] for k, v in parse_qs(enviado.content.decode()).items()}
    assert (form["page"], form["start"], form["sort"]) == ("1", "100", "lot_number asc")
