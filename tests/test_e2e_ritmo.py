"""Varredura sem pagos e intervalo por leiloeiro (feature 005: RF-11, RF-12, cenário 5; roadmap D-100, D-101)."""

from datetime import datetime, timedelta, timezone

from apoio import (ALVO_VERSA, BASE_MILAN, FUSO_SP, LEILOEIROS_VIP_E_MILAN, ApifySimulado, CenarioE2E, pagina_vazia,
                   pagina_vip)

VESPERA = datetime(2026, 10, 13, 21, 0, tzinfo=timezone.utc)
SEM_PAGOS = "| Milan Leilões | não incluído nesta varredura (sem pagos) |"


def _cenario(raiz, relogio, agora, leiloeiros=LEILOEIROS_VIP_E_MILAN, token=True):
    agora.instante = VESPERA
    cenario = CenarioE2E(raiz, relogio, agora, alvos=ALVO_VERSA, leiloeiros=leiloeiros)
    cenario.apify = ApifySimulado()
    cenario.vip = pagina_vazia()
    return cenario.com_token_apify() if token else cenario


def _com_intervalo(horas: int) -> str:
    return LEILOEIROS_VIP_E_MILAN.replace("    nivel_coleta: apify\n", f"    nivel_coleta: apify\n    intervalo_horas: {horas}\n")


def test_cenario_5_sem_pagos_nao_chama_o_apify_nem_exige_token(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, token=False)
    cenario.varrer()  # semeia o Vip
    cenario.vip = pagina_vip()

    resultado = cenario.varrer(sem_pagos=True)

    assert resultado.veredito == "sucesso"
    assert cenario.apify.chamadas == []
    assert SEM_PAGOS in cenario.relatorio(), "aparece só na seção Leiloeiros do relatório"
    assert "Milan" not in cenario.lista()
    assert cenario.alertas() == []
    assert all("Milan" not in m for m in cenario.mensagens)
    assert any("Vip Leilões" in m for m in cenario.mensagens)


def test_sem_pagos_nao_conta_como_leitura_para_o_intervalo(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, leiloeiros=_com_intervalo(72))
    cenario.varrer(sem_pagos=True)
    cenario.varrer()
    assert len(cenario.apify.execucoes()) == 2, "a primeira leitura de verdade acontece na segunda varredura"


def test_intervalo_pula_o_leiloeiro_lido_ha_pouco_e_le_depois(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, leiloeiros=_com_intervalo(72))
    cenario.varrer()
    primeira_leitura = agora()
    assert len(cenario.apify.execucoes()) == 2

    agora.avancar(hours=48)
    cenario.varrer()
    assert len(cenario.apify.execucoes()) == 2, "dentro das 72 h: nenhuma página paga"
    proxima = (primeira_leitura + timedelta(hours=72)).astimezone(FUSO_SP)
    assert (f"| Milan Leilões | pulado pelo intervalo de 72 h (próxima leitura a partir de "
            f"{proxima:%d/%m %H:%M}) |") in cenario.relatorio()
    assert cenario.alertas() == []

    agora.avancar(hours=25)
    cenario.varrer()
    assert len(cenario.apify.execucoes()) == 4


def test_dry_run_nao_conta_como_leitura(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, leiloeiros=_com_intervalo(72))
    cenario.varrer(dry_run=True)
    cenario.varrer()
    assert len(cenario.apify.execucoes()) == 4


def test_so_o_milan_pulado_nao_exige_token(raiz, relogio, agora):
    cenario = _cenario(raiz, relogio, agora, leiloeiros=_com_intervalo(72))
    cenario.varrer()
    cenario.deps.environ = {k: v for k, v in cenario.deps.environ.items() if k != "APIFY_TOKEN"}
    agora.avancar(hours=1)
    assert cenario.varrer().veredito == "sucesso"
