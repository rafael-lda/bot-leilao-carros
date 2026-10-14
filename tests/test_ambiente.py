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


# --- Feature 005: token do Apify (RF-02; roadmap D-90) ------------------------------------------------

TOKEN_APIFY = "apify_api_SegredoDeTesteComTamanhoSuficiente123"


def test_token_do_apify_lido_do_env_e_mascarado_como_segredo(raiz):
    _env(raiz, f"TELEGRAM_BOT_TOKEN={TOKEN}\nTELEGRAM_CHAT_ID=1\nAPIFY_TOKEN={TOKEN_APIFY}\n")
    ambiente = carregar_ambiente(raiz, environ={}, exigir_apify=("Milan Leilões",))
    assert ambiente.apify_token == TOKEN_APIFY
    assert TOKEN_APIFY in ambiente.segredos
    assert TOKEN in ambiente.segredos


def test_token_do_apify_tambem_vem_do_ambiente(raiz):
    ambiente = carregar_ambiente(raiz, environ={"TELEGRAM_BOT_TOKEN": TOKEN, "TELEGRAM_CHAT_ID": "1",
                                                "APIFY_TOKEN": TOKEN_APIFY})
    assert ambiente.apify_token == TOKEN_APIFY


@pytest.mark.parametrize("linha", ["", "APIFY_TOKEN=\n", "APIFY_TOKEN=   \n"])
def test_sem_token_do_apify_aborta_so_quando_exigido_citando_leiloeiro_e_variavel(raiz, linha):
    _env(raiz, f"TELEGRAM_BOT_TOKEN={TOKEN}\nTELEGRAM_CHAT_ID=1\n{linha}")
    assert carregar_ambiente(raiz, environ={}).apify_token is None, "sem leiloeiro pago, o token não é exigido"
    with pytest.raises(ErroConfiguracao) as erro:
        carregar_ambiente(raiz, environ={}, exigir_apify=("Milan Leilões",))
    assert "APIFY_TOKEN" in str(erro.value)
    assert "Milan Leilões" in str(erro.value)


def test_token_do_apify_exigido_mesmo_em_dry_run(raiz):
    with pytest.raises(ErroConfiguracao, match="APIFY_TOKEN"):
        carregar_ambiente(raiz, exigir_telegram=False, environ={}, exigir_apify=("Milan Leilões",))
    ambiente = carregar_ambiente(raiz, exigir_telegram=False, environ={"APIFY_TOKEN": TOKEN_APIFY},
                                 exigir_apify=("Milan Leilões",))
    assert ambiente.segredos == [TOKEN_APIFY]
