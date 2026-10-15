"""configuracao-veiculos-alvo + RF-01 e RF-16 da feature."""

from decimal import Decimal

import pytest

from apoio import escrever
from bot_leilao.config.arquivos import ConfiguracaoAusente, ErroConfiguracao
from bot_leilao.config.veiculos import TIPOS_LEILAO, carregar_veiculos

VALIDO = """
veiculos:
  - marca: Nissan
    modelo: Versa
    ano_min: 2018
    ano_max: 2021
    preco_maximo: 45000
    quilometragem_maxima: 120000
    tipos_leilao: [financiamento]
    ativo: true
  - marca: Toyota
    modelo: Corolla
    ano_min: 2017
    ano_max: 2020
    preco_maximo: 62000.50
    tipos_leilao: [financiamento, seguradora]
"""


def _carregar(raiz, texto):
    return carregar_veiculos(escrever(raiz / "config" / "veiculos-alvo.yaml", texto))


def _bloco(**campos):
    base = dict(marca="Nissan", modelo="Versa", ano_min=2018, ano_max=2021, preco_maximo=45000,
                tipos_leilao="[financiamento]")
    base.update(campos)
    linhas = [f"    {k}: {v}" for k, v in base.items() if v is not None]
    linhas[0] = "  - " + linhas[0].strip()
    return "veiculos:\n" + "\n".join(linhas) + "\n"


def test_carrega_alvos_validos(raiz):
    resultado = _carregar(raiz, VALIDO)
    assert [a.id for a in resultado.ativos] == ["nissan-versa-2018-2021", "toyota-corolla-2017-2020"]
    versa, corolla = resultado.ativos
    assert versa.preco_maximo == Decimal("45000")
    assert corolla.preco_maximo == Decimal("62000.5")
    assert versa.quilometragem_maxima == 120000
    assert corolla.quilometragem_maxima is None, "km é opcional (RN-11)"
    assert corolla.ativo is True, "ativo omitido vale true (EC-09)"
    assert corolla.tipos_leilao == ("financiamento", "seguradora")


def test_id_e_estavel_entre_carregamentos(raiz):
    assert [a.id for a in _carregar(raiz, VALIDO).ativos] == [a.id for a in _carregar(raiz, VALIDO).ativos]


def test_ano_min_maior_que_ano_max_cita_alvo_e_campo(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _bloco(ano_min=2020, ano_max=2018))
    mensagem = str(erro.value)
    assert "Nissan Versa" in mensagem
    assert "ano_min" in mensagem
    assert "2020" in mensagem and "2018" in mensagem


@pytest.mark.parametrize("preco", [0, -10, '"caro"', None])
def test_preco_ausente_zero_ou_negativo_e_rejeitado(raiz, preco):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _bloco(preco_maximo=preco))
    assert "Nissan Versa" in str(erro.value)
    assert "preco_maximo" in str(erro.value)


@pytest.mark.parametrize("km", [0, -1, '"muito"'])
def test_quilometragem_maxima_invalida_e_rejeitada(raiz, km):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _bloco(quilometragem_maxima=km))
    assert "quilometragem_maxima" in str(erro.value)


def test_quilometragem_maxima_nula_e_aceita(raiz):
    resultado = _carregar(raiz, _bloco(quilometragem_maxima="null"))
    assert resultado.ativos[0].quilometragem_maxima is None


def test_tipo_de_leilao_invalido_lista_os_aceitos(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _bloco(tipos_leilao="[leilao judicial]"))
    mensagem = str(erro.value)
    assert "leilao judicial" in mensagem
    for tipo in TIPOS_LEILAO:
        assert tipo in mensagem


def test_tipos_de_leilao_vazio_e_rejeitado(raiz):
    with pytest.raises(ErroConfiguracao):
        _carregar(raiz, _bloco(tipos_leilao="[]"))


@pytest.mark.parametrize("campo", ["marca", "modelo"])
def test_marca_ou_modelo_vazio_e_rejeitado(raiz, campo):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _bloco(**{campo: '""'}))
    assert campo in str(erro.value)


def test_ano_fora_de_quatro_digitos_e_rejeitado(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _bloco(ano_min=18))
    assert "ano_min" in str(erro.value)


def test_alvo_inativo_e_ignorado_e_contado(raiz):
    resultado = _carregar(raiz, VALIDO.replace("ativo: true", "ativo: false"))
    assert [a.id for a in resultado.ativos] == ["toyota-corolla-2017-2020"]
    assert resultado.inativos == 1


def test_todos_inativos_geram_aviso_e_nao_erro(raiz):
    """RF-01 da feature e RF-08 da spec: lista sem ativos é aviso, e não erro (A006)."""
    resultado = _carregar(raiz, _bloco(ativo="false"))
    assert resultado.ativos == []
    assert any("Nenhum veículo-alvo ativo" in aviso for aviso in resultado.avisos)


def test_lista_vazia_gera_aviso(raiz):
    resultado = _carregar(raiz, "veiculos: []\n")
    assert resultado.ativos == []
    assert resultado.avisos


def test_alvo_duplicado_gera_aviso_e_mantem_o_primeiro(raiz):
    texto = _bloco(preco_maximo=45000) + _bloco(preco_maximo=99000).replace("veiculos:\n", "")
    resultado = _carregar(raiz, texto)
    assert len(resultado.ativos) == 1
    assert resultado.ativos[0].preco_maximo == Decimal("45000")
    assert any("duplicado" in aviso for aviso in resultado.avisos)


def test_raiz_sem_lista_veiculos_e_rejeitada(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, "alvos: []\n")
    assert "veiculos" in str(erro.value)


def test_arquivo_ausente_cria_exemplo(raiz):
    with pytest.raises(ConfiguracaoAusente):
        carregar_veiculos(raiz / "config" / "veiculos-alvo.yaml")
    assert (raiz / "config" / "veiculos-alvo.yaml").exists()


# --- Feature 003: palavras a excluir (RF-10, D-72) -------------------------------------------------

def test_excluir_como_lista(raiz):
    (alvo,) = _carregar(raiz, _bloco(excluir="[Oroch, Pick-up]")).ativos
    assert alvo.excluir == ("Oroch", "Pick-up")


def test_excluir_como_texto_unico_vira_lista_de_um(raiz):
    (alvo,) = _carregar(raiz, _bloco(excluir="Oroch")).ativos
    assert alvo.excluir == ("Oroch",)


def test_sem_excluir_e_vazio(raiz):
    (alvo,) = _carregar(raiz, _bloco()).ativos
    assert alvo.excluir == ()


@pytest.mark.parametrize("valor", ['[""]', "[123]", '["  "]', "{a: 1}"])
def test_excluir_invalido_cita_alvo_e_campo(raiz, valor):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _bloco(excluir=valor))
    assert "Nissan Versa" in str(erro.value)
    assert "excluir" in str(erro.value)


# --- Feature 006: critérios da triagem no YAML (RF-05; roadmap D-107) ---------------------------------

def _com_padrao(padrao: str, alvo_extra: str = "") -> str:
    return (f"padrao:\n{padrao}" + "veiculos:\n  - marca: Nissan\n    modelo: Versa\n    ano_min: 2018\n"
            "    ano_max: 2021\n    preco_maximo: 45000\n    tipos_leilao: [financiamento]\n" + alvo_extra)


def test_sem_padrao_nem_campos_aceita_tudo(raiz):
    (versa,) = _carregar(raiz, _bloco()).ativos
    assert versa.cambio is None
    assert (versa.aceitar_sinistro, versa.aceitar_sucata, versa.aceitar_mecanica_com_problema,
            versa.aceitar_pequenas_avarias) == (True, True, True, True)
    assert versa.triagem is None


def test_padrao_vale_para_todos(raiz):
    texto = _com_padrao("  cambio: [automatico, cvt]\n  aceitar_sinistro: false\n  aceitar_sucata: false\n"
                        "  aceitar_mecanica_com_problema: false\n  aceitar_pequenas_avarias: true\n")
    (versa,) = _carregar(raiz, texto).ativos
    assert versa.cambio == ("automatico", "cvt")
    assert (versa.aceitar_sinistro, versa.aceitar_sucata, versa.aceitar_mecanica_com_problema,
            versa.aceitar_pequenas_avarias) == (False, False, False, True)


def test_alvo_sobrescreve_o_padrao_campo_a_campo(raiz):
    texto = _com_padrao("  cambio: [automatico, cvt]\n  aceitar_sinistro: false\n",
                        "    cambio: [manual]\n    triagem: \"Só SL ou Unique.\"\n")
    (versa,) = _carregar(raiz, texto).ativos
    assert versa.cambio == ("manual",)
    assert versa.aceitar_sinistro is False, "o que o alvo não repete vem do padrão"
    assert versa.triagem == "Só SL ou Unique."


@pytest.mark.parametrize("campo, valor, trecho", [
    ("cambio", "[automático]", "cambio"),
    ("cambio", "[]", "cambio"),
    ("cambio", "automatico", "cambio"),
    ("aceitar_sinistro", "talvez", "aceitar_sinistro"),
    ("aceitar_sucata", "1", "aceitar_sucata"),
    ("triagem", "''", "triagem"),
])
def test_campo_de_criterio_invalido_aborta_citando_alvo_e_campo(raiz, campo, valor, trecho):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _bloco(**{campo: valor}))
    assert trecho in str(erro.value)
    assert "Nissan Versa" in str(erro.value)


def test_padrao_invalido_aborta_citando_o_bloco(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _com_padrao("  cambio: [automatico, sequencial]\n"))
    assert "padrao" in str(erro.value) and "sequencial" in str(erro.value)


def test_padrao_com_campo_desconhecido_aborta(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _com_padrao("  aceitar_tudo: true\n"))
    assert "aceitar_tudo" in str(erro.value)
