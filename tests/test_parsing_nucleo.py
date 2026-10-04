"""Núcleo de parsing (parser-lotes RF-01, RF-07 a RF-11, EC-02, EC-06, EC-10, EC-15; RF-07 da feature; roadmap D-31)."""

from datetime import datetime, timezone

import pytest

from apoio import lote
from bot_leilao.coleta.modelos import Pagina, RespostaBruta, Veredito
from bot_leilao.parsing.modelos import ContextoParsing, ExtracaoPagina
from bot_leilao.parsing.nucleo import obter_parser, processar, registrar_parser

INSTANTE = datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc)
CTX = ContextoParsing(leiloeiro_id="falso", busca_id="falso:b1", base_url="https://x", coletado_em=INSTANTE,
                      tipo_leilao="financiamento")


class ParserRoteirizado:
    """Devolve, para cada página, a extração indicada em `por_pagina` (pelo conteúdo)."""

    def __init__(self, por_pagina):
        self.por_pagina = por_pagina

    def extrair(self, conteudo, contexto):
        item = self.por_pagina[conteudo]
        if isinstance(item, Exception):
            raise item
        return item


def _resposta(*conteudos, veredito=Veredito.OK):
    paginas = [Pagina(numero=i + 1, metodo="POST", url="https://x", conteudo=c) for i, c in enumerate(conteudos)]
    return RespostaBruta(busca_id="falso:b1", leiloeiro_id="falso", iniciado_em=INSTANTE, duracao_ms=10,
                         status_http=200, paginas=paginas, nivel_usado="script", tentativas=1, veredito=veredito)


def _lotes(n, inicio=0, **campos):
    return [lote(id_canonico=f"falso:{i}", link=f"https://x/{i}", **campos) for i in range(inicio, inicio + n)]


def test_registro_de_parsers_por_leiloeiro():
    parser = ParserRoteirizado({})
    registrar_parser("falso-registro", parser)
    assert obter_parser("falso-registro") is parser


def test_junta_lotes_de_todas_as_paginas():
    parser = ParserRoteirizado({b"p1": ExtracaoPagina(lotes=_lotes(12)), b"p2": ExtracaoPagina(lotes=_lotes(3, 12))})
    resultado = processar(_resposta(b"p1", b"p2"), CTX, parser)
    assert len(resultado.lotes) == 15
    assert resultado.quebra_suspeita is False
    assert resultado.descartados == 0
    assert resultado.tamanho_conteudo == 4
    assert (resultado.busca_id, resultado.leiloeiro_id) == ("falso:b1", "falso")


def test_conteudo_nao_vazio_sem_lotes_e_quebra():
    """RF-07: layout mudou."""
    parser = ParserRoteirizado({b"x" * 2048: ExtracaoPagina(lotes=[])})
    resultado = processar(_resposta(b"x" * 2048), CTX, parser)
    assert resultado.quebra_suspeita is True
    assert resultado.lotes == []
    assert "KB" in resultado.motivo_quebra


def test_busca_vazia_declarada_pelo_site_nao_e_quebra():
    """D-31 / EC-15: 'Nenhum lote encontrado.' é resultado legítimo."""
    parser = ParserRoteirizado({b"vazia": ExtracaoPagina(lotes=[], busca_vazia=True)})
    resultado = processar(_resposta(b"vazia"), CTX, parser)
    assert resultado.quebra_suspeita is False
    assert resultado.lotes == []


@pytest.mark.parametrize("incompletos, quebra", [(3, False), (4, True)])
def test_mais_de_30_por_cento_incompletos_e_quebra(incompletos, quebra):
    """RF-08: 'mais de 30%' — 3 de 10 não é, 4 de 10 é."""
    lotes = _lotes(10 - incompletos) + _lotes(incompletos, 100, lance_inicial=None, lance_corrente=None)
    resultado = processar(_resposta(b"p"), CTX, ParserRoteirizado({b"p": ExtracaoPagina(lotes=lotes)}))
    assert resultado.quebra_suspeita is quebra
    assert len(resultado.lotes) == 10, "lote incompleto não é descartado, só contado"


@pytest.mark.parametrize("campo", ["marca", "modelo", "ano_modelo"])
def test_campos_obrigatorios_contam_como_incompleto(campo):
    lotes = _lotes(5, **{campo: None})
    resultado = processar(_resposta(b"p"), CTX, ParserRoteirizado({b"p": ExtracaoPagina(lotes=lotes)}))
    assert resultado.quebra_suspeita is True


def test_lote_sem_link_ou_id_e_descartado_e_contado():
    lotes = _lotes(3) + [lote(id_canonico="falso:x", link=None), lote(id_canonico=None, link="https://x/y")]
    resultado = processar(_resposta(b"p"), CTX, ParserRoteirizado({b"p": ExtracaoPagina(lotes=lotes)}))
    assert len(resultado.lotes) == 3
    assert resultado.descartados == 2


def test_lote_repetido_na_mesma_busca_fica_uma_vez():
    parser = ParserRoteirizado({b"p1": ExtracaoPagina(lotes=_lotes(2)), b"p2": ExtracaoPagina(lotes=_lotes(2))})
    resultado = processar(_resposta(b"p1", b"p2"), CTX, parser)
    assert [l.id_canonico for l in resultado.lotes] == ["falso:0", "falso:1"]


def test_excecao_no_parser_e_isolada_e_vira_quebra():
    """RF-10 / EC-02."""
    parser = ParserRoteirizado({b"p": ValueError("estrutura inesperada")})
    resultado = processar(_resposta(b"p"), CTX, parser)
    assert resultado.quebra_suspeita is True
    assert "estrutura inesperada" in resultado.motivo_quebra
    assert resultado.lotes == []


def test_conteudo_vazio_nao_e_quebra_de_parser():
    """EC-10: atribuído ao coletor, sem falso alarme."""
    resultado = processar(_resposta(b""), CTX, ParserRoteirizado({b"": ExtracaoPagina(lotes=[])}))
    assert resultado.sem_conteudo is True
    assert resultado.quebra_suspeita is False


def test_coleta_sem_sucesso_nao_e_processada():
    resultado = processar(_resposta(veredito=Veredito.FALHA_REDE), CTX, ParserRoteirizado({}))
    assert resultado.lotes == []
    assert resultado.quebra_suspeita is False


def test_usa_o_parser_registrado_quando_nao_informado():
    registrar_parser("falso", ParserRoteirizado({b"p": ExtracaoPagina(lotes=_lotes(1))}))
    assert len(processar(_resposta(b"p"), CTX).lotes) == 1
