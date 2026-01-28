# global-state-extraction Specification

## Purpose
TBD - created by archiving change add-global-state-extraction. Update Purpose after archive.
## Requirements
### Requirement: Parse GLOBAL declarations (Stack-Agnostic)

O sistema MUST detectar e parsear declarações `GLOBAL` preservando tipos WLanguage originais.

#### Scenario: Simple GLOBAL declaration

- **GIVEN** código WLanguage contendo:
  ```wlanguage
  GLOBAL
      gCnn is Connection
      gsUrlAPI is string
  ```
- **WHEN** `GlobalStateExtractor.extract_variables(code, type_code=0, source="Project.wwp")` é chamado
- **THEN** deve retornar lista com 2 `GlobalVariable`:
  - `{name: "gCnn", wlanguage_type: "Connection", scope: APP}`
  - `{name: "gsUrlAPI", wlanguage_type: "string", scope: APP}`
- **AND** tipos são WLanguage originais (NÃO Python/Node/Go)

#### Scenario: GLOBAL with default values

- **GIVEN** código WLanguage contendo:
  ```wlanguage
  GLOBAL
      gnTempoSessao is int = 20
      gsAmbiente is string = "PRODUCAO"
  ```
- **WHEN** declarações são extraídas
- **THEN** deve retornar:
  - `{name: "gnTempoSessao", wlanguage_type: "int", default_value: "20"}`
  - `{name: "gsAmbiente", wlanguage_type: "string", default_value: "PRODUCAO"}`

#### Scenario: Multiple variables same line

- **GIVEN** código WLanguage contendo:
  ```wlanguage
  GLOBAL
      gDtIni, gDtFim are Date
  ```
- **WHEN** declarações são extraídas
- **THEN** deve retornar 2 `GlobalVariable` com `wlanguage_type: "Date"`

#### Scenario: Complex types preserved

- **GIVEN** código WLanguage contendo:
  ```wlanguage
  GLOBAL
      ListaRecebiveis is array of stRecebiceisSintetico
      gjsonParametros is JSON
  ```
- **WHEN** declarações são extraídas
- **THEN** deve retornar tipos WLanguage exatos:
  - `{wlanguage_type: "array of stRecebiceisSintetico"}`
  - `{wlanguage_type: "JSON"}`

---

### Requirement: Extract initialization code

O sistema MUST extrair código de inicialização preservando código WLanguage original.

#### Scenario: Database connection initialization

- **GIVEN** código WLanguage contendo:
  ```wlanguage
  IF HOpenConnection(gCnn) = False THEN
      EndProgram("NÃO FOI POSSÍVEL CONECTAR")
  ELSE
      HChangeConnection("*", gCnn)
  END
  ```
- **WHEN** `GlobalStateExtractor.extract_initialization(code)` é chamado
- **THEN** deve retornar `InitializationBlock` com:
  - `code` contendo código WLanguage original
  - `dependencies: ["gCnn"]`

#### Scenario: Multiple initialization blocks

- **GIVEN** código com inicialização de banco e SMTP
- **WHEN** blocos são extraídos
- **THEN** deve retornar lista ordenada de `InitializationBlock`

---

### Requirement: Categorize by scope

O sistema MUST categorizar variáveis por escopo baseado no `type_code`.

#### Scenario: Project Code scope (APP)

- **GIVEN** declaração em elemento com `type_code: 0`
- **WHEN** escopo é determinado
- **THEN** `scope = Scope.APP`

#### Scenario: Set of Procedures scope (MODULE)

- **GIVEN** declaração em elemento com `type_code: 31`
- **WHEN** escopo é determinado
- **THEN** `scope = Scope.MODULE`

#### Scenario: Page scope (REQUEST)

- **GIVEN** declaração em elemento com `type_code: 38` ou `60`
- **WHEN** escopo é determinado
- **THEN** `scope = Scope.REQUEST`

---

### Requirement: Build stack-agnostic GlobalStateContext

O sistema MUST construir `GlobalStateContext` sem referências a stack específico.

#### Scenario: Context contains only WLanguage types

- **GIVEN** variáveis extraídas com tipos WLanguage
- **WHEN** `GlobalStateContext` é construído
- **THEN** NÃO deve conter tipos Python (AsyncEngine, dict)
- **AND** NÃO deve conter tipos Node (Pool, object)
- **AND** NÃO deve conter tipos Go (*sql.DB)

#### Scenario: Group by scope

- **GIVEN** declarações de app, module e request scope
- **WHEN** `context.get_by_scope(Scope.APP)` é chamado
- **THEN** retorna apenas variáveis de escopo APP

#### Scenario: Get variable by name

- **GIVEN** contexto com variável `gCnn`
- **WHEN** `context.get_variable("gCnn")` é chamado
- **THEN** retorna a variável correspondente

---

### Requirement: Type mapping per stack

O sistema MUST ter TypeMapper separado para cada stack target.

#### Scenario: Python type mapping

- **GIVEN** variável com `wlanguage_type: "Connection"`
- **WHEN** `PythonTypeMapper.map_type("Connection")` é chamado
- **THEN** retorna `MappedType(type_name="AsyncEngine", import_statement="from sqlalchemy...")`

#### Scenario: Node type mapping (extensibility)

- **GIVEN** variável com `wlanguage_type: "Connection"`
- **WHEN** `NodeTypeMapper.map_type("Connection")` é chamado
- **THEN** retorna `MappedType(type_name="Pool", import_statement="const { Pool } = require('pg')")`

#### Scenario: Unknown type fallback

- **GIVEN** variável com tipo WLanguage não mapeado
- **WHEN** type mapping é executado
- **THEN** retorna tipo genérico do stack (`Any`, `object`, `interface{}`)
- **AND** adiciona comentário TODO

---

### Requirement: BaseStateGenerator interface

O sistema MUST ter interface abstrata para geradores de estado.

#### Scenario: Generator receives TypeMapper

- **GIVEN** `PythonStateGenerator` instanciado
- **THEN** deve ter `PythonTypeMapper` como atributo

#### Scenario: Generator methods

- **GIVEN** `BaseStateGenerator` interface
- **THEN** deve ter métodos abstratos:
  - `generate(context, output_dir) -> list[Path]`
  - `get_state_access(var_name) -> str`
  - `get_state_import() -> str`

---

### Requirement: Generate Python state files

O sistema MUST gerar arquivos de estado para stack Python/FastAPI.

#### Scenario: Generate state dataclass

- **GIVEN** `GlobalStateContext` com variáveis
- **WHEN** `PythonStateGenerator.generate(context, output_dir)` é chamado
- **THEN** deve gerar `app/state.py` com:
  ```python
  @dataclass
  class AppState:
      db: AsyncEngine
      params: dict[str, Any]
  ```

#### Scenario: Generate lifespan

- **GIVEN** contexto com `initialization_blocks`
- **WHEN** generator é executado
- **THEN** deve gerar `app/lifespan.py` com `@asynccontextmanager`

#### Scenario: Generate dependencies

- **GIVEN** contexto com app_state
- **WHEN** generator é executado
- **THEN** deve gerar `app/dependencies.py` com:
  ```python
  def get_app_state(request: Request) -> AppState:
      return request.app.state.app_state
  ```

---

### Requirement: Stack-specific state access pattern

O sistema MUST gerar pattern de acesso específico para cada stack.

#### Scenario: Python state access

- **GIVEN** variável `gCnn` convertida
- **WHEN** `PythonStateGenerator.get_state_access("gCnn")` é chamado
- **THEN** retorna `"app_state.db"`

#### Scenario: Node state access (extensibility)

- **GIVEN** variável `gCnn` convertida
- **WHEN** `NodeStateGenerator.get_state_access("gCnn")` é chamado
- **THEN** retorna `"req.appState.db"`

#### Scenario: Go state access (extensibility)

- **GIVEN** variável `gCnn` convertida
- **WHEN** `GoStateGenerator.get_state_access("gCnn")` é chamado
- **THEN** retorna `"appState.DB"`

---

### Requirement: Integrate with code conversion

O sistema MUST substituir referências a globais por pattern do stack.

#### Scenario: Replace global reference in Python

- **GIVEN** código usando `gCnn` e stack target = Python
- **WHEN** código é convertido
- **THEN** deve usar `app_state.db`
- **AND** deve adicionar `app_state: AppState = Depends(get_app_state)` como parâmetro

#### Scenario: Add state import

- **GIVEN** código que usa estado
- **WHEN** convertido para Python
- **THEN** deve incluir `from app.dependencies import get_app_state, AppState`

---

### Requirement: Extensibility for new stacks

O sistema MUST permitir adicionar novos stacks sem modificar extração.

#### Scenario: Add new stack generator

- **GIVEN** novo stack "node" a ser suportado
- **WHEN** desenvolvedor cria `NodeTypeMapper` e `NodeStateGenerator`
- **THEN** extração (`GlobalStateExtractor`) não precisa ser modificada
- **AND** IR (`GlobalStateContext`) não precisa ser modificado

#### Scenario: Register new stack

- **GIVEN** `NodeStateGenerator` implementado
- **WHEN** registrado em `STATE_GENERATORS`
- **THEN** CLI `--stack node` deve funcionar

