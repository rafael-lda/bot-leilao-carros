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
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from urllib.parse import urlsplit

import httpx

import bot_leilao.coleta.claudio_kuss  # noqa: F401 — registra o adaptador (feature 002)
import bot_leilao.coleta.copart  # noqa: F401 — registra o adaptador (feature 003)
import bot_leilao.coleta.freitas  # noqa: F401 — registra o adaptador (feature 004)
import bot_leilao.coleta.milan  # noqa: F401 — registra o adaptador (feature 005)
import bot_leilao.coleta.vip  # noqa: F401 — registra o adaptador
import bot_leilao.parsing.claudio_kuss  # noqa: F401 — registra o parser (feature 002)
import bot_leilao.parsing.copart  # noqa: F401 — registra o parser (feature 003)
import bot_leilao.parsing.freitas  # noqa: F401 — registra o parser (feature 004)
import bot_leilao.parsing.milan  # noqa: F401 — registra o parser (feature 005)
import bot_leilao.parsing.vip  # noqa: F401 — registra o parser
from bot_leilao.coleta import registro
from bot_leilao.coleta.apify import ClienteApify, Consumo
from bot_leilao.coleta.coletor import Coletor
from bot_leilao.coleta.enriquecimento import enriquecer
from bot_leilao.coleta.http import ClienteHTTP
from bot_leilao.coleta.modelos import Veredito
from bot_leilao.coleta.roteador import ClienteRoteado
from bot_leilao.config.ambiente import carregar_ambiente
from bot_leilao.config.arquivos import ConfiguracaoAusente, ErroConfiguracao
from bot_leilao.config.coerencia import verificar_coerencia
from bot_leilao.config.leiloeiros import carregar_leiloeiros
from bot_leilao.config.veiculos import carregar_veiculos
from bot_leilao.db.conexao import ErroBanco, conectar
from bot_leilao.db.eventos import RepositorioEventos
from bot_leilao.db.execucoes import RegistroBusca, RepositorioExecucoes
from bot_leilao.db.lotes import RepositorioLotes
from bot_leilao.db.migracoes import migrar
from bot_leilao.db.trava import Trava
from bot_leilao.logsetup import mascarar
from bot_leilao.filtro.fluxo import FluxoFiltragem
from bot_leilao.notificacao.alertas import AlertaPendente, processar_alertas
from bot_leilao.notificacao.digest import AlertaOperacional, item_de, montar_digest
from bot_leilao.notificacao.relatorio import (DadosRelatorio, LoteRelatorio, acrescentar_monitoramento,
                                             gravar_relatorio, lote_de)
from bot_leilao.notificacao.telegram import NotificadorTelegram
from bot_leilao.parsing import nucleo
from bot_leilao.parsing.modelos import ContextoParsing, ResultadoParsing

log = logging.getLogger(__name__)

PASTA_RELATORIOS = "1OUTPUT"  # emenda E001: um relatório Markdown por varredura real, fora do git
LISTA_MONITORAMENTO = "lotes-a-monitorar.md"  # emenda E002: lista acumulada, o bot só acrescenta
RUNBOOK_CERTIFICADO = "src/bot_leilao/coleta/certificados/LEIA-ME.md"
CODIGO_SAIDA = {"sucesso": 0, "sucesso_parcial": 0, "falha": 1, "recusada": 3}
ALERTA_GASTO_APIFY = 0.80   # feature 005 (RN-13, D-91): alerta quando o ciclo passa de 80% do limite
ID_ALERTA_APIFY = "apify"   # chave do limite de 1 alerta por dia para o alerta de gasto


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Dependencias:
    """Pontos de injeção para testes; os padrões são os de produção."""

    transporte_leiloeiros: httpx.BaseTransport | None = None
    transporte_telegram: httpx.BaseTransport | None = None
    transporte_apify: httpx.BaseTransport | None = None   # feature 005
    transporte_analise: httpx.BaseTransport | None = None  # feature 006: FIPE e mapas
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
        # Emenda E001 (relatório Markdown)
        self.novos: list[LoteRelatorio] = []
        self.semeados_lotes: list[LoteRelatorio] = []   # E001 da feature 002
        self.leiloeiros: list[tuple[str, str]] = []     # situação de cada leiloeiro; E001 da feature 003
        self.telegram: str | None = None
        self.semeados = 0
        self.em_semeadura = False

    def seguro(self, texto: str | None) -> str | None:
        return None if texto is None else mascarar(texto, self.segredos)


def varrer(raiz: Path, dry_run: bool = False, deps: Dependencias | None = None,
           sem_pagos: bool = False) -> ResultadoVarredura:
    """`sem_pagos`: pula os leiloeiros de nível pago (feature 005, D-100)."""
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
            _executar(raiz, dry_run, deps, fuso, con, repo_exec, execucao_id, estado, sem_pagos)
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
            if not dry_run:
                _gravar_relatorio(raiz, estado, inicio.astimezone(fuso), segundos)
        saida = estado.saida
        saida.veredito, saida.codigo_saida = estado.veredito, CODIGO_SAIDA[estado.veredito]
        saida.execucao_id, saida.motivo, saida.contagens = execucao_id, estado.motivo, estado.contagens
        return saida
    finally:
        trava.liberar()


def _gravar_relatorio(raiz: Path, estado: "_Execucao", inicio_local: datetime, segundos: float) -> None:
    """Emenda E001. Uma falha aqui fica no log e nunca derruba a varredura."""
    try:
        caminho = gravar_relatorio(raiz / PASTA_RELATORIOS, DadosRelatorio(
            inicio=inicio_local, duracao_s=segundos, veredito=estado.veredito, motivo=estado.motivo,
            novos=estado.novos, telegram=estado.seguro(estado.telegram), semeados=estado.semeados,
            em_semeadura=estado.em_semeadura, semeados_lotes=estado.semeados_lotes,
            leiloeiros=[(nome, estado.seguro(situacao)) for nome, situacao in estado.leiloeiros]))
        log.info("exec    | relatório gravado em %s", caminho)
    except Exception as erro:  # noqa: BLE001
        log.warning("exec    | não consegui gravar o relatório em %s: %s", raiz / PASTA_RELATORIOS, erro)
    # Avisados entram só com o Telegram confirmado; semeados entram sempre (E001 da feature 002).
    pendentes = (estado.novos if estado.telegram == "enviado" else []) + estado.semeados_lotes
    if not pendentes:
        return
    try:
        lista = raiz / PASTA_RELATORIOS / LISTA_MONITORAMENTO
        entraram = acrescentar_monitoramento(lista, pendentes)
        if entraram:
            log.info("exec    | %d lote(s) acrescentado(s) a %s", entraram, lista)
    except Exception as erro:  # noqa: BLE001
        log.warning("exec    | não consegui atualizar a lista de lotes a monitorar: %s", erro)


def _abrir_banco(dados: Path):
    con = conectar(dados / "bot-leilao.sqlite3")
    migrar(con)
    return con


class _ExemplosCriados(ErroConfiguracao):
    """Arquivo(s) de configuração ausente(s): exemplos criados, execução abortada."""


def _carregar_configuracao(raiz: Path, dry_run: bool, deps: Dependencias, selecionar):
    """`selecionar(ativos) -> (incluídos, pulados)`: o token do Apify só é exigido para pagos incluídos (D-90)."""
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
    incluidos, pulados = selecionar(leiloeiros.ativos)
    ambiente = carregar_ambiente(raiz, exigir_telegram=not dry_run, environ=deps.environ,
                                 exigir_apify=[l.nome for l in incluidos if l.nivel_coleta == "apify"])
    if deps.ao_carregar_segredos and ambiente.segredos:
        deps.ao_carregar_segredos(ambiente.segredos)
    return veiculos, leiloeiros, ambiente, incluidos, pulados


def _selecionar(ativos, sem_pagos: bool, repo_exec: RepositorioExecucoes, agora: datetime, fuso: tzinfo):
    """Leiloeiros desta varredura (feature 005): `--sem-pagos` (D-100) e `intervalo_horas` (D-101).

    Devolve (incluídos, pulados); `pulados` mapeia o id à linha da seção "Leiloeiros" do relatório.
    """
    incluidos, pulados = [], {}
    for leiloeiro in ativos:
        if sem_pagos and leiloeiro.pago:
            pulados[leiloeiro.id] = "não incluído nesta varredura (sem pagos)"
        elif leiloeiro.intervalo_horas and (ultima := repo_exec.ultima_coleta_ok(leiloeiro.id)) is not None \
                and agora - ultima < timedelta(hours=leiloeiro.intervalo_horas):
            proxima = (ultima + timedelta(hours=leiloeiro.intervalo_horas)).astimezone(fuso)
            pulados[leiloeiro.id] = (f"pulado pelo intervalo de {leiloeiro.intervalo_horas} h (próxima leitura a "
                                     f"partir de {proxima:%d/%m %H:%M})")
        else:
            incluidos.append(leiloeiro)
            continue
        log.info("config  | %s | %s", leiloeiro.nome, pulados[leiloeiro.id])
    return incluidos, pulados


def _executar(raiz: Path, dry_run: bool, deps: Dependencias, fuso: tzinfo, con, repo_exec: RepositorioExecucoes,
              execucao_id: str, estado: _Execucao, sem_pagos: bool = False) -> None:
    # Configuração: tudo validado antes da primeira requisição.
    try:
        veiculos, leiloeiros, ambiente, incluidos, pulados = _carregar_configuracao(
            raiz, dry_run, deps, lambda ativos: _selecionar(ativos, sem_pagos, repo_exec, deps.agora(), fuso))
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
    ordem = {l.id: l.nome for l in leiloeiros.ativos}
    if not veiculos.ativos or not incluidos:
        estado.leiloeiros = [(ordem[i], situacao) for i, situacao in pulados.items()]
        estado.veredito, estado.motivo = "sucesso", "nada_a_varrer"
        estado.saida = _resultado("sucesso")
        return

    # Coleta, parsing, filtragem e enriquecimento. Os clientes vivem até o detalhe dos lotes novos
    # (feature 002, D-48). Cada requisição sai pelo nível do leiloeiro (feature 005, D-87).
    cliente = ClienteHTTP(deps.transporte_leiloeiros, relogio=deps.relogio, dormir=deps.dormir)
    apify = None
    if any(l.nivel_coleta == "apify" for l in incluidos):
        apify = ClienteApify(ambiente.apify_token, deps.transporte_apify, relogio=deps.relogio, dormir=deps.dormir,
                             atores_por_host={urlsplit(l.base_url).hostname: l.apify_ator
                                              for l in incluidos if l.apify_ator})
    roteado = ClienteRoteado({"script": cliente, **({"apify": apify} if apify else {})})
    consumo = None
    try:
        respostas = Coletor(roteado, adaptadores, relogio=deps.relogio, agora=deps.agora).coletar(incluidos)
        parsings, aptas = _processar(respostas, incluidos, adaptadores)
        fluxo = FluxoFiltragem(RepositorioLotes(con))
        filtragem = fluxo.filtrar(list(parsings.values()), veiculos.ativos, aptas)
        log.info("filtro  | %d lotes vistos, %d retirados | %d candidatos | %d já conhecidos | %d novos",
                 filtragem.vistos, filtragem.descartados_retirados, filtragem.candidatos, filtragem.ja_conhecidos,
                 len(filtragem.novos))
        semeados_visiveis = _enriquecer(filtragem, roteado, adaptadores, detalhar_semeados=not dry_run,
                                        niveis={l.id: l.nivel_coleta for l in incluidos})
        if apify is not None:
            consumo = apify.consumo()
            log.info("coleta  | apify | %d página(s)%s", apify.execucoes,
                     f"; US$ {consumo.gasto_varredura:.2f} nesta varredura, ciclo US$ {consumo.gasto_ciclo:.2f} de "
                     f"{consumo.limite:.2f}" if consumo else "; consumo indisponível")
    finally:
        roteado.fechar()
    estado.contagens.update(filtragem.contagens())
    extras = _eventos_vistos(incluidos, respostas, filtragem, con, deps.agora(), dry_run)
    situacoes = dict(_situacao_leiloeiros(incluidos, respostas, parsings))
    for leiloeiro in incluidos:
        complementos = [texto for texto, _alerta in extras.get(leiloeiro.id, [])]
        if apify is not None and leiloeiro.nivel_coleta == "apify":
            complementos.append(_linha_consumo(apify.execucoes, consumo, fuso))
        if complementos:
            situacoes[leiloeiro.nome] = " · ".join([situacoes[leiloeiro.nome], *complementos])
    situacoes.update({ordem[i]: situacao for i, situacao in pulados.items()})
    estado.leiloeiros = [(nome, situacoes[nome]) for nome in ordem.values() if nome in situacoes]

    # Semeadura e digest.
    if filtragem.buscas_a_semear:
        log.info("filtro  | busca(s) em semeadura: %d candidato(s) %s como conhecido(s), nenhum digest",
                 len(filtragem.semeaveis), "seriam registrados (dry-run)" if dry_run else "registrado(s)")
    agora_local = deps.agora().astimezone(fuso)
    estado.saida = _resultado("sucesso", em_semeadura=bool(filtragem.buscas_a_semear),
                              candidatos=[f"{c.lote.titulo} — {c.lote.ano_modelo} — {c.lote.link}"
                                          for c in filtragem.novos + filtragem.semeaveis])
    nomes = {l.id: l.nome for l in leiloeiros.ativos}
    if not dry_run:
        fluxo.registrar_semeadura(filtragem, execucao_id, deps.agora())
        estado.semeados_lotes = [lote_de(c, nomes[c.lote.leiloeiro_id], origem="semeadura")
                                 for c in semeados_visiveis]
    estado.semeados, estado.em_semeadura = len(filtragem.semeaveis), bool(filtragem.buscas_a_semear)

    estado.novos = [lote_de(c, nomes[c.lote.leiloeiro_id]) for c in filtragem.novos]
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
                estado.telegram = "enviado"
                log.info("notif   | digest enviado: %d lote(s), %d mensagem(ns)", len(filtragem.novos), len(digest))
            else:
                envio_falhou = envio.erro
                estado.telegram = f"não enviado: {envio.erro}"
                log.error("notif   | digest não enviado; os lotes voltam na próxima execução: %s", envio.erro)

        # Alertas: quebra por leiloeiro e falha geral (EC-08 do agendador).
        pendentes = _alertas(incluidos, respostas, parsings, agora_local)
        pendentes += [AlertaPendente(leiloeiros=(lid,), alerta=AlertaOperacional(
                          executado_em=agora_local, leiloeiro=ordem[lid], mensagem=mensagem))
                      for lid, itens in extras.items() for _texto, mensagem in itens if mensagem]
        pendentes += _alerta_gasto(consumo, agora_local, fuso)
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
    if ID_ALERTA_APIFY in alertas.enviados_para:  # base do limite de 1 alerta de gasto por dia
        repo_exec.registrar_leiloeiro(execucao_id, ID_ALERTA_APIFY, alerta_enviado=True)
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


def _processar(respostas, leiloeiros, adaptadores) -> tuple[dict[str, ResultadoParsing], set[str]]:
    """Parsing de cada busca; `aptas` são as buscas coletadas e lidas sem sinal de quebra (D-20)."""
    buscas = {b.id: (l, b) for l in leiloeiros for b in l.buscas}
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
    return parsings, aptas


def _situacao_leiloeiros(leiloeiros, respostas, parsings) -> list[tuple[str, str]]:
    """Uma linha por leiloeiro para o relatório (E001 da feature 003): o veredito parcial passa a ter explicação."""
    situacoes = []
    for leiloeiro in leiloeiros:
        dele = [r for r in respostas if r.leiloeiro_id == leiloeiro.id]
        bloqueadas = [r.motivo or "bloqueado" for r in dele if r.veredito is Veredito.BLOQUEADO]
        falhas = [r.motivo or r.veredito.value for r in dele if r.veredito not in (Veredito.OK, Veredito.BLOQUEADO)]
        quebras = [parsings[r.busca_id].motivo_quebra or "quebra" for r in dele if parsings[r.busca_id].quebra_suspeita]
        if bloqueadas:
            situacao = f"bloqueado pelo site ({'; '.join(sorted(set(bloqueadas)))})"
        elif falhas:
            situacao = f"falha de acesso ({'; '.join(sorted(set(falhas)))})"
        elif quebras:
            situacao = f"o leitor não entendeu a página ({'; '.join(quebras)})"
        else:
            situacao = f"ok: {sum(len(parsings[r.busca_id].lotes) for r in dele)} lote(s) lido(s)"
        situacoes.append((leiloeiro.nome, situacao))
    return situacoes


def _enriquecer(filtragem, cliente, adaptadores, detalhar_semeados: bool, niveis=None) -> list:
    """Detalhe dos lotes novos (feature 002, D-48): retirados e sucata saem do aviso e entram na contagem.

    Os semeáveis também são detalhados (E001 da feature 002), só para os documentos: todos continuam
    registrados como conhecidos, mas retirados e sucata não aparecem. Devolve os semeados a mostrar.
    """
    parsers = nucleo.parsers()
    if filtragem.novos:
        resultado = enriquecer(filtragem.novos, cliente, adaptadores, parsers, niveis)
        filtragem.novos = resultado.novos
        filtragem.descartados_retirados += resultado.retirados
        filtragem.descartados_sem_casar += resultado.acima_do_teto  # feature 005 (D-98)
        _log_enriquecimento("novos", resultado)
    if not detalhar_semeados or not filtragem.semeaveis:
        return []
    semeados = enriquecer(filtragem.semeaveis, cliente, adaptadores, parsers, niveis)
    _log_enriquecimento("semeados", semeados)
    return semeados.novos


def _log_enriquecimento(quais: str, resultado) -> None:
    if resultado.detalhados or resultado.falhas:
        log.info("enriq   | %s: %d lote(s) detalhado(s), %d retirado(s), %d sucata(s), %d acima do teto, %d falha(s)",
                 quais, resultado.detalhados, resultado.retirados, resultado.sucatas, resultado.acima_do_teto,
                 resultado.falhas)


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
    # Bloqueio de um leiloeiro, com os outros funcionando (feature 003): antes ficava só no registro.
    bloqueios: dict[str, list[str]] = defaultdict(list)
    for resposta in respostas:
        if resposta.veredito is Veredito.BLOQUEADO:
            bloqueios[resposta.leiloeiro_id].append(resposta.motivo or "bloqueado")
    for leiloeiro_id, motivos in bloqueios.items():
        pendentes.append(AlertaPendente(
            leiloeiros=(leiloeiro_id,),
            alerta=AlertaOperacional(executado_em=agora_local, leiloeiro=nomes.get(leiloeiro_id, leiloeiro_id),
                                     mensagem=f"o site bloqueou o acesso do bot ({'; '.join(sorted(set(motivos)))}). "
                                              "Este leiloeiro ficou sem cobertura nesta varredura; os outros "
                                              "seguem normalmente.")))
    # Certificado inválido (feature 004, D-85): não se resolve sozinho; o alerta aponta o procedimento.
    certificados: dict[str, list[str]] = defaultdict(list)
    for resposta in respostas:
        if resposta.veredito is Veredito.FALHA_REDE and "certificado:" in (resposta.motivo or ""):
            certificados[resposta.leiloeiro_id].append(resposta.motivo)
    for leiloeiro_id, motivos in certificados.items():
        pendentes.append(AlertaPendente(
            leiloeiros=(leiloeiro_id,),
            alerta=AlertaOperacional(executado_em=agora_local, leiloeiro=nomes.get(leiloeiro_id, leiloeiro_id),
                                     mensagem=f"o certificado do site não pôde ser verificado ({'; '.join(sorted(set(motivos)))})"
                                              ". Por segurança a conexão não foi feita, e este leiloeiro ficou sem "
                                              f"cobertura. Como resolver: {RUNBOOK_CERTIFICADO}")))
    # Falhas do Apify (feature 005, D-103): a causa e o que fazer; o desafio não resolvido usa o alerta de bloqueio.
    apify: dict[str, set[str]] = defaultdict(set)
    for resposta in respostas:
        motivo = resposta.motivo or ""
        if resposta.veredito is not Veredito.BLOQUEADO and "apify:" in motivo:
            causa = motivo.split("apify:", 1)[1].strip()
            apify[resposta.leiloeiro_id].add(ORIENTACAO_APIFY.get(causa, f"falha no Apify ({causa})."))
    for leiloeiro_id, mensagens in apify.items():
        pendentes.append(AlertaPendente(
            leiloeiros=(leiloeiro_id,),
            alerta=AlertaOperacional(executado_em=agora_local, leiloeiro=nomes.get(leiloeiro_id, leiloeiro_id),
                                     mensagem=" ".join(sorted(mensagens)) + " Este leiloeiro ficou sem cobertura "
                                              "nesta varredura; os outros seguem normalmente.")))
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


# --- Feature 005: Apify e antecedência dos leilões ---------------------------------------------------

ORIENTACAO_APIFY = {
    "token inválido": "token do Apify inválido: confira o APIFY_TOKEN no .env (console.apify.com → Settings → "
                      "API & Integrations).",
    "cota esgotada": "cota do Apify esgotada: o leiloeiro volta quando o ciclo da conta renovar, ou depois de "
                     "pagar o excedente no console do Apify.",
    "tempo esgotado": "o Apify não terminou a página a tempo (tempo esgotado); costuma passar sozinho.",
    "plataforma indisponível": "plataforma do Apify indisponível; costuma passar sozinho. Se repetir por dias, veja "
                               "status.apify.com.",
    "sem resultado": "o Apify não devolveu a página (sem resultado).",
}


def _reais(valor: float) -> str:
    return f"{valor:.2f}".replace(".", ",")


def _linha_consumo(paginas: int, consumo: Consumo | None, fuso: tzinfo) -> str:
    """Linha do leiloeiro pago na seção "Leiloeiros" (D-91)."""
    if consumo is None:
        return f"Apify: {paginas} página(s); consumo indisponível"
    ciclo = f"ciclo US$ {_reais(consumo.gasto_ciclo)} de {_reais(consumo.limite)}"
    if consumo.fim_ciclo is not None:
        ciclo += f" até {consumo.fim_ciclo.astimezone(fuso):%d/%m}"
    return f"Apify: {paginas} página(s), US$ {_reais(consumo.gasto_varredura)} nesta varredura; {ciclo}"


def _alerta_gasto(consumo: Consumo | None, agora_local: datetime, fuso: tzinfo) -> list[AlertaPendente]:
    """RN-13: gasto do ciclo acima de 80% do limite da conta; 1 por dia (chave `apify`)."""
    if consumo is None or consumo.limite <= 0 or consumo.gasto_ciclo < ALERTA_GASTO_APIFY * consumo.limite:
        return []
    percentual = round(consumo.gasto_ciclo / consumo.limite * 100)
    fim = f" O ciclo renova depois de {consumo.fim_ciclo.astimezone(fuso):%d/%m}." if consumo.fim_ciclo else ""
    mensagem = (f"Apify: o gasto do ciclo chegou a US$ {_reais(consumo.gasto_ciclo)} de {_reais(consumo.limite)} "
                f"({percentual}%), acima de {round(ALERTA_GASTO_APIFY * 100)}% do limite.{fim} Para economizar: rode "
                "as varreduras manuais com varrer.bat (sem pagos) ou ponha intervalo_horas no leiloeiro pago.")
    return [AlertaPendente(leiloeiros=(ID_ALERTA_APIFY,),
                           alerta=AlertaOperacional(executado_em=agora_local, mensagem=mensagem))]


def _eventos_vistos(leiloeiros, respostas, filtragem, con, agora: datetime, dry_run: bool) -> dict:
    """D-102: grava a primeira vez que cada leilão (evento) aparece e devolve, por leiloeiro, os leilões novos.

    Retorno: id do leiloeiro → [(texto para a seção "Leiloeiros", mensagem de alerta ou None)]. Os leilões da
    semeadura ficam marcados e não contam. Em dry-run nada é gravado.
    """
    if dry_run:
        return {}
    repo = RepositorioEventos(con)
    por_id = {l.id: l for l in leiloeiros}
    semear = set(filtragem.buscas_a_semear)
    saida: dict[str, list] = defaultdict(list)
    for resposta in respostas:
        vistos: set[str] = set()
        for pagina in resposta.paginas:
            evento = pagina.anotacoes.get("evento")
            pregao = pagina.anotacoes.get("pregao_em")
            if not evento or evento in vistos or not isinstance(pregao, datetime):
                continue
            vistos.add(evento)
            na_semeadura = resposta.busca_id in semear
            if not repo.registrar(resposta.leiloeiro_id, str(evento), pagina.anotacoes.get("rotulo"), pregao, agora,
                                  na_semeadura=na_semeadura) or na_semeadura:
                continue
            visto = repo.obter(resposta.leiloeiro_id, str(evento))
            dias = visto.antecedencia_dias
            texto = f"leilão novo {evento}, visto {dias} dia(s) antes do pregão"
            leiloeiro = por_id[resposta.leiloeiro_id]
            alerta = None
            if leiloeiro.intervalo_horas and visto.antecedencia_horas < leiloeiro.intervalo_horas:
                alerta = (f"anunciou o leilão {evento} com {dias} dia(s) de antecedência, menos que o intervalo de "
                          f"{leiloeiro.intervalo_horas} h; considere baixar intervalo_horas em config/leiloeiros.yaml "
                          "para não perder leilão anunciado em cima da hora.")
            log.info("coleta  | %s | %s", leiloeiro.nome, texto)
            saida[resposta.leiloeiro_id].append((texto, alerta))
    return saida
