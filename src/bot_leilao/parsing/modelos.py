"""Modelos do parsing (parser-lotes §9, com os campos novos de data-delta.md §1.4)."""

from __future__ import annotations

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


@dataclass
class ContextoParsing:
    leiloeiro_id: str
    busca_id: str
    base_url: str
    coletado_em: datetime
    tipo_leilao: str | None = None


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
