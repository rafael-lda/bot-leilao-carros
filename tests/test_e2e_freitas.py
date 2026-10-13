"""Cenários do requirements da feature 004 (§7), de ponta a ponta, sem rede."""

from apoio import (LEILOEIRO_FREITAS, LEILOEIROS_VIP_E_FREITAS, ALVO_VERSA, CenarioE2E, SiteFreitas, card_freitas,
                   pagina_vazia, pagina_vip)

ALVO_DUSTER_ATE_2024 = """\
veiculos:
  - marca: Renault
    modelo: Duster
    ano_min: 2018
    ano_max: 2024
    preco_maximo: 59500
    tipos_leilao: [financiamento]
"""
UNO = "FIAT/UNO WAY, 15/16, PLACA: A__-___1, GASOL/ALC, PRATA"
LINK_DUSTER = "https://www.freitasleiloeiro.com.br/Leiloes/LoteDetalhes?leilaoId=8112&loteNumero=1"


def _cenario(raiz, relogio, agora, alvos=ALVO_DUSTER_ATE_2024, leiloeiros=LEILOEIRO_FREITAS, **site):
    cenario = CenarioE2E(raiz, relogio, agora, alvos=alvos, leiloeiros=leiloeiros)
    cenario.freitas = SiteFreitas(**site)
    return cenario


def _unos(n):
    return [card_freitas(lote=f"9000/{i}", desc=UNO) for i in range(1, n + 1)]


def test_le_ate_a_mensagem_de_fim_sem_repeticao(raiz, relogio, agora, caplog):
    cenario = _cenario(raiz, relogio, agora, cards=_unos(250))
    assert cenario.varrer().veredito == "sucesso"
    assert [b["PageNumber"] for b in cenario.freitas.buscas()] == ["1", "2", "3"]
    assert cenario.execucoes()[-1]["lotes_vistos"] == 250
    assert "repetid" not in caplog.text


def test_lote_de_financeira_que_casa_e_avisado_com_patio_pregao_e_link(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, cards=_unos(2))
    cenario.varrer()  # semeia
    assert cenario.mensagens == []

    cenario.freitas.cards = _unos(2) + [card_freitas("8112/1")]
    resultado = cenario.varrer()

    assert resultado.veredito == "sucesso"
    (digest,) = cenario.mensagens
    assert "1. RENAULT/DUSTER INTP CVT — 2024" in digest
    assert "R$ 50.500 — Freitas Leiloeiro — SANTO ANDRE - SP — Pregão 16/10 10:00" in digest
    assert "Obs.: IPVA 2026 PAGO" in digest
    assert LINK_DUSTER in digest
    assert cenario.notificados() == ["freitas-leiloeiro:8112-1"]


def test_lote_sem_etiqueta_de_financeira_nao_e_avisado(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, cards=_unos(1))
    cenario.varrer()
    cenario.freitas.cards = _unos(1) + [card_freitas("8112/1", etiqueta="")]
    cenario.varrer()
    assert cenario.mensagens == []


def test_lote_em_loteamento_nunca_vira_candidato(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, cards=_unos(1))
    cenario.varrer()
    cenario.freitas.cards = _unos(1) + [card_freitas("8111/700", desc="RENAULT/DUSTER INTP CVT, 23/24, PLACA: S__-___4,"
                                                                       " GASOL/ALC, PRATA")]
    cenario.varrer()
    assert cenario.mensagens == []


def test_freitas_bloqueando_nao_derruba_o_vip_e_gera_alerta(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, alvos=ALVO_VERSA, leiloeiros=LEILOEIROS_VIP_E_FREITAS, cards=[])
    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.vip = pagina_vip()
    cenario.freitas.bloqueio = 403
    resultado = cenario.varrer()
    assert resultado.veredito == "sucesso_parcial"
    assert any("Vip Leilões" in m and "lote novo" in m for m in cenario.mensagens)
    alerta = next(m for m in cenario.mensagens if "Alerta" in m)
    assert "Freitas Leiloeiro" in alerta and "bloque" in alerta.lower()


def test_falha_de_certificado_gera_alerta_que_aponta_o_runbook(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, alvos=ALVO_VERSA, leiloeiros=LEILOEIROS_VIP_E_FREITAS,
                       certificado_invalido=True)
    cenario.vip = pagina_vazia()
    resultado = cenario.varrer()
    assert resultado.veredito == "sucesso_parcial"
    assert len(cenario.freitas.chamadas) == 1, "certificado inválido não se resolve tentando de novo"
    (alerta,) = [m for m in cenario.mensagens if "Alerta" in m]
    assert "Freitas Leiloeiro" in alerta and "certificado" in alerta
    assert "src/bot_leilao/coleta/certificados/LEIA-ME.md" in alerta
    relatorio = sorted((raiz / "1OUTPUT").glob("*_varredura*.md"))[-1].read_text(encoding="utf-8")
    assert "| Freitas Leiloeiro | falha de acesso (pagina 1: certificado: www.freitasleiloeiro.com.br) |" in relatorio


def test_alerta_de_certificado_no_maximo_um_por_dia(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, alvos=ALVO_VERSA, leiloeiros=LEILOEIROS_VIP_E_FREITAS,
                       certificado_invalido=True)
    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.varrer()
    assert sum(1 for m in cenario.mensagens if "Alerta" in m) == 1


def test_estreia_lista_os_semeados_com_patio_e_despesas(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, cards=[card_freitas("8112/1")])
    assert cenario.varrer().em_semeadura is True
    assert cenario.mensagens == []
    assert cenario.freitas.detalhes_pedidos() == ["8112-1"]
    lista = (raiz / "1OUTPUT" / "lotes-a-monitorar.md").read_text(encoding="utf-8")
    assert "### 1. RENAULT/DUSTER INTP CVT — 2024" in lista
    assert "- **Pátio:** SANTO ANDRE - SP" in lista
    assert "- **Despesas admin.:** R$ 2.350" in lista
    assert "- **Documento:** Placa S\\_\\_-\\_\\_\\_4" in lista
