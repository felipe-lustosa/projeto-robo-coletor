"""Hierarquia de exceções do domínio de coleta (Seção 2.5)."""


class ErroColeta(Exception):
    """Base de toda exceção do domínio de coleta."""


class ConfiguracaoInvalida(ErroColeta):
    """Combinação inválida de tipo, rota ou área do robô."""


class PedidoInvalido(ErroColeta):
    """Conteúdo inválido no pedido: codinome, quantidade ou pedido vazio."""
