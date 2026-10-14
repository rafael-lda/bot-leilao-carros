"""Antecedência, consumo e alertas do Apify (feature 005: RF-06, RF-09, RF-13; roadmap D-91, D-102, D-103)."""

from datetime import datetime, timezone

from apoio import (ALVO_VERSA, ATOR_PADRAO_TESTE, BASE_MILAN, LEILOEIRO_MILAN, LEILOEIROS_VIP_E_MILAN, ApifySimulado,
                   CenarioE2E, item_milan, pagina_vazia)

VESPERA = datetime(2026, 10, 13, 21, 0, tzinfo=timezone.utc)
AGENDA = f"{BASE_MILAN}/agenda/veiculos"


def _cenario(raiz, relogio, agora, leiloeiros=LEILOEIROS_VIP_E_MILAN, quando=VESPERA, **apify):
    agora.instante = quando
    cenario = CenarioE2E(raiz, relogio, agora, alvos=ALVO_VERSA, leiloeiros=leiloeiros)
    cenario.apify = ApifySimulado(**apify)
    cenario.vip = pagina_vazia()
    return cenario.com_token_apify()


def _leilao_novo_15700(cenario):
    """A agenda passa a anunciar o 15700 (pregão 20/10 09:30) no lugar do 15618; catálogo igual, com a data nova."""
    agenda = item_milan("agenda.json")
    agenda["content"] = (agenda["content"].replace("/leilao/veiculos/15618", "/leilao/veiculos/15700")
                         .replace("14 de OUT", "20 de OUT"))
    catalogo = item_milan("catalogo_15618.json")
    catalogo["content"] = catalogo["content"].replace("14 OUT 09:30", "20 OUT 09:30")
    cenario.apify.paginas[AGENDA] = agenda
    cenario.apify.paginas[f"{BASE_MILAN}/leilao/15700/catalogo"] = catalogo


def _eventos(cenario):
    return {r["evento_id"]: r for r in cenario.banco().execute("SELECT * FROM evento_visto")}


def test_leiloes_da_primeira_leitura_ficam_marcados_e_nao_contam(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora)
    cenario.varrer()
    evento = _eventos(cenario)["15618"]
    assert evento["leiloeiro_id"] == "milan-leiloes"
    assert evento["na_semeadura"] == 1
    assert "leilão novo" not in cenario.relatorio()


def test_leilao_novo_aparece_com_a_antecedencia(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora)
    cenario.varrer()
    _leilao_novo_15700(cenario)
    cenario.varrer()
    assert _eventos(cenario)["15700"]["na_semeadura"] == 0
    assert "leilão novo 15700, visto 6 dia(s) antes do pregão" in cenario.relatorio()
    assert cenario.alertas() == [], "sem intervalo_horas, nenhum alerta de antecedência"


def test_antecedencia_menor_que_o_intervalo_gera_alerta(raiz, relogio, agora):
    leiloeiros = LEILOEIROS_VIP_E_MILAN.replace("    nivel_coleta: apify\n",
                                                "    nivel_coleta: apify\n    intervalo_horas: 200\n")
    cenario = _cenario(raiz, relogio, agora, leiloeiros=leiloeiros, quando=datetime(2026, 10, 5, 11, 0,
                                                                                     tzinfo=timezone.utc))
    cenario.varrer()
    agora.instante = VESPERA  # 8 dias depois: fora do intervalo de 200 h
    _leilao_novo_15700(cenario)
    cenario.varrer()
    (alerta,) = cenario.alertas()
    assert "Milan Leilões" in alerta
    assert "leilão 15700 com 6 dia(s) de antecedência, menos que o intervalo de 200 h" in alerta
    assert "intervalo_horas" in alerta and "config/leiloeiros.yaml" in alerta


def test_consumo_do_apify_na_linha_do_leiloeiro(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, leiloeiros=LEILOEIRO_MILAN, uso=0.39)
    cenario.varrer()
    relatorio = cenario.relatorio()
    assert "Apify: 2 página(s), US$ 0,16 nesta varredura; ciclo US$ 0,55 de 5,00 até 17/10" in relatorio


def test_consumo_indisponivel_nao_derruba_a_varredura(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, leiloeiros=LEILOEIRO_MILAN)
    cenario.apify.limites_falham = True
    assert cenario.varrer().veredito == "sucesso"
    assert "consumo indisponível" in cenario.relatorio()


def test_alerta_quando_o_ciclo_passa_de_80_porcento_uma_vez_por_dia(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, uso=3.95)
    cenario.varrer()
    (alerta,) = cenario.alertas()
    assert "Apify" in alerta and "80%" in alerta and "US$ 4,11 de 5,00" in alerta
    cenario.varrer()
    assert len(cenario.alertas()) == 1, "no máximo 1 por dia"


def test_alerta_de_token_invalido(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, falha="token")
    assert cenario.varrer().veredito == "sucesso_parcial"
    (alerta,) = cenario.alertas()
    assert "Milan Leilões" in alerta and "token do Apify inválido" in alerta and "APIFY_TOKEN" in alerta


def test_desafio_nao_resolvido_usa_o_alerta_de_bloqueio_citando_o_ator(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, falha="desafio")
    cenario.varrer()
    (alerta,) = cenario.alertas()
    assert "o site bloqueou o acesso do bot" in alerta
    assert f"via apify: {ATOR_PADRAO_TESTE}" in alerta


def test_plataforma_fora_alerta_com_a_causa(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, falha="plataforma")
    cenario.varrer()
    (alerta,) = cenario.alertas()
    assert "Milan Leilões" in alerta and "plataforma do Apify indisponível" in alerta
