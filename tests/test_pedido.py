# TODO: seus testes de pedido — enunciado, Seção 2.7 (pytest.raises(PedidoInvalido),
# conflito fragil+urgente de Seção 2.4).

import pytest

from celular_robo.persistencia import montar_pedido_de_json
from celular_robo.excecoes import PedidoInvalido


def test_pedido_invalido_codinome_inexistente(escrever_pedido):
    caminho = escrever_pedido({
        "lote": "Lote Teste",
        "itens": [
            {"quantidade": 1, "posicao": [0, 0]},
        ],
    })
    with pytest.raises(PedidoInvalido):
        montar_pedido_de_json(caminho)


def test_pedido_item_fragil_e_urgente_ao_mesmo_tempo_e_contraditorio(escrever_pedido):
    caminho = escrever_pedido({
        "lote": "Lote Teste",
        "itens": [
            {"codinome": "Projeto X", "quantidade": 1, "posicao": [0, 0],
             "fragil": True, "urgente": True},
        ],
    })
    with pytest.raises(PedidoInvalido):
        montar_pedido_de_json(caminho)


def test_pedido_com_item_urgente_e_item_fragil_diferentes_e_invalido(escrever_pedido):
    caminho = escrever_pedido({
        "lote": "Lote Teste",
        "itens": [
            {"codinome": "Projeto A", "quantidade": 1, "posicao": [0, 0], "urgente": True},
            {"codinome": "Projeto B", "quantidade": 1, "posicao": [1, 1], "fragil": True},
        ],
    })
    with pytest.raises(PedidoInvalido):
        montar_pedido_de_json(caminho)


def test_pedido_valido_monta_comandos_corretos(escrever_pedido):
    caminho = escrever_pedido({
        "lote": "Lote Teste",
        "itens": [
            {"codinome": "Projeto A", "quantidade": 2, "posicao": [3, 4]},
        ],
    })
    pedido = montar_pedido_de_json(caminho)
    assert pedido.lote == "Lote Teste"
    assert len(pedido.comandos) == 1
    assert pedido.comandos[0].codinome == "Projeto A"
    assert pedido.comandos[0].quantidade == 2
