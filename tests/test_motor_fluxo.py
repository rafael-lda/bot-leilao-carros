"""Deduplicação, semeadura e gravação (RN-05 a RN-07; RF-09, RF-12, RF-13 da feature; roadmap D-20)."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from apoio import alvo, lote
from bot_leilao.db.conexao import conectar
from bot_leilao.db.lotes import RegistroLote, RepositorioLotes
from bot_leilao.db.migracoes import migrar
from bot_leilao.filtro.fluxo import FluxoFiltragem
from bot_leilao.parsing.modelos import ResultadoParsing

AGORA = datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc)
B1 = "vip-leiloes:b1"


@pytest.fixture
def repo(caminho_banco):
    con = conectar(caminho_banco)
    migrar(con)
    con.execute("INSERT INTO execucao (id, iniciado_em, modo) VALUES ('exec-1', '2026-10-05T11:00:00.000Z', 'normal')")
    con.commit()
    return RepositorioLotes(con)


def _parsing(*ids, busca=B1, **campos):
    lotes = [lote(id_canonico=i, busca_id=busca, link=f"https://x/{i}", **campos) for i in ids]
    return ResultadoParsing(busca_id=busca, leiloeiro_id="vip-leiloes", lotes=lotes)


def _semear(repo, busca=B1):
    repo.marcar_semeada(busca, "exec-1", AGORA)


def test_primeira_execucao_de_uma_busca_semeia_sem_notificar(repo):
    """RN-07 / cenário 1."""
    fluxo = FluxoFiltragem(repo)
    resultado = fluxo.filtrar([_parsing("v:1", "v:2")], [alvo()], buscas_aptas={B1})
    assert resultado.novos == []
    assert [c.lote.id_canonico for c in resultado.semeaveis] == ["v:1", "v:2"]
    assert resultado.buscas_a_semear == [B1]
    assert repo.total() == 0, "nada é gravado até registrar a semeadura"
    assert fluxo.registrar_semeadura(resultado, "exec-1", AGORA) == 2
    assert repo.busca_semeada(B1)
    origens = {r["origem"] for r in repo.con.execute("SELECT origem FROM lote_conhecido")}
    assert origens == {"semeadura"}


def test_busca_semeada_entrega_novos(repo):
    _semear(repo)
    resultado = FluxoFiltragem(repo).filtrar([_parsing("v:1")], [alvo()], buscas_aptas={B1})
    assert [c.lote.id_canonico for c in resultado.novos] == ["v:1"]
    assert resultado.semeaveis == []


def test_novos_so_sao_gravados_apos_confirmacao(repo):
    """RN-06."""
    _semear(repo)
    fluxo = FluxoFiltragem(repo)
    resultado = fluxo.filtrar([_parsing("v:1")], [alvo()], buscas_aptas={B1})
    assert repo.total() == 0
    assert fluxo.confirmar_notificacao(resultado.novos, AGORA) == 1
    linha = repo.con.execute("SELECT * FROM lote_conhecido").fetchone()
    assert linha["origem"] == "notificacao"
    assert linha["alvo_id"] == "nissan-versa-2018-2021"
    assert Decimal(str(linha["preco_na_notificacao"])) == Decimal("41900")
    assert linha["busca_id"] == B1


def test_ja_notificado_nao_volta(repo):
    """RN-05 / cenário 4."""
    _semear(repo)
    fluxo = FluxoFiltragem(repo)
    fluxo.confirmar_notificacao(fluxo.filtrar([_parsing("v:1")], [alvo()], buscas_aptas={B1}).novos, AGORA)
    resultado = fluxo.filtrar([_parsing("v:1")], [alvo()], buscas_aptas={B1})
    assert resultado.novos == []
    assert resultado.ja_conhecidos == 1


def test_sem_confirmacao_o_lote_volta_na_proxima(repo):
    """Cenário 6: falha no envio preserva os lotes."""
    _semear(repo)
    fluxo = FluxoFiltragem(repo)
    fluxo.filtrar([_parsing("v:1")], [alvo()], buscas_aptas={B1})
    assert len(fluxo.filtrar([_parsing("v:1")], [alvo()], buscas_aptas={B1}).novos) == 1


def test_busca_nao_apta_nao_e_semeada(repo):
    """D-20: coleta falha ou quebra não semeiam; lotes dela ficam de fora."""
    resultado = FluxoFiltragem(repo).filtrar([_parsing("v:1")], [alvo()], buscas_aptas=set())
    assert resultado.buscas_a_semear == []
    assert resultado.semeaveis == []
    assert resultado.novos == []


def test_busca_apta_sem_candidatos_tambem_e_semeada(repo):
    """Semear é alinhar ao presente, mesmo que nada case hoje."""
    fluxo = FluxoFiltragem(repo)
    resultado = fluxo.filtrar([_parsing("v:1", marca="fiat", modelo="uno")], [alvo()], buscas_aptas={B1})
    assert resultado.buscas_a_semear == [B1]
    fluxo.registrar_semeadura(resultado, "exec-1", AGORA)
    assert repo.busca_semeada(B1)


def test_mudar_os_filtros_cria_busca_nova_que_semeia_de_novo(repo):
    _semear(repo, "vip-leiloes:antiga")
    resultado = FluxoFiltragem(repo).filtrar([_parsing("v:1", busca="vip-leiloes:nova")], [alvo()],
                                             buscas_aptas={"vip-leiloes:nova"})
    assert resultado.novos == []
    assert resultado.buscas_a_semear == ["vip-leiloes:nova"]


def test_mesmo_lote_em_duas_buscas_conta_uma_vez(repo):
    _semear(repo, "b1")
    _semear(repo, "b2")
    resultado = FluxoFiltragem(repo).filtrar([_parsing("v:1", busca="b1"), _parsing("v:1", busca="b2")],
                                             [alvo()], buscas_aptas={"b1", "b2"})
    assert len(resultado.novos) == 1


def test_contagens_para_o_historico(repo):
    """RF-12: vistos, candidatos, novos e já conhecidos."""
    _semear(repo)
    repo.registrar([RegistroLote("v:2", "vip-leiloes", B1, "x", "notificacao", None, None, "https://x/2", AGORA)])
    parsing = _parsing("v:1", "v:2")
    parsing.lotes += [lote(id_canonico="v:3", busca_id=B1, marca="fiat", modelo="uno"),
                      lote(id_canonico="v:4", busca_id=B1, retirado=True)]
    contagens = FluxoFiltragem(repo).filtrar([parsing], [alvo()], buscas_aptas={B1}).contagens()
    assert contagens == {
        "lotes_vistos": 4, "lotes_candidatos": 2, "lotes_novos": 1, "lotes_ja_conhecidos": 1,
        "lotes_semeados": 0, "descartados_sem_casar": 1, "descartados_dado_ausente": 0,
        "descartados_retirados": 1,
    }
