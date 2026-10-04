"""Orquestrador da varredura (RF-12, RF-14, RF-15 da feature; roadmap D-21; interfaces/cli.md).

Ordem garantida: trava → banco → registro da execução → configuração → coleta → parsing →
filtragem → semeadura → digest → confirmação → alertas → fechamento do registro, este num `finally`.
"""

from __future__ import annotations

import logging
import time
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone, tzinfo
from pathlib import Path

import httpx

import bot_leilao.coleta.vip  # noqa: F401 — registra o adaptador
import bot_leilao.parsing.vip  # noqa: F401 — registra o parser
from bot_leilao.coleta import registro
from bot_leilao.coleta.coletor import Coletor
from bot_leilao.coleta.http import ClienteHTTP
from bot_leilao.coleta.modelos import Veredito
from bot_leilao.config.ambiente import carregar_ambiente
from bot_leilao.config.arquivos import ConfiguracaoAusente, ErroConfiguracao
from bot_leilao.config.coerencia import verificar_coerencia
from bot_leilao.config.leiloeiros import carregar_leiloeiros
from bot_leilao.config.veiculos import carregar_veiculos
from bot_leilao.db.conexao import ErroBanco, conectar
from bot_leilao.db.execucoes import RegistroBusca, RepositorioExecucoes
from bot_leilao.db.lotes import RepositorioLotes
from bot_leilao.db.migracoes import migrar
from bot_leilao.db.trava import Trava
from bot_leilao.logsetup import mascarar
from bot_leilao.filtro.fluxo import FluxoFiltragem
from bot_leilao.notificacao.alertas import AlertaPendente, processar_alertas
from bot_leilao.notificacao.digest import AlertaOperacional, item_de, montar_digest
from bot_leilao.notificacao.telegram import NotificadorTelegram
from bot_leilao.parsing import nucleo
from bot_leilao.parsing.modelos import ContextoParsing, ResultadoParsing

log = logging.getLogger(__name__)

CODIGO_SAIDA = {"sucesso": 0, "sucesso_parcial": 0, "falha": 1, "recusada": 3}


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Dependencias:
    """Pontos de injeção para testes; os padrões são os de produção."""

    transporte_leiloeiros: httpx.BaseTransport | None = None
    transporte_telegram: httpx.BaseTransport | None = None
    relogio: Callable[[], float] = time.monotonic
    dormir: Callable[[float], None] = time.sleep
    agora: Callable[[], datetime] = _agora_utc
    fuso: tzinfo | None = None                      # padrão: fuso local da máquina
    environ: Mapping[str, str] | None = None        # padrão: os.environ
    ao_carregar_segredos: Callable[[list[str]], None] | None = None


@dataclass
class ResultadoVarredura:
    veredito: str
    codigo_saida: int
    execucao_id: str | None = None
    motivo: str | None = None
    digest: list[str] = field(default_factory=list)
    alertas: list[str] = field(default_factory=list)
    candidatos: list[str] = field(default_factory=list)
    em_semeadura: bool = False
    contagens: dict[str, int] = field(default_factory=dict)


def _resultado(veredito: str, **campos) -> ResultadoVarredura:
    return ResultadoVarredura(veredito=veredito, codigo_saida=CODIGO_SAIDA[veredito], **campos)


class _Execucao:
    """Estado mutável de uma varredura, fechado no `finally`."""

    def __init__(self) -> None:
        self.veredito = "falha"
        self.motivo: str | None = "erro_interno"
        self.contagens: dict[str, int] = {}
        self.digest_enviado = False
        self.saida = _resultado("falha")
        self.segredos: list[str] = []      # RN-08: nada que vai para o banco pode conter um segredo

    def seguro(self, texto: str | None) -> str | None:
        return None if texto is None else mascarar(texto, self.segredos)


def varrer(raiz: Path, dry_run: bool = False, deps: Dependencias | None = None) -> ResultadoVarredura:
    deps = deps or Dependencias()
    fuso = deps.fuso or datetime.now().astimezone().tzinfo
    dados = raiz / "dados"
    inicio = deps.agora()

    trava = Trava(dados / "varredura.lock", agora=deps.agora)
    if not trava.adquirir():
        log.warning("exec    | outra varredura está em andamento; esta foi recusada")
        try:
            execucao_id = RepositorioExecucoes(_abrir_banco(dados)).registrar_recusa(inicio, "trava_ocupada")
        except ErroBanco:
            execucao_id = None
        return _resultado("recusada", execucao_id=execucao_id, motivo="trava_ocupada")
    if trava.orfa_liberada:
        log.warning("exec    | trava órfã de execução anterior foi liberada")

    try:
        try:
            con = _abrir_banco(dados)
        except ErroBanco as erro:
            log.error("exec    | execução abortada: banco inacessível (%s). Nada foi varrido.", erro)
            return _resultado("falha", motivo="banco_inacessivel")

        repo_exec = RepositorioExecucoes(con)
        modo = "dry_run" if dry_run else "normal"
        execucao_id = repo_exec.abrir(modo, inicio)
        estado = _Execucao()
        try:
            _executar(raiz, dry_run, deps, fuso, con, repo_exec, execucao_id, estado)
        except Exception as erro:  # noqa: BLE001 — a execução sempre é registrada (RNF-03 do agendador)
            log.exception("exec    | erro interno")
            estado.veredito, estado.motivo = "falha", f"erro_interno: {type(erro).__name__}: {erro}"[:300]
        finally:
            fim = deps.agora()
            estado.motivo = estado.seguro(estado.motivo)
            repo_exec.fechar(execucao_id, estado.veredito, fim, motivo=estado.motivo, contagens=estado.contagens,
                             digest_enviado=estado.digest_enviado)
            segundos = (fim - inicio).total_seconds()
            log.info("exec    | %s em %dm%02ds | registro %s%s", estado.veredito, segundos // 60, segundos % 60,
                     execucao_id[:8], f" | motivo: {estado.motivo}" if estado.motivo else "")
            con.close()
        saida = estado.saida
        saida.veredito, saida.codigo_saida = estado.veredito, CODIGO_SAIDA[estado.veredito]
        saida.execucao_id, saida.motivo, saida.contagens = execucao_id, estado.motivo, estado.contagens
        return saida
    finally:
        trava.liberar()


def _abrir_banco(dados: Path):
    con = conectar(dados / "bot-leilao.sqlite3")
    migrar(con)
    return con


class _ExemplosCriados(ErroConfiguracao):
    """Arquivo(s) de configuração ausente(s): exemplos criados, execução abortada."""


def _carregar_configuracao(raiz: Path, dry_run: bool, deps: Dependencias):
    config = raiz / "config"
    ausentes: list[ConfiguracaoAusente] = []
    veiculos = leiloeiros = None
    try:
        veiculos = carregar_veiculos(config / "veiculos-alvo.yaml")
    except ConfiguracaoAusente as erro:
        ausentes.append(erro)
    try:
        leiloeiros = carregar_leiloeiros(config / "leiloeiros.yaml", registro.adaptadores(), set(nucleo.parsers()))
    except ConfiguracaoAusente as erro:
        ausentes.append(erro)
    if ausentes:
        criados = ", ".join(str(e.caminho) for e in ausentes)
        raise _ExemplosCriados(f"Criei arquivo(s) de exemplo em {criados}. Edite-os, ative o que quiser monitorar "
                               "e rode de novo.")
    ambiente = carregar_ambiente(raiz, exigir_telegram=not dry_run, environ=deps.environ)
    if deps.ao_carregar_segredos and ambiente.segredos:
        deps.ao_carregar_segredos(ambiente.segredos)
    return veiculos, leiloeiros, ambiente


def _executar(raiz: Path, dry_run: bool, deps: Dependencias, fuso: tzinfo, con, repo_exec: RepositorioExecucoes,
              execucao_id: str, estado: _Execucao) -> None:
    # Configuração: tudo validado antes da primeira requisição.
    try:
        veiculos, leiloeiros, ambiente = _carregar_configuracao(raiz, dry_run, deps)
        estado.segredos = ambiente.segredos
    except ErroConfiguracao as erro:
        log.error("config  | %s", erro)
        tipo = "config_ausente" if isinstance(erro, _ExemplosCriados) else "config_invalida"
        estado.motivo = f"{tipo}: {erro}"[:300]
        return
    for aviso in veiculos.avisos + leiloeiros.avisos:
        log.warning("config  | %s", aviso)
    adaptadores = registro.adaptadores()
    for aviso in verificar_coerencia(veiculos.ativos, leiloeiros.ativos,
                                     lambda l, b: adaptadores[l.id].tipo_leilao_da_busca(b.filtros)):
        log.warning("config  | %s", aviso)
    n_buscas = sum(len(l.buscas) for l in leiloeiros.ativos)
    log.info("config  | %d veículo(s)-alvo ativo(s), %d leiloeiro(s) ativo(s), %d busca(s)",
             len(veiculos.ativos), len(leiloeiros.ativos), n_buscas)
    estado.contagens["alvos_ativos"] = len(veiculos.ativos)
    if not veiculos.ativos or not leiloeiros.ativos:
        estado.veredito, estado.motivo = "sucesso", "nada_a_varrer"
        estado.saida = _resultado("sucesso")
        return

    # Coleta e parsing.
    cliente = ClienteHTTP(deps.transporte_leiloeiros, relogio=deps.relogio, dormir=deps.dormir)
    try:
        respostas = Coletor(cliente, adaptadores, relogio=deps.relogio, agora=deps.agora).coletar(leiloeiros.ativos)
    finally:
        cliente.fechar()

    buscas = {b.id: (l, b) for l in leiloeiros.ativos for b in l.buscas}
    parsings: dict[str, ResultadoParsing] = {}
    for resposta in respostas:
        leiloeiro, busca = buscas[resposta.busca_id]
        contexto = ContextoParsing(leiloeiro_id=leiloeiro.id, busca_id=busca.id, base_url=leiloeiro.base_url,
                                   coletado_em=resposta.iniciado_em,
                                   tipo_leilao=adaptadores[leiloeiro.id].tipo_leilao_da_busca(busca.filtros))
        parsings[busca.id] = nucleo.processar(resposta, contexto)
    aptas = {r.busca_id for r in respostas
             if r.veredito is Veredito.OK and not parsings[r.busca_id].quebra_suspeita
             and not parsings[r.busca_id].sem_conteudo}

    # Filtragem, semeadura e digest.
    fluxo = FluxoFiltragem(RepositorioLotes(con))
    filtragem = fluxo.filtrar(list(parsings.values()), veiculos.ativos, aptas)
    estado.contagens.update(filtragem.contagens())
    log.info("filtro  | %d lotes vistos, %d retirados | %d candidatos | %d já conhecidos | %d novos",
             filtragem.vistos, filtragem.descartados_retirados, filtragem.candidatos, filtragem.ja_conhecidos,
             len(filtragem.novos))
    if filtragem.buscas_a_semear:
        log.info("filtro  | busca(s) em semeadura: %d candidato(s) %s como conhecido(s), nenhum digest",
                 len(filtragem.semeaveis), "seriam registrados (dry-run)" if dry_run else "registrado(s)")
    agora_local = deps.agora().astimezone(fuso)
    estado.saida = _resultado("sucesso", em_semeadura=bool(filtragem.buscas_a_semear),
                              candidatos=[f"{c.lote.titulo} — {c.lote.ano_modelo} — {c.lote.link}"
                                          for c in filtragem.novos + filtragem.semeaveis])
    if not dry_run:
        fluxo.registrar_semeadura(filtragem, execucao_id, deps.agora())

    nomes = {l.id: l.nome for l in leiloeiros.ativos}
    digest = montar_digest([item_de(c, nomes[c.lote.leiloeiro_id]) for c in filtragem.novos], agora_local)
    estado.saida.digest = digest
    notificador = None if dry_run else NotificadorTelegram(ambiente.telegram_token, ambiente.telegram_chat_id,
                                                           deps.transporte_telegram, dormir=deps.dormir)
    envio_falhou = None
    try:
        if digest and notificador is not None:
            envio = notificador.enviar(digest)
            if envio.ok:
                fluxo.confirmar_notificacao(filtragem.novos, deps.agora())
                estado.digest_enviado = True
                log.info("notif   | digest enviado: %d lote(s), %d mensagem(ns)", len(filtragem.novos), len(digest))
            else:
                envio_falhou = envio.erro
                log.error("notif   | digest não enviado; os lotes voltam na próxima execução: %s", envio.erro)

        # Alertas: quebra por leiloeiro e falha geral (EC-08 do agendador).
        pendentes = _alertas(leiloeiros.ativos, respostas, parsings, agora_local)
        desde = agora_local.replace(hour=0, minute=0, second=0, microsecond=0)
        alertas = processar_alertas(pendentes, repo_exec, notificador, desde, dry_run=dry_run)
        estado.saida.alertas = alertas.textos
    finally:
        if notificador is not None:
            notificador.fechar()

    # Registro por busca e por leiloeiro.
    novos_por_leiloeiro = Counter(c.lote.leiloeiro_id for c in filtragem.novos) if estado.digest_enviado else Counter()
    por_leiloeiro: dict[str, Counter] = defaultdict(Counter)
    for resposta in respostas:
        parsing = parsings[resposta.busca_id]
        repo_exec.registrar_busca(execucao_id, RegistroBusca(
            busca_id=resposta.busca_id, leiloeiro_id=resposta.leiloeiro_id, iniciado_em=resposta.iniciado_em,
            duracao_ms=resposta.duracao_ms, status_http=resposta.status_http, nivel_usado=resposta.nivel_usado,
            tentativas=resposta.tentativas, paginas=len(resposta.paginas), veredito=resposta.veredito.value,
            motivo=estado.seguro(resposta.motivo), lotes_extraidos=len(parsing.lotes),
            lotes_descartados_parser=parsing.descartados, quebra_suspeita=parsing.quebra_suspeita,
            motivo_quebra=estado.seguro(parsing.motivo_quebra)))
        contagem = por_leiloeiro[resposta.leiloeiro_id]
        contagem["ok" if resposta.veredito is Veredito.OK else
                 "bloqueadas" if resposta.veredito is Veredito.BLOQUEADO else "falhas"] += 1
        contagem["quebra"] += int(parsing.quebra_suspeita)
    for leiloeiro_id, contagem in por_leiloeiro.items():
        repo_exec.registrar_leiloeiro(
            execucao_id, leiloeiro_id, buscas_ok=contagem["ok"], buscas_bloqueadas=contagem["bloqueadas"],
            buscas_falhas=contagem["falhas"], lotes_novos=novos_por_leiloeiro[leiloeiro_id],
            quebra_suspeita=contagem["quebra"] > 0, alerta_enviado=leiloeiro_id in alertas.enviados_para)

    # Veredito.
    ok = sum(1 for r in respostas if r.veredito is Veredito.OK)
    if envio_falhou:
        estado.veredito, estado.motivo = "falha", f"envio_digest: {envio_falhou}"[:300]
    elif respostas and ok == 0:
        estado.veredito, estado.motivo = "falha", "nenhuma_busca_coletada"
    elif ok < len(respostas) or any(p.quebra_suspeita for p in parsings.values()):
        estado.veredito, estado.motivo = "sucesso_parcial", None
    else:
        estado.veredito, estado.motivo = "sucesso", None


def _alertas(leiloeiros, respostas, parsings, agora_local: datetime) -> list[AlertaPendente]:
    pendentes: list[AlertaPendente] = []
    if respostas and all(r.veredito is not Veredito.OK for r in respostas):
        motivos = sorted({r.motivo or r.veredito.value for r in respostas})
        pendentes.append(AlertaPendente(
            leiloeiros=tuple(sorted({r.leiloeiro_id for r in respostas})),
            alerta=AlertaOperacional(executado_em=agora_local, severidade="critico",
                                     mensagem=f"falha geral: nenhuma busca foi coletada nesta varredura "
                                              f"({'; '.join(motivos)[:300]}).")))
        return pendentes
    nomes = {l.id: l.nome for l in leiloeiros}
    quebras: dict[str, list[str]] = defaultdict(list)
    for parsing in parsings.values():
        if parsing.quebra_suspeita:
            quebras[parsing.leiloeiro_id].append(parsing.motivo_quebra or "motivo desconhecido")
    for leiloeiro_id, motivos in quebras.items():
        pendentes.append(AlertaPendente(
            leiloeiros=(leiloeiro_id,),
            alerta=AlertaOperacional(executado_em=agora_local, leiloeiro=nomes.get(leiloeiro_id, leiloeiro_id),
                                     mensagem=f"o parser não conseguiu ler a página ({'; '.join(motivos)}). "
                                              "O site provavelmente mudou de layout e este leiloeiro está sem "
                                              "cobertura até o parser ser consertado.")))
    return pendentes
