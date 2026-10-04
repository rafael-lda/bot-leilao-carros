"""Histórico de execuções (agendador-observabilidade; data-delta.md §2.3 a §2.5)."""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Mapping
from dataclasses import astuple, dataclass, fields
from datetime import datetime

from bot_leilao.db.conexao import de_iso, para_iso

CONTAGENS = frozenset({
    "alvos_ativos", "lotes_vistos", "lotes_candidatos", "lotes_novos", "lotes_ja_conhecidos", "lotes_semeados",
    "descartados_sem_casar", "descartados_dado_ausente", "descartados_retirados",
})


@dataclass
class RegistroBusca:
    busca_id: str
    leiloeiro_id: str
    iniciado_em: datetime
    duracao_ms: int
    status_http: int | None
    nivel_usado: str
    tentativas: int
    paginas: int
    veredito: str
    motivo: str | None = None
    lotes_extraidos: int | None = None
    lotes_descartados_parser: int | None = None
    quebra_suspeita: bool = False
    motivo_quebra: str | None = None


class RepositorioExecucoes:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def abrir(self, modo: str, iniciado_em: datetime) -> str:
        execucao_id = str(uuid.uuid4())
        with self.con:
            self.con.execute("INSERT INTO execucao (id, iniciado_em, modo) VALUES (?, ?, ?)",
                             (execucao_id, para_iso(iniciado_em), modo))
        return execucao_id

    def registrar_recusa(self, iniciado_em: datetime, motivo: str) -> str:
        execucao_id = str(uuid.uuid4())
        instante = para_iso(iniciado_em)
        with self.con:
            self.con.execute(
                "INSERT INTO execucao (id, iniciado_em, finalizado_em, duracao_ms, veredito, motivo, modo)"
                " VALUES (?, ?, ?, 0, 'recusada', ?, 'normal')", (execucao_id, instante, instante, motivo))
        return execucao_id

    def fechar(self, execucao_id: str, veredito: str, finalizado_em: datetime, motivo: str | None = None,
               contagens: Mapping[str, int] | None = None, digest_enviado: bool = False) -> None:
        contagens = dict(contagens or {})
        desconhecidas = set(contagens) - CONTAGENS
        if desconhecidas:
            raise ValueError(f"contagens desconhecidas: {sorted(desconhecidas)}")
        linha = self.obter(execucao_id)
        duracao = int((finalizado_em - de_iso(linha["iniciado_em"])).total_seconds() * 1000)
        colunas = ["finalizado_em = ?", "duracao_ms = ?", "veredito = ?", "motivo = ?", "digest_enviado = ?"]
        valores: list = [para_iso(finalizado_em), duracao, veredito, motivo, int(digest_enviado)]
        for nome, valor in sorted(contagens.items()):
            colunas.append(f"{nome} = ?")
            valores.append(int(valor))
        with self.con:
            self.con.execute(f"UPDATE execucao SET {', '.join(colunas)} WHERE id = ?", (*valores, execucao_id))

    def registrar_leiloeiro(self, execucao_id: str, leiloeiro_id: str, *, buscas_ok: int = 0,
                            buscas_bloqueadas: int = 0, buscas_falhas: int = 0, lotes_novos: int = 0,
                            quebra_suspeita: bool = False, alerta_enviado: bool = False) -> None:
        with self.con:
            self.con.execute(
                "INSERT OR REPLACE INTO execucao_leiloeiro (execucao_id, leiloeiro_id, buscas_ok, buscas_bloqueadas,"
                " buscas_falhas, lotes_novos, quebra_suspeita, alerta_enviado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (execucao_id, leiloeiro_id, buscas_ok, buscas_bloqueadas, buscas_falhas, lotes_novos,
                 int(quebra_suspeita), int(alerta_enviado)))

    def registrar_busca(self, execucao_id: str, registro: RegistroBusca) -> None:
        nomes = [f.name for f in fields(RegistroBusca)]
        valores = list(astuple(registro))
        valores[nomes.index("iniciado_em")] = para_iso(registro.iniciado_em)
        valores[nomes.index("quebra_suspeita")] = int(registro.quebra_suspeita)
        with self.con:
            self.con.execute(
                f"INSERT OR REPLACE INTO execucao_busca (execucao_id, {', '.join(nomes)})"
                f" VALUES (?, {', '.join('?' * len(nomes))})", (execucao_id, *valores))

    def alerta_enviado_desde(self, leiloeiro_id: str, desde: datetime) -> bool:
        """Base do limite de 1 alerta por dia por leiloeiro (roadmap D-22). Execuções dry_run não contam."""
        linha = self.con.execute(
            "SELECT 1 FROM execucao_leiloeiro el JOIN execucao e ON e.id = el.execucao_id"
            " WHERE el.leiloeiro_id = ? AND el.alerta_enviado = 1 AND e.modo = 'normal' AND e.iniciado_em >= ?"
            " LIMIT 1", (leiloeiro_id, para_iso(desde))).fetchone()
        return linha is not None

    def obter(self, execucao_id: str) -> sqlite3.Row | None:
        return self.con.execute("SELECT * FROM execucao WHERE id = ?", (execucao_id,)).fetchone()
