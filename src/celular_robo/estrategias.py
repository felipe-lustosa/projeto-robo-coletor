"""Strategy: rotas de coleta (Seção 2.3).

A base própria RotaColeta mantém um registro separado do Strategy genérico
do curso (estrategias_base.py), de onde sai ESTRATEGIAS_VALIDAS.
"""

from abc import ABC, abstractmethod

from celular_robo.robo_base import Direcao
from celular_robo.excecoes import ColetaBloqueada


class RotaColeta(ABC):
    """Base das rotas; cada subclasse se registra em _registro_rotas."""

    _registro_rotas = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        RotaColeta._registro_rotas[cls.__name__] = cls

    @abstractmethod
    def coletar(self, robo, comando):
        """Navega até o item do comando e o deposita na bandeja."""

    def mover(self, robo):
        return robo.avancar()

    def _navegar_ate(self, robo, posicao):
        """Anda primeiro no eixo x, depois no y, até a posição.

        `avancar_n` para no primeiro obstáculo, então a chegada é conferida
        no fim: sem isso a rota depositaria um item que o robô nunca
        alcançou.
        """
        tx, ty = posicao
        if robo.x < tx:
            robo.girar_ate(Direcao.LESTE)
            robo.avancar_n(tx - robo.x)
        elif robo.x > tx:
            robo.girar_ate(Direcao.OESTE)
            robo.avancar_n(robo.x - tx)
        if robo.y < ty:
            robo.girar_ate(Direcao.NORTE)
            robo.avancar_n(ty - robo.y)
        elif robo.y > ty:
            robo.girar_ate(Direcao.SUL)
            robo.avancar_n(robo.y - ty)
        if robo.posicao != (tx, ty):
            raise ColetaBloqueada(
                f"caminho bloqueado até {(tx, ty)}: robô parou em {robo.posicao}"
            )

    def _depositar(self, robo, comando):
        """Põe o item na bandeja e notifica "item_coletado".

        Toda rota deve depositar por aqui — é o que a auditoria enxerga.
        """
        comando.quantidade_coletada = comando.quantidade
        robo.bandeja[comando.codinome] = (
            robo.bandeja.get(comando.codinome, 0) + comando.quantidade
        )
        robo.notificar(
            "item_coletado", codinome=comando.codinome, quantidade=comando.quantidade
        )


class RotaDireta(RotaColeta):
    """Vai direto até cada prateleira, sem revalidar o item."""

    def coletar(self, robo, comando):
        self._navegar_ate(robo, comando.posicao)
        self._depositar(robo, comando)


class RotaComDuplaConferencia(RotaColeta):
    """Confere a posição antes de depositar — mais lenta, mais segura."""

    def coletar(self, robo, comando):
        self._navegar_ate(robo, comando.posicao)
        self._conferir(robo, comando)
        self._conferir(robo, comando)
        self._depositar(robo, comando)

    def _conferir(self, robo, comando):
        """Levanta ColetaBloqueada se o robô não parou na posição do item."""
        esperado = tuple(comando.posicao)
        if robo.posicao != esperado:
            raise ColetaBloqueada(
                f"{comando.codinome}: robô em ({robo.x}, {robo.y}), "
                f"esperado {esperado}"
            )
