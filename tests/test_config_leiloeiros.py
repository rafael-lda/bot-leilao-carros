"""cadastro-leiloeiros v1.3 + RF-02 da feature + roadmap D-12, D-17, D-18, D-24."""

import pytest

from apoio import escrever
from bot_leilao.config.arquivos import ConfiguracaoAusente, ErroConfiguracao
from bot_leilao.config.leiloeiros import FREQUENCIA_PADRAO, carregar_leiloeiros, id_busca


class AdaptadorFalso:
    leiloeiro_id = "vip-leiloes"
    CHAVES = {"procedencia", "monta", "marca"}

    def validar_filtros(self, filtros):
        desconhecidas = set(filtros) - self.CHAVES
        if desconhecidas:
            raise ValueError(f"chave de filtro desconhecida: {sorted(desconhecidas)[0]}")


ADAPTADORES = {"vip-leiloes": AdaptadorFalso()}
PARSERS = {"vip-leiloes"}

VALIDO = """
leiloeiros:
  - nome: Vip Leilões
    base_url: https://www.vipleiloes.com.br
    ativo: true
    estrategia_acesso: publico
    nivel_coleta: script
    buscas:
      - descricao: Recuperados de financiamento, conservados
        filtros:
          procedencia: 4
          monta: 1
"""


def _yaml(**sobrescritas):
    campos = dict(nome="Vip Leilões", base_url="https://www.vipleiloes.com.br", ativo="true",
                  estrategia_acesso="publico", nivel_coleta="script", credencial_env=None, frequencia=None)
    campos.update(sobrescritas)
    buscas = campos.pop("buscas", "      - descricao: Ampla\n        filtros:\n          procedencia: 4\n          monta: 1\n")
    linhas = ["leiloeiros:"]
    primeiro = True
    for chave, valor in campos.items():
        if valor is None:
            continue
        prefixo = "  - " if primeiro else "    "
        linhas.append(f"{prefixo}{chave}: {valor}")
        primeiro = False
    texto = "\n".join(linhas) + "\n"
    if buscas is not None:
        texto += "    buscas:\n" + buscas
    return texto


def _carregar(raiz, texto, adaptadores=ADAPTADORES, parsers=PARSERS):
    caminho = escrever(raiz / "config" / "leiloeiros.yaml", texto)
    return carregar_leiloeiros(caminho, adaptadores, parsers)


def test_carrega_leiloeiro_valido(raiz):
    resultado = _carregar(raiz, VALIDO)
    (vip,) = resultado.ativos
    assert vip.id == "vip-leiloes"
    assert vip.nome == "Vip Leilões"
    assert vip.nivel_coleta == "script"
    assert vip.frequencia == FREQUENCIA_PADRAO
    (busca,) = vip.buscas
    assert busca.filtros == {"procedencia": 4, "monta": 1}
    assert busca.leiloeiro_id == "vip-leiloes"
    assert busca.id.startswith("vip-leiloes:")


def test_rf02_busca_com_tres_filtros_acessiveis(raiz):
    buscas = "      - descricao: Nissan\n        filtros:\n          marca: NISSAN\n          procedencia: 4\n          monta: 1\n"
    (vip,) = _carregar(raiz, _yaml(buscas=buscas)).ativos
    assert vip.buscas[0].filtros == {"marca": "NISSAN", "procedencia": 4, "monta": 1}


def test_id_da_busca_independe_da_ordem_das_chaves():
    assert id_busca("vip-leiloes", {"procedencia": 4, "monta": 1}) == id_busca("vip-leiloes", {"monta": 1, "procedencia": 4})
    assert id_busca("vip-leiloes", {"procedencia": 4}) != id_busca("vip-leiloes", {"procedencia": 5})


def test_id_da_busca_e_estavel_entre_carregamentos(raiz):
    assert _carregar(raiz, VALIDO).ativos[0].buscas[0].id == _carregar(raiz, VALIDO).ativos[0].buscas[0].id


def test_busca_sem_filtros_e_rejeitada_citando_leiloeiro_e_busca(raiz):
    buscas = "      - descricao: Esquecida\n        filtros: {}\n"
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(buscas=buscas))
    assert "Vip Leilões" in str(erro.value)
    assert "Esquecida" in str(erro.value)


def test_filtro_com_valor_aninhado_e_rejeitado(raiz):
    buscas = "      - descricao: Aninhada\n        filtros:\n          procedencia: {codigo: 4}\n"
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(buscas=buscas))
    assert "procedencia" in str(erro.value)


def test_filtro_com_lista_vazia_e_rejeitado(raiz):
    buscas = "      - descricao: Lista\n        filtros:\n          procedencia: []\n"
    with pytest.raises(ErroConfiguracao):
        _carregar(raiz, _yaml(buscas=buscas))


def test_leiloeiro_sem_buscas_e_rejeitado(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(buscas=None))
    assert "Vip Leilões" in str(erro.value)


@pytest.mark.parametrize("url", ["http://www.vipleiloes.com.br", "/busca", "www.vipleiloes.com.br"])
def test_base_url_sem_https_absoluta_e_rejeitada(raiz, url):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(base_url=url))
    assert "Vip Leilões" in str(erro.value)
    assert url in str(erro.value)


def test_chave_de_filtro_desconhecida_aborta_antes_da_rede(raiz):
    buscas = "      - descricao: Errada\n        filtros:\n          cor: azul\n"
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(buscas=buscas))
    assert "cor" in str(erro.value)
    assert "Errada" in str(erro.value)


def test_leiloeiro_ativo_sem_adaptador_lista_os_disponiveis(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(nome="Leilão Novo"))
    mensagem = str(erro.value)
    assert "Leilão Novo" in mensagem
    assert "adaptador" in mensagem
    assert "vip-leiloes" in mensagem


def test_leiloeiro_ativo_sem_parser_e_rejeitado(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, VALIDO, parsers=set())
    assert "parser" in str(erro.value)


def test_leiloeiro_inativo_sem_adaptador_carrega(raiz):
    resultado = _carregar(raiz, _yaml(nome="Leilão Novo", ativo="false"))
    assert resultado.ativos == []
    assert resultado.inativos == 1


def test_logado_exige_credencial_env(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(estrategia_acesso="logado", ativo="false"))
    assert "credencial_env" in str(erro.value)


def test_logado_ativo_nao_implementado_nesta_versao(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(estrategia_acesso="logado", credencial_env="VIP_LOGIN"))
    assert "não implementado" in str(erro.value)


def test_nivel_apify_residencial_ainda_nao_implementado(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(nivel_coleta="apify_residencial"))
    assert "não implementado" in str(erro.value)


# --- Feature 005: nível apify, intervalo e ator (D-88, D-90, D-101) ---------------------------------


def test_nivel_apify_implementado_com_ator_padrao_e_sem_intervalo(raiz):
    (vip,) = _carregar(raiz, _yaml(nivel_coleta="apify")).ativos
    assert vip.nivel_coleta == "apify"
    assert vip.apify_ator is None, "ausente = ator padrão do cliente Apify"
    assert vip.intervalo_horas is None


@pytest.mark.parametrize("valor, esperado", [("1", 1), ("72", 72), ("720", 720)])
def test_intervalo_horas_aceito(raiz, valor, esperado):
    (vip,) = _carregar(raiz, _yaml(intervalo_horas=valor)).ativos
    assert vip.intervalo_horas == esperado


@pytest.mark.parametrize("valor", ["0", "-5", "721", "3.5", "tres", "true", "''"])
def test_intervalo_horas_invalido_cita_o_campo_e_a_faixa(raiz, valor):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(intervalo_horas=valor))
    assert "intervalo_horas" in str(erro.value)
    assert "1 e 720" in str(erro.value)


def test_apify_ator_conhecido(raiz):
    (vip,) = _carregar(raiz, _yaml(nivel_coleta="apify", apify_ator="neatrat/cloudflare-scraper")).ativos
    assert vip.apify_ator == "neatrat/cloudflare-scraper"


def test_apify_ator_sem_perfil_lista_os_conhecidos(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(nivel_coleta="apify", apify_ator="alguem/outro-ator"))
    assert "alguem/outro-ator" in str(erro.value)
    assert "neatrat/cloudflare-scraper" in str(erro.value)


def test_apify_ator_so_vale_com_nivel_apify(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(apify_ator="neatrat/cloudflare-scraper"))
    assert "apify_ator" in str(erro.value)
    assert "nivel_coleta: apify" in str(erro.value)


def test_nivel_omitido_vale_script(raiz):
    (vip,) = _carregar(raiz, _yaml(nivel_coleta=None)).ativos
    assert vip.nivel_coleta == "script"


def test_nivel_fora_do_conjunto_lista_os_tres(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(nivel_coleta="apify-residencial"))
    for nivel in ("script", "apify", "apify_residencial"):
        assert nivel in str(erro.value)


def test_estrategia_invalida_e_rejeitada(raiz):
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(estrategia_acesso="aberto"))
    assert "estrategia_acesso" in str(erro.value)


def test_senha_no_lugar_do_nome_da_variavel_e_erro_de_seguranca(raiz):
    """EC-04: o campo guarda só o nome da variável."""
    with pytest.raises(ErroConfiguracao) as erro:
        _carregar(raiz, _yaml(estrategia_acesso="logado", credencial_env='"minhaSenha#2026"', ativo="false"))
    assert ".env" in str(erro.value)
    assert "minhaSenha#2026" not in str(erro.value)


def test_frequencia_e_aceita_como_texto_opaco(raiz):
    """D-18: sem validação nesta feature."""
    (vip,) = _carregar(raiz, _yaml(frequencia='"qualquer coisa"')).ativos
    assert vip.frequencia == "qualquer coisa"


def test_busca_duplicada_gera_aviso_e_mantem_a_primeira(raiz):
    buscas = ("      - descricao: Primeira\n        filtros:\n          procedencia: 4\n          monta: 1\n"
              "      - descricao: Segunda\n        filtros:\n          monta: 1\n          procedencia: 4\n")
    resultado = _carregar(raiz, _yaml(buscas=buscas))
    (vip,) = resultado.ativos
    assert [b.descricao for b in vip.buscas] == ["Primeira"]
    assert any("duplicada" in aviso for aviso in resultado.avisos)


def test_dois_leiloeiros_com_o_mesmo_id_sao_rejeitados(raiz):
    texto = VALIDO + VALIDO.replace("leiloeiros:\n", "")
    with pytest.raises(ErroConfiguracao):
        _carregar(raiz, texto)


def test_nenhum_leiloeiro_ativo_gera_aviso(raiz):
    resultado = _carregar(raiz, _yaml(ativo="false"))
    assert any("Nenhum leiloeiro ativo" in aviso for aviso in resultado.avisos)


def test_arquivo_ausente_cria_exemplo(raiz):
    with pytest.raises(ConfiguracaoAusente):
        carregar_leiloeiros(raiz / "config" / "leiloeiros.yaml", ADAPTADORES, PARSERS)
    assert (raiz / "config" / "leiloeiros.yaml").exists()
