"""Distância do pátio até a cidade base (feature 006; roadmap D-115; interfaces/distancias.md).

Ordem: tabela `distancias` do `custos.yaml` (correção do Rafael) → cache `dados/distancias.json` → geocodificação
pelo Nominatim (OpenStreetMap) e rota pelo OSRM, guardada no cache. Falha ou pátio só com UF: None ("a confirmar").
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections.abc import Callable, Mapping
from pathlib import Path

import httpx

from bot_leilao import __version__
from bot_leilao.texto import normalizar_texto

log = logging.getLogger(__name__)

NOMINATIM = "https://nominatim.openstreetmap.org/search"
OSRM = "https://router.project-osrm.org/route/v1/driving"
AGENTE = f"bot-leilao-carros/{__version__} (analise de lotes; uso pessoal, consultas esporadicas)"
INTERVALO_NOMINATIM_S = 1.0   # política de uso do Nominatim: no máximo 1 consulta por segundo
_CIDADE_UF = re.compile(r"^\s*(.+?)\s*-\s*([A-Za-z]{2})\s*$")


class Distancias:
    def __init__(self, tabela: Mapping[str, int], cache: Path, origem: str = "Londrina - PR",
                 transporte: httpx.BaseTransport | None = None, relogio: Callable[[], float] = time.monotonic,
                 dormir: Callable[[float], None] = time.sleep, timeout: float = 20.0) -> None:
        self.tabela = {normalizar_texto(k): v for k, v in tabela.items()}
        self.caminho_cache = cache
        self.origem = origem
        self.relogio = relogio
        self.dormir = dormir
        self._ultima_consulta: float | None = None
        self._cliente = httpx.Client(transport=transporte, timeout=timeout, headers={"User-Agent": AGENTE})

    def _ler_cache(self) -> dict:
        try:
            return json.loads(self.caminho_cache.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _gravar_cache(self, cache: dict) -> None:
        self.caminho_cache.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho_cache.with_name(f".{self.caminho_cache.name}.tmp")
        temporario.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(temporario, self.caminho_cache)

    def km(self, patio: str) -> int | None:
        chave = normalizar_texto(patio)
        if chave in self.tabela:
            return self.tabela[chave]
        cache = self._ler_cache()
        if isinstance(cache.get(chave), dict) and "km" in cache[chave]:
            return cache[chave]["km"]
        if not _CIDADE_UF.match(patio or ""):
            return None  # só a UF, ou formato desconhecido: frete "a confirmar"
        coordenadas = cache.setdefault("_coordenadas", {})
        origem = self._coordenadas(self.origem, coordenadas)
        destino = self._coordenadas(patio, coordenadas) if origem else None
        km = self._rota(origem, destino) if destino else None
        if km is not None:
            cache[chave] = {"km": km, "fonte": "osrm"}
            log.info("analise | distância %s → %s: %d km (OSRM)", self.origem, patio, km)
        self._gravar_cache(cache)
        return km

    def _coordenadas(self, lugar: str, coordenadas: dict) -> dict | None:
        chave = normalizar_texto(lugar)
        if chave in coordenadas:
            return coordenadas[chave]
        cidade, uf = _CIDADE_UF.match(lugar).groups()
        if self._ultima_consulta is not None:
            falta = self._ultima_consulta + INTERVALO_NOMINATIM_S - self.relogio()
            if falta > 0:
                self.dormir(falta)
        self._ultima_consulta = self.relogio()
        try:
            resposta = self._cliente.get(NOMINATIM, params={"q": f"{cidade},{uf.upper()},Brasil", "format": "json",
                                                            "limit": "1"})
            achados = resposta.json() if resposta.status_code == 200 else []
        except (httpx.HTTPError, ValueError) as erro:
            log.info("analise | Nominatim falhou para %s: %s", lugar, type(erro).__name__)
            return None
        if not achados:
            return None
        coordenadas[chave] = {"lat": achados[0]["lat"], "lon": achados[0]["lon"]}
        return coordenadas[chave]

    def _rota(self, origem: dict, destino: dict) -> int | None:
        try:
            resposta = self._cliente.get(f"{OSRM}/{origem['lon']},{origem['lat']};{destino['lon']},{destino['lat']}",
                                         params={"overview": "false"})
            if resposta.status_code != 200:
                return None
            return round(resposta.json()["routes"][0]["distance"] / 1000)
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as erro:
            log.info("analise | OSRM falhou: %s", type(erro).__name__)
            return None
