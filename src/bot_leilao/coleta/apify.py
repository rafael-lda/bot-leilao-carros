"""Cliente do nível `apify` (feature 005; interfaces/apify.md; roadmap D-86, D-88, D-89, D-91).

O bot não fala com o site: pede a um ator da loja do Apify que abra a URL num navegador capaz de passar pelo
desafio do Cloudflare e devolva o HTML renderizado. A operação é a mesma do `ClienteHTTP` (`requisitar`), então
adaptador, parser e enriquecimento não sabem por onde a página veio. O token vai só no cabeçalho.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit

import httpx

from bot_leilao.coleta.modelos import Requisicao, ResultadoHTTP, Veredito

log = logging.getLogger(__name__)

API = "https://api.apify.com/v2"
ATOR_PADRAO = "neatrat/cloudflare-scraper"
TIMEOUT_EXECUCAO_S = 180          # tempo máximo da execução no Apify; o httpx espera um pouco mais
# Só a página do desafio. As páginas liberadas também carregam o script `challenge-platform` do Cloudflare
# (visto nas 5 amostras de 2026-10-13), por isso essa marca do nível `script` não serve aqui.
_MARCAS_DESAFIO = ("Just a moment", "cf-chl", "Performing security verification")
_MARCAS_COTA = ("usage", "limit", "not-enough")


@dataclass(frozen=True)
class PerfilAtor:
    """Como montar a entrada e ler a saída de um ator (D-88): cada ator da loja tem o seu formato."""

    entrada: Callable[[str], dict]
    campo_conteudo: str
    campo_status: str


PERFIS_ATOR: dict[str, PerfilAtor] = {
    ATOR_PADRAO: PerfilAtor(entrada=lambda url: {"url": url}, campo_conteudo="content", campo_status="status"),
}


@dataclass(frozen=True)
class Consumo:
    """Gasto do Apify em dólares (D-91): o da varredura é a diferença entre a primeira e a última consulta."""

    gasto_varredura: float
    gasto_ciclo: float
    limite: float
    fim_ciclo: datetime | None


def validar_ator(ator: str) -> None:
    if ator not in PERFIS_ATOR:
        raise ValueError(f"ator do Apify '{ator}' sem perfil conhecido; aceitos: {', '.join(sorted(PERFIS_ATOR))}")


class ClienteApify:
    def __init__(
        self,
        token: str,
        transporte: httpx.BaseTransport | None = None,
        *,
        atores_por_host: Mapping[str, str] | None = None,
        intervalo_minimo: float = 5.0,
        tentativas: int = 2,
        espera_nova_tentativa: float = 10.0,
        timeout: float = TIMEOUT_EXECUCAO_S + 20.0,
        relogio: Callable[[], float] = time.monotonic,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self.atores = dict(atores_por_host or {})
        for ator in self.atores.values():
            validar_ator(ator)
        self.intervalo_minimo = intervalo_minimo
        self.tentativas = tentativas
        self.espera_nova_tentativa = espera_nova_tentativa
        self.relogio = relogio
        self.dormir = dormir
        self.execucoes = 0                       # execuções cobradas (resposta 201)
        self._ultimo_envio: dict[str, float] = {}
        self._uso_inicial: tuple | None = None
        self._consultou_inicio = False
        self._cliente = httpx.Client(transport=transporte, timeout=timeout,
                                     headers={"Authorization": f"Bearer {token}"})

    @property
    def cookies(self) -> dict:
        return {}  # os cookies devolvidos pelo ator (cf_clearance) são descartados

    def fechar(self) -> None:
        self._cliente.close()

    def _ator(self, url: str) -> str:
        return self.atores.get(urlsplit(url).hostname or "", ATOR_PADRAO)

    def _respeitar_intervalo(self, host: str) -> None:
        ultimo = self._ultimo_envio.get(host)
        if ultimo is not None:
            falta = ultimo + self.intervalo_minimo - self.relogio()
            if falta > 0:
                self.dormir(falta)
        self._ultimo_envio[host] = self.relogio()

    # --- Páginas ------------------------------------------------------------------------------

    def requisitar(self, req: Requisicao) -> ResultadoHTTP:
        if req.metodo.upper() != "GET" or req.dados:
            raise ValueError(f"o ator do Apify só faz GET de uma URL, sem corpo: {req.metodo} {req.url}")
        if not self._consultou_inicio:
            self._consultou_inicio = True
            self._uso_inicial = self._limites()
        ator = self._ator(req.url)
        host = urlsplit(req.url).hostname or ""
        inicio = self.relogio()
        tentativa = 0
        while True:
            tentativa += 1
            self._respeitar_intervalo(host)
            veredito, status, conteudo, motivo, repetir = self._uma_execucao(req.url, ator)
            if veredito is Veredito.OK or not repetir or tentativa >= self.tentativas:
                return ResultadoHTTP(veredito=veredito, status_http=status, conteudo=conteudo, tentativas=tentativa,
                                     duracao_ms=int((self.relogio() - inicio) * 1000), url=req.url, motivo=motivo)
            log.info("coleta  | apify | %s | tentativa %d/%d falhou (%s); nova tentativa em %.0fs",
                     host, tentativa, self.tentativas, motivo, self.espera_nova_tentativa)
            self.dormir(self.espera_nova_tentativa)

    def _uma_execucao(self, url: str, ator: str):
        """Devolve (veredito, status, conteudo, motivo, repetir). Contrato §4."""
        perfil = PERFIS_ATOR[ator]
        try:
            resposta = self._cliente.post(f"{API}/acts/{ator.replace('/', '~')}/run-sync-get-dataset-items",
                                          params={"timeout": str(TIMEOUT_EXECUCAO_S)}, json=perfil.entrada(url))
        except httpx.TimeoutException:
            return Veredito.FALHA_REDE, None, None, "apify: tempo esgotado", True
        except httpx.TransportError as erro:
            log.debug("coleta  | apify | erro de transporte: %s", type(erro).__name__)
            return Veredito.FALHA_REDE, None, None, "apify: plataforma indisponível", True

        status = resposta.status_code
        if status not in (200, 201):
            tipo, mensagem = self._erro(resposta)
            if status == 401:
                return Veredito.FALHA_AUTENTICACAO, status, None, "apify: token inválido", False
            if status in (402, 403) and any(m in f"{tipo} {mensagem}".lower() for m in _MARCAS_COTA):
                return Veredito.FALHA_REDE, status, None, "apify: cota esgotada", False
            if status == 408:
                return Veredito.FALHA_REDE, status, None, "apify: tempo esgotado", True
            if status >= 500:
                return Veredito.FALHA_REDE, status, None, "apify: plataforma indisponível", True
            return Veredito.FALHA_REDE, status, None, f"apify: http_{status} ({tipo or 'sem tipo'})", False

        self.execucoes += 1
        try:
            itens = resposta.json()
        except ValueError:
            itens = None
        item = itens[0] if isinstance(itens, list) and itens and isinstance(itens[0], dict) else None
        if item is None:
            return Veredito.FALHA_REDE, status, None, "apify: sem resultado", True
        conteudo = item.get(perfil.campo_conteudo) or ""
        status_site = item.get(perfil.campo_status)
        if status_site in (403, 503) or any(m in conteudo for m in _MARCAS_DESAFIO):
            return Veredito.BLOQUEADO, status_site, None, f"desafio_antibot (via apify: {ator})", True
        if isinstance(status_site, int) and status_site >= 400:
            return Veredito.FALHA_REDE, status_site, None, f"http_{status_site} (via apify)", False
        if not conteudo:
            return Veredito.FALHA_REDE, status_site, None, "apify: sem resultado", True
        return Veredito.OK, status_site or 200, conteudo.encode("utf-8"), None, False

    @staticmethod
    def _erro(resposta: httpx.Response) -> tuple[str, str]:
        try:
            erro = resposta.json().get("error") or {}
            return str(erro.get("type") or ""), str(erro.get("message") or "")
        except (ValueError, AttributeError):
            return "", ""

    # --- Consumo (D-91) -----------------------------------------------------------------------

    def _limites(self) -> tuple[float, float, datetime | None] | None:
        """(uso do ciclo, limite, fim do ciclo) de `GET /users/me/limits`; None se a consulta falhar."""
        try:
            resposta = self._cliente.get(f"{API}/users/me/limits")
            if resposta.status_code != 200:
                return None
            dados = resposta.json()["data"]
            fim = dados.get("monthlyUsageCycle", {}).get("endAt")
            return (float(dados["current"]["monthlyUsageUsd"]), float(dados["limits"]["maxMonthlyUsageUsd"]),
                    datetime.fromisoformat(fim.replace("Z", "+00:00")) if fim else None)
        except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError) as erro:
            log.info("coleta  | apify | consulta de consumo falhou: %s", type(erro).__name__)
            return None

    def consumo(self) -> Consumo | None:
        """Gasto da varredura e do ciclo. None se nenhuma página foi pedida ou se uma das consultas falhou."""
        if not self._consultou_inicio or self._uso_inicial is None:
            return None
        final = self._limites()
        if final is None:
            return None
        uso, limite, fim = final
        return Consumo(gasto_varredura=max(0.0, uso - self._uso_inicial[0]), gasto_ciclo=uso, limite=limite,
                       fim_ciclo=fim)
