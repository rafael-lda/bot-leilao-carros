"""Linha de comando (interfaces/cli.md; RF-14 da feature; roadmap D-25)."""

import pytest

from apoio import escrever, pagina_vazia, pagina_vip
from bot_leilao.cli import principal
from bot_leilao.db.trava import Trava


def _rodar(cenario, *args):
    return principal([*args, "--raiz", str(cenario.raiz)], deps=cenario.deps)


def test_varrer_com_sucesso_sai_com_zero(cenario):
    cenario.vip = pagina_vazia()
    assert _rodar(cenario, "varrer") == 0


def test_configuracao_invalida_sai_com_um(cenario):
    escrever(cenario.raiz / "config" / "veiculos-alvo.yaml", "veiculos: [1]\n")
    assert _rodar(cenario, "varrer") == 1


def test_uso_incorreto_sai_com_dois():
    with pytest.raises(SystemExit) as saida:
        principal(["comando-que-nao-existe"])
    assert saida.value.code == 2


def test_trava_ocupada_sai_com_tres(cenario):
    trava = Trava(cenario.raiz / "dados" / "varredura.lock", agora=cenario.agora)
    trava.adquirir()
    try:
        assert _rodar(cenario, "varrer") == 3
    finally:
        trava.liberar()


def test_pasta_vazia_cria_exemplos_e_orienta(tmp_path, capsys):
    assert principal(["varrer", "--raiz", str(tmp_path)]) == 1
    assert (tmp_path / "config" / "veiculos-alvo.yaml").exists()
    assert (tmp_path / "config" / "leiloeiros.yaml").exists()
    assert "Criei arquivo(s) de exemplo" in capsys.readouterr().out


def test_exemplos_recem_criados_rodam_sem_varrer(tmp_path):
    """Passo 4 do onboarding: exemplos vêm com tudo inativo."""
    principal(["varrer", "--raiz", str(tmp_path)])
    assert principal(["varrer", "--raiz", str(tmp_path), "--dry-run"]) == 0


def test_dry_run_imprime_o_digest_e_nao_envia(cenario, capsys):
    cenario.vip = pagina_vazia()
    _rodar(cenario, "varrer")
    cenario.vip = pagina_vip()
    capsys.readouterr()

    assert _rodar(cenario, "varrer", "--dry-run") == 0
    saida = capsys.readouterr().out
    assert "DRY-RUN" in saida
    assert "Digest que seria enviado" in saida
    assert "Versa" in saida
    assert cenario.mensagens == []
    assert cenario.notificados() == []


def test_dry_run_dispensa_o_telegram_no_env(cenario, capsys):
    cenario.deps.environ = {}
    cenario.vip = pagina_vip()
    assert _rodar(cenario, "varrer", "--dry-run") == 0
    assert "semeadura" in capsys.readouterr().out


def test_testar_telegram(cenario):
    assert _rodar(cenario, "testar-telegram") == 0
    (mensagem,) = cenario.mensagens
    assert "teste" in mensagem.lower()


def test_testar_telegram_com_token_invalido_sai_com_um(cenario):
    cenario.telegram = 401
    assert _rodar(cenario, "testar-telegram") == 1


def test_testar_telegram_sem_env_sai_com_um(cenario):
    cenario.deps.environ = {}
    assert _rodar(cenario, "testar-telegram") == 1


def test_log_em_arquivo(cenario):
    cenario.vip = pagina_vazia()
    _rodar(cenario, "varrer")
    log = (cenario.raiz / "dados" / "logs" / "bot-leilao.log").read_text(encoding="utf-8")
    assert "coleta  | Vip Leilões" in log
    assert "exec    | sucesso" in log
