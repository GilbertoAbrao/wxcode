# Architecture Patterns: Initialization Context Integration

**Domain:** WXCODE Project Initialization Context Extraction
**Researched:** 2026-01-24
**Confidence:** HIGH (based on direct codebase analysis)

## Executive Summary

This document analyzes how initialization context extraction integrates with the existing PromptBuilder architecture. The current system has a clean separation between:
1. **Data Extraction** (schema_extractor.py, GlobalStateExtractor)
2. **Prompt Building** (PromptBuilder, MilestonePromptBuilder)
3. **GSD Invocation** (GSDInvoker, output_projects.py WebSocket)

The integration requires extending the extraction layer to pull connections, global state, and initialization code, then modifying PromptBuilder to format these new data sources into CONTEXT.md.

## Current Architecture

### Data Flow (Current State)

```
+-----------------------------------------------------------------------------+
|                         WebSocket /initialize Endpoint                       |
|                         (output_projects.py:267)                            |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                    1. extract_schema_for_configuration()                     |
|                       (schema_extractor.py:15)                              |
|                                                                             |
|    Input: project_id, configuration_id                                      |
|    Output: list[dict] (tables with columns, indexes)                        |
|                                                                             |
|    Source: DatabaseSchema.tables (MongoDB)                                  |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                    2. PromptBuilder.write_context_file()                     |
|                       (prompt_builder.py:196)                               |
|                                                                             |
|    Input: output_project, stack, tables, workspace_path                     |
|    Output: CONTEXT.md file written to workspace                             |
|                                                                             |
|    Template: PROMPT_TEMPLATE (line 15)                                      |
|    Sections: Project Info, Stack Characteristics, Database Schema           |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                    3. GSDInvoker.invoke_with_streaming()                     |
|                       (gsd_invoker.py:213)                                  |
|                                                                             |
|    Input: context_md_path, working_dir                                      |
|    Output: WebSocket streaming, exit code                                   |
|                                                                             |
|    Command: claude -p "/gsd:new-project CONTEXT.md"                         |
+-----------------------------------------------------------------------------+
```

### Existing Components to Leverage

| Component | Location | Current Function | Integration Point |
|-----------|----------|------------------|-------------------|
| `DatabaseSchema.connections` | models/schema.py:95 | Stores connection configs | **Existing data source** |
| `GlobalStateExtractor` | parser/global_state_extractor.py | Extracts GLOBAL variables | **Existing but not integrated** |
| `GlobalStateContext` | models/global_state_context.py | IR for global state | **Existing model** |
| `schema_extractor.py` | services/schema_extractor.py | Extracts tables | **Extension point** |
| `PromptBuilder` | services/prompt_builder.py | Builds CONTEXT.md | **Extension point** |
| `orchestrator._extract_global_state()` | generator/orchestrator.py:238 | Full extraction logic | **Reference implementation** |

### Data Sources in MongoDB

```
+-----------------------------------------------------------------------------+
|                            MongoDB Collections                               |
+-----------------------------------------------------------------------------+
|                                                                             |
|  schemas (DatabaseSchema)                                                   |
|  +-- project_id: ObjectId                                                   |
|  +-- connections: [SchemaConnection]  <-- CONNECTIONS (existing)            |
|  |   +-- name: str ("CNX_BASE_HOMOLOG")                                    |
|  |   +-- type_code: int (1 = SQL Server)                                   |
|  |   +-- database_type: str ("sqlserver")                                  |
|  |   +-- source: str (server host)                                         |
|  |   +-- port: str ("1433")                                                |
|  |   +-- database: str (db name)                                           |
|  +-- tables: [SchemaTable]            <-- TABLES (currently used)           |
|                                                                             |
|  elements (Element)                                                         |
|  +-- project_id: ObjectId                                                   |
|  +-- windev_type: int                                                       |
|  |   +-- 0 = Project Code            <-- GLOBAL state + INIT code          |
|  |   +-- 31 = WDG (Procedure Group)  <-- MODULE-level globals              |
|  +-- raw_content: str                <-- WLanguage source code             |
|  +-- source_name: str                                                       |
|                                                                             |
+-----------------------------------------------------------------------------+
```

## Recommended Architecture

### Extended Data Flow

```
+-----------------------------------------------------------------------------+
|                         WebSocket /initialize Endpoint                       |
+-----------------------------------------------------------------------------+
                                      |
        +-----------------------------+-----------------------------+
        |                             |                             |
        v                             v                             v
+-------------------+   +-------------------+   +---------------------------+
| extract_schema    |   | extract_connections|   | extract_global_state      |
| _for_config()     |   | (NEW function)     |   | _for_config()             |
|                   |   |                   |   | (NEW function)            |
| Source: Schema    |   | Source: Schema    |   | Source: Elements          |
| Output: tables[]  |   | Output: conns[]   |   | Output: GlobalStateContext|
+-------------------+   +-------------------+   +---------------------------+
        |                             |                             |
        +-----------------------------+-----------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                   PromptBuilder.build_context() [EXTENDED]                   |
|                                                                             |
|   Input: output_project, stack, tables, connections, global_state           |
|   Output: CONTEXT.md with new sections:                                     |
|     - ## Database Connections                                               |
|     - ## Global State (Application-level)                                   |
|     - ## Initialization Code                                                |
|     - ## MCP Server Instructions                                            |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                    GSDInvoker.invoke_with_streaming()                        |
|                       (unchanged)                                           |
+-----------------------------------------------------------------------------+
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `schema_extractor.py` | Extract tables and connections from DatabaseSchema | MongoDB schemas collection |
| `init_context_extractor.py` (NEW) | Extract global state and init code from Elements | MongoDB elements collection, GlobalStateExtractor |
| `PromptBuilder` | Format all extracted data into CONTEXT.md | Extractors, Stack model |
| `output_projects.py` | Orchestrate extraction and invoke GSD | All extractors, PromptBuilder, GSDInvoker |

## Integration Points

### 1. schema_extractor.py Extension

**Current signature:**
```python
async def extract_schema_for_configuration(
    project_id: PydanticObjectId,
    configuration_id: Optional[str],
) -> list[dict]:
```

**New function to add:**
```python
async def extract_connections_for_configuration(
    project_id: PydanticObjectId,
) -> list[dict]:
    """
    Extract database connections from schema.

    Returns:
        List of connection dicts with:
        - name: str
        - database_type: str (sqlserver, mysql, postgresql)
        - driver_name: str (human-readable)
        - source: str (host)
        - port: str
        - database: str
    """
```

**Rationale:** Keep connection extraction in schema_extractor.py since connections are part of DatabaseSchema model. Simple function that queries `DatabaseSchema.connections`.

### 2. New init_context_extractor.py Service

**Purpose:** Extract global state and initialization code from Project Code elements.

```python
# services/init_context_extractor.py

from wxcode.models.element import Element
from wxcode.models.global_state_context import GlobalStateContext
from wxcode.parser.global_state_extractor import GlobalStateExtractor

async def extract_global_state_for_configuration(
    project_id: PydanticObjectId,
    configuration_id: Optional[str] = None,
) -> GlobalStateContext:
    """
    Extract global state from Project Code and WDGs.

    Follows same pattern as orchestrator._extract_global_state() but:
    - Respects configuration_id exclusion scope
    - Returns stack-agnostic IR (GlobalStateContext)

    Returns:
        GlobalStateContext with variables and init blocks
    """
```

**Design decision:** Separate file rather than adding to schema_extractor because:
1. Different data source (elements collection vs schemas collection)
2. More complex logic (uses GlobalStateExtractor)
3. Returns different type (GlobalStateContext vs list[dict])

### 3. PromptBuilder.build_context() Extension

**Current signature:**
```python
@classmethod
def build_context(
    cls,
    output_project: OutputProject,
    stack: Stack,
    tables: list[dict],
) -> str:
```

**Extended signature:**
```python
@classmethod
def build_context(
    cls,
    output_project: OutputProject,
    stack: Stack,
    tables: list[dict],
    connections: list[dict] = None,           # NEW
    global_state: GlobalStateContext = None,  # NEW
) -> str:
```

**Backward compatibility:** Optional parameters with defaults preserve existing behavior.

### 4. PROMPT_TEMPLATE Extension

Add new sections after `## Database Schema`:

```markdown
## Database Connections ({connection_count} connections)

{connections_section}

## Global State

### Application-level Variables
{app_variables_section}

### Module-level Variables
{module_variables_section}

## Initialization Code

The following WLanguage code runs at application startup:

```wlanguage
{initialization_code}
```

## MCP Server Instructions

This project will connect to a WXCODE MCP server for database operations.
Configure your environment with:

- `WXCODE_MCP_URL`: URL of WXCODE API
- Connection names match the Database Connections section above
```

## New Functions/Services Needed

### 1. extract_connections_for_configuration (schema_extractor.py)

```python
async def extract_connections_for_configuration(
    project_id: PydanticObjectId,
) -> list[dict]:
    """
    Extract database connections from schema.

    Note: Connections are project-wide (not scoped by configuration).
    """
    schema = await DatabaseSchema.find_one(
        DatabaseSchema.project_id == project_id
    )
    if not schema or not schema.connections:
        return []

    return [
        {
            "name": conn.name,
            "database_type": conn.database_type,
            "driver_name": conn.driver_name,
            "source": conn.source,
            "port": conn.port,
            "database": conn.database,
        }
        for conn in schema.connections
    ]
```

### 2. extract_global_state_for_configuration (NEW: init_context_extractor.py)

```python
async def extract_global_state_for_configuration(
    project_id: PydanticObjectId,
    configuration_id: Optional[str] = None,
) -> GlobalStateContext:
    """
    Extract global state from Project Code and WDGs.
    """
    extractor = GlobalStateExtractor()
    all_variables = []
    all_init_blocks = []

    # Query builder with optional configuration scope
    base_query = {"project_id": project_id}
    if configuration_id:
        base_query["excluded_from"] = {"$nin": [configuration_id]}

    # Project Code (windev_type: 0) - APP scope
    project_elements = await Element.find(
        {**base_query, "windev_type": 0}
    ).to_list()

    for elem in project_elements:
        if elem.raw_content:
            variables = extractor.extract_variables(
                elem.raw_content, elem.windev_type, elem.source_name
            )
            init_blocks = extractor.extract_initialization(elem.raw_content)
            all_variables.extend(variables)
            all_init_blocks.extend(init_blocks)

    # WDGs (windev_type: 31) - MODULE scope
    wdg_elements = await Element.find(
        {**base_query, "windev_type": 31}
    ).to_list()

    for elem in wdg_elements:
        if elem.raw_content:
            variables = extractor.extract_variables(
                elem.raw_content, elem.windev_type, elem.source_name
            )
            init_blocks = extractor.extract_initialization(elem.raw_content)
            all_variables.extend(variables)
            all_init_blocks.extend(init_blocks)

    return GlobalStateContext.from_extractor_results(
        all_variables, all_init_blocks
    )
```

### 3. PromptBuilder Formatting Helpers

```python
@staticmethod
def format_connections(connections: list[dict]) -> str:
    """Format connections as markdown table."""
    if not connections:
        return "*No database connections defined.*"

    lines = [
        "| Name | Type | Host | Port | Database |",
        "|------|------|------|------|----------|",
    ]
    for conn in connections:
        lines.append(
            f"| {conn['name']} | {conn['driver_name']} | "
            f"{conn['source']} | {conn['port']} | {conn['database']} |"
        )
    return "\n".join(lines)

@staticmethod
def format_global_variables(global_state: GlobalStateContext, scope: Scope) -> str:
    """Format variables of given scope as markdown table."""
    variables = global_state.get_by_scope(scope)
    if not variables:
        return "*None*"

    lines = [
        "| Variable | WLanguage Type | Default | Source |",
        "|----------|----------------|---------|--------|",
    ]
    for var in variables:
        default = var.default_value or "-"
        lines.append(
            f"| `{var.name}` | `{var.wlanguage_type}` | "
            f"{default} | {var.source_element} |"
        )
    return "\n".join(lines)

@staticmethod
def format_initialization_code(global_state: GlobalStateContext) -> str:
    """Format initialization blocks as code."""
    if not global_state.initialization_blocks:
        return "// No initialization code"

    blocks = []
    for block in global_state.initialization_blocks:
        blocks.append(f"// Dependencies: {', '.join(block.dependencies)}")
        blocks.append(block.code)
    return "\n\n".join(blocks)
```

## Build Order

Based on dependencies, recommended implementation order:

```
Phase 1: Connection Extraction (no dependencies)
+-- Add extract_connections_for_configuration() to schema_extractor.py
+-- Add format_connections() to PromptBuilder

Phase 2: Global State Extraction (depends on existing GlobalStateExtractor)
+-- Create services/init_context_extractor.py
+-- Add extract_global_state_for_configuration()
+-- Add format_global_variables() to PromptBuilder

Phase 3: Initialization Code Extraction (depends on Phase 2)
+-- Add format_initialization_code() to PromptBuilder
+-- Update PROMPT_TEMPLATE with new sections

Phase 4: Integration (depends on Phases 1-3)
+-- Update PromptBuilder.build_context() signature
+-- Update output_projects.py WebSocket to call new extractors
+-- Test end-to-end flow

Phase 5: MCP Instructions (independent, can be parallel with Phase 4)
+-- Add MCP server configuration section to PROMPT_TEMPLATE
```

## Patterns to Follow

### Pattern 1: Extraction Function Signature

All extraction functions follow this pattern:

```python
async def extract_{what}_for_configuration(
    project_id: PydanticObjectId,
    configuration_id: Optional[str] = None,  # Optional scope
) -> {return_type}:
    """
    Extract {what} from {source}.

    Args:
        project_id: Knowledge Base (Project) ID
        configuration_id: Optional Configuration for scoping

    Returns:
        {description of return type}
    """
```

**Why:** Consistent interface, easy to test, respects configuration scope.

### Pattern 2: Graceful Degradation

All new extraction should handle missing data gracefully:

```python
# Good: Handle empty/None gracefully
if not schema or not schema.connections:
    return []

# Good: Optional parameters with sensible defaults
def build_context(
    ...,
    connections: list[dict] = None,  # None = skip section
    global_state: GlobalStateContext = None,
):
    ...
    if connections:
        sections.append(format_connections(connections))
```

**Why:** Existing projects without connections/global state should still work.

### Pattern 3: Stack-Agnostic IR

Global state extraction returns WLanguage types (not Python/TypeScript types):

```python
GlobalVariable(
    name="gCnn",
    wlanguage_type="Connection",  # NOT "sqlalchemy.Connection"
    ...
)
```

**Why:** Type mapping is the responsibility of generators/Claude Code, not extractors. This keeps extraction clean and testable.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Modifying Existing Models

**Bad:** Adding new fields to DatabaseSchema or Element models just for this feature.

**Why bad:** Requires migration, affects other parts of codebase.

**Instead:** Work with existing model structure. All needed data is already there.

### Anti-Pattern 2: Complex Queries in PromptBuilder

**Bad:**
```python
class PromptBuilder:
    async def build_context(...):
        # Query MongoDB directly here
        elements = await Element.find(...).to_list()
```

**Why bad:** PromptBuilder is synchronous, formatting-focused. Mixing I/O violates separation.

**Instead:** Keep extraction in service layer, pass results to PromptBuilder.

### Anti-Pattern 3: Duplicating GlobalStateExtractor Logic

**Bad:** Writing new regex patterns for parsing GLOBAL blocks.

**Why bad:** GlobalStateExtractor already handles this correctly.

**Instead:** Reuse GlobalStateExtractor, just wrap it with configuration scoping.

## Scalability Considerations

| Concern | At 10 elements | At 1000 elements | At 10000 elements |
|---------|----------------|------------------|-------------------|
| Connection extraction | Instant (1 schema doc) | Same | Same |
| Global state extraction | ~100ms (few Project Code elements) | ~500ms | Consider pagination |
| CONTEXT.md size | ~5KB | ~20KB | May need truncation |

**Note:** For very large projects, consider adding `--limit` flags to extractors or summarization.

## Sources

All findings based on direct codebase analysis:

- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/prompt_builder.py`
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/schema_extractor.py`
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/api/output_projects.py`
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/global_state_extractor.py`
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/global_state_context.py`
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/schema.py`
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/generator/orchestrator.py` (lines 238-287)
