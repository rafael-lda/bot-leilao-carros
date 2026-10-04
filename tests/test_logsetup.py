"""RN-08: nenhum segredo em log, inclusive em rastreamento de exceção (roadmap D-26)."""

import io
import logging

from bot_leilao.logsetup import FiltroSegredos, configurar_logs, mascarar

TOKEN = "123456789:AAH-segredo-de-teste-com-tamanho-suficiente"


def _logger_com_buffer(filtro: FiltroSegredos) -> tuple[logging.Logger, io.StringIO]:
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    handler.addFilter(filtro)
    logger = logging.getLogger(f"teste.logsetup.{id(buffer)}")
    logger.handlers[:] = [handler]
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    return logger, buffer


def test_mascarar_troca_segredo_por_asteriscos():
    assert mascarar(f"url=/bot{TOKEN}/sendMessage", [TOKEN]) == "url=/bot***/sendMessage"


def test_mascarar_ignora_segredos_curtos_e_vazios():
    assert mascarar("abc def", ["", "ab"]) == "abc def"


def test_filtro_mascara_mensagem_e_argumentos():
    logger, buffer = _logger_com_buffer(FiltroSegredos([TOKEN]))
    logger.info("enviando com token %s", TOKEN)
    saida = buffer.getvalue()
    assert TOKEN not in saida
    assert "enviando com token ***" in saida


def test_filtro_mascara_rastreamento_de_excecao():
    logger, buffer = _logger_com_buffer(FiltroSegredos([TOKEN]))
    try:
        raise RuntimeError(f"falha ao chamar https://api.telegram.org/bot{TOKEN}/sendMessage")
    except RuntimeError:
        logger.exception("envio falhou")
    saida = buffer.getvalue()
    assert TOKEN not in saida
    assert "RuntimeError" in saida
    assert "bot***/sendMessage" in saida


def test_filtro_aceita_segredos_adicionados_depois():
    filtro = FiltroSegredos()
    logger, buffer = _logger_com_buffer(filtro)
    filtro.adicionar([TOKEN])
    logger.warning("token=%s", TOKEN)
    assert TOKEN not in buffer.getvalue()


def test_configurar_logs_grava_arquivo_mascarado(tmp_path):
    filtro = configurar_logs(tmp_path / "logs", segredos=[TOKEN])
    try:
        logging.getLogger("bot_leilao.teste").error("vazamento? %s", TOKEN)
        for handler in logging.getLogger("bot_leilao").handlers:
            handler.flush()
        conteudo = (tmp_path / "logs" / "bot-leilao.log").read_text(encoding="utf-8")
        assert "vazamento? ***" in conteudo
        assert TOKEN not in conteudo
        assert isinstance(filtro, FiltroSegredos)
    finally:
        for handler in list(logging.getLogger("bot_leilao").handlers):
            handler.close()
            logging.getLogger("bot_leilao").removeHandler(handler)
