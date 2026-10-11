"""Critérios do motor de filtros (RN-01 a RN-04, RN-11, RN-12; motor-filtros RF-01 a RF-08, RF-11; roadmap D-19)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from bot_leilao.config.veiculos import VeiculoAlvo
from bot_leilao.parsing.marcas import SINONIMOS
from bot_leilao.parsing.modelos import Lote
from bot_leilao.texto import normalizar_texto


@dataclass
class Candidato:
    lote: Lote
    alvo: VeiculoAlvo
    preco_a_confirmar: bool
    km_a_confirmar: bool

    @property
    def preco(self) -> Decimal | None:
        """Lance corrente; sem lance, o inicial (RN-03)."""
        return self.lote.lance_corrente if self.lote.lance_corrente is not None else self.lote.lance_inicial


@dataclass
class ResultadoCriterios:
    candidatos: list[Candidato] = field(default_factory=list)
    vistos: int = 0
    descartados_retirados: int = 0
    descartados_dado_ausente: int = 0
    descartados_sem_casar: int = 0
    descartados_acima_km: int = 0


def _marca(marca: str | None) -> str:
    """Tradução pela tabela comum, sem log: a marca do lote já chega canônica do parser."""
    normalizada = normalizar_texto(marca)
    return SINONIMOS.get(normalizada, normalizada)


def _casa_sem_km(lote: Lote, alvo: VeiculoAlvo) -> bool:
    marca_alvo = _marca(alvo.marca)
    if not marca_alvo or marca_alvo not in _marca(lote.marca):
        return False
    if normalizar_texto(alvo.modelo) not in normalizar_texto(lote.modelo):
        return False
    if alvo.excluir:  # RF-10 da feature 003 (D-72): pelo modelo e pelo título
        texto = f"{normalizar_texto(lote.modelo)} {normalizar_texto(lote.titulo)}"
        if any(normalizar_texto(palavra) in texto for palavra in alvo.excluir):
            return False
    if lote.ano_modelo is None or not alvo.ano_min <= lote.ano_modelo <= alvo.ano_max:
        return False
    preco = lote.lance_corrente if lote.lance_corrente is not None else lote.lance_inicial
    if preco is not None and preco > alvo.preco_maximo:
        return False
    return lote.tipo_leilao is not None and lote.tipo_leilao in alvo.tipos_leilao


def _km_ok(lote: Lote, alvo: VeiculoAlvo) -> bool:
    return alvo.quilometragem_maxima is None or lote.quilometragem is None or lote.quilometragem <= alvo.quilometragem_maxima


def casa(lote: Lote, alvo: VeiculoAlvo) -> bool:
    """Todos os critérios de RN-01 para um mesmo alvo."""
    return _casa_sem_km(lote, alvo) and _km_ok(lote, alvo)


def avaliar(lotes: Sequence[Lote], alvos: Sequence[VeiculoAlvo]) -> ResultadoCriterios:
    resultado = ResultadoCriterios(vistos=len(lotes))
    if not alvos:
        return resultado
    for lote in lotes:
        if lote.retirado:
            resultado.descartados_retirados += 1
            continue
        if lote.ano_modelo is None:
            resultado.descartados_dado_ausente += 1
            continue
        escolhido = next((alvo for alvo in alvos if casa(lote, alvo)), None)
        if escolhido is not None:
            resultado.candidatos.append(Candidato(
                lote=lote,
                alvo=escolhido,
                preco_a_confirmar=lote.lance_corrente is None and lote.lance_inicial is None,
                km_a_confirmar=escolhido.quilometragem_maxima is not None and lote.quilometragem is None,
            ))
        elif any(_casa_sem_km(lote, alvo) for alvo in alvos):
            resultado.descartados_acima_km += 1
        else:
            resultado.descartados_sem_casar += 1
    return resultado
