# Observer — EquipeDeTestes, RegistroAuditoria — enunciado, Seção 2.3.
#
# Herde de `Observador` (observadores_base.py — ABC com registro automático):
#
#   from celular_robo.observadores_base import Observador
#
# TODO: implemente aqui. EquipeDeTestes(Observador) reage a "bandeja_pronta";
# RegistroAuditoria(Observador) loga todo evento (coleta, bandeja pronta,
# pedido rejeitado), pensando em trilha de auditoria, não só depuração.

from celular_robo.observadores_base import Observador
from celular_robo.modos import ModoAguardandoVerificacao

class EquipeDeTestes(Observador):
    def __init__(self):
        self.bandeja_pronta = False

    def atualizar(self, evento, **dados):
        if evento == "bandeja_pronta":
            self.bandeja_pronta = True
            robo = dados.get("robo")
            if robo is not None:
                robo.modo = ModoAguardandoVerificacao()
            alvo = f" ({robo.nome})" if robo else ""
            print(f"[EquipeDeTestes] bandeja pronta pra retirada{alvo}.")


class RegistroAuditoria(Observador):
    pass