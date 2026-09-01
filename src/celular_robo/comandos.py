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
from celular_robo.estrategias import RotaDireta, RotaComDuplaConferencia
from celular_robo.excecoes import ConfiguracaoInvalida


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
        if self.fragil and not isinstance(robo.estrategia, RotaComDuplaConferencia):
            raise ConfiguracaoInvalida(
                f"{self.codinome}: item frágil exige RotaComDuplaConferencia, "
                f"robô está com {type(robo.estrategia).__name__}"
            )
        if self.urgente and not isinstance(robo.estrategia, RotaDireta):
            raise ConfiguracaoInvalida(
                f"{self.codinome}: item urgente exige RotaDireta, "
                f"robô está com {type(robo.estrategia).__name__}"
            )
        robo.estrategia.coletar(robo, self)

    def desfazer(self, robo):
        """Remove o item da bandeja e zera a contagem coletada deste
        comando."""
        restante = robo.bandeja.get(self.codinome, 0) - self.quantidade_coletada
        if restante > 0:
            robo.bandeja[self.codinome] = restante
        else:
            robo.bandeja.pop(self.codinome, None)
        self.quantidade_coletada = 0

    def __repr__(self):
        return f"ComandoColeta({self.codinome!r}, {self.posicao}, {self.quantidade})"
