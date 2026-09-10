"""State: modos de operação dos robôs (Seções 2.3 e 7)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from celular_robo.modos_base import ModoOperacao
from celular_robo.robo_base import Robo
from celular_robo.excecoes import ColetaBloqueada, TransporteBloqueado

if TYPE_CHECKING:
    from celular_robo.comandos import ComandoColeta
    from celular_robo.transportador import RoboTransportador


class ModoColetando(ModoOperacao):
    """Modo normal: movimento e coleta seguem a rota configurada."""

    def mover(self, robo: Robo) -> bool:
        return robo.estrategia.mover(robo)

    def coletar(self, robo: Robo, comando: ComandoColeta) -> None:
        """Delega a coleta pra rota, igual mover() — o State escolhe se a
        operação acontece, o Strategy escolhe como."""
        return robo.estrategia.coletar(robo, comando)


class ModoAguardandoVerificacao(ModoOperacao):
    """Bandeja cheia: o robô para até a equipe de testes decidir."""

    def mover(self, robo: Robo) -> bool:
        print(f"{robo.nome} está aguardando verificação da bandeja.")
        return False

    def coletar(self, robo: Robo, comando: ComandoColeta) -> None:
        """Recusa iniciar nova coleta antes de a equipe aprovar o lote."""
        raise ColetaBloqueada(
            f"{robo.nome} aguarda verificação da bandeja: a equipe precisa "
            f"decidir sobre o lote antes de coletar {comando.codinome}"
        )


class ModoAguardandoCarga(ModoOperacao):
    """Modo inicial do RoboTransportador: parado no ponto de
    partida até a equipe aprovar um lote e a carga chegar."""

    def mover(self, robo: Robo) -> bool:
        print(f"{robo.nome} está sem carga, aguardando um lote aprovado.")
        return False

    def transportar(self, robo: RoboTransportador) -> dict[str, int]:
        """Recusa transportar sem carga — mesma ideia de
        ModoAguardandoVerificacao recusando coletar."""
        raise TransporteBloqueado(
            f"{robo.nome} não tem carga: só transporta depois de a equipe "
            f"aprovar um lote"
        )


class ModoTransportando(ModoOperacao):
    """Carga a bordo: o transportador leva o lote até o ponto de retirada."""

    def mover(self, robo: Robo) -> bool:
        return robo.estrategia.mover(robo)

    def transportar(self, robo: RoboTransportador) -> dict[str, int]:
        """Navega até o ponto de retirada pela rota configurada e confirma a
        entrega; o State decide se transporta, o Strategy decide por onde."""
        try:
            robo.estrategia.navegar_ate(robo, robo.PONTO_RETIRADA)
        except ColetaBloqueada as erro:
            raise TransporteBloqueado(
                f"{robo.nome}: caminho bloqueado até o ponto de retirada "
                f"{robo.PONTO_RETIRADA} ({erro})"
            ) from erro
        return robo.confirmar_entrega()
