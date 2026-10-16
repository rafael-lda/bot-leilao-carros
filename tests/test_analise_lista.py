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


# --- Ajuste de 2026-10-15 (pedido do Rafael): anotar um campo do bloco -----------------------------------

from bot_leilao.analise.lista import CAMPOS_ANOTAVEIS, anotar_campo  # noqa: E402


def test_anotar_campo_existente_substitui_o_valor(lista):
    antes = _blocos_por_numero(lista)
    anotar_campo(lista, 1, "Câmbio", "CVT (título \"S DRCT CVT\")")
    depois = _blocos_por_numero(lista)
    assert depois[1].campos["Câmbio"] == "CVT (título \"S DRCT CVT\")"
    assert depois[1].texto.count("**Câmbio:**") == 1
    assert all(depois[n].texto == antes[n].texto for n in range(2, 15))


def test_anotar_campo_novo_entra_antes_do_link(lista):
    anotar_campo(lista, 1, "Resultado do pregão", "13/10: último lance presencial; valor não divulgado pelo site")
    linhas = _blocos_por_numero(lista)[1].texto.splitlines()
    i = next(n for n, l in enumerate(linhas) if l.startswith("- **Resultado do pregão:**"))
    assert linhas[i + 1].startswith("- **Link:**")


def test_so_campos_conhecidos(lista):
    assert {"Câmbio", "Resultado do pregão"} <= set(CAMPOS_ANOTAVEIS)
    with pytest.raises(ErroLista, match="campo"):
        anotar_campo(lista, 1, "Link", "outro")
    with pytest.raises(ErroLista, match="valor"):
        anotar_campo(lista, 1, "Câmbio", "  ")


def test_campo_de_triagem_sai_sem_a_data_no_nome(lista):
    triar(lista, 1, "aprovado", hoje=HOJE)
    assert _blocos_por_numero(lista)[1].campos["Triagem"] == "aprovado (15/10/2026)"
    triar(lista, 2, "reprovado", motivo="câmbio manual", evidencia="título 'DYN 20M'", hoje=HOJE)
    (descartado,) = ler_lista(lista.parent / "lotes-descartados.md")
    assert descartado.campos["Descartado"] == "câmbio manual — título 'DYN 20M' (15/10/2026)"


def test_reconferencia_grava_lance_atual_e_pregao_e_retria(lista):
    """Emenda de 2026-10-15 (RF-14, D-121): o "a confirmar" é relido; lance e pregão entram no bloco e a triagem
    nova substitui a antiga."""
    triar(lista, 4, "a-confirmar", hoje=date(2026, 10, 15), falta="data e lance (aguardando classificação)")
    anotar_campo(lista, 4, "Lance atual", "R$ 21.000 (lido em 16/10/2026)")
    anotar_campo(lista, 4, "Pregão", "22/10/2026 10:00")
    triar(lista, 4, "a-confirmar", hoje=date(2026, 10, 16), falta="câmbio")
    bloco = _blocos_por_numero(lista)[4]
    assert bloco.campos["Lance atual"] == "R$ 21.000 (lido em 16/10/2026)"
    assert bloco.campos["Pregão"] == "22/10/2026 10:00"
    assert bloco.campos["Triagem"] == "a confirmar — câmbio (16/10/2026)"
    assert bloco.texto.count("**Triagem (") == 1
    assert bloco.texto.count("**Lance atual:**") == 1


def test_encerrado_fica_na_lista_com_o_resultado(lista):
    """Emenda de 2026-10-16 (D-124): pregão acabado não é "aprovado"; o lote fica como registro."""
    assert triar(lista, 1, "encerrado", hoje=date(2026, 10, 16), motivo="vendido em 13/10; valor não divulgado") == \
        "lotes-a-monitorar.md"
    assert _blocos_por_numero(lista)[1].campos["Triagem"] == "encerrado — vendido em 13/10; valor não divulgado (16/10/2026)"
    with pytest.raises(ErroLista, match="encerrado exige"):
        triar(lista, 2, "encerrado", hoje=date(2026, 10, 16))
