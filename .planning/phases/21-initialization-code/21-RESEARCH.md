# Phase 21: Initialization Code - Research

**Researched:** 2026-01-24
**Domain:** Initialization code extraction and FastAPI lifespan pattern documentation for CONTEXT.md
**Confidence:** HIGH

## Summary

Phase 21 extends the existing global state infrastructure (from Phase 20) to include initialization code blocks in CONTEXT.md. The key insight is that **most of the extraction infrastructure already exists** - the work is primarily about:

1. **Formatting initialization blocks** for CONTEXT.md (the extraction via `extract_initialization()` already works)
2. **Determining dependency order** between init blocks (currently not implemented)
3. **Adding FastAPI lifespan pattern documentation** to help Claude understand how to convert WLanguage init code

The real Project Code example (Linkpay_ADM.wwp lines 2446-2790) reveals a complex initialization structure:
- CONSTANT declarations
- GLOBAL variable declarations
- COMPILE IF blocks for environment-specific configuration (Homolog, Producao, ProducaoControlada)
- Connection setup (HOpenConnection, HChangeConnection)
- External API configuration (Fitbank, Keycloak, Elasticsearch)

**Primary recommendation:** Add `format_initialization_blocks()` method to PromptBuilder that renders init code as WLanguage snippets, implement basic dependency ordering based on variable references, and add a static FastAPI lifespan documentation section.

## Current State Analysis

### What Already Works (HIGH confidence)

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| GlobalStateExtractor.extract_initialization() | `parser/global_state_extractor.py` | Exists | Extracts code after GLOBAL block as single InitializationBlock |
| InitializationBlock dataclass | `parser/global_state_extractor.py` | Complete | code, dependencies, order fields |
| GlobalStateContext.initialization_blocks | `models/global_state_context.py` | Complete | Stores list of InitializationBlock |
| extract_global_state_for_project() | `services/schema_extractor.py` | Complete | Already calls extract_initialization() for type=0 elements |
| PromptBuilder with global_state | `services/prompt_builder.py` | Complete | format_global_state() exists, template includes global state section |
| API wiring | `api/output_projects.py` | Complete | Passes global_state to PromptBuilder |

### What's Missing

| Gap | Description | Requirement |
|-----|-------------|-------------|
| format_initialization_blocks() | No method to format init code as markdown | INIT-03 |
| Dependency ordering | extract_initialization() returns all code as single block with order=0 | INIT-02 |
| Template section | PROMPT_TEMPLATE lacks initialization code section | INIT-03 |
| Lifespan documentation | No FastAPI lifespan pattern docs in template | INIT-04 |

### Current extract_initialization() Limitations

The current implementation (lines 235-292 of global_state_extractor.py) has limitations:

```python
# Current behavior:
# 1. Finds end of GLOBAL block
# 2. Takes ALL code after GLOBAL as single init_code string
# 3. Extracts variable references (g[A-Z]\w*) as dependencies
# 4. Returns single InitializationBlock with order=0
```

**Limitation 1:** Returns single block instead of multiple blocks
**Limitation 2:** Order is always 0 (no sequencing)
**Limitation 3:** Dependencies are just variable names, not inter-block dependencies

For Phase 21, this is **acceptable** because:
- Claude only needs to SEE the init code, not execute it
- The raw WLanguage shows the sequence implicitly
- Overly complex parsing adds little value for LLM consumption

## Architecture Patterns

### Initialization Code Structure in Real Projects

From Linkpay_ADM.wwp (lines 2446-2790):

```
CONSTANT declarations
    |
    v
GLOBAL variable declarations
    |
    v
<COMPILE IF Configuration="Homolog">
    Environment-specific setup (INI paths, connection params)
<END>
    |
    v
<COMPILE IF Configuration="Producao">
    Production setup
<END>
    |
    v
Connection opening (HOpenConnection)
    |
    v
Table mapping (HChangeConnection)
    |
    v
Global parameter initialization
    |
    v
API-specific configuration (Fitbank, Keycloak, etc.)
```

### Dependency Order Categories

Based on real code analysis, initialization blocks have natural ordering:

| Order | Category | Dependencies | Example |
|-------|----------|--------------|---------|
| 0 | Constants | None | CONSTANT NOME_PROJETO = "Linkpay_ADM" |
| 1 | Variable declarations | Constants | gCnn is Connection |
| 2 | Environment config | Variables | sCaminhoINI = fDataDir() + ... |
| 3 | Connection setup | Environment, Variables | gCnn..Server = Global_PegaInfoINI(...) |
| 4 | Connection open | Connections | HOpenConnection(gCnn) |
| 5 | Table mapping | Open connections | HChangeConnection("*", gCnn) |
| 6 | API configuration | Variables, possibly connections | gjParametroFIT.Authorization = ... |

### Recommended Implementation Approach

**Option A: Simple (Recommended)**
- Keep single init block from extract_initialization()
- Present as single WLanguage code block in CONTEXT.md
- Let Claude interpret ordering from code structure
- Pros: Simple, reliable, code is self-documenting

**Option B: Complex (Not Recommended)**
- Parse init code into multiple blocks
- Determine dependencies between blocks
- Order blocks topologically
- Cons: Complex parsing, fragile, little benefit for LLM

**Recommendation: Option A** - The raw WLanguage code already shows ordering clearly. Over-engineering the parser adds complexity without proportional value.

### PromptBuilder Extension Pattern

Following Phase 20's pattern for format_global_state():

```python
@staticmethod
def format_initialization_blocks(global_state: GlobalStateContext) -> str:
    """Format initialization code as WLanguage snippet."""
    if not global_state or not global_state.initialization_blocks:
        return "*No initialization code found.*"

    lines = []
    for i, block in enumerate(global_state.initialization_blocks):
        if i > 0:
            lines.append("")  # Separator between blocks

        # Header with dependency info
        deps = ", ".join(block.dependencies[:5]) if block.dependencies else "none"
        if len(block.dependencies) > 5:
            deps += f" (+{len(block.dependencies) - 5} more)"
        lines.append(f"### Initialization Block {i + 1}")
        lines.append(f"**Global variables used:** {deps}")
        lines.append("")
        lines.append("```wlanguage")
        lines.append(block.code)
        lines.append("```")

    return "\n".join(lines)
```

## Standard Stack

This phase uses only existing project infrastructure:

| Component | Version | Purpose | Already in Project |
|-----------|---------|---------|-------------------|
| GlobalStateExtractor | - | Extract init blocks | Yes |
| GlobalStateContext | - | IR for global state | Yes |
| InitializationBlock | - | Dataclass for init code | Yes |
| PromptBuilder | - | Template generation | Yes |

No new dependencies required.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Init code extraction | New extractor | GlobalStateExtractor.extract_initialization() | Already works, returns InitializationBlock |
| Complex block parsing | Multi-block parser | Single block with raw code | Claude can interpret WLanguage structure |
| Topological sorting | Custom graph algorithm | Present code in original order | Code is already ordered correctly in source |

**Key insight:** The initialization code is already in correct order in the source file. Complex dependency analysis is unnecessary - just present the code to Claude.

## Common Pitfalls

### Pitfall 1: Over-Engineering the Parser
**What goes wrong:** Trying to parse COMPILE IF blocks, split into semantic units
**Why it happens:** Engineering instinct to structure data
**How to avoid:** Remember Claude is the consumer - it can read WLanguage
**Warning signs:** Parser complexity > formatting complexity

### Pitfall 2: Ignoring COMPILE IF Blocks
**What goes wrong:** Init code contains environment-specific branches that confuse
**Why it happens:** Not documenting the conditional structure
**How to avoid:** Add note explaining COMPILE IF is WinDev's conditional compilation
**Warning signs:** Generated code hardcodes Homolog settings

### Pitfall 3: Token Budget Explosion
**What goes wrong:** Full init code (300+ lines) bloats CONTEXT.md
**Why it happens:** Real projects have extensive initialization
**How to avoid:** Consider truncating with "... (N more lines)" or focusing on HOpenConnection section
**Warning signs:** Initialization section > 200 lines

### Pitfall 4: Missing Lifespan Documentation
**What goes wrong:** Claude doesn't know how to convert init code to FastAPI
**Why it happens:** WLanguage init patterns don't map obviously to Python
**How to avoid:** Include explicit lifespan pattern documentation
**Warning signs:** Generated code uses deprecated @app.on_event()

## Code Examples

### InitializationBlock Dataclass (existing)
```python
# Source: src/wxcode/parser/global_state_extractor.py lines 50-65
@dataclass
class InitializationBlock:
    code: str                    # Full WLanguage init code
    dependencies: list[str]      # Variable names referenced (g[A-Z]\w*)
    order: int                   # Execution order (currently always 0)
```

### Current extract_initialization() Pattern
```python
# Source: src/wxcode/parser/global_state_extractor.py lines 235-292
def extract_initialization(self, code: str) -> list[InitializationBlock]:
    # Finds end of GLOBAL block
    global_match = self.GLOBAL_BLOCK_PATTERN.search(code)
    if not global_match:
        return []

    # Extracts all code after GLOBAL
    init_code = code[global_match.end():].strip()

    # Finds variable references (gXxx pattern)
    var_pattern = re.compile(r"\b(g[A-Z]\w*)\b")
    dependencies = list(set(var_pattern.findall(init_code)))

    return [InitializationBlock(code=init_code, dependencies=dependencies, order=0)]
```

### FastAPI Lifespan Pattern (from official docs)
```python
# Source: https://fastapi.tiangolo.com/advanced/events/
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: runs before accepting requests
    # Load resources, open connections, etc.
    yield
    # Shutdown: runs after handling requests
    # Close connections, release resources

app = FastAPI(lifespan=lifespan)
```

### Recommended format_initialization_blocks() Implementation
```python
@staticmethod
def format_initialization_blocks(global_state: GlobalStateContext) -> str:
    """
    Formata blocos de inicializacao como snippets WLanguage.

    Args:
        global_state: Contexto com initialization_blocks extraidos

    Returns:
        String markdown formatada com codigo WLanguage
    """
    if not global_state or not global_state.initialization_blocks:
        return "*No initialization code found.*"

    lines = []
    for i, block in enumerate(global_state.initialization_blocks):
        if i > 0:
            lines.append("")

        # Dependency summary
        deps = block.dependencies[:5] if block.dependencies else []
        deps_str = ", ".join(f"`{d}`" for d in deps) if deps else "*none*"
        if len(block.dependencies) > 5:
            deps_str += f" (+{len(block.dependencies) - 5} more)"

        lines.append(f"### Initialization Block {i + 1}")
        lines.append(f"**References:** {deps_str}")
        lines.append("")

        # Truncate if too long (> 100 lines)
        code_lines = block.code.split("\n")
        if len(code_lines) > 100:
            truncated = "\n".join(code_lines[:100])
            lines.append("```wlanguage")
            lines.append(truncated)
            lines.append(f"// ... ({len(code_lines) - 100} more lines)")
            lines.append("```")
        else:
            lines.append("```wlanguage")
            lines.append(block.code)
            lines.append("```")

    return "\n".join(lines)
```

### Recommended Lifespan Pattern Documentation
```python
@staticmethod
def format_lifespan_pattern() -> str:
    """
    Gera documentacao do pattern FastAPI lifespan para CONTEXT.md.
    """
    return '''### FastAPI Lifespan Pattern

The WLanguage initialization code above should be converted to FastAPI's lifespan context manager:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Convert WLanguage init code here
    # - Database connections -> async engine creation
    # - Global config -> Settings class / environment variables
    # - HOpenConnection -> engine.connect() or connection pool
    # - HChangeConnection -> schema/table routing configuration

    yield  # Application runs here

    # SHUTDOWN: Release resources
    # - Close database connections
    # - Cleanup any global state

app = FastAPI(lifespan=lifespan)
```

**Key Conversion Patterns:**

| WLanguage | FastAPI/Python |
|-----------|----------------|
| `gCnn is Connection` | `app.state.db_engine` or `Depends()` |
| `HOpenConnection(gCnn)` | `create_async_engine(DATABASE_URL)` |
| `HChangeConnection("*", gCnn)` | Default database routing in ORM |
| `<COMPILE IF Configuration="X">` | Environment variables / `.env` files |
| `Global_PegaInfoINI(path, key)` | `os.getenv()` or `pydantic_settings.BaseSettings` |

**Important:**
- Use `@asynccontextmanager` (not deprecated `@app.on_event`)
- Store shared resources in `app.state` or use dependency injection
- Keep startup/shutdown quick - use background tasks for heavy operations'''
```

## Template Section to Add

Add after "Global State" section in PROMPT_TEMPLATE:

```python
## Initialization Code

{initialization_code}

{lifespan_pattern}
```

Update PROMPT_TEMPLATE.format() call to include:
```python
initialization_code=cls.format_initialization_blocks(global_state),
lifespan_pattern=cls.format_lifespan_pattern() if global_state and global_state.initialization_blocks else "",
```

## Implementation Plan Summary

### Task 1: Add format_initialization_blocks() to PromptBuilder
**File:** `src/wxcode/services/prompt_builder.py`

1. Add `format_initialization_blocks()` static method
2. Add `format_lifespan_pattern()` static method
3. Update PROMPT_TEMPLATE with Initialization Code section
4. Update build_context() to call new formatters

### Task 2: Update PROMPT_TEMPLATE
**File:** `src/wxcode/services/prompt_builder.py`

1. Add `## Initialization Code` section after Global State
2. Add placeholders for `{initialization_code}` and `{lifespan_pattern}`
3. Update format() call in build_context()

## Open Questions

### 1. Init Code Truncation Strategy
**What we know:** Real init code can be 300+ lines
**What's unclear:** Optimal truncation point
**Recommendation:** Truncate at 100 lines with indicator, or focus on HOpenConnection section only

### 2. COMPILE IF Block Handling
**What we know:** Code contains environment-specific branches
**What's unclear:** Whether to include all branches or just one
**Recommendation:** Include all branches with explanatory note - Claude needs to understand the pattern

### 3. Dependency Order Enhancement
**What we know:** Current implementation returns order=0 for all blocks
**What's unclear:** Whether enhanced ordering adds value
**Recommendation:** Defer to future phase - current approach sufficient for MVP

## Sources

### Primary (HIGH confidence)
- `src/wxcode/parser/global_state_extractor.py` - extract_initialization() implementation
- `src/wxcode/models/global_state_context.py` - InitializationBlock storage
- `src/wxcode/services/prompt_builder.py` - format_global_state() pattern
- `src/wxcode/services/schema_extractor.py` - extract_global_state_for_project()
- `project-refs/Linkpay_ADM/Linkpay_ADM.wwp` lines 2446-2790 - Real init code example
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) - Official documentation

### Secondary (MEDIUM confidence)
- Phase 20 research and implementation - Pattern for extending PromptBuilder

## Metadata

**Confidence breakdown:**
- Current state analysis: HIGH - direct code inspection
- Implementation approach: HIGH - follows established Phase 20 patterns
- FastAPI lifespan: HIGH - verified with official documentation
- Truncation strategy: MEDIUM - trade-off decision, may need adjustment

**Research date:** 2026-01-24
**Valid until:** 60 days (stable internal API, no external dependencies)
