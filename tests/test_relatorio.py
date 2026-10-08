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
