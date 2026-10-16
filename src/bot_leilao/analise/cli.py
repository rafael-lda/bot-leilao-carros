"""Subcomandos `python -m bot_leilao analise …` (feature 006; interfaces/cli-analise.md; roadmap D-104, D-117).

Contrato com o roteiro da skill `analisar-lotes`: saída JSON em UTF-8 na saída padrão; código 0 (ok), 1 (erro, com
`{"erro": ...}`) ou 3 (varredura em andamento, nos subcomandos que escrevem). Os logs vão só para o arquivo.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from bot_leilao.analise.custos import ErroCustos, calcular, carregar_custos
from bot_leilao.analise.distancias import Distancias
from bot_leilao.analise.fipe import ErroFipe, Fipe
from bot_leilao.analise.lista import (CAMPOS_ANOTAVEIS, VEREDITOS, ErroLista, anotar_campo, anotar_custo, devolver,
                                     ler_lista, numero_por_link, triar)
from bot_leilao.analise.pagina import ErroPagina, ler_pagina
from bot_leilao.config.arquivos import ErroConfiguracao
from bot_leilao.db.trava import Trava

CODIGO_OK, CODIGO_ERRO, CODIGO_VARREDURA = 0, 1, 3
LISTA = Path("1OUTPUT") / "lotes-a-monitorar.md"


class _VarreduraEmAndamento(Exception):
    pass


def registrar(sub) -> None:
    analise = sub.add_parser("analise", help="análise dos lotes da lista (base da skill analisar-lotes)")
    comandos = analise.add_subparsers(dest="analise", required=True)

    def novo(nome: str, ajuda: str):
        parser = comandos.add_parser(nome, help=ajuda)
        parser.add_argument("--raiz", default=".", help="pasta com config/, dados/ e 1OUTPUT/ (padrão: a atual)")
        return parser

    lotes = novo("lotes", "lista os lotes com o alvo e os critérios")
    grupo = lotes.add_mutually_exclusive_group()
    grupo.add_argument("--numero", type=int)
    grupo.add_argument("--link")
    novo("pagina", "lê o lote pelo acesso do bot").add_argument("lote", help="número do bloco ou link do lote")
    t = novo("triar", "escreve o veredito da triagem (o reprovado vai para lotes-descartados.md; o encerrado fica, "
                      "com o resultado do pregão em --motivo)")
    t.add_argument("lote", help="número do bloco ou link do lote")
    t.add_argument("--veredito", required=True, choices=VEREDITOS)
    t.add_argument("--motivo")
    t.add_argument("--evidencia")
    t.add_argument("--falta")
    novo("devolver", "traz um lote descartado de volta para a lista").add_argument("numero", type=int)
    an = novo("anotar", "grava um campo do bloco (câmbio deduzido, resultado do pregão, lance atual, pregão)")
    an.add_argument("lote", help="número do bloco ou link do lote")
    an.add_argument("--campo", required=True, choices=CAMPOS_ANOTAVEIS)
    an.add_argument("--valor", required=True)
    fc = novo("fipe-candidatos", "versões FIPE de um ano cujo nome contém os termos")
    fc.add_argument("--marca", required=True)
    fc.add_argument("--modelo", required=True, help="termos do modelo, ex.: \"versa sl 1.6\"")
    fc.add_argument("--ano", required=True, type=int)
    fv = novo("fipe-valor", "valor de um código FIPE num ano de modelo")
    fv.add_argument("--codigo", required=True)
    fv.add_argument("--ano", required=True, type=int)
    c = novo("custo", "custo na garagem, %% da FIPE e lance máximo")
    c.add_argument("--lance", required=True, type=Decimal)
    c.add_argument("--despesa", type=Decimal)
    c.add_argument("--patio", required=True, help="\"Cidade - UF\", como no bloco")
    c.add_argument("--documento-uf")
    c.add_argument("--fipe", type=Decimal)
    c.add_argument("--reparos-extra", type=Decimal)
    c.add_argument("--motivo-reparos")
    a = novo("anotar-custo", "preenche FIPE e custo no bloco do lote")
    a.add_argument("lote", help="número do bloco ou link do lote")
    a.add_argument("--json", required=True, help="arquivo com {fipe, candidatas, custo}, ou - para a entrada padrão")


def _json(valor):
    if isinstance(valor, Decimal):
        return int(valor) if valor == valor.to_integral_value() else float(valor)
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    raise TypeError(f"não serializável: {type(valor).__name__}")


def _imprimir(dados: dict) -> None:
    sys.stdout.write(json.dumps(dados, ensure_ascii=False, default=_json) + "\n")
    sys.stdout.flush()


def _numero(lista: Path, referencia: str) -> int:
    return int(referencia) if str(referencia).isdigit() else numero_por_link(lista, referencia)


def _com_trava(raiz: Path, deps, acao):
    trava = Trava(raiz / "dados" / "varredura.lock", agora=deps.agora)
    if not trava.adquirir():
        raise _VarreduraEmAndamento()
    try:
        return acao()
    finally:
        trava.liberar()


def _alvos(raiz: Path) -> dict:
    from bot_leilao.config.veiculos import carregar_veiculos

    return {a.id: a for a in carregar_veiculos(raiz / "config" / "veiculos-alvo.yaml").ativos}


def _alvo_json(alvo) -> dict | None:
    if alvo is None:
        return None
    return {"id": alvo.id, "marca": alvo.marca, "modelo": alvo.modelo, "ano_min": alvo.ano_min, "ano_max": alvo.ano_max,
            "preco_maximo": alvo.preco_maximo, "quilometragem_maxima": alvo.quilometragem_maxima,
            "tipos_leilao": list(alvo.tipos_leilao), "excluir": list(alvo.excluir),
            "criterios": {"cambio": list(alvo.cambio) if alvo.cambio else None,
                          "aceitar_sinistro": alvo.aceitar_sinistro, "aceitar_sucata": alvo.aceitar_sucata,
                          "aceitar_mecanica_com_problema": alvo.aceitar_mecanica_com_problema,
                          "aceitar_pequenas_avarias": alvo.aceitar_pequenas_avarias},
            "triagem": alvo.triagem}


def _cliente(raiz: Path, deps):
    """Clientes da varredura (D-110): `script` sempre; `apify` quando houver token e leiloeiro em `apify`."""
    import bot_leilao.orquestrador  # noqa: F401 — registra todos os adaptadores e parsers
    from bot_leilao.coleta import registro
    from bot_leilao.coleta.apify import ClienteApify
    from bot_leilao.coleta.http import ClienteHTTP
    from bot_leilao.coleta.roteador import ClienteRoteado
    from bot_leilao.config.ambiente import carregar_ambiente
    from bot_leilao.config.leiloeiros import carregar_leiloeiros
    from bot_leilao.parsing import nucleo

    try:
        leiloeiros = carregar_leiloeiros(raiz / "config" / "leiloeiros.yaml", registro.adaptadores(),
                                         set(nucleo.parsers())).ativos
    except ErroConfiguracao:
        leiloeiros = []
    niveis = {l.id: l.nivel_coleta for l in leiloeiros}
    clientes = {"script": ClienteHTTP(deps.transporte_leiloeiros, relogio=deps.relogio, dormir=deps.dormir)}
    if "apify" in niveis.values():
        token = carregar_ambiente(raiz, exigir_telegram=False, environ=deps.environ).apify_token
        if token:
            clientes["apify"] = ClienteApify(token, deps.transporte_apify, relogio=deps.relogio, dormir=deps.dormir)
    return ClienteRoteado(clientes), niveis


def executar(args: argparse.Namespace, raiz: Path, deps) -> int:
    lista = raiz / LISTA
    try:
        _imprimir(_executar(args, raiz, deps, lista))
        return CODIGO_OK
    except _VarreduraEmAndamento:
        _imprimir({"erro": "varredura em andamento: nada foi escrito; rode de novo quando ela terminar"})
        return CODIGO_VARREDURA
    except (ErroLista, ErroCustos, ErroFipe, ErroPagina, ErroConfiguracao, ValueError, OSError) as erro:
        _imprimir({"erro": str(erro)})
        return CODIGO_ERRO


def _executar(args, raiz: Path, deps, lista: Path) -> dict:
    hoje = deps.agora().astimezone(deps.fuso or datetime.now().astimezone().tzinfo).date()
    comando = args.analise
    if comando == "lotes":
        blocos = ler_lista(lista)
        if args.numero is not None:
            blocos = [b for b in blocos if b.numero == args.numero] or _erro_lista(args.numero)
        elif args.link:
            numero = numero_por_link(lista, args.link)
            blocos = [b for b in blocos if b.numero == numero]
        alvos = _alvos(raiz)
        return {"lotes": [{"numero": b.numero, "id": b.id, "titulo": b.titulo, "ano": b.ano, "campos": b.campos,
                           "alvo": _alvo_json(alvos.get(b.campos.get("Alvo", "").split(" ")[0]))} for b in blocos]}
    if comando == "pagina":
        numero = _numero(lista, args.lote)
        bloco = next((b for b in ler_lista(lista) if b.numero == numero), None) or _erro_lista(numero)
        cliente, niveis = _cliente(raiz, deps)
        try:
            return {"numero": numero, **ler_pagina(bloco.id, bloco.campos.get("Link", ""), cliente, niveis)}
        finally:
            cliente.fechar()
    if comando == "triar":
        numero = _numero(lista, args.lote)
        destino = _com_trava(raiz, deps, lambda: triar(lista, numero, args.veredito, hoje=hoje, motivo=args.motivo,
                                                       evidencia=args.evidencia, falta=args.falta))
        return {"numero": numero, "veredito": args.veredito, "destino": destino}
    if comando == "anotar":
        numero = _numero(lista, args.lote)
        _com_trava(raiz, deps, lambda: anotar_campo(lista, numero, args.campo, args.valor))
        return {"numero": numero, "campo": args.campo, "valor": args.valor.strip()}
    if comando == "devolver":
        _com_trava(raiz, deps, lambda: devolver(lista, args.numero))
        return {"numero": args.numero, "destino": lista.name}
    if comando in ("fipe-candidatos", "fipe-valor"):
        fipe = Fipe(raiz / "dados" / "fipe-cache.json", deps.transporte_analise, relogio=deps.relogio,
                    dormir=deps.dormir, hoje=lambda: hoje)
        if comando == "fipe-valor":
            return fipe.valor(args.codigo, args.ano)
        return fipe.candidatas(args.marca, args.modelo, args.ano)
    if comando == "custo":
        custos = carregar_custos(raiz / "config" / "custos.yaml")
        distancias = Distancias(custos.distancias, raiz / "dados" / "distancias.json", origem=custos.cidade_base,
                                transporte=deps.transporte_analise, relogio=deps.relogio, dormir=deps.dormir)
        resultado = calcular(custos, lance=args.lance, despesa=args.despesa, km=distancias.km(args.patio),
                             documento_uf=args.documento_uf, fipe=args.fipe, reparos_extra=args.reparos_extra,
                             motivo_reparos=args.motivo_reparos)
        return {"patio": args.patio, **resultado}
    if comando == "anotar-custo":
        numero = _numero(lista, args.lote)
        bruto = sys.stdin.read() if args.json == "-" else Path(args.json).read_text(encoding="utf-8")
        dados = json.loads(bruto)
        _com_trava(raiz, deps, lambda: anotar_custo(lista, numero, dados))
        return {"numero": numero, "anotado": True}
    raise ValueError(f"subcomando desconhecido: {comando}")


def _erro_lista(numero):
    raise ErroLista(f"o lote {numero} não está em {LISTA.name}")
