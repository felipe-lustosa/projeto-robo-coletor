"""Testes do modelo de features: estratégia x área (Seção 2.7)."""

import pytest

from celular_robo.fabrica import criar_robo_configurado
from celular_robo.comandos import ComandoColeta
from celular_robo.estrategias import RotaDireta, RotaComDuplaConferencia
from celular_robo.modos import ModoColetando
from celular_robo.excecoes import ConfiguracaoInvalida, PedidoInvalido

CENARIOS = [
    ("direta", "centro_padrao", RotaDireta, None),
    ("com_dupla_conferencia", "centro_padrao", RotaComDuplaConferencia, None),
    ("com_dupla_conferencia", "area_quarentena", RotaComDuplaConferencia, None),
    ("direta", "area_quarentena", None, ConfiguracaoInvalida),
]


@pytest.mark.parametrize(
    "estrategia_nome, area_nome, classe_esperada, excecao_esperada", CENARIOS
)
def test_contrato_criar_ou_recusar(
    estrategia_nome, area_nome, classe_esperada, excecao_esperada
):
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


# requires (Seção 2.4): fragil exige RotaComDuplaConferencia, urgente exige
# RotaDireta. O par (marcação do item, rota do robô) ou coleta, ou é recusado.
REQUIRES = [
    ("fragil", "com_dupla_conferencia", None),
    ("fragil", "direta", ConfiguracaoInvalida),
    ("urgente", "direta", None),
    ("urgente", "com_dupla_conferencia", ConfiguracaoInvalida),
    (None, "direta", None),
    (None, "com_dupla_conferencia", None),
]


@pytest.mark.parametrize("marcacao, estrategia_nome, excecao_esperada", REQUIRES)
def test_requires_item_para_rota(marcacao, estrategia_nome, excecao_esperada):
    """A rota do robô precisa atender o requires do item, senão a coleta é
    recusada antes de mexer na bandeja."""
    robo = criar_robo_configurado(
        "RoboColetor", "Coletor-Teste",
        estrategia_nome=estrategia_nome, area_nome="centro_padrao",
    )
    comando = ComandoColeta(
        "Projeto Aurora", (2, 2), 1,
        fragil=marcacao == "fragil", urgente=marcacao == "urgente",
    )

    if excecao_esperada is not None:
        with pytest.raises(excecao_esperada):
            comando.executar(robo)
        assert robo.bandeja == {}
        assert comando.quantidade_coletada == 0
        assert robo.historico == ()
        return

    comando.executar(robo)
    assert robo.bandeja == {"Projeto Aurora": 1}


def test_item_fragil_e_urgente_direto_no_comando_tambem_e_pedido_invalido():
    """A escolha do README (PedidoInvalido pra item contraditório) vale
    também fora do JSON: construir o ComandoColeta à mão e executar cai na
    mesma exceção, não em ConfiguracaoInvalida."""
    robo = criar_robo_configurado(
        "RoboColetor", "Coletor-Teste",
        estrategia_nome="direta", area_nome="centro_padrao",
    )
    comando = ComandoColeta("Projeto Aurora", (1, 1), 1, fragil=True, urgente=True)

    with pytest.raises(PedidoInvalido):
        comando.executar(robo)
    assert robo.bandeja == {}
    assert robo.historico == ()
