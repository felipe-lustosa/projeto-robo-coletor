"""Fixtures compartilhadas entre os testes."""

import json

import pytest


@pytest.fixture
def escrever_pedido(tmp_path):
    """Escreve um pedido JSON temporário e devolve o caminho."""
    def _escrever(dados, nome="pedido.json"):
        caminho = tmp_path / nome
        caminho.write_text(json.dumps(dados), encoding="utf-8")
        return str(caminho)
    return _escrever