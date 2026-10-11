"""Parser da Copart Brasil (feature 003; interfaces/copart-busca.md; roadmap D-61 a D-67).

Cada lote da busca JSON já traz pátio, FIPE, lance, data do leilão e estado; não há etapa de detalhe.
Armadilhas conferidas em 2026-10-11: `fv` é o chassi (a FIPE é `la`) e `ad` está em UTC.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from bot_leilao.parsing.marcas import marca_canonica
from bot_leilao.parsing.modelos import ContextoParsing, ExtracaoPagina, Lote
from bot_leilao.parsing.normalizadores import normalizar_preco
from bot_leilao.parsing.nucleo import registrar_parser
from bot_leilao.texto import normalizar_texto

LEILOEIRO_ID = "copart"
BRASILIA = timezone(timedelta(hours=-3))  # offset fixo: o Windows não traz a base do zoneinfo (D-22 da 002)
AGUARDANDO = "aguardando classificacao"
SEM_CLASSIFICACAO = "Aguardando classificação da Copart (data, FIPE e lance a definir)"
_DATA_UTC = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


def _texto(valor) -> str:
    return " ".join(str(valor or "").split())


def _decimal(valor) -> Decimal | None:
    try:
        numero = Decimal(str(valor).strip())
    except (InvalidOperation, ValueError):
        return None
    return numero if numero > 0 else None


def _pregao(ad: str) -> datetime | None:
    """D-65: `2026-10-15 11:30:00` é UTC; vazio ou "Copart Select" não é data."""
    if not _DATA_UTC.fullmatch(_texto(ad)):
        return None
    return datetime.strptime(ad.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(BRASILIA)


def _ano(valor) -> int | None:
    texto = _texto(valor)
    return int(texto) if texto.isdigit() and len(texto) == 4 else None


def _observacoes(item: dict) -> str | None:
    """D-66: Compre Agora, dano, documento, monta, funcionamento e comitente, nessa ordem, sem vazios."""
    partes = []
    if _texto(item.get("saleType")) == "Compre Agora":
        partes.append("Compre Agora")
    if _texto(item.get("dd")):
        partes.append(_texto(item["dd"]))
    documento = _texto(item.get("stt") or item.get("td"))
    if normalizar_texto(documento) == AGUARDANDO:
        partes.append(SEM_CLASSIFICACAO)
    else:
        if documento:
            partes.append(f"Documento {documento}")
        monta = _texto(item.get("damageClassification"))
        if monta and normalizar_texto(monta) not in (AGUARDANDO, "nao aplicavel"):
            partes.append(monta)
    if _texto(item.get("drivabilityRating")) and normalizar_texto(item["drivabilityRating"]) != "desconhecido":
        partes.append(_texto(item["drivabilityRating"]))
    if _texto(item.get("sellerName")):
        partes.append(f"Comitente {_texto(item['sellerName'])}")
    return " · ".join(partes) or None


class ParserCopart:
    preco_obrigatorio = False  # D-63: 1.445 de 1.506 lotes sem lance (2026-10-11)

    def extrair(self, conteudo: bytes, contexto: ContextoParsing) -> ExtracaoPagina:
        dados = json.loads(conteudo)
        if dados.get("returnCode") != 1:
            raise ValueError(f"busca da Copart sem sucesso: {dados.get('returnCodeDesc')!r}")
        resultados = dados["data"]["results"]
        total = int(resultados["totalElements"])
        lotes = [self._lote(item, contexto) for item in resultados["content"]]
        return ExtracaoPagina(lotes=lotes, busca_vazia=total == 0 and not lotes, total_informado=total)

    def _lote(self, item: dict, contexto: ContextoParsing) -> Lote:
        numero = str(item["ln"]).strip()
        marca, modelo = _texto(item["mkn"]), _texto(item.get("lm"))
        if not numero or not marca:
            raise ValueError("lote da Copart sem número ou marca")
        if _texto(item.get("saleType")) == "Compre Agora":
            preco = normalizar_preco(_texto(item.get("saleAmountBIN")) or None)
        else:
            preco = _decimal(item.get("hb"))
        return Lote(
            id_canonico=f"{LEILOEIRO_ID}:{numero}",                                  # D-61
            leiloeiro_id=contexto.leiloeiro_id,
            busca_id=contexto.busca_id,
            link=f"{contexto.base_url}/lotDetail/{numero}",
            coletado_em=contexto.coletado_em,
            titulo=" ".join(filter(None, [marca, modelo, _texto(item.get("eng"))])),  # D-62
            marca=marca_canonica(marca),
            modelo=normalizar_texto(modelo) or None,
            ano_fabricacao=_ano(item.get("manufactureYear")),
            ano_modelo=_ano(item.get("lcy")),
            lance_corrente=preco,
            tipo_leilao=contexto.tipo_leilao,
            pregao_em=_pregao(_texto(item.get("ad"))),
            observacoes=_observacoes(item),
            patio=_texto(item.get("yn")) or None,
            fipe=_decimal(item.get("la")),                                           # D-64: nunca `fv` (chassi)
        )


registrar_parser(LEILOEIRO_ID, ParserCopart())
