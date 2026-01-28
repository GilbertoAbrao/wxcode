# Feature Landscape: Initialization Context for PromptBuilder

**Domain:** Starter project generation with initialization context
**Researched:** 2026-01-24
**Milestone:** Adding initialization context to PromptBuilder

## Context

When `/gsd:new-project` runs, it receives CONTEXT.md and generates a starter project. Currently:
- CONTEXT.md includes stack characteristics (language, framework, ORM, type mappings)
- CONTEXT.md includes database schema (tables with columns, indexes)
- **Missing:** Database connection configuration
- **Missing:** Global variables and state
- **Missing:** Initialization patterns (lifespan events, startup code)

The goal is that PAGE_LOGIN (first converted element) works immediately because the starter already has proper config.

---

## Table Stakes

Features users **expect**. Missing = starter project feels incomplete or broken.

| Feature | Why Expected | Complexity | User Benefit | Dependencies |
|---------|--------------|------------|--------------|--------------|
| **Database Connection Config** | Every converted page uses `gCnn` connection | Low | Generated code connects to database without manual setup | `ConfigurationContext` extraction |
| **Environment-Specific Settings** | WinDev has COMPILE IF for Homolog/Producao | Medium | Developer chooses environment, gets correct URLs/credentials | `CompileIfExtractor` |
| **Settings/Config File Generation** | Modern apps need .env, settings.py, config.yaml | Low | Standard config pattern for target stack | Stack model |
| **Database URL Pattern** | `DATABASE_URL` is standard for Python/Node | Low | ORM configuration works out of the box | Connection extraction |
| **Session Timeout Config** | `gnTempoSessao` controls session duration | Low | Authentication behavior matches original | Global state extraction |

### Feature Details

#### Database Connection Config
**What:** Extract connection parameters (server, user, password, database) from `gCnn` initialization.
**Why:** The original project reads from INI files via `Global_PegaInfoINI()`. The converted project needs these in environment variables or config files.
**Example from Linkpay_ADM:**
```wlanguage
gCnn..Server    = Global_PegaInfoINI(sCaminhoINI,"SERVER")
gCnn..User      = Global_PegaInfoINI(sCaminhoINI,"USER")
gCnn..Password  = Global_PegaInfoINI(sCaminhoINI,"PASSWORD")
gCnn..Database  = Global_PegaInfoINI(sCaminhoINI,"DATABASE")
```
**Target output (.env.example):**
```
DATABASE_HOST=localhost
DATABASE_USER=user
DATABASE_PASSWORD=changeme
DATABASE_NAME=linkpay
```

#### Environment-Specific Settings
**What:** Extract configuration blocks from `<COMPILE IF Configuration="X">` sections.
**Why:** Production vs Homolog have different API URLs, credentials, feature flags.
**Implementation:** `ConfigurationContext` already exists but is not connected to PromptBuilder.
**Target output:** Multiple .env files or environment-specific config sections.

#### Settings File Generation
**What:** Generate stack-appropriate config files (Python: `settings.py`, Node: `config.ts`, etc.)
**Why:** Each stack has conventions for configuration management.
**Implementation:** Stack model should include `config_template` field similar to `model_template`.

---

## Differentiators

Features that set the starter apart. Not expected, but make conversion smoother.

| Feature | Value Proposition | Complexity | User Benefit | Dependencies |
|---------|-------------------|------------|--------------|--------------|
| **API Endpoint Mapping** | Extract external API URLs from global state | Medium | External integrations already configured | Global state + COMPILE IF |
| **OAuth/Client Credentials** | Extract `ClientId`, `ClientSecret` patterns | Medium | Auth services pre-configured | COMPILE IF extractor |
| **Lifespan Event Generation** | Generate Python `@asynccontextmanager` or Node startup | Medium | Database pool, connections managed correctly | Stack model extension |
| **Multiple Connections Support** | Some projects have `gCnn`, `gCnn_Log`, etc. | Low | All database connections configured | Connection enumeration |
| **Initialization Order** | Respect dependency order (connect before query) | Medium | No startup crashes | `InitializationBlock` analysis |
| **Feature Flags** | Extract `sAmbiente` style environment indicators | Low | Toggle features per environment | Global state |

### Feature Details

#### API Endpoint Mapping
**What:** Extract API URLs like `gjParametrosAPINET.URL`, `gsUrlApiLinkPay` into config.
**Why:** Original project has dozens of external API integrations (Fitbank, APICartoes, etc.)
**Example from Linkpay_ADM:**
```wlanguage
gjParametrosAPINET.URL      = "https://api.linkpay.com.br/"
gjParametrosAPINET.URLToken = "https://api.linkpay.com.br/token"
gsUrlApiLinkPay             = "https://sandboxapiadm.linkpay.com.br/"
```
**Target output:**
```python
class ExternalAPIs(BaseSettings):
    api_net_url: str = "https://api.linkpay.com.br/"
    api_net_token_url: str = "https://api.linkpay.com.br/token"
    api_linkpay_url: str = "https://sandboxapiadm.linkpay.com.br/"
```

#### Lifespan Event Generation
**What:** Generate FastAPI lifespan context manager or equivalent for other stacks.
**Why:** Database connections must be opened at startup, closed at shutdown.
**Target output (FastAPI):**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize connections
    await database.connect()
    yield
    # Shutdown: cleanup
    await database.disconnect()
```

#### Multiple Connections Support
**What:** Detect and configure all connection variables (gCnn, gCnn_Log, etc.)
**Why:** Linkpay_ADM has separate connections for main DB and logging DB.
**Implementation:** Enumerate all `Connection` type global variables.

---

## Anti-Features

Features to explicitly **NOT** include in CONTEXT.md. Common mistakes.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Hardcoded Credentials** | Security risk, breaks in production | Use environment variables, .env.example with placeholders |
| **INI File Path Logic** | `fDataDir()` is WinDev-specific | Convert to standard config loading pattern |
| **Provider-Specific Constants** | `hNativeAccessSQLServer` is WinDev | Map to generic DB driver config |
| **Test Mode Detection** | `InTestMode()` is WinDev-specific | Use environment variable (NODE_ENV, APP_ENV) |
| **Raw Connection Objects** | `gCnn..Property` syntax is WinDev | Convert to ORM connection pool pattern |
| **Palette/UI Constants** | `garrPaletaCores` not needed for backend | Exclude from initialization context |
| **Session Objects** | `gSessaoSMTP is emailSMTPSession` | Convert to email service config, not object |
| **WinDev Structures** | `ListaRecebiveis is array of stRecebiceisSintetico` | Convert to Pydantic models, not global state |

### Why These Anti-Features Matter

**Hardcoded Credentials:**
The original code uses INI files which effectively hardcode paths. The converted project should use:
- Environment variables for secrets
- `.env.example` with placeholder values
- Never commit actual credentials

**Provider-Specific Constants:**
```wlanguage
// DON'T include in CONTEXT.md:
gCnn..Provider = hOledbSQLServer

// DO convert to:
DATABASE_DRIVER=postgresql+asyncpg
```

**Global State Objects:**
WinDev uses global objects like `gUsuarioLogado is STUsuarioLogado`. These should become:
- Request-scoped dependencies (FastAPI `Depends`)
- Session/JWT claims
- Not global mutable state

---

## Feature Dependencies

```
Stack Model (existing)
    |
    v
GlobalStateContext (existing but not connected)
    |
    +---> ConfigurationContext (existing but not connected)
    |         |
    |         v
    |     Environment Config Section in CONTEXT.md
    |
    +---> Database Connection Section in CONTEXT.md
    |
    v
PromptBuilder.build_context() <-- MODIFICATION POINT
    |
    v
CONTEXT.md with Initialization Section (NEW)
    |
    v
Claude Code generates starter with working config
```

### Integration Points

1. **GlobalStateExtractor** - Already extracts variables, needs to be called
2. **ConfigurationContext** - Already models config, needs PromptBuilder integration
3. **PromptBuilder.build_context()** - Needs new parameters for init context
4. **PROMPT_TEMPLATE** - Needs new sections for initialization

---

## MVP Recommendation

For MVP, prioritize features that make PAGE_LOGIN work immediately:

### Phase 1: Core Initialization (MVP)
1. **Database Connection Config** - Essential for any database operation
2. **Settings File Generation** - Provides structure for config
3. **Environment Variables Template** - .env.example with placeholders

### Phase 2: Environment Support
4. **Environment-Specific Settings** - COMPILE IF extraction for prod/homolog
5. **Multiple Connections** - gCnn + gCnn_Log

### Phase 3: External Services
6. **API Endpoint Mapping** - External API URLs
7. **OAuth Credentials Pattern** - ClientId/ClientSecret structure

### Defer to Post-MVP
- Lifespan event generation (can be manual for now)
- Initialization order analysis (complex, rarely critical)
- Feature flags (nice to have)

---

## Implementation Notes

### Changes to PromptBuilder

Current signature:
```python
def build_context(
    output_project: OutputProject,
    stack: Stack,
    tables: list[dict],
) -> str:
```

Proposed signature:
```python
def build_context(
    output_project: OutputProject,
    stack: Stack,
    tables: list[dict],
    global_state: GlobalStateContext | None = None,
    configuration: ConfigurationContext | None = None,
) -> str:
```

### New PROMPT_TEMPLATE Sections

```markdown
## Initialization Context

### Database Connections
{database_connections}

### Environment Variables
{env_variables}

### External API Endpoints
{api_endpoints}

### Startup Code Pattern
{startup_pattern}
```

### Stack Model Extension

Add to `Stack` model:
```python
# Configuration patterns
config_file_path: str = Field(
    default="",
    description="Path to config file: 'config/settings.py' or 'src/config.ts'"
)
config_template: str = Field(
    default="",
    description="Example config file structure"
)
env_template: str = Field(
    default="",
    description="Example .env file content"
)
lifespan_template: str = Field(
    default="",
    description="Startup/shutdown lifecycle code"
)
```

---

## Sources

- Existing codebase analysis:
  - `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/prompt_builder.py`
  - `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/configuration_context.py`
  - `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/global_state_context.py`
  - `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/global_state_extractor.py`
  - `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/compile_if_extractor.py`
- Reference project:
  - `/Users/gilberto/projetos/wxk/wxcode/project-refs/Linkpay_ADM/Linkpay_ADM.wwp` (lines 2450-2700 for initialization patterns)
- Confidence: HIGH (based on existing codebase, not external research)
