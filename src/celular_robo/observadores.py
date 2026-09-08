"""Observer: equipe de testes e trilha de auditoria (Seção 2.3)."""

from celular_robo.observadores_base import Observador
from celular_robo.modos import ModoAguardandoVerificacao


class EquipeDeTestes(Observador):
    """Reage a "bandeja_pronta" e põe o robô em ModoAguardandoVerificacao."""

    def __init__(self):
        self.bandeja_pronta = False

    def atualizar(self, evento, **dados):
        if evento == "bandeja_pronta":
            self.bandeja_pronta = True
            robo = dados.get("robo")
            if robo is not None:
                robo.modo = ModoAguardandoVerificacao()
            alvo = f" ({robo.nome})" if robo is not None else ""
            print(f"[EquipeDeTestes] bandeja pronta pra retirada{alvo}.")


class RegistroAuditoria(Observador):
    """Guarda e imprime todo evento notificado pelo robô."""

    def __init__(self):
        self.eventos = []

    def atualizar(self, evento, **dados):
        self.eventos.append((evento, dados))
        robo = dados.get("robo")
        alvo = f"[{robo.nome}] " if robo is not None else ""
        extras = {k: v for k, v in dados.items() if k != "robo"}
        print(f"[AUDITORIA] {alvo}{evento}: {extras}")
