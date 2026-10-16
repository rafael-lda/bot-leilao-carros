"""FIPE pela parallelum v2 e pelo site oficial, com cache por mês (feature 006; roadmap D-114, D-123; interfaces/fipe.md).

A parallelum repassa os dados da FIPE (500 pedidos por dia, sem token; cada pedido HTTP conta); o site oficial tem os
mesmos códigos e valores. Toda resposta diz o mês de referência e a fonte. O cache (`dados/fipe-cache.json`) vale
para o mês de referência atual: quando a FIPE publica o mês novo, as consultas são refeitas.

Emenda de 2026-10-16 (D-123): a busca de versões custava um pedido por versão parecida com o nome (até 119 no
"hb20") e esgotou o limite da parallelum. Agora ela vai primeiro ao site oficial, que lista num pedido só as versões
de um ano e combustível (`ConsultarModelosAtravesDoAno`); a parallelum fica de reserva. O valor por código continua
na parallelum (2 pedidos). Os pedidos ao site oficial são espaçados e repetidos quando ele bloqueia (429); a
parallelum no limite não é chamada de novo na mesma execução; o mês de referência e as marcas ficam no cache.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections.abc import Callable, Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx

from bot_leilao.texto import normalizar_texto

log = logging.getLogger(__name__)

PARALLELUM = "https://parallelum.com.br/fipe/api/v2"
OFICIAL = "https://veiculos.fipe.org.br/api/veiculos"
FONTE_PARALLELUM = "parallelum"
FONTE_OFICIAL = "fipe.org.br"
COMBUSTIVEIS = ("5", "1", "3", "2")   # flex, gasolina, diesel, álcool: ordem de tentativa no site oficial
INTERVALO_OFICIAL = 1.0               # segundos entre pedidos ao site oficial
ESPERAS_OFICIAL = (5.0, 15.0)         # esperas antes de repetir um pedido bloqueado (429)
ESPERA_MAXIMA = 60.0                  # Retry-After maior que isto não é esperado
_REFERENCIA = "_referencia"           # chave do cache com o mês de referência do dia
_PONTUACAO = re.compile(r"[.,;:()]+$")


class ErroFipe(Exception):
    """FIPE indisponível nas duas fontes, ou código/ano inexistente."""


class _FonteFora(Exception):
    """A fonte não respondeu como esperado: tentar a outra."""


def _valor(texto: str) -> Decimal:
    """"R$ 62.464,00" → Decimal("62464.00")."""
    return Decimal(texto.replace("R$", "").strip().replace(".", "").replace(",", "."))


def _tokens(texto: str) -> list[str]:
    return [_PONTUACAO.sub("", t) for t in normalizar_texto(texto).split()]


def _casa(nome: str, termos: str) -> bool:
    disponiveis = set(_tokens(nome))
    return all(t in disponiveis for t in _tokens(termos))


class Fipe:
    def __init__(self, cache: Path, transporte: httpx.BaseTransport | None = None, timeout: float = 20.0, *,
                 intervalo_oficial: float = INTERVALO_OFICIAL, esperas_oficial: Sequence[float] = ESPERAS_OFICIAL,
                 relogio: Callable[[], float] = time.monotonic, dormir: Callable[[float], None] = time.sleep,
                 hoje: Callable[[], date] = date.today) -> None:
        self.caminho_cache = cache
        self._cliente = httpx.Client(transport=transporte, timeout=timeout,
                                     headers={"User-Agent": "bot-leilao-carros (analise de lotes)"})
        self._referencia: tuple[str, str] | None = None
        self._intervalo = intervalo_oficial
        self._esperas = tuple(esperas_oficial)
        self._relogio, self._dormir, self._hoje = relogio, dormir, hoje
        self._ultimo_oficial: float | None = None
        self._parallelum_esgotada = False

    # --- Infra -------------------------------------------------------------------------------------------

    def _get(self, caminho: str):
        if self._parallelum_esgotada:
            raise _FonteFora("parallelum: limite diário já atingido nesta execução")
        try:
            resposta = self._cliente.get(f"{PARALLELUM}/{caminho}")
        except httpx.HTTPError as erro:
            raise _FonteFora(f"parallelum: {type(erro).__name__}") from None
        if resposta.status_code == 404:
            return None
        if resposta.status_code == 429:
            self._parallelum_esgotada = True   # o limite é diário: esperar não adianta
        if resposta.status_code != 200:
            raise _FonteFora(f"parallelum: http_{resposta.status_code}")
        return resposta.json()

    def _espacar(self) -> None:
        if self._ultimo_oficial is not None:
            falta = self._intervalo - (self._relogio() - self._ultimo_oficial)
            if falta > 0:
                self._dormir(falta)
        self._ultimo_oficial = self._relogio()

    def _post(self, acao: str, dados: dict):
        for tentativa in range(len(self._esperas) + 1):
            self._espacar()
            try:
                resposta = self._cliente.post(f"{OFICIAL}/{acao}", data=dados,
                                              headers={"Referer": "https://veiculos.fipe.org.br/"})
            except httpx.HTTPError as erro:
                raise _FonteFora(f"fipe.org.br: {type(erro).__name__}") from None
            if resposta.status_code == 429 and tentativa < len(self._esperas):
                espera = self._esperas[tentativa]
                try:
                    espera = max(espera, float(resposta.headers.get("retry-after", 0)))
                except ValueError:
                    pass
                if espera > ESPERA_MAXIMA:
                    break
                log.info("analise | FIPE: fipe.org.br bloqueou (429); nova tentativa em %.0f s", espera)
                self._dormir(espera)
                continue
            break
        if resposta.status_code != 200:
            raise _FonteFora(f"fipe.org.br: http_{resposta.status_code}")
        corpo = resposta.json()
        if isinstance(corpo, dict) and corpo.get("erro"):
            return None
        return corpo

    def _ler_cache(self) -> dict:
        try:
            tudo = json.loads(self.caminho_cache.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            tudo = {}
        return tudo if isinstance(tudo, dict) else {}

    def _gravar_cache(self, tudo: dict) -> None:
        self.caminho_cache.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho_cache.with_name(f".{self.caminho_cache.name}.tmp")
        temporario.write_text(json.dumps(tudo, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        os.replace(temporario, self.caminho_cache)

    def referencia(self) -> tuple[str, str]:
        """(código, mês) da tabela de referência atual. Consultada uma vez por dia (fica no cache)."""
        if self._referencia is not None:
            return self._referencia
        dia = self._hoje().isoformat()
        guardada = self._ler_cache().get(_REFERENCIA) or {}
        if guardada.get("dia") == dia and guardada.get("codigo") and guardada.get("mes"):
            self._referencia = (str(guardada["codigo"]), guardada["mes"])
            return self._referencia
        try:
            atual = self._get("references")[0]
            self._referencia = (str(atual["code"]), atual["month"].strip())
        except (_FonteFora, TypeError, IndexError, KeyError):
            try:
                atual = self._post("ConsultarTabelaDeReferencia", {})[0]
                self._referencia = (str(atual["Codigo"]), atual["Mes"].strip())
            except (_FonteFora, TypeError, IndexError, KeyError):
                raise ErroFipe("FIPE indisponível: parallelum e site oficial não responderam") from None
        tudo = self._ler_cache()
        tudo[_REFERENCIA] = {"codigo": self._referencia[0], "mes": self._referencia[1], "dia": dia}
        self._gravar_cache(tudo)
        return self._referencia

    def _cache(self) -> dict:
        return self._ler_cache().get(self.referencia()[1], {})

    def _guardar(self, chave: str, valor) -> None:
        mes = self.referencia()[1]
        tudo = self._ler_cache()
        # meses antigos saem do cache; a referência do dia fica
        tudo = {_REFERENCIA: tudo.get(_REFERENCIA), mes: {**tudo.get(mes, {}), chave: valor}}
        self._gravar_cache({k: v for k, v in tudo.items() if v is not None})

    @staticmethod
    def _decimais(resultado: dict) -> dict:
        """O cache guarda valores como texto; devolve com Decimal."""
        if "valor" in resultado:
            return {**resultado, "valor": Decimal(str(resultado["valor"]))}
        return {**resultado, "candidatas": [{**c, "valor": Decimal(str(c["valor"]))} for c in resultado["candidatas"]]}

    def _com_reserva(self, chave: str, fontes: Sequence[tuple[str, Callable[[], dict]]]) -> dict:
        guardado = self._cache().get(chave)
        if guardado is not None:
            return self._decimais(guardado)
        mes = self.referencia()[1]
        for posicao, (nome, consultar) in enumerate(fontes):
            try:
                resultado = {**consultar(), "mes_referencia": mes, "fonte": nome}
                break
            except _FonteFora as erro:
                if posicao + 1 < len(fontes):
                    log.info("analise | FIPE: %s; usando %s", erro, fontes[posicao + 1][0])
        else:
            raise ErroFipe("FIPE indisponível: parallelum e site oficial não responderam")
        self._guardar(chave, resultado)
        return resultado

    # --- Valor por código ---------------------------------------------------------------------------------

    def valor(self, codigo: str, ano: int) -> dict:
        """Valor de um código FIPE num ano de modelo: {codigo, versao, combustivel, valor, mes_referencia, fonte}."""
        return self._com_reserva(f"valor|{codigo}|{ano}", [
            (FONTE_PARALLELUM, lambda: self._valor_parallelum(codigo, ano)),
            (FONTE_OFICIAL, lambda: self._valor_oficial(codigo, ano))])

    def _valor_parallelum(self, codigo: str, ano: int) -> dict:
        anos = self._get(f"cars/{codigo}/years") or []
        ano_codigo = next((a["code"] for a in anos if a["code"].startswith(f"{ano}-")), None)
        if ano_codigo is None:
            raise ErroFipe(f"o código FIPE {codigo} não tem o ano {ano}")
        preco = self._get(f"cars/{codigo}/years/{ano_codigo}")
        if preco is None:
            raise ErroFipe(f"o código FIPE {codigo} não tem o ano {ano}")
        return {"codigo": preco["codeFipe"], "versao": preco["model"].strip(), "combustivel": preco["fuel"],
                "valor": _valor(preco["price"])}

    def _valor_oficial(self, codigo: str, ano: int) -> dict:
        tabela = self.referencia()[0]
        for combustivel in COMBUSTIVEIS:
            preco = self._post("ConsultarValorComTodosParametros", {
                "codigoTabelaReferencia": tabela, "codigoTipoVeiculo": "1", "anoModelo": str(ano),
                "codigoTipoCombustivel": combustivel, "tipoVehiculo": "carro", "modeloCodigoExterno": codigo,
                "tipoConsulta": "codigo"})
            if preco:
                return self._oficial_para_valor(preco)
        raise ErroFipe(f"o código FIPE {codigo} não tem o ano {ano}")

    @staticmethod
    def _oficial_para_valor(preco: dict) -> dict:
        return {"codigo": preco["CodigoFipe"], "versao": preco["Modelo"].strip(), "combustivel": preco["Combustivel"],
                "valor": _valor(preco["Valor"])}

    # --- Candidatas por marca, termos e ano ---------------------------------------------------------------

    def candidatas(self, marca: str, termos: str, ano: int) -> dict:
        """Versões daquele ano de modelo cujo nome contém todos os termos: {candidatas: [...], mes_referencia, fonte}."""
        chave = f"candidatas|{normalizar_texto(marca)}|{normalizar_texto(termos)}|{ano}"
        return self._com_reserva(chave, [
            (FONTE_OFICIAL, lambda: self._candidatas_oficial(marca, termos, ano)),
            (FONTE_PARALLELUM, lambda: self._candidatas_parallelum(marca, termos, ano))])

    def _marcas_oficial(self, tabela: str) -> list:
        guardadas = self._cache().get("marcas|oficial")
        if guardadas is None:
            guardadas = self._post("ConsultarMarcas", {"codigoTabelaReferencia": tabela, "codigoTipoVeiculo": "1"}) or []
            self._guardar("marcas|oficial", guardadas)
        return guardadas

    def _candidatas_oficial(self, marca: str, termos: str, ano: int) -> dict:
        """Um pedido por combustível lista as versões do ano; depois, um pedido de valor por versão que casa."""
        tabela = self.referencia()[0]
        base = {"codigoTabelaReferencia": tabela, "codigoTipoVeiculo": "1"}
        codigo_marca = next((m["Value"] for m in self._marcas_oficial(tabela)
                             if normalizar_texto(m["Label"]) == normalizar_texto(marca)), None)
        if codigo_marca is None:
            return {"candidatas": []}
        candidatas, vistos = [], set()
        for combustivel in COMBUSTIVEIS:
            modelos = self._post("ConsultarModelosAtravesDoAno", {
                **base, "codigoMarca": str(codigo_marca), "codigoModelo": "", "ano": f"{ano}-{combustivel}",
                "codigoTipoCombustivel": combustivel, "anoModelo": str(ano)}) or []
            for modelo in modelos:
                if (modelo["Value"], combustivel) in vistos or not _casa(modelo["Label"], termos):
                    continue
                vistos.add((modelo["Value"], combustivel))
                preco = self._post("ConsultarValorComTodosParametros", {
                    **base, "codigoMarca": str(codigo_marca), "codigoModelo": str(modelo["Value"]),
                    "anoModelo": str(ano), "codigoTipoCombustivel": combustivel, "tipoVehiculo": "carro",
                    "tipoConsulta": "tradicional"})
                if preco:
                    candidatas.append(self._oficial_para_valor(preco))
        return {"candidatas": candidatas}

    def _candidatas_parallelum(self, marca: str, termos: str, ano: int) -> dict:
        """Reserva: a parallelum não lista versões por ano, então custa um pedido de anos por versão que casa."""
        marcas = self._get("cars/brands") or []
        codigo_marca = next((m["code"] for m in marcas if normalizar_texto(m["name"]) == normalizar_texto(marca)), None)
        if codigo_marca is None:
            return {"candidatas": []}
        candidatas = []
        for modelo in self._get(f"cars/brands/{codigo_marca}/models") or []:
            if not _casa(modelo["name"], termos):
                continue
            anos = self._get(f"cars/brands/{codigo_marca}/models/{modelo['code']}/years") or []
            ano_codigo = next((a["code"] for a in anos if a["code"].startswith(f"{ano}-")), None)
            if ano_codigo is None:
                continue
            preco = self._get(f"cars/brands/{codigo_marca}/models/{modelo['code']}/years/{ano_codigo}")
            if preco:
                candidatas.append({"codigo": preco["codeFipe"], "versao": preco["model"].strip(),
                                   "combustivel": preco["fuel"], "valor": _valor(preco["price"])})
        return {"candidatas": candidatas}
