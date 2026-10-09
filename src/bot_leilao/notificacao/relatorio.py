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
    id_canonico: str = ""


def lote_de(candidato: Candidato, nome_leiloeiro: str) -> LoteRelatorio:
    tem_lance = candidato.lote.lance_corrente is not None
    return LoteRelatorio(
        item=item_de(candidato, nome_leiloeiro),
        rotulo_preco="Lance atual" if tem_lance else "Lance inicial (ainda sem lances)",
        alvo=candidato.alvo.id,
        teto=formatar_preco(candidato.alvo.preco_maximo),
        id_canonico=candidato.lote.id_canonico or "",
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


# --- Emenda E002: lista acumulada de lotes a monitorar ----------------------------------------

CABECALHO_MONITORAMENTO = """# Lotes a monitorar

Lista acumulada dos lotes avisados pelo bot no Telegram. O bot só ACRESCENTA lotes no fim deste
arquivo: nunca reescreve, reordena nem apaga nada. Quem tira lotes daqui é o Rafael, ou um agente
(Claude, Antigravity, Codex) a pedido dele.

## Como manter

- **Para tirar um lote:** apague o bloco inteiro dele, da linha `---` até a linha antes do próximo `---`
  (ou até o fim do arquivo, se for o último).
- **Quando tirar:** o martelo bateu (leilão encerrado), o lote foi retirado, ou o lance passou do teto.
- **Ao atualizar um lote** (lance atual, análise FIPE): edite só as linhas daquele bloco e não mexa no
  comentário `<!-- lote: ... -->`, que identifica o lote para o bot não repeti-lo.
- **Lote tirado não volta:** o bot avisa cada lote uma única vez.
- **Reaparições:** um carro que não vendeu pode voltar em outro evento com **outro número de anúncio**, e o
  bot o avisa como lote novo. Ao revisar a lista, compare marca, modelo e versão, ano, **quilometragem** e
  **final de placa** (aparece no card do site); se coincidirem, é o mesmo carro. Anote nos dois blocos
  `- **Reaparição de:** <link do outro>` e não apague nenhum: pode ser oportunidade (sem lances antes) ou
  problema oculto, e o Rafael decide caso a caso.
"""


def _bloco_monitoramento(novo: LoteRelatorio, entrada: datetime, relatorio: str) -> str:
    item = novo.item
    titulo = _escapar(item.titulo) + (f" — {item.ano}" if item.ano else "")
    linhas = [
        "", "---", "",
        f"### {titulo}",
        f"<!-- lote: {novo.id_canonico} -->",
        "",
        f"- **Entrou na lista:** {entrada:%d/%m/%Y %H:%M} (varredura `{relatorio}`)",
        f"- **{'Lance ao entrar' if novo.rotulo_preco == 'Lance atual' else novo.rotulo_preco}:** {item.preco}",
        f"- **Leiloeiro:** {_escapar(item.leiloeiro)}",
    ]
    if item.km:
        linhas.append(f"- **Km:** {item.km}")
    linhas += [
        f"- **Link:** {item.link}",
        f"- **Alvo:** {novo.alvo} (teto {novo.teto})",
        "- **Análise FIPE:** _pendente_",
    ]
    return "\n".join(linhas) + "\n"


def acrescentar_monitoramento(caminho: Path, novos: list[LoteRelatorio], entrada: datetime, relatorio: str) -> int:
    """Acrescenta no fim da lista os lotes que ainda não estão nela. Devolve quantos entraram.

    Só abre o arquivo para leitura (deduplicação pelo comentário de id) e para acréscimo: o conteúdo
    existente, inclusive anotações, nunca é reescrito.
    """
    existente = caminho.read_text(encoding="utf-8") if caminho.exists() else None
    pendentes = [n for n in novos if n.id_canonico and f"<!-- lote: {n.id_canonico} -->" not in (existente or "")]
    if not pendentes:
        return 0
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if existente is None:
        with caminho.open("x", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(CABECALHO_MONITORAMENTO)
    with caminho.open("a", encoding="utf-8", newline="\n") as arquivo:
        for novo in pendentes:
            arquivo.write(_bloco_monitoramento(novo, entrada, relatorio))
    return len(pendentes)
