"""Factory do robô coletor (Seção 2.3).

Contrato exigido por tests/test_00_fornecido.py:
criar_robo_configurado(tipo_nome, nome, estrategia_nome=..., area_nome=...)
"""

from celular_robo.fabrica_base import criar_robo
from celular_robo.estrategias import RotaColeta
from celular_robo.modelo_features import (
    NOMES_ROTAS,
    obstaculos_da_area,
    validar_configuracao,
)


def criar_robo_coletor(tipo_nome, nome, estrategia_nome, area_nome, **kwargs):
    """Monta o robô com a rota e os obstáculos da área, a partir do registro."""
    classe_rota = RotaColeta._registro_rotas[NOMES_ROTAS[estrategia_nome]]
    return criar_robo(
        tipo_nome, nome,
        estrategia=classe_rota(),
        obstaculos=obstaculos_da_area(area_nome),
        **kwargs,
    )


def criar_robo_configurado(tipo_nome, nome, estrategia_nome, area_nome, **kwargs):
    """Valida a configuração (Seção 2.4) antes de criar o robô."""
    validar_configuracao(tipo_nome, estrategia_nome, area_nome)
    return criar_robo_coletor(tipo_nome, nome, estrategia_nome, area_nome, **kwargs)
