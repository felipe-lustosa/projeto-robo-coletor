"""Testes do modelo de features: estratégia x área (Seção 2.7)."""

import pytest

from celular_robo.fabrica import criar_robo_configurado
from celular_robo.estrategias import RotaDireta, RotaComDuplaConferencia
from celular_robo.modos import ModoColetando
from celular_robo.excecoes import ConfiguracaoInvalida

CENARIOS = [
    ("direta", "centro_padrao", RotaDireta, None),
    ("com_dupla_conferencia", "centro_padrao", RotaComDuplaConferencia, None),
    ("com_dupla_conferencia", "area_quarentena", RotaComDuplaConferencia, None),
    ("direta", "area_quarentena", None, ConfiguracaoInvalida),
]


@pytest.mark.parametrize("estrategia_nome, area_nome, classe_esperada, excecao_esperada", CENARIOS)
def test_contrato_criar_ou_recusar(estrategia_nome, area_nome, classe_esperada, excecao_esperada):
    """Cada combinação estratégia x área ou cria o robô, ou é recusada."""
    if excecao_esperada is not None:
        with pytest.raises(excecao_esperada):
            criar_robo_configurado(
                "RoboColetor", "Coletor-Teste",
                estrategia_nome=estrategia_nome, area_nome=area_nome,
            )
        return

    robo = criar_robo_configurado(
        "RoboColetor", "Coletor-Teste",
        estrategia_nome=estrategia_nome, area_nome=area_nome,
    )
    assert type(robo).__name__ == "RoboColetor"
    assert isinstance(robo.estrategia, classe_esperada)
    assert isinstance(robo.modo, ModoColetando)


def test_area_quarentena_tem_obstaculo_de_verdade():
    """A área escolhida chega ao robô como obstáculos de verdade."""
    robo = criar_robo_configurado(
        "RoboColetor", "Coletor-Teste",
        estrategia_nome="com_dupla_conferencia", area_nome="area_quarentena",
    )
    assert len(robo.obstaculos) >= 1
