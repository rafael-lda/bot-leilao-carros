"""Coletor (coletor-lotes v1.1 RF-01, RF-05, RF-07, RF-12 a RF-15; RF-18 da feature)."""

import re

import httpx
import pytest

from bot_leilao.coleta.coletor import Coletor
from bot_leilao.coleta.http import ClienteHTTP
from bot_leilao.coleta.modelos import Requisicao, Veredito
from bot_leilao.config.leiloeiros import Busca, Leiloeiro

BASE = "https://leiloeiro.exemplo.com.br"


class AdaptadorFalso:
    """Busca por GET ?p=N; o conteúdo diz 'pagina N de M'."""

    leiloeiro_id = "falso"

    def __init__(self, explodir_em=None):
        self.preparacoes = 0
        self.explodir_em = explodir_em

    def preparar_sessao(self, cliente):
        self.preparacoes += 1
        return cliente.requisitar(Requisicao("GET", f"{BASE}/"))

    def montar_requisicao(self, filtros, pagina):
        if self.explodir_em and filtros.get("q") == self.explodir_em:
            raise RuntimeError("bug no adaptador")
        return Requisicao("GET", f"{BASE}/busca?q={filtros['q']}&p={pagina}")

    def tem_proxima_pagina(self, conteudo, pagina):
        atual, total = map(int, re.search(rb"pagina (\d+) de (\d+)", conteudo).groups())
        return atual < total

    def validar_filtros(self, filtros):
        pass

    def tipo_leilao_da_busca(self, filtros):
        return None


def _leiloeiro(*consultas, ativo=True):
    buscas = tuple(Busca(id=f"falso:{q}", leiloeiro_id="falso", descricao=q, filtros={"q": q}) for q in consultas)
    return Leiloeiro(id="falso", nome="Leiloeiro Falso", base_url=BASE, ativo=ativo, estrategia_acesso="publico",
                     credencial_env=None, nivel_coleta="script", frequencia="seg-qua-sex-08h", buscas=buscas)


def _site(paginas_por_busca, falhas=None):
    """Responde 'pagina N de M'; `falhas` mapeia (q, p) -> exceção ou status."""
    falhas = falhas or {}

    def responder(request):
        if request.url.path == "/":
            return httpx.Response(200, text="home")
        q, p = request.url.params["q"], int(request.url.params["p"])
        falha = falhas.get((q, p))
        if isinstance(falha, int):
            return httpx.Response(falha)
        if falha is not None:
            raise falha(f"falha simulada em {q}/{p}", request=request)
        return httpx.Response(200, text=f"<html>{q} pagina {p} de {paginas_por_busca[q]}</html>")

    return responder


def _coletor(transp, relogio, adaptador=None, **opcoes):
    cliente = ClienteHTTP(transp.transporte, relogio=relogio.agora, dormir=relogio.dormir)
    adaptador = adaptador or AdaptadorFalso()
    return Coletor(cliente, {"falso": adaptador}, relogio=relogio.agora, **opcoes), adaptador


def test_coleta_todas_as_paginas_de_uma_busca(roteiro, relogio):
    transp = roteiro(_site({"carros": 3}))
    coletor, _ = _coletor(transp, relogio)
    (resposta,) = coletor.coletar([_leiloeiro("carros")])
    assert resposta.veredito is Veredito.OK
    assert [p.numero for p in resposta.paginas] == [1, 2, 3]
    assert resposta.paginas[2].conteudo.endswith(b"pagina 3 de 3</html>")
    assert resposta.nivel_usado == "script"
    assert resposta.busca_id == "falso:carros"
    assert resposta.leiloeiro_id == "falso"
    assert resposta.status_http == 200


def test_paginas_espacadas_em_pelo_menos_5s(roteiro, relogio):
    """RF-18: 30 resultados em páginas de 12 → 3 requisições espaçadas."""
    instantes = []
    base = _site({"carros": 3})

    def responder(request):
        instantes.append(relogio.agora())
        return base(request)

    coletor, _ = _coletor(roteiro(responder), relogio)
    coletor.coletar([_leiloeiro("carros")])
    assert len(instantes) == 4, "preparação + 3 páginas"
    assert all(b - a >= 5.0 for a, b in zip(instantes, instantes[1:]))


def test_sessao_preparada_uma_vez_por_leiloeiro(roteiro, relogio):
    coletor, adaptador = _coletor(roteiro(_site({"a": 1, "b": 1})), relogio)
    respostas = coletor.coletar([_leiloeiro("a", "b")])
    assert adaptador.preparacoes == 1
    assert [r.veredito for r in respostas] == [Veredito.OK, Veredito.OK]


def test_falha_numa_pagina_intermediaria_derruba_a_busca_inteira(roteiro, relogio):
    """RF-15 (busca atômica): nenhuma página é entregue."""
    transp = roteiro(_site({"carros": 3}, falhas={("carros", 2): httpx.ReadTimeout}))
    coletor, _ = _coletor(transp, relogio)
    (resposta,) = coletor.coletar([_leiloeiro("carros")])
    assert resposta.veredito is Veredito.FALHA_REDE
    assert resposta.paginas == []
    assert resposta.motivo.startswith("pagina 2")
    assert "timeout" in resposta.motivo
    assert resposta.tentativas == 3


def test_bloqueio_numa_pagina_vira_veredito_da_busca(roteiro, relogio):
    transp = roteiro(_site({"carros": 2}, falhas={("carros", 1): 429}))
    coletor, _ = _coletor(transp, relogio)
    (resposta,) = coletor.coletar([_leiloeiro("carros")])
    assert resposta.veredito is Veredito.BLOQUEADO
    assert resposta.bloqueado is True


def test_falha_de_uma_busca_nao_impede_as_outras(roteiro, relogio):
    transp = roteiro(_site({"ruim": 1, "boa": 2}, falhas={("ruim", 1): httpx.ConnectError}))
    coletor, _ = _coletor(transp, relogio)
    ruim, boa = coletor.coletar([_leiloeiro("ruim", "boa")])
    assert ruim.veredito is Veredito.FALHA_REDE
    assert boa.veredito is Veredito.OK
    assert len(boa.paginas) == 2


def test_teto_de_paginas(roteiro, relogio):
    transp = roteiro(_site({"infinita": 999}))
    coletor, _ = _coletor(transp, relogio, teto_paginas=3)
    (resposta,) = coletor.coletar([_leiloeiro("infinita")])
    assert resposta.veredito is Veredito.FALHA_REDE
    assert resposta.motivo == "teto_paginas"
    assert resposta.paginas == []
    assert len([c for c in transp.chamadas if c.url.path == "/busca"]) == 3


def test_falha_na_preparacao_de_sessao_falha_todas_as_buscas_do_leiloeiro(roteiro, relogio):
    def responder(request):
        if request.url.path == "/":
            raise httpx.ConnectError("fora do ar", request=request)
        return httpx.Response(200, text="pagina 1 de 1")

    coletor, _ = _coletor(roteiro(responder), relogio)
    respostas = coletor.coletar([_leiloeiro("a", "b")])
    assert [r.veredito for r in respostas] == [Veredito.FALHA_REDE, Veredito.FALHA_REDE]
    assert all(r.motivo.startswith("preparacao_sessao") for r in respostas)


def test_excecao_do_adaptador_e_isolada(roteiro, relogio):
    coletor, _ = _coletor(roteiro(_site({"bug": 1, "boa": 1})), relogio, adaptador=AdaptadorFalso(explodir_em="bug"))
    bug, boa = coletor.coletar([_leiloeiro("bug", "boa")])
    assert bug.veredito is Veredito.FALHA_REDE
    assert bug.motivo.startswith("erro_interno")
    assert boa.veredito is Veredito.OK


def test_leiloeiro_inativo_nao_e_coletado(roteiro, relogio):
    transp = roteiro(_site({"a": 1}))
    coletor, _ = _coletor(transp, relogio)
    assert coletor.coletar([_leiloeiro("a", ativo=False)]) == []
    assert transp.chamadas == []


def test_registro_de_duracao_e_inicio(roteiro, relogio, agora):
    cliente = ClienteHTTP(roteiro(_site({"a": 2})).transporte, relogio=relogio.agora, dormir=relogio.dormir)
    coletor = Coletor(cliente, {"falso": AdaptadorFalso()}, relogio=relogio.agora, agora=agora)
    (resposta,) = coletor.coletar([_leiloeiro("a")])
    assert resposta.iniciado_em == agora()
    assert resposta.duracao_ms >= 5000, "inclui a espera entre as duas páginas"
