# TODO: teste da transição ModoColetando -> ModoAguardandoVerificacao
# disparada pelo Observer quando a bandeja completa — enunciado, Seção 2.7.

import json
from pathlib import Path

from celular_robo.robo import RoboColetor
from celular_robo.estrategias import RotaDireta
from celular_robo.observadores import EquipeDeTestes
from celular_robo.modos import ModoColetando, ModoAguardandoVerificacao
from celular_robo.persistencia import montar_robo_de_config, montar_pedido_de_json

DADOS = Path(__file__).resolve().parent.parent / "dados"

def test_transicao_modo_via_observer_ao_notificar_bandeja_pronta():
    robo = RoboColetor("Coletor-Teste", estrategia=RotaDireta(), modo=ModoColetando())
    equipe = EquipeDeTestes()
    robo.adicionar_observador(equipe)

    assert isinstance(robo.modo, ModoColetando)

    robo.notificar("bandeja_pronta")

    assert equipe.bandeja_pronta is True
    assert isinstance(robo.modo, ModoAguardandoVerificacao)


def test_fluxo_completo_pedido_ate_bandeja_pronta():
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