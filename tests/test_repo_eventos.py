"""Leilões vistos e última coleta (feature 005; data-delta.md §2; roadmap D-101, D-102)."""

from datetime import datetime, timedelta, timezone

import pytest

from bot_leilao.db.conexao import conectar
from bot_leilao.db.eventos import RepositorioEventos
from bot_leilao.db.execucoes import RepositorioExecucoes
from bot_leilao.db.migracoes import _VERSAO_1, migrar

BRASILIA = timezone(timedelta(hours=-3))
VISTO = datetime(2026, 10, 13, 22, 0, tzinfo=timezone.utc)
PREGAO = datetime(2026, 10, 14, 9, 30, tzinfo=BRASILIA)


@pytest.fixture
def con(caminho_banco):
    con = conectar(caminho_banco)
    migrar(con)
    return con


def test_banco_da_versao_1_sobe_para_a_2_sem_perder_dados(caminho_banco):
    con = conectar(caminho_banco)
    con.executescript("BEGIN;" + _VERSAO_1 + "PRAGMA user_version = 1; COMMIT;")
    con.execute("INSERT INTO execucao (id, iniciado_em, modo) VALUES ('x', '2026-10-05T11:00:00.000Z', 'normal')")
    con.commit()
    assert migrar(con) == 2
    assert con.execute("SELECT COUNT(*) FROM execucao").fetchone()[0] == 1
    colunas = {r[1] for r in con.execute("PRAGMA table_info(evento_visto)")}
    assert colunas == {"leiloeiro_id", "evento_id", "rotulo", "pregao_em", "visto_primeiro_em", "na_semeadura"}


def test_primeira_vez_fica_e_as_seguintes_sao_ignoradas(con):
    repo = RepositorioEventos(con)
    assert repo.registrar("milan-leiloes", "15618", "RECUPERADOS DE FINANCIAMENTO", PREGAO, VISTO) is True
    assert repo.registrar("milan-leiloes", "15618", "outro rótulo", PREGAO, VISTO + timedelta(days=2),
                          na_semeadura=True) is False
    evento = repo.obter("milan-leiloes", "15618")
    assert evento.visto_primeiro_em == VISTO
    assert evento.pregao_em == PREGAO
    assert evento.rotulo == "RECUPERADOS DE FINANCIAMENTO"
    assert evento.na_semeadura is False


def test_antecedencia_em_dias_e_marca_de_semeadura(con):
    repo = RepositorioEventos(con)
    repo.registrar("milan-leiloes", "15700", None, datetime(2026, 10, 20, 9, 30, tzinfo=BRASILIA),
                   datetime(2026, 10, 15, 11, 0, tzinfo=timezone.utc))
    repo.registrar("claudio-kuss-leiloes", "897", None, None, VISTO, na_semeadura=True)
    assert repo.obter("milan-leiloes", "15700").antecedencia_dias == 5
    kuss = repo.obter("claudio-kuss-leiloes", "897")
    assert kuss.na_semeadura is True and kuss.antecedencia_dias is None
    assert repo.obter("milan-leiloes", "nao-existe") is None


def test_mesmo_evento_em_leiloeiros_diferentes(con):
    repo = RepositorioEventos(con)
    assert repo.registrar("milan-leiloes", "1", None, PREGAO, VISTO)
    assert repo.registrar("claudio-kuss-leiloes", "1", None, PREGAO, VISTO)


def _execucao(repo, quando, modo="normal", ok=1, leiloeiro="milan-leiloes"):
    execucao_id = repo.abrir(modo, quando)
    repo.registrar_leiloeiro(execucao_id, leiloeiro, buscas_ok=ok, buscas_falhas=1 - ok)
    return execucao_id


def test_ultima_coleta_ok_ignora_dry_run_e_execucoes_sem_busca_ok(con):
    repo = RepositorioExecucoes(con)
    assert repo.ultima_coleta_ok("milan-leiloes") is None
    _execucao(repo, VISTO)
    _execucao(repo, VISTO + timedelta(days=1), modo="dry_run")
    _execucao(repo, VISTO + timedelta(days=2), ok=0)
    _execucao(repo, VISTO + timedelta(days=3), leiloeiro="vip-leiloes")
    assert repo.ultima_coleta_ok("milan-leiloes") == VISTO
