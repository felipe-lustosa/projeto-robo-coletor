# Command — ComandoColeta — enunciado, Seção 2.3.
#
# Herde de `Comando` (comandos_base.py — ABC com registro automático):
#
#   from celular_robo.comandos_base import Comando
#
# TODO: implemente aqui. ComandoColeta(Comando): __init__(codinome, posicao,
# quantidade), com .executar(robo) e .desfazer(robo) (remove o item da
# bandeja, decrementa a contagem coletada).
from celular_robo.comandos_base import Comando
from celular_robo.robo import QuantidadeValida


class ComandoColeta(Comando):
    """Um item do pedido: codinome, posição, quantidade pedida.
    .executar(robo) delega a navegação/coleta pra robo.estrategia (a
    RotaColeta configurada no robô)."""

    quantidade_coletada = QuantidadeValida()

    def __init__(self, codinome, posicao, quantidade):
        self.codinome = codinome
        self.posicao = posicao
        self.quantidade = quantidade
        self.quantidade_coletada = 0

    def executar(self, robo):
        robo.estrategia.coletar(robo, self)

    def desfazer(self, robo):
        pass

    def __repr__(self):
        return f"ComandoColeta({self.codinome!r}, {self.posicao}, {self.quantidade})"