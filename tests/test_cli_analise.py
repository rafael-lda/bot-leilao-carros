"""Linha de comando `analise` (feature 006; interfaces/cli-analise.md; roadmap D-104, D-117; RF-01, RF-11, RN-01)."""

import io
import json
from pathlib import Path

import pytest

from apoio import CenarioE2E, SiteFipe, SiteKuss, SiteMapas, detalhe_kuss, escrever, lista_de_teste
from bot_leilao.cli import principal
from bot_leilao.db.trava import Trava

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
LINK_3 = "https://www.claudiokussleiloes.com.br/lance/897/0/282622"
CUSTOS = ("cidade_base: Londrina - PR\nuf_base: PR\ncomissao_percentual: 5\ndespesa_padrao: 2650\n"
          "frete_por_km: 4.50\ntransferencia_mesmo_estado: 450\ntransferencia_outro_estado: 650\n"
          "reparos_reserva: 2000\nrevenda_percentual_fipe: 85\nmargem_percentual: 10\n"
          "distancias:\n  \"Curitiba - PR\": 380\n")
ALVOS = """\
padrao:
  cambio: [automatico, cvt]
  aceitar_sinistro: false
veiculos:
  - marca: Renault
    modelo: Fluence
    ano_min: 2010
    ano_max: 2017
    preco_maximo: 46900
    tipos_leilao: [financiamento]
    triagem: "Só 2.0 Dynamique Plus ou Privilège, automáticos."
  - marca: Nissan
    modelo: Kicks
    ano_min: 2018
    ano_max: 2019
    preco_maximo: 56900
    tipos_leilao: [financiamento]
"""


@pytest.fixture
def cenario(raiz, relogio, agora):
    cenario = CenarioE2E(raiz, relogio, agora, alvos=ALVOS)
    cenario.fipe, cenario.mapas = SiteFipe(), SiteMapas()
    escrever(raiz / "config" / "custos.yaml", CUSTOS)
    lista_de_teste(raiz)
    return cenario


def _rodar(cenario, capsys, *args, entrada: str | None = None, monkeypatch=None):
    if entrada is not None:
        monkeypatch.setattr("sys.stdin", io.StringIO(entrada))
    codigo = principal(["analise", *args, "--raiz", str(cenario.raiz)], deps=cenario.deps)
    saida = capsys.readouterr().out
    return codigo, (json.loads(saida) if saida.strip() else None)


def _lista(cenario) -> str:
    return (cenario.raiz / "1OUTPUT" / "lotes-a-monitorar.md").read_text(encoding="utf-8")


def test_lotes_com_o_alvo_e_os_criterios(cenario, capsys):
    codigo, saida = _rodar(cenario, capsys, "lotes")
    assert codigo == 0 and len(saida["lotes"]) == 14
    codigo, saida = _rodar(cenario, capsys, "lotes", "--numero", "2")
    (fluence,) = saida["lotes"]
    assert fluence["titulo"] == "IMP RENAULT/FLUENCE DYN 20M"
    assert fluence["alvo"]["id"] == "renault-fluence-2010-2017"
    assert fluence["alvo"]["criterios"]["cambio"] == ["automatico", "cvt"]
    assert fluence["alvo"]["criterios"]["aceitar_sinistro"] is False
    assert fluence["alvo"]["triagem"].startswith("Só 2.0")


def test_lotes_pelo_link(cenario, capsys):
    _, saida = _rodar(cenario, capsys, "lotes", "--link", LINK_3)
    assert [l["numero"] for l in saida["lotes"]] == [3]


def test_alvo_que_saiu_da_configuracao_vem_nulo(cenario, capsys):
    _, saida = _rodar(cenario, capsys, "lotes", "--numero", "4")  # Duster: fora do ALVOS deste teste
    assert saida["lotes"][0]["alvo"] is None


def test_pagina_pelo_numero_ou_pelo_link(cenario, capsys):
    cenario.kuss = SiteKuss(detalhes={"282622": detalhe_kuss()})
    for referencia in ("3", LINK_3):
        codigo, saida = _rodar(cenario, capsys, "pagina", referencia)
        assert codigo == 0
        assert (saida["numero"], saida["leiloeiro"]) == (3, "claudio-kuss-leiloes")
        assert "SINISTRADO" in saida["texto"]


def test_triar_reprovado_move_para_os_descartados(cenario, capsys):
    codigo, saida = _rodar(cenario, capsys, "triar", "2", "--veredito", "reprovado", "--motivo", "câmbio manual",
                           "--evidencia", "título 'DYN 20M'")
    assert codigo == 0 and saida["numero"] == 2 and saida["destino"] == "lotes-descartados.md"
    assert "### 2." not in _lista(cenario)
    codigo, _ = _rodar(cenario, capsys, "devolver", "2")
    assert codigo == 0 and "### 2." in _lista(cenario)


def test_triar_pelo_link_e_a_confirmar(cenario, capsys):
    codigo, _ = _rodar(cenario, capsys, "triar", LINK_3, "--veredito", "a-confirmar", "--falta", "câmbio")
    assert codigo == 0 and "a confirmar — câmbio" in _lista(cenario)


def test_com_a_varredura_em_andamento_nada_e_escrito(cenario, capsys):
    original = _lista(cenario)
    trava = Trava(cenario.raiz / "dados" / "varredura.lock")
    assert trava.adquirir()
    try:
        codigo, saida = _rodar(cenario, capsys, "triar", "1", "--veredito", "aprovado")
    finally:
        trava.liberar()
    assert codigo == 3
    assert "varredura" in saida["erro"]
    assert _lista(cenario) == original


def test_erro_vira_json_com_codigo_1(cenario, capsys):
    codigo, saida = _rodar(cenario, capsys, "triar", "99", "--veredito", "aprovado")
    assert codigo == 1 and "99" in saida["erro"]


def test_fipe_candidatas_e_valor(cenario, capsys):
    codigo, saida = _rodar(cenario, capsys, "fipe-candidatos", "--marca", "Nissan", "--modelo", "versa sl 1.6",
                           "--ano", "2019")
    assert codigo == 0 and {c["codigo"] for c in saida["candidatas"]} == {"023140-1", "023138-0"}
    codigo, saida = _rodar(cenario, capsys, "fipe-valor", "--codigo", "023140-1", "--ano", "2019")
    assert codigo == 0 and saida["valor"] == 62464 and saida["mes_referencia"] == "outubro/2026"


def test_custo_do_exemplo_do_requirements(cenario, capsys):
    codigo, saida = _rodar(cenario, capsys, "custo", "--lance", "61000", "--despesa", "2650", "--patio",
                           "Curitiba - PR", "--documento-uf", "SC")
    assert codigo == 0 and saida["total"] == 71060 and saida["parcelas"]["frete_km"] == 380


def test_custo_calcula_a_distancia_quando_nao_esta_na_tabela(cenario, capsys):
    escrever(cenario.raiz / "config" / "custos.yaml", CUSTOS.split("distancias:")[0])
    _, saida = _rodar(cenario, capsys, "custo", "--lance", "61000", "--patio", "Curitiba - PR", "--documento-uf", "PR")
    assert saida["parcelas"]["frete_km"] == 385


def test_anotar_custo_preenche_os_campos_do_bloco(cenario, capsys, monkeypatch):
    _, custo = _rodar(cenario, capsys, "custo", "--lance", "43000", "--despesa", "2350", "--patio", "Curitiba - PR",
                      "--documento-uf", "SC", "--fipe", "81336")
    entrada = json.dumps({"fipe": {"codigo": "023149-5", "versao": "KICKS SL 1.6 16V CVT", "valor": 81336,
                                   "mes_referencia": "outubro/2026"}, "custo": custo})
    codigo, _ = _rodar(cenario, capsys, "anotar-custo", "1", "--json", "-", entrada=entrada, monkeypatch=monkeypatch)
    assert codigo == 0
    bloco = _lista(cenario).split("### 1.")[1].split("---")[0]
    linhas = bloco.splitlines()
    assert "- **FIPE:** R$ 81.336 — KICKS SL 1.6 16V CVT (023149-5, outubro/2026)" in linhas
    assert "- **Lance ao entrar:** R$ 43.000 (53% da FIPE)" in linhas
    assert "- **Despesas admin.:** R$ 2.350" in linhas, "já estava preenchida: não muda"
    assert "- **Frete:** R$ 1.710 (380 km × R$ 4,50, estimativa)" in linhas
    i = linhas.index("- **Valor estimado na garagem:** R$ 51.860 (64% da FIPE)")
    assert linhas[i + 1] == "- **Lance máximo (margem 10%):** R$ 53.467"
    assert "<!-- lote: claudio-kuss-leiloes:282164 -->" in bloco


def test_anotar_custo_com_versao_ambigua_lista_as_candidatas(cenario, capsys, monkeypatch):
    _, candidatas = _rodar(cenario, capsys, "fipe-candidatos", "--marca", "Nissan", "--modelo", "versa sl 1.6",
                           "--ano", "2019")
    entrada = json.dumps({"fipe": None, "candidatas": candidatas, "custo": None})
    codigo, _ = _rodar(cenario, capsys, "anotar-custo", "10", "--json", "-", entrada=entrada, monkeypatch=monkeypatch)
    assert codigo == 0
    bloco = _lista(cenario).split("### 10.")[1].split("---")[0]
    linha_fipe = next(l for l in bloco.splitlines() if l.startswith("- **FIPE:**"))
    assert linha_fipe.startswith("- **FIPE:** _a escolher_:")
    assert "023140-1" in linha_fipe and "023138-0" in linha_fipe and "outubro/2026" in linha_fipe
    assert "- **Valor estimado na garagem:** (% da FIPE)" in bloco, "sem versão escolhida, sem custo"


def test_anotar_campo_pela_linha_de_comando(cenario, capsys):
    codigo, saida = _rodar(cenario, capsys, "anotar", "1", "--campo", "Câmbio", "--valor", "CVT (título)")
    assert codigo == 0 and saida == {"numero": 1, "campo": "Câmbio", "valor": "CVT (título)"}
    assert "- **Câmbio:** CVT (título)" in _lista(cenario)
    trava = Trava(cenario.raiz / "dados" / "varredura.lock")
    assert trava.adquirir()
    try:
        codigo, _ = _rodar(cenario, capsys, "anotar", "1", "--campo", "Câmbio", "--valor", "manual")
    finally:
        trava.liberar()
    assert codigo == 3
