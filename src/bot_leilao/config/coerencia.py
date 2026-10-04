"""Aviso de coerência entre veículos-alvo e buscas (audit A004).

Um alvo cujo `tipos_leilao` não contém nenhum tipo produzido pelas buscas ativas
nunca casará com lote nenhum. Sem aviso, isso seria perda silenciosa.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from bot_leilao.config.leiloeiros import Busca, Leiloeiro
from bot_leilao.config.veiculos import VeiculoAlvo


def verificar_coerencia(
    alvos: Sequence[VeiculoAlvo],
    leiloeiros: Sequence[Leiloeiro],
    tipo_da_busca: Callable[[Leiloeiro, Busca], str | None],
) -> list[str]:
    """Devolve avisos; nunca levanta."""
    alvos_ativos = [a for a in alvos if a.ativo]
    if not alvos_ativos or not leiloeiros:
        return []

    avisos: list[str] = []
    produzidos: set[str] = set()
    for leiloeiro in leiloeiros:
        for busca in leiloeiro.buscas:
            try:
                tipo = tipo_da_busca(leiloeiro, busca)
            except Exception as erro:  # noqa: BLE001 — aviso, nunca aborta
                avisos.append(f"Não consegui determinar o tipo de leilão da busca '{busca.descricao}' "
                              f"de {leiloeiro.nome}: {erro}")
                continue
            if tipo is None:
                avisos.append(f"A busca '{busca.descricao}' de {leiloeiro.nome} não informa o tipo de leilão; "
                              "seus lotes não casarão com nenhum veículo-alvo.")
            else:
                produzidos.add(tipo)

    if produzidos:
        for alvo in alvos_ativos:
            if not produzidos & set(alvo.tipos_leilao):
                avisos.append(
                    f"O veículo-alvo '{alvo.marca} {alvo.modelo}' aceita {', '.join(alvo.tipos_leilao)}, "
                    f"mas as buscas ativas só trazem {', '.join(sorted(produzidos))}: ele nunca vai casar."
                )
    return avisos
