"""Testes de validação do pedido de coleta (Seções 2.4 e 2.7)."""

import pytest

from celular_robo.persistencia import montar_pedido_de_json
from celular_robo.excecoes import PedidoInvalido

LOTE_TESTE = {"Projeto A": 5, "Projeto B": 2, "Projeto X": 1}


def test_pedido_invalido_codinome_inexistente(escrever_pedido):
    """Codinome fora do lote rejeita o pedido."""
    caminho = escrever_pedido({
        "lote": "Lote Teste",
        "itens": [
            {"codinome": "Projeto Fantasma", "quantidade": 1, "posicao": [0, 0]},
        ],
    })
    with pytest.raises(PedidoInvalido):
        montar_pedido_de_json(caminho, lote_disponivel=LOTE_TESTE)


def test_pedido_invalido_quantidade_maior_que_a_disponivel(escrever_pedido):
    """Quantidade maior que a disponível no lote rejeita o pedido."""
    caminho = escrever_pedido({
        "lote": "Lote Teste",
        "itens": [
            {"codinome": "Projeto B", "quantidade": 3, "posicao": [1, 1]},  # só há 2
        ],
    })
    with pytest.raises(PedidoInvalido):
        montar_pedido_de_json(caminho, lote_disponivel=LOTE_TESTE)


def test_pedido_invalido_item_sem_campo_codinome(escrever_pedido):
    """Item sem codinome rejeita o pedido."""
    caminho = escrever_pedido({
        "lote": "Lote Teste",
        "itens": [
            {"quantidade": 1, "posicao": [0, 0]},  # sem "codinome"
        ],
    })
    with pytest.raises(PedidoInvalido):
        montar_pedido_de_json(caminho, lote_disponivel=LOTE_TESTE)


def test_pedido_vazio_e_invalido(escrever_pedido):
    """Pedido sem itens é inválido."""
    caminho = escrever_pedido({"lote": "Lote Teste", "itens": []})
    with pytest.raises(PedidoInvalido):
        montar_pedido_de_json(caminho, lote_disponivel=LOTE_TESTE)


def test_pedido_item_fragil_e_urgente_ao_mesmo_tempo_e_contraditorio(escrever_pedido):
    """Um item frágil e urgente exigiria as duas rotas ao mesmo tempo."""
    caminho = escrever_pedido({
        "lote": "Lote Teste",
        "itens": [
            {"codinome": "Projeto X", "quantidade": 1, "posicao": [0, 0],
             "fragil": True, "urgente": True},
        ],
    })
    with pytest.raises(PedidoInvalido):
        montar_pedido_de_json(caminho, lote_disponivel=LOTE_TESTE)


def test_pedido_com_item_urgente_e_item_fragil_diferentes_e_invalido(escrever_pedido):
    """A rota é única por robô: itens frágil e urgente não convivem."""
    caminho = escrever_pedido({
        "lote": "Lote Teste",
        "itens": [
            {"codinome": "Projeto A", "quantidade": 1, "posicao": [0, 0], "urgente": True},
            {"codinome": "Projeto B", "quantidade": 1, "posicao": [1, 1], "fragil": True},
        ],
    })
    with pytest.raises(PedidoInvalido):
        montar_pedido_de_json(caminho, lote_disponivel=LOTE_TESTE)


def test_pedido_valido_monta_comandos_corretos(escrever_pedido):
    """Pedido válido vira comandos com codinome e quantidade certos."""
    caminho = escrever_pedido({
        "lote": "Lote Teste",
        "itens": [
            {"codinome": "Projeto A", "quantidade": 2, "posicao": [3, 4]},
        ],
    })
    pedido = montar_pedido_de_json(caminho, lote_disponivel=LOTE_TESTE)
    assert pedido.lote == "Lote Teste"
    assert len(pedido.comandos) == 1
    assert pedido.comandos[0].codinome == "Projeto A"
    assert pedido.comandos[0].quantidade == 2
