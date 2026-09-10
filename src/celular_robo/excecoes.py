"""Hierarquia de exceções do domínio de coleta (Seção 2.5)."""


class ErroColeta(Exception):
    """Base de toda exceção do domínio de coleta."""


class ConfiguracaoInvalida(ErroColeta):
    """Combinação inválida de tipo, rota ou área do robô."""


class PedidoInvalido(ErroColeta):
    """Conteúdo inválido no pedido: codinome, quantidade ou pedido vazio."""


class ColetaBloqueada(ErroColeta):
    """Coleta impedida pelo estado de execução, com config e pedido
    válidos: robô em ModoAguardandoVerificacao, ou prateleira inalcançável
    por obstáculo no caminho."""


class TransporteBloqueado(ErroColeta):
    """Transporte impedido pelo estado de execução: transportador sem carga,
    ou ponto de retirada inalcançável por obstáculo no caminho (Seção 7)."""
