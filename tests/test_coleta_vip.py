"""Adaptador do Vip Leilões (interfaces/vip-pesquisa.md; roadmap D-10 a D-13, D-15)."""

import logging

import httpx
import pytest

from bot_leilao.coleta import registro
from bot_leilao.coleta.http import ClienteHTTP
from bot_leilao.coleta.vip import BASE, AdaptadorVip

AMPLA = {"procedencia": 4, "monta": 1}


@pytest.fixture
def vip():
    return AdaptadorVip()


def test_esta_registrado_pelo_id(vip):
    assert isinstance(registro.obter_adaptador("vip-leiloes"), AdaptadorVip)
    assert "vip-leiloes" in registro.nomes_adaptadores()


def test_valida_chaves_conhecidas(vip):
    vip.validar_filtros({"procedencia": 4, "monta": 1, "marca": "NISSAN", "ano": 2020})


def test_chave_desconhecida_e_recusada_listando_as_aceitas(vip):
    with pytest.raises(ValueError) as erro:
        vip.validar_filtros({"procedencia": 4, "cor": "azul"})
    assert "cor" in str(erro.value)
    assert "procedencia" in str(erro.value)


def test_lista_e_recusada_porque_o_vip_nao_tem_multipla_escolha(vip):
    with pytest.raises(ValueError):
        vip.validar_filtros({"procedencia": [4, 5]})


def test_requisicao_da_pagina_1(vip):
    req = vip.montar_requisicao(AMPLA, 1)
    assert req.metodo == "POST"
    assert req.url == f"{BASE}/pesquisa?handler=pesquisar"
    assert req.dados == {
        "Filtro.OrdenarPor": "DataInicio",
        "Filtro.SelecaoVeiculos": "true",
        "Filtro.Procedencia": "4",
        "Filtro.Monta": "1",
    }
    assert req.cabecalhos == {"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE}/pesquisa/index"}


def test_pagina_n_reenvia_o_mesmo_corpo(vip):
    """D-13: observado em 2026-10-03."""
    req = vip.montar_requisicao(AMPLA, 3)
    assert req.url == f"{BASE}/pesquisa?SortOrder=DataInicio&pageNumber=3&handler=pesquisar"
    assert req.dados == vip.montar_requisicao(AMPLA, 1).dados


def test_marca_e_traduzida_para_o_campo_do_formulario(vip):
    assert vip.montar_requisicao({"marca": "NISSAN"}, 1).dados["Filtro.Marca"] == "NISSAN"


def test_proxima_pagina_lida_da_marcacao(vip, ler_fixture):
    assert vip.tem_proxima_pagina(ler_fixture("vip/busca_ampla_pagina_1.html"), 1) is True
    assert vip.tem_proxima_pagina(ler_fixture("vip/busca_ampla_ultima_pagina.html"), 17) is False
    assert vip.tem_proxima_pagina(ler_fixture("vip/busca_um_resultado.html"), 1) is False
    assert vip.tem_proxima_pagina(ler_fixture("vip/busca_zero_resultados.html"), 1) is False


def test_verificacao_cruzada_do_total_avisa_divergencia(vip, ler_fixture, caplog):
    """201 resultados = 17 páginas; parar na 5 indica adaptador desatualizado."""
    with caplog.at_level(logging.WARNING):
        vip.tem_proxima_pagina(ler_fixture("vip/busca_ampla_ultima_pagina.html"), 5)
    assert any("201" in r.getMessage() for r in caplog.records)


def test_preparar_sessao_faz_get_na_home(vip, roteiro, relogio):
    transp = roteiro(lambda r: httpx.Response(200, text="home", headers={"Set-Cookie": "__CBCanal=x; Path=/"}))
    cliente = ClienteHTTP(transp.transporte, relogio=relogio.agora, dormir=relogio.dormir)
    resultado = vip.preparar_sessao(cliente)
    assert resultado.ok
    assert str(transp.chamadas[0].url) == f"{BASE}/"
    assert "__CBCanal" in cliente.cookies


@pytest.mark.parametrize("filtros, tipo", [
    ({"procedencia": 4}, "financiamento"),
    ({"procedencia": "4", "monta": 1}, "financiamento"),
    ({"procedencia": 5}, None),
    ({"monta": 1}, None),
])
def test_tipo_de_leilao_herdado_da_busca(vip, filtros, tipo):
    """D-15: só procedencia 4 tem correspondência inequívoca."""
    assert vip.tipo_leilao_da_busca(filtros) == tipo
