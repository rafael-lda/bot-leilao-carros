"""Envio pela Bot API do Telegram (notificador-telegram RF-04, RF-05, RF-09; interfaces/telegram-bot-api.md).

O token faz parte da URL da API: nenhuma mensagem de erro deste módulo inclui texto de exceção
do httpx, e tudo passa por `mascarar` antes de sair (RN-08).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import httpx

from bot_leilao.logsetup import mascarar

log = logging.getLogger(__name__)
API = "https://api.telegram.org"


@dataclass
class ResultadoEnvio:
    ok: bool
    blocos_enviados: int
    erro: str | None = None
    definitivo: bool = False


class NotificadorTelegram:
    def __init__(
        self,
        token: str,
        chat_id: int,
        transporte: httpx.BaseTransport | None = None,
        *,
        tentativas: int = 3,
        timeout: float = 20.0,
        esperas: Sequence[float] = (2.0, 4.0),
        espera_entre_blocos: float = 1.0,
        espera_max_retry_after: float = 60.0,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self._token = token
        self.chat_id = chat_id
        self.tentativas = tentativas
        self.esperas = tuple(esperas)
        self.espera_entre_blocos = espera_entre_blocos
        self.espera_max_retry_after = espera_max_retry_after
        self.dormir = dormir
        self._cliente = httpx.Client(transport=transporte, timeout=timeout)

    def _seguro(self, texto: str) -> str:
        return mascarar(texto, [self._token])

    def _uma_tentativa(self, texto: str) -> tuple[bool, str | None, bool, float | None]:
        """(ok, erro, definitivo, retry_after)."""
        corpo = {"chat_id": self.chat_id, "text": texto, "parse_mode": "HTML",
                 "link_preview_options": {"is_disabled": True}}
        try:
            resposta = self._cliente.post(f"{API}/bot{self._token}/sendMessage", json=corpo)
        except httpx.TimeoutException:
            return False, "timeout ao falar com o Telegram", False, None
        except httpx.TransportError as erro:
            return False, f"falha de conexão com o Telegram ({type(erro).__name__})", False, None

        try:
            dados = resposta.json()
        except ValueError:
            dados = {}
        descricao = self._seguro(str(dados.get("description", "")))
        status = resposta.status_code

        if status == 200 and dados.get("ok") is True:
            return True, None, False, None
        if status == 200:
            return False, f"o Telegram não confirmou o envio: {descricao or 'resposta sem ok'}", True, None
        if status == 429:
            retry_after = (dados.get("parameters") or {}).get("retry_after")
            return False, "limite de taxa do Telegram (429)", False, float(retry_after or 0) or None
        if status == 401:
            return False, ("token do bot inválido ou revogado (401): gere um novo com o @BotFather "
                           "e atualize TELEGRAM_BOT_TOKEN no .env"), True, None
        if status == 403:
            return False, (f"o bot foi bloqueado ou não pode escrever no chat {self.chat_id} (403): {descricao}. "
                           "Desbloqueie o bot e mande uma mensagem a ele"), True, None
        if status == 400:
            return False, f"o Telegram recusou o envio para o chat {self.chat_id} (400): {descricao}", True, None
        if status >= 500:
            return False, f"Telegram indisponível ({status})", False, None
        return False, f"resposta inesperada do Telegram ({status}): {descricao}", True, None

    def _enviar_um(self, texto: str) -> tuple[bool, str | None, bool]:
        erro, definitivo = None, False
        for tentativa in range(1, self.tentativas + 1):
            ok, erro, definitivo, retry_after = self._uma_tentativa(texto)
            if ok:
                return True, None, False
            if definitivo or tentativa == self.tentativas:
                break
            if retry_after is not None:
                espera = min(retry_after, self.espera_max_retry_after)
            else:
                espera = self.esperas[min(tentativa - 1, len(self.esperas) - 1)]
            log.info("notif   | tentativa %d/%d falhou (%s); nova tentativa em %.0fs",
                     tentativa, self.tentativas, self._seguro(erro or ""), espera)
            self.dormir(espera)
        return False, self._seguro(erro or "falha desconhecida"), definitivo

    def enviar(self, blocos: Sequence[str]) -> ResultadoEnvio:
        """Confirma só depois do aceite do último bloco (RF-05, EC-07)."""
        for indice, bloco in enumerate(blocos):
            if indice:
                self.dormir(self.espera_entre_blocos)
            ok, erro, definitivo = self._enviar_um(bloco)
            if not ok:
                log.error("notif   | envio falhou no bloco %d de %d: %s", indice + 1, len(blocos), erro)
                return ResultadoEnvio(ok=False, blocos_enviados=indice, erro=erro, definitivo=definitivo)
        return ResultadoEnvio(ok=True, blocos_enviados=len(blocos))

    def testar(self) -> ResultadoEnvio:
        return self.enviar(["<b>Bot Leilão Carros</b>: mensagem de teste. A configuração do Telegram está OK."])

    def fechar(self) -> None:
        self._cliente.close()
