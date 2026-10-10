"""Enriquecimento dos lotes novos pelo detalhe (feature 002; roadmap D-48, D-49)."""

import logging

import httpx

from apoio import SiteKuss, alvo, detalhe_kuss, json_kuss, lote
from bot_leilao.coleta import registro
from bot_leilao.coleta.enriquecimento import enriquecer
from bot_leilao.coleta.http import ClienteHTTP
from bot_leilao.filtro.motor import Candidato
from bot_leilao.parsing import nucleo

import bot_leilao.coleta.claudio_kuss  # noqa: F401 — registra o adaptador
import bot_leilao.coleta.vip  # noqa: F401
import bot_leilao.parsing.claudio_kuss  # noqa: F401 — registra o parser
import bot_leilao.parsing.vip  # noqa: F401

SINISTRADO = "SINISTRADO - NOS DOCUMENTOS CONSTA RECUPERADO DE SINISTRO. REGULARIZAÇÃO POR CONTA DO ARREMATANTE"


def _kuss(seq="282622"):
    return Candidato(lote=lote(id_canonico=f"claudio-kuss-leiloes:{seq}", leiloeiro_id="claudio-kuss-leiloes",
                               link=f"https://www.claudiokussleiloes.com.br/lance/897/0/{seq}", evento_id="897",
                               lance_corrente=None, lance_inicial=None, quilometragem=None),
                     alvo=alvo(), preco_a_confirmar=True, km_a_confirmar=False)


def _vip():
    return Candidato(lote=lote(), alvo=alvo(), preco_a_confirmar=False, km_a_confirmar=False)


def _enriquecer(candidatos, site, relogio):
    cliente = ClienteHTTP(httpx.MockTransport(site.responder), relogio=relogio.agora, dormir=relogio.dormir)
    try:
        return enriquecer(candidatos, cliente, registro.adaptadores(), nucleo.parsers())
    finally:
        cliente.fechar()


def test_lote_novo_do_kuss_recebe_observacoes_e_despesas(relogio):
    site = SiteKuss(detalhes={"282622": detalhe_kuss()})
    resultado = _enriquecer([_kuss()], site, relogio)
    (candidato,) = resultado.novos
    assert candidato.lote.observacoes == SINISTRADO
    assert candidato.lote.detalhe_lido is True
    assert (resultado.detalhados, resultado.retirados, resultado.falhas) == (1, 0, 0)
    assert [f["le_id"] for f in site.chamadas_op("D")] == ["282622"]


def test_lote_do_vip_passa_sem_requisicao(relogio):
    site = SiteKuss()
    vip = _vip()
    resultado = _enriquecer([vip], site, relogio)
    assert resultado.novos == [vip]
    assert vip.lote.detalhe_lido is None
    assert site.chamadas == []


def test_retirado_no_detalhe_sai_da_lista_e_e_contado(relogio):
    site = SiteKuss(detalhes={"282622": detalhe_kuss(retirado="S")})
    resultado = _enriquecer([_kuss(), _vip()], site, relogio)
    assert [c.lote.leiloeiro_id for c in resultado.novos] == ["vip-leiloes"]
    assert resultado.retirados == 1


def test_falha_de_rede_mantem_o_lote_sem_observacoes(relogio, caplog):
    site = SiteKuss(detalhes={"282622": httpx.ConnectError})
    with caplog.at_level(logging.WARNING, logger="bot_leilao"):
        resultado = _enriquecer([_kuss()], site, relogio)
    (candidato,) = resultado.novos
    assert (candidato.lote.observacoes, candidato.lote.detalhe_lido) == (None, False)
    assert resultado.falhas == 1
    assert "282622" in caplog.text


def test_detalhe_em_formato_inesperado_mantem_o_lote(relogio):
    site = SiteKuss(detalhes={"282622": b"<html>manutencao</html>"})
    (candidato,) = _enriquecer([_kuss()], site, relogio).novos
    assert candidato.lote.detalhe_lido is False


def test_falha_num_lote_nao_impede_os_outros(relogio):
    site = SiteKuss(detalhes={"1": 500, "2": detalhe_kuss()})
    resultado = _enriquecer([_kuss("1"), _kuss("2")], site, relogio)
    assert [c.lote.detalhe_lido for c in resultado.novos] == [False, True]
    assert (resultado.detalhados, resultado.falhas) == (1, 1)


def test_sucata_no_detalhe_sai_da_lista_e_e_contada(relogio):
    site = SiteKuss(detalhes={"282622": json_kuss("detalhe_282327_sucata.json")})
    resultado = _enriquecer([_kuss(), _vip()], site, relogio)
    assert [c.lote.leiloeiro_id for c in resultado.novos] == ["vip-leiloes"]
    assert (resultado.sucatas, resultado.retirados) == (1, 0)
