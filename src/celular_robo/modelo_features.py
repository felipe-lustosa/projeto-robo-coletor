"""Modelo de features / LPS: o que pode ser combinado com o quê (Seção 2.4).

TIPOS_VALIDOS e ESTRATEGIAS_VALIDAS vêm dos registros da Seção 2.2, não
são digitados à mão.
"""

from celular_robo.robo_base import Robo
from celular_robo.robo import RoboColetor
from celular_robo.estrategias import RotaColeta
from celular_robo.excecoes import ConfiguracaoInvalida


def _slug_rota(nome_classe):
    """RotaComDuplaConferencia -> "com_dupla_conferencia"."""
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

REQUER = {
    "fragil": "RotaComDuplaConferencia",
    "urgente": "RotaDireta",
}


def obstaculos_da_area(area_nome):
    """Cópia do mapa de obstáculos da área, pronta pra virar robo.obstaculos."""
    return dict(_OBSTACULOS_POR_AREA[area_nome])


def rotas_exigidas_por_item(fragil=False, urgente=False):
    """Nomes de rota que os atributos do item exigem, derivados de REQUER."""
    return {
        REQUER[atributo]
        for atributo, ativo in (("fragil", fragil), ("urgente", urgente))
        if ativo
    }


def validar_item_para_estrategia(codinome, estrategia, fragil=False, urgente=False):
    """Aplica o requires item -> rota; levanta ConfiguracaoInvalida se a rota
    do robô não atende o item."""
    exigidas = rotas_exigidas_por_item(fragil=fragil, urgente=urgente)
    if not exigidas:
        return
    if len(exigidas) > 1:
        raise ConfiguracaoInvalida(
            f"{codinome}: item exige {sorted(exigidas)} ao mesmo tempo — "
            f"robo.estrategia é única por robô"
        )
    exigida = next(iter(exigidas))
    atual = type(estrategia).__name__
    if atual != exigida:
        raise ConfiguracaoInvalida(
            f"{codinome}: item exige {exigida}, robô está com {atual}"
        )


def validar_configuracao(tipo_nome, estrategia_nome, area_nome):
    """Valida tipo x estratégia x área antes de instanciar qualquer robô."""
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
