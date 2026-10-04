"""Repositório de lotes conhecidos e de buscas semeadas (data-delta.md §2.1 e §2.2)."""

import time
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from bot_leilao.db.conexao import conectar
from bot_leilao.db.lotes import RegistroLote, RepositorioLotes
from bot_leilao.db.migracoes import migrar

INSTANTE = datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc)


@pytest.fixture
def con(caminho_banco):
    conexao = conectar(caminho_banco)
    migrar(conexao)
    conexao.execute("INSERT INTO execucao (id, iniciado_em, modo) VALUES ('exec-1', '2026-10-05T11:00:00.000Z', 'normal')")
    conexao.commit()
    return conexao


def _registro(id_canonico, origem="notificacao", preco=Decimal("41900")):
    return RegistroLote(id_canonico=id_canonico, leiloeiro_id="vip-leiloes", busca_id="vip-leiloes:abc",
                        alvo_id="nissan-versa-2018-2021", origem=origem, preco_na_notificacao=preco,
                        lance_inicial=Decimal("30000"), link=f"https://x/{id_canonico}", registrado_em=INSTANTE)


def test_registrar_e_consultar_conhecidos(con):
    repo = RepositorioLotes(con)
    assert repo.registrar([_registro("vip-leiloes:1"), _registro("vip-leiloes:2", origem="semeadura")]) == 2
    assert repo.conhecidos(["vip-leiloes:1", "vip-leiloes:2", "vip-leiloes:3"]) == {"vip-leiloes:1", "vip-leiloes:2"}
    assert repo.total() == 2


def test_preco_nulo_e_preservado(con):
    repo = RepositorioLotes(con)
    repo.registrar([_registro("vip-leiloes:1", preco=None)])
    linha = con.execute("SELECT preco_na_notificacao, origem, registrado_em FROM lote_conhecido").fetchone()
    assert linha["preco_na_notificacao"] is None
    assert linha["origem"] == "notificacao"
    assert linha["registrado_em"] == "2026-10-05T11:00:00.000Z"


def test_colisao_de_id_e_ignorada(con):
    """EC-09 do motor: o segundo é tratado como já conhecido, sem erro."""
    repo = RepositorioLotes(con)
    repo.registrar([_registro("vip-leiloes:1")])
    assert repo.registrar([_registro("vip-leiloes:1"), _registro("vip-leiloes:9")]) == 1
    assert repo.total() == 2


def test_registro_e_atomico(con):
    """RNF-02 do motor: transação única; falha no meio não deixa registro parcial."""
    repo = RepositorioLotes(con)
    invalido = _registro("vip-leiloes:2", origem="invalida")
    with pytest.raises(Exception):
        repo.registrar([_registro("vip-leiloes:1"), invalido])
    assert repo.total() == 0


def test_busca_semeada(con):
    repo = RepositorioLotes(con)
    assert repo.busca_semeada("vip-leiloes:abc") is False
    repo.marcar_semeada("vip-leiloes:abc", "exec-1", INSTANTE)
    assert repo.busca_semeada("vip-leiloes:abc") is True
    repo.marcar_semeada("vip-leiloes:abc", "exec-1", INSTANTE)  # idempotente


def test_consulta_de_deduplicacao_rapida_com_50_mil_registros(con):
    """RNF-01 do motor: < 1 s com 50.000 lotes."""
    repo = RepositorioLotes(con)
    repo.registrar(_registro(f"vip-leiloes:{i}") for i in range(50_000))
    consulta = [f"vip-leiloes:{i}" for i in range(0, 100_000, 50)]
    inicio = time.perf_counter()
    achados = repo.conhecidos(consulta)
    assert time.perf_counter() - inicio < 1.0
    assert len(achados) == 1000
