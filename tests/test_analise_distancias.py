"""Distância do pátio até Londrina (feature 006; roadmap D-115; interfaces/distancias.md)."""

import json

import httpx

from apoio import SiteMapas
from bot_leilao.analise.distancias import Distancias


def _distancias(raiz, relogio, mapas=None, tabela=None) -> Distancias:
    mapas = mapas or SiteMapas()
    return Distancias(tabela or {}, raiz / "dados" / "distancias.json", origem="Londrina - PR",
                      transporte=httpx.MockTransport(mapas.responder), relogio=relogio.agora, dormir=relogio.dormir)


def test_tabela_do_custos_yaml_vence_sem_consulta(raiz, relogio):
    mapas = SiteMapas()
    distancias = _distancias(raiz, relogio, mapas, tabela={"Curitiba - PR": 380})
    assert distancias.km("CURITIBA - PR") == 380, "comparação sem caixa nem acento"
    assert mapas.chamadas == []


def test_calcula_pela_rota_e_guarda_no_cache(raiz, relogio):
    assert _distancias(raiz, relogio).km("Curitiba - PR") == 385
    cache = json.loads((raiz / "dados" / "distancias.json").read_text(encoding="utf-8"))
    assert cache["curitiba - pr"]["km"] == 385
    mapas = SiteMapas()
    assert _distancias(raiz, relogio, mapas).km("Curitiba - PR") == 385
    assert mapas.chamadas == [], "segunda vez vem do cache"


def test_espera_um_segundo_entre_consultas_ao_nominatim(raiz, relogio):
    mapas = SiteMapas()
    _distancias(raiz, relogio, mapas).km("Curitiba - PR")
    assert mapas.consultas_nominatim() == ["Londrina,PR,Brasil", "Curitiba,PR,Brasil"]
    assert any(espera >= 1.0 for espera in relogio.dormidas)


def test_identifica_o_bot_no_nominatim(raiz, relogio):
    mapas = SiteMapas()
    _distancias(raiz, relogio, mapas).km("Curitiba - PR")
    assert "bot-leilao" in mapas.chamadas[0].headers["User-Agent"]


def test_sem_resposta_fica_sem_distancia(raiz, relogio):
    assert _distancias(raiz, relogio, SiteMapas(nominatim="fora")).km("Curitiba - PR") is None
    assert _distancias(raiz, relogio, SiteMapas(osrm="fora")).km("Curitiba - PR") is None
    assert _distancias(raiz, relogio).km("Cidade Inexistente - ZZ") is None


def test_patio_so_com_uf_fica_sem_distancia(raiz, relogio):
    mapas = SiteMapas()
    assert _distancias(raiz, relogio, mapas).km("SC") is None
    assert mapas.chamadas == []
