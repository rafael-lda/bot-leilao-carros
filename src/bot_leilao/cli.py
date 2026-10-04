"""Linha de comando `python -m bot_leilao` (interfaces/cli.md; RF-14 da feature; roadmap D-25)."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from bot_leilao import __version__
from bot_leilao.config.ambiente import carregar_ambiente
from bot_leilao.config.arquivos import ErroConfiguracao
from bot_leilao.logsetup import configurar_logs
from bot_leilao.notificacao.telegram import NotificadorTelegram
from bot_leilao.orquestrador import Dependencias, varrer

log = logging.getLogger("bot_leilao.cli")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m bot_leilao",
                                     description="Varre leilões de carros, filtra pelos veículos-alvo e avisa no Telegram.")
    parser.add_argument("--version", action="version", version=f"bot_leilao {__version__}")
    sub = parser.add_subparsers(dest="comando", required=True)

    varredura = sub.add_parser("varrer", help="executa a varredura completa uma vez")
    varredura.add_argument("--dry-run", action="store_true",
                           help="coleta de verdade, mas não envia nada ao Telegram nem grava lotes conhecidos")
    varredura.add_argument("--raiz", default=".", help="pasta com config/, dados/ e .env (padrão: a atual)")

    teste = sub.add_parser("testar-telegram", help="envia uma mensagem de teste ao Telegram")
    teste.add_argument("--raiz", default=".", help="pasta com o .env (padrão: a atual)")
    return parser


def _imprimir_dry_run(resultado) -> None:
    print("\n===== DRY-RUN: nada foi enviado ao Telegram =====")
    if resultado.em_semeadura:
        print("Busca em semeadura: numa execução real, os candidatos abaixo seriam registrados como conhecidos, "
              "sem digest.")
    print(f"Candidatos ({len(resultado.candidatos)}):")
    for candidato in resultado.candidatos:
        print(f"  - {candidato}")
    if resultado.digest:
        print("\nDigest que seria enviado:")
        for bloco in resultado.digest:
            print(bloco, end="\n\n")
    else:
        print("\nNenhum digest seria enviado.")
    for alerta in resultado.alertas:
        print(f"\nAlerta que seria enviado:\n{alerta}")


def principal(argv: Sequence[str] | None = None, deps: Dependencias | None = None) -> int:
    args = _parser().parse_args(argv)
    raiz = Path(args.raiz).resolve()
    filtro = configurar_logs(raiz / "dados" / "logs")

    if args.comando == "testar-telegram":
        try:
            ambiente = carregar_ambiente(raiz, environ=deps.environ if deps else None)
        except ErroConfiguracao as erro:
            log.error("config  | %s", erro)
            return 1
        filtro.adicionar(ambiente.segredos)
        notificador = NotificadorTelegram(ambiente.telegram_token, ambiente.telegram_chat_id,
                                          deps.transporte_telegram if deps else None)
        try:
            envio = notificador.testar()
        finally:
            notificador.fechar()
        if envio.ok:
            log.info("notif   | mensagem de teste enviada; confira o Telegram")
            return 0
        log.error("notif   | teste falhou: %s", envio.erro)
        return 1

    deps = deps or Dependencias()
    anterior = deps.ao_carregar_segredos

    def registrar_segredos(segredos: list[str]) -> None:
        filtro.adicionar(segredos)
        if anterior:
            anterior(segredos)

    deps.ao_carregar_segredos = registrar_segredos
    resultado = varrer(raiz, dry_run=args.dry_run, deps=deps)
    if args.dry_run:
        _imprimir_dry_run(resultado)
    return resultado.codigo_saida
