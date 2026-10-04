"""Cliente HTTP do nível `script` (coletor-lotes v1.1 RF-02, RF-06 a RF-08, RF-13; roadmap D-02, D-30)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from urllib.parse import urlsplit

import httpx

from bot_leilao.coleta.modelos import Requisicao, ResultadoHTTP, Veredito

log = logging.getLogger(__name__)

# D-30: cabeçalho de navegador comum, definido só aqui. Sem autoidentificação como robô,
# sem rotação de User-Agent, sem resolver CAPTCHA (decisão do Rafael em 2026-09-22).
CABECALHOS_NAVEGADOR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

_MARCAS_DESAFIO = (b"cf-chl", b"Just a moment", b"challenge-platform")
_MEBIBYTE = 1024 * 1024


class ClienteHTTP:
    """Sessão com cookies, limite de redirecionamentos, retry e espaçamento por host."""

    def __init__(
        self,
        transporte: httpx.BaseTransport | None = None,
        *,
        intervalo_minimo: float = 5.0,
        tentativas: int = 3,
        timeout: float = 30.0,
        max_redirecionamentos: int = 3,
        limite_bytes: int = 20 * _MEBIBYTE,
        esperas: Sequence[float] = (5.0, 15.0),
        espera_max_retry_after: float = 60.0,
        espera_429: float = 30.0,
        relogio: Callable[[], float] = time.monotonic,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self.intervalo_minimo = intervalo_minimo
        self.tentativas = tentativas
        self.limite_bytes = limite_bytes
        self.esperas = tuple(esperas)
        self.espera_max_retry_after = espera_max_retry_after
        # Observado em 2026-10-04: o Vip devolveu 429 na 17ª requisição a 5 s de intervalo, sem Retry-After.
        # Sem indicação do site, uma pausa maior é mais respeitosa que insistir no intervalo mínimo.
        self.espera_429 = espera_429
        self.relogio = relogio
        self.dormir = dormir
        self._ultimo_envio: dict[str, float] = {}
        self._cliente = httpx.Client(
            transport=transporte,
            headers=CABECALHOS_NAVEGADOR,
            follow_redirects=True,
            max_redirects=max_redirecionamentos,
            timeout=timeout,
        )

    @property
    def cookies(self) -> httpx.Cookies:
        return self._cliente.cookies

    def fechar(self) -> None:
        self._cliente.close()

    def __enter__(self) -> "ClienteHTTP":
        return self

    def __exit__(self, *_exc) -> None:
        self.fechar()

    def _respeitar_intervalo(self, host: str) -> None:
        ultimo = self._ultimo_envio.get(host)
        if ultimo is not None:
            falta = ultimo + self.intervalo_minimo - self.relogio()
            if falta > 0:
                self.dormir(falta)
        self._ultimo_envio[host] = self.relogio()

    def _uma_tentativa(self, req: Requisicao, host: str):
        """Devolve (veredito, status, conteudo, url_final, motivo, repetir, retry_after)."""
        try:
            with self._cliente.stream(req.metodo, req.url, data=req.dados, headers=req.cabecalhos) as resposta:
                partes: list[bytes] = []
                total = 0
                for parte in resposta.iter_bytes():
                    total += len(parte)
                    if total > self.limite_bytes:
                        return Veredito.FALHA_REDE, resposta.status_code, None, str(resposta.url), "resposta_grande", False, None
                    partes.append(parte)
                corpo = b"".join(partes)
                status, url_final, cabecalhos = resposta.status_code, str(resposta.url), resposta.headers
        except httpx.TooManyRedirects:
            return Veredito.FALHA_REDE, None, None, req.url, "laco_redirecionamento", True, None
        except httpx.TimeoutException:
            return Veredito.FALHA_REDE, None, None, req.url, "timeout", True, None
        except httpx.TransportError as erro:
            log.debug("coleta  | erro de transporte em %s: %s", host, type(erro).__name__)
            return Veredito.FALHA_REDE, None, None, req.url, f"conexao: {host} ({type(erro).__name__})", True, None

        if status in (403, 503) and any(m in corpo for m in _MARCAS_DESAFIO):
            return Veredito.BLOQUEADO, status, None, url_final, "desafio_antibot", True, None
        if status in (403, 429):
            retry_after = None
            if status == 429:
                try:
                    retry_after = float(cabecalhos.get("Retry-After", ""))
                except ValueError:
                    retry_after = self.espera_429
            return Veredito.BLOQUEADO, status, None, url_final, f"http_{status}", True, retry_after
        if status >= 500:
            return Veredito.FALHA_REDE, status, None, url_final, f"http_{status}", True, None
        if status >= 300:
            return Veredito.FALHA_REDE, status, None, url_final, f"http_{status}", False, None
        if not corpo:
            return Veredito.FALHA_REDE, status, None, url_final, "conteudo_vazio", False, None
        return Veredito.OK, status, corpo, url_final, None, False, None

    def requisitar(self, req: Requisicao) -> ResultadoHTTP:
        host = urlsplit(req.url).hostname or ""
        inicio = self.relogio()
        tentativa = 0
        while True:
            tentativa += 1
            self._respeitar_intervalo(host)
            veredito, status, conteudo, url, motivo, repetir, retry_after = self._uma_tentativa(req, host)
            if veredito is Veredito.OK or not repetir or tentativa >= self.tentativas:
                return ResultadoHTTP(veredito=veredito, status_http=status, conteudo=conteudo, tentativas=tentativa,
                                     duracao_ms=int((self.relogio() - inicio) * 1000), url=url, motivo=motivo)
            if retry_after is not None:
                espera = min(retry_after, self.espera_max_retry_after)
            else:
                espera = self.esperas[min(tentativa - 1, len(self.esperas) - 1)]
            log.info("coleta  | %s | tentativa %d/%d falhou (%s); nova tentativa em %.0fs",
                     host, tentativa, self.tentativas, motivo, espera)
            self.dormir(espera)
