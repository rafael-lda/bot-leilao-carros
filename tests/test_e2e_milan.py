"""Cenários 1 a 4 do requirements da feature 005 (§7), mais RF-08 e RF-14, de ponta a ponta e sem rede."""

from datetime import datetime, timezone

import pytest

from apoio import (ALVO_CRETA, ALVO_VERSA_2018, BASE_MILAN, LEILOEIRO_MILAN, LEILOEIROS_VIP_E_MILAN, TOKEN_APIFY_TESTE,
                   ApifySimulado, CenarioE2E, item_milan, lote_milan_com_lance, paginas_milan_reais, pagina_vazia,
                   pagina_vip)

AGENDA = f"{BASE_MILAN}/agenda/veiculos"
CATALOGO = f"{BASE_MILAN}/leilao/15618/catalogo"
LOTE_046 = f"{BASE_MILAN}/leilao/15618/lote/046"
VESPERA = datetime(2026, 10, 13, 21, 0, tzinfo=timezone.utc)  # véspera do pregão de 14/10 09:30


def _cenario(raiz, relogio, agora, alvos=ALVO_CRETA, leiloeiros=LEILOEIRO_MILAN, token=True, **apify):
    agora.instante = VESPERA
    cenario = CenarioE2E(raiz, relogio, agora, alvos=alvos, leiloeiros=leiloeiros)
    cenario.apify = ApifySimulado(**apify)
    return cenario.com_token_apify() if token else cenario


def _catalogo_sem_creta():
    item = item_milan("catalogo_15618.json")
    assert "HYUNDAI CRETA ACTION" in item["content"]
    item["content"] = item["content"].replace("HYUNDAI CRETA ACTION", "HYUNDAI HB20 COMFORT")
    return item


def _semeado_sem_creta(raiz, relogio, agora, **kwargs):
    """Primeira varredura com o catálogo sem o Creta: a busca fica semeada sem nenhum candidato."""
    cenario = _cenario(raiz, relogio, agora, **kwargs)
    cenario.apify.paginas[CATALOGO] = _catalogo_sem_creta()
    cenario.varrer()
    assert cenario.mensagens == []
    cenario.apify.paginas[CATALOGO] = item_milan("catalogo_15618.json")
    return cenario


def test_cenario_1_so_o_leilao_de_financiamento_e_lido_pelo_apify(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora)
    resultado = cenario.varrer()

    assert resultado.veredito == "sucesso"
    assert cenario.apify.urls_pedidas() == [AGENDA, CATALOGO, LOTE_046], \
        "agenda, catálogo do 15618 (o judicial fica de fora) e o lance do único candidato"
    assert cenario.chamadas_milan_locais == [], "nenhuma requisição ao Milan sai do IP local"
    busca = cenario.banco().execute("SELECT nivel_usado, paginas, lotes_extraidos FROM execucao_busca").fetchone()
    assert (busca["nivel_usado"], busca["paginas"], busca["lotes_extraidos"]) == ("apify", 2, 243)


def test_cenario_2_creta_novo_avisado_com_km_cambio_patio_pregao_e_comitente(raiz, relogio, agora):
    cenario = _semeado_sem_creta(raiz, relogio, agora)
    cenario.apify.paginas[LOTE_046] = lote_milan_com_lance("046", "50.000,00")
    assert cenario.varrer().veredito == "sucesso"

    (digest,) = cenario.mensagens
    linhas = digest.split("\n")
    assert "1. HYUNDAI CRETA ACTION 1.6 FLEX 4P ANO 2022/2022 — 2022" in linhas
    assert "   R$ 50.000 — Milan Leilões — 99.020 km — automático — São Paulo - SP — Pregão 14/10 09:30" in linhas
    assert "   Obs.: IPVA 2026 PAGO · Comitente Banco Honda" in linhas
    assert f"   {LOTE_046}" in linhas
    assert cenario.notificados() == ["milan-leiloes:15618-046"]
    assert "- **Câmbio:** automático" in cenario.lista()


def test_rf14_creta_com_lance_acima_do_teto_no_detalhe_nao_e_avisado(raiz, relogio, agora):
    cenario = _semeado_sem_creta(raiz, relogio, agora)
    cenario.apify.paginas[LOTE_046] = lote_milan_com_lance("046", "70.000,00")
    cenario.varrer()
    assert cenario.mensagens == []
    assert cenario.notificados() == []


def test_cenario_3_sem_token_aborta_antes_da_rede(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, token=False)
    resultado = cenario.varrer()
    assert resultado.veredito == "falha"
    assert "APIFY_TOKEN" in resultado.motivo and "Milan Leilões" in resultado.motivo
    assert cenario.chamadas == [], "nenhuma requisição, nem ao Apify, nem ao Telegram"


def test_cenario_4_cota_esgotada_vira_alerta_e_o_vip_segue(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, alvos=ALVO_VERSA_2018, leiloeiros=LEILOEIROS_VIP_E_MILAN)
    cenario.vip = pagina_vazia()
    cenario.varrer()  # semeia as duas buscas
    cenario.vip = pagina_vip()
    cenario.apify.falha = "cota"

    resultado = cenario.varrer()

    assert resultado.veredito == "sucesso_parcial"
    assert any("Vip Leilões" in m and "lote novo" in m for m in cenario.mensagens)
    (alerta,) = cenario.alertas()
    assert "Milan Leilões" in alerta and "cota do Apify esgotada" in alerta
    assert len(cenario.apify.execucoes()) == 3, "2 na primeira varredura; a cota esgotada não é repetida"


def test_rf08_estreia_do_milan_semeia_e_lista_o_candidato_nos_documentos(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora)
    cenario.varrer()
    assert cenario.mensagens == [], "semeadura: nada no Telegram"
    lista = cenario.lista()
    assert "HYUNDAI CRETA ACTION 1.6 FLEX 4P ANO 2022/2022 — 2022" in lista
    assert "- **Câmbio:** automático" in lista
    assert "Comitente Banco Honda" in lista
    assert "| Milan Leilões | ok: 243 lote(s) lido(s)" in cenario.relatorio()


def test_token_do_apify_nunca_aparece_em_log_banco_ou_relatorio(raiz, relogio, agora, caplog):
    cenario = _cenario(raiz, relogio, agora, alvos=ALVO_VERSA_2018, leiloeiros=LEILOEIROS_VIP_E_MILAN, falha="token")
    cenario.varrer()
    assert TOKEN_APIFY_TESTE not in caplog.text
    assert all(TOKEN_APIFY_TESTE not in p.read_text(encoding="utf-8") for p in (raiz / "1OUTPUT").glob("*.md"))
    assert TOKEN_APIFY_TESTE not in "\n".join(cenario.banco().iterdump())
