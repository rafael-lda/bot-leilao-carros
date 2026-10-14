"""Roteamento das requisições pelo nível de coleta (feature 005; roadmap D-87)."""

import pytest

from bot_leilao.coleta.coletor import Coletor
from bot_leilao.coleta.modelos import Requisicao, ResultadoHTTP, Veredito
from bot_leilao.coleta.roteador import ClienteRoteado
from bot_leilao.config.leiloeiros import Busca, Leiloeiro

BASE = "https://leiloeiro.exemplo.com.br"


class ClienteFalso:
    def __init__(self, nome):
        self.nome = nome
        self.recebidas: list[Requisicao] = []
        self.fechado = False
        self.cookies = {"de": nome}
        self.tentativas = 3

    def requisitar(self, requisicao):
        self.recebidas.append(requisicao)
        return ResultadoHTTP(veredito=Veredito.OK, status_http=200, conteudo=b"pagina 1 de 1", tentativas=1,
                             duracao_ms=1, url=requisicao.url)

    def fechar(self):
        self.fechado = True


class AdaptadorDeUmaPagina:
    leiloeiro_id = "falso"

    def preparar_sessao(self, cliente):
        return cliente.requisitar(Requisicao("GET", f"{BASE}/"))

    def montar_requisicao(self, filtros, pagina):
        return Requisicao("GET", f"{BASE}/busca?p={pagina}")

    def tem_proxima_pagina(self, conteudo, pagina):
        return False

    def validar_filtros(self, filtros):
        pass

    def tipo_leilao_da_busca(self, filtros):
        return None


def _leiloeiro(nivel):
    busca = Busca(id="falso:a", leiloeiro_id="falso", descricao="a", filtros={})
    return Leiloeiro(id="falso", nome="Leiloeiro Falso", base_url=BASE, ativo=True, estrategia_acesso="publico",
                     credencial_env=None, nivel_coleta=nivel, frequencia="seg-qua-sex-08h", buscas=(busca,))


def test_requisicao_nasce_no_nivel_script():
    assert Requisicao("GET", BASE).nivel == "script"


def test_roteador_entrega_cada_requisicao_ao_cliente_do_seu_nivel():
    script, apify = ClienteFalso("script"), ClienteFalso("apify")
    roteado = ClienteRoteado({"script": script, "apify": apify})
    roteado.requisitar(Requisicao("GET", f"{BASE}/a"))
    roteado.requisitar(Requisicao("GET", f"{BASE}/b", nivel="apify"))
    assert [r.url for r in script.recebidas] == [f"{BASE}/a"]
    assert [r.url for r in apify.recebidas] == [f"{BASE}/b"]


def test_nivel_sem_cliente_e_erro_claro():
    roteado = ClienteRoteado({"script": ClienteFalso("script")})
    with pytest.raises(ValueError, match="apify"):
        roteado.requisitar(Requisicao("GET", BASE, nivel="apify"))


def test_cookies_tentativas_e_fechamento():
    script, apify = ClienteFalso("script"), ClienteFalso("apify")
    roteado = ClienteRoteado({"script": script, "apify": apify})
    assert roteado.cookies == {"de": "script"}
    assert roteado.tentativas == 3
    roteado.fechar()
    assert script.fechado and apify.fechado


@pytest.mark.parametrize("nivel", ["script", "apify"])
def test_coletor_carimba_o_nivel_do_leiloeiro_na_busca_e_na_preparacao(nivel):
    script, apify = ClienteFalso("script"), ClienteFalso("apify")
    coletor = Coletor(ClienteRoteado({"script": script, "apify": apify}), {"falso": AdaptadorDeUmaPagina()})
    (resposta,) = coletor.coletar([_leiloeiro(nivel)])
    assert resposta.veredito is Veredito.OK
    assert resposta.nivel_usado == nivel
    usado, outro = (script, apify) if nivel == "script" else (apify, script)
    assert [r.url for r in usado.recebidas] == [f"{BASE}/", f"{BASE}/busca?p=1"]
    assert all(r.nivel == nivel for r in usado.recebidas)
    assert outro.recebidas == [], "nada do leiloeiro sai pelo outro nível"
