class ErroColeta(Exception):
    """Base de toda exceção do domínio de coleta."""


class ConfiguracaoInvalida(ErroColeta):
    """Configuração do robô/rota/área inválida (ex.: área exclui a
    estratégia escolhida)"""


class PedidoInvalido(ErroColeta):
    """Problema no conteúdo do pedido: codinome inexistente, quantidade
    maior que a disponível, pedido vazio, etc."""