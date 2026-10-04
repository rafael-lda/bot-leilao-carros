"""Deduplicação, semeadura e gravação (RN-05 a RN-07; motor-filtros RF-09 a RF-13; roadmap D-20)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from bot_leilao.config.veiculos import VeiculoAlvo
from bot_leilao.db.lotes import RegistroLote, RepositorioLotes
from bot_leilao.filtro.motor import Candidato, avaliar
from bot_leilao.parsing.modelos import ResultadoParsing


@dataclass
class ResultadoFiltragem:
    vistos: int = 0
    candidatos: int = 0
    novos: list[Candidato] = field(default_factory=list)
    semeaveis: list[Candidato] = field(default_factory=list)
    ja_conhecidos: int = 0
    descartados_sem_casar: int = 0
    descartados_dado_ausente: int = 0
    descartados_retirados: int = 0
    descartados_acima_km: int = 0
    buscas_a_semear: list[str] = field(default_factory=list)

    def contagens(self) -> dict[str, int]:
        """Colunas de `execucao` (data-delta.md §2.3)."""
        return {
            "lotes_vistos": self.vistos,
            "lotes_candidatos": self.candidatos,
            "lotes_novos": len(self.novos),
            "lotes_ja_conhecidos": self.ja_conhecidos,
            "lotes_semeados": len(self.semeaveis),
            "descartados_sem_casar": self.descartados_sem_casar,
            "descartados_dado_ausente": self.descartados_dado_ausente,
            "descartados_retirados": self.descartados_retirados,
        }


def _registro(candidato: Candidato, origem: str, quando: datetime) -> RegistroLote:
    lote = candidato.lote
    return RegistroLote(id_canonico=lote.id_canonico, leiloeiro_id=lote.leiloeiro_id, busca_id=lote.busca_id,
                        alvo_id=candidato.alvo.id, origem=origem, preco_na_notificacao=candidato.preco,
                        lance_inicial=lote.lance_inicial, link=lote.link, registrado_em=quando)


class FluxoFiltragem:
    def __init__(self, repo: RepositorioLotes) -> None:
        self.repo = repo

    def filtrar(self, resultados: Sequence[ResultadoParsing], alvos: Sequence[VeiculoAlvo],
                buscas_aptas: set[str]) -> ResultadoFiltragem:
        """`buscas_aptas`: buscas com coleta `ok` e sem sinal de quebra nesta execução (D-20)."""
        lotes = [lote for r in resultados for lote in r.lotes]
        criterios = avaliar(lotes, alvos)
        saida = ResultadoFiltragem(
            vistos=criterios.vistos,
            descartados_sem_casar=criterios.descartados_sem_casar,
            descartados_dado_ausente=criterios.descartados_dado_ausente,
            descartados_retirados=criterios.descartados_retirados,
            descartados_acima_km=criterios.descartados_acima_km,
        )

        busca_ids = list(dict.fromkeys(r.busca_id for r in resultados))
        semeadas = {b for b in busca_ids if self.repo.busca_semeada(b)}
        saida.buscas_a_semear = [b for b in busca_ids if b not in semeadas and b in buscas_aptas]

        unicos: dict[str, Candidato] = {}
        for candidato in criterios.candidatos:
            unicos.setdefault(candidato.lote.id_canonico, candidato)
        saida.candidatos = len(unicos)
        conhecidos = self.repo.conhecidos(unicos)

        for id_canonico, candidato in unicos.items():
            busca = candidato.lote.busca_id
            if id_canonico in conhecidos:
                saida.ja_conhecidos += 1
            elif busca in semeadas:
                saida.novos.append(candidato)
            elif busca in saida.buscas_a_semear:
                saida.semeaveis.append(candidato)
            # Busca não semeada e não apta: fica de fora até uma execução saudável semeá-la.
        return saida

    def registrar_semeadura(self, resultado: ResultadoFiltragem, execucao_id: str, agora: datetime) -> int:
        gravados = self.repo.registrar(_registro(c, "semeadura", agora) for c in resultado.semeaveis)
        for busca_id in resultado.buscas_a_semear:
            self.repo.marcar_semeada(busca_id, execucao_id, agora)
        return gravados

    def confirmar_notificacao(self, novos: Iterable[Candidato], agora: datetime) -> int:
        """Só depois da confirmação do Telegram (RN-06), numa transação única."""
        return self.repo.registrar(_registro(c, "notificacao", agora) for c in novos)
