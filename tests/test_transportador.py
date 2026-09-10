"""Testes da extensão RoboTransportador: registro, excludes e handoff (Seção 7)."""

import json
from pathlib import Path

import pytest

from celular_robo.robo_base import Robo
from celular_robo.transportador import RoboTransportador
from celular_robo.fabrica import criar_robo_configurado
from celular_robo.modelo_features import TIPOS_VALIDOS
from celular_robo.modos import (
    ModoAguardandoCarga,
    ModoColetando,
    ModoTransportando,
)
from celular_robo.observadores import (
    DespachoTransporte,
    EquipeDeTestes,
    RegistroAuditoria,
)
from celular_robo.excecoes import ConfiguracaoInvalida, TransporteBloqueado
from celular_robo.persistencia import montar_robo_de_config, montar_pedido_de_json

DADOS = Path(__file__).resolve().parent.parent / "dados"


def _coletor_com_despacho(area_transporte="centro_padrao"):
    """Coletor de exemplo já observado pela equipe, auditoria e despacho."""
    config = json.loads((DADOS / "config_robo_exemplo.json").read_text(encoding="utf-8"))
    coletor = montar_robo_de_config(config)
    auditoria = RegistroAuditoria()
    despacho = DespachoTransporte(area_nome=area_transporte, observadores=[auditoria])
    coletor.adicionar_observador(EquipeDeTestes())
    coletor.adicionar_observador(auditoria)
    coletor.adicionar_observador(despacho)
    return coletor, despacho, auditoria


def _transportador(area_nome="centro_padrao", estrategia_nome="direta"):
    return criar_robo_configurado(
        "RoboTransportador", "Transportador-Teste",
        estrategia_nome=estrategia_nome, area_nome=area_nome,
    )


def test_novo_tipo_entra_sozinho_no_registro_e_em_tipos_validos():
    """Seção 7: herdar de Robo basta — nada em TIPOS_VALIDOS foi digitado."""
    assert Robo._registro["RoboTransportador"] is RoboTransportador
    assert {"RoboColetor", "RoboTransportador"} <= TIPOS_VALIDOS
    assert RoboTransportador.categoria == "logistica"


def test_transportador_exclui_area_quarentena():
    """Restrição nova de excludes: o transportador não entra na quarentena."""
    with pytest.raises(ConfiguracaoInvalida):
        criar_robo_configurado(
            "RoboTransportador", "Transportador-1",
            estrategia_nome="com_dupla_conferencia", area_nome="area_quarentena",
        )


def test_coletor_continua_aceitando_area_quarentena():
    """O excludes novo vale só pro transportador — o coletor não regrediu."""
    coletor = criar_robo_configurado(
        "RoboColetor", "Coletor-1",
        estrategia_nome="com_dupla_conferencia", area_nome="area_quarentena",
    )
    assert isinstance(coletor.modo, ModoColetando)
    assert len(coletor.obstaculos) >= 1


def test_transportador_sem_carga_recusa_transportar():
    """State: ModoAguardandoCarga recusa o transporte antes do lote chegar."""
    transportador = _transportador()
    assert isinstance(transportador.modo, ModoAguardandoCarga)

    with pytest.raises(TransporteBloqueado):
        transportador.transportar()

    assert transportador.posicao == (0, 0)
    assert transportador.entregues == {}


def test_carregar_troca_o_modo_e_entregar_devolve_ao_inicial():
    """Ciclo de estados: aguardando carga -> transportando -> aguardando."""
    transportador = _transportador()

    transportador.carregar({"Projeto 01": 2})
    assert isinstance(transportador.modo, ModoTransportando)
    assert len(transportador) == 2

    entregues = transportador.transportar()

    assert entregues == {"Projeto 01": 2}
    assert transportador.posicao == RoboTransportador.PONTO_RETIRADA
    assert transportador.carga == {}
    assert len(transportador) == 0
    assert isinstance(transportador.modo, ModoAguardandoCarga)


def test_handoff_coletor_para_transportador_ao_aprovar_o_lote():
    """Seção 7: aprovar a bandeja despacha o lote até o ponto de retirada."""
    coletor, despacho, auditoria = _coletor_com_despacho()
    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))
    coletor.processar_pedido(pedido)
    esperado = dict(coletor.bandeja)

    coletor.aprovar_lote()

    transportador = despacho.transportador
    assert isinstance(transportador, RoboTransportador)
    assert despacho.entregas == [esperado]
    assert transportador.entregues == esperado
    assert transportador.posicao == RoboTransportador.PONTO_RETIRADA
    assert coletor.bandeja == {}
    assert isinstance(coletor.modo, ModoColetando)

    eventos = [evento for evento, _ in auditoria.eventos]
    assert eventos[-3:] == ["lote_aprovado", "carga_recebida", "lote_entregue"]


def test_despacho_registra_recusa_do_modelo_de_features():
    """Configuração recusada vira evento auditado, sem quebrar a notificação."""
    coletor, despacho, auditoria = _coletor_com_despacho(
        area_transporte="area_quarentena"
    )
    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))
    coletor.processar_pedido(pedido)

    coletor.aprovar_lote()

    assert despacho.transportador is None
    assert despacho.entregas == []
    recusas = [dados for evento, dados in auditoria.eventos
               if evento == "transporte_recusado"]
    assert len(recusas) == 1
    assert "area_quarentena" in recusas[0]["motivo"]


def test_despacho_registra_transporte_bloqueado_por_obstaculo():
    """Ponto de retirada inalcançável: a falha é auditada, o lote não some."""
    coletor, despacho, auditoria = _coletor_com_despacho()
    pedido = montar_pedido_de_json(str(DADOS / "pedido_coleta_exemplo.json"))
    coletor.processar_pedido(pedido)
    lote = dict(coletor.bandeja)
    despacho.area_nome = "centro_padrao"

    despacho_original = despacho._criar_transportador

    def _com_muro(coletor_notificante):
        transportador = despacho_original(coletor_notificante)
        transportador.obstaculos = {(x, 1): "equipamento" for x in range(10)}
        return transportador

    despacho._criar_transportador = _com_muro
    coletor.aprovar_lote()

    assert despacho.entregas == []
    assert despacho.transportador.carga == lote
    falhas = [evento for evento, _ in auditoria.eventos
              if evento == "transporte_falhou"]
    assert falhas == ["transporte_falhou"]
