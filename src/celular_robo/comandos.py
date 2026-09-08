"""Command do domínio de coleta: ComandoColeta (Seção 2.3)."""

from celular_robo.comandos_base import Comando
from celular_robo.robo import QuantidadeValida
from celular_robo.modelo_features import validar_item_para_estrategia


class ComandoColeta(Comando):
    """Um item do pedido; a coleta é delegada à rota configurada no robô."""

    quantidade_coletada = QuantidadeValida()

    def __init__(self, codinome, posicao, quantidade, fragil=False, urgente=False):
        self.codinome = codinome
        self.posicao = posicao
        self.quantidade = quantidade
        self.fragil = fragil
        self.urgente = urgente
        self.quantidade_coletada = 0

    def executar(self, robo):
        """Valida o item contra a rota, coleta e empilha no histórico do robô."""
        validar_item_para_estrategia(
            self.codinome, robo.estrategia,
            fragil=self.fragil, urgente=self.urgente,
        )
        robo.modo.coletar(robo, self)
        robo._historico_comandos.append(self)

    def desfazer(self, robo):
        """Tira o item da bandeja e o comando do histórico."""
        restante = robo.bandeja.get(self.codinome, 0) - self.quantidade_coletada
        if restante > 0:
            robo.bandeja[self.codinome] = restante
        else:
            robo.bandeja.pop(self.codinome, None)
        self.quantidade_coletada = 0
        if self in robo._historico_comandos:
            robo._historico_comandos.remove(self)
        robo.notificar("coleta_desfeita", codinome=self.codinome)

    def __repr__(self):
        return f"ComandoColeta({self.codinome!r}, {self.posicao}, {self.quantidade})"
