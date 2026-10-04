"""Leitura segura dos YAML de configuração e arquivos de exemplo (EC-01, EC-02, EC-08 das specs de config)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as TempoEsgotado
from pathlib import Path
from typing import Any

import yaml


class ErroConfiguracao(Exception):
    """Configuração inválida: a execução aborta antes de qualquer requisição de rede."""


class ConfiguracaoAusente(ErroConfiguracao):
    """O arquivo não existia; um exemplo comentado foi criado no lugar."""

    def __init__(self, caminho: Path) -> None:
        self.caminho = caminho
        super().__init__(
            f"Arquivo {caminho} não existia. Criei um exemplo comentado nesse caminho: "
            "edite-o, ative o que quiser monitorar e rode de novo."
        )


BOM_UTF8 = b"\xef\xbb\xbf"


def ler_yaml(caminho: Path, timeout: float = 5.0) -> Any:
    """Lê e interpreta um YAML em UTF-8 sem BOM, com timeout de leitura (EC-10 / EC-09)."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        futuro = executor.submit(caminho.read_bytes)
        try:
            bruto = futuro.result(timeout=timeout)
        except TempoEsgotado:
            raise ErroConfiguracao(
                f"A leitura de {caminho.resolve()} passou de {timeout:g} s (arquivo travado ou sincronizando?)."
            ) from None
        except OSError as erro:
            raise ErroConfiguracao(f"Não consegui ler {caminho.resolve()}: {erro.strerror or erro}.") from None

    if bruto.startswith(BOM_UTF8):
        raise ErroConfiguracao(
            f"{caminho.name} está salvo com BOM. Salve como UTF-8 sem BOM "
            "(no Bloco de Notas: Salvar como → Codificação: UTF-8)."
        )
    try:
        texto = bruto.decode("utf-8")
    except UnicodeDecodeError:
        raise ErroConfiguracao(
            f"{caminho.name} não está em UTF-8 (provavelmente ANSI/Latin-1). Salve como UTF-8 sem BOM."
        ) from None

    try:
        return yaml.safe_load(texto)
    except yaml.YAMLError as erro:
        marca = getattr(erro, "problem_mark", None) or getattr(erro, "context_mark", None)
        onde = f"linha {marca.line + 1}, coluna {marca.column + 1}" if marca else "linha desconhecida"
        problema = getattr(erro, "problem", None) or str(erro)
        raise ErroConfiguracao(f"{caminho.name} tem erro de sintaxe YAML na {onde}: {problema}.") from None


def garantir_arquivo(caminho: Path, exemplo: str) -> None:
    """Se o arquivo não existe, grava o exemplo e aborta com `ConfiguracaoAusente`. Nunca reescreve."""
    if caminho.exists():
        return
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(exemplo, encoding="utf-8")
    raise ConfiguracaoAusente(caminho)


EXEMPLO_VEICULOS = """\
# Veículos que quero encontrar.
# Desative um alvo com `ativo: false` em vez de apagar o bloco.
# ano_min e ano_max referem-se ao ANO DE MODELO (o segundo número em 2018/2019).
# preco_maximo é comparado contra o LANCE CORRENTE do lote.
# quilometragem_maxima é opcional: sem ela, qualquer quilometragem serve.
# Escreva a marca por extenso (Mitsubishi, Chevrolet): o sistema traduz as abreviações do site.
# tipos_leilao aceita: judicial, extrajudicial, financiamento, seguradora, recuperado.
# A busca do Vip traz só recuperados de financiamento: mantenha "financiamento" na lista.
veiculos:
  - marca: Nissan
    modelo: Versa
    ano_min: 2018
    ano_max: 2021
    preco_maximo: 45000
    quilometragem_maxima: 120000
    tipos_leilao:
      - financiamento
    ativo: false
"""

EXEMPLO_LEILOEIROS = """\
# Leiloeiros monitorados.
# A senha nunca entra aqui: credencial_env aponta para uma variável no .env.
# Os filtros são os do formulário de busca do site; veja os valores aceitos
# em _reversa_forward/001-mvp-varredura-ponta-a-ponta/interfaces/vip-pesquisa.md
# Não filtre por marca nem modelo: esse recorte é feito pelos veículos-alvo
# (cadastro-leiloeiros, seção 6.1.1, "busca ampla").
leiloeiros:
  - nome: Vip Leilões
    base_url: https://www.vipleiloes.com.br
    ativo: false
    estrategia_acesso: publico
    nivel_coleta: script
    frequencia: seg-qua-sex-08h      # ainda não usada; o agendamento automático vem em feature futura
    buscas:
      - descricao: Recuperados de financiamento, conservados, qualquer marca
        filtros:
          procedencia: 4   # Recuperado Financiamento
          monta: 1         # Conservado
"""
