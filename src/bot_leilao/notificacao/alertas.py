"""Alertas operacionais com limite de 1 por dia por leiloeiro (RF-11; notificador-telegram RF-08, EC-10; roadmap D-22)."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

from bot_leilao.db.execucoes import RepositorioExecucoes
from bot_leilao.notificacao.digest import AlertaOperacional, montar_alerta
from bot_leilao.notificacao.telegram import NotificadorTelegram

log = logging.getLogger(__name__)


@dataclass
class AlertaPendente:
    """Alerta a enviar. `leiloeiros`: ids cujo limite diário o alerta consome (vários no alerta de falha geral)."""

    leiloeiros: tuple[str, ...]
    alerta: AlertaOperacional


@dataclass
class ResultadoAlertas:
    textos: list[str] = field(default_factory=list)            # o que foi (ou, em dry-run, seria) enviado
    enviados_para: set[str] = field(default_factory=set)       # leiloeiros com alerta enviado nesta execução
    suprimidos: int = 0
    falhas: int = 0


def processar_alertas(
    pendentes: Sequence[AlertaPendente],
    repo: RepositorioExecucoes,
    notificador: NotificadorTelegram | None,
    desde: datetime,
    dry_run: bool = False,
) -> ResultadoAlertas:
    """`desde`: início do dia local, em qualquer fuso. Em dry-run nada é enviado nem consome o limite."""
    resultado = ResultadoAlertas()
    for pendente in pendentes:
        if not dry_run and all(repo.alerta_enviado_desde(lid, desde) for lid in pendente.leiloeiros):
            resultado.suprimidos += 1
            log.info("notif   | alerta suprimido (já enviado hoje): %s", pendente.alerta.mensagem)
            continue
        texto = montar_alerta(pendente.alerta)
        resultado.textos.append(texto)
        if dry_run or notificador is None:
            continue
        envio = notificador.enviar([texto])
        if envio.ok:
            resultado.enviados_para.update(pendente.leiloeiros)
            log.info("notif   | alerta enviado: %s", pendente.alerta.leiloeiro or "sistema")
        else:
            resultado.falhas += 1
            log.error("notif   | alerta não enviado (%s); fica só no log: %s", envio.erro, pendente.alerta.mensagem)
    return resultado
