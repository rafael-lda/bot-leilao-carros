"""Cenários do requirements da feature 002 (§7), de ponta a ponta, sem rede."""

import logging

import httpx

from apoio import (ALVO_FLUENCE, ALVO_VERSA, LEILOEIRO_KUSS, LEILOEIROS_VIP_E_KUSS, CenarioE2E, SiteKuss,
                   agenda_sem_financeiras, detalhe_kuss, json_kuss, lote_kuss, pagina_vazia, pagina_vip)

ALVO_DUSTER = """\
veiculos:
  - marca: Renault
    modelo: Duster
    ano_min: 2018
    ano_max: 2022
    preco_maximo: 59500
    tipos_leilao: [financiamento]
"""
DUSTER = lote_kuss(seq="283001", bem="RENAULT/DUSTER ICONIC 1.6 CVT", ano="21/22", valor="45.000,00")
OUTRO = lote_kuss(seq="283002", bem="FIAT/UNO WAY 1.0", ano="15/16")
LINK_DUSTER = "https://www.claudiokussleiloes.com.br/lance/897/0/283001"


def _cenario(raiz, relogio, agora, alvos=ALVO_DUSTER, leiloeiros=LEILOEIRO_KUSS, **site):
    cenario = CenarioE2E(raiz, relogio, agora, alvos=alvos, leiloeiros=leiloeiros)
    cenario.kuss = SiteKuss(**site)
    return cenario


def test_lotes_dos_dois_eventos_sao_lidos_e_conferidos(raiz, relogio, agora, caplog):
    cenario = _cenario(raiz, relogio, agora, eventos={"897": [[DUSTER, OUTRO]], "898": [[lote_kuss(seq="9")]]})
    with caplog.at_level(logging.WARNING, logger="bot_leilao"):
        resultado = cenario.varrer()
    assert resultado.veredito == "sucesso"
    assert [f["leilaoID"] for f in cenario.kuss.chamadas_op("P")] == ["897", "898"]
    assert cenario.execucoes()[-1]["lotes_vistos"] == 3
    assert "evento 89" not in caplog.text, "sem aviso de divergência entre total informado e lido"


def test_lote_que_casa_e_avisado_com_leiloeiro_ano_pregao_observacoes_e_link(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, eventos={"897": [[OUTRO]], "898": []})
    assert cenario.varrer().veredito == "sucesso"  # semeia a busca do Kuss
    assert cenario.mensagens == []

    cenario.kuss.eventos = {"897": [[OUTRO, DUSTER]], "898": []}
    cenario.kuss.detalhes = {"283001": detalhe_kuss(tblInformacoes="PARA-CHOQUE DIANTEIRO RISCADO")}
    resultado = cenario.varrer()

    assert resultado.veredito == "sucesso"
    (digest,) = cenario.mensagens
    assert "1. RENAULT/DUSTER ICONIC 1.6 CVT — 2022" in digest
    assert "R$ 45.000 — Claudio Kuss Leilões — Curitiba - PR — Pregão 13/10 10:00" in digest, "pátio: feature 003"
    assert "Obs.: PARA-CHOQUE DIANTEIRO RISCADO" in digest
    assert LINK_DUSTER in digest
    assert cenario.notificados() == ["claudio-kuss-leiloes:283001"]
    relatorio = sorted((raiz / "1OUTPUT").glob("*_varredura*.md"))[-1]
    assert "- **Despesas admin.:** R$ 2.750" in relatorio.read_text(encoding="utf-8")


def test_candidato_retirado_no_detalhe_nao_e_avisado(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, eventos={"897": [[OUTRO]], "898": []})
    cenario.varrer()
    cenario.kuss.eventos = {"897": [[OUTRO, DUSTER]], "898": []}
    cenario.kuss.detalhes = {"283001": detalhe_kuss(retirado="S")}
    resultado = cenario.varrer()

    assert resultado.veredito == "sucesso"
    assert cenario.mensagens == []
    assert cenario.execucoes()[-1]["descartados_retirados"] == 1
    assert cenario.notificados() == []


def test_sem_eventos_de_financeiras_nao_e_erro(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, agenda=agenda_sem_financeiras())
    resultado = cenario.varrer()
    assert resultado.veredito == "sucesso"
    assert resultado.alertas == []
    assert cenario.mensagens == []
    assert cenario.kuss.chamadas_op("Q") == []


def test_formato_alterado_vira_alerta_do_kuss(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, eventos={"897": [b"<html>Manutencao</html>"], "898": []})
    resultado = cenario.varrer()
    assert resultado.veredito == "sucesso_parcial"
    (alerta,) = cenario.mensagens
    assert "Claudio Kuss Leilões" in alerta


def test_kuss_fora_do_ar_nao_impede_o_aviso_do_vip(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, alvos=ALVO_VERSA, leiloeiros=LEILOEIROS_VIP_E_KUSS,
                       eventos={"897": [[OUTRO]], "898": []})
    cenario.vip = pagina_vazia()
    assert cenario.varrer().veredito == "sucesso"  # semeia as duas buscas

    cenario.vip = pagina_vip()
    cenario.kuss.falha = httpx.ConnectError
    resultado = cenario.varrer()

    assert resultado.veredito == "sucesso_parcial"
    digest = next(m for m in cenario.mensagens if "lote novo" in m)
    assert "Vip Leilões" in digest
    assert cenario.notificados() == ["vip-leiloes:400001"]


def test_primeira_varredura_semeia_o_kuss_sem_aviso_e_mostra_nos_documentos(raiz, relogio, agora):
    """RF-09, com a emenda E001 da 002: semeado sem aviso no Telegram, mas detalhado e listado nos .md."""
    cenario = _cenario(raiz, relogio, agora, alvos=ALVO_FLUENCE, eventos={"897": [[lote_kuss()]], "898": []},
                       detalhes={"282622": detalhe_kuss()})
    resultado = cenario.varrer()
    assert resultado.veredito == "sucesso"
    assert resultado.em_semeadura is True
    assert cenario.mensagens == []
    assert [f["le_id"] for f in cenario.kuss.chamadas_op("D")] == ["282622"]
    origens = [r["origem"] for r in cenario.banco().execute("SELECT origem FROM lote_conhecido")]
    assert origens == ["semeadura"]
    relatorio = next((raiz / "1OUTPUT").glob("*_varredura.md")).read_text(encoding="utf-8")
    assert "## Já estavam no site (semeadura)" in relatorio
    assert "- **Observações:** SINISTRADO" in relatorio
    lista = (raiz / "1OUTPUT" / "lotes-a-monitorar.md").read_text(encoding="utf-8")
    assert "<!-- lote: claudio-kuss-leiloes:282622 -->" in lista
    assert "### 1. IMP RENAULT/FLUENCE DYN 20A — 2013" in lista


def test_semeado_retirado_ou_sucata_e_registrado_mas_nao_aparece(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, alvos=ALVO_FLUENCE,
                       eventos={"897": [[lote_kuss(), lote_kuss(seq="282623")]], "898": []},
                       detalhes={"282622": detalhe_kuss(retirado="S"), "282623": json_kuss("detalhe_282327_sucata.json")})
    cenario.varrer()
    assert len(list(cenario.banco().execute("SELECT 1 FROM lote_conhecido"))) == 2, "ambos viram conhecidos"
    assert not (raiz / "1OUTPUT" / "lotes-a-monitorar.md").exists()
    relatorio = next((raiz / "1OUTPUT").glob("*_varredura.md")).read_text(encoding="utf-8")
    assert "## Já estavam no site" not in relatorio


def test_dry_run_nao_detalha_semeados(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, alvos=ALVO_FLUENCE, eventos={"897": [[lote_kuss()]], "898": []})
    cenario.varrer(dry_run=True)
    assert cenario.kuss.chamadas_op("D") == []
