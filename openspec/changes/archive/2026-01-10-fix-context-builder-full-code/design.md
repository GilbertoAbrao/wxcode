# Design: fix-context-builder-full-code

## Current Flow

```
┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  ContextBuilder  │────▶│  BaseLLMProvider │────▶│   Claude LLM    │
│                  │     │                  │     │                 │
│ - load element   │     │ - format control │     │ - generate code │
│ - load controls  │     │ - TRUNCATE code  │     │ - return JSON   │
│ - load local     │     │   to 100 chars   │     │                 │
│   procedures     │     │                  │     │                 │
└──────────────────┘     └─────────────────┘     └─────────────────┘
         │                        │
         │                        ▼
         │               ┌─────────────────┐
         │               │  LLM receives:  │
         │               │  - Event: xxx...│ ◀── Truncated!
         │               │  - No global    │ ◀── Missing!
         │               │    procedures   │
         │               └─────────────────┘
         ▼
   Only local procedures loaded
   Global procedures NOT loaded
```

## Proposed Flow

```
┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  ContextBuilder  │────▶│  BaseLLMProvider │────▶│   Claude LLM    │
│                  │     │                  │     │                 │
│ - load element   │     │ - format control │     │ - generate code │
│ - load controls  │     │ - FULL code in   │     │ - return JSON   │
│ - load local     │     │   code blocks    │     │                 │
│   procedures     │     │ - referenced     │     │                 │
│ - LOAD GLOBAL ◀──│     │   procedures     │     │                 │
│   PROCEDURES     │     │                  │     │                 │
└──────────────────┘     └─────────────────┘     └─────────────────┘
         │                        │
         │                        ▼
         │               ┌─────────────────┐
         │               │  LLM receives:  │
         │               │  - Event: full  │ ◀── Complete!
         │               │    WLanguage    │
         │               │  - Global procs │ ◀── Included!
         │               │    referenced   │
         │               └─────────────────┘
         ▼
   Extract procedure calls from events
   Load matching global procedures
```

## Token Budget Management

```
Total Budget: 150,000 tokens (configurable)

Priority 1 (Always include):
├── Page metadata: ~100 tokens
├── Control hierarchy: ~500-2000 tokens
└── Event code (complete): ~1000-10000 tokens

Priority 2 (Include if space):
├── Local procedures: ~500-5000 tokens
└── Referenced global procedures: ~1000-20000 tokens

Priority 3 (Truncate if needed):
└── Secondary dependencies: variable
```

## Procedure Extraction Pattern

```python
# WLanguage patterns to match:
ProcedureName()           # Simple call
ProcedureName(param)      # With params
Module.ProcedureName()    # Qualified name
CALL ProcedureName        # Legacy syntax

# Regex:
r'\b([A-Z][a-zA-Z0-9_]*)\s*\('
r'\bCALL\s+([A-Z][a-zA-Z0-9_]+)'

# Exclusions (WLanguage built-ins):
IF, WHILE, FOR, SWITCH, CASE, RESULT, RETURN,
END, THEN, ELSE, DO, LOOP, BREAK, CONTINUE
```

## Data Model Changes

```python
@dataclass
class ConversionContext:
    page_name: str
    element_id: str
    controls: list[dict]
    local_procedures: list[dict]
    referenced_procedures: list[dict]  # NEW
    dependencies: list[str]
    estimated_tokens: int
    theme: str | None = None
    theme_skills: str | None = None
```

## Output Format Changes

```markdown
# Converter Página: PAGE_Login

## Hierarquia de Controles

- BTN_Entrar [type=8]
  → OnClick [type=851984]:
    ```wlanguage
    Local_Login(EDT_LOGIN, EDT_Senha)
    IF gbOK THEN
      PageDisplay(PAGE_PRINCIPAL_MENU)
    ELSE
      Info(gsMessage)
    END
    ```

## Procedures Locais

### MyPage
```wlanguage
// código completo
```

## Procedures Globais Referenciadas    ◀── NEW SECTION

### Local_Login
```wlanguage
PROCEDURE Local_Login(login, senha)
  // Lógica completa de autenticação
  HExecuteQuery(QRY_LOGIN)
  ...
```
```

## Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| Include all code | Best conversion quality | Higher token cost |
| Truncate to N chars | Lower cost | Poor conversion quality |
| **Smart prioritization** | Balance cost/quality | More complex logic |

**Decision:** Smart prioritization with configurable token limit.
