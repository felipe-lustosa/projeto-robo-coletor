"""Menu interativo do robô coletor (Seção 4)."""

import json
import os

from celular_robo.persistencia import montar_robo_de_config, montar_pedido_de_json
from celular_robo.observadores import EquipeDeTestes, RegistroAuditoria
from celular_robo.modos import ModoColetando, ModoAguardandoVerificacao
from celular_robo.excecoes import ErroColeta

CAMINHO_BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CONFIG_PADRAO = os.path.join(CAMINHO_BASE, "dados", "config_robo_exemplo.json")
PEDIDO_PADRAO = os.path.join(CAMINHO_BASE, "dados", "pedido_coleta_exemplo.json")


class Sessao:
    """Robô, pedido carregado e observadores da sessão; o menu só orquestra."""

    def __init__(self, robo, equipe, auditoria):
        self.robo = robo
        self.equipe = equipe
        self.auditoria = auditoria
        self.pedido = None
        self.indice = 0


def iniciar_sessao(caminho_config=CONFIG_PADRAO):
    """Monta o robô do arquivo de config e registra os observadores."""
    with open(caminho_config, encoding="utf-8") as arquivo:
        config = json.load(arquivo)
    robo = montar_robo_de_config(config)
    equipe = EquipeDeTestes()
    auditoria = RegistroAuditoria()
    robo.adicionar_observador(equipe)
    robo.adicionar_observador(auditoria)
    return Sessao(robo, equipe, auditoria)


def carregar_pedido(sessao, caminho_pedido=PEDIDO_PADRAO):
    """Carrega um pedido de coleta na sessão."""
    sessao.pedido = montar_pedido_de_json(caminho_pedido)
    sessao.indice = 0


def listar_pedido(sessao):
    """Mostra os itens do pedido, marcando os já processados."""
    if sessao.pedido is None:
        print("Nenhum pedido carregado.")
        return
    print(f"Lote: {sessao.pedido.lote}")
    for i, comando in enumerate(sessao.pedido.comandos):
        marca = "x" if i < sessao.indice else " "
        print(f"  [{marca}] {comando.codinome} qtd={comando.quantidade} "
              f"pos={comando.posicao} fragil={comando.fragil} urgente={comando.urgente}")


def processar_pedido(sessao):
    """Executa os itens restantes; para na primeira falha de coleta."""
    if sessao.pedido is None:
        print("Nenhum pedido carregado.")
        return
    if isinstance(sessao.robo.modo, ModoAguardandoVerificacao):
        print("Bandeja aguardando verificação da equipe — aprove ou rejeite antes.")
        return

    while sessao.indice < len(sessao.pedido.comandos):
        comando = sessao.pedido.comandos[sessao.indice]
        try:
            comando.executar(sessao.robo)
        except ErroColeta as erro:
            sessao.robo.notificar("pedido_rejeitado", motivo=str(erro))
            print(f"Falha ao coletar {comando.codinome}: {erro}")
            return
        sessao.indice += 1

    sessao.robo.conferir_bandeja(sessao.pedido)


def desfazer_ultima_coleta(sessao):
    """Undo do Command: devolve a última coleta (bandeja, contagem e
    histórico do robô) e recua o ponteiro do pedido."""
    if not sessao.robo.historico:
        print("Nada a desfazer.")
        return
    comando = sessao.robo.historico[-1]
    comando.desfazer(sessao.robo)
    sessao.indice = max(0, sessao.indice - 1)
    print(f"Coleta de {comando.codinome} desfeita.")


def ver_bandeja(sessao):
    """Imprime o conteúdo atual da bandeja."""
    print(f"Bandeja ({len(sessao.robo)} item(ns)): {sessao.robo.bandeja}")


def aprovar_retirada(sessao):
    """Libera a bandeja e deixa o robô pronto pra um novo pedido."""
    if not sessao.equipe.bandeja_pronta:
        print("Bandeja ainda não está pronta.")
        return
    sessao.equipe.bandeja_pronta = False
    sessao.robo.bandeja = {}
    sessao.robo.modo = ModoColetando()
    sessao.pedido = None
    print("Retirada aprovada — bandeja liberada, robô pronto pra novo pedido.")


def rejeitar_retirada(sessao):
    """Recusa a retirada; a bandeja e o pedido continuam como estão."""
    if not sessao.equipe.bandeja_pronta:
        print("Bandeja ainda não está pronta.")
        return
    sessao.equipe.bandeja_pronta = False
    sessao.robo.notificar("pedido_rejeitado", motivo="rejeitado pela equipe")
    sessao.robo.modo = ModoColetando()
    print("Retirada rejeitada — itens coletados permanecem, mesmo pedido continua.")


def menu():
    """Laço do menu interativo."""
    sessao = iniciar_sessao()
    opcoes = {
        "1": ("listar pedido carregado", lambda: listar_pedido(sessao)),
        "2": ("carregar pedido de exemplo", lambda: carregar_pedido(sessao)),
        "3": ("processar pedido", lambda: processar_pedido(sessao)),
        "4": ("ver estado da bandeja", lambda: ver_bandeja(sessao)),
        "5": ("desfazer última coleta", lambda: desfazer_ultima_coleta(sessao)),
        "6": ("aprovar retirada", lambda: aprovar_retirada(sessao)),
        "7": ("rejeitar retirada", lambda: rejeitar_retirada(sessao)),
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
        item[1]()


if __name__ == "__main__":
    menu()
