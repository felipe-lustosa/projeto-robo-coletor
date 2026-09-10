"""Modelo de features / LPS: o que pode ser combinado com o quê (Seção 2.4).

TIPOS_VALIDOS e ESTRATEGIAS_VALIDAS vêm dos registros da Seção 2.2, não
são digitados à mão.
"""

from __future__ import annotations

from celular_robo.robo_base import Robo
from celular_robo.robo import RoboColetor  # noqa: F401 — registra o tipo
from celular_robo.transportador import RoboTransportador  # noqa: F401 — idem
from celular_robo.estrategias import RotaColeta
from celular_robo.excecoes import ConfiguracaoInvalida, PedidoInvalido


def _slug_rota(nome_classe: str) -> str:
    """RotaComDuplaConferencia -> "com_dupla_conferencia"."""
    letras: list[str] = []
    for letra in nome_classe.removeprefix("Rota"):
        if letra.isupper() and letras:
            letras.append("_")
        letras.append(letra.lower())
    return "".join(letras)


TIPOS_VALIDOS: set[str] = set(Robo._registro)
ESTRATEGIAS_VALIDAS: set[str] = set(RotaColeta._registro_rotas)
NOMES_ROTAS: dict[str, str] = {
    _slug_rota(nome): nome for nome in RotaColeta._registro_rotas
}

_OBSTACULOS_POR_AREA: dict[str, dict[tuple[int, int], str]] = {
    "centro_padrao": {},
    "area_quarentena": {(5, 5): "quarentena"},
}
AREAS_VALIDAS: set[str] = set(_OBSTACULOS_POR_AREA)

EXCLUI: dict[str, set[str]] = {
    "area_quarentena": {"RotaDireta"},
    "RoboTransportador": {"area_quarentena"},
}

REQUER: dict[str, str] = {
    "fragil": "RotaComDuplaConferencia",
    "urgente": "RotaDireta",
}


def obstaculos_da_area(area_nome: str) -> dict[tuple[int, int], str]:
    """Cópia do mapa de obstáculos da área, pronta pra virar robo.obstaculos."""
    return dict(_OBSTACULOS_POR_AREA[area_nome])


def rotas_exigidas_por_item(fragil: bool = False, urgente: bool = False) -> set[str]:
    """Nomes de rota que os atributos do item exigem, derivados de REQUER."""
    return {
        REQUER[atributo]
        for atributo, ativo in (("fragil", fragil), ("urgente", urgente))
        if ativo
    }


def validar_item_para_estrategia(
    codinome: str,
    estrategia: object,
    fragil: bool = False,
    urgente: bool = False,
) -> None:
    """Aplica o requires item -> rota.

    Levanta PedidoInvalido se o item em si é contraditório (fragil e
    urgente juntos — mesma exceção que montar_pedido_de_json usa pro
    mesmo defeito, o problema está no item e não na configuração), e
    ConfiguracaoInvalida se a rota do robô não atende o item.
    """
    exigidas = rotas_exigidas_por_item(fragil=fragil, urgente=urgente)
    if not exigidas:
        return
    if len(exigidas) > 1:
        raise PedidoInvalido(
            f"{codinome}: fragil e urgente ao mesmo tempo é contraditório "
            f"(exigiria {sorted(exigidas)} juntas — robo.estrategia é única)"
        )
    exigida = next(iter(exigidas))
    atual = type(estrategia).__name__
    if atual != exigida:
        raise ConfiguracaoInvalida(
            f"{codinome}: item exige {exigida}, robô está com {atual}"
        )


def validar_configuracao(tipo_nome: str, estrategia_nome: str, area_nome: str) -> None:
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
    for feature_a, feature_b in ((area_nome, nome_rota), (tipo_nome, area_nome)):
        if (feature_b in EXCLUI.get(feature_a, set())
                or feature_a in EXCLUI.get(feature_b, set())):
            raise ConfiguracaoInvalida(
                f"combinação recusada: {feature_a!r} exclui {feature_b!r}"
            )
