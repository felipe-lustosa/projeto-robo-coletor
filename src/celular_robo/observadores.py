"""Observer: equipe de testes, trilha de auditoria e despacho do
transporte (Seções 2.3 e 7)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from celular_robo.observadores_base import Observador
from celular_robo.modos import ModoAguardandoVerificacao
from celular_robo.fabrica import criar_robo_configurado
from celular_robo.excecoes import ConfiguracaoInvalida, ErroColeta

if TYPE_CHECKING:
    from celular_robo.robo_base import Robo
    from celular_robo.transportador import RoboTransportador


class EquipeDeTestes(Observador):
    """Reage a "bandeja_pronta" e põe o robô em ModoAguardandoVerificacao."""

    def __init__(self) -> None:
        self.bandeja_pronta = False

    def atualizar(self, evento: str, **dados: Any) -> None:
        if evento == "bandeja_pronta":
            self.bandeja_pronta = True
            robo = dados.get("robo")
            if robo is not None:
                robo.modo = ModoAguardandoVerificacao()
            alvo = f" ({robo.nome})" if robo is not None else ""
            print(f"[EquipeDeTestes] bandeja pronta pra retirada{alvo}.")


class RegistroAuditoria(Observador):
    """Guarda e imprime todo evento notificado pelo robô."""

    def __init__(self) -> None:
        self.eventos: list[tuple[str, dict[str, Any]]] = []

    def atualizar(self, evento: str, **dados: Any) -> None:
        self.eventos.append((evento, dados))
        robo = dados.get("robo")
        alvo = f"[{robo.nome}] " if robo is not None else ""
        extras = {k: v for k, v in dados.items() if k != "robo"}
        print(f"[AUDITORIA] {alvo}{evento}: {extras}")


class DespachoTransporte(Observador):
    """Reage a "lote_aprovado": cria um `RoboTransportador` pela mesma fábrica
    do coletor e manda o lote até o ponto de retirada. O coletor não sabe
    que este observador existe — o handoff é só mais uma reação a um evento
    que ele já emitia.
    """

    def __init__(
        self,
        estrategia_nome: str = "direta",
        area_nome: str = "centro_padrao",
        tipo_nome: str = "RoboTransportador",
        observadores: list[Observador] | None = None,
    ) -> None:
        self.estrategia_nome = estrategia_nome
        self.area_nome = area_nome
        self.tipo_nome = tipo_nome
        self.observadores = list(observadores) if observadores else []
        self.transportador: RoboTransportador | None = None
        self.entregas: list[dict[str, int]] = []

    def atualizar(self, evento: str, **dados: Any) -> None:
        if evento != "lote_aprovado":
            return
        coletor = dados.get("robo")
        itens = dados.get("itens") or {}
        transportador = self._criar_transportador(coletor)
        if transportador is None:
            return
        self.transportador = transportador
        try:
            transportador.carregar(itens)
            entregues = transportador.transportar()
        except ErroColeta as erro:
            self._avisar(coletor, "transporte_falhou", motivo=str(erro))
            return
        self.entregas.append(entregues)

    def _criar_transportador(self, coletor: Robo | None) -> RoboTransportador | None:
        """Cria o transportador, ou registra a recusa do modelo de features.

        A `ConfiguracaoInvalida` é capturada em vez de subir: `notificar`
        percorre os observadores em sequência, e uma exceção aqui impediria
        os demais (auditoria inclusive) de verem o evento.
        """
        nome = f"Transportador-{len(self.entregas) + 1}"
        try:
            transportador = criar_robo_configurado(
                self.tipo_nome, nome,
                estrategia_nome=self.estrategia_nome, area_nome=self.area_nome,
            )
        except ConfiguracaoInvalida as erro:
            self._avisar(coletor, "transporte_recusado", motivo=str(erro))
            return None
        for observador in self.observadores:
            transportador.adicionar_observador(observador)
        return transportador

    def _avisar(self, coletor: Robo | None, evento: str, **dados: Any) -> None:
        """Reemite o problema no coletor, pra cair na trilha de auditoria."""
        if coletor is not None:
            coletor.notificar(evento, **dados)
