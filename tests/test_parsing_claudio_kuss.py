"""Parser do Claudio Kuss (feature 002; interfaces/claudio-kuss.md; roadmap D-38, D-41 a D-46, D-50, D-52)."""

import logging
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from apoio import (FIXTURES_KUSS, agenda_kuss, agenda_sem_blocos, agenda_sem_financeiras, bytes_json, detalhe_kuss,
                   lote, lote_kuss)
from bot_leilao.coleta.modelos import Pagina, RespostaBruta, Veredito
from bot_leilao.parsing.claudio_kuss import ParserClaudioKuss
from bot_leilao.parsing.modelos import ContextoParsing
from bot_leilao.parsing.nucleo import obter_parser, processar

BASE = "https://www.claudiokussleiloes.com.br"
BRASILIA = timezone(timedelta(hours=-3))
PREGAO = datetime(2026, 10, 13, 10, 0, tzinfo=BRASILIA)
COLETADO = datetime(2026, 10, 10, 11, 0, tzinfo=timezone.utc)
CTX = ContextoParsing(leiloeiro_id="claudio-kuss-leiloes", busca_id="claudio-kuss-leiloes:abc", base_url=BASE,
                      coletado_em=COLETADO, tipo_leilao="financiamento")
AGENDA = {"tipo": "agenda", "categoria": "Veículos - Financeiras"}
LOTES = {"tipo": "lotes", "evento": "897", "pregao_em": PREGAO}
SINISTRADO = "SINISTRADO - NOS DOCUMENTOS CONSTA RECUPERADO DE SINISTRO. REGULARIZAÇÃO POR CONTA DO ARREMATANTE"

parser = ParserClaudioKuss()


def _ctx(pagina):
    return replace(CTX, pagina=pagina)


def _lotes(itens):
    return parser.extrair(bytes_json(itens), _ctx(LOTES)).lotes


def _fixture(nome):
    return (FIXTURES_KUSS / nome).read_bytes()


def test_registrado_e_sem_preco_obrigatorio():
    assert isinstance(obter_parser("claudio-kuss-leiloes"), ParserClaudioKuss)
    assert ParserClaudioKuss.preco_obrigatorio is False


# --- Agenda e quantidade (D-41) -------------------------------------------------------------

def test_agenda_reconhecida_e_sempre_vazia():
    """A agenda nunca traz lotes; quem distingue vazio de quebra é a página de quantidade de cada evento."""
    extracao = parser.extrair(agenda_kuss(), _ctx(AGENDA))
    assert (extracao.lotes, extracao.busca_vazia) == ([], True)


def test_agenda_so_com_outras_categorias_e_busca_vazia_legitima():
    extracao = parser.extrair(agenda_sem_financeiras(), _ctx(AGENDA))
    assert (extracao.lotes, extracao.busca_vazia) == ([], True)


def test_agenda_sem_nenhum_bloco_nao_e_vazia():
    """Layout novo da agenda não pode virar silêncio: o núcleo acusa quebra."""
    assert parser.extrair(agenda_sem_blocos(), _ctx(AGENDA)).busca_vazia is False


@pytest.mark.parametrize("corpo, vazia, total", [
    ({"qtde": 0, "qtdePag": 0}, True, 0),
    ({"qtde": 346, "qtdePag": 35}, False, 346),
    ({"qtde": "45", "qtdePag": "5"}, False, 45),
])
def test_quantidade(corpo, vazia, total):
    extracao = parser.extrair(bytes_json(corpo), _ctx({"tipo": "quantidade", "evento": "897", "pregao_em": PREGAO}))
    assert (extracao.lotes, extracao.busca_vazia, extracao.total_informado) == ([], vazia, total)


def _resposta(*paginas):
    return RespostaBruta(busca_id=CTX.busca_id, leiloeiro_id=CTX.leiloeiro_id, iniciado_em=COLETADO, duracao_ms=1,
                         status_http=200, veredito=Veredito.OK,
                         paginas=[Pagina(numero=i + 1, metodo="GET", url=BASE, conteudo=c, anotacoes=a)
                                  for i, (c, a) in enumerate(paginas)])


def test_no_nucleo_agenda_sem_financeiras_nao_e_quebra():
    resultado = processar(_resposta((agenda_sem_financeiras(), AGENDA)), CTX)
    assert (resultado.lotes, resultado.quebra_suspeita) == ([], False)


def test_no_nucleo_agenda_sem_blocos_e_quebra():
    assert processar(_resposta((agenda_sem_blocos(), AGENDA)), CTX).quebra_suspeita is True


def test_no_nucleo_eventos_da_categoria_sem_lotes_nao_e_quebra():
    quantidade = {"tipo": "quantidade", "evento": "897", "pregao_em": PREGAO}
    resultado = processar(_resposta((agenda_kuss(), AGENDA), (bytes_json({"qtde": 0, "qtdePag": 0}), quantidade)), CTX)
    assert (resultado.lotes, resultado.quebra_suspeita) == ([], False)


def test_no_nucleo_evento_com_lotes_informados_e_nenhum_lido_e_quebra():
    quantidade = {"tipo": "quantidade", "evento": "897", "pregao_em": PREGAO}
    resultado = processar(_resposta((agenda_kuss(), AGENDA), (bytes_json({"qtde": 2, "qtdePag": 1}), quantidade),
                                    (b"[]", LOTES)), CTX)
    assert resultado.quebra_suspeita is True


def test_no_nucleo_lotes_sem_preco_nao_sao_quebra():
    quantidade = {"tipo": "quantidade", "evento": "897", "pregao_em": PREGAO}
    resultado = processar(_resposta((agenda_kuss(), AGENDA), (bytes_json({"qtde": 2, "qtdePag": 1}), quantidade),
                                    (_fixture("lotes_897_fluence.json"), LOTES)), CTX)
    assert (len(resultado.lotes), resultado.quebra_suspeita) == (2, False)


# --- Lotes (D-38, D-42 a D-45) --------------------------------------------------------------

def test_fluence_real_com_todos_os_campos():
    extracao = parser.extrair(_fixture("lotes_897_fluence.json"), _ctx(LOTES))
    fluence, _ = extracao.lotes
    assert extracao.busca_vazia is False
    assert fluence.id_canonico == "claudio-kuss-leiloes:282622"
    assert fluence.link == f"{BASE}/lance/897/0/282622"
    assert (fluence.leiloeiro_id, fluence.busca_id, fluence.coletado_em) == (CTX.leiloeiro_id, CTX.busca_id, COLETADO)
    assert fluence.titulo == "IMP RENAULT/FLUENCE DYN 20A"
    assert (fluence.marca, fluence.modelo) == ("renault", "fluence dyn 20a")
    assert (fluence.ano_fabricacao, fluence.ano_modelo) == (2013, 2013)
    assert (fluence.lance_corrente, fluence.lance_inicial, fluence.quilometragem) == (None, None, None)
    assert fluence.tipo_leilao == "financiamento"
    assert (fluence.evento_id, fluence.pregao_em) == ("897", PREGAO)
    assert fluence.numero_lote is None
    assert fluence.retirado is False


def test_segundo_fluence_real_manual():
    _, manual = parser.extrair(_fixture("lotes_897_fluence.json"), _ctx(LOTES)).lotes
    assert (manual.modelo, manual.ano_fabricacao, manual.ano_modelo) == ("fluence dyn 20m", 2014, 2015)


def test_lote_real_com_lance():
    (compass,) = parser.extrair(_fixture("lotes_897_com_lance.json"), _ctx(LOTES)).lotes
    assert compass.lance_corrente == Decimal("74000.00")
    assert (compass.marca, compass.modelo, compass.ano_modelo) == ("jeep", "compass long tf", 2022)


def test_ultima_pagina_real_do_evento_898():
    lotes = parser.extrair(_fixture("lotes_898_ultima_pagina.json"), _ctx({**LOTES, "evento": "898"})).lotes
    assert len(lotes) == 5
    assert lotes[0].link == f"{BASE}/lance/898/0/280879"
    assert lotes[0].marca == "volkswagen"


def test_sinonimo_e_valor():
    (onix,) = _lotes([lote_kuss(seq="282745", bem="CHEV/ONIX 10 MT LT1", ano="20/21", valor="21.600,00")])
    assert (onix.marca, onix.modelo, onix.ano_modelo, onix.lance_corrente) == (
        "chevrolet", "onix 10 mt lt1", 2021, Decimal("21600.00"))


def test_numero_do_lote_quando_loteado():
    (loteado,) = _lotes([lote_kuss(lote="119")])
    assert loteado.numero_lote == "119"


def test_retirado():
    (retirado,) = _lotes([lote_kuss(bem="RETIRADO")])
    assert retirado.retirado is True
    assert retirado.id_canonico == "claudio-kuss-leiloes:282622"


def test_sucata_nao_e_devolvida_e_vai_para_o_log(caplog):
    with caplog.at_level(logging.INFO, logger="bot_leilao"):
        lotes = _lotes([lote_kuss(seq="1", bem="SUCATA RENAULT/FLUENCE"), lote_kuss(seq="2", bem="SUCATA IMP RENAULT/X"),
                        lote_kuss(seq="3")])
    assert [l.id_canonico for l in lotes] == ["claudio-kuss-leiloes:3"]
    assert "2 lote(s) de sucata" in caplog.text


def test_ano_vazio_e_nao_veiculo():
    (painel,) = _lotes([lote_kuss(bem="MODULOS FOTOVOLTAICOS", ano="")])
    assert (painel.marca, painel.ano_fabricacao, painel.ano_modelo) == (None, None, None)
    assert painel.titulo == "MODULOS FOTOVOLTAICOS"


def test_pagina_alem_da_ultima_e_vazia():
    extracao = parser.extrair(_fixture("lotes_alem_da_ultima.json"), _ctx(LOTES))
    assert (extracao.lotes, extracao.busca_vazia) == ([], True)


@pytest.mark.parametrize("conteudo", [b"<html>erro</html>", b'{"seq": "1"}', bytes_json([{"seq": "1"}]),
                                      bytes_json([{"bem": "X/Y"}])])
def test_formato_inesperado_levanta(conteudo):
    with pytest.raises(Exception):
        parser.extrair(conteudo, _ctx(LOTES))


def test_tipo_de_pagina_desconhecido_levanta():
    with pytest.raises(ValueError):
        parser.extrair(b"[]", CTX)


def test_apelido_de_quem_deu_lance_nunca_e_lido():
    (lido,) = _lotes([{**lote_kuss(valor="30.000,00"), "usuario": "Fulano123"}])
    assert "Fulano123" not in repr(lido)


# --- Detalhe (D-50, D-52) -------------------------------------------------------------------

def _novo():
    return lote(id_canonico="claudio-kuss-leiloes:282622", leiloeiro_id="claudio-kuss-leiloes", evento_id="897")


def test_detalhe_real_sinistrado():
    alvo = _novo()
    parser.aplicar_detalhe(alvo, _fixture("detalhe_282622_sinistrado.json"))
    assert alvo.observacoes == SINISTRADO
    assert alvo.despesas_adm == Decimal("2750.00")
    assert (alvo.placa_parcial, alvo.local_documento) == ("F**-**35", "SÃO PAULO")
    assert (alvo.detalhe_lido, alvo.retirado) == (True, False)


def test_detalhe_real_mecanica_com_problemas():
    alvo = _novo()
    parser.aplicar_detalhe(alvo, _fixture("detalhe_282341.json"))
    assert alvo.observacoes == "MECÂNICA COM PROBLEMAS"
    assert (alvo.despesas_adm, alvo.local_documento) == (Decimal("2350.00"), "SANTA CATARINA")


def test_texto_padrao_de_todo_lote_nunca_entra_nas_observacoes():
    alvo = _novo()
    parser.aplicar_detalhe(alvo, bytes_json(detalhe_kuss(tblInformacoes="&nbsp;")))
    assert alvo.observacoes is None
    assert alvo.detalhe_lido is True


@pytest.mark.parametrize("campo", ["", "&nbsp;", "  "])
def test_campos_vazios_viram_nulo(campo):
    alvo = _novo()
    parser.aplicar_detalhe(alvo, bytes_json(detalhe_kuss(tblInformacoes=campo, tblDespAdm=campo, tblPlaca=campo,
                                                         tblTransf=campo)))
    assert (alvo.observacoes, alvo.despesas_adm, alvo.placa_parcial, alvo.local_documento) == (None,) * 4


def test_entidades_e_espacos_sao_limpos():
    alvo = _novo()
    parser.aplicar_detalhe(alvo, bytes_json(detalhe_kuss(tblInformacoes="PARA-CHOQUE &amp; FAROL\n  QUEBRADOS ")))
    assert alvo.observacoes == "PARA-CHOQUE & FAROL QUEBRADOS"


def test_detalhe_retirado():
    alvo = _novo()
    parser.aplicar_detalhe(alvo, bytes_json(detalhe_kuss(retirado="S")))
    assert alvo.retirado is True


def test_detalhe_invalido_levanta():
    with pytest.raises(Exception):
        parser.aplicar_detalhe(_novo(), b"<html>erro</html>")
