"""Normalização de texto e geração de identificadores estáveis."""

from __future__ import annotations

import re
import unicodedata

_NAO_ALFANUMERICO = re.compile(r"[^a-z0-9]+")


def normalizar_texto(texto: str | None) -> str:
    """Minúsculas, sem acento, espaços colapsados e sem bordas."""
    if texto is None:
        return ""
    decomposto = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return " ".join(sem_acento.lower().split())


def gerar_id(*partes: object) -> str:
    """Identificador estável: `gerar_id("Vip Leilões") == "vip-leiloes"`."""
    pedacos = (_NAO_ALFANUMERICO.sub("-", normalizar_texto(str(p))).strip("-") for p in partes)
    return "-".join(p for p in pedacos if p)
