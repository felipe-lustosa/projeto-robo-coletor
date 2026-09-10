"""Testes de fluxo: pedido, Observer, transição de modo e undo (Seção 2.7)."""

import json
from pathlib import Path

import pytest

from celular_robo.robo import RoboColetor
from celular_robo.estrategias import RotaDireta, RotaComDuplaConferencia
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
    novo = ComandoColeta("Projeto Boreal", (2, 2), 1)
    with pytest.raises(ColetaBloqueada):
        novo.executar(robo)
    assert robo.bandeja == bandeja_antes

    robo.modo = ModoColetando()
    novo.executar(robo)
    assert robo.bandeja["Projeto Boreal"] == 1


def test_rota_nao_deposita_item_que_o_robo_nao_alcancou():
    """Um obstáculo no caminho interrompe avancar_n; a rota precisa recusar
    a coleta em vez de depositar um item que nunca foi pego."""
    robo = _robo_de_exemplo()
    robo.obstaculos = {(0, 3): "equipamento", (1, 3): "equipamento"}

    comando = ComandoColeta("Projeto Boreal", (0, 5), 1)
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


def test_pedido_rejeitado_e_registrado_pela_auditoria():
    """Seção 2.3: a coleta recusada vira "pedido_rejeitado" no modelo, não na
    CLI — é assim que a auditoria enxerga a rejeição."""
    robo = _robo_de_exemplo()
    auditoria = RegistroAuditoria()
    robo.adicionar_observador(auditoria)
    robo.obstaculos = {(1, 0): "equipamento", (0, 1): "equipamento"}
    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))

    indice, erro = robo.processar_pedido(pedido)

    assert isinstance(erro, ColetaBloqueada)
    assert indice == 0
    assert robo.bandeja == {}
    rejeicoes = [dados for evento, dados in auditoria.eventos
                 if evento == "pedido_rejeitado"]
    assert len(rejeicoes) == 1
    assert rejeicoes[0]["codinome"] == pedido.comandos[0].codinome


def test_processar_pedido_completo_avisa_a_equipe():
    """Sem falha, processar_pedido vai até o fim e confere a bandeja sozinho."""
    robo = _robo_de_exemplo()
    equipe = EquipeDeTestes()
    robo.adicionar_observador(equipe)
    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))

    indice, erro = robo.processar_pedido(pedido)

    assert erro is None
    assert indice == len(pedido.comandos)
    assert equipe.bandeja_pronta is True
    assert isinstance(robo.modo, ModoAguardandoVerificacao)


def test_rejeitar_lote_volta_a_coletando_mantendo_a_bandeja():
    """Seção 2.3: rejeitado, o robô volta ao mesmo pedido com os itens já
    coletados, e a rejeição fica registrada."""
    robo = _robo_de_exemplo()
    auditoria = RegistroAuditoria()
    robo.adicionar_observador(auditoria)
    robo.adicionar_observador(EquipeDeTestes())
    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))
    robo.processar_pedido(pedido)
    assert isinstance(robo.modo, ModoAguardandoVerificacao)
    bandeja_antes = dict(robo.bandeja)

    robo.rejeitar_lote("rejeitado pela equipe")

    assert isinstance(robo.modo, ModoColetando)
    assert robo.bandeja == bandeja_antes
    assert "pedido_rejeitado" in [evento for evento, _ in auditoria.eventos]


def test_aprovar_lote_libera_a_bandeja():
    """Aprovado, o lote sai da bandeja e o robô volta a poder coletar."""
    robo = _robo_de_exemplo()
    robo.adicionar_observador(EquipeDeTestes())
    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))
    robo.processar_pedido(pedido)

    robo.aprovar_lote()

    assert robo.bandeja == {}
    assert len(robo) == 0
    assert isinstance(robo.modo, ModoColetando)


def test_rota_com_dupla_conferencia_registra_a_revalidacao_na_auditoria():
    """A segunda conferência da rota lenta é visível: emite
    "item_revalidado" antes de "item_coletado". A RotaDireta não emite."""
    lenta = RoboColetor(
        "Coletor-Lento", estrategia=RotaComDuplaConferencia(), modo=ModoColetando()
    )
    auditoria = RegistroAuditoria()
    lenta.adicionar_observador(auditoria)
    ComandoColeta("Projeto Boreal", (2, 3), 1).executar(lenta)

    eventos = [evento for evento, _ in auditoria.eventos]
    assert eventos == ["item_revalidado", "item_coletado"]
    revalidacao = auditoria.eventos[0][1]
    assert revalidacao["codinome"] == "Projeto Boreal"
    assert revalidacao["posicao"] == (2, 3)

    rapida = RoboColetor(
        "Coletor-Rapido", estrategia=RotaDireta(), modo=ModoColetando()
    )
    auditoria_rapida = RegistroAuditoria()
    rapida.adicionar_observador(auditoria_rapida)
    ComandoColeta("Projeto Boreal", (2, 3), 1).executar(rapida)
    assert [evento for evento, _ in auditoria_rapida.eventos] == ["item_coletado"]


def test_desfazer_comando_nunca_executado_nao_notifica():
    """Undo sem coleta anterior não mexe na bandeja nem suja a auditoria."""
    robo = _robo_de_exemplo()
    auditoria = RegistroAuditoria()
    robo.adicionar_observador(auditoria)
    comando = ComandoColeta("Projeto Boreal", (2, 2), 1)

    assert comando.desfazer(robo) is False
    assert robo.bandeja == {}
    assert auditoria.eventos == []

    comando.executar(robo)
    assert comando.desfazer(robo) is True
    assert robo.bandeja == {}
    assert [evento for evento, _ in auditoria.eventos][-1] == "coleta_desfeita"
