"""Extensão opcional: RoboTransportador (Seção 7).
Segundo tipo de robô, num módulo próprio — herdar de `Robo` já o
registra em `Robo._registro`, de onde `TIPOS_VALIDOS` é derivado
(modelo_features.py).
"""

from celular_robo.robo_base import Robo
from celular_robo.modos import ModoAguardandoCarga, ModoTransportando
from celular_robo.excecoes import TransporteBloqueado


class RoboTransportador(Robo, categoria="logistica"):
    """Leva o lote aprovado da bandeja do coletor até o ponto de retirada.

    O carrinho robótico que recolhe o lote no ponto de retirada continua
    fora de escopo: o transportador só entrega ali.
    """

    PONTO_RETIRADA = (Robo.LADO_GRADE - 1, Robo.LADO_GRADE - 1)

    def __init__(self, nome, **kwargs):
        kwargs.setdefault("modo", ModoAguardandoCarga())
        super().__init__(nome, **kwargs)
        self.carga = {}
        self.entregues = {}

    def __repr__(self):
        return f"RoboTransportador({self.nome!r}, x={self.x}, y={self.y})"

    def __str__(self):
        return (
            f"{self.nome} em ({self.x}, {self.y}), {len(self)} item(ns) a bordo, "
            f"modo {type(self.modo).__name__}"
        )

    def __len__(self):
        """Total de itens a bordo — mesmo critério do `__len__` da bandeja."""
        return sum(self.carga.values())

    def __bool__(self):
        """Um transportador existe mesmo sem carga (mesmo motivo do
        `__bool__` de RoboColetor: `__len__` zerado não o torna falsy)."""
        return True

    def carregar(self, itens):
        """Recebe o lote aprovado e passa pra ModoTransportando."""
        if not itens:
            raise TransporteBloqueado(
                f"{self.nome}: lote vazio, não há o que transportar"
            )
        self.carga = dict(itens)
        self.modo = ModoTransportando()
        self.notificar("carga_recebida", itens=dict(self.carga))
        return self.carga

    def transportar(self):
        """Delega ao modo atual, igual `Robo.mover` — o State recusa se o
        transportador ainda estiver sem carga."""
        return self.modo.transportar(self)

    def confirmar_entrega(self):
        """Descarrega no ponto de retirada e volta a aguardar carga."""
        entregues = dict(self.carga)
        self.entregues = entregues
        self.carga = {}
        self.modo = ModoAguardandoCarga()
        self.notificar(
            "lote_entregue", itens=entregues, ponto=self.PONTO_RETIRADA
        )
        return entregues
