"""State: modos de operação do robô coletor (Seção 2.3)."""

from celular_robo.modos_base import ModoOperacao


class ModoColetando(ModoOperacao):
    """Modo normal: o movimento segue a rota configurada."""

    def mover(self, robo):
        return robo.estrategia.mover(robo)


class ModoAguardandoVerificacao(ModoOperacao):
    """Bandeja cheia: o robô para até a equipe de testes decidir."""

    def mover(self, robo):
        print(f"{robo.nome} está aguardando verificação da bandeja.")
        return False
