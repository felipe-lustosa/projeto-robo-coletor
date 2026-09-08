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
coleta, aprovar e rejeitar retirada.

Valores válidos na configuração:

- `estrategia_nome`: `"direta"` (`RotaDireta`) ou `"com_dupla_conferencia"`
  (`RotaComDuplaConferencia`).
- `area_nome`: `"centro_padrao"` ou `"area_quarentena"`.

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
  configuração de robô/rota/área.
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
- **Quem confere a bandeja é o robô**: `bandeja_completa(pedido)` compara
  codinome a codinome e `conferir_bandeja(pedido)` emite
  `notificar("bandeja_pronta")`; a CLI só chama `conferir_bandeja`.
- **Nenhuma rota deposita item que o robô não alcançou**: `avancar_n` para
  no primeiro obstáculo, então `RotaColeta._navegar_ate` confere a chegada
  e levanta `ColetaBloqueada`.
- **`dados/pedido_coleta_exemplo.json` diverge do trecho da Seção 2.6**: o
  exemplo do enunciado tem um item `urgente` e um `fragil`, exatamente o
  conflito acima. Usei o trecho como referência de schema; o JSON entregue
  roda de ponta a ponta.
- **Aprovar/rejeitar** (Seção 2.3): aprovar limpa a bandeja e volta pra
  `ModoColetando`; rejeitar também volta pra `ModoColetando`, mas mantém os
  itens coletados e o mesmo pedido, registrando a rejeição na auditoria.
- **Extensão opcional `RoboTransportador`** (Seção 7): não implementada.

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
| State (transição via Observer) | `modos.py` — `ModoColetando`, `ModoAguardandoVerificacao`; `robo.py` — `conferir_bandeja` dispara o Observer |
| Modelo de features / LPS (`requires`/`excludes`) | `modelo_features.py` — `TIPOS_VALIDOS`, `ESTRATEGIAS_VALIDAS`, `AREAS_VALIDAS`, `REQUER`, `EXCLUI`, `validar_configuracao`, `validar_item_para_estrategia` |
| Hierarquia de exceções | `excecoes.py` — `ErroColeta`, `ConfiguracaoInvalida`, `PedidoInvalido`, `ColetaBloqueada` |
| Configuração/persistência | `persistencia.py` — `montar_robo_de_config`, `montar_pedido_de_json`, `LOTE_DISPONIVEL` |
| CLI | `cli.py` |
| Testes fornecidos | `tests/test_00_fornecido.py` |
| Testes próprios | `tests/test_configuracao.py`, `tests/test_pedido.py`, `tests/test_fluxo_completo.py` (fixtures em `tests/conftest.py`) |
