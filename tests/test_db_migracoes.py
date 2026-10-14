"""Conexão e migrações (data-delta.md §2 e §3; roadmap D-06)."""

from datetime import datetime, timedelta, timezone

import pytest

from bot_leilao.db.conexao import ErroBanco, conectar, de_iso, para_iso
from bot_leilao.db.migracoes import VERSAO_ATUAL, migrar

TABELAS = {"lote_conhecido", "busca_semeada", "execucao", "execucao_leiloeiro", "execucao_busca", "evento_visto"}
INDICES = {"ix_lote_conhecido_registrado_em", "ix_lote_conhecido_leiloeiro",
           "ix_execucao_iniciado_em", "ix_execucao_leiloeiro_leiloeiro"}


def _nomes(con, tipo):
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = ?", (tipo,))}


def test_conectar_cria_pasta_e_aplica_pragmas(tmp_path):
    con = conectar(tmp_path / "nova" / "pasta" / "banco.sqlite3")
    assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert con.execute("PRAGMA busy_timeout").fetchone()[0] == 10000
    linha = con.execute("SELECT 1 AS um").fetchone()
    assert linha["um"] == 1, "row_factory = sqlite3.Row"


def test_migrar_cria_as_cinco_tabelas_e_indices(caminho_banco):
    con = conectar(caminho_banco)
    assert migrar(con) == VERSAO_ATUAL == 2  # feature 005: evento_visto
    assert TABELAS <= _nomes(con, "table")
    assert INDICES <= _nomes(con, "index")
    assert con.execute("PRAGMA user_version").fetchone()[0] == 2


def test_migrar_e_idempotente(caminho_banco):
    con = conectar(caminho_banco)
    migrar(con)
    con.execute("INSERT INTO execucao (id, iniciado_em, modo) VALUES ('x', '2026-10-05T11:00:00.000Z', 'normal')")
    con.commit()
    assert migrar(con) == 2
    assert con.execute("SELECT COUNT(*) FROM execucao").fetchone()[0] == 1


def test_versao_maior_que_a_conhecida_aborta(caminho_banco):
    con = conectar(caminho_banco)
    con.execute("PRAGMA user_version = 99")
    with pytest.raises(ErroBanco) as erro:
        migrar(con)
    assert "99" in str(erro.value)


def test_restricoes_de_dominio(caminho_banco):
    con = conectar(caminho_banco)
    migrar(con)
    with pytest.raises(Exception):
        con.execute("INSERT INTO lote_conhecido (id_canonico, leiloeiro_id, busca_id, alvo_id, origem, link, registrado_em)"
                    " VALUES ('a', 'l', 'b', 'x', 'outra', 'https://x', '2026-10-05T11:00:00.000Z')")
    with pytest.raises(Exception):
        con.execute("INSERT INTO busca_semeada (busca_id, semeada_em, execucao_id) VALUES ('b', 'agora', 'inexistente')")


def test_para_iso_grava_utc_com_z_e_volta():
    instante = datetime(2026, 10, 5, 8, 3, 1, 500000, tzinfo=timezone(timedelta(hours=-3)))
    texto = para_iso(instante)
    assert texto == "2026-10-05T11:03:01.500Z"
    assert de_iso(texto) == instante


def test_para_iso_recusa_datetime_ingenuo():
    with pytest.raises(ValueError):
        para_iso(datetime(2026, 10, 5, 11, 0))
