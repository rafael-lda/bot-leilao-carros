"""Cenários 1 a 4 do requirements.md §7, de ponta a ponta, sem rede."""

from apoio import pagina_vazia, pagina_vip


def test_cenario_1_primeira_execucao_popula_a_base_sem_notificar(cenario):
    cenario.vip = pagina_vip()
    resultado = cenario.varrer()

    assert resultado.veredito == "sucesso"
    assert resultado.codigo_saida == 0
    assert cenario.mensagens == [], "nenhuma mensagem na semeadura (RN-07)"
    con = cenario.banco()
    assert [r["origem"] for r in con.execute("SELECT origem FROM lote_conhecido")] == ["semeadura"]
    assert con.execute("SELECT COUNT(*) FROM busca_semeada").fetchone()[0] == 1
    (execucao,) = cenario.execucoes()
    assert execucao["finalizado_em"] is not None
    assert (execucao["lotes_vistos"], execucao["lotes_candidatos"], execucao["lotes_novos"],
            execucao["lotes_semeados"]) == (1, 1, 0, 1)


def test_cenario_2_lote_novo_gera_digest(cenario):
    cenario.vip = pagina_vazia()
    assert cenario.varrer().veredito == "sucesso"  # semeia a busca, ainda sem lotes

    notificados_no_envio = []
    cenario.ao_enviar = lambda: notificados_no_envio.append(cenario.notificados())
    cenario.vip = pagina_vip(titulo="VERSA 1.6 SV - 2017/2018", valor_atual="R$ 41.900,00")
    resultado = cenario.varrer()

    assert resultado.veredito == "sucesso"
    (digest,) = cenario.mensagens
    assert "1 lote novo" in digest
    assert "Nissan Versa 1.6 Sv — 2018" in digest, "marca, modelo e ano de modelo"
    assert "R$ 41.900 — Vip Leilões" in digest, "preço e leiloeiro"
    assert "https://www.vipleiloes.com.br/evento/anuncio/nissan-versa-16-sv-400001" in digest
    assert notificados_no_envio == [[]], "nada gravado antes da confirmação (RN-06)"
    assert cenario.notificados() == ["vip-leiloes:400001"]
    assert cenario.execucoes()[-1]["digest_enviado"] == 1


def test_cenario_3_lote_acima_do_teto_nao_e_notificado(cenario):
    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.vip = pagina_vip(valor_inicial="R$ 30.000,00", valor_atual="R$ 52.000,00")
    resultado = cenario.varrer()

    assert resultado.veredito == "sucesso"
    assert cenario.mensagens == []
    assert cenario.execucoes()[-1]["lotes_candidatos"] == 0


def test_cenario_4_execucao_repetida_nao_renotifica(cenario):
    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.vip = pagina_vip()
    cenario.varrer()
    assert len(cenario.mensagens) == 1

    cenario.varrer()
    assert len(cenario.mensagens) == 1, "nenhuma mensagem nova"
    ultima = cenario.execucoes()[-1]
    assert ultima["lotes_novos"] == 0
    assert ultima["lotes_ja_conhecidos"] == 1


def test_retirado_nao_e_notificado(cenario):
    """RN-12 / RF-17 de ponta a ponta."""
    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.vip = pagina_vip(situacao="Lote Retirado")
    cenario.varrer()
    assert cenario.mensagens == []
    assert cenario.execucoes()[-1]["descartados_retirados"] == 1


def test_dry_run_nao_envia_nem_grava(cenario):
    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.vip = pagina_vip()
    resultado = cenario.varrer(dry_run=True)

    assert cenario.mensagens == []
    assert cenario.notificados() == []
    assert len(resultado.digest) == 1 and "Versa" in resultado.digest[0]
    assert cenario.execucoes()[-1]["modo"] == "dry_run"


def test_dry_run_na_estreia_avisa_semeadura_e_nao_semeia(cenario):
    cenario.vip = pagina_vip()
    resultado = cenario.varrer(dry_run=True)
    assert resultado.em_semeadura is True
    assert resultado.digest == []
    assert len(resultado.candidatos) == 1
    assert cenario.banco().execute("SELECT COUNT(*) FROM busca_semeada").fetchone()[0] == 0


def test_sem_alvo_ativo_termina_com_sucesso_sem_varrer(cenario):
    """RF-01 da feature (A006)."""
    from apoio import ALVO_VERSA, escrever

    escrever(cenario.raiz / "config" / "veiculos-alvo.yaml", ALVO_VERSA + "    ativo: false\n")
    resultado = cenario.varrer()
    assert resultado.veredito == "sucesso"
    assert cenario.chamadas == []


def _cenario_com_teto_de_km(raiz, relogio, agora):
    from apoio import ALVO_VERSA, CenarioE2E

    return CenarioE2E(raiz, relogio, agora, alvos=ALVO_VERSA + "    quilometragem_maxima: 120000\n")


def test_km_sentinela_nao_esconde_o_carro_com_teto_de_km(raiz, relogio, agora):
    """Roadmap D-32: com teto de 120.000, um lote com km 999.999 (não informada) ainda é notificado."""
    cenario = _cenario_com_teto_de_km(raiz, relogio, agora)
    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.vip = pagina_vip(km="999.999 Km")
    cenario.varrer()
    (digest,) = cenario.mensagens
    assert "Versa" in digest
    assert "999.999" not in digest, "o resumo não pode exibir a km sentinela como se fosse real"


def test_km_real_acima_do_teto_continua_eliminada(raiz, relogio, agora):
    cenario = _cenario_com_teto_de_km(raiz, relogio, agora)
    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.vip = pagina_vip(km="167.387 Km")
    cenario.varrer()
    assert cenario.mensagens == []
    assert cenario.execucoes()[-1]["lotes_candidatos"] == 0


# --- Emenda E001: relatório Markdown por varredura -------------------------------------------

def _relatorios(cenario):
    pasta = cenario.raiz / "1OUTPUT"
    return sorted(pasta.glob("*.md")) if pasta.exists() else []


def test_cada_varredura_gera_um_relatorio_so_com_os_lotes_novos(cenario):
    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.vip = pagina_vip()
    cenario.varrer()
    cenario.varrer()

    estreia, com_novo, repetida = [p.read_text(encoding="utf-8") for p in _relatorios(cenario)]
    assert "Nenhum lote novo nesta varredura." in estreia
    assert "### 1. Nissan Versa 1.6 Sv — 2018" in com_novo
    assert "| Telegram | enviado |" in com_novo
    assert "Versa" not in repetida, "lote já avisado não aparece de novo"
    assert "Nenhum lote novo nesta varredura." in repetida


def test_dry_run_nao_gera_relatorio(cenario):
    cenario.vip = pagina_vip()
    cenario.varrer(dry_run=True)
    assert _relatorios(cenario) == []


def test_varredura_com_falha_tambem_gera_relatorio(cenario):
    import httpx

    cenario.vip = httpx.ConnectError
    cenario.varrer()
    (relatorio,) = _relatorios(cenario)
    texto = relatorio.read_text(encoding="utf-8")
    assert "| Veredito | falha |" in texto
    assert "| Motivo | nenhuma_busca_coletada |" in texto


def test_execucao_recusada_pela_trava_nao_gera_relatorio(cenario):
    from bot_leilao.db.trava import Trava

    trava = Trava(cenario.raiz / "dados" / "varredura.lock", agora=cenario.agora)
    trava.adquirir()
    try:
        cenario.varrer()
    finally:
        trava.liberar()
    assert _relatorios(cenario) == []


def test_relatorio_nao_contem_o_token(cenario):
    from apoio import TOKEN_TESTE

    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.vip = pagina_vip()
    cenario.telegram = 401
    cenario.varrer()
    for relatorio in _relatorios(cenario):
        assert TOKEN_TESTE not in relatorio.read_text(encoding="utf-8")


def test_falha_ao_gravar_relatorio_nao_derruba_a_varredura(cenario):
    (cenario.raiz / "1OUTPUT").write_text("um arquivo no lugar da pasta", encoding="utf-8")
    cenario.vip = pagina_vazia()
    assert cenario.varrer().veredito == "sucesso"
