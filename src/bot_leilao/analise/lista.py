"""Lista de monitoramento: leitura e escrita por bloco (feature 006; roadmap D-112, D-117; interfaces/cli-analise.md).

Formato (emenda E002 da 003): cabeçalho, depois blocos separados por linhas `---`, cada um com `### N. TÍTULO — ANO`,
o comentário `<!-- lote: id -->` e as linhas `- **Campo:** valor`. Só o bloco alterado muda; os outros ficam
byte a byte iguais. Toda escrita é atômica (arquivo temporário + rename).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

SEPARADOR = "\n---\n"
ARQUIVO_DESCARTADOS = "lotes-descartados.md"
CABECALHO_DESCARTADOS = (
    "# Lotes descartados\n\n"
    "Lotes tirados de `lotes-a-monitorar.md` pela triagem (skill `analisar-lotes`), com o motivo e a evidência.\n"
    "Para devolver um lote à lista: `python -m bot_leilao analise devolver <número>`, ou peça ao agente.\n"
)
VEREDITOS = ("aprovado", "a-confirmar", "reprovado")
# Ajuste de 2026-10-15: campos que a skill pode gravar fora da triagem e do custo.
CAMPOS_ANOTAVEIS = ("Câmbio", "Resultado do pregão")
_TITULO = re.compile(r"^### (\d+)\. (.*?)(?: — (\S+))?\s*$", re.M)
_ID = re.compile(r"<!-- lote: (.+?) -->")
_CAMPO = re.compile(r"^- \*\*(.+?):\*\* ?(.*)$", re.M)
_REAIS = re.compile(r"R\$ ([\d.]+)")


class ErroLista(Exception):
    """Lista ausente, número inexistente ou pedido inválido: nada é escrito."""


@dataclass
class Bloco:
    numero: int
    id: str
    titulo: str
    ano: str | None
    texto: str
    campos: dict[str, str] = field(default_factory=dict)


def _bloco(texto: str) -> Bloco | None:
    titulo = _TITULO.search(texto)
    if titulo is None:
        return None
    identificador = _ID.search(texto)
    return Bloco(numero=int(titulo.group(1)), id=identificador.group(1) if identificador else "",
                 titulo=titulo.group(2).strip(), ano=titulo.group(3), texto=texto,
                 campos={m.group(1): m.group(2).strip() for m in _CAMPO.finditer(texto)})


def _partes(caminho: Path) -> tuple[str, list[str]]:
    if not caminho.exists():
        raise ErroLista(f"lista não encontrada: {caminho}")
    partes = caminho.read_text(encoding="utf-8").split(SEPARADOR)
    return partes[0], partes[1:]


def _gravar(caminho: Path, cabecalho: str, blocos: list[str]) -> None:
    temporario = caminho.with_name(f".{caminho.name}.tmp")
    temporario.write_text(SEPARADOR.join([cabecalho, *blocos]), encoding="utf-8", newline="\n")
    os.replace(temporario, caminho)


def ler_lista(caminho: Path) -> list[Bloco]:
    _, blocos = _partes(caminho)
    return [b for b in (_bloco(t) for t in blocos) if b is not None]


def _indice(blocos: list[str], numero: int, caminho: Path) -> int:
    for i, texto in enumerate(blocos):
        bloco = _bloco(texto)
        if bloco is not None and bloco.numero == numero:
            return i
    raise ErroLista(f"o lote {numero} não está em {caminho.name}")


def numero_por_link(caminho: Path, link: str) -> int:
    for bloco in ler_lista(caminho):
        if bloco.campos.get("Link", "").strip() == link.strip():
            return bloco.numero
    raise ErroLista(f"nenhum lote de {caminho.name} tem o link {link}")


def _sem_linhas(texto: str, prefixo: str) -> str:
    return "".join(l for l in texto.splitlines(keepends=True) if not l.startswith(prefixo))


def _inserir_antes_do_link(texto: str, linha: str) -> str:
    linhas = texto.splitlines(keepends=True)
    for i, atual in enumerate(linhas):
        if atual.startswith("- **Link:**"):
            return "".join(linhas[:i] + [linha + "\n"] + linhas[i:])
    return texto.rstrip("\n") + "\n" + linha + "\n"


def triar(caminho: Path, numero: int, veredito: str, *, hoje: date, motivo: str | None = None,
          evidencia: str | None = None, falta: str | None = None) -> str:
    """Escreve o veredito no bloco; o reprovado vai para `lotes-descartados.md`. Devolve o arquivo de destino."""
    if veredito not in VEREDITOS:
        raise ErroLista(f"veredito '{veredito}' inválido; aceitos: {', '.join(VEREDITOS)}")
    if veredito == "reprovado" and not (motivo or "").strip():
        raise ErroLista("reprovado exige --motivo")
    if veredito == "reprovado" and not (evidencia or "").strip():
        raise ErroLista("reprovado exige --evidencia (trecho do título, observação ou página)")
    if veredito == "a-confirmar" and not (falta or "").strip():
        raise ErroLista("a confirmar exige --falta (o que falta para decidir)")
    cabecalho, blocos = _partes(caminho)
    i = _indice(blocos, numero, caminho)
    data = f"{hoje:%d/%m/%Y}"
    texto = _sem_linhas(blocos[i], "- **Triagem (")
    if veredito == "reprovado":
        descartado = _inserir_antes_do_link(texto, f"- **Descartado em {data}:** {motivo.strip()} — {evidencia.strip()}")
        destino = caminho.with_name(ARQUIVO_DESCARTADOS)
        cab_d, blocos_d = _partes(destino) if destino.exists() else (CABECALHO_DESCARTADOS, [])
        _gravar(destino, cab_d, [*blocos_d, descartado])
        _gravar(caminho, cabecalho, blocos[:i] + blocos[i + 1:])
        return ARQUIVO_DESCARTADOS
    linha = (f"- **Triagem ({data}):** aprovado" if veredito == "aprovado"
             else f"- **Triagem ({data}):** a confirmar — {falta.strip()}")
    blocos[i] = _inserir_antes_do_link(texto, linha)
    _gravar(caminho, cabecalho, blocos)
    return caminho.name


def devolver(caminho: Path, numero: int) -> None:
    """Traz o bloco de `lotes-descartados.md` de volta para o fim da lista, sem a linha de descarte."""
    origem = caminho.with_name(ARQUIVO_DESCARTADOS)
    if not origem.exists():
        raise ErroLista(f"não há {ARQUIVO_DESCARTADOS} para devolver o lote {numero}")
    cab_d, blocos_d = _partes(origem)
    i = _indice(blocos_d, numero, origem)
    cabecalho, blocos = _partes(caminho)
    _gravar(caminho, cabecalho, [*blocos, _sem_linhas(blocos_d[i], "- **Descartado em ")])
    _gravar(origem, cab_d, blocos_d[:i] + blocos_d[i + 1:])


def anotar_campo(caminho: Path, numero: int, campo: str, valor: str) -> None:
    """Grava um campo do bloco (ex.: câmbio deduzido do título, resultado do pregão): substitui a linha se ela
    existe, senão a insere antes de `- **Link:**`."""
    if campo not in CAMPOS_ANOTAVEIS:
        raise ErroLista(f"campo '{campo}' não pode ser anotado; aceitos: {', '.join(CAMPOS_ANOTAVEIS)}")
    if not (valor or "").strip():
        raise ErroLista("o valor do campo não pode ser vazio")
    cabecalho, blocos = _partes(caminho)
    i = _indice(blocos, numero, caminho)
    if campo in (_bloco(blocos[i]).campos or {}):
        blocos[i] = _trocar_campo(blocos[i], campo, valor.strip())
    else:
        blocos[i] = _inserir_antes_do_link(blocos[i], f"- **{campo}:** {valor.strip()}")
    _gravar(caminho, cabecalho, blocos)


# --- Anotação de custo (D-117) --------------------------------------------------------------------------


def reais(valor) -> str:
    inteiro = int(Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return "R$ " + f"{inteiro:,}".replace(",", ".")


def _percentual(parte: Decimal, todo: Decimal) -> int:
    return int((parte / todo * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _trocar_campo(texto: str, campo: str, valor: str) -> str:
    padrao = re.compile(rf"^- \*\*{re.escape(campo)}:\*\*.*$", re.M)
    novo = f"- **{campo}:** {valor}"
    return padrao.sub(lambda _m: novo, texto, count=1) if padrao.search(texto) else texto


def anotar_custo(caminho: Path, numero: int, dados: dict) -> None:
    """Preenche FIPE, % da FIPE do lance ao entrar, Despesas admin. (se vazia), Frete, Manutenções, Valor estimado
    na garagem e Lance máximo. `dados`: {"fipe": {...} | None, "candidatas": {...} | None, "custo": {...} | None}."""
    cabecalho, blocos = _partes(caminho)
    i = _indice(blocos, numero, caminho)
    texto = blocos[i]
    fipe, candidatas, custo = dados.get("fipe"), dados.get("candidatas"), dados.get("custo")
    valor_fipe = Decimal(str(fipe["valor"])) if fipe else None
    if fipe:
        texto = _trocar_campo(texto, "FIPE", f"{reais(valor_fipe)} — {fipe['versao']} ({fipe['codigo']}, "
                                             f"{fipe['mes_referencia']})")
        lance = _lance_ao_entrar(texto)
        if lance is not None:
            texto = _trocar_campo(texto, "Lance ao entrar",
                                  f"{reais(lance)} ({_percentual(lance, valor_fipe)}% da FIPE)")
    elif candidatas and candidatas.get("candidatas"):
        opcoes = "; ".join(f"{c['versao']} {reais(c['valor'])} ({c['codigo']})" for c in candidatas["candidatas"])
        texto = _trocar_campo(texto, "FIPE", f"_a escolher_: {opcoes} — {candidatas['mes_referencia']}")
    if custo:
        p = custo["parcelas"]
        campos = _bloco(texto).campos
        if not campos.get("Despesas admin.") and p.get("despesa") is not None:
            sufixo = " (padrão)" if p.get("despesa_padrao") else ""
            texto = _trocar_campo(texto, "Despesas admin.", reais(p["despesa"]) + sufixo)
        if p.get("frete") is not None:
            por_km = f"{Decimal(str(p['frete_por_km'])):.2f}".replace(".", ",")
            texto = _trocar_campo(texto, "Frete", f"{reais(p['frete'])} ({p['frete_km']} km × R$ {por_km}, estimativa)")
        manutencoes = f"{reais(p['reparos'])} (reserva)"
        if p.get("reparos_extra"):
            manutencoes += f" + {reais(p['reparos_extra'])} ({p.get('motivo_reparos')})"
        texto = _trocar_campo(texto, "Manutenções", manutencoes)
        garagem = reais(custo["total"])
        if custo.get("percentual_fipe") is not None:
            garagem += f" ({custo['percentual_fipe']}% da FIPE)"
        texto = _trocar_campo(texto, "Valor estimado na garagem", garagem)
        texto = _sem_linhas(texto, "- **Lance máximo (")
        if custo.get("lance_maximo") is not None:
            linha = f"- **Lance máximo (margem {custo['margem_percentual']}%):** {reais(custo['lance_maximo'])}"
            texto = re.sub(r"^(- \*\*Valor estimado na garagem:\*\*.*)$", lambda m: m.group(1) + "\n" + linha, texto,
                           count=1, flags=re.M)
    blocos[i] = texto
    _gravar(caminho, cabecalho, blocos)


def _lance_ao_entrar(texto: str) -> Decimal | None:
    """Valor em reais da linha "Lance ao entrar", ou None se for "Preço a confirmar"."""
    linha = re.search(r"^- \*\*Lance ao entrar:\*\* (.*)$", texto, re.M)
    achado = _REAIS.search(linha.group(1)) if linha else None
    return Decimal(achado.group(1).replace(".", "")) if achado else None
