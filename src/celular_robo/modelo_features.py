# Modelo de features / LPS — enunciado, Seção 2.4.
#
# TODO: implemente aqui. TIPOS_VALIDOS, ESTRATEGIAS_VALIDAS (derivados dos
# registros de Seção 2.2, não digitados à mão), REQUER/EXCLUI (4 dimensões: tipo,
# estratégia, área, urgência) e validar_configuracao levantando
# ConfiguracaoInvalida antes de qualquer robô ser instanciado.
from celular_robo.robo_base import Robo
from celular_robo.robo import RoboColetor
from celular_robo.estrategias import RotaColeta
from celular_robo.excecoes import ConfiguracaoInvalida


def _slug_rota(nome_classe):
    letras = []
    for letra in nome_classe.removeprefix("Rota"):
        if letra.isupper() and letras:
            letras.append("_")
        letras.append(letra.lower())
    return "".join(letras)


TIPOS_VALIDOS = set(Robo._registro)
ESTRATEGIAS_VALIDAS = set(RotaColeta._registro_rotas)
NOMES_ROTAS = {_slug_rota(nome): nome for nome in RotaColeta._registro_rotas}

_OBSTACULOS_POR_AREA = {
    "centro_padrao": {},
    "area_quarentena": {(5, 5): "quarentena"},
}
AREAS_VALIDAS = set(_OBSTACULOS_POR_AREA)

EXCLUI = {
    "area_quarentena": {"RotaDireta"},
}


def obstaculos_da_area(area_nome):
    return dict(_OBSTACULOS_POR_AREA[area_nome])


def validar_configuracao(tipo_nome, estrategia_nome, area_nome):
    if tipo_nome not in TIPOS_VALIDOS:
        raise ConfiguracaoInvalida(
            f"tipo desconhecido: {tipo_nome!r}. Disponíveis: {sorted(TIPOS_VALIDOS)}"
        )
    nome_rota = NOMES_ROTAS.get(estrategia_nome)
    if nome_rota is None or nome_rota not in ESTRATEGIAS_VALIDAS:
        raise ConfiguracaoInvalida(
            f"estratégia desconhecida: {estrategia_nome!r}. "
            f"Disponíveis: {sorted(NOMES_ROTAS)}"
        )
    if area_nome not in AREAS_VALIDAS:
        raise ConfiguracaoInvalida(
            f"área desconhecida: {area_nome!r}. Disponíveis: {sorted(AREAS_VALIDAS)}"
        )
    if nome_rota in EXCLUI.get(area_nome, set()):
        raise ConfiguracaoInvalida(
            f"área {area_nome!r} exclui a estratégia {estrategia_nome!r}"
        )