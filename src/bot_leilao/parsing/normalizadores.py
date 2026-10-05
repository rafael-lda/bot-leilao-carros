"""Normalizadores de preço, ano, quilometragem e link (parser-lotes RF-03 a RF-05)."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

_VALOR = re.compile(r"\d[\d.]*(?:,\d+)?")
_ANOS = re.compile(r"(?<!\d)(\d{4})(?:\s*/\s*(\d{4}))?(?!\d)")
_KM = re.compile(r"(\d[\d.]*)\s*km\b", re.IGNORECASE)
_INTEIRO = re.compile(r"\d+")
ANO_MINIMO = 1900
# Roadmap D-32: leiloeiros preenchem 0 ou 999.999 quando não sabem a km (carro sem chave, bateria arriada).
# Nenhum carro de verdade roda 900 mil km, e 0 km é o "não informado" mais comum; os dois valem "desconhecida".
KM_SENTINELA_MINIMO = 900_000


def normalizar_preco(texto: str | None) -> Decimal | None:
    """`R$ 45.000,00` → `Decimal('45000.00')`; texto sem número → None."""
    if not texto:
        return None
    achado = _VALOR.search(texto)
    if not achado:
        return None
    try:
        return Decimal(achado.group().replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _ano_plausivel(valor: str | None) -> int | None:
    if valor is None:
        return None
    ano = int(valor)
    return ano if ANO_MINIMO <= ano <= date.today().year + 2 else None


def normalizar_anos(texto: str | None) -> tuple[int | None, int | None]:
    """`2018/2019` → (2018, 2019); `2018` → (2018, 2018); fora de faixa plausível → None."""
    if not texto:
        return None, None
    achados = list(_ANOS.finditer(texto))
    if not achados:
        return None, None
    fabricacao_txt, modelo_txt = achados[-1].groups()
    fabricacao = _ano_plausivel(fabricacao_txt)
    modelo = _ano_plausivel(modelo_txt) if modelo_txt else fabricacao
    return fabricacao, modelo


def normalizar_km(texto: str | None) -> int | None:
    """`228.227 Km` → 228227. Valor 0 ou a partir de 900.000 é "não informado" (D-32): devolve None."""
    if not texto:
        return None
    achado = _KM.search(texto)
    if not achado:
        return None
    km = int(achado.group(1).replace(".", ""))
    return None if km == 0 or km >= KM_SENTINELA_MINIMO else km


def link_absoluto(href: str | None, base_url: str) -> str | None:
    if not href or href.startswith("#") or href.lower().startswith("javascript:"):
        return None
    return urljoin(base_url.rstrip("/") + "/", href)


def inteiro(texto: str | None) -> int | None:
    if not texto:
        return None
    achado = _INTEIRO.search(texto)
    return int(achado.group()) if achado else None
