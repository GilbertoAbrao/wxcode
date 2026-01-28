# Design: add-global-state-extraction

## Context

Projetos WinDev usam variáveis globais extensivamente. O código está distribuído em:
- **Project Code** (`type_code: 0`): Inicialização da aplicação
- **Set of Procedures** (`type_code: 31`): Módulos de lógica de negócio
- **Page Code** (`type_code: 38/60`): UI e eventos

A conversão deve suportar múltiplos stacks target, cada um com seus próprios patterns idiomáticos.

## Architecture Decisions

### AD1: IR 100% Stack-Agnostic

**Opções consideradas:**
1. IR com tipos Python já mapeados → acoplamento, difícil adicionar stacks
2. IR com tipos genéricos abstratos → complexidade desnecessária
3. **IR com tipos WLanguage originais** → simples, extensível ✅

**Decisão:** O `GlobalStateContext` contém APENAS informações WLanguage. Mapeamento de tipos fica na camada de geração.

```python
# CORRETO - IR agnóstico
@dataclass
class GlobalVariable:
    name: str
    wlanguage_type: str          # "Connection" - tipo original
    default_value: str | None    # "20" - valor original

# INCORRETO - IR acoplado a Python
@dataclass
class GlobalVariable:
    name: str
    python_type: str             # ❌ Acoplado a Python
    python_import: str           # ❌ Acoplado a Python
```

### AD2: TypeMapper por Stack

**Decisão:** Cada stack tem seu próprio `TypeMapper`:

```python
class BaseTypeMapper(ABC):
    @abstractmethod
    def map_type(self, wlanguage_type: str) -> MappedType: ...

class PythonTypeMapper(BaseTypeMapper):
    MAPPINGS = {
        "Connection": MappedType("AsyncEngine", "from sqlalchemy.ext.asyncio import AsyncEngine"),
        "JSON": MappedType("dict[str, Any]", "from typing import Any"),
        "string": MappedType("str", None),
    }

class NodeTypeMapper(BaseTypeMapper):
    MAPPINGS = {
        "Connection": MappedType("Pool", "const { Pool } = require('pg')"),
        "JSON": MappedType("object", None),
        "string": MappedType("string", None),
    }
```

### AD3: PatternMapper por Stack

**Decisão:** Cada stack define como converter variáveis globais para seus patterns:

| Stack | Pattern | Acesso |
|-------|---------|--------|
| Python/FastAPI | `app.state` + `Depends()` | `state: AppState = Depends(get_app_state)` |
| Node/Express | `app.locals` + middleware | `req.appState` |
| Go/Fiber | `c.Locals()` | `c.Locals("appState").(*AppState)` |

### AD4: Separação Extração vs Geração

**Decisão:** Arquitetura em 3 camadas bem definidas:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ CAMADA 1: EXTRAÇÃO (Stack-Agnostic)                                     │
│                                                                         │
│ GlobalStateExtractor                                                    │
│   └─► GlobalStateContext (IR puro, tipos WLanguage)                    │
│                                                                         │
│ Responsabilidades:                                                      │
│   - Parsear declarações GLOBAL                                          │
│   - Extrair código de inicialização                                     │
│   - Determinar escopo (app/module/request)                              │
│   - NÃO fazer mapeamento de tipos                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ CAMADA 2: MAPEAMENTO (Por Stack)                                        │
│                                                                         │
│ BaseTypeMapper (ABC)                                                    │
│   ├─► PythonTypeMapper                                                  │
│   ├─► NodeTypeMapper                                                    │
│   └─► GoTypeMapper                                                      │
│                                                                         │
│ Responsabilidades:                                                      │
│   - Mapear WLanguage types → Stack types                                │
│   - Gerar imports/requires necessários                                  │
│   - Definir patterns de acesso                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ CAMADA 3: GERAÇÃO (Por Stack)                                           │
│                                                                         │
│ BaseStateGenerator (ABC)                                                │
│   ├─► PythonStateGenerator (FastAPI + Depends)                          │
│   ├─► NodeStateGenerator (Express + middleware)                         │
│   └─► GoStateGenerator (Fiber + context)                                │
│                                                                         │
│ Responsabilidades:                                                      │
│   - Usar TypeMapper para obter tipos do stack                           │
│   - Gerar arquivos de estado                                            │
│   - Gerar código de inicialização                                       │
│   - Gerar funções/middleware de acesso                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. GlobalStateExtractor (Stack-Agnostic)

```
Location: src/wxcode/parser/global_state_extractor.py
```

```python
class Scope(Enum):
    APP = "app"           # Project Code (type_code: 0)
    MODULE = "module"     # WDG (type_code: 31)
    REQUEST = "request"   # Page (type_code: 38, 60)

@dataclass
class GlobalVariable:
    """Variável global extraída - tipos WLanguage originais."""
    name: str                    # "gCnn"
    wlanguage_type: str          # "Connection" (NÃO AsyncEngine)
    default_value: str | None    # "20" (valor WLanguage)
    scope: Scope                 # APP | MODULE | REQUEST
    source_element: str          # "Linkpay_ADM.wwp"
    source_type_code: int        # 0, 31, 38, etc.

@dataclass
class InitializationBlock:
    """Bloco de código de inicialização - código WLanguage original."""
    code: str                    # Código WLanguage original
    dependencies: list[str]      # Variáveis globais usadas
    order: int                   # Ordem de execução

class GlobalStateExtractor:
    def extract_variables(self, code: str, type_code: int, source: str) -> list[GlobalVariable]: ...
    def extract_initialization(self, code: str) -> list[InitializationBlock]: ...
```

### 2. GlobalStateContext (IR Stack-Agnostic)

```
Location: src/wxcode/models/global_state_context.py
```

```python
@dataclass
class GlobalStateContext:
    """IR stack-agnostic para estado global."""
    variables: list[GlobalVariable]
    initialization_blocks: list[InitializationBlock]

    def get_by_scope(self, scope: Scope) -> list[GlobalVariable]: ...
    def get_by_source(self, source: str) -> list[GlobalVariable]: ...
    def get_variable(self, name: str) -> GlobalVariable | None: ...

    @classmethod
    def from_elements(cls, elements: list[Element]) -> "GlobalStateContext": ...
```

### 3. BaseTypeMapper (Interface)

```
Location: src/wxcode/generator/type_mapper.py
```

```python
@dataclass
class MappedType:
    """Tipo mapeado para um stack específico."""
    type_name: str              # "AsyncEngine", "Pool", "*sql.DB"
    import_statement: str | None # "from sqlalchemy.ext.asyncio import AsyncEngine"
    default_value: str | None   # Valor default no stack target

class BaseTypeMapper(ABC):
    @abstractmethod
    def map_type(self, wlanguage_type: str) -> MappedType:
        """Mapeia tipo WLanguage para tipo do stack."""
        ...

    @abstractmethod
    def map_default_value(self, wlanguage_value: str, wlanguage_type: str) -> str:
        """Converte valor default para sintaxe do stack."""
        ...
```

### 4. PythonTypeMapper

```
Location: src/wxcode/generator/python/type_mapper.py
```

```python
class PythonTypeMapper(BaseTypeMapper):
    MAPPINGS = {
        "Connection": MappedType("AsyncEngine", "from sqlalchemy.ext.asyncio import AsyncEngine"),
        "JSON": MappedType("dict[str, Any]", "from typing import Any"),
        "string": MappedType("str", None),
        "int": MappedType("int", None),
        "boolean": MappedType("bool", None),
        "DateTime": MappedType("datetime", "from datetime import datetime"),
        "Date": MappedType("date", "from datetime import date"),
        "array of *": MappedType("list[{inner}]", None),  # Template
        "emailSMTPSession": MappedType("SMTPClient", "from app.integrations.smtp import SMTPClient"),
    }

    def map_type(self, wlanguage_type: str) -> MappedType:
        if wlanguage_type in self.MAPPINGS:
            return self.MAPPINGS[wlanguage_type]
        if wlanguage_type.startswith("array of "):
            inner = wlanguage_type[9:]
            inner_mapped = self.map_type(inner)
            return MappedType(f"list[{inner_mapped.type_name}]", inner_mapped.import_statement)
        # Tipo não mapeado
        return MappedType("Any", "from typing import Any")
```

### 5. BaseStateGenerator (Interface)

```
Location: src/wxcode/generator/state_generator.py
```

```python
class BaseStateGenerator(ABC):
    def __init__(self, type_mapper: BaseTypeMapper):
        self.type_mapper = type_mapper

    @abstractmethod
    def generate(self, context: GlobalStateContext, output_dir: Path) -> list[Path]:
        """Gera todos os arquivos de estado."""
        ...

    @abstractmethod
    def get_state_access(self, var_name: str) -> str:
        """Retorna código para acessar uma variável de estado."""
        ...

    @abstractmethod
    def get_state_import(self) -> str:
        """Retorna import necessário para usar estado."""
        ...
```

### 6. PythonStateGenerator

```
Location: src/wxcode/generator/python/state_generator.py
```

```python
class PythonStateGenerator(BaseStateGenerator):
    def __init__(self):
        super().__init__(PythonTypeMapper())

    def generate(self, context: GlobalStateContext, output_dir: Path) -> list[Path]:
        files = []
        files.append(self._generate_state_class(context, output_dir))
        files.append(self._generate_lifespan(context, output_dir))
        files.append(self._generate_dependencies(context, output_dir))
        return files

    def get_state_access(self, var_name: str) -> str:
        # gCnn → app_state.db
        return f"app_state.{self._normalize_name(var_name)}"

    def get_state_import(self) -> str:
        return "from app.dependencies import get_app_state"
```

**Arquivos gerados:**
```
output/{config_name}/
├── app/
│   ├── state.py          # @dataclass AppState
│   ├── lifespan.py       # @asynccontextmanager lifespan
│   └── dependencies.py   # def get_app_state(request) -> AppState
```

## Extensibilidade

### Adicionando Novo Stack (exemplo: Node/Express)

1. **Criar TypeMapper:**
```python
# src/wxcode/generator/node/type_mapper.py
class NodeTypeMapper(BaseTypeMapper):
    MAPPINGS = {
        "Connection": MappedType("Pool", "const { Pool } = require('pg')"),
        "JSON": MappedType("object", None),
        ...
    }
```

2. **Criar StateGenerator:**
```python
# src/wxcode/generator/node/state_generator.py
class NodeStateGenerator(BaseStateGenerator):
    def __init__(self):
        super().__init__(NodeTypeMapper())

    def generate(self, context: GlobalStateContext, output_dir: Path) -> list[Path]:
        # Gera: state.js, middleware.js
        ...

    def get_state_access(self, var_name: str) -> str:
        return f"req.appState.{self._normalize_name(var_name)}"
```

3. **Registrar no Orchestrator:**
```python
STATE_GENERATORS = {
    "python": PythonStateGenerator,
    "node": NodeStateGenerator,
    "go": GoStateGenerator,
}
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         wxcode convert                                │
│  --stack python | --stack node | --stack go                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     GlobalStateExtractor                                 │
│  (Stack-Agnostic - mesmo código para qualquer stack)                    │
│                                                                         │
│  Entrada: Project Code + WDGs + Pages                                   │
│  Saída: GlobalStateContext (tipos WLanguage)                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      GlobalStateContext (IR)                             │
│  {                                                                       │
│    variables: [                                                          │
│      {name: "gCnn", wlanguage_type: "Connection", scope: APP},          │
│      {name: "gjsonParams", wlanguage_type: "JSON", scope: APP}          │
│    ],                                                                    │
│    initialization_blocks: [...]                                          │
│  }                                                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            PythonState     NodeState       GoState
            Generator       Generator       Generator
                    │               │               │
                    ▼               ▼               ▼
            app/state.py    state.js        state.go
            app/lifespan.py middleware.js   init.go
            app/deps.py
```

## Type Code Reference

| type_code | Contexto | Escopo | Tratamento |
|-----------|----------|--------|------------|
| 0 | Project Code | APP | Estado global da aplicação |
| 15 | Procedure | LOCAL | Ignorar (variáveis locais) |
| 31 | Set of Procedures | MODULE | Estado do módulo |
| 38 | Page events | REQUEST | Estado da requisição |
| 60 | Cell events | REQUEST | Estado da requisição |

## Edge Cases

1. **Tipo não mapeável**: TypeMapper retorna `Any`/`object`/`interface{}` com TODO
2. **Variável em múltiplos escopos**: Priorizar escopo mais amplo (app > module > request)
3. **Inicialização com COMPILE IF**: Integrar com ConfigurationContext
4. **Stack não suportado**: Erro claro com lista de stacks disponíveis
