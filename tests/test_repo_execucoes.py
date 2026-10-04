"""Histórico de execuções (RF-12 da feature; data-delta.md §2.3 a §2.5; roadmap D-21, D-22)."""

from datetime import datetime, timedelta, timezone

import pytest

from bot_leilao.db.conexao import conectar
from bot_leilao.db.execucoes import RegistroBusca, RepositorioExecucoes
from bot_leilao.db.migracoes import migrar

INICIO = datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc)


@pytest.fixture
def repo(caminho_banco):
    con = conectar(caminho_banco)
    migrar(con)
    return RepositorioExecucoes(con)


def test_abrir_e_fechar_com_contagens(repo):
    execucao_id = repo.abrir("normal", INICIO)
    linha = repo.obter(execucao_id)
    assert linha["finalizado_em"] is None, "aberta sem encerramento até o fechamento"
    repo.fechar(execucao_id, "sucesso", INICIO + timedelta(minutes=2, seconds=3),
                contagens={"lotes_vistos": 201, "lotes_candidatos": 3, "lotes_novos": 1,
                           "lotes_ja_conhecidos": 2, "lotes_semeados": 0, "alvos_ativos": 1},
                digest_enviado=True)
    linha = repo.obter(execucao_id)
    assert linha["veredito"] == "sucesso"
    assert linha["duracao_ms"] == 123_000
    assert linha["lotes_vistos"] == 201
    assert linha["lotes_novos"] == 1
    assert linha["digest_enviado"] == 1
    assert linha["modo"] == "normal"
    assert linha["finalizado_em"] == "2026-10-05T11:02:03.000Z"


def test_fechar_falha_com_motivo(repo):
    execucao_id = repo.abrir("normal", INICIO)
    repo.fechar(execucao_id, "falha", INICIO + timedelta(seconds=1), motivo="config_invalida")
    linha = repo.obter(execucao_id)
    assert (linha["veredito"], linha["motivo"]) == ("falha", "config_invalida")


def test_contagem_desconhecida_e_recusada(repo):
    execucao_id = repo.abrir("normal", INICIO)
    with pytest.raises(ValueError):
        repo.fechar(execucao_id, "sucesso", INICIO, contagens={"coluna_inexistente; DROP TABLE x": 1})


def test_registrar_recusa(repo):
    execucao_id = repo.registrar_recusa(INICIO, "trava_ocupada")
    linha = repo.obter(execucao_id)
    assert linha["veredito"] == "recusada"
    assert linha["motivo"] == "trava_ocupada"
    assert linha["finalizado_em"] is not None


def test_modo_dry_run_e_registrado(repo):
    assert repo.obter(repo.abrir("dry_run", INICIO))["modo"] == "dry_run"


def test_registrar_leiloeiro_e_busca(repo):
    execucao_id = repo.abrir("normal", INICIO)
    repo.registrar_leiloeiro(execucao_id, "vip-leiloes", buscas_ok=1, lotes_novos=2, quebra_suspeita=False)
    repo.registrar_busca(execucao_id, RegistroBusca(
        busca_id="vip-leiloes:abc", leiloeiro_id="vip-leiloes", iniciado_em=INICIO, duracao_ms=95_000,
        status_http=200, nivel_usado="script", tentativas=1, paginas=17, veredito="ok",
        lotes_extraidos=201, lotes_descartados_parser=0))
    con = repo.con
    leiloeiro = con.execute("SELECT * FROM execucao_leiloeiro").fetchone()
    assert (leiloeiro["buscas_ok"], leiloeiro["lotes_novos"], leiloeiro["alerta_enviado"]) == (1, 2, 0)
    busca = con.execute("SELECT * FROM execucao_busca").fetchone()
    assert busca["nivel_usado"] == "script", "RF-03: o registro marca o nível script"
    assert busca["paginas"] == 17


def test_registrar_leiloeiro_de_novo_atualiza(repo):
    execucao_id = repo.abrir("normal", INICIO)
    repo.registrar_leiloeiro(execucao_id, "vip-leiloes", buscas_ok=1)
    repo.registrar_leiloeiro(execucao_id, "vip-leiloes", buscas_ok=1, alerta_enviado=True)
    linhas = repo.con.execute("SELECT alerta_enviado FROM execucao_leiloeiro").fetchall()
    assert [l["alerta_enviado"] for l in linhas] == [1]


def test_alerta_enviado_desde(repo):
    ontem = repo.abrir("normal", INICIO - timedelta(days=1))
    repo.registrar_leiloeiro(ontem, "vip-leiloes", quebra_suspeita=True, alerta_enviado=True)
    meia_noite = INICIO.replace(hour=3)  # 00:00 em São Paulo
    assert repo.alerta_enviado_desde("vip-leiloes", meia_noite) is False
    hoje = repo.abrir("normal", INICIO)
    repo.registrar_leiloeiro(hoje, "vip-leiloes", quebra_suspeita=True, alerta_enviado=True)
    assert repo.alerta_enviado_desde("vip-leiloes", meia_noite) is True
    assert repo.alerta_enviado_desde("outro", meia_noite) is False


def test_alerta_em_execucao_dry_run_nao_conta(repo):
    execucao_id = repo.abrir("dry_run", INICIO)
    repo.registrar_leiloeiro(execucao_id, "vip-leiloes", alerta_enviado=True)
    assert repo.alerta_enviado_desde("vip-leiloes", INICIO - timedelta(hours=1)) is False
