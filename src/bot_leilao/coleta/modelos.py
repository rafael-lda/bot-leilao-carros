"""Modelos do coletor (coletor-lotes v1.1 §9)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Mapping, Protocol

if TYPE_CHECKING:
    from bot_leilao.coleta.http import ClienteHTTP


class Veredito(StrEnum):
    OK = "ok"
    BLOQUEADO = "bloqueado"
    FALHA_REDE = "falha_rede"
    FALHA_AUTENTICACAO = "falha_autenticacao"


@dataclass
class Requisicao:
    metodo: str
    url: str
    dados: dict | None = None
    cabecalhos: dict | None = None
    anotacoes: dict | None = None      # para o parser, não vai para a rede (feature 002, D-37)


@dataclass
class ResultadoHTTP:
    veredito: Veredito
    status_http: int | None
    conteudo: bytes | None
    tentativas: int
    duracao_ms: int
    url: str
    motivo: str | None = None

    @property
    def ok(self) -> bool:
        return self.veredito is Veredito.OK


@dataclass
class Pagina:
    numero: int
    metodo: str
    url: str
    conteudo: bytes
    anotacoes: dict = field(default_factory=dict)


@dataclass
class RespostaBruta:
    busca_id: str
    leiloeiro_id: str
    iniciado_em: datetime
    duracao_ms: int
    status_http: int | None
    paginas: list[Pagina] = field(default_factory=list)
    nivel_usado: str = "script"
    tentativas: int = 0
    veredito: Veredito = Veredito.OK
    motivo: str | None = None

    @property
    def bloqueado(self) -> bool:
        return self.veredito is Veredito.BLOQUEADO


class Adaptador(Protocol):
    """Conhecimento de um leiloeiro sobre como receber uma busca (coletor-lotes RF-12)."""

    leiloeiro_id: str

    def preparar_sessao(self, cliente: "ClienteHTTP") -> ResultadoHTTP | None: ...

    def montar_requisicao(self, filtros: Mapping, pagina: int) -> Requisicao: ...

    def tem_proxima_pagina(self, conteudo: bytes, pagina: int) -> bool: ...

    def validar_filtros(self, filtros: Mapping) -> None: ...

    def tipo_leilao_da_busca(self, filtros: Mapping) -> str | None: ...

    # Opcionais, lidos com getattr (feature 002): `teto_paginas: int` (D-47) e
    # `requisicao_detalhe(lote) -> Requisicao | None` (enriquecimento, D-48).
