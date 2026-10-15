"""FIPE pela parallelum, com reserva no site oficial e cache por mês (feature 006; roadmap D-114; RF-09)."""

from decimal import Decimal

import httpx
import pytest

from apoio import HOST_FIPE_OFICIAL, HOST_PARALLELUM, SiteFipe
from bot_leilao.analise.fipe import ErroFipe, Fipe

AUT, MEC = "VERSA SL 1.6 16V FlexStart 4p Aut.", "VERSA SL 1.6 16V FlexStart 4p Mec."


def _fipe(raiz, site: SiteFipe) -> Fipe:
    return Fipe(raiz / "dados" / "fipe-cache.json", httpx.MockTransport(site.responder))


def test_candidatas_por_marca_termos_e_ano(raiz):
    resultado = _fipe(raiz, SiteFipe()).candidatas("Nissan", "versa sl 1.6", 2019)
    assert resultado["mes_referencia"] == "outubro/2026"
    assert resultado["fonte"] == "parallelum"
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
    assert [h for h in site.hosts_chamados() if h == HOST_PARALLELUM] == [HOST_PARALLELUM], \
        "só a consulta do mês de referência"


def test_mes_novo_ignora_o_cache_antigo(raiz):
    _fipe(raiz, SiteFipe()).valor("023140-1", 2019)
    site = SiteFipe(referencia=("339", "novembro/2026"))
    assert _fipe(raiz, site).valor("023140-1", 2019)["mes_referencia"] == "novembro/2026"
    assert len(site.chamadas) > 1


def test_codigo_sem_o_ano_e_erro(raiz):
    with pytest.raises(ErroFipe, match="2030"):
        _fipe(raiz, SiteFipe()).valor("023140-1", 2030)
