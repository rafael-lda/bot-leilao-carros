"""Cenários 9 a 11 do requirements.md §7, de ponta a ponta, sem rede."""

import httpx

from apoio import LEILOEIRO_VIP, escrever, pagina_vip
from bot_leilao.db.trava import Trava


def test_cenario_9_cadastro_de_leiloeiro_invalido_e_rejeitado(cenario):
    escrever(cenario.raiz / "config" / "leiloeiros.yaml",
             LEILOEIRO_VIP.replace("        filtros:\n          procedencia: 4\n          monta: 1\n",
                                   "        filtros: {}\n"))
    resultado = cenario.varrer()

    assert resultado.veredito == "falha"
    assert "Vip Leilões" in resultado.motivo and "Ampla" in resultado.motivo
    assert cenario.chamadas == [], "nenhuma requisição HTTP"


def test_cenario_10_execucao_que_falha_por_completo_fica_registrada(cenario):
    cenario.vip = httpx.ConnectError
    cenario.telegram = httpx.ConnectError
    resultado = cenario.varrer()

    assert resultado.veredito == "falha"
    assert resultado.motivo == "nenhuma_busca_coletada"
    vereditos = [r[0] for r in cenario.banco().execute("SELECT veredito FROM execucao_busca")]
    assert vereditos == ["falha_rede"]
    (execucao,) = cenario.execucoes()
    assert execucao["veredito"] == "falha"
    assert execucao["finalizado_em"] is not None


def test_falha_total_com_telegram_no_ar_manda_um_alerta_geral(cenario):
    """agendador-observabilidade EC-08: alerta único de falha geral."""
    cenario.vip = 503
    cenario.varrer()
    (alerta,) = cenario.mensagens
    assert "falha geral" in alerta


def test_cenario_11_segunda_execucao_simultanea_e_recusada(cenario, caplog):
    trava = Trava(cenario.raiz / "dados" / "varredura.lock", agora=cenario.agora)
    assert trava.adquirir()
    cenario.vip = pagina_vip()

    resultado = cenario.varrer()

    assert resultado.veredito == "recusada"
    assert resultado.codigo_saida == 3
    assert cenario.chamadas == [], "nada processado"
    (execucao,) = cenario.execucoes()
    assert (execucao["veredito"], execucao["motivo"]) == ("recusada", "trava_ocupada")
    assert any("recusada" in r.getMessage() for r in caplog.records), "recusa registrada em log"
    assert (cenario.raiz / "dados" / "varredura.lock").exists(), "a trava alheia continua lá"
    trava.liberar()


def test_trava_e_liberada_ao_fim_mesmo_com_erro(cenario, monkeypatch):
    from bot_leilao.filtro import fluxo

    def explodir(*_args, **_kwargs):
        raise RuntimeError("bug inesperado")

    monkeypatch.setattr(fluxo.FluxoFiltragem, "filtrar", explodir)
    cenario.vip = pagina_vip()
    resultado = cenario.varrer()

    assert resultado.veredito == "falha"
    assert "bug inesperado" in resultado.motivo
    assert not (cenario.raiz / "dados" / "varredura.lock").exists()
    assert cenario.execucoes()[-1]["finalizado_em"] is not None
