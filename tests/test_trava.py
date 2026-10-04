"""Trava de execução (RF-15 da feature; agendador-observabilidade RF-02 e EC-01; roadmap D-07)."""

import json
from datetime import timedelta

import pytest

from bot_leilao.db.trava import Trava, TravaOcupada


def test_primeira_adquire_e_segunda_e_recusada(tmp_path, agora):
    caminho = tmp_path / "varredura.lock"
    primeira = Trava(caminho, agora=agora)
    segunda = Trava(caminho, agora=agora)
    assert primeira.adquirir() is True
    assert segunda.adquirir() is False
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    assert {"pid", "adquirida_em"} <= set(conteudo)


def test_liberar_permite_nova_aquisicao(tmp_path, agora):
    caminho = tmp_path / "varredura.lock"
    primeira = Trava(caminho, agora=agora)
    primeira.adquirir()
    primeira.liberar()
    assert not caminho.exists()
    assert Trava(caminho, agora=agora).adquirir() is True


def test_trava_com_mais_de_duas_horas_e_orfa(tmp_path, agora):
    caminho = tmp_path / "varredura.lock"
    Trava(caminho, agora=agora).adquirir()
    agora.avancar(hours=2, minutes=1)
    nova = Trava(caminho, agora=agora)
    assert nova.adquirir() is True
    assert nova.orfa_liberada is True


def test_trava_recente_nao_e_orfa(tmp_path, agora):
    caminho = tmp_path / "varredura.lock"
    Trava(caminho, agora=agora).adquirir()
    agora.avancar(hours=1, minutes=59)
    assert Trava(caminho, agora=agora).adquirir() is False


def test_trava_ilegivel_e_tratada_como_orfa(tmp_path, agora):
    caminho = tmp_path / "varredura.lock"
    caminho.write_text("lixo", encoding="utf-8")
    trava = Trava(caminho, agora=agora, orfa_apos=timedelta(hours=2))
    assert trava.adquirir() is True
    assert trava.orfa_liberada is True


def test_context_manager_libera_mesmo_com_excecao(tmp_path, agora):
    caminho = tmp_path / "varredura.lock"
    with pytest.raises(RuntimeError):
        with Trava(caminho, agora=agora):
            assert caminho.exists()
            raise RuntimeError("falha no meio da execução")
    assert not caminho.exists()


def test_context_manager_ocupado_levanta(tmp_path, agora):
    caminho = tmp_path / "varredura.lock"
    Trava(caminho, agora=agora).adquirir()
    with pytest.raises(TravaOcupada):
        with Trava(caminho, agora=agora):
            pass
    assert caminho.exists(), "quem não adquiriu não pode apagar a trava alheia"
