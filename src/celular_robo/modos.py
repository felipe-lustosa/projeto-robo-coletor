"""State: modos de operação do robô coletor (Seção 2.3)."""

from celular_robo.modos_base import ModoOperacao
from celular_robo.excecoes import ColetaBloqueada


class ModoColetando(ModoOperacao):
    """Modo normal: movimento e coleta seguem a rota configurada."""

    def mover(self, robo):
        return robo.estrategia.mover(robo)

    def coletar(self, robo, comando):
        """Delega a coleta pra rota, igual mover() — o State escolhe se a
        operação acontece, o Strategy escolhe como."""
        return robo.estrategia.coletar(robo, comando)


class ModoAguardandoVerificacao(ModoOperacao):
    """Bandeja cheia: o robô para até a equipe de testes decidir."""

    def mover(self, robo):
        print(f"{robo.nome} está aguardando verificação da bandeja.")
        return False

    def coletar(self, robo, comando):
        """Recusa iniciar nova coleta antes de a equipe aprovar o lote."""
        raise ColetaBloqueada(
            f"{robo.nome} aguarda verificação da bandeja: a equipe precisa "
            f"decidir sobre o lote antes de coletar {comando.codinome}"
        )
