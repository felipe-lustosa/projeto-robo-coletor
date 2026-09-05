"""Testes de fluxo: pedido, Observer, transição de modo e undo (Seção 2.7)."""

import json
from pathlib import Path

from celular_robo.robo import RoboColetor
from celular_robo.estrategias import RotaDireta
from celular_robo.observadores import EquipeDeTestes, RegistroAuditoria
from celular_robo.modos import ModoColetando, ModoAguardandoVerificacao
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
