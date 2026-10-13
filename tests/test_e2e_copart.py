"""Cenários do requirements da feature 003 (§7), de ponta a ponta, sem rede."""

import logging

from apoio import (ALVO_VERSA, LEILOEIRO_COPART, LEILOEIRO_KUSS, LEILOEIRO_VIP, LEILOEIROS_VIP_E_COPART, CenarioE2E,
                   SiteCopart, SiteKuss, lote_copart, lote_kuss, pagina_vazia, pagina_vip)

ALVO_DUSTER_SEM_OROCH = """\
veiculos:
  - marca: Renault
    modelo: Duster
    ano_min: 2018
    ano_max: 2022
    preco_maximo: 59500
    tipos_leilao: [financiamento]
    excluir: [Oroch]
"""
VERSA_MS = dict(ln=1176233, la="62000.00", hb=25000.0)
LINK_VERSA = "https://www.copart.com.br/lotDetail/1176233"


def _cenario(raiz, relogio, agora, alvos=ALVO_VERSA, leiloeiros=LEILOEIRO_COPART, **site):
    cenario = CenarioE2E(raiz, relogio, agora, alvos=alvos, leiloeiros=leiloeiros)
    cenario.copart = SiteCopart(**site)
    return cenario


def _muitos(n):
    return [lote_copart(ln=500000 + i, lm="UNO", mkn="FIAT") for i in range(n)]


def test_todas_as_paginas_sao_lidas_e_conferidas(raiz, relogio, agora, caplog):
    cenario = _cenario(raiz, relogio, agora, lotes=_muitos(250))
    with caplog.at_level(logging.WARNING, logger="bot_leilao"):
        resultado = cenario.varrer()
    assert resultado.veredito == "sucesso"
    assert [b["page"] for b in cenario.copart.buscas()] == ["0", "1", "2"]
    assert cenario.execucoes()[-1]["lotes_vistos"] == 250
    assert "repetid" not in caplog.text and "informou" not in caplog.text


def test_lote_que_casa_e_avisado_com_patio_fipe_e_link(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, lotes=_muitos(3))
    assert cenario.varrer().veredito == "sucesso"  # semeia a busca da Copart
    assert cenario.mensagens == []

    cenario.copart.lotes = _muitos(3) + [lote_copart(**VERSA_MS)]
    resultado = cenario.varrer()

    assert resultado.veredito == "sucesso"
    (digest,) = cenario.mensagens
    assert "1. NISSAN VERSA 1.6 16V — 2019" in digest
    assert "R$ 25.000 — Copart — CAMPO GRANDE - MS — FIPE R$ 62.000" in digest
    assert LINK_VERSA in digest
    assert cenario.notificados() == ["copart:1176233"]


def test_todo_aviso_mostra_o_patio(raiz, relogio, agora):
    leiloeiros = LEILOEIRO_VIP + LEILOEIRO_KUSS.removeprefix("leiloeiros:\n") + LEILOEIRO_COPART.removeprefix(
        "leiloeiros:\n")
    cenario = _cenario(raiz, relogio, agora, leiloeiros=leiloeiros, lotes=[])
    cenario.vip = pagina_vazia()
    cenario.kuss = SiteKuss(eventos={"897": [[lote_kuss(seq="9", bem="FIAT/UNO", ano="15/16")]], "898": []})
    assert cenario.varrer().veredito == "sucesso"  # semeia as três buscas

    cenario.vip = pagina_vip()
    cenario.kuss.eventos = {"897": [[lote_kuss(seq="10", bem="NISSAN/VERSA 1.6 SL", ano="18/19")]], "898": []}
    cenario.copart.lotes = [lote_copart(**VERSA_MS)]
    cenario.varrer()

    (digest,) = cenario.mensagens
    assert "3 lotes novos" in digest
    assert "Vip Leilões — 228.227 km — SC" in digest
    assert "Claudio Kuss Leilões — Curitiba - PR" in digest
    assert "Copart — CAMPO GRANDE - MS" in digest


def test_copart_bloqueando_nao_impede_o_vip_e_gera_alerta(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, leiloeiros=LEILOEIROS_VIP_E_COPART, lotes=[])
    cenario.vip = pagina_vazia()
    assert cenario.varrer().veredito == "sucesso"

    cenario.vip = pagina_vip()
    cenario.copart.desafio = 200
    resultado = cenario.varrer()

    assert resultado.veredito == "sucesso_parcial"
    digest = next(m for m in cenario.mensagens if "lote novo" in m)
    assert "Vip Leilões" in digest
    alerta = next(m for m in cenario.mensagens if "Alerta" in m)
    assert "Copart" in alerta and "bloque" in alerta.lower()
    busca = cenario.banco().execute("SELECT veredito, motivo FROM execucao_busca WHERE leiloeiro_id='copart' "
                                    "ORDER BY iniciado_em DESC").fetchone()
    assert (busca["veredito"], busca["motivo"]) == ("bloqueado", "pagina 1: desafio_antibot")
    relatorio = sorted((raiz / "1OUTPUT").glob("*_varredura*.md"))[-1].read_text(encoding="utf-8")
    assert "| Copart | bloqueado pelo site (pagina 1: desafio_antibot) |" in relatorio
    assert "| Vip Leilões | ok: 1 lote(s) lido(s) |" in relatorio


def test_alerta_de_bloqueio_no_maximo_um_por_dia(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, leiloeiros=LEILOEIROS_VIP_E_COPART, desafio=403)
    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.varrer()
    assert sum(1 for m in cenario.mensagens if "Alerta" in m) == 1


def test_formato_alterado_vira_alerta_da_copart(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, corpo=b'{"returnCode":1,"data":{}}')
    resultado = cenario.varrer()
    assert resultado.veredito == "sucesso_parcial"
    (alerta,) = cenario.mensagens
    assert "Copart" in alerta


def test_duster_oroch_excluida_pelo_alvo(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, alvos=ALVO_DUSTER_SEM_OROCH, lotes=[])
    cenario.varrer()
    cenario.copart.lotes = [lote_copart(ln=1141180), lote_copart(ln=2000, lm="DUSTER", hb=40000.0)]
    cenario.varrer()
    (digest,) = cenario.mensagens
    assert "lotDetail/2000" in digest
    assert "OROCH" not in digest


def test_busca_nao_passa_pela_pagina_html(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, lotes=[])
    cenario.varrer()
    assert all(caminho == "/public/vehicleFinder/search" for _, caminho, _ in cenario.copart.chamadas)


def test_estreia_da_copart_lista_os_semeados_com_patio(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, lotes=[lote_copart(ln=1176233)])
    assert cenario.varrer().em_semeadura is True
    assert cenario.mensagens == []
    relatorio = next((raiz / "1OUTPUT").glob("*_varredura.md")).read_text(encoding="utf-8")
    assert "## Já estavam no site (semeadura)" in relatorio
    assert "- **Pátio:** CAMPO GRANDE - MS" in relatorio
    lista = (raiz / "1OUTPUT" / "lotes-a-monitorar.md").read_text(encoding="utf-8")
    assert "<!-- lote: copart:1176233 -->" in lista
