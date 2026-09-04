# Fixtures compartilhadas entre seus test_*.py — TODO, à sua escolha.
# (A fixture usada por test_00_fornecido.py já vem definida nele mesmo —
# não precisa duplicar aqui.)
import json

import pytest


@pytest.fixture
def escrever_pedido(tmp_path):
    def _escrever(dados, nome="pedido.json"):
        caminho = tmp_path / nome
        caminho.write_text(json.dumps(dados), encoding="utf-8")
        return str(caminho)
    return _escrever