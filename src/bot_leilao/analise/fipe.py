"""FIPE pela parallelum v2, com reserva no site oficial e cache por mês (feature 006; roadmap D-114; interfaces/fipe.md).

A parallelum repassa os dados da FIPE (500 consultas por dia, sem token); o site oficial tem os mesmos códigos e
valores. Toda resposta diz o mês de referência e a fonte. O cache (`dados/fipe-cache.json`) vale para o mês de
referência atual: quando a FIPE publica o mês novo, as consultas são refeitas.
"""

from __future__ import annotations

import json
import logging
import os
import re
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
    def __init__(self, cache: Path, transporte: httpx.BaseTransport | None = None, timeout: float = 20.0) -> None:
        self.caminho_cache = cache
        self._cliente = httpx.Client(transport=transporte, timeout=timeout,
                                     headers={"User-Agent": "bot-leilao-carros (analise de lotes)"})
        self._referencia: tuple[str, str] | None = None

    # --- Infra -------------------------------------------------------------------------------------------

    def _get(self, caminho: str):
        try:
            resposta = self._cliente.get(f"{PARALLELUM}/{caminho}")
        except httpx.HTTPError as erro:
            raise _FonteFora(f"parallelum: {type(erro).__name__}") from None
        if resposta.status_code == 404:
            return None
        if resposta.status_code != 200:
            raise _FonteFora(f"parallelum: http_{resposta.status_code}")
        return resposta.json()

    def _post(self, acao: str, dados: dict):
        try:
            resposta = self._cliente.post(f"{OFICIAL}/{acao}", data=dados,
                                          headers={"Referer": "https://veiculos.fipe.org.br/"})
        except httpx.HTTPError as erro:
            raise _FonteFora(f"fipe.org.br: {type(erro).__name__}") from None
        if resposta.status_code != 200:
            raise _FonteFora(f"fipe.org.br: http_{resposta.status_code}")
        corpo = resposta.json()
        if isinstance(corpo, dict) and corpo.get("erro"):
            return None
        return corpo

    def referencia(self) -> tuple[str, str]:
        """(código, mês) da tabela de referência atual, pela parallelum ou pelo site oficial."""
        if self._referencia is None:
            try:
                atual = self._get("references")[0]
                self._referencia = (str(atual["code"]), atual["month"].strip())
            except (_FonteFora, TypeError, IndexError, KeyError):
                try:
                    atual = self._post("ConsultarTabelaDeReferencia", {})[0]
                    self._referencia = (str(atual["Codigo"]), atual["Mes"].strip())
                except (_FonteFora, TypeError, IndexError, KeyError):
                    raise ErroFipe("FIPE indisponível: parallelum e site oficial não responderam") from None
        return self._referencia

    def _cache(self) -> dict:
        try:
            tudo = json.loads(self.caminho_cache.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            tudo = {}
        return tudo.get(self.referencia()[1], {})

    def _guardar(self, chave: str, valor: dict) -> None:
        try:
            tudo = json.loads(self.caminho_cache.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            tudo = {}
        mes = self.referencia()[1]
        tudo = {mes: {**tudo.get(mes, {}), chave: valor}}   # meses antigos saem do cache
        self.caminho_cache.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho_cache.with_name(f".{self.caminho_cache.name}.tmp")
        temporario.write_text(json.dumps(tudo, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        os.replace(temporario, self.caminho_cache)

    @staticmethod
    def _decimais(resultado: dict) -> dict:
        """O cache guarda valores como texto; devolve com Decimal."""
        if "valor" in resultado:
            return {**resultado, "valor": Decimal(str(resultado["valor"]))}
        return {**resultado, "candidatas": [{**c, "valor": Decimal(str(c["valor"]))} for c in resultado["candidatas"]]}

    def _com_reserva(self, chave: str, pela_parallelum, pelo_oficial) -> dict:
        guardado = self._cache().get(chave)
        if guardado is not None:
            return self._decimais(guardado)
        mes = self.referencia()[1]
        try:
            resultado = {**pela_parallelum(), "mes_referencia": mes, "fonte": FONTE_PARALLELUM}
        except _FonteFora as erro:
            log.info("analise | FIPE: %s; usando o site oficial", erro)
            try:
                resultado = {**pelo_oficial(), "mes_referencia": mes, "fonte": FONTE_OFICIAL}
            except _FonteFora:
                raise ErroFipe("FIPE indisponível: parallelum e site oficial não responderam") from None
        self._guardar(chave, resultado)
        return resultado

    # --- Valor por código ---------------------------------------------------------------------------------

    def valor(self, codigo: str, ano: int) -> dict:
        """Valor de um código FIPE num ano de modelo: {codigo, versao, combustivel, valor, mes_referencia, fonte}."""
        return self._com_reserva(f"valor|{codigo}|{ano}", lambda: self._valor_parallelum(codigo, ano),
                                 lambda: self._valor_oficial(codigo, ano))

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
        return self._com_reserva(chave, lambda: self._candidatas_parallelum(marca, termos, ano),
                                 lambda: self._candidatas_oficial(marca, termos, ano))

    def _candidatas_parallelum(self, marca: str, termos: str, ano: int) -> dict:
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

    def _candidatas_oficial(self, marca: str, termos: str, ano: int) -> dict:
        base = {"codigoTabelaReferencia": self.referencia()[0], "codigoTipoVeiculo": "1"}
        marcas = self._post("ConsultarMarcas", base) or []
        codigo_marca = next((m["Value"] for m in marcas if normalizar_texto(m["Label"]) == normalizar_texto(marca)),
                            None)
        if codigo_marca is None:
            return {"candidatas": []}
        modelos = (self._post("ConsultarModelos", {**base, "codigoMarca": codigo_marca}) or {}).get("Modelos", [])
        candidatas = []
        for modelo in modelos:
            if not _casa(modelo["Label"], termos):
                continue
            anos = self._post("ConsultarAnoModelo", {**base, "codigoMarca": codigo_marca,
                                                     "codigoModelo": str(modelo["Value"])}) or []
            ano_codigo = next((a["Value"] for a in anos if str(a["Value"]).startswith(f"{ano}-")), None)
            if ano_codigo is None:
                continue
            preco = self._post("ConsultarValorComTodosParametros", {
                **base, "codigoMarca": codigo_marca, "codigoModelo": str(modelo["Value"]), "anoModelo": str(ano),
                "codigoTipoCombustivel": ano_codigo.split("-")[1], "tipoVehiculo": "carro",
                "tipoConsulta": "tradicional"})
            if preco:
                candidatas.append(self._oficial_para_valor(preco))
        return {"candidatas": candidatas}
