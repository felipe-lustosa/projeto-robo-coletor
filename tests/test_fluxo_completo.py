"""Testes de fluxo: pedido, Observer, transição de modo e undo (Seção 2.7)."""

import json
from pathlib import Path

import pytest

from celular_robo.robo import RoboColetor
from celular_robo.estrategias import RotaDireta
from celular_robo.observadores import EquipeDeTestes, RegistroAuditoria
from celular_robo.modos import ModoColetando, ModoAguardandoVerificacao
from celular_robo.comandos import ComandoColeta
from celular_robo.excecoes import ColetaBloqueada
from celular_robo.persistencia import montar_robo_de_config, montar_pedido_de_json

DADOS = Path(__file__).resolve().parent.parent / "dados"

def test_transicao_modo_via_observer_ao_notificar_bandeja_pronta():
    """É o Observer que troca o modo quando a bandeja fica pronta."""
    robo = RoboColetor("Coletor-Teste", estrategia=RotaDireta(), modo=ModoColetando())
    equipe = EquipeDeTestes()
    robo.adicionar_observador(equipe)

    assert isinstance(robo.modo, ModoColetando)

    robo.notificar("bandeja_pronta")

    assert equipe.bandeja_pronta is True
    assert isinstance(robo.modo, ModoAguardandoVerificacao)


def test_fluxo_completo_pedido_ate_bandeja_pronta():
    """Do JSON de config e pedido até a bandeja pronta."""
    config = json.loads((DADOS / "config_robo_exemplo.json").read_text(encoding="utf-8"))
    robo = montar_robo_de_config(config)
    equipe = EquipeDeTestes()
    robo.adicionar_observador(equipe)

    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))
    for comando in pedido.comandos:
        comando.executar(robo)

    total_pedido = sum(comando.quantidade for comando in pedido.comandos)
    assert len(robo) == total_pedido

    robo.notificar("bandeja_pronta")
    assert isinstance(robo.modo, ModoAguardandoVerificacao)


def test_auditoria_loga_coleta_e_pedido_guarda_historico():
    """A auditoria loga cada coleta e o histórico guarda os comandos."""
    config = json.loads((DADOS / "config_robo_exemplo.json").read_text(encoding="utf-8"))
    robo = montar_robo_de_config(config)
    auditoria = RegistroAuditoria()
    robo.adicionar_observador(auditoria)

    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))
    for comando in pedido.comandos:
        comando.executar(robo)

    coletados = [dados["codinome"] for evento, dados in auditoria.eventos
                 if evento == "item_coletado"]
    assert coletados == [comando.codinome for comando in pedido.comandos]
    assert robo.historico == tuple(pedido.comandos)


def test_desfazer_remove_da_bandeja_e_do_historico():
    """desfazer devolve bandeja e histórico ao estado anterior à coleta."""
    config = json.loads((DADOS / "config_robo_exemplo.json").read_text(encoding="utf-8"))
    robo = montar_robo_de_config(config)
    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))

    primeiro = pedido.comandos[0]
    primeiro.executar(robo)
    assert len(robo) == primeiro.quantidade
    assert robo.historico == (primeiro,)

    primeiro.desfazer(robo)
    assert len(robo) == 0
    assert robo.historico == ()
    assert primeiro.quantidade_coletada == 0


def _robo_de_exemplo():
    config = json.loads((DADOS / "config_robo_exemplo.json").read_text(encoding="utf-8"))
    return montar_robo_de_config(config)


def test_robo_confere_a_bandeja_e_avisa_a_equipe_sozinho():
    """Seção 1: é o robô que notifica quando a bandeja completa — a CLI só
    chama conferir_bandeja, não decide nem notifica no lugar dele."""
    robo = _robo_de_exemplo()
    equipe = EquipeDeTestes()
    robo.adicionar_observador(equipe)
    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))

    primeiro, *restantes = pedido.comandos
    primeiro.executar(robo)
    assert robo.conferir_bandeja(pedido) is False
    assert equipe.bandeja_pronta is False
    assert isinstance(robo.modo, ModoColetando)

    for comando in restantes:
        comando.executar(robo)

    assert robo.conferir_bandeja(pedido) is True
    assert equipe.bandeja_pronta is True
    assert isinstance(robo.modo, ModoAguardandoVerificacao)


def test_modo_aguardando_verificacao_recusa_nova_coleta():
    """Seção 2.3: o modo recusa iniciar nova coleta até a equipe aprovar —
    a regra vive no State, não só na CLI."""
    robo = _robo_de_exemplo()
    robo.adicionar_observador(EquipeDeTestes())
    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))
    for comando in pedido.comandos:
        comando.executar(robo)
    robo.conferir_bandeja(pedido)
    assert isinstance(robo.modo, ModoAguardandoVerificacao)

    bandeja_antes = dict(robo.bandeja)
    novo = ComandoColeta("Projeto 03", (2, 2), 1)
    with pytest.raises(ColetaBloqueada):
        novo.executar(robo)
    assert robo.bandeja == bandeja_antes

    robo.modo = ModoColetando()
    novo.executar(robo)
    assert robo.bandeja["Projeto 03"] == 1


def test_rota_nao_deposita_item_que_o_robo_nao_alcancou():
    """Um obstáculo no caminho interrompe avancar_n; a rota precisa recusar
    a coleta em vez de depositar um item que nunca foi pego."""
    robo = _robo_de_exemplo()
    robo.obstaculos = {(0, 3): "equipamento", (1, 3): "equipamento"}

    comando = ComandoColeta("Projeto 03", (0, 5), 1)
    with pytest.raises(ColetaBloqueada):
        comando.executar(robo)

    assert robo.posicao != (0, 5)
    assert robo.bandeja == {}
    assert comando.quantidade_coletada == 0
    assert robo.historico == ()


def test_robo_com_bandeja_vazia_continua_verdadeiro():
    """__len__ soma a bandeja, então sem __bool__ o robô ficaria falsy —
    e `if robo:` passaria a significar "bandeja vazia"."""
    robo = _robo_de_exemplo()
    assert len(robo) == 0
    assert bool(robo) is True
