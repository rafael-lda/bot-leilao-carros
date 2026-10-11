"""Modelos do parsing (parser-lotes §9, com os campos novos de data-delta.md §1.4)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class Lote:
    id_canonico: str | None
    leiloeiro_id: str
    busca_id: str
    link: str | None
    coletado_em: datetime
    numero_lote: str | None = None
    titulo: str | None = None          # marca e modelo para exibição, como vieram do leiloeiro
    marca: str | None = None           # canônica, minúsculas, sem acento
    modelo: str | None = None          # minúsculas, sem acento
    ano_fabricacao: int | None = None
    ano_modelo: int | None = None
    lance_inicial: Decimal | None = None
    lance_corrente: Decimal | None = None
    quilometragem: int | None = None
    descricao: str | None = None
    tipo_leilao: str | None = None
    situacao: str | None = None
    retirado: bool = False
    # Feature 002 (data-delta §1.1): leilão por evento e detalhe do lote. O Vip deixa todos em None.
    evento_id: str | None = None
    pregao_em: datetime | None = None
    observacoes: str | None = None     # estado do lote, como o leiloeiro escreveu
    despesas_adm: Decimal | None = None
    placa_parcial: str | None = None
    local_documento: str | None = None
    detalhe_lido: bool | None = None   # None: não se aplica; False: o detalhe falhou; True: lido
    # Feature 003 (data-delta §1.1): onde o veículo está e o valor FIPE informado pelo leiloeiro.
    patio: str | None = None
    fipe: Decimal | None = None


@dataclass
class ContextoParsing:
    leiloeiro_id: str
    busca_id: str
    base_url: str
    coletado_em: datetime
    tipo_leilao: str | None = None
    pagina: Mapping[str, object] = field(default_factory=dict)   # anotações da página em leitura (D-37)


@dataclass
class ExtracaoPagina:
    lotes: list[Lote]
    busca_vazia: bool = False          # o site declarou que não há resultados (D-31)
    total_informado: int | None = None


@dataclass
class ResultadoParsing:
    busca_id: str
    leiloeiro_id: str
    lotes: list[Lote] = field(default_factory=list)
    descartados: int = 0
    quebra_suspeita: bool = False
    motivo_quebra: str | None = None
    tamanho_conteudo: int = 0
    sem_conteudo: bool = False
