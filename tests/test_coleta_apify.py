"""Cliente do nível `apify` (feature 005; interfaces/apify.md; roadmap D-86, D-88, D-89, D-91)."""

import json
from datetime import datetime, timezone

import httpx
import pytest

from apoio import (ATOR_PADRAO_TESTE, BASE_MILAN, CAMINHO_EXECUCAO, TOKEN_APIFY_TESTE, ApifySimulado, item_milan)
from bot_leilao.coleta.apify import ATOR_PADRAO, PERFIS_ATOR, ClienteApify
from bot_leilao.coleta.modelos import Requisicao, Veredito

AGENDA = f"{BASE_MILAN}/agenda/veiculos"
CATALOGO = f"{BASE_MILAN}/leilao/15618/catalogo"


def _cliente(apify: ApifySimulado, relogio, **opcoes) -> ClienteApify:
    return ClienteApify(TOKEN_APIFY_TESTE, httpx.MockTransport(apify.responder), relogio=relogio.agora,
                        dormir=relogio.dormir, **opcoes)


def test_ator_padrao_e_o_unico_perfil_conhecido():
    assert ATOR_PADRAO == ATOR_PADRAO_TESTE
    assert set(PERFIS_ATOR) == {ATOR_PADRAO}


def test_chamada_sincrona_com_a_url_e_o_token_so_no_cabecalho(relogio):
    apify = ApifySimulado()
    _cliente(apify, relogio).requisitar(Requisicao("GET", AGENDA))

    (execucao,) = apify.execucoes()
    assert execucao.method == "POST"
    assert execucao.url.path == CAMINHO_EXECUCAO
    assert execucao.url.params["timeout"] == "180"
    assert json.loads(execucao.content) == {"url": AGENDA}
    assert execucao.headers["Authorization"] == f"Bearer {TOKEN_APIFY_TESTE}"
    assert all(TOKEN_APIFY_TESTE not in str(c.url) for c in apify.chamadas), "o token nunca vai na URL"


def test_pagina_ok_devolve_o_html_e_a_url_do_site(relogio):
    resultado = _cliente(ApifySimulado(), relogio).requisitar(Requisicao("GET", CATALOGO))
    assert resultado.veredito is Veredito.OK
    assert resultado.status_http == 200
    assert resultado.url == CATALOGO
    assert resultado.conteudo == item_milan("catalogo_15618.json")["content"].encode("utf-8")
    assert resultado.tentativas == 1


def test_cookies_do_ator_sao_descartados(relogio):
    item = dict(item_milan("lote_001.json"), cookies=[{"name": "cf_clearance", "value": "segredo-do-site"}])
    apify = ApifySimulado(paginas={AGENDA: item})
    resultado = _cliente(apify, relogio).requisitar(Requisicao("GET", AGENDA))
    assert resultado.ok
    assert "segredo-do-site" not in repr(resultado)


@pytest.mark.parametrize("falha, veredito, motivo, execucoes", [
    ("token", Veredito.FALHA_AUTENTICACAO, "apify: token inválido", 1),
    ("cota", Veredito.FALHA_REDE, "apify: cota esgotada", 1),
    ("tempo", Veredito.FALHA_REDE, "apify: tempo esgotado", 2),
    ("plataforma", Veredito.FALHA_REDE, "apify: plataforma indisponível", 2),
    ("desafio", Veredito.BLOQUEADO, f"desafio_antibot (via apify: {ATOR_PADRAO_TESTE})", 2),
    ("vazio", Veredito.FALHA_REDE, "apify: sem resultado", 2),
])
def test_falhas_traduzidas_com_a_causa_e_sem_insistir_em_token_ou_cota(relogio, falha, veredito, motivo, execucoes):
    apify = ApifySimulado(falha=falha)
    resultado = _cliente(apify, relogio).requisitar(Requisicao("GET", AGENDA))
    assert resultado.veredito is veredito
    assert resultado.motivo == motivo
    assert resultado.tentativas == execucoes
    assert len(apify.execucoes()) == execucoes


def test_erro_de_conexao_com_a_plataforma(relogio):
    apify = ApifySimulado(paginas={AGENDA: httpx.ConnectError})
    resultado = _cliente(apify, relogio).requisitar(Requisicao("GET", AGENDA))
    assert resultado.veredito is Veredito.FALHA_REDE
    assert resultado.motivo == "apify: plataforma indisponível"
    assert resultado.tentativas == 2


def test_pagina_inexistente_no_site_nao_e_repetida(relogio):
    apify = ApifySimulado(paginas={})
    resultado = _cliente(apify, relogio).requisitar(Requisicao("GET", f"{BASE_MILAN}/leilao/1/catalogo"))
    assert resultado.veredito is Veredito.FALHA_REDE
    assert resultado.motivo == "http_404 (via apify)"
    assert len(apify.execucoes()) == 1


def test_status_desconhecido_da_api_cita_o_tipo_do_erro(relogio):
    apify = ApifySimulado(paginas={AGENDA: 418})
    resultado = _cliente(apify, relogio).requisitar(Requisicao("GET", AGENDA))
    assert resultado.veredito is Veredito.FALHA_REDE
    assert resultado.motivo == "apify: http_418 (simulado)"


@pytest.mark.parametrize("requisicao", [
    Requisicao("POST", AGENDA),
    Requisicao("GET", AGENDA, dados={"op": "P"}),
])
def test_requisicao_que_o_ator_nao_sabe_fazer_e_recusada_antes_de_qualquer_chamada(relogio, requisicao):
    apify = ApifySimulado()
    with pytest.raises(ValueError, match="GET"):
        _cliente(apify, relogio).requisitar(requisicao)
    assert apify.chamadas == []


def test_conta_as_execucoes_e_espaca_o_mesmo_host(relogio):
    apify = ApifySimulado()
    cliente = _cliente(apify, relogio)
    cliente.requisitar(Requisicao("GET", AGENDA))
    cliente.requisitar(Requisicao("GET", CATALOGO))
    assert cliente.execucoes == 2
    assert 5.0 in relogio.dormidas, "5 s entre páginas do mesmo site, também pelo Apify"


def test_consumo_pela_diferenca_dos_limites_da_conta(relogio):
    apify = ApifySimulado(uso=0.39)
    cliente = _cliente(apify, relogio)
    cliente.requisitar(Requisicao("GET", AGENDA))
    cliente.requisitar(Requisicao("GET", CATALOGO))
    consumo = cliente.consumo()
    assert consumo.gasto_varredura == pytest.approx(0.16)
    assert consumo.gasto_ciclo == pytest.approx(0.55)
    assert consumo.limite == pytest.approx(5.0)
    assert consumo.fim_ciclo == datetime(2026, 10, 17, 23, 59, 59, 999000, tzinfo=timezone.utc)


def test_sem_paginas_nao_ha_consumo_nem_consulta(relogio):
    apify = ApifySimulado()
    assert _cliente(apify, relogio).consumo() is None
    assert apify.chamadas == []


def test_consulta_de_limites_falhando_deixa_o_consumo_indisponivel(relogio):
    apify = ApifySimulado()
    apify.limites_falham = True
    cliente = _cliente(apify, relogio)
    assert cliente.requisitar(Requisicao("GET", AGENDA)).ok, "a página sai mesmo sem a consulta de limites"
    assert cliente.consumo() is None


def test_ator_sem_perfil_e_recusado(relogio):
    with pytest.raises(ValueError, match="neatrat/cloudflare-scraper"):
        _cliente(ApifySimulado(), relogio, atores_por_host={"milanleiloes.com.br": "alguem/outro-ator"})


def test_ator_escolhido_pelo_host_do_site(relogio):
    apify = ApifySimulado()
    _cliente(apify, relogio, atores_por_host={"milanleiloes.com.br": ATOR_PADRAO}).requisitar(Requisicao("GET", AGENDA))
    assert apify.execucoes()[0].url.path == CAMINHO_EXECUCAO
