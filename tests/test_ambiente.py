"""Variáveis do .env (notificador-telegram §10; interfaces/arquivos-configuracao.md §4)."""

import pytest

from apoio import escrever
from bot_leilao.config.ambiente import carregar_ambiente
from bot_leilao.config.arquivos import ErroConfiguracao

TOKEN = "123456789:AAHsegredoDeTesteComTamanhoSuficiente_x"


def _env(raiz, texto):
    escrever(raiz / ".env", texto)


def test_carrega_token_e_chat_id_do_env(raiz):
    _env(raiz, f"TELEGRAM_BOT_TOKEN={TOKEN}\nTELEGRAM_CHAT_ID=-100123\n")
    ambiente = carregar_ambiente(raiz, environ={})
    assert ambiente.telegram_token == TOKEN
    assert ambiente.telegram_chat_id == -100123
    assert ambiente.segredos == [TOKEN]


def test_variavel_exportada_vence_o_env(raiz):
    _env(raiz, f"TELEGRAM_BOT_TOKEN={TOKEN}\nTELEGRAM_CHAT_ID=1\n")
    ambiente = carregar_ambiente(raiz, environ={"TELEGRAM_CHAT_ID": "42"})
    assert ambiente.telegram_chat_id == 42


def test_funciona_sem_arquivo_env(raiz):
    ambiente = carregar_ambiente(raiz, environ={"TELEGRAM_BOT_TOKEN": TOKEN, "TELEGRAM_CHAT_ID": "7"})
    assert ambiente.telegram_chat_id == 7


@pytest.mark.parametrize("conteudo, variavel", [
    ("TELEGRAM_CHAT_ID=1\n", "TELEGRAM_BOT_TOKEN"),
    (f"TELEGRAM_BOT_TOKEN={TOKEN}\n", "TELEGRAM_CHAT_ID"),
    ("TELEGRAM_BOT_TOKEN=\nTELEGRAM_CHAT_ID=1\n", "TELEGRAM_BOT_TOKEN"),
    (f"TELEGRAM_BOT_TOKEN={TOKEN}\nTELEGRAM_CHAT_ID=abc\n", "TELEGRAM_CHAT_ID"),
])
def test_ausente_vazia_ou_invalida_aborta_citando_a_variavel(raiz, conteudo, variavel):
    _env(raiz, conteudo)
    with pytest.raises(ErroConfiguracao) as erro:
        carregar_ambiente(raiz, environ={})
    assert variavel in str(erro.value)


def test_token_malformado_e_rejeitado_sem_expor_o_valor(raiz):
    malformado = "nao-e-um-token-valido-mas-e-secreto"
    _env(raiz, f"TELEGRAM_BOT_TOKEN={malformado}\nTELEGRAM_CHAT_ID=1\n")
    with pytest.raises(ErroConfiguracao) as erro:
        carregar_ambiente(raiz, environ={})
    assert "TELEGRAM_BOT_TOKEN" in str(erro.value)
    assert malformado not in str(erro.value)


def test_dry_run_dispensa_variaveis_do_telegram(raiz):
    ambiente = carregar_ambiente(raiz, exigir_telegram=False, environ={})
    assert ambiente.telegram_token is None
    assert ambiente.segredos == []
