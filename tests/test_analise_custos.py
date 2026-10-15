"""Custo na garagem (feature 006; roadmap D-116; RN-08, RF-08, RF-10)."""

from decimal import Decimal

import pytest

from apoio import escrever
from bot_leilao.analise.custos import ErroCustos, calcular, carregar_custos


@pytest.fixture
def custos(raiz):
    return carregar_custos(raiz / "config" / "custos.yaml")


def test_arquivo_criado_com_os_valores_do_clarify(raiz, custos):
    texto = (raiz / "config" / "custos.yaml").read_text(encoding="utf-8")
    assert "frete_por_km: 4.50" in texto
    assert custos.comissao_percentual == Decimal("5")
    assert custos.despesa_padrao == Decimal("2650")
    assert custos.frete_por_km == Decimal("4.50")
    assert (custos.transferencia_mesmo_estado, custos.transferencia_outro_estado) == (Decimal("450"), Decimal("650"))
    assert custos.uf_base == "PR"
    assert custos.reparos_reserva == Decimal("2000")
    assert (custos.revenda_percentual_fipe, custos.margem_percentual) == (Decimal("85"), Decimal("10"))
    assert custos.cidade_base == "Londrina - PR"
    assert custos.distancias == {}


def test_exemplo_do_requirements(custos):
    resultado = calcular(custos, lance=Decimal("61000"), despesa=Decimal("2650"), km=380, documento_uf="SC")
    p = resultado["parcelas"]
    assert (p["lance"], p["comissao"], p["despesa"], p["frete"], p["transferencia"], p["reparos"]) == (
        Decimal("61000"), Decimal("3050"), Decimal("2650"), Decimal("1710"), Decimal("650"), Decimal("2000"))
    assert p["frete_km"] == 380 and p["frete_estimado"] is True
    assert resultado["total"] == Decimal("71060")
    assert resultado["percentual_fipe"] is None and resultado["lance_maximo"] is None


def test_percentual_da_fipe_e_lance_maximo(custos):
    resultado = calcular(custos, lance=Decimal("61000"), despesa=Decimal("2650"), km=380, documento_uf="SC",
                         fipe=Decimal("99011"))
    assert resultado["percentual_fipe"] == 72
    # (99.011 × 0,85 ÷ 1,10 − 2.650 − 1.710 − 650 − 2.000) ÷ 1,05 = 66.189,05
    assert resultado["lance_maximo"] == Decimal("66189")


def test_mesma_entrada_mesmo_resultado(custos):
    entrada = dict(lance=Decimal("43000"), despesa=None, km=386, documento_uf="PR", fipe=Decimal("81336"))
    assert calcular(custos, **entrada) == calcular(custos, **entrada)


def test_despesa_ausente_usa_o_padrao_marcado(custos):
    p = calcular(custos, lance=Decimal("43000"), despesa=None, km=386, documento_uf="PR")["parcelas"]
    assert p["despesa"] == Decimal("2650") and p["despesa_padrao"] is True
    assert p["transferencia"] == Decimal("450"), "documento do PR"


def test_documento_desconhecido_usa_outro_estado_com_aviso(custos):
    resultado = calcular(custos, lance=Decimal("43000"), despesa=Decimal("2350"), km=386, documento_uf=None)
    assert resultado["parcelas"]["transferencia"] == Decimal("650")
    assert any("documento" in a for a in resultado["avisos"])


def test_distancia_desconhecida_deixa_o_frete_a_confirmar(custos):
    resultado = calcular(custos, lance=Decimal("43000"), despesa=Decimal("2350"), km=None, documento_uf="PR")
    assert resultado["parcelas"]["frete"] is None
    assert any("frete a confirmar" in a for a in resultado["avisos"])
    assert resultado["total"] == Decimal("43000") + Decimal("2150") + Decimal("2350") + Decimal("450") + Decimal("2000")


def test_reparos_extras_com_motivo(custos):
    resultado = calcular(custos, lance=Decimal("61000"), despesa=Decimal("2650"), km=380, documento_uf="SC",
                         reparos_extra=Decimal("1500"), motivo_reparos="para-choque traseiro")
    assert resultado["parcelas"]["reparos_extra"] == Decimal("1500")
    assert resultado["parcelas"]["motivo_reparos"] == "para-choque traseiro"
    assert resultado["total"] == Decimal("72560")


def test_reparos_extras_sem_motivo_e_erro(custos):
    with pytest.raises(ErroCustos, match="motivo"):
        calcular(custos, lance=Decimal("1"), despesa=None, km=1, documento_uf="PR", reparos_extra=Decimal("10"))


def test_tabela_de_distancias_lida_do_arquivo(raiz):
    escrever(raiz / "config" / "custos.yaml", _arquivo_completo() + "distancias:\n  \"Curitiba - PR\": 380\n")
    assert carregar_custos(raiz / "config" / "custos.yaml").distancias == {"Curitiba - PR": 380}


@pytest.mark.parametrize("linha", ["frete_por_km: barato", "comissao_percentual: -5", "margem_percentual: ''"])
def test_campo_invalido_e_erro_citando_o_campo(raiz, linha):
    campo = linha.split(":")[0]
    texto = "\n".join(l for l in _arquivo_completo().splitlines() if not l.startswith(campo + ":")) + f"\n{linha}\n"
    escrever(raiz / "config" / "custos.yaml", texto)
    with pytest.raises(ErroCustos, match=campo):
        carregar_custos(raiz / "config" / "custos.yaml")


def _arquivo_completo() -> str:
    return ("cidade_base: Londrina - PR\nuf_base: PR\ncomissao_percentual: 5\ndespesa_padrao: 2650\n"
            "frete_por_km: 4.50\ntransferencia_mesmo_estado: 450\ntransferencia_outro_estado: 650\n"
            "reparos_reserva: 2000\nrevenda_percentual_fipe: 85\nmargem_percentual: 10\n")
