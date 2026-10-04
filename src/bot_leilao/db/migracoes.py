"""Migrações por `PRAGMA user_version` (data-delta.md §3; roadmap D-06)."""

from __future__ import annotations

import sqlite3

from bot_leilao.db.conexao import ErroBanco

VERSAO_ATUAL = 1

_VERSAO_1 = """
CREATE TABLE IF NOT EXISTS execucao (
  id                       TEXT PRIMARY KEY,
  iniciado_em              TEXT NOT NULL,
  finalizado_em            TEXT,
  duracao_ms               INTEGER,
  veredito                 TEXT CHECK (veredito IN ('sucesso', 'sucesso_parcial', 'falha', 'recusada')),
  motivo                   TEXT,
  modo                     TEXT NOT NULL CHECK (modo IN ('normal', 'dry_run')),
  alvos_ativos             INTEGER,
  lotes_vistos             INTEGER,
  lotes_candidatos         INTEGER,
  lotes_novos              INTEGER,
  lotes_ja_conhecidos      INTEGER,
  lotes_semeados           INTEGER,
  descartados_sem_casar    INTEGER,
  descartados_dado_ausente INTEGER,
  descartados_retirados    INTEGER,
  digest_enviado           INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_execucao_iniciado_em ON execucao (iniciado_em);

CREATE TABLE IF NOT EXISTS lote_conhecido (
  id_canonico          TEXT PRIMARY KEY,
  leiloeiro_id         TEXT NOT NULL,
  busca_id             TEXT NOT NULL,
  alvo_id              TEXT NOT NULL,
  origem               TEXT NOT NULL CHECK (origem IN ('notificacao', 'semeadura')),
  preco_na_notificacao NUMERIC,
  lance_inicial        NUMERIC,
  link                 TEXT NOT NULL,
  registrado_em        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_lote_conhecido_registrado_em ON lote_conhecido (registrado_em);
CREATE INDEX IF NOT EXISTS ix_lote_conhecido_leiloeiro ON lote_conhecido (leiloeiro_id);

CREATE TABLE IF NOT EXISTS busca_semeada (
  busca_id    TEXT PRIMARY KEY,
  semeada_em  TEXT NOT NULL,
  execucao_id TEXT NOT NULL REFERENCES execucao (id)
);

CREATE TABLE IF NOT EXISTS execucao_leiloeiro (
  execucao_id       TEXT NOT NULL REFERENCES execucao (id),
  leiloeiro_id      TEXT NOT NULL,
  buscas_ok         INTEGER NOT NULL DEFAULT 0,
  buscas_bloqueadas INTEGER NOT NULL DEFAULT 0,
  buscas_falhas     INTEGER NOT NULL DEFAULT 0,
  lotes_novos       INTEGER NOT NULL DEFAULT 0,
  quebra_suspeita   INTEGER NOT NULL DEFAULT 0,
  alerta_enviado    INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (execucao_id, leiloeiro_id)
);
CREATE INDEX IF NOT EXISTS ix_execucao_leiloeiro_leiloeiro ON execucao_leiloeiro (leiloeiro_id);

CREATE TABLE IF NOT EXISTS execucao_busca (
  execucao_id              TEXT NOT NULL REFERENCES execucao (id),
  busca_id                 TEXT NOT NULL,
  leiloeiro_id             TEXT NOT NULL,
  iniciado_em              TEXT NOT NULL,
  duracao_ms               INTEGER NOT NULL,
  status_http              INTEGER,
  nivel_usado              TEXT NOT NULL CHECK (nivel_usado IN ('script', 'apify', 'apify_residencial')),
  tentativas               INTEGER NOT NULL,
  paginas                  INTEGER NOT NULL DEFAULT 0,
  veredito                 TEXT NOT NULL CHECK (veredito IN ('ok', 'bloqueado', 'falha_rede', 'falha_autenticacao')),
  motivo                   TEXT,
  lotes_extraidos          INTEGER,
  lotes_descartados_parser INTEGER,
  quebra_suspeita          INTEGER NOT NULL DEFAULT 0,
  motivo_quebra            TEXT,
  PRIMARY KEY (execucao_id, busca_id)
);
"""


def migrar(con: sqlite3.Connection) -> int:
    """Leva o banco à versão atual, de forma idempotente. Devolve a versão final."""
    try:
        versao = con.execute("PRAGMA user_version").fetchone()[0]
        if versao > VERSAO_ATUAL:
            raise ErroBanco(f"O banco está na versão de esquema {versao}, mais nova que a conhecida "
                            f"por este programa ({VERSAO_ATUAL}). Atualize o programa.")
        if versao < 1:
            con.executescript("BEGIN;" + _VERSAO_1 + f"PRAGMA user_version = 1; COMMIT;")
        return con.execute("PRAGMA user_version").fetchone()[0]
    except sqlite3.Error as erro:
        raise ErroBanco(f"Falha ao preparar o banco: {erro}") from erro
