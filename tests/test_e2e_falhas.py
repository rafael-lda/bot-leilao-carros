"""Cenários 5 a 8 do requirements.md §7, de ponta a ponta, sem rede."""

import httpx

from apoio import escrever, pagina_vazia, pagina_vip


def test_cenario_5_parser_quebrado_avisa_em_vez_de_silenciar(cenario):
    cenario.vip = pagina_vip().replace(b"card-anuncio", b"card-layout-novo").replace(
        b"resultadosEncontrados", b"totalNovo")
    resultado = cenario.varrer()

    (alerta,) = cenario.mensagens
    assert alerta.startswith("<b>Alerta do sistema")
    assert "Vip Leilões" in alerta
    assert resultado.veredito == "sucesso_parcial"
    con = cenario.banco()
    assert con.execute("SELECT quebra_suspeita, alerta_enviado FROM execucao_leiloeiro").fetchone()[:] == (1, 1)
    assert con.execute("SELECT quebra_suspeita FROM execucao_busca").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM busca_semeada").fetchone()[0] == 0, "busca quebrada não semeia (D-20)"


def test_alerta_de_quebra_no_maximo_um_por_dia(cenario):
    """D-22 / notificador EC-10."""
    cenario.vip = pagina_vip().replace(b"card-anuncio", b"card-layout-novo").replace(
        b"resultadosEncontrados", b"totalNovo")
    cenario.varrer()
    cenario.varrer()
    assert len(cenario.mensagens) == 1
    cenario.agora.avancar(days=1)
    cenario.varrer()
    assert len(cenario.mensagens) == 2


def test_busca_vazia_legitima_nao_alerta(cenario):
    """D-31: 'Nenhum lote encontrado.' não é layout quebrado."""
    cenario.vip = pagina_vazia()
    resultado = cenario.varrer()
    assert resultado.veredito == "sucesso"
    assert cenario.mensagens == []


def test_cenario_6_falha_no_envio_preserva_os_lotes(cenario):
    cenario.vip = pagina_vazia()
    cenario.varrer()
    cenario.vip = pagina_vip()
    cenario.telegram = 500
    resultado = cenario.varrer()

    assert resultado.veredito == "falha"
    assert resultado.codigo_saida == 1
    assert resultado.motivo.startswith("envio_digest")
    assert cenario.notificados() == [], "nenhum lote gravado como notificado"
    assert len([c for c in cenario.chamadas if c.url.host == "api.telegram.org"]) == 3, "3 tentativas"

    cenario.telegram = 200
    cenario.varrer()
    (digest,) = cenario.mensagens
    assert "Versa" in digest, "o mesmo lote volta como candidato"
    assert cenario.notificados() == ["vip-leiloes:400001"]


def test_cenario_7_configuracao_invalida_aborta_antes_da_rede(cenario):
    escrever(cenario.raiz / "config" / "veiculos-alvo.yaml",
             "veiculos:\n  - marca: Nissan\n    modelo: Versa\n    ano_min: 2021\n    ano_max: 2018\n"
             "    preco_maximo: 45000\n    tipos_leilao: [financiamento]\n")
    resultado = cenario.varrer()

    assert resultado.veredito == "falha"
    assert resultado.codigo_saida == 1
    assert "Nissan Versa" in resultado.motivo and "ano_min" in resultado.motivo
    assert cenario.chamadas == [], "nenhuma requisição HTTP"
    assert cenario.execucoes()[-1]["motivo"].startswith("config_invalida")


def test_cenario_8_bloqueio_e_distinto_de_falha_de_rede(cenario):
    cenario.vip = 429
    resultado = cenario.varrer()

    busca = cenario.banco().execute("SELECT veredito, tentativas, motivo FROM execucao_busca").fetchone()
    assert busca["veredito"] == "bloqueado"
    assert busca["tentativas"] == 3
    leiloeiro = cenario.banco().execute("SELECT buscas_bloqueadas, buscas_falhas FROM execucao_leiloeiro").fetchone()
    assert (leiloeiro["buscas_bloqueadas"], leiloeiro["buscas_falhas"]) == (1, 0), "evidência para escalar o nível"
    assert resultado.veredito == "falha"


def test_timeout_e_falha_de_rede_e_nao_bloqueio(cenario):
    cenario.vip = httpx.ReadTimeout
    cenario.varrer()
    assert cenario.banco().execute("SELECT veredito FROM execucao_busca").fetchone()[0] == "falha_rede"
