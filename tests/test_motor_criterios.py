"""Critérios do motor (RN-01 a RN-04, RN-11, RN-12; RF-08, RF-16, RF-17 da feature; roadmap D-19)."""

from decimal import Decimal

import pytest

from apoio import alvo, lote
from bot_leilao.filtro.motor import avaliar, casa


def test_exemplo_do_requirements_casa():
    """RF-08: 2017/2018, R$ 41.900 × alvo 2018–2021, teto R$ 45.000."""
    assert casa(lote(ano_fabricacao=2017, ano_modelo=2018, lance_corrente=Decimal("41900")), alvo())


def test_exemplo_do_requirements_acima_do_teto_nao_casa():
    """Cenário 3: abriu em R$ 30.000, está em R$ 52.000."""
    assert not casa(lote(lance_inicial=Decimal("30000"), lance_corrente=Decimal("52000")), alvo())


@pytest.mark.parametrize("ano_modelo, esperado", [(2017, False), (2018, True), (2021, True), (2022, False)])
def test_ano_de_modelo_com_extremos(ano_modelo, esperado):
    """RN-02: compara o ano de modelo, e não o de fabricação."""
    assert casa(lote(ano_fabricacao=2017, ano_modelo=ano_modelo), alvo()) is esperado


def test_ano_de_fabricacao_dentro_da_faixa_nao_basta():
    assert not casa(lote(ano_fabricacao=2018, ano_modelo=2017), alvo())


def test_preco_igual_ao_teto_casa():
    assert casa(lote(lance_corrente=Decimal("45000")), alvo())


@pytest.mark.parametrize("inicial, esperado", [(Decimal("30000"), True), (Decimal("50000"), False)])
def test_sem_lance_compara_o_inicial(inicial, esperado):
    """RN-03."""
    assert casa(lote(lance_corrente=None, lance_inicial=inicial), alvo()) is esperado


def test_sem_nenhum_preco_e_candidato_a_confirmar():
    """RN-04 / motor RF-07."""
    resultado = avaliar([lote(lance_corrente=None, lance_inicial=None)], [alvo()])
    (candidato,) = resultado.candidatos
    assert candidato.preco_a_confirmar is True
    assert candidato.preco is None


def test_preco_do_candidato_e_o_corrente_senao_o_inicial():
    (com_lance,) = avaliar([lote(lance_corrente=Decimal("41900"))], [alvo()]).candidatos
    (sem_lance,) = avaliar([lote(lance_corrente=None, lance_inicial=Decimal("30000"))], [alvo()]).candidatos
    assert com_lance.preco == Decimal("41900")
    assert sem_lance.preco == Decimal("30000")


def test_sem_ano_de_modelo_e_descartado_por_dado_ausente():
    """RN-04 / motor RF-08."""
    resultado = avaliar([lote(ano_modelo=None)], [alvo()])
    assert resultado.candidatos == []
    assert resultado.descartados_dado_ausente == 1


def test_quilometragem_maxima_opcional():
    """RN-11 / RF-16: teto de 120.000 não casa com 167.387 km; sem teto, qualquer km."""
    com_teto = alvo(quilometragem_maxima=120000)
    assert not casa(lote(quilometragem=167387), com_teto)
    assert casa(lote(quilometragem=120000), com_teto)
    assert casa(lote(quilometragem=167387), alvo(quilometragem_maxima=None))


def test_quilometragem_ausente_nao_elimina():
    """D-19."""
    (candidato,) = avaliar([lote(quilometragem=None)], [alvo(quilometragem_maxima=120000)]).candidatos
    assert candidato.km_a_confirmar is True


def test_acima_do_teto_de_km_tem_contador_proprio():
    resultado = avaliar([lote(quilometragem=200000)], [alvo(quilometragem_maxima=120000)])
    assert resultado.descartados_acima_km == 1
    assert resultado.descartados_sem_casar == 0


@pytest.mark.parametrize("tipo, esperado", [("financiamento", True), ("seguradora", False), (None, False)])
def test_tipo_de_leilao(tipo, esperado):
    assert casa(lote(tipo_leilao=tipo), alvo(tipos_leilao=("financiamento",))) is esperado


def test_marca_e_modelo_por_conteudo_sem_acento_nem_caixa():
    """Motor RF-02."""
    assert casa(lote(marca="citroen", modelo="c3 glx 14 flex"), alvo(marca="Citroën", modelo="C3"))
    assert not casa(lote(marca="citroen", modelo="c4 lounge"), alvo(marca="Citroën", modelo="C3"))
    assert not casa(lote(marca="fiat", modelo="versa"), alvo())


def test_marca_do_alvo_tambem_passa_pela_tabela_de_sinonimos():
    """Alvo escrito 'GM' casa com lote canônico 'chevrolet' (D-28)."""
    assert casa(lote(marca="chevrolet", modelo="onix 10mt lt2"), alvo(marca="GM", modelo="Onix"))


def test_retirados_sao_descartados_antes_de_filtrar():
    """RN-12 / RF-17: 12 lotes, 2 retirados → 10 avaliados, contador 2."""
    lotes = [lote(id_canonico=f"v:{i}", retirado=i < 2) for i in range(12)]
    resultado = avaliar(lotes, [alvo()])
    assert resultado.descartados_retirados == 2
    assert len(resultado.candidatos) == 10
    assert resultado.vistos == 12


def test_lote_que_casa_com_dois_alvos_gera_um_candidato_com_o_primeiro():
    """Motor RF-11."""
    primeiro = alvo(id="primeiro")
    segundo = alvo(id="segundo", preco_maximo=Decimal("99999"))
    (candidato,) = avaliar([lote()], [primeiro, segundo]).candidatos
    assert candidato.alvo.id == "primeiro"


def test_contagens():
    lotes = [lote(id_canonico="a"), lote(id_canonico="b", marca="fiat", modelo="uno"),
             lote(id_canonico="c", ano_modelo=None), lote(id_canonico="d", retirado=True)]
    resultado = avaliar(lotes, [alvo()])
    assert (resultado.vistos, len(resultado.candidatos), resultado.descartados_sem_casar,
            resultado.descartados_dado_ausente, resultado.descartados_retirados) == (4, 1, 1, 1, 1)


def test_sem_alvos_nada_e_avaliado():
    """Motor EC-10."""
    resultado = avaliar([lote()], [])
    assert resultado.candidatos == []
