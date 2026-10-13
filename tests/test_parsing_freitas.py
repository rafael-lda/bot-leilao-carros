"""Parser do Freitas (feature 004; interfaces/freitas.md; roadmap D-76 a D-82)."""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from apoio import FIXTURES_FREITAS, INICIO_CARD, card_freitas, cards_freitas_reais, detalhe_freitas, lote
from bot_leilao.parsing.freitas import ParserFreitas
from bot_leilao.parsing.modelos import ContextoParsing
from bot_leilao.parsing.nucleo import obter_parser

BASE = "https://www.freitasleiloeiro.com.br"
BRASILIA = timezone(timedelta(hours=-3))
COLETADO = datetime(2026, 10, 13, 15, 0, tzinfo=timezone.utc)
CTX = ContextoParsing(leiloeiro_id="freitas-leiloeiro", busca_id="freitas-leiloeiro:abc", base_url=BASE,
                      coletado_em=COLETADO, tipo_leilao="financiamento")
parser = ParserFreitas()


def _pagina(*cards):
    return ('\n\n    <div class="row">\n' + "".join(cards) + "    </div>\n").encode("utf-8")


def _todos():
    return {l.id_canonico: l for l in parser.extrair((FIXTURES_FREITAS / "cards_selecionados.html").read_bytes(),
                                                     CTX).lotes}


def test_registrado():
    assert isinstance(obter_parser("freitas-leiloeiro"), ParserFreitas)


def test_duster_real_com_todos_os_campos():
    duster = _todos()["freitas-leiloeiro:8112-1"]
    assert duster.link == f"{BASE}/Leiloes/LoteDetalhes?leilaoId=8112&loteNumero=1"
    assert (duster.leiloeiro_id, duster.busca_id, duster.coletado_em) == ("freitas-leiloeiro", "freitas-leiloeiro:abc",
                                                                          COLETADO)
    assert duster.numero_lote == "001"
    assert duster.titulo == "RENAULT/DUSTER INTP CVT"
    assert (duster.marca, duster.modelo) == ("renault", "duster intp cvt")
    assert (duster.ano_fabricacao, duster.ano_modelo) == (2023, 2024)
    assert (duster.lance_corrente, duster.lance_inicial) == (Decimal("50500.00"), None)
    assert duster.pregao_em == datetime(2026, 10, 16, 10, 0, tzinfo=BRASILIA)
    assert duster.placa_parcial == "S__-___4"
    assert duster.tipo_leilao == "financiamento"
    assert duster.quilometragem is None


def test_importado_sem_barra_entre_marca_e_modelo():
    sentra = _todos()["freitas-leiloeiro:8103-124"]
    assert (sentra.marca, sentra.modelo, sentra.ano_modelo) == ("nissan", "sentra 20s flex", 2013)


def test_grafia_m_benz():
    assert _todos()["freitas-leiloeiro:8103-57"].marca == "mercedes-benz"


def test_lance_inicial_quando_ainda_sem_lances():
    sem_lance = _todos()["freitas-leiloeiro:8103-9"]
    assert sem_lance.lance_corrente is None
    assert sem_lance.lance_inicial is not None and sem_lance.lance_inicial > 0


def test_sem_etiqueta_fica_sem_tipo():
    assert _todos()["freitas-leiloeiro:8112-12"].tipo_leilao is None


def test_em_loteamento_nao_e_devolvido_e_vai_para_o_log(caplog):
    """D-77 / RN-10: número provisório ("X", 700+) mudaria no loteamento."""
    with caplog.at_level(logging.INFO, logger="bot_leilao"):
        lidos = _todos()
    assert "freitas-leiloeiro:8111-700" not in lidos
    assert len(lidos) == 6
    assert "1 lote(s) em loteamento" in caplog.text


def test_pagina_real_com_25_lotes():
    extracao = parser.extrair((FIXTURES_FREITAS / "lotes_pag2.html").read_bytes(), CTX)
    assert extracao.busca_vazia is False
    assert all(l.id_canonico.startswith("freitas-leiloeiro:") and l.link for l in extracao.lotes)


def test_mensagem_de_fim_e_busca_vazia():
    extracao = parser.extrair((FIXTURES_FREITAS / "lotes_fim.html").read_bytes(), CTX)
    assert (extracao.lotes, extracao.busca_vazia) == ([], True)


@pytest.mark.parametrize("conteudo", [b"<html>layout novo</html>", b""])
def test_sem_cards_e_sem_mensagem_de_fim_levanta(conteudo):
    with pytest.raises(ValueError):
        parser.extrair(conteudo, CTX)


def test_card_com_descricao_fora_do_formato_levanta():
    with pytest.raises(ValueError):
        parser.extrair(_pagina(card_freitas(desc="RENAULT/DUSTER SEM VIRGULAS")), CTX)


# --- Detalhe (D-82) ------------------------------------------------------------------------------

def _novo(leilao="8112", numero="1"):
    return lote(id_canonico=f"freitas-leiloeiro:{leilao}-{numero}", leiloeiro_id="freitas-leiloeiro",
                link=f"{BASE}/Leiloes/LoteDetalhes?leilaoId={leilao}&loteNumero={numero}")


def test_detalhe_real_do_duster():
    alvo = _novo()
    parser.aplicar_detalhe(alvo, detalhe_freitas("detalhe_8112_1.html"))
    assert alvo.patio == "SANTO ANDRE - SP"
    assert alvo.despesas_adm == Decimal("2350.00")
    assert alvo.observacoes == "IPVA 2026 PAGO · AR COND. · DIR. HIDR."
    assert (alvo.detalhe_lido, alvo.retirado) == (True, False)


def test_detalhe_real_em_santa_barbara():
    alvo = _novo("8103", "3")
    parser.aplicar_detalhe(alvo, detalhe_freitas("detalhe_8103_3.html"))
    assert alvo.patio == "SANTA BARBARA D OESTE - SP"


def test_despesas_de_logistica_somadas_com_a_composicao_nas_observacoes():
    alvo = _novo("8111", "700")
    parser.aplicar_detalhe(alvo, detalhe_freitas("detalhe_8111_700.html"))
    assert alvo.despesas_adm == Decimal("2700.00")
    assert alvo.observacoes == "Despesas: operacionais R$ 2.350 + logística R$ 350"


def test_detalhe_retirado():
    alvo = _novo()
    parser.aplicar_detalhe(alvo, detalhe_freitas().replace(b"ABERTO PARA LANCES", b"RETIRADO"))
    assert alvo.retirado is True


def test_detalhe_sem_patio_nem_despesas_levanta():
    with pytest.raises(ValueError):
        parser.aplicar_detalhe(_novo(), b"<html>pagina de erro</html>")
