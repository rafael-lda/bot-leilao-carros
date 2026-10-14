"""Variáveis de ambiente e `.env` (notificador-telegram §10; interfaces/arquivos-configuracao.md §4)."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from bot_leilao.config.arquivos import ErroConfiguracao

_FORMATO_TOKEN = re.compile(r"^\d+:[A-Za-z0-9_-]{30,}$")


@dataclass
class Ambiente:
    telegram_token: str | None
    telegram_chat_id: int | None
    apify_token: str | None = None      # feature 005 (D-90)

    @property
    def segredos(self) -> list[str]:
        return [s for s in (self.telegram_token, self.apify_token) if s]


def carregar_ambiente(raiz: Path, exigir_telegram: bool = True, environ: Mapping[str, str] | None = None,
                      exigir_apify: Sequence[str] = ()) -> Ambiente:
    """Lê `raiz/.env` sem sobrescrever o ambiente: variável já exportada vence o arquivo.

    `exigir_apify`: nomes dos leiloeiros em nível `apify` incluídos na varredura; com algum, `APIFY_TOKEN` é
    obrigatório (também em dry-run, que coleta de verdade).
    """
    exportadas = os.environ if environ is None else environ
    arquivo = raiz / ".env"
    valores: dict[str, str] = {}
    if arquivo.exists():
        valores.update({k: v for k, v in dotenv_values(arquivo, encoding="utf-8").items() if v is not None})
    valores.update(exportadas)

    token = (valores.get("TELEGRAM_BOT_TOKEN") or "").strip() or None
    chat = (valores.get("TELEGRAM_CHAT_ID") or "").strip() or None
    apify = (valores.get("APIFY_TOKEN") or "").strip() or None
    if exigir_apify and apify is None:
        raise ErroConfiguracao(f"APIFY_TOKEN ausente ou vazio no .env, e a varredura inclui leiloeiro em nível apify "
                               f"({', '.join(exigir_apify)}). Copie o token em console.apify.com → Settings → "
                               "API & Integrations para o .env, ou rode a varredura com --sem-pagos.")

    if not exigir_telegram and token is None and chat is None:
        return Ambiente(telegram_token=None, telegram_chat_id=None, apify_token=apify)

    if token is None:
        raise ErroConfiguracao("TELEGRAM_BOT_TOKEN ausente ou vazio no .env. Veja o .env.example e o onboarding.md, passo 3.")
    if not _FORMATO_TOKEN.match(token):
        raise ErroConfiguracao("TELEGRAM_BOT_TOKEN não tem o formato de token do BotFather (número:código). "
                               "Copie o token de novo da conversa com o @BotFather.")
    if chat is None:
        raise ErroConfiguracao("TELEGRAM_CHAT_ID ausente ou vazio no .env. Veja o onboarding.md, passo 3.")
    try:
        chat_id = int(chat)
    except ValueError:
        raise ErroConfiguracao(f"TELEGRAM_CHAT_ID ({chat!r}) deve ser um número inteiro.") from None
    return Ambiente(telegram_token=token, telegram_chat_id=chat_id, apify_token=apify)
