"""Relatório Markdown por varredura (emenda E001 do requirements da feature 001)."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from apoio import alvo, lote
from bot_leilao.filtro.motor import Candidato
from bot_leilao.notificacao.relatorio import DadosRelatorio, gravar_relatorio, lote_de, montar_relatorio

SP = timezone(timedelta(hours=-3))
INICIO = datetime(2026, 10, 8, 19, 37, 9, tzinfo=SP)
LINK = "https://www.vipleiloes.com.br/evento/anuncio/nissan-versa-excl-cvt-315452"


def _candidato(**campos):
    padrao = dict(titulo="Nissan Versa Excl Cvt", ano_modelo=2024, lance_corrente=Decimal("61000"),
                  lance_inicial=Decimal("12000"), quilometragem=35647, link=LINK)
    padrao.update(campos)
    return Candidato(lote=lote(**padrao), alvo=alvo(id="nissan-versa-2023-2024", preco_maximo=Decimal("69300")),
                     preco_a_confirmar=False, km_a_confirmar=False)


def _dados(**campos):
    padrao = dict(inicio=INICIO, duracao_s=216, veredito="sucesso", motivo=None,
                  novos=[lote_de(_candidato(), "Vip Leilões")], telegram="enviado", semeados=0, em_semeadura=False)
    padrao.update(campos)
    return DadosRelatorio(**padrao)


def test_cabecalho_com_data_hora_veredito_e_duracao():
    texto = montar_relatorio(_dados())
    assert texto.startswith("# Varredura de 08/10/2026 19:37\n")
    assert "| Data | 08/10/2026 |" in texto
    assert "| Hora | 19:37 |" in texto
    assert "| Veredito | sucesso |" in texto
    assert "| Duração | 3m36s |" in texto
    assert "| Lotes novos | 1 |" in texto
    assert "| Telegram | enviado |" in texto


def test_lote_novo_com_os_dados_para_a_analise_da_fipe():
    texto = montar_relatorio(_dados())
    assert "### 1. Nissan Versa Excl Cvt — 2024" in texto
    assert "- **Lance atual:** R$ 61.000" in texto
    assert "- **Leiloeiro:** Vip Leilões" in texto
    assert "- **Km:** 35.647 km" in texto
    assert f"- **Link:** {LINK}" in texto
    assert "- **Alvo:** nissan-versa-2023-2024 (teto R$ 69.300)" in texto
    assert "- **Análise FIPE:** _pendente_" in texto


def test_lote_sem_lance_mostra_o_lance_inicial():
    novo = lote_de(_candidato(lance_corrente=None, lance_inicial=Decimal("30000")), "Vip Leilões")
    assert "- **Lance inicial (ainda sem lances):** R$ 30.000" in montar_relatorio(_dados(novos=[novo]))


def test_km_desconhecida_e_omitida():
    novo = lote_de(_candidato(quilometragem=None), "Vip Leilões")
    assert "**Km:**" not in montar_relatorio(_dados(novos=[novo]))


def test_sem_lotes_novos_diz_isso_e_nao_lista_nada():
    texto = montar_relatorio(_dados(novos=[], telegram=None))
    assert "| Lotes novos | 0 |" in texto
    assert "Nenhum lote novo nesta varredura." in texto
    assert "###" not in texto
    assert "| Telegram | nada a enviar |" in texto


def test_semeadura_e_explicada():
    texto = montar_relatorio(_dados(novos=[], telegram=None, semeados=3, em_semeadura=True))
    assert "semeadura" in texto
    assert "3 lote(s)" in texto


def test_falha_mostra_o_motivo():
    texto = montar_relatorio(_dados(veredito="falha", motivo="nenhuma_busca_coletada", novos=[], telegram=None))
    assert "| Veredito | falha |" in texto
    assert "| Motivo | nenhuma_busca_coletada |" in texto


def test_envio_falho_avisa_que_os_lotes_voltam():
    texto = montar_relatorio(_dados(veredito="falha", motivo="envio_digest: timeout",
                                    telegram="não enviado: timeout ao falar com o Telegram"))
    assert "| Telegram | não enviado: timeout ao falar com o Telegram |" in texto
    assert "voltam na próxima varredura" in texto


def test_texto_do_site_nao_quebra_o_markdown():
    novo = lote_de(_candidato(titulo="Fiat *Uno* | Cia_1"), "Vip Leilões")
    assert "Fiat \\*Uno\\* \\| Cia\\_1" in montar_relatorio(_dados(novos=[novo]))


def test_grava_com_nome_pela_data_e_hora_e_cria_a_pasta(tmp_path):
    caminho = gravar_relatorio(tmp_path / "1OUTPUT", _dados())
    assert caminho == tmp_path / "1OUTPUT" / "2026-10-08_19h37_varredura.md"
    assert caminho.read_text(encoding="utf-8") == montar_relatorio(_dados())


def test_nunca_sobrescreve_relatorio_existente(tmp_path):
    """O Rafael anota a análise FIPE nos relatórios; um arquivo anotado jamais pode ser perdido."""
    primeiro = gravar_relatorio(tmp_path, _dados())
    primeiro.write_text("ANOTADO PELO RAFAEL", encoding="utf-8")
    segundo = gravar_relatorio(tmp_path, _dados())
    assert segundo.name == "2026-10-08_19h37_varredura_2.md"
    assert primeiro.read_text(encoding="utf-8") == "ANOTADO PELO RAFAEL"


# --- Emenda E002: lista acumulada de lotes a monitorar ----------------------------------------

from bot_leilao.notificacao.relatorio import acrescentar_monitoramento  # noqa: E402


def test_lista_criada_com_regras_de_manutencao_no_topo(tmp_path):
    caminho = tmp_path / "lotes-a-monitorar.md"
    assert acrescentar_monitoramento(caminho, [lote_de(_candidato(), "Vip Leilões")], INICIO,
                                     "2026-10-08_19h37_varredura.md") == 1
    texto = caminho.read_text(encoding="utf-8")
    assert texto.startswith("# Lotes a monitorar")
    for regra in ("só ACRESCENTA", "apague o bloco inteiro", "martelo", "teto", "<!-- lote:", "Reaparições",
                  "final de placa", "quilometragem"):
        assert regra in texto
    assert "### Nissan Versa Excl Cvt — 2024" in texto
    assert "<!-- lote: vip-leiloes:1 -->" in texto
    assert "- **Entrou na lista:** 08/10/2026 19:37 (varredura `2026-10-08_19h37_varredura.md`)" in texto
    assert "- **Lance ao entrar:** R$ 61.000" in texto
    assert "- **Alvo:** nissan-versa-2023-2024 (teto R$ 69.300)" in texto
    assert "- **Análise FIPE:** _pendente_" in texto


def test_acrescenta_no_fim_sem_tocar_no_que_ja_existe(tmp_path):
    """Anotações do Rafael e dos agentes nunca podem ser perdidas."""
    caminho = tmp_path / "lotes-a-monitorar.md"
    acrescentar_monitoramento(caminho, [lote_de(_candidato(), "Vip Leilões")], INICIO, "a.md")
    editado = caminho.read_text(encoding="utf-8").replace("_pendente_", "62% da FIPE — ANOTADO")
    caminho.write_text(editado, encoding="utf-8")

    outro = lote_de(_candidato(id_canonico="vip-leiloes:2", titulo="Nissan Sentra Sl"), "Vip Leilões")
    assert acrescentar_monitoramento(caminho, [outro], INICIO, "b.md") == 1
    texto = caminho.read_text(encoding="utf-8")
    assert texto.startswith(editado), "o conteúdo anterior fica intacto, byte a byte"
    assert texto.index("Nissan Sentra Sl") > texto.index("ANOTADO")


def test_nao_repete_lote_que_ja_esta_na_lista(tmp_path):
    caminho = tmp_path / "lotes-a-monitorar.md"
    novo = lote_de(_candidato(), "Vip Leilões")
    acrescentar_monitoramento(caminho, [novo], INICIO, "a.md")
    antes = caminho.read_text(encoding="utf-8")
    assert acrescentar_monitoramento(caminho, [novo], INICIO, "b.md") == 0
    assert caminho.read_text(encoding="utf-8") == antes


def test_sem_lotes_novos_nao_cria_nem_altera(tmp_path):
    caminho = tmp_path / "lotes-a-monitorar.md"
    assert acrescentar_monitoramento(caminho, [], INICIO, "a.md") == 0
    assert not caminho.exists()


# --- Feature 002: linhas do Claudio Kuss (roadmap D-51) -----------------------------------------

from decimal import Decimal as _D  # noqa: E402

PREGAO = datetime(2026, 10, 13, 10, 0, tzinfo=SP)
SINISTRADO = "SINISTRADO - NOS DOCUMENTOS CONSTA RECUPERADO DE SINISTRO. REGULARIZAÇÃO POR CONTA DO ARREMATANTE"


def _kuss(**campos):
    padrao = dict(id_canonico="claudio-kuss-leiloes:282622", leiloeiro_id="claudio-kuss-leiloes",
                  titulo="IMP RENAULT/FLUENCE DYN 20A", ano_modelo=2013, lance_corrente=None, lance_inicial=None,
                  quilometragem=None, link="https://www.claudiokussleiloes.com.br/lance/897/0/282622",
                  evento_id="897", pregao_em=PREGAO, observacoes=SINISTRADO, despesas_adm=_D("2750.00"),
                  placa_parcial="F**-**35", local_documento="SÃO PAULO", detalhe_lido=True)
    padrao.update(campos)
    return lote_de(Candidato(lote=lote(**padrao), alvo=alvo(id="renault-fluence-2010-2017",
                                                             preco_maximo=_D("46900")),
                             preco_a_confirmar=True, km_a_confirmar=False), "Claudio Kuss Leilões")


LINHAS_KUSS = [
    "- **Preço:** Preço a confirmar",
    "- **Pregão:** 13/10/2026 10:00",
    "- **Despesas admin.:** R$ 2.750",
    "- **Documento:** Placa F\\*\\*-\\*\\*35, documento de SÃO PAULO",
    f"- **Observações:** {SINISTRADO}",
]


def test_relatorio_do_kuss_tem_pregao_despesas_documento_e_observacoes():
    texto = montar_relatorio(_dados(novos=[_kuss()]))
    for linha in LINHAS_KUSS:
        assert linha in texto


def test_lista_de_monitoramento_do_kuss_tem_as_mesmas_linhas(tmp_path):
    caminho = tmp_path / "lotes-a-monitorar.md"
    acrescentar_monitoramento(caminho, [_kuss()], INICIO, "a.md")
    texto = caminho.read_text(encoding="utf-8")
    for linha in LINHAS_KUSS[1:]:
        assert linha in texto
    assert "- **Preço ao entrar:** Preço a confirmar" in texto


def test_detalhe_que_falhou_aparece_no_relatorio():
    texto = montar_relatorio(_dados(novos=[_kuss(observacoes=None, detalhe_lido=False, despesas_adm=None,
                                                  placa_parcial=None, local_documento=None)]))
    assert "- **Observações:** observações não lidas; veja o link" in texto
    assert "Despesas admin." not in texto and "Documento:" not in texto


def test_documento_so_com_o_estado():
    texto = montar_relatorio(_dados(novos=[_kuss(placa_parcial=None)]))
    assert "- **Documento:** documento de SÃO PAULO" in texto


def test_lote_do_vip_nao_ganha_as_linhas_novas():
    texto = montar_relatorio(_dados())
    for rotulo in ("Pregão", "Despesas admin.", "Documento", "Observações"):
        assert f"**{rotulo}:**" not in texto


# --- Emenda E001 da feature 002: lotes da semeadura nos documentos ------------------------------

def test_relatorio_lista_os_semeados_numa_secao_propria():
    semeado = _kuss()
    semeado.origem = "semeadura"
    texto = montar_relatorio(_dados(novos=[], telegram=None, semeados=1, em_semeadura=True, semeados_lotes=[semeado]))
    assert "Nenhum lote novo nesta varredura." in texto
    secao = texto.split("## Já estavam no site (semeadura)", 1)[1]
    assert "sem aviso no Telegram" in secao
    assert "### 1. IMP RENAULT/FLUENCE DYN 20A — 2013" in secao
    assert f"- **Observações:** {SINISTRADO}" in secao


def test_sem_semeados_nao_ha_secao():
    assert "Já estavam no site" not in montar_relatorio(_dados())


def test_lista_marca_o_lote_que_entrou_por_semeadura(tmp_path):
    caminho = tmp_path / "lotes-a-monitorar.md"
    semeado = _kuss()
    semeado.origem = "semeadura"
    acrescentar_monitoramento(caminho, [semeado], INICIO, "a.md")
    texto = caminho.read_text(encoding="utf-8")
    assert ("- **Entrou na lista:** 08/10/2026 19:37 por semeadura: já estava no site na estreia da busca, "
            "sem aviso no Telegram (varredura `a.md`)") in texto
