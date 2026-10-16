"""FIPE pela parallelum e pelo site oficial, com cache por mês (feature 006; roadmap D-114, D-123; RF-09)."""

from datetime import date
from decimal import Decimal

import httpx
import pytest

from apoio import HOST_FIPE_OFICIAL, HOST_PARALLELUM, SiteFipe
from bot_leilao.analise.fipe import ErroFipe, Fipe

AUT, MEC = "VERSA SL 1.6 16V FlexStart 4p Aut.", "VERSA SL 1.6 16V FlexStart 4p Mec."


class Relogio:
    """Relógio falso: `dormir` só avança o tempo e anota a espera."""

    def __init__(self) -> None:
        self.agora, self.esperas = 0.0, []

    def __call__(self) -> float:
        return self.agora

    def dormir(self, segundos: float) -> None:
        self.esperas.append(segundos)
        self.agora += segundos


def _fipe(raiz, site: SiteFipe, relogio: Relogio | None = None, hoje: date = date(2026, 10, 16)) -> Fipe:
    relogio = relogio or Relogio()
    return Fipe(raiz / "dados" / "fipe-cache.json", httpx.MockTransport(site.responder), relogio=relogio,
                dormir=relogio.dormir, hoje=lambda: hoje)


def test_candidatas_por_marca_termos_e_ano(raiz):
    resultado = _fipe(raiz, SiteFipe()).candidatas("Nissan", "versa sl 1.6", 2019)
    assert resultado["mes_referencia"] == "outubro/2026"
    assert resultado["fonte"] == "fipe.org.br", "a busca de versões vai primeiro ao site oficial (D-123)"
    assert {(c["codigo"], c["versao"], c["valor"]) for c in resultado["candidatas"]} == {
        ("023140-1", AUT, Decimal("62464.00")), ("023138-0", MEC, Decimal("61547.00"))}, \
        "só os modelos com todos os termos e com o ano 2019"
    assert all(c["combustivel"] == "Flex" for c in resultado["candidatas"])


def test_termos_sem_acento_e_caixa(raiz):
    assert len(_fipe(raiz, SiteFipe()).candidatas("NISSAN", "Versa SL 1.6 Aut", 2019)["candidatas"]) == 1


def test_valor_por_codigo(raiz):
    valor = _fipe(raiz, SiteFipe()).valor("023140-1", 2019)
    assert (valor["codigo"], valor["versao"], valor["valor"], valor["mes_referencia"], valor["fonte"]) == (
        "023140-1", AUT, Decimal("62464.00"), "outubro/2026", "parallelum")


@pytest.mark.parametrize("estado", ["fora", "limite"])
def test_parallelum_fora_ou_no_limite_usa_o_site_oficial(raiz, estado):
    site = SiteFipe(parallelum=estado)
    fipe = _fipe(raiz, site)
    assert fipe.valor("023140-1", 2019)["fonte"] == "fipe.org.br"
    candidatas = fipe.candidatas("Nissan", "versa sl 1.6", 2019)
    assert candidatas["fonte"] == "fipe.org.br"
    assert {c["codigo"] for c in candidatas["candidatas"]} == {"023140-1", "023138-0"}
    assert HOST_FIPE_OFICIAL in site.hosts_chamados()


def test_as_duas_fora_e_erro_claro(raiz):
    with pytest.raises(ErroFipe, match="FIPE indisponível"):
        _fipe(raiz, SiteFipe(parallelum="fora", oficial="fora")).valor("023140-1", 2019)


def test_cache_evita_nova_consulta_no_mesmo_mes(raiz):
    _fipe(raiz, SiteFipe()).valor("023140-1", 2019)
    site = SiteFipe()
    assert _fipe(raiz, site).valor("023140-1", 2019)["valor"] == Decimal("62464.00")
    assert site.chamadas == [], "no mesmo dia nem o mês de referência é consultado de novo"
    _fipe(raiz, site, hoje=date(2026, 10, 17)).valor("023140-1", 2019)
    assert site.pedidos(HOST_PARALLELUM) == 1, "no dia seguinte, só o mês de referência"


def test_mes_novo_ignora_o_cache_antigo(raiz):
    _fipe(raiz, SiteFipe()).valor("023140-1", 2019)
    site = SiteFipe(referencia=("339", "novembro/2026"))
    assert _fipe(raiz, site, hoje=date(2026, 11, 3)).valor("023140-1", 2019)["mes_referencia"] == "novembro/2026"
    assert len(site.chamadas) > 1


def test_codigo_sem_o_ano_e_erro(raiz):
    with pytest.raises(ErroFipe, match="2030"):
        _fipe(raiz, SiteFipe()).valor("023140-1", 2030)


# Emenda de 2026-10-16 (D-123): a busca de versões esgotou o limite da parallelum (um pedido por versão parecida).


def test_busca_de_versoes_gasta_poucos_pedidos(raiz):
    site = SiteFipe()
    _fipe(raiz, site).candidatas("Nissan", "versa sl 1.6", 2019)
    # referência (parallelum) + marcas + 4 combustíveis + 3 valores (SL Aut., SL Mec., SL Direct) no site oficial
    assert site.pedidos(HOST_PARALLELUM) == 1
    assert site.pedidos(HOST_FIPE_OFICIAL) == 8


def test_segunda_busca_da_mesma_marca_reaproveita_as_marcas(raiz):
    site = SiteFipe()
    fipe = _fipe(raiz, site)
    fipe.candidatas("Nissan", "versa sl 1.6", 2019)
    antes = site.pedidos(HOST_FIPE_OFICIAL)
    fipe.candidatas("Nissan", "versa sv", 2019)
    assert site.pedidos(HOST_FIPE_OFICIAL) - antes == 4 + 2, "sem pedir as marcas de novo"


def test_site_oficial_fora_busca_versoes_pela_parallelum(raiz):
    resultado = _fipe(raiz, SiteFipe(oficial="fora")).candidatas("Nissan", "versa sl 1.6", 2019)
    assert resultado["fonte"] == "parallelum"
    assert {c["codigo"] for c in resultado["candidatas"]} == {"023140-1", "023138-0"}


def test_pedidos_ao_site_oficial_sao_espacados(raiz):
    relogio = Relogio()
    site = SiteFipe()
    _fipe(raiz, site, relogio).candidatas("Nissan", "versa sl 1.6", 2019)
    assert len(relogio.esperas) == site.pedidos(HOST_FIPE_OFICIAL) - 1
    assert all(e == pytest.approx(1.0) for e in relogio.esperas)


def test_site_oficial_bloqueado_espera_e_tenta_de_novo(raiz):
    relogio = Relogio()
    site = SiteFipe(parallelum="limite", oficial_bloqueios=2)
    assert _fipe(raiz, site, relogio).valor("023140-1", 2019)["fonte"] == "fipe.org.br"
    assert 5.0 in relogio.esperas and 15.0 in relogio.esperas


def test_site_oficial_que_nao_volta_e_erro_claro(raiz):
    with pytest.raises(ErroFipe, match="FIPE indisponível"):
        _fipe(raiz, SiteFipe(parallelum="limite", oficial_bloqueios=99)).valor("023140-1", 2019)


def test_parallelum_no_limite_nao_e_chamada_de_novo(raiz):
    site = SiteFipe(parallelum="limite")
    fipe = _fipe(raiz, site)
    fipe.valor("023140-1", 2019)
    fipe.candidatas("Nissan", "versa sl 1.6", 2019)
    assert site.pedidos(HOST_PARALLELUM) == 1, "o limite é diário: depois do primeiro 429, só o site oficial"
