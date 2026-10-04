"""Aviso de coerência entre alvos e buscas (audit A004; interfaces/arquivos-configuracao.md §2)."""

from apoio import alvo
from bot_leilao.config.coerencia import verificar_coerencia
from bot_leilao.config.leiloeiros import Busca, Leiloeiro


def _leiloeiro(*buscas):
    return Leiloeiro(id="vip-leiloes", nome="Vip Leilões", base_url="https://www.vipleiloes.com.br", ativo=True,
                     estrategia_acesso="publico", credencial_env=None, nivel_coleta="script",
                     frequencia="seg-qua-sex-08h",
                     buscas=tuple(Busca(id=f"vip-leiloes:{d}", leiloeiro_id="vip-leiloes", descricao=d, filtros=f)
                                  for d, f in buscas))


AMPLA = ("Ampla", {"procedencia": 4, "monta": 1})


def _tipo(leiloeiro, busca):
    return {"4": "financiamento"}.get(str(busca.filtros.get("procedencia")))


def test_alvo_coerente_nao_gera_aviso():
    assert verificar_coerencia([alvo(tipos_leilao=("financiamento", "seguradora"))], [_leiloeiro(AMPLA)], _tipo) == []


def test_alvo_que_nunca_casa_gera_aviso_citando_tipos():
    avisos = verificar_coerencia([alvo(marca="Toyota", modelo="Corolla", tipos_leilao=("seguradora",))],
                                 [_leiloeiro(AMPLA)], _tipo)
    (aviso,) = avisos
    assert "Toyota Corolla" in aviso
    assert "seguradora" in aviso
    assert "financiamento" in aviso


def test_busca_sem_tipo_gera_aviso_proprio():
    """Lote com tipo nulo não casa com alvo nenhum (motor RF-05)."""
    avisos = verificar_coerencia([alvo()], [_leiloeiro(AMPLA, ("Sem procedência", {"monta": 1}))], _tipo)
    assert any("Sem procedência" in a for a in avisos)


def test_alvos_inativos_sao_ignorados():
    assert verificar_coerencia([alvo(tipos_leilao=("seguradora",), ativo=False)], [_leiloeiro(AMPLA)], _tipo) == []


def test_sem_alvos_ou_sem_leiloeiros_nao_avisa():
    assert verificar_coerencia([], [_leiloeiro(AMPLA)], _tipo) == []
    assert verificar_coerencia([alvo()], [], _tipo) == []


def test_nunca_levanta():
    def explode(leiloeiro, busca):
        raise RuntimeError("adaptador com bug")

    avisos = verificar_coerencia([alvo()], [_leiloeiro(AMPLA)], explode)
    assert avisos and "adaptador com bug" in avisos[0]
