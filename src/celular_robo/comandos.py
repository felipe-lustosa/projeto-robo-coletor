"""Command do domínio de coleta: ComandoColeta (Seção 2.3)."""

from __future__ import annotations

from celular_robo.comandos_base import Comando
from celular_robo.robo_base import Robo
from celular_robo.robo import QuantidadeValida
from celular_robo.modelo_features import validar_item_para_estrategia


class ComandoColeta(Comando):
    """Um item do pedido; a coleta é delegada à rota configurada no robô."""

    quantidade_coletada = QuantidadeValida()

    def __init__(
        self,
        codinome: str,
        posicao: tuple[int, int],
        quantidade: int,
        fragil: bool = False,
        urgente: bool = False,
    ) -> None:
        self.codinome = codinome
        self.posicao = posicao
        self.quantidade = quantidade
        self.fragil = fragil
        self.urgente = urgente
        self.quantidade_coletada = 0

    def executar(self, robo: Robo) -> None:
        """Valida o item contra a rota, coleta e empilha no histórico do robô."""
        validar_item_para_estrategia(
            self.codinome, robo.estrategia,
            fragil=self.fragil, urgente=self.urgente,
        )
        robo.modo.coletar(robo, self)
        robo._historico_comandos.append(self)

    def desfazer(self, robo: Robo) -> bool:
        """Tira o item da bandeja e o comando do histórico.

        Devolve False (sem notificar) se o comando nunca foi executado —
        não há o que desfazer, e a auditoria não deve registrar um undo
        vazio.
        """
        if self.quantidade_coletada == 0:
            return False
        restante = robo.bandeja.get(self.codinome, 0) - self.quantidade_coletada
        if restante > 0:
            robo.bandeja[self.codinome] = restante
        else:
            robo.bandeja.pop(self.codinome, None)
        self.quantidade_coletada = 0
        if self in robo._historico_comandos:
            robo._historico_comandos.remove(self)
        robo.notificar("coleta_desfeita", codinome=self.codinome)
        return True

    def __repr__(self) -> str:
        return f"ComandoColeta({self.codinome!r}, {self.posicao}, {self.quantidade})"
