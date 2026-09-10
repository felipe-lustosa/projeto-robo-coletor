"""Menu interativo do robô coletor (Seção 4)."""

from __future__ import annotations

import json
import os
from typing import Callable

from celular_robo.persistencia import (
    Pedido,
    montar_pedido_de_json,
    montar_robo_de_config,
)
from celular_robo.robo import RoboColetor
from celular_robo.observadores import (
    DespachoTransporte,
    EquipeDeTestes,
    RegistroAuditoria,
)
from celular_robo.modos import ModoAguardandoVerificacao

CAMINHO_BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CONFIG_PADRAO = os.path.join(CAMINHO_BASE, "dados", "config_robo_exemplo.json")
PEDIDO_PADRAO = os.path.join(CAMINHO_BASE, "dados", "pedido_coleta_exemplo.json")


class Sessao:
    """Robô, pedido carregado e observadores da sessão; o menu só orquestra."""

    def __init__(
        self,
        robo: RoboColetor,
        equipe: EquipeDeTestes,
        auditoria: RegistroAuditoria,
        despacho: DespachoTransporte,
    ) -> None:
        self.robo = robo
        self.equipe = equipe
        self.auditoria = auditoria
        self.despacho = despacho
        self.pedido: Pedido | None = None
        self.indice = 0


def iniciar_sessao(caminho_config: str = CONFIG_PADRAO) -> Sessao:
    """Monta o robô do arquivo de config e registra os observadores."""
    with open(caminho_config, encoding="utf-8") as arquivo:
        config = json.load(arquivo)
    robo = montar_robo_de_config(config)
    equipe = EquipeDeTestes()
    auditoria = RegistroAuditoria()
    despacho = DespachoTransporte(observadores=[auditoria])
    robo.adicionar_observador(equipe)
    robo.adicionar_observador(auditoria)
    robo.adicionar_observador(despacho)
    return Sessao(robo, equipe, auditoria, despacho)


def carregar_pedido(sessao: Sessao, caminho_pedido: str = PEDIDO_PADRAO) -> None:
    """Carrega um pedido de coleta na sessão."""
    sessao.pedido = montar_pedido_de_json(caminho_pedido)
    sessao.indice = 0


def listar_pedido(sessao: Sessao) -> None:
    """Mostra os itens do pedido, marcando os já processados."""
    if sessao.pedido is None:
        print("Nenhum pedido carregado.")
        return
    print(f"Lote: {sessao.pedido.lote}")
    for i, comando in enumerate(sessao.pedido.comandos):
        marca = "x" if i < sessao.indice else " "
        print(f"  [{marca}] {comando.codinome} qtd={comando.quantidade} "
              f"pos={comando.posicao} fragil={comando.fragil} "
              f"urgente={comando.urgente}")


def processar_pedido(sessao: Sessao) -> None:
    """Executa os itens restantes; para na primeira falha de coleta."""
    if sessao.pedido is None:
        print("Nenhum pedido carregado.")
        return
    if isinstance(sessao.robo.modo, ModoAguardandoVerificacao):
        print("Bandeja aguardando verificação da equipe — aprove ou rejeite antes.")
        return

    sessao.indice, erro = sessao.robo.processar_pedido(sessao.pedido, sessao.indice)
    if erro is not None:
        parado = sessao.pedido.comandos[sessao.indice]
        print(f"Falha ao coletar {parado.codinome}: {erro}")


def desfazer_ultima_coleta(sessao: Sessao) -> None:
    """Undo do Command: devolve a última coleta (bandeja, contagem e
    histórico do robô) e recua o ponteiro do pedido."""
    if not sessao.robo.historico:
        print("Nada a desfazer.")
        return
    comando = sessao.robo.historico[-1]
    if not comando.desfazer(sessao.robo):
        print("Nada a desfazer.")
        return
    sessao.indice = max(0, sessao.indice - 1)
    print(f"Coleta de {comando.codinome} desfeita.")


def ver_bandeja(sessao: Sessao) -> None:
    """Imprime o conteúdo atual da bandeja."""
    print(f"Bandeja ({len(sessao.robo)} item(ns)): {sessao.robo.bandeja}")


def aprovar_retirada(sessao: Sessao) -> None:
    """Libera a bandeja e deixa o robô pronto pra um novo pedido."""
    if not sessao.equipe.bandeja_pronta:
        print("Bandeja ainda não está pronta.")
        return
    sessao.equipe.bandeja_pronta = False
    sessao.robo.aprovar_lote()
    sessao.pedido = None
    sessao.indice = 0
    print("Retirada aprovada — bandeja liberada, robô pronto pra novo pedido.")
    ver_transporte(sessao)


def rejeitar_retirada(sessao: Sessao) -> None:
    """Recusa a retirada; a bandeja e o pedido continuam como estão."""
    if not sessao.equipe.bandeja_pronta:
        print("Bandeja ainda não está pronta.")
        return
    sessao.equipe.bandeja_pronta = False
    sessao.robo.rejeitar_lote("rejeitado pela equipe")
    print("Retirada rejeitada — itens coletados permanecem, mesmo pedido continua.")


def ver_transporte(sessao: Sessao) -> None:
    """Mostra o transportador despachado no último lote aprovado (Seção 7)."""
    transportador = sessao.despacho.transportador
    if transportador is None:
        print("Nenhum transporte despachado ainda.")
        return
    print(f"Transportador: {transportador}")
    if transportador.entregues:
        print(f"  entregue em {transportador.PONTO_RETIRADA}: "
              f"{transportador.entregues}")
    else:
        print(f"  carga a bordo: {transportador.carga}")


def menu() -> None:
    """Laço do menu interativo."""
    sessao = iniciar_sessao()
    opcoes: dict[str, tuple[str, Callable[[], None] | None]] = {
        "1": ("listar pedido carregado", lambda: listar_pedido(sessao)),
        "2": ("carregar pedido de exemplo", lambda: carregar_pedido(sessao)),
        "3": ("processar pedido", lambda: processar_pedido(sessao)),
        "4": ("ver estado da bandeja", lambda: ver_bandeja(sessao)),
        "5": ("desfazer última coleta", lambda: desfazer_ultima_coleta(sessao)),
        "6": ("aprovar retirada", lambda: aprovar_retirada(sessao)),
        "7": ("rejeitar retirada", lambda: rejeitar_retirada(sessao)),
        "8": ("ver estado do transporte", lambda: ver_transporte(sessao)),
        "0": ("sair", None),
    }
    while True:
        print("\n--- Robô Coletor de Celulares ---")
        for chave, (rotulo, _) in opcoes.items():
            print(f"{chave}) {rotulo}")
        escolha = input("Escolha: ").strip()
        if escolha == "0":
            break
        item = opcoes.get(escolha)
        if item is None:
            print("Opção inválida.")
            continue
        acao = item[1]
        if acao is not None:
            acao()


if __name__ == "__main__":
    menu()
