"""RoboColetor e o descriptor QuantidadeValida (Seção 2.1)."""

from celular_robo.robo_base import Robo
from celular_robo.modos import ModoColetando


class QuantidadeValida:
    """Descriptor: a quantidade coletada fica entre 0 e a quantidade pedida."""

    def __set_name__(self, owner, name):
        self.nome_publico = name
        self.nome = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.nome, 0)

    def __set__(self, instance, valor):
        maximo = instance.quantidade
        if not (0 <= valor <= maximo):
            raise ValueError(
                f"{self.nome_publico}={valor} inválido: quantidade coletada "
                f"não pode ser negativa nem passar da quantidade pedida "
                f"({maximo})"
            )
        instance.__dict__[self.nome] = valor


class RoboColetor(Robo):
    """Robô que navega até as prateleiras e deposita os itens na bandeja."""

    def __init__(self, nome, **kwargs):
        kwargs.setdefault("modo", ModoColetando())
        super().__init__(nome, **kwargs)
        self.bandeja = {}

    def __repr__(self):
        return f"RoboColetor({self.nome!r}, x={self.x}, y={self.y})"

    def __str__(self):
        return (
            f"{self.nome} em ({self.x}, {self.y}), {len(self)} item(ns) na bandeja"
        )

    def __len__(self):
        """Total de itens na bandeja."""
        return sum(self.bandeja.values())

    def __bool__(self):
        """Um robô existe independente da bandeja.

        Sem isto, `__len__` deixaria o robô falsy com a bandeja vazia e um
        `if robo:` em qualquer lugar leria "não há robô".
        """
        return True

    def bandeja_completa(self, pedido):
        """True quando todo codinome do pedido já está na bandeja na
        quantidade pedida (soma os itens repetidos do mesmo codinome)."""
        exigido = {}
        for comando in pedido.comandos:
            exigido[comando.codinome] = (
                exigido.get(comando.codinome, 0) + comando.quantidade
            )
        return all(
            self.bandeja.get(codinome, 0) >= quantidade
            for codinome, quantidade in exigido.items()
        )

    def conferir_bandeja(self, pedido):
        """Notifica "bandeja_pronta" se o pedido está completo, e devolve
        se notificou.

        É o robô que avisa a equipe (Seção 1), não a CLI; o Observer
        EquipeDeTestes reage trocando o modo pra ModoAguardandoVerificacao.
        """
        if not self.bandeja_completa(pedido):
            return False
        self.notificar("bandeja_pronta", lote=getattr(pedido, "lote", None))
        return True
