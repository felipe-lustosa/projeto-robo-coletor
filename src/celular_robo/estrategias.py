# Strategy — RotaDireta, RotaComDuplaConferencia — enunciado, Seção 2.3.
# (Não confundir com estrategias_base.py — genérico do curso, não editar. Ao
# contrário de Command/Observer/State, aqui você NÃO herda de `Estrategia`:
# escreva sua própria base, ver TODO abaixo — motivo em estrategias_base.py.)
#
# TODO: implemente aqui. Considere uma base comum (RotaColeta) com
# __init_subclass__ registrando cada rota, ver Seção 2.2 (metaprogramação
# aplicada a uma segunda hierarquia).
from abc import ABC, abstractmethod
from celular_robo.robo_base import Direcao

class RotaColeta(ABC):
  _registro = {}

  def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    RotaColeta._registro[cls.__name__] = cls

  @abstractmethod
  def coletar(self, robo):
    ...

  def _navegar_ate(self, robo, posicao):
    tx, ty = posicao
    if robo.x < tx:
      robo.girar_ate(Direcao.LESTE)
      robo.avancar_n(tx - robo.x)
    elif robo.x > tx:
      robo.girar_ate(Direcao.OESTE)
      robo.avancar_n(robo.x - tx)
    if robo.y < ty:
      robo.girar_ate(Direcao.NORTE)
      robo.avancar_n(ty - robo.y)
    elif robo.y > ty:
      robo.girar_ate(Direcao.SUL)
      robo.avancar_n(robo.y - ty)

class RotaDireta(RotaColeta):
  """Vai direto até cada prateleira, sem revalidar o item."""
  def coletar(self, robo, comando):
    self._navegar_ate(robo, comando.posicao)
    comando.quantidade_coletada = comando.quantidade
    robo.bandeja[comando.codinome] = (
      robo.bandeja.get(comando.codinome, 0) + comando.quantidade
    )


class RotaComDuplaConferencia(RotaColeta):
  pass