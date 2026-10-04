"""Cliente HTTP do coletor (RF-03, RF-04, RF-18 da feature; coletor-lotes v1.1; roadmap D-02, D-30)."""

import httpx
import pytest

from bot_leilao.coleta.http import CABECALHOS_NAVEGADOR, ClienteHTTP
from bot_leilao.coleta.modelos import Requisicao, Veredito

URL = "https://www.vipleiloes.com.br/pesquisa?handler=pesquisar"


def _cliente(roteiro_transp, relogio, **opcoes):
    return ClienteHTTP(roteiro_transp.transporte, relogio=relogio.agora, dormir=relogio.dormir, **opcoes)


def test_get_ok_devolve_conteudo(roteiro, relogio):
    transp = roteiro(lambda r: httpx.Response(200, text="<html>lotes</html>"))
    resultado = _cliente(transp, relogio).requisitar(Requisicao("GET", URL))
    assert resultado.ok
    assert resultado.veredito is Veredito.OK
    assert resultado.status_http == 200
    assert resultado.conteudo == b"<html>lotes</html>"
    assert resultado.tentativas == 1


def test_toda_requisicao_leva_cabecalho_de_navegador(roteiro, relogio):
    """D-30: nunca o padrão python-httpx."""
    transp = roteiro(lambda r: httpx.Response(200, text="ok"))
    cliente = _cliente(transp, relogio)
    cliente.requisitar(Requisicao("GET", URL))
    cliente.requisitar(Requisicao("POST", URL, dados={"a": "1"}, cabecalhos={"X-Requested-With": "XMLHttpRequest"}))
    for chamada in transp.chamadas:
        assert chamada.headers["User-Agent"] == CABECALHOS_NAVEGADOR["User-Agent"]
        assert "python-httpx" not in chamada.headers["User-Agent"]
        assert "Mozilla/5.0" in chamada.headers["User-Agent"]
        assert chamada.headers["Accept-Language"].startswith("pt-BR")
    assert transp.chamadas[1].headers["X-Requested-With"] == "XMLHttpRequest"


def test_post_envia_formulario(roteiro, relogio):
    transp = roteiro(lambda r: httpx.Response(200, text="ok"))
    _cliente(transp, relogio).requisitar(Requisicao("POST", URL, dados={"Filtro.Procedencia": "4", "Filtro.Monta": "1"}))
    chamada = transp.chamadas[0]
    assert chamada.method == "POST"
    assert chamada.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert chamada.content == b"Filtro.Procedencia=4&Filtro.Monta=1"


def test_cookies_persistem_na_sessao(roteiro, relogio):
    def responder(request):
        if request.url.path == "/":
            return httpx.Response(200, text="home", headers={"Set-Cookie": "__CBCanal=abc; Path=/"})
        return httpx.Response(200, text="busca")

    transp = roteiro(responder)
    cliente = _cliente(transp, relogio)
    cliente.requisitar(Requisicao("GET", "https://www.vipleiloes.com.br/"))
    cliente.requisitar(Requisicao("POST", URL, dados={}))
    assert "__CBCanal" in cliente.cookies
    assert "__CBCanal=abc" in transp.chamadas[1].headers["Cookie"]


def test_intervalo_minimo_de_5s_entre_requisicoes_ao_mesmo_host(roteiro, relogio):
    instantes = []

    def responder(request):
        instantes.append((request.url.host, relogio.agora()))
        return httpx.Response(200, text="ok")

    cliente = _cliente(roteiro(responder), relogio)
    cliente.requisitar(Requisicao("GET", URL))
    cliente.requisitar(Requisicao("GET", URL))
    cliente.requisitar(Requisicao("GET", "https://api.telegram.org/x"))
    (h1, t1), (h2, t2), (h3, t3) = instantes
    assert t2 - t1 >= 5.0
    assert t3 == t2, "outro host não espera"


def test_redirecionamento_em_laco_vira_falha_de_rede(roteiro, relogio):
    transp = roteiro(lambda r: httpx.Response(302, headers={"Location": URL}))
    resultado = _cliente(transp, relogio).requisitar(Requisicao("GET", URL))
    assert resultado.veredito is Veredito.FALHA_REDE
    assert resultado.motivo == "laco_redirecionamento"
    assert resultado.tentativas == 3
    assert len(transp.chamadas) > 3, "cada tentativa segue alguns redirecionamentos antes de desistir"


def test_tres_redirecionamentos_ainda_sao_aceitos(roteiro, relogio):
    def responder(request):
        passo = int(request.url.params.get("passo", "0"))
        if passo < 3:
            return httpx.Response(302, headers={"Location": f"https://www.vipleiloes.com.br/?passo={passo + 1}"})
        return httpx.Response(200, text="chegou")

    resultado = _cliente(roteiro(responder), relogio).requisitar(Requisicao("GET", "https://www.vipleiloes.com.br/"))
    assert resultado.ok
    assert resultado.url.endswith("passo=3")


def test_retry_com_espera_crescente_ate_dar_certo(roteiro, relogio):
    transp = roteiro([httpx.Response(500), httpx.Response(502), httpx.Response(200, text="ok")])
    resultado = _cliente(transp, relogio).requisitar(Requisicao("GET", URL))
    assert resultado.ok
    assert resultado.tentativas == 3
    esperas = [d for d in relogio.dormidas if d > 0]
    assert esperas == sorted(esperas) and esperas[0] < esperas[-1], "espera crescente"
    assert all(d >= 5.0 for d in esperas), "nunca abaixo do intervalo mínimo do host"


def test_timeout_esgota_tentativas_como_falha_de_rede(roteiro, relogio):
    transp = roteiro(lambda r: (_ for _ in ()).throw(httpx.ReadTimeout("lento", request=r)))
    resultado = _cliente(transp, relogio).requisitar(Requisicao("GET", URL))
    assert resultado.veredito is Veredito.FALHA_REDE
    assert resultado.motivo == "timeout"
    assert resultado.tentativas == 3
    assert resultado.status_http is None


def test_erro_de_conexao_cita_o_host(roteiro, relogio):
    transp = roteiro(lambda r: (_ for _ in ()).throw(httpx.ConnectError("sem rede", request=r)))
    resultado = _cliente(transp, relogio).requisitar(Requisicao("GET", URL))
    assert resultado.veredito is Veredito.FALHA_REDE
    assert resultado.motivo.startswith("conexao")
    assert "www.vipleiloes.com.br" in resultado.motivo


@pytest.mark.parametrize("status", [403, 429])
def test_403_e_429_sao_bloqueio_apos_3_tentativas(roteiro, relogio, status):
    """Cenário 8: bloqueio é distinto de falha de rede."""
    transp = roteiro(lambda r: httpx.Response(status))
    resultado = _cliente(transp, relogio).requisitar(Requisicao("GET", URL))
    assert resultado.veredito is Veredito.BLOQUEADO
    assert resultado.motivo == f"http_{status}"
    assert resultado.tentativas == 3
    assert len(transp.chamadas) == 3


def test_429_respeita_retry_after_com_teto(roteiro, relogio):
    transp = roteiro([httpx.Response(429, headers={"Retry-After": "30"}),
                      httpx.Response(429, headers={"Retry-After": "600"}),
                      httpx.Response(200, text="ok")])
    resultado = _cliente(transp, relogio).requisitar(Requisicao("GET", URL))
    assert resultado.ok
    assert 30.0 in relogio.dormidas
    assert 60.0 in relogio.dormidas, "Retry-After limitado a 60 s"
    assert 600.0 not in relogio.dormidas


def test_desafio_cloudflare_e_bloqueio(roteiro, relogio):
    transp = roteiro(lambda r: httpx.Response(503, text="<title>Just a moment...</title> cf-chl"))
    resultado = _cliente(transp, relogio).requisitar(Requisicao("GET", URL))
    assert resultado.veredito is Veredito.BLOQUEADO
    assert resultado.motivo == "desafio_antibot"


def test_404_e_falha_sem_retry(roteiro, relogio):
    transp = roteiro(lambda r: httpx.Response(404))
    resultado = _cliente(transp, relogio).requisitar(Requisicao("GET", URL))
    assert resultado.veredito is Veredito.FALHA_REDE
    assert resultado.motivo == "http_404"
    assert resultado.tentativas == 1


def test_200_vazio_e_falha_de_coleta(roteiro, relogio):
    """coletor-lotes EC-06."""
    resultado = _cliente(roteiro(lambda r: httpx.Response(200, content=b"")), relogio).requisitar(Requisicao("GET", URL))
    assert resultado.veredito is Veredito.FALHA_REDE
    assert resultado.motivo == "conteudo_vazio"
    assert resultado.tentativas == 1


def test_resposta_acima_do_limite_e_abortada(roteiro, relogio):
    """coletor-lotes EC-09 (limite reduzido para o teste)."""
    transp = roteiro(lambda r: httpx.Response(200, content=b"x" * 5000))
    resultado = _cliente(transp, relogio, limite_bytes=1000).requisitar(Requisicao("GET", URL))
    assert resultado.veredito is Veredito.FALHA_REDE
    assert resultado.motivo == "resposta_grande"
    assert resultado.conteudo is None
