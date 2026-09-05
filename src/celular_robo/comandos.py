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
from celular_robo.modelo_features import validar_item_para_estrategia


class ComandoColeta(Comando):
    """Um item do pedido: codinome, posição, quantidade pedida.
    .executar(robo) delega a navegação/coleta pra robo.estrategia (a
    RotaColeta configurada no robô)."""

    quantidade_coletada = QuantidadeValida()

    def __init__(self, codinome, posicao, quantidade, fragil=False, urgente=False):
        self.codinome = codinome
        self.posicao = posicao
        self.quantidade = quantidade
        self.fragil = fragil
        self.urgente = urgente
        self.quantidade_coletada = 0

    def executar(self, robo):
        """Confere o `requires` item -> estratégia (REQUER, modelo_features),
        delega a navegação/coleta pra rota configurada no robô e guarda o
        comando em `robo._historico_comandos` — a pilha que `desfazer`
        consome."""
        validar_item_para_estrategia(
            self.codinome, robo.estrategia,
            fragil=self.fragil, urgente=self.urgente,
        )
        robo.estrategia.coletar(robo, self)
        robo._historico_comandos.append(self)

    def desfazer(self, robo):
        """Remove o item da bandeja, zera a contagem coletada deste comando
        e o tira do histórico."""
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
