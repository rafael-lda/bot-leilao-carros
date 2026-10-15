"""Custo na garagem (feature 006; roadmap D-116; RN-08, RF-08, RF-10).

Custo = lance + comissão + despesa fixa do lote + frete (km × R$/km) + transferência + reserva de reparos (+ reparos
extras com motivo). Lance máximo = (revenda ÷ (1 + margem) − despesa − frete − transferência − reparos) ÷ (1 +
comissão), com revenda = % da FIPE. Contas em Decimal, sempre iguais para a mesma entrada.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

from bot_leilao.config.arquivos import ErroConfiguracao, ler_yaml

EXEMPLO_CUSTOS = """\
# Custos para estimar o valor do carro na garagem (skill analisar-lotes, feature 006).
# Valores do esclarecimento de 2026-10-15; edite à vontade. Valores em reais, percentuais de 0 a 100.
cidade_base: Londrina - PR
uf_base: PR
comissao_percentual: 5            # do leiloeiro, sobre o lance
despesa_padrao: 2650              # quando o lote não traz a despesa fixa (mediana do Vip)
frete_por_km: 4.50                # ESTIMATIVA: troque quando tiver orçamento de guincho
transferencia_mesmo_estado: 450   # documento do PR
transferencia_outro_estado: 650   # documento de outro estado (vistoria, talvez placa)
reparos_reserva: 2000             # colchão por carro
revenda_percentual_fipe: 85       # carro de leilão revende 10 a 20% abaixo da FIPE
margem_percentual: 10             # lucro desejado, sobre o custo na garagem
# Distância do pátio até a cidade base, em km (ida). Opcional: vence o cálculo automático.
distancias: {}
#  "Curitiba - PR": 386
"""

CAMPOS_VALOR = ("despesa_padrao", "frete_por_km", "transferencia_mesmo_estado", "transferencia_outro_estado",
                "reparos_reserva")
CAMPOS_PERCENTUAL = ("comissao_percentual", "revenda_percentual_fipe", "margem_percentual")
_CIDADE_UF = re.compile(r"^.+ - [A-Z]{2}$")


class ErroCustos(Exception):
    """`custos.yaml` inválido ou pedido de cálculo incompleto."""


@dataclass(frozen=True)
class Custos:
    cidade_base: str
    uf_base: str
    comissao_percentual: Decimal
    despesa_padrao: Decimal
    frete_por_km: Decimal
    transferencia_mesmo_estado: Decimal
    transferencia_outro_estado: Decimal
    reparos_reserva: Decimal
    revenda_percentual_fipe: Decimal
    margem_percentual: Decimal
    distancias: dict[str, int] = field(default_factory=dict)


def _numero(dados: dict, campo: str, maximo: Decimal | None = None) -> Decimal:
    valor = dados.get(campo)
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErroCustos(f"custos.yaml: {campo} ({valor!r}) deve ser um número")
    numero = Decimal(str(valor))
    if numero < 0 or (maximo is not None and numero > maximo):
        raise ErroCustos(f"custos.yaml: {campo} ({valor!r}) fora da faixa"
                         + (f" de 0 a {maximo}" if maximo is not None else ": deve ser zero ou mais"))
    return numero


def carregar_custos(caminho: Path) -> Custos:
    """Lê `config/custos.yaml`; se não existir, cria com os valores do esclarecimento e segue."""
    if not caminho.exists():
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(EXEMPLO_CUSTOS, encoding="utf-8")
    try:
        dados = ler_yaml(caminho)
    except ErroConfiguracao as erro:
        raise ErroCustos(str(erro)) from None
    if not isinstance(dados, dict):
        raise ErroCustos("custos.yaml deve ter um campo por linha (veja o exemplo no próprio arquivo)")
    cidade, uf = dados.get("cidade_base"), dados.get("uf_base")
    if not isinstance(cidade, str) or not _CIDADE_UF.match(cidade.strip()):
        raise ErroCustos(f"custos.yaml: cidade_base ({cidade!r}) deve ser \"Cidade - UF\", ex.: Londrina - PR")
    if not isinstance(uf, str) or not re.fullmatch(r"[A-Z]{2}", uf.strip()):
        raise ErroCustos(f"custos.yaml: uf_base ({uf!r}) deve ser a sigla do estado, ex.: PR")
    distancias = dados.get("distancias") or {}
    if not isinstance(distancias, dict) or not all(
            isinstance(k, str) and isinstance(v, int) and not isinstance(v, bool) and v > 0
            for k, v in distancias.items()):
        raise ErroCustos("custos.yaml: distancias deve mapear \"Cidade - UF\" para km inteiros, ex.: \"Curitiba - PR\": 386")
    return Custos(
        cidade_base=cidade.strip(), uf_base=uf.strip(),
        **{c: _numero(dados, c, Decimal(100)) for c in CAMPOS_PERCENTUAL},
        **{c: _numero(dados, c) for c in CAMPOS_VALOR},
        distancias=dict(distancias),
    )


def _inteiro(valor: Decimal, arredondamento=ROUND_HALF_UP) -> Decimal:
    return valor.quantize(Decimal("1"), rounding=arredondamento)


def calcular(custos: Custos, *, lance: Decimal, despesa: Decimal | None = None, km: int | None = None,
             documento_uf: str | None = None, fipe: Decimal | None = None, reparos_extra: Decimal | None = None,
             motivo_reparos: str | None = None) -> dict:
    """Parcelas, total, % da FIPE e lance máximo. Distância desconhecida: frete "a confirmar", fora do total."""
    if reparos_extra and not (motivo_reparos or "").strip():
        raise ErroCustos("reparos extras exigem o motivo (--motivo-reparos)")
    try:
        lance = Decimal(str(lance))
    except InvalidOperation:
        raise ErroCustos(f"lance inválido: {lance!r}") from None
    avisos: list[str] = []
    comissao = lance * custos.comissao_percentual / 100
    despesa_padrao = despesa is None
    despesa = custos.despesa_padrao if despesa is None else Decimal(str(despesa))
    frete = None if km is None else Decimal(km) * custos.frete_por_km
    if frete is None:
        avisos.append("frete a confirmar: distância do pátio desconhecida (fora do total)")
    if documento_uf is None:
        transferencia = custos.transferencia_outro_estado
        avisos.append("estado do documento desconhecido: transferência calculada como de outro estado")
    elif documento_uf.strip().upper() == custos.uf_base:
        transferencia = custos.transferencia_mesmo_estado
    else:
        transferencia = custos.transferencia_outro_estado
    extra = Decimal(str(reparos_extra)) if reparos_extra else Decimal(0)
    total = lance + comissao + despesa + (frete or 0) + transferencia + custos.reparos_reserva + extra
    percentual = lance_maximo = None
    if fipe:
        fipe = Decimal(str(fipe))
        percentual = int(_inteiro(total / fipe * 100))
        revenda = fipe * custos.revenda_percentual_fipe / 100
        teto = revenda / (1 + custos.margem_percentual / 100)
        livre = teto - despesa - (frete or 0) - transferencia - custos.reparos_reserva - extra
        lance_maximo = max(Decimal(0), _inteiro(livre / (1 + custos.comissao_percentual / 100), ROUND_DOWN))
    return {
        "parcelas": {"lance": lance, "comissao": comissao, "despesa": despesa, "despesa_padrao": despesa_padrao,
                     "frete": frete, "frete_km": km, "frete_por_km": custos.frete_por_km,
                     "frete_estimado": frete is not None, "transferencia": transferencia,
                     "reparos": custos.reparos_reserva, "reparos_extra": extra if extra else None,
                     "motivo_reparos": motivo_reparos.strip() if extra and motivo_reparos else None},
        "total": total,
        "percentual_fipe": percentual,
        "lance_maximo": lance_maximo,
        "margem_percentual": int(custos.margem_percentual) if custos.margem_percentual == int(custos.margem_percentual)
        else float(custos.margem_percentual),
        "avisos": avisos,
    }
