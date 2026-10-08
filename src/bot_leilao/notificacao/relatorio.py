"""Relatório Markdown por varredura (emenda E001 da feature 001).

Uma segunda fonte do resultado, além do Telegram: cada varredura real grava um arquivo em
`1OUTPUT/` com os lotes novos. O Rafael pede depois ao Claude para anotar nele a análise da
FIPE, então um relatório existente nunca é sobrescrito.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from bot_leilao.filtro.motor import Candidato
from bot_leilao.notificacao.digest import ItemDigest, formatar_preco, item_de

_MARKDOWN = re.compile(r"([\\`*_\[\]#|<>])")


def _escapar(texto: str) -> str:
    return _MARKDOWN.sub(r"\\\1", texto)


def _celula(texto: str) -> str:
    """Numa célula de tabela basta neutralizar `|` e quebras de linha; o resto fica legível."""
    return texto.replace("|", "\\|").replace("\n", " ")


@dataclass
class LoteRelatorio:
    item: ItemDigest
    rotulo_preco: str
    alvo: str
    teto: str


def lote_de(candidato: Candidato, nome_leiloeiro: str) -> LoteRelatorio:
    tem_lance = candidato.lote.lance_corrente is not None
    return LoteRelatorio(
        item=item_de(candidato, nome_leiloeiro),
        rotulo_preco="Lance atual" if tem_lance else "Lance inicial (ainda sem lances)",
        alvo=candidato.alvo.id,
        teto=formatar_preco(candidato.alvo.preco_maximo),
    )


@dataclass
class DadosRelatorio:
    inicio: datetime                         # hora local do início da varredura
    duracao_s: float
    veredito: str
    motivo: str | None
    novos: list[LoteRelatorio] = field(default_factory=list)
    telegram: str | None = None              # "enviado", "não enviado: <erro>" ou None (nada a enviar)
    semeados: int = 0
    em_semeadura: bool = False


def _duracao(segundos: float) -> str:
    segundos = int(round(segundos))
    return f"{segundos // 60}m{segundos % 60:02d}s"


def montar_relatorio(dados: DadosRelatorio) -> str:
    linhas = [
        f"# Varredura de {dados.inicio:%d/%m/%Y %H:%M}",
        "",
        "| Campo | Valor |",
        "|---|---|",
        f"| Data | {dados.inicio:%d/%m/%Y} |",
        f"| Hora | {dados.inicio:%H:%M} |",
        f"| Veredito | {dados.veredito} |",
    ]
    if dados.motivo:
        linhas.append(f"| Motivo | {_celula(dados.motivo)} |")
    linhas += [
        f"| Duração | {_duracao(dados.duracao_s)} |",
        f"| Lotes novos | {len(dados.novos)} |",
        f"| Telegram | {_celula(dados.telegram) if dados.telegram else 'nada a enviar'} |",
        "",
        "## Lotes novos",
        "",
    ]
    if not dados.novos:
        linhas.append("Nenhum lote novo nesta varredura.")
        if dados.em_semeadura:
            linhas += ["", f"Busca em estreia (semeadura): {dados.semeados} lote(s) que já estavam no site foram "
                           "registrados como conhecidos, sem aviso."]
    else:
        if dados.telegram and dados.telegram != "enviado":
            linhas += ["> O Telegram não confirmou o envio: estes lotes voltam na próxima varredura.", ""]
        for numero, novo in enumerate(dados.novos, start=1):
            item = novo.item
            titulo = _escapar(item.titulo) + (f" — {item.ano}" if item.ano else "")
            linhas += [f"### {numero}. {titulo}", ""]
            linhas.append(f"- **{novo.rotulo_preco}:** {item.preco}")
            linhas.append(f"- **Leiloeiro:** {_escapar(item.leiloeiro)}")
            if item.km:
                linhas.append(f"- **Km:** {item.km}")
            linhas.append(f"- **Link:** {item.link}")
            linhas.append(f"- **Alvo:** {novo.alvo} (teto {novo.teto})")
            linhas += ["- **Análise FIPE:** _pendente_", ""]
    return "\n".join(linhas).rstrip("\n") + "\n"


def gravar_relatorio(pasta: Path, dados: DadosRelatorio) -> Path:
    """Grava `AAAA-MM-DD_HHhMM_varredura.md`; se já existir, usa `_2`, `_3`... Nunca sobrescreve."""
    pasta.mkdir(parents=True, exist_ok=True)
    base = f"{dados.inicio:%Y-%m-%d_%Hh%M}_varredura"
    texto = montar_relatorio(dados)
    for indice in range(1, 1000):
        caminho = pasta / (f"{base}.md" if indice == 1 else f"{base}_{indice}.md")
        try:
            with caminho.open("x", encoding="utf-8", newline="\n") as arquivo:
                arquivo.write(texto)
            return caminho
        except FileExistsError:
            continue
    raise FileExistsError(f"Relatórios demais com o nome {base} em {pasta}")
