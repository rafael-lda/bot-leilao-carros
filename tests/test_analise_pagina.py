"""Leitura do lote pelo acesso do bot (feature 006; roadmap D-110; RF-07)."""

import pytest

from apoio import (BASE_MILAN, FIXTURES_ANALISE, TOKEN_APIFY_TESTE, ApifySimulado, CenarioE2E, SiteCopart, SiteFreitas,
                   SiteKuss, detalhe_kuss, lote_copart)
from bot_leilao.analise.pagina import ErroPagina, ler_pagina
from bot_leilao.coleta.apify import ClienteApify
from bot_leilao.coleta.http import ClienteHTTP
from bot_leilao.coleta.roteador import ClienteRoteado

LINK_VIP = "https://www.vipleiloes.com.br/evento/anuncio/nissan-sentra-20s-flex-310800"
NIVEIS = {"milan-leiloes": "apify"}


@pytest.fixture
def cenario(raiz, relogio, agora):
    return CenarioE2E(raiz, relogio, agora)


def _cliente(cenario):
    return ClienteRoteado({
        "script": ClienteHTTP(cenario.transporte, relogio=cenario.relogio.agora, dormir=cenario.relogio.dormir),
        "apify": ClienteApify(TOKEN_APIFY_TESTE, cenario.transporte, relogio=cenario.relogio.agora,
                              dormir=cenario.relogio.dormir)})


def test_vip_pela_pagina_do_anuncio_com_o_cambio(cenario):
    cenario.vip = (FIXTURES_ANALISE / "vip_anuncio_310800.html").read_bytes()
    resultado = ler_pagina("vip-leiloes:310800", LINK_VIP, _cliente(cenario), NIVEIS)
    assert (resultado["leiloeiro"], resultado["nivel"], resultado["pago"]) == ("vip-leiloes", "script", False)
    assert resultado["campos"]["cambio"] == "automático"
    assert "Câmbio Automático" in resultado["texto"]
    assert "<" not in resultado["texto"], "texto limpo, sem HTML"
    assert len(resultado["texto"]) <= 8000


def test_kuss_pelo_detalhe_com_evento_e_sequencia_tirados_do_link(cenario):
    cenario.kuss = SiteKuss(detalhes={"282622": detalhe_kuss()})
    resultado = ler_pagina("claudio-kuss-leiloes:282622", "https://www.claudiokussleiloes.com.br/lance/897/0/282622",
                           _cliente(cenario), NIVEIS)
    assert resultado["campos"]["observacoes"].startswith("SINISTRADO")
    assert "SINISTRADO" in resultado["texto"]
    assert [f["le_id"] for f in cenario.kuss.chamadas_op("D")] == ["282622"]


def test_copart_pela_busca_com_o_numero_do_lote(cenario):
    cenario.copart = SiteCopart(lotes=[lote_copart(1176233)])
    resultado = ler_pagina("copart:1176233", "https://www.copart.com.br/lotDetail/1176233", _cliente(cenario), NIVEIS)
    assert cenario.copart.buscas()[0]["query"] == "1176233"
    assert resultado["leiloeiro"] == "copart"
    assert resultado["campos"]["patio"]
    assert "1176233" in resultado["texto"]


def test_freitas_pelo_detalhe(cenario):
    cenario.freitas = SiteFreitas()
    link = "https://www.freitasleiloeiro.com.br/Leiloes/LoteDetalhes?leilaoId=8112&loteNumero=1"
    resultado = ler_pagina("freitas-leiloeiro:8112-1", link, _cliente(cenario), NIVEIS)
    assert resultado["campos"]["patio"] == "SANTO ANDRE - SP"
    assert cenario.freitas.detalhes_pedidos() == ["8112-1"]


def test_milan_pelo_apify_e_marcado_como_pago(cenario):
    cenario.apify = ApifySimulado()
    resultado = ler_pagina("milan-leiloes:15618-209", f"{BASE_MILAN}/leilao/15618/lote/209", _cliente(cenario), NIVEIS)
    assert (resultado["nivel"], resultado["pago"], resultado["custo_estimado_usd"]) == ("apify", True, 0.08)
    assert resultado["campos"]["cambio"] == "automático"
    assert str(resultado["campos"]["lance_corrente"]) == "22400.00"
    assert cenario.chamadas_milan_locais == []


def test_falha_de_acesso_vira_erro_com_o_motivo(cenario):
    cenario.kuss = SiteKuss(detalhes={"282622": 500})
    with pytest.raises(ErroPagina, match="falha"):
        ler_pagina("claudio-kuss-leiloes:282622", "https://www.claudiokussleiloes.com.br/lance/897/0/282622",
                   _cliente(cenario), NIVEIS)


def test_leiloeiro_desconhecido_e_erro(cenario):
    with pytest.raises(ErroPagina, match="leiloeiro"):
        ler_pagina("outro:1", "https://exemplo.com/1", _cliente(cenario), NIVEIS)


def test_kuss_traz_o_resultado_do_pregao_sem_o_apelido(cenario):
    cenario.kuss = SiteKuss(detalhes={"282164": detalhe_kuss()},
                            lances={"897": {"282164": "PRESENCIAL", "282341": "fulano123", "282622": ""}})
    cliente = _cliente(cenario)
    link = "https://www.claudiokussleiloes.com.br/lance/897/0/{}"
    assert ler_pagina("claudio-kuss-leiloes:282164", link.format(282164), cliente, NIVEIS)["campos"]["resultado"] == \
        "último lance presencial; valor não divulgado pelo site"
    online = ler_pagina("claudio-kuss-leiloes:282341", link.format(282341), cliente, NIVEIS)
    assert online["campos"]["resultado"] == "último lance online; valor não divulgado pelo site"
    assert "fulano123" not in str(online), "apelido de quem deu lance nunca sai (privacidade)"
    assert ler_pagina("claudio-kuss-leiloes:282622", link.format(282622), cliente, NIVEIS)["campos"]["resultado"] == \
        "sem lance"
