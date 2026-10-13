"""Adaptador do Freitas (feature 004; interfaces/freitas.md; roadmap D-74 a D-78, D-82)."""

import logging

import httpx
import pytest

from apoio import SiteFreitas, card_freitas, lote
from bot_leilao.coleta.freitas import BASE, AdaptadorFreitas
from bot_leilao.coleta.registro import obter_adaptador

FILTROS = {"categoria": 1, "condicao": "inteiros"}


def _cards(n, inicio=1):
    return [card_freitas(lote=f"9000/{inicio + i}", desc="FIAT/UNO WAY, 15/16, PLACA: A__-___1, GASOL/ALC, PRATA")
            for i in range(n)]


def _percorrer(adaptador, site, filtros=FILTROS):
    requisicoes, numero = [], 1
    while True:
        requisicao = adaptador.montar_requisicao(filtros, numero)
        requisicoes.append(requisicao)
        resposta = site.responder(httpx.Request(requisicao.metodo, requisicao.url, headers=requisicao.cabecalhos))
        if not adaptador.tem_proxima_pagina(resposta.content, numero):
            return requisicoes
        numero += 1


def _pagina(requisicao):
    return httpx.URL(requisicao.url).params["PageNumber"]


def test_registrado_pelo_id_do_leiloeiro():
    assert isinstance(obter_adaptador("freitas-leiloeiro"), AdaptadorFreitas)


def test_filtros_aceitos_e_chave_desconhecida():
    adaptador = AdaptadorFreitas()
    adaptador.validar_filtros({"categoria": 1, "condicao": "inteiros", "estado": "SP", "ano_modelo_min": 2018})
    with pytest.raises(ValueError, match="Freitas"):
        adaptador.validar_filtros({"categoria": 1, "procedencia": 4})


def test_nao_precisa_de_sessao():
    assert AdaptadorFreitas().preparar_sessao(None) is None


def test_requisicao_da_primeira_pagina():
    requisicao = AdaptadorFreitas().montar_requisicao(FILTROS, 1)
    url = httpx.URL(requisicao.url)
    assert (requisicao.metodo, f"{url.scheme}://{url.host}{url.path}") == ("GET", f"{BASE}/Leiloes/PesquisarLotes")
    assert dict(url.params) == {"Nome": "", "Categoria": "1", "TipoLoteId": "0", "FaixaValor": "0",
                                "Condicao": "inteiros", "PatioId": "0", "AnoModeloMin": "0", "AnoModeloMax": "0",
                                "ArCondicionado": "false", "DirecaoAssistida": "false", "Tag": "", "Estado": "",
                                "Cidade": "", "ClienteSclId": "0", "PageNumber": "1", "TopRows": "200"}
    assert requisicao.cabecalhos == {"X-Requested-With": "XMLHttpRequest",
                                     "Referer": f"{BASE}/Leiloes/Pesquisar?query=&categoria=1"}


def test_filtros_viram_os_parametros_do_site():
    url = httpx.URL(AdaptadorFreitas().montar_requisicao({**FILTROS, "estado": "SP", "ano_modelo_min": 2018}, 2).url)
    assert (url.params["Estado"], url.params["AnoModeloMin"], url.params["PageNumber"]) == ("SP", "2018", "2")


def test_percorre_ate_a_mensagem_de_fim():
    requisicoes = _percorrer(AdaptadorFreitas(), SiteFreitas(cards=_cards(250)))
    assert [_pagina(r) for r in requisicoes] == ["1", "2", "3"]


def test_pagina_com_menos_de_200_nao_encerra_a_busca():
    """Lição da Copart: se o site passar a limitar o tamanho da página, parar cedo perderia lotes em silêncio."""
    site = SiteFreitas(paginas=[_cards(12), _cards(12, inicio=100)])
    assert [_pagina(r) for r in _percorrer(AdaptadorFreitas(), site)] == ["1", "2", "3"]


def test_busca_sem_lotes_e_uma_pagina_so():
    assert len(_percorrer(AdaptadorFreitas(), SiteFreitas(cards=[]))) == 1


def test_pagina_sem_cards_e_sem_mensagem_de_fim_encerra():
    """O parser acusa a quebra; o adaptador só não insiste."""
    assert len(_percorrer(AdaptadorFreitas(), SiteFreitas(corpo=b"<html>layout novo</html>"))) == 1


def test_lote_repetido_entre_paginas_gera_aviso(caplog):
    pagina1 = _cards(3)
    site = SiteFreitas(paginas=[pagina1, [pagina1[1]] + _cards(2, inicio=50)])
    with caplog.at_level(logging.WARNING, logger="bot_leilao"):
        _percorrer(AdaptadorFreitas(), site)
    assert "repetid" in caplog.text and "9000-2" in caplog.text


def test_cursor_recomeca_a_cada_busca(caplog):
    adaptador, site = AdaptadorFreitas(), SiteFreitas(cards=_cards(5))
    _percorrer(adaptador, site)
    with caplog.at_level(logging.WARNING, logger="bot_leilao"):
        _percorrer(adaptador, site)
    assert caplog.text == ""


def test_tipo_de_leilao_da_busca_para_a_checagem_de_coerencia():
    assert AdaptadorFreitas().tipo_leilao_da_busca(FILTROS) == "financiamento"


def test_requisicao_do_detalhe_e_o_link_do_lote():
    alvo = lote(id_canonico="freitas-leiloeiro:8112-1", leiloeiro_id="freitas-leiloeiro",
                link=f"{BASE}/Leiloes/LoteDetalhes?leilaoId=8112&loteNumero=1")
    requisicao = AdaptadorFreitas().requisicao_detalhe(alvo)
    assert (requisicao.metodo, requisicao.url) == ("GET", f"{BASE}/Leiloes/LoteDetalhes?leilaoId=8112&loteNumero=1")
