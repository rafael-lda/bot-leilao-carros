"""Leitura segura de YAML e arquivos de exemplo (EC-01, EC-02, EC-08 das specs de config)."""

import pytest
import yaml

from bot_leilao.config.arquivos import (
    EXEMPLO_LEILOEIROS,
    EXEMPLO_VEICULOS,
    ConfiguracaoAusente,
    ErroConfiguracao,
    garantir_arquivo,
    ler_yaml,
)


def test_le_yaml_utf8(tmp_path):
    caminho = tmp_path / "a.yaml"
    caminho.write_text("marca: Citroën\n", encoding="utf-8")
    assert ler_yaml(caminho) == {"marca": "Citroën"}


def test_aceita_fim_de_linha_crlf(tmp_path):
    caminho = tmp_path / "a.yaml"
    caminho.write_bytes(b"veiculos:\r\n  - marca: Nissan\r\n")
    assert ler_yaml(caminho) == {"veiculos": [{"marca": "Nissan"}]}


def test_bom_e_rejeitado_citando_o_encoding(tmp_path):
    caminho = tmp_path / "a.yaml"
    caminho.write_bytes("﻿marca: Nissan\n".encode("utf-8"))
    with pytest.raises(ErroConfiguracao) as erro:
        ler_yaml(caminho)
    assert "BOM" in str(erro.value)
    assert "UTF-8" in str(erro.value)


def test_encoding_diferente_de_utf8_e_rejeitado(tmp_path):
    caminho = tmp_path / "a.yaml"
    caminho.write_bytes("marca: Citroën\n".encode("latin-1"))
    with pytest.raises(ErroConfiguracao) as erro:
        ler_yaml(caminho)
    assert "UTF-8" in str(erro.value)


def test_sintaxe_invalida_cita_a_linha(tmp_path):
    caminho = tmp_path / "a.yaml"
    caminho.write_text("veiculos:\n  - marca: Nissan\n   modelo: [Versa\n", encoding="utf-8")
    with pytest.raises(ErroConfiguracao) as erro:
        ler_yaml(caminho)
    assert "linha" in str(erro.value)
    assert str(caminho.name) in str(erro.value)


def test_arquivo_ausente_cria_exemplo_e_aborta(tmp_path):
    caminho = tmp_path / "config" / "veiculos-alvo.yaml"
    with pytest.raises(ConfiguracaoAusente) as erro:
        garantir_arquivo(caminho, EXEMPLO_VEICULOS)
    assert caminho.exists()
    assert erro.value.caminho == caminho
    assert caminho.read_text(encoding="utf-8") == EXEMPLO_VEICULOS


def test_arquivo_existente_nunca_e_reescrito(tmp_path):
    caminho = tmp_path / "veiculos-alvo.yaml"
    caminho.write_text("meu conteúdo\n", encoding="utf-8")
    garantir_arquivo(caminho, EXEMPLO_VEICULOS)
    assert caminho.read_text(encoding="utf-8") == "meu conteúdo\n"


def test_exemplo_de_veiculos_segue_o_contrato():
    dados = yaml.safe_load(EXEMPLO_VEICULOS)
    alvos = dados["veiculos"]
    assert alvos and all(a["ativo"] is False for a in alvos)
    assert all("financiamento" in a["tipos_leilao"] for a in alvos)
    assert "ANO DE MODELO" in EXEMPLO_VEICULOS
    assert "LANCE CORRENTE" in EXEMPLO_VEICULOS
    assert "quilometragem_maxima" in EXEMPLO_VEICULOS


def test_exemplo_de_leiloeiros_traz_a_busca_ampla_do_vip():
    dados = yaml.safe_load(EXEMPLO_LEILOEIROS)
    vip = dados["leiloeiros"][0]
    assert vip["nome"] == "Vip Leilões"
    assert vip["ativo"] is False
    assert vip["estrategia_acesso"] == "publico"
    assert vip["nivel_coleta"] == "script"
    filtros = vip["buscas"][0]["filtros"]
    assert filtros == {"procedencia": 4, "monta": 1}, "busca ampla, sem marca (D-29)"
    assert "credencial_env" not in vip
