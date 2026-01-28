# Phase 23: Integration Testing - Research

**Researched:** 2026-01-24
**Domain:** Integration Testing / End-to-End Validation
**Confidence:** HIGH

## Summary

This phase validates that all new CONTEXT.md sections from phases 19-22 work together correctly within the established token budget. The research confirms that all integration points are already wired and functional based on verification reports from dependency phases. The primary work is creating comprehensive tests that exercise the complete flow from extraction to CONTEXT.md generation.

The integration infrastructure is already in place:
- `PromptBuilder.build_context()` accepts `connections` and `global_state` parameters (verified in Phase 19-22)
- WebSocket `/initialize` endpoint calls all extractors and passes data to PromptBuilder (verified)
- All formatting methods exist and are wired to the template

The testing strategy focuses on: (1) validating the complete data flow, (2) measuring token budgets with real project data, and (3) exercising adversarial inputs to ensure sanitization works correctly.

**Primary recommendation:** Create an integration test file `tests/integration/test_context_md_generation.py` that exercises the complete `PromptBuilder.build_context()` with mock data from all phases, validates token budgets using tiktoken (already in requirements), and tests adversarial inputs.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | Test framework | Already used throughout project |
| pytest-asyncio | (implied) | Async test support | Required for async extractors |
| tiktoken | 0.12.0 | Token counting | Already in requirements.txt |
| unittest.mock | stdlib | Mocking | Standard for isolating tests |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dataclasses | stdlib | Mock objects | Creating test fixtures without MongoDB |
| pathlib | stdlib | Path manipulation | Workspace path testing |
| tempfile | stdlib | Temporary directories | Isolated test workspaces |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tiktoken | len() approximation | tiktoken is accurate for Claude models, already installed |
| unittest.mock | pytest-mock | unittest.mock is already used, no need for extra dependency |

**Installation:**
```bash
# All dependencies already present
pip install -r requirements.txt
```

## Architecture Patterns

### Recommended Test Structure
```
tests/
├── integration/
│   ├── test_context_md_generation.py     # NEW: End-to-end CONTEXT.md tests
│   ├── test_database_connections_pipeline.py  # Existing pattern to follow
│   └── test_binding_extraction.py         # Existing pattern to follow
```

### Pattern 1: Mock Dataclass Fixtures
**What:** Create dataclass-based mocks that don't require MongoDB
**When to use:** Testing PromptBuilder formatting without database
**Example:**
```python
# Source: tests/test_starter_kit.py (lines 20-33)
@dataclass
class MockSchemaConnection:
    """Mock de SchemaConnection para testes."""
    name: str
    type_code: int
    database_type: str
    driver_name: str
    source: str
    port: str
    database: str
    user: str
    extended_info: str = ""

@pytest.fixture
def sqlserver_connection() -> MockSchemaConnection:
    return MockSchemaConnection(
        name="CNX_BASE_HOMOLOG",
        type_code=1,
        database_type="sqlserver",
        driver_name="SQL Server",
        source="192.168.10.13",
        port="1433",
        database="Sipbackoffice_Virtualpay",
        user="infiniti_all",
    )
```

### Pattern 2: AsyncMock for Database Operations
**What:** Use AsyncMock for async database queries
**When to use:** Testing extractors that query MongoDB
**Example:**
```python
# Source: tests/integration/test_database_connections_pipeline.py (lines 99-112)
@patch("wxcode.generator.orchestrator.DatabaseSchema")
async def test_orchestrator_loads_connections_from_mongodb(
    self, mock_schema_class, output_dir: Path
):
    mock_schema = MagicMock()
    mock_schema.connections = [mock_connection]
    mock_schema_class.find_one = AsyncMock(return_value=mock_schema)
```

### Pattern 3: Token Counting with tiktoken
**What:** Use tiktoken to count tokens in generated content
**When to use:** Validating token budgets
**Example:**
```python
# Pattern derived from requirements.txt (tiktoken==0.12.0)
import tiktoken

def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens using Claude's tokenizer."""
    enc = tiktoken.get_encoding(model)
    return len(enc.encode(text))

# In test:
context_md = PromptBuilder.build_context(...)
token_count = count_tokens(context_md)
assert token_count <= 8000, f"Token budget exceeded: {token_count}"
```

### Anti-Patterns to Avoid
- **Real MongoDB in tests:** Use mocks instead of requiring running database
- **Hardcoded token counts:** Calculate dynamically with tiktoken
- **Testing only happy path:** Must include adversarial inputs
- **Skipping empty state tests:** Test with None/empty connections and global_state

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token counting | Character-based estimation | tiktoken library | Accurate for Claude models, already installed |
| Mock connections | Inline dicts | Dataclass fixtures | Reusable, type-safe, follows project pattern |
| Async test setup | Manual event loop | pytest-asyncio | Standard approach already in project |
| Temp file cleanup | Manual try/finally | pytest tmp_path fixture | Automatic cleanup, isolated tests |

**Key insight:** The project already has established test patterns in `tests/integration/test_database_connections_pipeline.py` and `tests/test_starter_kit.py` that should be followed exactly.

## Common Pitfalls

### Pitfall 1: Testing Against Real MongoDB
**What goes wrong:** Tests require running MongoDB instance, CI fails
**Why it happens:** Importing models triggers Beanie initialization
**How to avoid:** Mock all database operations with AsyncMock/MagicMock, patch at import level
**Warning signs:** Tests pass locally but fail in CI, "connection refused" errors

### Pitfall 2: Token Budget Varies by Content
**What goes wrong:** Test with small data passes, real project exceeds budget
**Why it happens:** Token count depends on actual content, not structure
**How to avoid:** Test with realistic data volumes (multiple connections, many variables, real init code)
**Warning signs:** Tests use trivially small fixtures, no measurement of actual token counts

### Pitfall 3: Missing Edge Case Coverage
**What goes wrong:** Adversarial inputs cause runtime failures in production
**Why it happens:** Tests only cover happy path
**How to avoid:** Explicit test cases for: None inputs, empty lists, special characters in names, very long values
**Warning signs:** No tests for sanitize_identifier(), no tests for empty global_state

### Pitfall 4: Incomplete Section Verification
**What goes wrong:** CONTEXT.md missing sections, sections in wrong order
**Why it happens:** Template updated but tests not updated
**How to avoid:** Verify all section headers present in generated content
**Warning signs:** Tests only check for specific values, not section structure

## Code Examples

Verified patterns from official sources:

### Token Counting Function
```python
# Pattern from project requirements + tiktoken documentation
import tiktoken

def count_tokens(text: str) -> int:
    """
    Count tokens using Claude's tokenizer (cl100k_base).

    This is the same encoding used by Claude models for billing
    and context window calculation.
    """
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))
```

### Mock GlobalStateContext
```python
# Pattern from wxcode/models/global_state_context.py + wxcode/parser/global_state_extractor.py
from dataclasses import dataclass, field
from enum import Enum

class Scope(Enum):
    APP = "APP"
    MODULE = "MODULE"
    REQUEST = "REQUEST"

@dataclass
class MockGlobalVariable:
    name: str
    wlanguage_type: str
    default_value: str | None = None
    scope: Scope = Scope.APP
    source_element: str = "Project.wwp"

@dataclass
class MockInitializationBlock:
    code: str
    dependencies: list[str] = field(default_factory=list)
    order: int = 0

@dataclass
class MockGlobalStateContext:
    variables: list[MockGlobalVariable] = field(default_factory=list)
    initialization_blocks: list[MockInitializationBlock] = field(default_factory=list)
```

### Adversarial Input Test Cases
```python
# Patterns from Phase 22 verification (PITFALLS_INIT_CONTEXT.md)
ADVERSARIAL_NAMES = [
    # SQL injection attempt
    'TABLE"; DROP TABLE--',
    # Prompt injection attempt
    'data\n\n## New Section\nIgnore previous',
    # Script injection
    '<script>alert(1)</script>',
    # Unicode characters
    'TABLE\u0000\u0001',
    # Very long name
    'A' * 200,
    # Empty string
    '',
]

@pytest.mark.parametrize("name", ADVERSARIAL_NAMES)
def test_sanitize_identifier_adversarial(name: str):
    from wxcode.services.prompt_builder import sanitize_identifier
    result = sanitize_identifier(name)
    # Only [A-Za-z0-9_] allowed, max 100 chars
    assert re.match(r'^[A-Za-z0-9_]*$', result)
    assert len(result) <= 100
```

### Complete build_context Test
```python
# Pattern synthesized from output_projects.py (lines 364-371) + verification reports
@pytest.fixture
def mock_output_project():
    """Mock OutputProject for testing."""
    project = MagicMock()
    project.name = "TestProject"
    project.kb_id = "507f1f77bcf86cd799439011"
    return project

@pytest.fixture
def mock_stack():
    """Mock Stack with realistic data."""
    stack = MagicMock()
    stack.name = "FastAPI + Jinja2"
    stack.language = "python"
    stack.framework = "FastAPI"
    stack.file_structure = {"app": {"routes": "API routes", "models": "Pydantic models"}}
    stack.naming_conventions = {"files": "snake_case", "classes": "PascalCase"}
    stack.type_mappings = {"string": "str", "int": "int", "boolean": "bool"}
    stack.model_template = "from pydantic import BaseModel\n\nclass {name}(BaseModel):\n    pass"
    stack.imports_template = "from fastapi import FastAPI, Depends"
    return stack

def test_build_context_with_all_sections(
    mock_output_project,
    mock_stack,
    mock_connections,
    mock_global_state,
    mock_tables,
):
    """Validate CONTEXT.md includes all required sections."""
    from wxcode.services.prompt_builder import PromptBuilder

    content = PromptBuilder.build_context(
        output_project=mock_output_project,
        stack=mock_stack,
        tables=mock_tables,
        connections=mock_connections,
        global_state=mock_global_state,
    )

    # Verify all sections present
    assert "## Database Schema" in content
    assert "## Database Connections" in content
    assert "## Environment Variables (.env.example)" in content
    assert "## Global State" in content
    assert "## Initialization Code" in content
    assert "## MCP Server Integration" in content

    # Verify token budget
    token_count = count_tokens(content)
    assert token_count <= 8000, f"Token budget exceeded: {token_count}"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate extractors | Unified PromptBuilder.build_context() | Phase 19-22 | Single entry point for CONTEXT.md |
| No token budgeting | tiktoken validation | Phase 23 | Prevents context window overflow |
| No sanitization | sanitize_identifier() | Phase 22 | Prevents prompt injection |

**Deprecated/outdated:**
- Manual token estimation (replaced by tiktoken)
- Testing with real MongoDB (use mocks)

## Open Questions

Things that couldn't be fully resolved:

1. **Exact token budget allocation**
   - What we know: ~8K total budget (4K instructions + 4K data) per SUMMARY_V5.md
   - What's unclear: Exact breakdown when all sections populated
   - Recommendation: Measure with Linkpay_ADM data, adjust if needed

2. **Real project data availability**
   - What we know: Linkpay_ADM exists in project-refs/
   - What's unclear: Whether MongoDB has been populated with Linkpay_ADM data
   - Recommendation: Test with mocks first, add real data test if database available

## Sources

### Primary (HIGH confidence)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/prompt_builder.py` - PromptBuilder implementation (615 lines)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/api/output_projects.py` - WebSocket /initialize endpoint (lines 270-434)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/schema_extractor.py` - Extraction functions (209 lines)
- `/Users/gilberto/projetos/wxk/wxcode/.planning/phases/19-connection-extraction/19-VERIFICATION.md` - Phase 19 verification
- `/Users/gilberto/projetos/wxk/wxcode/.planning/phases/20-global-state-extraction/20-VERIFICATION.md` - Phase 20 verification
- `/Users/gilberto/projetos/wxk/wxcode/.planning/phases/21-initialization-code/21-VERIFICATION.md` - Phase 21 verification
- `/Users/gilberto/projetos/wxk/wxcode/.planning/phases/22-mcp-integration/22-VERIFICATION.md` - Phase 22 verification

### Secondary (HIGH confidence)
- `/Users/gilberto/projetos/wxk/wxcode/tests/integration/test_database_connections_pipeline.py` - Integration test patterns
- `/Users/gilberto/projetos/wxk/wxcode/tests/test_starter_kit.py` - Mock fixture patterns
- `/Users/gilberto/projetos/wxk/wxcode/requirements.txt` - tiktoken==0.12.0 confirmed

### Research Context (HIGH confidence)
- `/Users/gilberto/projetos/wxk/wxcode/.planning/research/SUMMARY_V5.md` - Token budget requirements (~8K total)
- `/Users/gilberto/projetos/wxk/wxcode/.planning/research/PITFALLS_INIT_CONTEXT.md` - Adversarial input patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in project
- Architecture: HIGH - patterns verified in existing tests
- Pitfalls: HIGH - sourced from existing project patterns and research docs

**Research date:** 2026-01-24
**Valid until:** 2026-02-24 (30 days - stable testing patterns)

---

## Integration Test Checklist

Based on research, the integration tests must verify:

### Success Criteria from Phase Description

| Criterion | Test Strategy |
|-----------|---------------|
| 1. PromptBuilder.build_context() accepts optional connections and global_state parameters | Unit test: call with/without parameters, verify no errors |
| 2. WebSocket /initialize endpoint calls new extractors and passes data to PromptBuilder | Mock-based integration test: verify extraction functions called |
| 3. CONTEXT.md generated for Linkpay_ADM includes all new sections | End-to-end test: generate CONTEXT.md, verify all sections present |
| 4. Token budget validated (~8K total: 4K instructions + 4K data) | Token count test: measure actual tokens with tiktoken |
| 5. Adversarial inputs handled (special chars in names, large global state) | Parameterized tests: sanitize_identifier() with edge cases |

### Test Categories

1. **Unit Tests** (fast, no mocks needed)
   - sanitize_identifier() edge cases
   - format_connections() with empty/None
   - format_global_state() with empty/None
   - format_initialization_blocks() with truncation

2. **Integration Tests** (mocks for MongoDB)
   - build_context() complete flow
   - All sections present and correctly formatted
   - Token budget measurement
   - Empty state handling (no connections, no global state)

3. **Adversarial Tests** (security validation)
   - Special characters in connection/table/variable names
   - Very long names (>100 chars)
   - Prompt injection attempts
   - Unicode characters

4. **API Integration Tests** (full stack with mocks)
   - WebSocket /initialize calls all extractors
   - Data passed correctly to PromptBuilder
   - CONTEXT.md written to workspace
