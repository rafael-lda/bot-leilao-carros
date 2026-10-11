"""Veículos-alvo (spec configuracao-veiculos-alvo; RF-01 e RF-16 da feature)."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from bot_leilao.config.arquivos import EXEMPLO_VEICULOS, ErroConfiguracao, garantir_arquivo, ler_yaml
from bot_leilao.texto import gerar_id

TIPOS_LEILAO = ("judicial", "extrajudicial", "financiamento", "seguradora", "recuperado")
ANO_MINIMO_PLAUSIVEL = 1900
ANO_MAXIMO_PLAUSIVEL = 2100


@dataclass(frozen=True)
class VeiculoAlvo:
    id: str
    marca: str
    modelo: str
    ano_min: int
    ano_max: int
    preco_maximo: Decimal
    tipos_leilao: tuple[str, ...]
    quilometragem_maxima: int | None
    ativo: bool
    excluir: tuple[str, ...] = ()   # palavras que, no modelo ou no título do lote, impedem o casamento (D-72)

    @property
    def nome(self) -> str:
        return f"{self.marca} {self.modelo}"


@dataclass
class ResultadoVeiculos:
    ativos: list[VeiculoAlvo]
    inativos: int = 0
    avisos: list[str] = field(default_factory=list)


def _erro(nome: str, mensagem: str) -> ErroConfiguracao:
    return ErroConfiguracao(f"Configuração inválida em '{nome}': {mensagem}. Execução abortada.")


def _texto(bloco: dict, campo: str, nome: str) -> str:
    valor = bloco.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise _erro(nome, f"{campo} é obrigatório e não pode ser vazio")
    return valor.strip()


def _inteiro(valor: Any) -> int | None:
    if isinstance(valor, bool) or not isinstance(valor, int):
        return None
    return valor


def _ano(bloco: dict, campo: str, nome: str) -> int:
    ano = _inteiro(bloco.get(campo))
    if ano is None or not ANO_MINIMO_PLAUSIVEL <= ano <= ANO_MAXIMO_PLAUSIVEL:
        raise _erro(nome, f"{campo} ({bloco.get(campo)!r}) deve ser um ano de quatro dígitos")
    return ano


def _preco(bloco: dict, nome: str) -> Decimal:
    valor = bloco.get("preco_maximo")
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise _erro(nome, f"preco_maximo ({valor!r}) é obrigatório e deve ser um número maior que zero")
    try:
        preco = Decimal(str(valor))
    except InvalidOperation:
        raise _erro(nome, f"preco_maximo ({valor!r}) não é um número") from None
    if preco <= 0:
        raise _erro(nome, f"preco_maximo ({valor!r}) deve ser maior que zero")
    return preco


def _km(bloco: dict, nome: str) -> int | None:
    if bloco.get("quilometragem_maxima") is None:
        return None
    km = _inteiro(bloco["quilometragem_maxima"])
    if km is None or km <= 0:
        raise _erro(nome, f"quilometragem_maxima ({bloco['quilometragem_maxima']!r}) deve ser um inteiro maior que zero, "
                          "ou ser omitida para não limitar")
    return km


def _excluir(bloco: dict, nome: str) -> tuple[str, ...]:
    valor = bloco.get("excluir")
    if valor is None:
        return ()
    palavras = [valor] if isinstance(valor, str) else valor
    if not isinstance(palavras, list) or not all(isinstance(p, str) and p.strip() for p in palavras):
        raise _erro(nome, f"excluir ({valor!r}) deve ser uma palavra ou uma lista de palavras não vazias, ex.: [Oroch]")
    return tuple(p.strip() for p in palavras)


def _tipos(bloco: dict, nome: str) -> tuple[str, ...]:
    valor = bloco.get("tipos_leilao")
    aceitos = ", ".join(TIPOS_LEILAO)
    if not isinstance(valor, list) or not valor:
        raise _erro(nome, f"tipos_leilao deve listar ao menos um de: {aceitos}")
    tipos = []
    for tipo in valor:
        if tipo not in TIPOS_LEILAO:
            raise _erro(nome, f"tipos_leilao tem o valor inválido {tipo!r}; aceitos: {aceitos}")
        if tipo not in tipos:
            tipos.append(tipo)
    return tuple(tipos)


def _alvo(bloco: Any, posicao: int) -> VeiculoAlvo:
    if not isinstance(bloco, dict):
        raise ErroConfiguracao(f"Configuração inválida: o item {posicao} de 'veiculos' não é um bloco de campos.")
    nome = f"{bloco.get('marca', '?')} {bloco.get('modelo', '?')}"
    marca = _texto(bloco, "marca", nome)
    modelo = _texto(bloco, "modelo", nome)
    ano_min = _ano(bloco, "ano_min", nome)
    ano_max = _ano(bloco, "ano_max", nome)
    if ano_min > ano_max:
        raise _erro(nome, f"ano_min ({ano_min}) é maior que ano_max ({ano_max})")
    ativo = bloco.get("ativo", True)
    if not isinstance(ativo, bool):
        raise _erro(nome, f"ativo ({ativo!r}) deve ser true ou false")
    return VeiculoAlvo(
        id=gerar_id(marca, modelo, ano_min, ano_max),
        marca=marca,
        modelo=modelo,
        ano_min=ano_min,
        ano_max=ano_max,
        preco_maximo=_preco(bloco, nome),
        tipos_leilao=_tipos(bloco, nome),
        quilometragem_maxima=_km(bloco, nome),
        ativo=ativo,
        excluir=_excluir(bloco, nome),
    )


def carregar_veiculos(caminho: Path) -> ResultadoVeiculos:
    garantir_arquivo(caminho, EXEMPLO_VEICULOS)
    dados = ler_yaml(caminho)
    if not isinstance(dados, dict) or not isinstance(dados.get("veiculos"), list):
        raise ErroConfiguracao(f"{caminho.name} precisa ter uma lista 'veiculos' na raiz. Execução abortada.")

    resultado = ResultadoVeiculos(ativos=[])
    vistos: set[str] = set()
    for posicao, bloco in enumerate(dados["veiculos"], start=1):
        alvo = _alvo(bloco, posicao)
        if alvo.id in vistos:
            resultado.avisos.append(f"Veículo-alvo duplicado '{alvo.nome}' ({alvo.ano_min}–{alvo.ano_max}): "
                                    "mantida a primeira ocorrência.")
            continue
        vistos.add(alvo.id)
        if alvo.ativo:
            resultado.ativos.append(alvo)
        else:
            resultado.inativos += 1

    if not resultado.ativos:
        resultado.avisos.append("Nenhum veículo-alvo ativo. Nada a procurar nesta execução.")
    return resultado
