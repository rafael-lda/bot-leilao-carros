"""Cadastro de leiloeiros (spec cadastro-leiloeiros v1.3; RF-02 da feature; roadmap D-12, D-17, D-18, D-24)."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bot_leilao.coleta.apify import validar_ator
from bot_leilao.config.arquivos import EXEMPLO_LEILOEIROS, ErroConfiguracao, garantir_arquivo, ler_yaml
from bot_leilao.texto import gerar_id

NIVEIS_COLETA = ("script", "apify", "apify_residencial")
NIVEIS_IMPLEMENTADOS = ("script", "apify")  # feature 005 (D-90)
INTERVALO_MAXIMO_HORAS = 720                # 30 dias (D-101)
ESTRATEGIAS_ACESSO = ("publico", "logado")
ESTRATEGIAS_IMPLEMENTADAS = ("publico",)
FREQUENCIA_PADRAO = "seg-qua-sex-08h"
_NOME_DE_VARIAVEL = re.compile(r"^[A-Z][A-Z0-9_]*$")
_ESCALARES = (str, int, float, bool)


@dataclass(frozen=True)
class Busca:
    id: str
    leiloeiro_id: str
    descricao: str
    filtros: dict


@dataclass(frozen=True)
class Leiloeiro:
    id: str
    nome: str
    base_url: str
    ativo: bool
    estrategia_acesso: str
    credencial_env: str | None
    nivel_coleta: str
    frequencia: str
    buscas: tuple[Busca, ...]
    intervalo_horas: int | None = None   # feature 005 (D-101): ausente = lido em toda varredura
    apify_ator: str | None = None        # feature 005 (D-88): ausente = ator padrão do cliente Apify

    @property
    def pago(self) -> bool:
        """Coleta por ferramenta paga (nível diferente de `script`): fica fora de `--sem-pagos` (D-100)."""
        return self.nivel_coleta != "script"


@dataclass
class ResultadoLeiloeiros:
    ativos: list[Leiloeiro]
    inativos: int = 0
    avisos: list[str] = field(default_factory=list)


def id_busca(leiloeiro_id: str, filtros: dict) -> str:
    """Estável entre execuções e insensível à ordem das chaves (RF-09 v1.1)."""
    canonico = json.dumps(filtros, sort_keys=True, ensure_ascii=False)
    return f"{leiloeiro_id}:{hashlib.sha1(canonico.encode('utf-8')).hexdigest()[:10]}"


def _erro(nome: str, mensagem: str) -> ErroConfiguracao:
    return ErroConfiguracao(f"Leiloeiro '{nome}': {mensagem}. Execução abortada.")


def _filtros(valor: Any, nome: str, descricao: str) -> dict:
    if not isinstance(valor, dict) or not valor:
        raise _erro(nome, f"a busca '{descricao}' precisa de pelo menos um filtro em 'filtros'")
    for chave, item in valor.items():
        if not isinstance(chave, str) or not chave.strip():
            raise _erro(nome, f"a busca '{descricao}' tem um filtro sem nome")
        if isinstance(item, list):
            if not item or not all(isinstance(v, _ESCALARES) for v in item):
                raise _erro(nome, f"o filtro '{chave}' da busca '{descricao}' deve ser uma lista não vazia de valores simples")
        elif not isinstance(item, _ESCALARES):
            raise _erro(nome, f"o filtro '{chave}' da busca '{descricao}' deve ser texto, número ou lista; "
                              f"recebido {type(item).__name__}")
    return dict(valor)


def _buscas(bloco: dict, leiloeiro_id: str, nome: str, avisos: list[str]) -> tuple[Busca, ...]:
    brutas = bloco.get("buscas")
    if not isinstance(brutas, list) or not brutas:
        raise _erro(nome, "é obrigatório cadastrar ao menos uma busca em 'buscas'")
    buscas: list[Busca] = []
    vistas: set[str] = set()
    for posicao, bruta in enumerate(brutas, start=1):
        if not isinstance(bruta, dict):
            raise _erro(nome, f"a busca {posicao} não é um bloco de campos")
        descricao = bruta.get("descricao")
        if not isinstance(descricao, str) or not descricao.strip():
            raise _erro(nome, f"a busca {posicao} precisa de 'descricao'")
        descricao = descricao.strip()
        filtros = _filtros(bruta.get("filtros"), nome, descricao)
        identificador = id_busca(leiloeiro_id, filtros)
        if identificador in vistas:
            avisos.append(f"Leiloeiro '{nome}': busca '{descricao}' duplicada (mesmos filtros); mantida a primeira.")
            continue
        vistas.add(identificador)
        buscas.append(Busca(id=identificador, leiloeiro_id=leiloeiro_id, descricao=descricao, filtros=filtros))
    return tuple(buscas)


def _leiloeiro(bloco: Any, posicao: int, avisos: list[str]) -> Leiloeiro:
    if not isinstance(bloco, dict):
        raise ErroConfiguracao(f"O item {posicao} de 'leiloeiros' não é um bloco de campos. Execução abortada.")
    nome = bloco.get("nome")
    if not isinstance(nome, str) or not nome.strip():
        raise ErroConfiguracao(f"O leiloeiro {posicao} precisa de 'nome'. Execução abortada.")
    nome = nome.strip()
    leiloeiro_id = gerar_id(nome)

    base_url = bloco.get("base_url")
    if not isinstance(base_url, str) or not base_url.startswith("https://") or len(base_url) <= len("https://"):
        raise _erro(nome, f"base_url ({base_url}) deve ser uma URL absoluta em https")

    ativo = bloco.get("ativo", True)
    if not isinstance(ativo, bool):
        raise _erro(nome, f"ativo ({ativo!r}) deve ser true ou false")

    estrategia = bloco.get("estrategia_acesso")
    if estrategia not in ESTRATEGIAS_ACESSO:
        raise _erro(nome, f"estrategia_acesso ({estrategia!r}) deve ser {' ou '.join(ESTRATEGIAS_ACESSO)}")

    credencial = bloco.get("credencial_env")
    if estrategia == "logado" and not credencial:
        raise _erro(nome, "estrategia_acesso: logado exige credencial_env com o nome da variável do .env")
    if credencial is not None and (not isinstance(credencial, str) or not _NOME_DE_VARIAVEL.match(credencial)):
        raise _erro(nome, "credencial_env deve conter só o NOME de uma variável (ex.: VIP_LOGIN), e não a senha. "
                          "Mova o valor para o .env, que fica fora do git")

    nivel = bloco.get("nivel_coleta") or "script"
    if nivel not in NIVEIS_COLETA:
        raise _erro(nome, f"nivel_coleta ({nivel!r}) inválido; aceitos: {', '.join(NIVEIS_COLETA)}")

    frequencia = bloco.get("frequencia") or FREQUENCIA_PADRAO
    if not isinstance(frequencia, str):
        frequencia = str(frequencia)

    intervalo = bloco.get("intervalo_horas")
    if intervalo is not None and (isinstance(intervalo, bool) or not isinstance(intervalo, int)
                                  or not 1 <= intervalo <= INTERVALO_MAXIMO_HORAS):
        raise _erro(nome, f"intervalo_horas ({intervalo!r}) deve ser um número inteiro de horas entre 1 e "
                          f"{INTERVALO_MAXIMO_HORAS}; para ler em toda varredura, apague a linha")

    ator = bloco.get("apify_ator")
    if ator is not None:
        if nivel != "apify":
            raise _erro(nome, "apify_ator só vale com nivel_coleta: apify")
        try:
            validar_ator(str(ator))
        except ValueError as erro:
            raise _erro(nome, str(erro)) from None

    return Leiloeiro(
        id=leiloeiro_id,
        nome=nome,
        base_url=base_url.rstrip("/"),
        ativo=ativo,
        estrategia_acesso=estrategia,
        credencial_env=credencial,
        nivel_coleta=nivel,
        frequencia=frequencia,
        buscas=_buscas(bloco, leiloeiro_id, nome, avisos),
        intervalo_horas=intervalo,
        apify_ator=str(ator) if ator is not None else None,
    )


def _verificar_executavel(leiloeiro: Leiloeiro, adaptadores: Mapping[str, Any], parsers: Collection[str]) -> None:
    nome = leiloeiro.nome
    if leiloeiro.estrategia_acesso not in ESTRATEGIAS_IMPLEMENTADAS:
        raise _erro(nome, "acesso logado ainda não implementado nesta versão; use ativo: false por enquanto")
    if leiloeiro.nivel_coleta not in NIVEIS_IMPLEMENTADOS:
        raise _erro(nome, f"nivel_coleta {leiloeiro.nivel_coleta} ainda não implementado nesta versão; "
                          f"use {' ou '.join(NIVEIS_IMPLEMENTADOS)}")
    if leiloeiro.id not in adaptadores:
        disponiveis = ", ".join(sorted(adaptadores)) or "nenhum"
        raise _erro(nome, f"não há adaptador de coleta para '{leiloeiro.id}'; adaptadores disponíveis: {disponiveis}")
    if leiloeiro.id not in parsers:
        disponiveis = ", ".join(sorted(parsers)) or "nenhum"
        raise _erro(nome, f"não há parser para '{leiloeiro.id}'; parsers disponíveis: {disponiveis}")
    adaptador = adaptadores[leiloeiro.id]
    for busca in leiloeiro.buscas:
        try:
            adaptador.validar_filtros(busca.filtros)
        except ValueError as erro:
            raise _erro(nome, f"a busca '{busca.descricao}' tem filtro inválido: {erro}") from None


def carregar_leiloeiros(caminho: Path, adaptadores: Mapping[str, Any], parsers: Collection[str]) -> ResultadoLeiloeiros:
    garantir_arquivo(caminho, EXEMPLO_LEILOEIROS)
    dados = ler_yaml(caminho)
    if not isinstance(dados, dict) or not isinstance(dados.get("leiloeiros"), list):
        raise ErroConfiguracao(f"{caminho.name} precisa ter uma lista 'leiloeiros' na raiz. Execução abortada.")

    resultado = ResultadoLeiloeiros(ativos=[])
    ids: set[str] = set()
    for posicao, bloco in enumerate(dados["leiloeiros"], start=1):
        leiloeiro = _leiloeiro(bloco, posicao, resultado.avisos)
        if leiloeiro.id in ids:
            raise _erro(leiloeiro.nome, "cadastrado mais de uma vez (nomes que geram o mesmo identificador)")
        ids.add(leiloeiro.id)
        if not leiloeiro.ativo:
            resultado.inativos += 1
            continue
        _verificar_executavel(leiloeiro, adaptadores, parsers)
        resultado.ativos.append(leiloeiro)

    if not resultado.ativos:
        resultado.avisos.append("Nenhum leiloeiro ativo cadastrado. Nada a varrer nesta execução.")
    return resultado
