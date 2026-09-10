"""RoboColetor e o descriptor QuantidadeValida (Seção 2.1)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from celular_robo.robo_base import Robo
from celular_robo.modos import ModoColetando
from celular_robo.excecoes import ErroColeta

if TYPE_CHECKING:
    from celular_robo.persistencia import Pedido


class QuantidadeValida:
    """Descriptor: a quantidade coletada fica entre 0 e a quantidade pedida."""

    def __set_name__(self, owner: type, name: str) -> None:
        self.nome_publico = name
        self.nome = "_" + name

    def __get__(self, instance: object | None, owner: type) -> Any:
        if instance is None:
            return self
        return instance.__dict__.get(self.nome, 0)

    def __set__(self, instance: Any, valor: int) -> None:
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

    bandeja: dict[str, int]

    def __init__(self, nome: str, **kwargs: Any) -> None:
        kwargs.setdefault("modo", ModoColetando())
        super().__init__(nome, **kwargs)
        self.bandeja = {}

    def __repr__(self) -> str:
        return f"RoboColetor({self.nome!r}, x={self.x}, y={self.y})"

    def __str__(self) -> str:
        return (
            f"{self.nome} em ({self.x}, {self.y}), {len(self)} item(ns) na bandeja"
        )

    def __len__(self) -> int:
        """Total de itens na bandeja."""
        return sum(self.bandeja.values())

    def __bool__(self) -> bool:
        """Um robô existe independente da bandeja.

        Sem isto, `__len__` deixaria o robô falsy com a bandeja vazia e um
        `if robo:` em qualquer lugar leria "não há robô".
        """
        return True

    def bandeja_completa(self, pedido: Pedido) -> bool:
        """True quando todo codinome do pedido já está na bandeja na
        quantidade pedida (soma os itens repetidos do mesmo codinome)."""
        exigido: dict[str, int] = {}
        for comando in pedido.comandos:
            exigido[comando.codinome] = (
                exigido.get(comando.codinome, 0) + comando.quantidade
            )
        return all(
            self.bandeja.get(codinome, 0) >= quantidade
            for codinome, quantidade in exigido.items()
        )

    def conferir_bandeja(self, pedido: Pedido) -> bool:
        """Notifica "bandeja_pronta" se o pedido está completo, e devolve
        se notificou.

        É o robô que avisa a equipe (Seção 1), não a CLI; o Observer
        EquipeDeTestes reage trocando o modo pra ModoAguardandoVerificacao.
        """
        if not self.bandeja_completa(pedido):
            return False
        self.notificar("bandeja_pronta", lote=getattr(pedido, "lote", None))
        return True

    def processar_pedido(
        self, pedido: Pedido, inicio: int = 0
    ) -> tuple[int, ErroColeta | None]:
        """Executa os comandos do pedido a partir de `inicio` e confere a
        bandeja no fim.

        Devolve (índice do próximo item a processar, erro que interrompeu o
        pedido ou None). Uma coleta recusada vira notificação
        "pedido_rejeitado" e para o pedido — é por aqui que
        RegistroAuditoria enxerga a rejeição (Seção 2.3), em vez de ela ser
        emitida pela CLI.
        """
        indice = inicio
        while indice < len(pedido.comandos):
            comando = pedido.comandos[indice]
            try:
                comando.executar(self)
            except ErroColeta as erro:
                self.notificar(
                    "pedido_rejeitado",
                    codinome=comando.codinome,
                    motivo=str(erro),
                )
                return indice, erro
            indice += 1
        self.conferir_bandeja(pedido)
        return indice, None

    def aprovar_lote(self) -> None:
        """A equipe aprovou: bandeja liberada e robô pronto pra novo pedido.

        O lote sai junto no evento ("itens"), porque a bandeja já foi
        esvaziada quando o Observer é chamado — é esse conteúdo que o
        DespachoTransporte entrega ao RoboTransportador.
        """
        lote = dict(self.bandeja)
        self.bandeja = {}
        self.modo = ModoColetando()
        self.notificar("lote_aprovado", itens=lote)

    def rejeitar_lote(self, motivo: str) -> None:
        """A equipe recusou: volta a coletar o mesmo pedido, mantendo os
        itens já na bandeja (Seção 2.3); a rejeição só é registrada."""
        self.modo = ModoColetando()
        self.notificar("pedido_rejeitado", motivo=motivo)
