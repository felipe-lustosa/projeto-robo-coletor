# Factory — criar_robo_coletor, criar_robo_configurado — enunciado, Seção 2.3.
# (Ver fabrica_base.py — genérico do curso, não editar: criar_robo("RoboColetor",
# ...) já funciona, pode chamar direto ou usar como modelo.)
#
# TODO: implemente aqui. criar_robo_coletor(tipo_nome, ...) a partir do
# _registro (Seção 2.2); criar_robo_configurado combina isso com a validação do
# modelo de features (Seção 2.4).
#
# Contrato mínimo exigido por tests/test_00_fornecido.py (não altere a
# assinatura abaixo sem também atualizar aquele arquivo):
#
#   criar_robo_configurado(tipo_nome, nome, estrategia_nome=..., area_nome=...)
from celular_robo.fabrica_base import criar_robo
from celular_robo.estrategias import RotaColeta
from celular_robo.modos import ModoColetando
from celular_robo.modelo_features import (
    NOMES_ROTAS,
    obstaculos_da_area,
    validar_configuracao,
)


def criar_robo_coletor(tipo_nome, nome, estrategia_nome, area_nome, **kwargs):
    classe_rota = RotaColeta._registro_rotas[NOMES_ROTAS[estrategia_nome]]
    return criar_robo(
        tipo_nome, nome,
        estrategia=classe_rota(),
        modo=ModoColetando(),
        obstaculos=obstaculos_da_area(area_nome),
        **kwargs,
    )


def criar_robo_configurado(tipo_nome, nome, estrategia_nome, area_nome, **kwargs):
    validar_configuracao(tipo_nome, estrategia_nome, area_nome)
    return criar_robo_coletor(tipo_nome, nome, estrategia_nome, area_nome, **kwargs)