"""Parser do Vip contra HTML real (interfaces/vip-pesquisa.md §3; roadmap D-14 a D-16, D-28, D-31)."""

import logging
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from bot_leilao.coleta.modelos import Pagina, RespostaBruta, Veredito
from bot_leilao.parsing.modelos import ContextoParsing
from bot_leilao.parsing.nucleo import obter_parser, processar
from bot_leilao.parsing.vip import ParserVip

BASE = "https://www.vipleiloes.com.br"
INSTANTE = datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc)
CTX = ContextoParsing(leiloeiro_id="vip-leiloes", busca_id="vip-leiloes:ampla", base_url=BASE,
                      coletado_em=INSTANTE, tipo_leilao="financiamento")


@pytest.fixture
def parser():
    return ParserVip()


def _por_id(extracao):
    return {l.id_canonico: l for l in extracao.lotes}


def test_esta_registrado_pelo_id():
    assert isinstance(obter_parser("vip-leiloes"), ParserVip)


def test_um_resultado_todos_os_campos(parser, ler_fixture):
    extracao = parser.extrair(ler_fixture("vip/busca_um_resultado.html"), CTX)
    (sentra,) = extracao.lotes
    assert sentra.id_canonico == "vip-leiloes:310800", "id do anúncio, e não 'Lote: 21' (D-14)"
    assert sentra.numero_lote == "21"
    assert sentra.link == f"{BASE}/evento/anuncio/nissan-sentra-20s-flex-310800"
    assert sentra.marca == "nissan"
    assert sentra.modelo == "sentra 20s flex"
    assert sentra.titulo == "Nissan Sentra 20S Flex"
    assert (sentra.ano_fabricacao, sentra.ano_modelo) == (2012, 2013)
    assert sentra.quilometragem == 228227
    assert sentra.lance_inicial == Decimal("12500")
    assert sentra.lance_corrente == Decimal("12500"), "1 lance: o valor atual é o lance corrente"
    assert sentra.situacao == "Aberto para lances"
    assert sentra.retirado is False
    assert sentra.tipo_leilao == "financiamento", "herdado da busca (D-15)"
    assert sentra.leiloeiro_id == "vip-leiloes"
    assert sentra.busca_id == "vip-leiloes:ampla"
    assert sentra.coletado_em == INSTANTE
    assert "SC" in sentra.descricao
    assert "05/10/2026" in sentra.descricao
    assert extracao.total_informado == 1
    assert extracao.busca_vazia is False


def test_pagina_cheia_tem_12_lotes_e_total(parser, ler_fixture):
    extracao = parser.extrair(ler_fixture("vip/busca_ampla_pagina_1.html"), CTX)
    assert len(extracao.lotes) == 12
    assert extracao.total_informado == 201
    assert all(l.link.startswith(f"{BASE}/evento/anuncio/") for l in extracao.lotes)
    assert len({l.id_canonico for l in extracao.lotes}) == 12


def test_lance_corrente_diferente_do_inicial(parser, ler_fixture):
    civic = _por_id(parser.extrair(ler_fixture("vip/busca_ampla_pagina_1.html"), CTX))["vip-leiloes:312040"]
    assert civic.lance_corrente == Decimal("63000")
    assert civic.lance_inicial == Decimal("35000")


def test_sem_lance_corrente_e_nulo(parser, ler_fixture):
    """parser-lotes EC-11: '0 Lances' → corrente nulo, inicial preenchido."""
    aircross = _por_id(parser.extrair(ler_fixture("vip/busca_ampla_pagina_1.html"), CTX))["vip-leiloes:312839"]
    assert aircross.lance_corrente is None
    assert aircross.lance_inicial == Decimal("7000")


def test_quilometragem_ausente_e_nula(parser, ler_fixture):
    compass = _por_id(parser.extrair(ler_fixture("vip/busca_ampla_pagina_1.html"), CTX))["vip-leiloes:312937"]
    assert compass.quilometragem is None
    assert compass.ano_modelo == 2020


def test_sinonimos_de_marca_do_vip_sao_traduzidos(parser, ler_fixture):
    """D-28: mmc e gm aparecem em cards reais."""
    pagina_1 = _por_id(parser.extrair(ler_fixture("vip/busca_ampla_pagina_1.html"), CTX))
    ultima = _por_id(parser.extrair(ler_fixture("vip/busca_ampla_ultima_pagina.html"), CTX))
    l200 = pagina_1["vip-leiloes:311968"]
    s10 = ultima["vip-leiloes:306622"]
    assert (l200.marca, l200.titulo) == ("mitsubishi", "Mitsubishi L200 Outdoor")
    assert s10.marca == "chevrolet"


def test_zero_resultados_e_busca_vazia_declarada(parser, ler_fixture):
    """D-31: 'Nenhum lote encontrado.' sem indicador de total."""
    extracao = parser.extrair(ler_fixture("vip/busca_zero_resultados.html"), CTX)
    assert extracao.lotes == []
    assert extracao.busca_vazia is True
    assert extracao.total_informado is None


def _variacao(ler_fixture, *trocas):
    html = ler_fixture("vip/busca_um_resultado.html").decode("utf-8")
    for antes, depois in trocas:
        assert antes in html
        html = html.replace(antes, depois)
    return html.encode("utf-8")


@pytest.mark.parametrize("km_no_site", ["999.999 Km", "0 Km"])
def test_km_sentinela_do_site_vira_nao_informada(parser, ler_fixture, km_no_site):
    """D-32: 999.999 e 0 são como o leiloeiro diz 'não sei'; o lote não pode ser tratado como muito rodado."""
    conteudo = _variacao(ler_fixture, ("228.227 Km", km_no_site))
    (sentra,) = parser.extrair(conteudo, CTX).lotes
    assert sentra.quilometragem is None


def test_retirado_pelo_texto(parser, ler_fixture):
    """D-16 / RN-12."""
    conteudo = _variacao(ler_fixture, ("Aberto para lances", "Lote Retirado"))
    (sentra,) = parser.extrair(conteudo, CTX).lotes
    assert sentra.retirado is True
    assert sentra.situacao == "Lote Retirado"


def test_retirado_pela_classe(parser, ler_fixture):
    conteudo = _variacao(ler_fixture, ("anuncio-AbertoParaOfertas", "anuncio-Retirado"))
    assert parser.extrair(conteudo, CTX).lotes[0].retirado is True


def test_situacao_desconhecida_e_registrada_em_log(parser, ler_fixture, caplog):
    conteudo = _variacao(ler_fixture, ("Aberto para lances", "Em análise"))
    with caplog.at_level(logging.INFO, logger="bot_leilao"):
        (sentra,) = parser.extrair(conteudo, CTX).lotes
    assert sentra.retirado is False
    assert any("Em análise" in r.getMessage() for r in caplog.records)


def test_layout_novo_vira_quebra_no_processamento(ler_fixture):
    html = ler_fixture("vip/busca_ampla_pagina_1.html").replace(b"card-anuncio", b"card-novo-layout")
    resposta = RespostaBruta(busca_id="vip-leiloes:ampla", leiloeiro_id="vip-leiloes", iniciado_em=INSTANTE,
                             duracao_ms=1, status_http=200, paginas=[Pagina(1, "POST", BASE, html)],
                             nivel_usado="script", tentativas=1, veredito=Veredito.OK)
    resultado = processar(resposta, CTX)
    assert resultado.quebra_suspeita is True


def test_processamento_de_duas_paginas_reais(ler_fixture):
    paginas = [Pagina(1, "POST", BASE, ler_fixture("vip/busca_ampla_pagina_1.html")),
               Pagina(17, "POST", BASE, ler_fixture("vip/busca_ampla_ultima_pagina.html"))]
    resposta = RespostaBruta(busca_id="vip-leiloes:ampla", leiloeiro_id="vip-leiloes", iniciado_em=INSTANTE,
                             duracao_ms=1, status_http=200, paginas=paginas, nivel_usado="script",
                             tentativas=1, veredito=Veredito.OK)
    resultado = processar(resposta, CTX)
    assert len(resultado.lotes) == 21
    assert resultado.quebra_suspeita is False
    assert resultado.descartados == 0


def test_zero_resultados_no_processamento_nao_alerta(ler_fixture):
    resposta = RespostaBruta(busca_id="vip-leiloes:ampla", leiloeiro_id="vip-leiloes", iniciado_em=INSTANTE,
                             duracao_ms=1, status_http=200,
                             paginas=[Pagina(1, "POST", BASE, ler_fixture("vip/busca_zero_resultados.html"))],
                             nivel_usado="script", tentativas=1, veredito=Veredito.OK)
    resultado = processar(resposta, CTX)
    assert resultado.quebra_suspeita is False
    assert resultado.lotes == []


def test_patio_vem_do_local_do_card(parser, ler_fixture):
    """Feature 003, D-69: o "Local:" do card vira o pátio do lote."""
    (lote,) = parser.extrair(ler_fixture("vip/busca_um_resultado.html"), CTX).lotes
    assert lote.patio == "SC"
