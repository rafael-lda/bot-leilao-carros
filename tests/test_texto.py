from bot_leilao.texto import gerar_id, normalizar_texto


def test_normalizar_remove_acento_caixa_e_espacos():
    assert normalizar_texto("  Citroën   C3  ") == "citroen c3"
    assert normalizar_texto("LEILÕES") == "leiloes"


def test_normalizar_none_vira_vazio():
    assert normalizar_texto(None) == ""


def test_gerar_id_do_leiloeiro():
    assert gerar_id("Vip Leilões") == "vip-leiloes"


def test_gerar_id_com_varias_partes_e_numeros():
    assert gerar_id("Nissan", "Versa", 2018, 2021) == "nissan-versa-2018-2021"


def test_gerar_id_colapsa_pontuacao():
    assert gerar_id("Mercedes-Benz", "C 180 / Avantgarde") == "mercedes-benz-c-180-avantgarde"


def test_gerar_id_e_estavel():
    assert gerar_id("Toyota", "Corolla XEi") == gerar_id("toyota", "COROLLA  xei")
