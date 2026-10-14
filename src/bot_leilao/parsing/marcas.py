"""Tabela comum de sinônimos de marca (parser-lotes v1.1 RF-12, EC-14; roadmap D-28).

Comum a todos os parsers: o que um leiloeiro ensina vale para os outros.
Cada parser pode ampliar com `extras`. Toda grafia nova encontrada num
onboarding deve entrar aqui (onboarding-leiloeiro-assistido, armadilha `sinonimos_marca`).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

from bot_leilao.texto import normalizar_texto

log = logging.getLogger(__name__)

SINONIMOS: dict[str, str] = {
    "mmc": "mitsubishi",          # Vip, 2026-10-03
    "gm": "chevrolet",            # Vip, 2026-10-03
    "vw": "volkswagen",
    "mercedes": "mercedes-benz",
    "mercedes benz": "mercedes-benz",
    "jac": "jac motors",
    "chev": "chevrolet",          # Claudio Kuss, 2026-10-10
    "caoachery": "caoa chery",    # Claudio Kuss, 2026-10-10
    "m benz": "mercedes-benz",    # Claudio Kuss, 2026-10-10
    "lr": "land rover",           # Claudio Kuss, 2026-10-10 ("IMP LR")
    "m.benz": "mercedes-benz",    # Freitas, 2026-10-13
    "m-benz": "mercedes-benz",    # Milan, 2026-10-13 ("I/M-BENZ A200")
    "cintroen": "citroen",        # Milan, 2026-10-13 (erro de digitação do catálogo: "CINTROEN C3")
}

# Marcas do formulário do Vip (2026-10-03), normalizadas, mais as canônicas da tabela.
MARCAS_CONHECIDAS = frozenset({
    "agrale", "aima", "alfa romeo", "audi", "bajaj", "bmw", "bull", "byd", "caoa chery", "chery", "chevrolet",
    "chrysler", "citroen", "daf", "dafra", "dodge", "fiat", "flash", "ford", "gurgel", "gwm", "haojian", "honda",
    "hunter", "hyundai", "imp", "iveco", "jac motors", "jeep", "jianshe", "jincheng", "jta-suzuki", "jtz",
    "kasinski", "kawasaki", "kia", "land rover", "lifan", "loncin", "marcopolo", "mercedes-benz", "mitsubishi",
    "nissan", "peugeot", "porsche", "ram", "randon", "renault", "royal enfield", "scania", "shineray", "sr",
    "ssangyong", "subaru", "sundown", "suzuki", "tailg", "toyota", "traxx", "triumph", "valtra", "volkswagen",
    "volvo", "wuyang", "xinling", "yamaha",
    "jaguar",  # Milan, 2026-10-13
}) | frozenset(SINONIMOS.values())


def marca_canonica(marca: str | None, extras: Mapping[str, str] | None = None) -> str | None:
    normalizada = normalizar_texto(marca)
    if not normalizada:
        return None
    canonica = (extras or {}).get(normalizada) or SINONIMOS.get(normalizada) or normalizada
    if canonica not in MARCAS_CONHECIDAS:
        log.info("parser  | marca fora da tabela conhecida: %r (avaliar sinônimo em parsing/marcas.py)", canonica)
    return canonica
