"""Configuração e persistência: robô e pedido vindos de JSON (Seção 2.6)."""

import json
from collections import namedtuple

from celular_robo.fabrica import criar_robo_configurado
from celular_robo.comandos import ComandoColeta
from celular_robo.excecoes import PedidoInvalido

Pedido = namedtuple("Pedido", ["lote", "comandos"])

LOTE_DISPONIVEL = {
    "Projeto 01": 4,
    "Projeto 02": 3,
    "Projeto 03": 2,
    "Projeto 04": 1,
}


def montar_robo_de_config(config):
    """Cria o robô a partir do dict de config; chaves extras viram kwargs."""
    obrigatorios = {"tipo_nome", "nome", "estrategia_nome", "area_nome"}
    extras = {chave: valor for chave, valor in config.items() if chave not in obrigatorios}
    return criar_robo_configurado(
        config["tipo_nome"],
        config["nome"],
        estrategia_nome=config["estrategia_nome"],
        area_nome=config["area_nome"],
        **extras,
    )


def montar_pedido_de_json(caminho, lote_disponivel=None):
    """Lê o pedido do JSON e devolve Pedido(lote, comandos).

    Valida contra o lote disponível (LOTE_DISPONIVEL por padrão, injetável
    nos testes) e recusa o pedido inteiro na primeira falha.
    """
    if lote_disponivel is None:
        lote_disponivel = LOTE_DISPONIVEL

    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    itens = dados.get("itens") or []
    if not itens:
        raise PedidoInvalido("pedido vazio: nenhum item em 'itens'")

    comandos = []
    pedido_por_codinome = {}
    tem_urgente = False
    tem_fragil = False
    for item in itens:
        codinome = item.get("codinome")
        if not codinome:
            raise PedidoInvalido(f"item sem codinome: {item!r}")
        if codinome not in lote_disponivel:
            raise PedidoInvalido(
                f"codinome não encontrado no lote: {codinome!r}. "
                f"Disponíveis: {sorted(lote_disponivel)}"
            )

        quantidade = item.get("quantidade", 0)
        if quantidade <= 0:
            raise PedidoInvalido(f"{codinome}: quantidade inválida ({quantidade})")

        acumulado = pedido_por_codinome.get(codinome, 0) + quantidade
        disponivel = lote_disponivel[codinome]
        if acumulado > disponivel:
            raise PedidoInvalido(
                f"{codinome}: quantidade pedida ({acumulado}) maior que a "
                f"disponível no lote ({disponivel})"
            )
        pedido_por_codinome[codinome] = acumulado

        fragil = bool(item.get("fragil", False))
        urgente = bool(item.get("urgente", False))
        if fragil and urgente:
            raise PedidoInvalido(
                f"{codinome}: fragil e urgente ao mesmo tempo é contraditório "
                f"(exigiria RotaComDuplaConferencia e RotaDireta juntas)"
            )
        tem_fragil = tem_fragil or fragil
        tem_urgente = tem_urgente or urgente

        comandos.append(ComandoColeta(
            codinome, tuple(item["posicao"]), quantidade,
            fragil=fragil, urgente=urgente,
        ))

    if tem_urgente and tem_fragil:
        raise PedidoInvalido(
            "pedido com item urgente e item fragil ao mesmo tempo: "
            "robo.estrategia é única, não satisfaz os dois"
        )

    return Pedido(dados.get("lote", ""), comandos)
