# Configuração e persistência — enunciado, Seção 2.6.
#
# TODO: implemente aqui. montar_robo_de_config(config) e
# montar_pedido_de_json(caminho) — mesmo par de funções do capstone do curso
# (montar_robo_de_config/montar_frota_de_json), adaptado: um arquivo
# configura o robô (tipo, estratégia, área), outro traz o pedido de coleta.

import json
from collections import namedtuple

from celular_robo.fabrica import criar_robo_configurado
from celular_robo.comandos import ComandoColeta
from celular_robo.excecoes import PedidoInvalido

Pedido = namedtuple("Pedido", ["lote", "comandos"])


def montar_robo_de_config(config):
    obrigatorios = {"tipo_nome", "nome", "estrategia_nome", "area_nome"}
    extras = {chave: valor for chave, valor in config.items() if chave not in obrigatorios}
    return criar_robo_configurado(
        config["tipo_nome"],
        config["nome"],
        estrategia_nome=config["estrategia_nome"],
        area_nome=config["area_nome"],
        **extras,
    )


def montar_pedido_de_json(caminho):
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    itens = dados.get("itens") or []
    if not itens:
        raise PedidoInvalido("pedido vazio: nenhum item em 'itens'")

    comandos = []
    tem_urgente = False
    tem_fragil = False
    for item in itens:
        codinome = item.get("codinome")
        if not codinome:
            raise PedidoInvalido(f"codinome não encontrado no lote: {item!r}")

        quantidade = item.get("quantidade", 0)
        if quantidade <= 0:
            raise PedidoInvalido(f"{codinome}: quantidade inválida ({quantidade})")

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