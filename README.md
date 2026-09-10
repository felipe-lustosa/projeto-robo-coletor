# Robô Coletor de Celulares

Projeto final da disciplina: um `RoboColetor` recebe um pedido de coleta em
JSON, navega pela grade do laboratório, deposita os itens na bandeja e avisa
a equipe de testes quando o lote está pronto pra retirada.

## Setup

Python 3.x, biblioteca padrão + `pytest` (única dependência):

```bash
pip install -r requirements.txt
```

Não precisa de `pip install -e .`: o `pyproject.toml` já configura
`pythonpath = ["src"]` pro `pytest` enxergar o pacote `celular_robo`.

## Como rodar

**Testes** (a partir da raiz do projeto):

```bash
pytest -v
```

**CLI** (a mesma raiz; fora do `pytest` é preciso apontar `PYTHONPATH` pra `src/`):

```bash
PYTHONPATH=src python3 -m celular_robo.cli
```

O menu carrega o robô de `dados/config_robo_exemplo.json` ao iniciar, e a
opção 2 carrega o pedido de `dados/pedido_coleta_exemplo.json`. Opções:
listar pedido, carregar pedido, processar, ver bandeja, desfazer última
coleta, aprovar e rejeitar retirada, ver estado do transporte.

Valores válidos na configuração:

- `estrategia_nome`: `"direta"` (`RotaDireta`) ou `"com_dupla_conferencia"`
  (`RotaComDuplaConferencia`).
- `area_nome`: `"centro_padrao"` ou `"area_quarentena"`.
- `tipo_nome`: `"RoboColetor"` ou `"RoboTransportador"` (Seção 7) — o
  transportador não é configurado por arquivo, quem o cria é o
  `DespachoTransporte`.

## Decisões de projeto

Estrutura de pastas igual à sugerida na Seção 3 do enunciado, sem
reorganização.

- **Bandeja** (Seção 2.1): `dict` interno de `RoboColetor`
  (`codinome -> quantidade coletada`), não uma classe própria; `__len__`
  soma os valores.
- **`QuantidadeValida`** (`robo.py`): o teto de "quantidade coletada" varia
  por item, então o descriptor lê o limite do atributo `quantidade` da
  instância em que mora (`ComandoColeta`), em vez de receber min/max no
  construtor como `Coordenada`.
- **Método `navegar_ate` público em `RotaColeta`**: era `_navegar_ate`,
  privado, quando só a coleta navegava; o `RoboTransportador` (Seção 7) usa
  a mesma rota pra chegar ao ponto de retirada, então virou parte da
  interface da estratégia.
- **`RotaColeta` não herda de `Estrategia`** (Seção 2.2): hierarquia própria
  com `__init_subclass__`/`_registro_rotas`, senão
  `ESTRATEGIAS_VALIDAS = set(_registro_rotas)` viria contaminado com as
  estratégias de movimentação do curso.
- **Slugs de estratégia** (`NOMES_ROTAS`): derivados do nome da classe por
  `_slug_rota` (`RotaDireta` → `"direta"`), não digitados à mão — uma rota
  nova já nasce com slug.
- **Área → obstáculos** (Seção 2.4): `"centro_padrao"` sem obstáculos;
  `"area_quarentena"` bloqueia a posição `(5, 5)` de verdade
  (`Sensor.ler`/`avancar()` recusam atravessar). O mapeamento é digitado à
  mão: área não é hierarquia de classes, não há registro pra derivar.
- **`fragil=True` e `urgente=True` no mesmo item** (Seção 2.4) →
  `PedidoInvalido`, ao carregar o pedido. O defeito está no conteúdo do
  item, contraditório independente de qual robô o processe, não numa
  configuração de robô/rota/área. A mesma exceção vale se o
  `ComandoColeta` for construído à mão e executado sem passar pelo JSON
  (`validar_item_para_estrategia`) — a escolha é uma só, qualquer que seja
  o ponto de entrada.
- **Pedido com um item `urgente` e outro `fragil`** (Seção 2.4) → também
  `PedidoInvalido`, no carregamento e antes de processar qualquer item:
  `robo.estrategia` é única por robô. A checagem não cabe em
  `validar_configuracao`, que só enxerga o JSON de config.
- **`requires` de item para estratégia**: declarado em `REQUER`
  (`modelo_features.py`, ao lado de `EXCLUI`) e aplicado por
  `validar_item_para_estrategia`, chamado por `ComandoColeta.executar` →
  `ConfiguracaoInvalida`. É na coleta que se conhecem ao mesmo tempo o item
  e a estratégia atual do robô.
- **Item inválido entre vários no mesmo pedido** (Seção 2.5) → rejeita o
  pedido inteiro na primeira falha, em vez de processar os válidos e pular
  o inválido.
- **Representação do lote** (Seção 2.5): a relação codinome → quantidade
  disponível mora em `LOTE_DISPONIVEL`, um `dict` em `persistencia.py` — a
  opção "dict no módulo que faz a validação". `montar_pedido_de_json`
  aceita `lote_disponivel` injetado, usado pelos testes.
- **`ColetaBloqueada(ErroColeta)`**, terceiro ramo além dos dois exigidos
  pela Seção 2.5: a coleta que não pôde acontecer agora, com configuração e
  pedido válidos — robô em `ModoAguardandoVerificacao`, ou prateleira
  inalcançável por obstáculo. `except ErroColeta` continua pegando tudo.
- **O State decide *se*, o Strategy decide *como***: os modos têm
  `coletar(robo, comando)` ao lado de `mover(robo)`, e
  `ComandoColeta.executar` chama `robo.modo.coletar(...)`. Assim a regra
  "só depois da equipe aprovar o robô começa um pedido novo" vive no
  modelo, não na CLI.
- **O fluxo do pedido é do robô, não da CLI**:
  `processar_pedido(pedido, inicio)` executa os comandos, emite
  `notificar("pedido_rejeitado")` na primeira coleta recusada e confere a
  bandeja no fim (`bandeja_completa` compara codinome a codinome,
  `conferir_bandeja` emite `notificar("bandeja_pronta")`). Devolve
  `(índice do próximo item, erro ou None)`, e a CLI só imprime o resultado —
  assim os três eventos que a Seção 2.3 pede da auditoria (coleta, bandeja
  pronta, pedido rejeitado) saem todos do modelo e ficam testáveis.
- **As duas conferências da `RotaComDuplaConferencia` conferem coisas
  diferentes**: `_conferir_posicao` checa se o robô parou na prateleira
  certa; `_revalidar_item` checa o item em si (codinome, quantidade) e
  emite `"item_revalidado"` — o custo extra da rota lenta fica visível na
  trilha de auditoria, e a `RotaDireta` nunca emite esse evento.
- **`desfazer` de comando nunca executado é um no-op**: devolve `False` e
  não notifica `"coleta_desfeita"`, pra não sujar a auditoria com um undo
  vazio.
- **Nenhuma rota deposita item que o robô não alcançou**: `avancar_n` para
  no primeiro obstáculo, então `RotaColeta.navegar_ate` confere a chegada
  e levanta `ColetaBloqueada`.
- **`dados/pedido_coleta_exemplo.json` diverge do trecho da Seção 2.6 num
  campo**: o exemplo do enunciado tem um item `urgente` e um `fragil`,
  exatamente o conflito acima. Mantive lote, codinomes, posições e
  quantidades do enunciado, e só o `"Projeto Vesper"` deixou de ser
  `fragil` — assim o JSON entregue roda de ponta a ponta com a config de
  exemplo (`"direta"`).
- **Tipagem**: todos os módulos autorais têm anotações de tipo (`from
  __future__ import annotations`, imports só de tipo sob `TYPE_CHECKING`
  para evitar ciclos entre `robo`/`comandos`/`modos`/`persistencia`). Os
  `*_base.py` fornecidos não são anotados, e não foram tocados.
- **Aprovar/rejeitar** (Seção 2.3): `RoboColetor.aprovar_lote()` limpa a
  bandeja e volta pra `ModoColetando`; `rejeitar_lote(motivo)` também volta
  pra `ModoColetando`, mas mantém os itens coletados e o mesmo pedido,
  registrando a rejeição via `pedido_rejeitado`. A CLI só cuida do flag da
  `EquipeDeTestes` e do pedido carregado na sessão.

## Extensão opcional — `RoboTransportador` (Seção 7)

Implementada: aprovada a bandeja, um segundo robô leva o lote até o ponto de
retirada (o carrinho robótico em si continua fora de escopo).

- **Módulo próprio, `transportador.py`**: única divergência da estrutura da
  Seção 3, que não previa a extensão. Deixa visível que o tipo novo entra em
  `Robo._registro` — e em `TIPOS_VALIDOS` — só por herdar de `Robo`, sem
  tocar em `robo.py`. Modos e observador novos ficaram nos arquivos de
  sempre.
- **`excludes` novo**: `EXCLUI["RoboTransportador"] = {"area_quarentena"}`.
  Com restrição de área×rota e de tipo×área, `EXCLUI` passou a ser lido como
  "feature → features incompatíveis", conferido nos dois sentidos.
- **Handoff via Observer**: `DespachoTransporte` reage a `"lote_aprovado"`,
  cria o transportador por `criar_robo_configurado` e chama
  `carregar`/`transportar`. O coletor não conhece o transportador, só emite
  o evento que já emitia — agora com `itens=`, porque a bandeja é esvaziada
  antes de notificar.
- **State do transportador**: `ModoAguardandoCarga` recusa `transportar` sem
  carga; `ModoTransportando` navega até `PONTO_RETIRADA` e confirma a
  entrega. Mesma divisão do coletor.
- **`TransporteBloqueado(ErroColeta)`**: transporte sem carga ou ponto de
  retirada inalcançável. `DespachoTransporte` captura isso e
  `ConfiguracaoInvalida`, reemitindo como `"transporte_falhou"`/
  `"transporte_recusado"` — `notificar` percorre os observadores em
  sequência, e uma exceção ali cortaria a auditoria.
- **`criar_robo_coletor` não impõe mais o modo inicial**: cada tipo define o
  seu no `__init__`, senão a fábrica genérica teria que conhecer os tipos um
  a um.

## Mapeamento pra aulas da disciplina

| Mecanismo | Arquivo / Classe |
|---|---|
| Descriptor de posição (herdado, não reescrito) | `robo_base.py` — `Coordenada`, `Robo.x`/`Robo.y` |
| Descriptor de quantidade | `robo.py` — `QuantidadeValida` (usado em `ComandoColeta.quantidade_coletada`) |
| Métodos especiais (`__str__`/`__repr__`/`__len__`/`__bool__`) | `robo.py` — `RoboColetor` |
| `__init_subclass__`/registro automático — robôs | `robo_base.py` — `Robo._registro` (fornecido) |
| `__init_subclass__`/registro automático — rotas | `estrategias.py` — `RotaColeta._registro_rotas` |
| Strategy | `estrategias.py` — `RotaColeta`, `RotaDireta`, `RotaComDuplaConferencia` |
| Command (com `desfazer`) | `comandos.py` — `ComandoColeta` |
| Factory | `fabrica.py` — `criar_robo_coletor`, `criar_robo_configurado` |
| Observer | `observadores.py` — `EquipeDeTestes`, `RegistroAuditoria` |
| State (transição via Observer) | `modos.py` — `ModoColetando`, `ModoAguardandoVerificacao`; `robo.py` — `conferir_bandeja`/`aprovar_lote`/`rejeitar_lote` disparam o Observer |
| Modelo de features / LPS (`requires`/`excludes`) | `modelo_features.py` — `TIPOS_VALIDOS`, `ESTRATEGIAS_VALIDAS`, `AREAS_VALIDAS`, `REQUER`, `EXCLUI`, `validar_configuracao`, `validar_item_para_estrategia` |
| Hierarquia de exceções | `excecoes.py` — `ErroColeta`, `ConfiguracaoInvalida`, `PedidoInvalido`, `ColetaBloqueada` |
| Configuração/persistência | `persistencia.py` — `montar_robo_de_config`, `montar_pedido_de_json`, `LOTE_DISPONIVEL` |
| CLI | `cli.py` |
| Testes fornecidos | `tests/test_00_fornecido.py` |
| Testes próprios | `tests/test_configuracao.py`, `tests/test_pedido.py`, `tests/test_fluxo_completo.py` (fixtures em `tests/conftest.py`) |
| Extensão Seção 7 — segundo tipo no mesmo registro | `transportador.py` — `RoboTransportador` |
| Extensão Seção 7 — State do transportador | `modos.py` — `ModoAguardandoCarga`, `ModoTransportando` |
| Extensão Seção 7 — handoff via Observer | `observadores.py` — `DespachoTransporte` |
| Extensão Seção 7 — `excludes` novo | `modelo_features.py` — `EXCLUI["RoboTransportador"]` |
| Extensão Seção 7 — testes | `tests/test_transportador.py` |
