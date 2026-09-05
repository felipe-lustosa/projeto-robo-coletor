# Robô Coletor de Celulares

## Setup

Python 3.x, biblioteca padrão + `pytest` (única dependência):

```bash
cd celular_robo
pip install -r requirements.txt
```

Não precisa de `pip install -e .` nem de empacotamento — `pyproject.toml` já
configura `pythonpath = ["src"]` pro `pytest` enxergar o pacote
`celular_robo` (que mora em `src/`, não na raiz).

## Como rodar

**Testes** (a partir da raiz do projeto, `celular_robo/`):

```bash
pytest -v
```

**CLI** (a partir da mesma raiz — precisa apontar `PYTHONPATH` pra `src/`,
já que a CLI roda fora do `pytest`, que resolve isso sozinho):

```bash
PYTHONPATH=src python3 -m celular_robo.cli
```

O menu carrega o robô de `dados/config_robo_exemplo.json` ao iniciar.
Opção 2 carrega o pedido de `dados/pedido_coleta_exemplo.json`.

Valores válidos hoje pra configuração (`estrategia_nome`/`area_nome`,
usados no JSON de config e na CLI):

- `estrategia_nome`: `"direta"` (`RotaDireta`) ou `"com_dupla_conferencia"`
  (`RotaComDuplaConferencia`) — o slug é derivado automaticamente do nome
  da classe (`_slug_rota`, `modelo_features.py`), não digitado à mão.
- `area_nome`: `"centro_padrao"` ou `"area_quarentena"`.

## Decisões de projeto

Estrutura de pastas seguida exatamente como sugerida na Seção 3 do
enunciado, sem reorganização.

- **Bandeja**: `dict` interno de `RoboColetor` (`codinome -> quantidade
  coletada`), não uma classe própria — `__len__` soma os valores. Opção
  mais simples entre as duas permitidas pelo enunciado (Seção 2.1).
- **`QuantidadeValida`** (`robo.py`): ao contrário de `Coordenada`, cujo
  teto é fixo (`LADO_GRADE`, igual pra toda instância), o teto de
  "quantidade coletada" varia por item do pedido. Por isso o descriptor lê
  o limite do atributo `quantidade` da própria instância em que mora
  (`ComandoColeta.quantidade`), em vez de receber min/max no construtor.
- **`RotaColeta` não herda de `Estrategia`** (`estrategias.py`): hierarquia
  própria com `__init_subclass__`/`_registro_rotas` dela mesma — se
  herdasse de `Estrategia`, `ESTRATEGIAS_VALIDAS = set(_registro_rotas)`
  viria contaminado com `EstrategiaPadrao`/`Esquiva`/`Zigzag`
  (movimentação livre, sem relação com coleta).
- **`RotaColeta.mover(robo)`**: método concreto (não abstrato) que só
  chama `robo.avancar()`. Existe pra `ModoColetando.mover()` poder
  delegar pra `self.estrategia`, igual `ModoExplorando` delega pra
  `Estrategia.mover` no curso — sem ele, `RotaColeta` só teria `coletar`,
  que exige um `comando` específico e não serve pra movimentação avulsa.
- **Slugs de estratégia** (`NOMES_ROTAS`, `modelo_features.py`): derivados
  automaticamente do nome da classe (`RotaDireta` → `"direta"`,
  `RotaComDuplaConferencia` → `"com_dupla_conferencia"`) via
  `_slug_rota`, em vez de um dicionário digitado à mão — uma rota nova em
  `estrategias.py` já aparece com slug pronto, sem editar
  `modelo_features.py`.
- **Área → obstáculos** (`modelo_features.py`): `"centro_padrao"` não tem
  obstáculo nenhum; `"area_quarentena"` bloqueia a posição `(5, 5)` de
  verdade (`Sensor.ler`/`avancar()` recusam atravessar, não é só um
  rótulo). Esse mapeamento é digitado à mão — área não é uma hierarquia de
  classes como as rotas, não tem `_registro` pra derivar de onde.
- **`fragil=True` e `urgente=True` no mesmo item** (conflito item a item,
  Seção 2.4) → `PedidoInvalido`, checado ao carregar o pedido
  (`persistencia.montar_pedido_de_json`). Escolhi `PedidoInvalido` em vez
  de `ConfiguracaoInvalida` porque o defeito está no conteúdo do item em
  si (contraditório independente de qual robô for processá-lo), não numa
  configuração de robô/rota/área.
- **Pedido com item `urgente` e item `fragil` diferentes** (conflito entre
  itens do mesmo pedido, Seção 2.4) → também `PedidoInvalido`, mesmo
  lugar/momento (carregamento do pedido, antes de processar qualquer
  item) — `robo.estrategia` é única por robô, não há como atender as duas
  exigências ao mesmo tempo, e a checagem não pertence a
  `validar_configuracao` porque esta só enxerga o JSON de config do robô,
  sem visibilidade dos itens do pedido.
- **`requires` de item para estratégia** (`fragil` exige
  `RotaComDuplaConferencia`, `urgente` exige `RotaDireta`): declarado na
  tabela `REQUER` (`modelo_features.py`, ao lado de `EXCLUI`) e aplicado
  por `validar_item_para_estrategia`, que `ComandoColeta.executar(robo)`
  chama no momento da coleta → `ConfiguracaoInvalida`. A checagem é no
  momento da coleta, e não em `validar_configuracao`, porque é aí que se
  sabe ao mesmo tempo o item (do pedido) e a estratégia atual (do robô);
  antes disso nenhum dos dois lados sozinho tem essa informação completa.
  A tabela fica em `modelo_features.py` (não espalhada em `isinstance`
  dentro do comando) pra `requires` e `excludes` morarem no mesmo lugar,
  como o enunciado organiza a Seção 2.4.
- **Item inválido entre vários no mesmo pedido** (Seção 2.5) → rejeita o
  pedido inteiro (`PedidoInvalido` na primeira falha), não processa os
  itens válidos e pula o inválido. Opção mais simples; a alternativa
  (pular e logar via `RegistroAuditoria`) também seria defensável.
- **Representação d"o lote"** (Seção 2.5): o JSON do pedido só traz o
  *nome* do lote, então a relação codinome → quantidade disponível mora
  em `LOTE_DISPONIVEL`, um `dict` de módulo em `persistencia.py` — a
  primeira das duas opções sugeridas pelo enunciado (dict no módulo que
  faz a validação, ou arquivo próprio em `dados/`); escolhi o dict por
  não exigir um terceiro arquivo de dados só pra isso.
  `montar_pedido_de_json(caminho, lote_disponivel=None)` aceita um lote
  injetado, usado pelos testes pra não depender dos codinomes de produção.
  Contra esse lote são validados os três casos de `PedidoInvalido` da
  Seção 2.5: codinome inexistente no lote, quantidade pedida maior que a
  disponível (somada por codinome, se o mesmo aparecer em mais de um
  item) e pedido vazio.
- **Histórico de comandos** (Seção 2.3): `ComandoColeta.executar(robo)`
  guarda o comando em `robo._historico_comandos` (exposto pela property
  `robo.historico`, herdada de `Robo`) depois da coleta dar certo, e
  `desfazer(robo)` o remove de lá — o histórico é a pilha que o *undo*
  consome, não um log paralelo.
- **Depósito na bandeja passa sempre por `RotaColeta._depositar`**: é esse
  método que emite `robo.notificar("item_coletado", ...)`, então é por ele
  que `RegistroAuditoria` enxerga a coleta. As duas rotas o reaproveitam
  em vez de mexer em `robo.bandeja` direto — se `RotaDireta` fizesse o
  depósito à mão, a coleta sumiria da trilha de auditoria justamente na
  configuração padrão.
- **Todo evento passa por `robo.notificar`**, inclusive `pedido_rejeitado`
  (na CLI, tanto na falha ao coletar quanto na rejeição da equipe) — a CLI
  não chama `RegistroAuditoria.atualizar` direto, pra o Observer continuar
  sendo o único caminho de propagação de evento.
- **Retorno de `montar_pedido_de_json`**: um `Pedido = namedtuple("Pedido",
  ["lote", "comandos"])`, não só a lista de `ComandoColeta` — mantém o
  nome do lote (campo `"lote"` do JSON) acessível pra CLI/testes sem virar
  parâmetro solto.
- **`dados/pedido_coleta_exemplo.json` diverge do trecho ilustrativo do
  enunciado** (Seção 2.6): o exemplo do enunciado tem um item `urgente` e
  um item `fragil` diferentes — exatamente o conflito descrito acima, que
  seria rejeitado com `PedidoInvalido`. Usei aquele trecho só como
  referência de schema; o JSON entregue tem um item `urgente` e um item
  neutro, pra ser um exemplo que roda de ponta a ponta sem cair na
  rejeição.
- **Aprovar/rejeitar bandeja** (CLI, Seção 1): aprovar limpa a bandeja,
  volta `robo.modo` pra `ModoColetando` e libera um pedido novo; rejeitar
  também volta pra `ModoColetando`, mas mantém os itens já coletados na
  bandeja e o mesmo pedido carregado (não reprocessa do zero) — a
  rejeição em si é registrada via `RegistroAuditoria`, não como
  reprocessamento automático.
- **Extensão opcional `RoboTransportador`** (Seção 7, bônus): não
  implementada.

## Mapeamento pra aulas da disciplina

| Mecanismo | Arquivo / Classe |
|---|---|
| Descriptor de posição (herdado, não reescrito) | `robo_base.py` — `Coordenada`, `Robo.x`/`Robo.y` |
| Descriptor de quantidade | `robo.py` — `QuantidadeValida` (usado em `comandos.py` — `ComandoColeta.quantidade_coletada`) |
| Métodos especiais (`__str__`/`__repr__`/`__len__`) | `robo.py` — `RoboColetor` |
| `__init_subclass__`/registro automático — robôs | `robo_base.py` — `Robo._registro` (fornecido, não editado) |
| `__init_subclass__`/registro automático — rotas | `estrategias.py` — `RotaColeta._registro_rotas` |
| Strategy | `estrategias.py` — `RotaColeta`, `RotaDireta`, `RotaComDuplaConferencia` |
| Command (com `desfazer`) | `comandos.py` — `ComandoColeta` |
| Factory | `fabrica.py` — `criar_robo_coletor`, `criar_robo_configurado` |
| Observer | `observadores.py` — `EquipeDeTestes`, `RegistroAuditoria` |
| State (transição via Observer) | `modos.py` — `ModoColetando`, `ModoAguardandoVerificacao` |
| Modelo de features / LPS (`requires`/`excludes`) | `modelo_features.py` — `TIPOS_VALIDOS`, `ESTRATEGIAS_VALIDAS`, `AREAS_VALIDAS`, `REQUER`, `EXCLUI`, `validar_configuracao`, `validar_item_para_estrategia` |
| Hierarquia de exceções | `excecoes.py` — `ErroColeta`, `ConfiguracaoInvalida`, `PedidoInvalido` |
| Configuração/persistência | `persistencia.py` — `montar_robo_de_config`, `montar_pedido_de_json`, `LOTE_DISPONIVEL` |
| CLI | `cli.py` |
| Testes fornecidos | `tests/test_00_fornecido.py` |
| Testes próprios | `tests/test_configuracao.py`, `tests/test_pedido.py`, `tests/test_fluxo_completo.py` (fixtures em `tests/conftest.py`) |
