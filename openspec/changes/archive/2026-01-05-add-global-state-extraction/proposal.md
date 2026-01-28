# Proposal: add-global-state-extraction

## Problem Statement

Projetos WinDev/WebDev declaram variáveis globais em múltiplos lugares:

### 1. Project Code (arquivo .wwp)
```wlanguage
GLOBAL
    gCnn, gCnn_Log                are Connection
    gjsonParametros               is JSON
    gsUrlAPI                      is string
    gnTempoSessao                 is int = 20

// Código de inicialização
IF HOpenConnection(gCnn) = False THEN
    EndProgram("NÃO FOI POSSÍVEL CONECTAR NO BANCO")
ELSE
    HChangeConnection("*", gCnn)
END
```

### 2. Set of Procedures (.wdg)
```wlanguage
// ServerProcedures.wdg - declarações no início do arquivo
GLOBAL
    gApiConfig                    is JSON
    gCacheTimeout                 is int = 300
```

### 3. Pages (.wwh) - variáveis locais da página
```wlanguage
// Declarações locais da página
LOCAL
    PageData                      is string
    CurrentUser                   is JSON
```

**Problemas atuais:**
1. Declarações GLOBAL são ignoradas na conversão → variáveis undefined
2. Código de inicialização (HOpenConnection, etc.) não é convertido
3. Não há mapeamento para padrões modernos (DI, settings, state)
4. Variáveis globais = anti-pattern em stacks modernas → precisa converter para patterns apropriados

## Proposed Solution

### 1. Arquitetura Multi-Target-Stack (3 camadas)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CAMADA 1: EXTRAÇÃO                               │
│                     (Stack-Agnostic)                                    │
│                                                                         │
│   WLanguage Code → GlobalStateExtractor → GlobalStateContext (IR)       │
│                                                                         │
│   IR contém tipos WLanguage originais, sem mapeamento para stack        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CAMADA 2: MAPEAMENTO                             │
│                     (Por Stack Target)                                  │
│                                                                         │
│   TypeMapper: WLanguage types → Target stack types                      │
│   PatternMapper: GLOBAL → Pattern apropriado do stack                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CAMADA 3: GERAÇÃO                                │
│                     (Implementação por Stack)                           │
│                                                                         │
│   PythonStateGenerator  │  NodeStateGenerator  │  GoStateGenerator      │
│   (FastAPI + DI)        │  (Express + Context) │  (Fiber + Context)     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. IR Stack-Agnostic

O `GlobalStateContext` contém apenas informações WLanguage:

```python
@dataclass
class GlobalVariable:
    name: str                    # "gCnn"
    wlanguage_type: str          # "Connection" (tipo original)
    default_value: str | None    # valor default WLanguage
    scope: Scope                 # APP | MODULE | REQUEST
    source_element: str          # "Linkpay_ADM.wwp"

@dataclass
class GlobalStateContext:
    variables: list[GlobalVariable]
    initialization_blocks: list[InitializationBlock]
    # SEM tipos Python, Node, Go - isso fica no Generator
```

### 3. Padrões por Stack Target

| Stack | Pattern para Estado Global | Inicialização |
|-------|---------------------------|---------------|
| **Python/FastAPI** | `app.state` + Dependency Injection | lifespan context manager |
| **Node/Express** | `app.locals` + middleware | app.use() middleware |
| **Go/Fiber** | Context + dependency container | init() functions |
| **Java/Spring** | `@Component` + `@Autowired` | `@PostConstruct` |

### 4. Exemplo de Conversão Multi-Stack

**Entrada (WLanguage):**
```wlanguage
GLOBAL
    gCnn is Connection
    gjsonParametros is JSON
```

**Saída Python/FastAPI:**
```python
@dataclass
class AppState:
    db: AsyncEngine
    params: dict[str, Any]

def get_app_state(request: Request) -> AppState:
    return request.app.state.app_state
```

**Saída Node/Express:**
```javascript
// state.js
class AppState {
    constructor(db, params) {
        this.db = db;
        this.params = params;
    }
}

// middleware
app.use((req, res, next) => {
    req.appState = app.locals.appState;
    next();
});
```

**Saída Go/Fiber:**
```go
type AppState struct {
    DB     *sql.DB
    Params map[string]interface{}
}

func GetAppState(c *fiber.Ctx) *AppState {
    return c.Locals("appState").(*AppState)
}
```

### Benefícios

- **IR reutilizável**: Mesma extração para qualquer stack target
- **Extensível**: Novo stack = novo Generator, sem mudar extração
- **Type-safe por stack**: Cada stack tem seu próprio type mapping
- **Patterns nativos**: Cada stack usa seus patterns idiomáticos
- **Testável**: IR pode ser testado independente de stack

## Scope

### IN SCOPE
- Parser para declarações GLOBAL em Project Code, WDG, Pages
- Model `GlobalStateContext` (IR stack-agnostic)
- Interface `BaseStateGenerator` para extensibilidade
- Interface `BaseTypeMapper` para mapeamento de tipos
- `PythonStateGenerator` + `PythonTypeMapper` (implementação inicial)
- Geração de estado, lifespan, e DI para Python/FastAPI
- Conversão de referências: `gCnn` → pattern do stack
- Integração com `WLanguageConverter`

### OUT OF SCOPE
- `NodeStateGenerator`, `GoStateGenerator` (changes futuras)
- Conversão de HyperFile para ORM específico (spec separada)
- Geração de migrations (spec separada)

## Dependencies

- `add-compile-if-extraction`: ConfigurationContext para variáveis condicionais
- Specs existentes: `service-generator`, `route-generator`

## Acceptance Criteria

1. Declarações GLOBAL são detectadas em todos os elementos
2. `GlobalStateContext` é 100% stack-agnostic (tipos WLanguage)
3. `BaseTypeMapper` permite mapeamento customizado por stack
4. `BaseStateGenerator` permite implementação por stack
5. `PythonStateGenerator` gera código FastAPI idiomático
6. Código convertido usa patterns nativos do stack target
7. Novo stack pode ser adicionado sem modificar extração
