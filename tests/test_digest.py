"""Digest e alerta (notificador-telegram RF-01 a RF-03, RF-06, RF-08, RF-10, RF-11; interfaces/telegram-bot-api.md §3, §5)."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from apoio import alvo, lote
from bot_leilao.filtro.motor import Candidato
from bot_leilao.notificacao.digest import (
    LIMITE_BLOCO,
    AlertaOperacional,
    ItemDigest,
    escapar_html,
    formatar_km,
    formatar_preco,
    item_de,
    montar_alerta,
    montar_digest,
)

SP = timezone(timedelta(hours=-3))
QUANDO = datetime(2026, 10, 5, 8, 3, tzinfo=SP)
LINK = "https://www.vipleiloes.com.br/evento/anuncio/nissan-sentra-20s-flex-310800"


def _item(n=1, **campos):
    base = dict(titulo="Nissan Sentra 20S Flex", ano=2013, preco="R$ 12.500", leiloeiro="Vip Leilões",
                link=f"{LINK}?n={n}", km="228.227 km")
    base.update(campos)
    return ItemDigest(**base)


@pytest.mark.parametrize("valor, texto", [
    (Decimal("12500"), "R$ 12.500"),
    (Decimal("12500.00"), "R$ 12.500"),
    (Decimal("12500.5"), "R$ 12.500,50"),
    (Decimal("1234567"), "R$ 1.234.567"),
    (Decimal("950"), "R$ 950"),
    (None, "Preço a confirmar"),
])
def test_formatar_preco(valor, texto):
    assert formatar_preco(valor) == texto


def test_formatar_km():
    assert formatar_km(228227) == "228.227 km"
    assert formatar_km(None) is None


def test_escapar_html():
    assert escapar_html("Fiat <Uno> & Cia") == "Fiat &lt;Uno&gt; &amp; Cia"


def test_item_de_candidato():
    candidato = Candidato(lote=lote(titulo="Nissan Sentra 20S Flex", ano_modelo=2013, lance_corrente=Decimal("12500"),
                                    quilometragem=228227, link=LINK),
                          alvo=alvo(), preco_a_confirmar=False, km_a_confirmar=False)
    item = item_de(candidato, "Vip Leilões")
    assert item == ItemDigest(titulo="Nissan Sentra 20S Flex", ano=2013, preco="R$ 12.500",
                              leiloeiro="Vip Leilões", link=LINK, km="228.227 km")


def test_item_sem_preco_mostra_a_marcacao():
    """RF-03: nem zero, nem em branco."""
    candidato = Candidato(lote=lote(lance_corrente=None, lance_inicial=None), alvo=alvo(),
                          preco_a_confirmar=True, km_a_confirmar=False)
    assert item_de(candidato, "Vip Leilões").preco == "Preço a confirmar"


def test_sem_itens_nao_ha_mensagem():
    """RF-07."""
    assert montar_digest([], QUANDO) == []


def test_digest_com_cabecalho_e_itens():
    (bloco,) = montar_digest([_item(1), _item(2, km=None, preco="Preço a confirmar")], QUANDO)
    linhas = bloco.split("\n")
    assert linhas[0] == "<b>Varredura de 05/10/2026 08:03 — 2 lotes novos</b>"
    assert "1. Nissan Sentra 20S Flex — 2013" in linhas
    assert "   R$ 12.500 — Vip Leilões — 228.227 km" in linhas
    assert f"   {LINK}?n=1" in linhas
    assert "   Preço a confirmar — Vip Leilões" in linhas


def test_cabecalho_no_singular():
    (bloco,) = montar_digest([_item()], QUANDO)
    assert bloco.startswith("<b>Varredura de 05/10/2026 08:03 — 1 lote novo</b>")


def test_cada_item_ocupa_no_maximo_3_linhas():
    """RNF-04 do notificador."""
    (bloco,) = montar_digest([_item()], QUANDO)
    corpo = bloco.split("\n\n", 1)[1]
    assert len(corpo.strip().split("\n")) == 3


def test_texto_do_leiloeiro_e_escapado():
    """RF-10."""
    (bloco,) = montar_digest([_item(titulo="Fiat <Uno> & Cia")], QUANDO)
    assert "Fiat &lt;Uno&gt; &amp; Cia" in bloco
    assert "<Uno>" not in bloco


def test_ano_ausente_omite_o_ano():
    (bloco,) = montar_digest([_item(ano=None)], QUANDO)
    assert "1. Nissan Sentra 20S Flex\n" in bloco


def test_digest_grande_e_dividido_sem_cortar_item():
    """RF-06: 60 lotes em várias mensagens."""
    itens = [_item(n) for n in range(1, 61)]
    blocos = montar_digest(itens, QUANDO, limite=800)
    assert len(blocos) > 1
    assert all(len(b) <= 800 for b in blocos)
    assert blocos[0].startswith("<b>Varredura de")
    for i, bloco in enumerate(blocos[1:], start=2):
        assert bloco.startswith(f"(continuação {i}/{len(blocos)})")
    texto = "\n".join(blocos)
    for n in range(1, 61):
        assert texto.count(f"{LINK}?n={n}\n") + texto.endswith(f"{LINK}?n={n}") == 1
        bloco_do_item = next(b for b in blocos if f"\n{n}. Nissan" in b)
        assert f"{LINK}?n={n}" in bloco_do_item, "item inteiro no mesmo bloco"


def test_limite_padrao_abaixo_do_limite_da_plataforma():
    assert LIMITE_BLOCO == 3800 < 4096


def test_alerta_de_leiloeiro():
    texto = montar_alerta(AlertaOperacional(executado_em=QUANDO, leiloeiro="Vip Leilões",
                                            mensagem="o parser não extraiu nenhum lote de uma página com conteúdo (148 KB)."))
    assert texto.startswith("<b>Alerta do sistema — 05/10/2026 08:03</b>\n\n")
    assert "Vip Leilões: o parser não extraiu nenhum lote" in texto


def test_alerta_geral_sem_leiloeiro_e_escapado():
    texto = montar_alerta(AlertaOperacional(executado_em=QUANDO, mensagem="falha <geral> & total"))
    assert "falha &lt;geral&gt; &amp; total" in texto


# --- Feature 002: pregão e observações do Claudio Kuss (roadmap D-51) ---------------------------

PREGAO = datetime(2026, 10, 13, 10, 0, tzinfo=SP)
SINISTRADO = "SINISTRADO - NOS DOCUMENTOS CONSTA RECUPERADO DE SINISTRO. REGULARIZAÇÃO POR CONTA DO ARREMATANTE"
LINK_KUSS = "https://www.claudiokussleiloes.com.br/lance/897/0/282622"


def _kuss(**campos):
    padrao = dict(id_canonico="claudio-kuss-leiloes:282622", leiloeiro_id="claudio-kuss-leiloes",
                  titulo="IMP RENAULT/FLUENCE DYN 20A", ano_modelo=2013, lance_corrente=None, lance_inicial=None,
                  quilometragem=None, link=LINK_KUSS, evento_id="897", pregao_em=PREGAO, observacoes=SINISTRADO,
                  detalhe_lido=True)
    padrao.update(campos)
    return Candidato(lote=lote(**padrao), alvo=alvo(), preco_a_confirmar=True, km_a_confirmar=False)


def test_item_do_kuss_traz_pregao_e_observacoes():
    item = item_de(_kuss(), "Claudio Kuss Leilões")
    assert item.pregao == "Pregão 13/10 10:00"
    assert item.observacoes == SINISTRADO


def test_texto_do_item_do_kuss():
    (bloco,) = montar_digest([item_de(_kuss(), "Claudio Kuss Leilões")], QUANDO)
    assert bloco.split("\n\n", 1)[1].split("\n") == [
        "1. IMP RENAULT/FLUENCE DYN 20A — 2013",
        "   Preço a confirmar — Claudio Kuss Leilões — Pregão 13/10 10:00",
        f"   Obs.: {SINISTRADO}",
        f"   {LINK_KUSS}",
    ]


def test_observacoes_longas_sao_resumidas_em_160_caracteres():
    item = item_de(_kuss(observacoes="PARA-CHOQUE AMASSADO " * 20), "Claudio Kuss Leilões")
    assert 150 < len(item.observacoes) <= 160
    assert item.observacoes.endswith("…")


def test_observacoes_sao_escapadas():
    (bloco,) = montar_digest([item_de(_kuss(observacoes="RISCO < 10CM & FAROL"), "Claudio Kuss Leilões")], QUANDO)
    assert "Obs.: RISCO &lt; 10CM &amp; FAROL" in bloco


def test_detalhe_que_falhou_avisa_para_ver_o_link():
    item = item_de(_kuss(observacoes=None, detalhe_lido=False), "Claudio Kuss Leilões")
    assert item.observacoes == "observações não lidas; veja o link"


def test_lote_sem_observacoes_nao_tem_a_linha():
    (bloco,) = montar_digest([item_de(_kuss(observacoes=None), "Claudio Kuss Leilões")], QUANDO)
    assert "Obs.:" not in bloco


def test_item_do_vip_continua_igual():
    item = item_de(Candidato(lote=lote(), alvo=alvo(), preco_a_confirmar=False, km_a_confirmar=False), "Vip Leilões")
    assert (item.pregao, item.observacoes) == (None, None)


# --- Feature 003: pátio e FIPE na 2ª linha (D-71) ----------------------------------------------------

LINK_COPART = "https://www.copart.com.br/lotDetail/1141180"


def _copart(**campos):
    padrao = dict(id_canonico="copart:1141180", leiloeiro_id="copart", titulo="RENAULT DUSTER OROCH 1.6 16V SCE",
                  ano_modelo=2022, lance_corrente=Decimal("36000"), lance_inicial=None, quilometragem=None,
                  link=LINK_COPART, patio="VITÓRIA DE SANTO ANTÃO - PE", fipe=Decimal("80266.00"),
                  pregao_em=datetime(2026, 10, 15, 8, 30, tzinfo=SP),
                  observacoes="PEQUENOS AMASSADOS · Documento NORMAL · Motor dá partida e engrena")
    padrao.update(campos)
    return Candidato(lote=lote(**padrao), alvo=alvo(), preco_a_confirmar=False, km_a_confirmar=False)


def test_segunda_linha_com_patio_e_fipe_na_ordem():
    (bloco,) = montar_digest([item_de(_copart(), "Copart")], QUANDO)
    assert ("   R$ 36.000 — Copart — VITÓRIA DE SANTO ANTÃO - PE — FIPE R$ 80.266 — Pregão 15/10 08:30"
            in bloco.split("\n"))


def test_km_vem_antes_do_patio():
    (bloco,) = montar_digest([item_de(_copart(quilometragem=50000, fipe=None, pregao_em=None), "Copart")], QUANDO)
    assert "   R$ 36.000 — Copart — 50.000 km — VITÓRIA DE SANTO ANTÃO - PE" in bloco.split("\n")


def test_item_do_vip_ganha_o_patio():
    item = item_de(Candidato(lote=lote(patio="SC"), alvo=alvo(), preco_a_confirmar=False, km_a_confirmar=False),
                   "Vip Leilões")
    assert (item.patio, item.fipe) == ("SC", None)


def test_sem_patio_nem_fipe_a_linha_fica_igual():
    item = item_de(Candidato(lote=lote(), alvo=alvo(), preco_a_confirmar=False, km_a_confirmar=False), "Vip Leilões")
    assert (item.patio, item.fipe) == (None, None)
