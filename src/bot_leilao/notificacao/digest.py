"""Formatação do digest e do alerta (notificador-telegram RF-01 a RF-03, RF-06, RF-08, RF-10, RF-11).

Formato em interfaces/telegram-bot-api.md §3. Modo HTML do Telegram: só `<`, `>` e `&` precisam de escape.
"""

from __future__ import annotations

import html
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from bot_leilao.filtro.motor import Candidato

LIMITE_BLOCO = 3800  # abaixo dos 4096 da plataforma, com folga para entidades
PRECO_A_CONFIRMAR = "Preço a confirmar"
OBSERVACOES_NAO_LIDAS = "observações não lidas; veja o link"
LIMITE_OBSERVACOES = 160  # feature 002, D-51: o resumo continua legível com vários lotes
_RESERVA_CONTINUACAO = len("(continuação 999/999)\n\n")


def escapar_html(texto: str) -> str:
    return html.escape(texto, quote=False)


def _milhar(inteiro: int) -> str:
    return f"{inteiro:,}".replace(",", ".")


def formatar_preco(valor: Decimal | None) -> str:
    if valor is None:
        return PRECO_A_CONFIRMAR
    if valor == valor.to_integral_value():
        return f"R$ {_milhar(int(valor))}"
    inteiro, centavos = f"{valor:.2f}".split(".")
    return f"R$ {_milhar(int(inteiro))},{centavos}"


def formatar_km(km: int | None) -> str | None:
    return None if km is None else f"{_milhar(km)} km"


@dataclass
class ItemDigest:
    titulo: str
    ano: int | None
    preco: str
    leiloeiro: str
    link: str
    km: str | None = None
    pregao: str | None = None           # feature 002: leilão por evento (Claudio Kuss)
    observacoes: str | None = None      # feature 002: resumidas em LIMITE_OBSERVACOES
    patio: str | None = None            # feature 003: onde o veículo está
    fipe: str | None = None             # feature 003: "FIPE R$ 80.266", quando o leiloeiro informa
    cambio: str | None = None           # feature 005: "automático", "manual" ou "CVT", quando o leiloeiro informa


def resumir(texto: str, limite: int = LIMITE_OBSERVACOES) -> str:
    return texto if len(texto) <= limite else texto[:limite - 1].rstrip() + "…"


def observacoes_do_lote(lote) -> str | None:
    """Texto completo das observações; aviso explícito quando o detalhe foi tentado e falhou (D-49)."""
    if lote.detalhe_lido is False:
        return OBSERVACOES_NAO_LIDAS
    return lote.observacoes


def item_de(candidato: Candidato, nome_leiloeiro: str) -> ItemDigest:
    lote = candidato.lote
    return ItemDigest(
        titulo=lote.titulo or " ".join(filter(None, [lote.marca, lote.modelo])) or "Lote sem título",
        ano=lote.ano_modelo,
        preco=formatar_preco(candidato.preco),
        leiloeiro=nome_leiloeiro,
        link=lote.link,
        km=formatar_km(lote.quilometragem),
        pregao=f"Pregão {lote.pregao_em:%d/%m %H:%M}" if lote.pregao_em else None,
        observacoes=resumir(obs) if (obs := observacoes_do_lote(lote)) else None,
        patio=lote.patio,
        fipe=f"FIPE {formatar_preco(lote.fipe)}" if lote.fipe is not None else None,
        cambio=lote.cambio,
    )


def _texto_item(numero: int, item: ItemDigest) -> str:
    primeira = f"{numero}. {escapar_html(item.titulo)}" + (f" — {item.ano}" if item.ano else "")
    # D-71 da feature 003; câmbio depois do km quando o leiloeiro informa (feature 005, cenário 2)
    partes = (item.preco, item.leiloeiro, item.km, item.cambio, item.patio, item.fipe, item.pregao)
    segunda = "   " + " — ".join(escapar_html(p) for p in partes if p)
    linhas = [primeira, segunda]
    if item.observacoes:  # 4ª linha só para quem tem observações (RF-07 da feature 002)
        linhas.append(f"   Obs.: {escapar_html(item.observacoes)}")
    return "\n".join([*linhas, f"   {escapar_html(item.link)}"])


def montar_digest(itens: Sequence[ItemDigest], executado_em: datetime, limite: int = LIMITE_BLOCO) -> list[str]:
    """Um digest por execução, dividido entre itens quando passa do limite (RF-06). Sem itens, nada."""
    if not itens:
        return []
    total = len(itens)
    cabecalho = (f"<b>Varredura de {executado_em:%d/%m/%Y %H:%M} — {total} "
                 f"{'lote novo' if total == 1 else 'lotes novos'}</b>")

    blocos: list[list[str]] = [[]]
    tamanho = len(cabecalho)
    for numero, item in enumerate(itens, start=1):
        texto = _texto_item(numero, item)
        if blocos[-1] and tamanho + 2 + len(texto) > limite:
            blocos.append([])
            tamanho = _RESERVA_CONTINUACAO
        blocos[-1].append(texto)
        tamanho += 2 + len(texto)

    mensagens = []
    for indice, partes in enumerate(blocos, start=1):
        topo = cabecalho if indice == 1 else f"(continuação {indice}/{len(blocos)})"
        mensagens.append(topo + "\n\n" + "\n\n".join(partes))
    return mensagens


@dataclass
class AlertaOperacional:
    executado_em: datetime
    mensagem: str
    leiloeiro: str | None = None
    severidade: str = "aviso"


def montar_alerta(alerta: AlertaOperacional) -> str:
    corpo = escapar_html(alerta.mensagem)
    if alerta.leiloeiro:
        corpo = f"{escapar_html(alerta.leiloeiro)}: {corpo}"
    return f"<b>Alerta do sistema — {alerta.executado_em:%d/%m/%Y %H:%M}</b>\n\n{corpo}"
