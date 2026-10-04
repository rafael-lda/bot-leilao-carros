"""RN-08 de ponta a ponta: o token do bot nunca aparece no log, no console ou no banco (roadmap §10, critério de pronto)."""

import httpx

from apoio import TOKEN_TESTE, pagina_vazia, pagina_vip
from bot_leilao.cli import principal


def _saidas(cenario, capsys) -> str:
    console = capsys.readouterr()
    arquivo = (cenario.raiz / "dados" / "logs" / "bot-leilao.log").read_text(encoding="utf-8")
    banco = "\n".join(str(tuple(r)) for tabela in ("execucao", "execucao_busca", "execucao_leiloeiro")
                      for r in cenario.banco().execute(f"SELECT * FROM {tabela}"))
    return "\n".join([console.out, console.err, arquivo, banco])


def _varrer(cenario):
    return principal(["varrer", "--raiz", str(cenario.raiz)], deps=cenario.deps)


def test_erro_de_conexao_com_a_url_do_bot_nao_vaza_o_token(cenario, capsys):
    """A mensagem da exceção do httpx contém a URL da API, que contém o token."""
    cenario.vip = pagina_vazia()
    _varrer(cenario)
    cenario.vip = pagina_vip()
    cenario.telegram = httpx.ConnectError
    assert _varrer(cenario) == 1
    saidas = _saidas(cenario, capsys)
    assert "envio_digest" in saidas
    assert TOKEN_TESTE not in saidas


def test_excecao_inesperada_com_o_token_e_mascarada_no_rastreamento(cenario, capsys, monkeypatch):
    from bot_leilao.filtro import fluxo

    def explodir(*_args, **_kwargs):
        raise RuntimeError(f"falha ao chamar https://api.telegram.org/bot{TOKEN_TESTE}/sendMessage")

    monkeypatch.setattr(fluxo.FluxoFiltragem, "filtrar", explodir)
    cenario.vip = pagina_vip()
    assert _varrer(cenario) == 1
    saidas = _saidas(cenario, capsys)
    assert "Traceback" in saidas
    assert "bot***/sendMessage" in saidas
    assert TOKEN_TESTE not in saidas


def test_execucao_completa_com_digest_nao_vaza_o_token(cenario, capsys):
    cenario.vip = pagina_vazia()
    _varrer(cenario)
    cenario.vip = pagina_vip()
    assert _varrer(cenario) == 0
    assert len(cenario.mensagens) == 1
    assert TOKEN_TESTE not in _saidas(cenario, capsys)


def test_token_invalido_nao_vaza(cenario, capsys):
    cenario.telegram = 401
    principal(["testar-telegram", "--raiz", str(cenario.raiz)], deps=cenario.deps)
    console = capsys.readouterr()
    arquivo = (cenario.raiz / "dados" / "logs" / "bot-leilao.log").read_text(encoding="utf-8")
    assert "token do bot inválido" in console.out + arquivo
    assert TOKEN_TESTE not in console.out + console.err + arquivo
