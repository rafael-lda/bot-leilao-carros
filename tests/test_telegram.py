"""Envio ao Telegram (notificador-telegram RF-04, RF-05, RF-09, EC-01 a EC-07; interfaces/telegram-bot-api.md)."""

import json
import logging

import httpx

from bot_leilao.notificacao.telegram import NotificadorTelegram

TOKEN = "123456789:AAHsegredoDeTesteComTamanhoSuficiente_x"
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
OK = {"ok": True, "result": {"message_id": 1}}


def _notificador(transp, relogio, **opcoes):
    return NotificadorTelegram(TOKEN, 42, transp.transporte, dormir=relogio.dormir, **opcoes)


def _corpo(chamada):
    return json.loads(chamada.content)


def test_envia_blocos_em_ordem_com_os_parametros_do_contrato(roteiro, relogio):
    transp = roteiro(lambda r: httpx.Response(200, json=OK))
    resultado = _notificador(transp, relogio).enviar(["bloco 1", "bloco 2"])
    assert resultado.ok is True
    assert resultado.blocos_enviados == 2
    assert [str(c.url) for c in transp.chamadas] == [URL, URL]
    corpo = _corpo(transp.chamadas[0])
    assert corpo == {"chat_id": 42, "text": "bloco 1", "parse_mode": "HTML", "link_preview_options": {"is_disabled": True}}
    assert _corpo(transp.chamadas[1])["text"] == "bloco 2"
    assert 1.0 in relogio.dormidas, "espera de 1 s entre blocos do mesmo digest"


def test_sem_blocos_nada_e_enviado(roteiro, relogio):
    transp = roteiro(lambda r: httpx.Response(200, json=OK))
    resultado = _notificador(transp, relogio).enviar([])
    assert resultado.ok is True
    assert transp.chamadas == []


def test_so_ok_true_confirma(roteiro, relogio):
    """RNF-02: confirmação só após aceite da plataforma."""
    transp = roteiro(lambda r: httpx.Response(200, json={"ok": False, "description": "algo"}))
    assert _notificador(transp, relogio).enviar(["x"]).ok is False


def test_retry_com_espera_crescente(roteiro, relogio):
    """RF-09."""
    transp = roteiro([httpx.Response(500), httpx.Response(502), httpx.Response(200, json=OK)])
    resultado = _notificador(transp, relogio).enviar(["x"])
    assert resultado.ok is True
    assert relogio.dormidas[:2] == [2.0, 4.0]


def test_timeout_esgota_tres_tentativas(roteiro, relogio):
    transp = roteiro(lambda r: (_ for _ in ()).throw(httpx.ReadTimeout("lento", request=r)))
    resultado = _notificador(transp, relogio).enviar(["x"])
    assert resultado.ok is False
    assert resultado.definitivo is False
    assert len(transp.chamadas) == 3
    assert "timeout" in resultado.erro


def test_429_respeita_retry_after(roteiro, relogio):
    """EC-05."""
    transp = roteiro([httpx.Response(429, json={"ok": False, "parameters": {"retry_after": 7}}),
                      httpx.Response(200, json=OK)])
    assert _notificador(transp, relogio).enviar(["x"]).ok is True
    assert 7.0 in relogio.dormidas


def test_401_token_invalido_sem_retry(roteiro, relogio):
    """EC-02: distinto de indisponibilidade, sem laço."""
    transp = roteiro(lambda r: httpx.Response(401, json={"ok": False, "description": "Unauthorized"}))
    resultado = _notificador(transp, relogio).enviar(["x"])
    assert (resultado.ok, resultado.definitivo) == (False, True)
    assert len(transp.chamadas) == 1
    assert "token" in resultado.erro.lower()
    assert TOKEN not in resultado.erro


def test_400_chat_nao_encontrado_sem_retry(roteiro, relogio):
    """EC-03."""
    transp = roteiro(lambda r: httpx.Response(400, json={"ok": False, "description": "Bad Request: chat not found"}))
    resultado = _notificador(transp, relogio).enviar(["x"])
    assert resultado.definitivo is True
    assert "chat not found" in resultado.erro
    assert "42" in resultado.erro, "cita o destino configurado"


def test_403_bot_bloqueado(roteiro, relogio):
    transp = roteiro(lambda r: httpx.Response(403, json={"ok": False, "description": "Forbidden: bot was blocked by the user"}))
    resultado = _notificador(transp, relogio).enviar(["x"])
    assert resultado.definitivo is True
    assert "bloque" in resultado.erro.lower()


def test_falha_no_meio_nao_confirma(roteiro, relogio):
    """EC-07: o primeiro bloco foi, o segundo não; nada é confirmado."""
    transp = roteiro([httpx.Response(200, json=OK)] + [httpx.Response(500)] * 3)
    resultado = _notificador(transp, relogio).enviar(["1", "2"])
    assert resultado.ok is False
    assert resultado.blocos_enviados == 1


def test_token_nunca_aparece_em_erro_nem_em_log(roteiro, relogio, caplog):
    """RN-08: a mensagem de exceção do httpx contém a URL, que contém o token."""
    def responder(request):
        raise httpx.ConnectError(f"falha ao conectar em {request.url}", request=request)

    with caplog.at_level(logging.DEBUG, logger="bot_leilao"):
        resultado = _notificador(roteiro(responder), relogio).enviar(["x"])
    assert resultado.ok is False
    assert TOKEN not in resultado.erro
    assert all(TOKEN not in r.getMessage() for r in caplog.records)


def test_testar_envia_uma_mensagem(roteiro, relogio):
    transp = roteiro(lambda r: httpx.Response(200, json=OK))
    assert _notificador(transp, relogio).testar().ok is True
    assert "teste" in _corpo(transp.chamadas[0])["text"].lower()
