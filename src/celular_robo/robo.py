from celular_robo.robo_base import Robo

class QuantidadeValida:
    """Descriptor valida que a quantidade coletada não é negativa nem passa da quantidade pedida"""

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
    """Navega até cada prateleira, coleta os itens do pedido e deposita
    tudo na bandeja."""

    def __init__(self, nome, **kwargs):
        super().__init__(nome, **kwargs)
        self.bandeja = {}

    def __repr__(self):
        return f"RoboColetor({self.nome!r}, x={self.x}, y={self.y})"

    def __str__(self):
        return (
            f"{self.nome} em ({self.x}, {self.y}), {len(self)} item(ns) na bandeja"
        )

    def __len__(self):
        return sum(self.bandeja.values())
