# Tasks: add-global-state-extraction

> **Otimizado para Claude Sonnet 4.5**: Tasks pequenas, focadas, max 3-5 passos cada.

---

## Task 1: Criar dataclasses para GlobalStateExtractor

**File:** `src/wxcode/parser/global_state_extractor.py`

**Steps:**
1. Criar arquivo `global_state_extractor.py`
2. Criar enum `Scope` com valores: `APP`, `MODULE`, `REQUEST`
3. Criar dataclass `GlobalVariable` com campos: `name`, `wlanguage_type`, `default_value`, `scope`, `source_element`, `source_type_code`
4. Criar dataclass `InitializationBlock` com campos: `code`, `dependencies`, `order`

**Acceptance Criteria:**
- [x] Arquivo criado em `src/wxcode/parser/`
- [x] `wlanguage_type` armazena tipo WLanguage original (NÃO Python)
- [x] Docstrings em português

---

## Task 2: Implementar regex para declarações GLOBAL

**File:** `src/wxcode/parser/global_state_extractor.py`

**Steps:**
1. Criar classe `GlobalStateExtractor`
2. Adicionar regex `GLOBAL_BLOCK_PATTERN` para detectar bloco `GLOBAL...`
3. Adicionar regex `DECLARATION_PATTERN` para parsear `nome is tipo` e `nome = valor`
4. Adicionar regex para `a, b, c are tipo`

**Acceptance Criteria:**
- [x] Detecta bloco GLOBAL
- [x] Parseia `gCnn is Connection`
- [x] Parseia `gnTimeout is int = 20`
- [x] Parseia `a, b, c are string`

---

## Task 3: Implementar extract_variables

**File:** `src/wxcode/parser/global_state_extractor.py`

**Steps:**
1. Implementar método `extract_variables(code: str, type_code: int, source: str) -> list[GlobalVariable]`
2. Determinar escopo: `type_code 0 → APP`, `31 → MODULE`, `38/60 → REQUEST`
3. Preservar tipo WLanguage original (não fazer mapeamento)

**Acceptance Criteria:**
- [x] Extrai todas as declarações do bloco GLOBAL
- [x] Escopo correto por type_code
- [x] Tipos são WLanguage originais

---

## Task 4: Implementar extract_initialization

**File:** `src/wxcode/parser/global_state_extractor.py`

**Steps:**
1. Implementar método `extract_initialization(code: str) -> list[InitializationBlock]`
2. Detectar código após bloco GLOBAL (HOpenConnection, etc.)
3. Extrair dependências (variáveis globais referenciadas)

**Acceptance Criteria:**
- [x] Detecta blocos IF/SWITCH após GLOBAL
- [x] Identifica dependências (gCnn, etc.)
- [x] Preserva código WLanguage original

---

## Task 5: Criar GlobalStateContext (IR Stack-Agnostic)

**File:** `src/wxcode/models/global_state_context.py`

**Steps:**
1. Criar arquivo `global_state_context.py`
2. Criar dataclass `GlobalStateContext` com: `variables`, `initialization_blocks`
3. Implementar `get_by_scope(scope: Scope) -> list[GlobalVariable]`
4. Implementar `get_variable(name: str) -> GlobalVariable | None`

**Acceptance Criteria:**
- [x] IR contém APENAS tipos WLanguage
- [x] Sem referências a Python, Node, Go
- [x] Métodos de consulta funcionam

---

## Task 6: Criar interface BaseTypeMapper

**File:** `src/wxcode/generator/type_mapper.py`

**Steps:**
1. Criar arquivo `type_mapper.py`
2. Criar dataclass `MappedType` com: `type_name`, `import_statement`, `default_value`
3. Criar ABC `BaseTypeMapper` com métodos: `map_type()`, `map_default_value()`

**Acceptance Criteria:**
- [x] ABC com `@abstractmethod` em todos os métodos
- [x] `MappedType` é stack-agnostic (pode representar qualquer stack)
- [x] Docstrings em português

---

## Task 7: Implementar PythonTypeMapper

**File:** `src/wxcode/generator/python/type_mapper.py`

**Steps:**
1. Criar pasta `src/wxcode/generator/python/`
2. Criar `type_mapper.py` com classe `PythonTypeMapper(BaseTypeMapper)`
3. Implementar mapeamento: Connection→AsyncEngine, JSON→dict, string→str, etc.
4. Implementar fallback para tipos não mapeados → `Any`

**Acceptance Criteria:**
- [x] Mapeia tipos WLanguage → Python
- [x] Inclui imports necessários
- [x] Tipos não mapeados viram `Any` com TODO

---

## Task 8: Criar interface BaseStateGenerator

**File:** `src/wxcode/generator/state_generator.py`

**Steps:**
1. Criar arquivo `state_generator.py`
2. Criar ABC `BaseStateGenerator` com `__init__(type_mapper: BaseTypeMapper)`
3. Adicionar métodos abstratos: `generate()`, `get_state_access()`, `get_state_import()`

**Acceptance Criteria:**
- [x] Generator recebe TypeMapper no construtor
- [x] Métodos abstratos bem definidos
- [x] Type hints completos

---

## Task 9: Criar template state.py.j2

**File:** `src/wxcode/generator/templates/python/state.py.j2`

**Steps:**
1. Criar template Jinja2 para `app/state.py`
2. Incluir imports dinâmicos baseados nos tipos mapeados
3. Incluir dataclass `AppState` com campos dinâmicos

**Acceptance Criteria:**
- [x] Template gera código Python válido
- [x] Imports corretos por tipo
- [x] Dataclass com type hints

---

## Task 10: Criar template lifespan.py.j2

**File:** `src/wxcode/generator/templates/python/lifespan.py.j2`

**Steps:**
1. Criar template Jinja2 para `app/lifespan.py`
2. Incluir `@asynccontextmanager` e função `lifespan`
3. Incluir blocos de inicialização convertidos e cleanup

**Acceptance Criteria:**
- [x] Template gera código Python válido
- [x] Usa asynccontextmanager
- [x] Inclui yield entre startup e shutdown

---

## Task 11: Criar template dependencies.py.j2

**File:** `src/wxcode/generator/templates/python/dependencies.py.j2`

**Steps:**
1. Criar template Jinja2 para `app/dependencies.py`
2. Incluir função `get_app_state(request: Request) -> AppState`
3. Incluir getters específicos por campo

**Acceptance Criteria:**
- [x] Template gera código Python válido
- [x] Imports do FastAPI corretos
- [x] Type hints corretos

---

## Task 12: Implementar PythonStateGenerator

**File:** `src/wxcode/generator/python/state_generator.py`

**Steps:**
1. Criar classe `PythonStateGenerator(BaseStateGenerator)`
2. Implementar `generate()` usando templates
3. Implementar `get_state_access()` retornando `app_state.var`
4. Implementar `get_state_import()` retornando import correto

**Acceptance Criteria:**
- [x] Gera 3 arquivos: state.py, lifespan.py, dependencies.py
- [x] Usa PythonTypeMapper para mapear tipos
- [x] Arquivos são Python válido

---

## Task 13: Registrar generators no Orchestrator

**File:** `src/wxcode/generator/orchestrator.py`

**Steps:**
1. Criar dict `STATE_GENERATORS = {"python": PythonStateGenerator}`
2. Adicionar método `_get_state_generator(stack: str) -> BaseStateGenerator`
3. Adicionar parâmetro `stack` ao `convert()`

**Acceptance Criteria:**
- [x] Generator selecionado por nome do stack
- [x] Erro claro se stack não suportado
- [x] Default = "python"

---

## Task 14: Adicionar extração de estado ao Orchestrator

**File:** `src/wxcode/generator/orchestrator.py`

**Steps:**
1. Adicionar método `_extract_global_state(elements) -> GlobalStateContext`
2. Usar `GlobalStateExtractor` em Project Code (type_code: 0)
3. Usar `GlobalStateExtractor` em WDGs (type_code: 31)

**Acceptance Criteria:**
- [x] Extrai estado de Project Code
- [x] Extrai estado de WDGs
- [x] Retorna contexto consolidado

---

## Task 15: Gerar arquivos de estado no Orchestrator

**File:** `src/wxcode/generator/orchestrator.py`

**Steps:**
1. Adicionar método `_generate_state_files(context, output_dir, stack)`
2. Usar StateGenerator apropriado para gerar arquivos
3. Chamar no início de `convert()`

**Acceptance Criteria:**
- [x] `app/state.py` gerado
- [x] `app/lifespan.py` gerado
- [x] `app/dependencies.py` gerado

---

## Task 16: Adicionar state_context ao WLanguageConverter

**File:** `src/wxcode/generator/wlanguage_converter.py`

**Steps:**
1. Adicionar parâmetro `state_context: GlobalStateContext | None`
2. Adicionar parâmetro `state_generator: BaseStateGenerator | None`
3. Criar método `_get_state_reference(var_name: str) -> str | None`

**Acceptance Criteria:**
- [x] Parâmetros opcionais adicionados
- [x] Testes existentes continuam passando
- [x] Método usa generator para obter referência

---

## Task 17: Substituir referências globais no código

**File:** `src/wxcode/generator/wlanguage_converter.py`

**Steps:**
1. Em `convert()`, verificar se variável está em `state_context`
2. Se sim, usar `state_generator.get_state_access()` para substituir
3. Adicionar import usando `state_generator.get_state_import()`

**Acceptance Criteria:**
- [x] `gCnn` vira `app_state.db` (Python)
- [x] Import adicionado automaticamente
- [x] Variáveis não mapeadas mantidas

---

## Task 18: Adicionar --stack ao CLI

**File:** `src/wxcode/cli.py`

**Steps:**
1. Adicionar opção `--stack` ao comando `convert` (default: "python")
2. Validar stack contra `STATE_GENERATORS.keys()`
3. Passar stack para orchestrator

**Acceptance Criteria:**
- [x] `--stack python` funciona
- [x] Erro claro para stack inválido
- [x] Help mostra stacks disponíveis

---

## Task 19: Testes para GlobalStateExtractor

**File:** `tests/test_global_state_extractor.py`

**Steps:**
1. Testar extração de declaração simples
2. Testar declaração com default value
3. Testar múltiplas variáveis na mesma linha
4. Testar que tipos são WLanguage (não Python)

**Acceptance Criteria:**
- [x] 4 test cases passando
- [x] Verificar que IR é stack-agnostic

---

## Task 20: Testes para GlobalStateContext

**File:** `tests/test_global_state_context.py`

**Steps:**
1. Testar `get_by_scope()`
2. Testar `get_variable()`
3. Testar que contexto não tem tipos Python

**Acceptance Criteria:**
- [x] Métodos funcionam corretamente
- [x] IR é 100% stack-agnostic

---

## Task 21: Testes para PythonTypeMapper

**File:** `tests/test_python_type_mapper.py`

**Steps:**
1. Testar mapeamento Connection → AsyncEngine
2. Testar mapeamento JSON → dict[str, Any]
3. Testar fallback para tipo desconhecido → Any

**Acceptance Criteria:**
- [x] Mapeamentos corretos
- [x] Imports corretos
- [x] Fallback funciona

---

## Task 22: Testes para PythonStateGenerator

**File:** `tests/test_python_state_generator.py`

**Steps:**
1. Testar geração de `state.py`
2. Testar geração de `lifespan.py`
3. Testar geração de `dependencies.py`
4. Verificar código gerado é válido Python

**Acceptance Criteria:**
- [x] Arquivos gerados são válidos
- [x] `python -m py_compile` passa

---

## Task 23: Teste de integração

**Command:** `wxcode convert Linkpay_ADM --config Producao --stack python`

**Steps:**
1. Executar conversão com extração de estado
2. Verificar `app/state.py` gerado com tipos Python
3. Verificar services usam `app_state.var`
4. Verificar código Python válido

**Acceptance Criteria:**
- [x] Sem erros de execução
- [x] Arquivos de estado presentes
- [x] Referências substituídas

---

## Dependencies Graph

```
Group 1 (Parallel):     1 → 2 → 3 → 4 (Extractor)
                        5 (IR Context)
                        6 (TypeMapper Interface)
                        8 (StateGenerator Interface)

Group 2 (Parallel):     7 (PythonTypeMapper)
                        9 → 10 → 11 → 12 (PythonStateGen)

Group 3 (Sequential):   13 → 14 → 15 (Orchestrator)
                        16 → 17 (WLanguageConverter)
                        18 (CLI)

Group 4 (Parallel):     19, 20, 21, 22 (Tests)

Final:                  23 (Integration)
```

---

## Interdependências

**Com `add-compile-if-extraction`:**
- Ambas modificam `orchestrator.py` → merge sequencial
- Ambas adicionam contexto ao `WLanguageConverter` → coordenar parâmetros
- `add-compile-if-extraction` trata COMPILE IF em inicialização

**Recomendação:** Implementar `add-compile-if-extraction` primeiro, depois esta change.

---

## Extensibilidade (Futuro)

Para adicionar novo stack (ex: Node):
1. Criar `src/wxcode/generator/node/type_mapper.py`
2. Criar `src/wxcode/generator/node/state_generator.py`
3. Criar templates em `templates/node/`
4. Registrar em `STATE_GENERATORS`

Nenhuma modificação necessária em:
- `GlobalStateExtractor`
- `GlobalStateContext`
- `BaseTypeMapper`
- `BaseStateGenerator`
