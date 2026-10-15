"""Lista de monitoramento: leitura, triagem, descarte e devolução (feature 006; roadmap D-112; RF-03, RF-04)."""

from datetime import date

import pytest

from apoio import lista_de_teste
from bot_leilao.analise.lista import ErroLista, devolver, ler_lista, numero_por_link, triar

HOJE = date(2026, 10, 15)
LINK_3 = "https://www.claudiokussleiloes.com.br/lance/897/0/282622"


@pytest.fixture
def lista(raiz):
    return lista_de_teste(raiz)


def _blocos_por_numero(caminho):
    return {b.numero: b for b in ler_lista(caminho)}


def test_le_os_14_blocos_com_campos(lista):
    blocos = ler_lista(lista)
    assert [b.numero for b in blocos] == list(range(1, 15))
    kicks = blocos[0]
    assert kicks.id == "claudio-kuss-leiloes:282164"
    assert (kicks.titulo, kicks.ano) == ("NISSAN/KICKS S DRCT CVT", "2019")
    assert kicks.campos["Pátio"] == "Curitiba - PR"
    assert kicks.campos["Câmbio"] == ""
    assert kicks.campos["Alvo"].startswith("nissan-kicks-2018-2019")
    assert blocos[2].campos["Observações"].startswith("SINISTRADO")


def test_aprovado_ganha_a_linha_antes_do_link_e_o_resto_fica_igual(lista):
    antes = _blocos_por_numero(lista)
    triar(lista, 1, "aprovado", hoje=HOJE)
    depois = _blocos_por_numero(lista)
    linhas = depois[1].texto.splitlines()
    i = linhas.index("- **Triagem (15/10/2026):** aprovado")
    assert linhas[i + 1].startswith("- **Link:**")
    assert "<!-- lote: claudio-kuss-leiloes:282164 -->" in depois[1].texto
    assert all(depois[n].texto == antes[n].texto for n in range(2, 15))


def test_nova_triagem_substitui_a_anterior(lista):
    triar(lista, 5, "a-confirmar", falta="câmbio; lance", hoje=HOJE)
    triar(lista, 5, "aprovado", hoje=date(2026, 10, 20))
    texto = _blocos_por_numero(lista)[5].texto
    assert texto.count("**Triagem") == 1
    assert "- **Triagem (20/10/2026):** aprovado" in texto


def test_a_confirmar_diz_o_que_falta(lista):
    triar(lista, 5, "a-confirmar", falta="câmbio; lance", hoje=HOJE)
    assert "- **Triagem (15/10/2026):** a confirmar — câmbio; lance" in _blocos_por_numero(lista)[5].texto


def test_reprovado_vai_para_os_descartados_com_motivo_e_evidencia(lista):
    antes = _blocos_por_numero(lista)
    triar(lista, 2, "reprovado", motivo="câmbio manual", evidencia="título 'DYN 20M'", hoje=HOJE)

    depois = _blocos_por_numero(lista)
    assert 2 not in depois
    assert sorted(depois) == [1] + list(range(3, 15)), "os números dos outros não mudam"
    assert all(depois[n].texto == antes[n].texto for n in depois)

    descartados = (lista.parent / "lotes-descartados.md").read_text(encoding="utf-8")
    assert descartados.startswith("# Lotes descartados")
    assert "### 2. IMP RENAULT/FLUENCE DYN 20M — 2015" in descartados
    assert "<!-- lote: claudio-kuss-leiloes:282341 -->" in descartados
    assert "- **Descartado em 15/10/2026:** câmbio manual — título 'DYN 20M'" in descartados


def test_reprovado_exige_motivo_e_evidencia(lista):
    with pytest.raises(ErroLista, match="motivo"):
        triar(lista, 2, "reprovado", evidencia="x", hoje=HOJE)
    with pytest.raises(ErroLista, match="evid"):
        triar(lista, 2, "reprovado", motivo="x", hoje=HOJE)
    with pytest.raises(ErroLista, match="falta"):
        triar(lista, 2, "a-confirmar", hoje=HOJE)


def test_devolver_traz_o_bloco_de_volta_para_o_fim(lista):
    triar(lista, 2, "reprovado", motivo="câmbio manual", evidencia="título 'DYN 20M'", hoje=HOJE)
    devolver(lista, 2)
    blocos = ler_lista(lista)
    assert blocos[-1].numero == 2
    assert "Descartado em" not in blocos[-1].texto
    assert "### 2." not in (lista.parent / "lotes-descartados.md").read_text(encoding="utf-8")


def test_dois_descartes_acumulam_no_arquivo(lista):
    triar(lista, 2, "reprovado", motivo="câmbio manual", evidencia="título 'DYN 20M'", hoje=HOJE)
    triar(lista, 3, "reprovado", motivo="sinistro", evidencia="observação 'SINISTRADO'", hoje=HOJE)
    descartados = (lista.parent / "lotes-descartados.md").read_text(encoding="utf-8")
    assert descartados.index("### 2.") < descartados.index("### 3.")


@pytest.mark.parametrize("chamada", [
    lambda c: triar(c, 99, "aprovado", hoje=HOJE),
    lambda c: triar(c, 1, "talvez", hoje=HOJE),
    lambda c: devolver(c, 1),
])
def test_numero_inexistente_ou_veredito_invalido_e_erro(lista, chamada):
    original = lista.read_bytes()
    with pytest.raises(ErroLista):
        chamada(lista)
    assert lista.read_bytes() == original


def test_numero_pelo_link(lista):
    assert numero_por_link(lista, LINK_3) == 3
    with pytest.raises(ErroLista):
        numero_por_link(lista, "https://exemplo.com/lote/1")


def test_escrita_atomica_nao_deixa_temporario(lista):
    triar(lista, 1, "aprovado", hoje=HOJE)
    assert sorted(p.name for p in lista.parent.iterdir()) == ["lotes-a-monitorar.md"]
