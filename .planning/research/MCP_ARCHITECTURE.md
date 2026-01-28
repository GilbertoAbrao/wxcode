# Architecture Research: MCP Server Integration

**Project:** wxcode
**Dimension:** MCP Server KB Integration
**Researched:** 2026-01-21
**Confidence:** HIGH (official docs + existing codebase analysis)

---

## Executive Summary

The MCP Server integration follows a **standalone server pattern with shared infrastructure**. The MCP server runs as a separate process (stdio transport for Claude Code) but reuses wxcode's existing MongoDB/Neo4j connections and Beanie models. This approach maximizes code reuse while maintaining clean separation of concerns.

Key architectural decision: **FastMCP as standalone module** rather than mounting into the existing FastAPI app. This aligns with Claude Code's expectation of stdio-based MCP servers and simplifies deployment.

---

## Integration Points

### 1. Database Layer (Full Reuse)

| Component | Location | MCP Usage |
|-----------|----------|-----------|
| `database.py` | `src/wxcode/database.py` | Reuse `init_db()` for Beanie initialization |
| `config.py` | `src/wxcode/config.py` | Reuse `get_settings()` for all connection strings |

The MCP server will call `init_db()` at startup to initialize Beanie with the same document models used by the REST API. This ensures consistency between both interfaces.

```python
# MCP server startup
from wxcode.database import init_db
await init_db()
```

### 2. Models Layer (Full Reuse)

All Beanie document models are directly reusable:

| Model | Collection | MCP Tool Usage |
|-------|------------|----------------|
| `Project` | `projects` | `get_project_info`, context for all queries |
| `Element` | `elements` | `get_element_definition`, primary knowledge source |
| `Control` | `controls` | `get_controls`, UI component hierarchy |
| `Procedure` | `procedures` | `get_procedures`, business logic |
| `DatabaseSchema` | `schemas` | `get_schema`, data model info |

Import directly:
```python
from wxcode.models import Project, Element, Control, Procedure, DatabaseSchema
```

### 3. Graph Layer (Partial Reuse)

| Component | Location | MCP Usage |
|-----------|----------|-----------|
| `Neo4jConnection` | `src/wxcode/graph/neo4j_connection.py` | Reuse for all Neo4j queries |
| `ImpactAnalyzer` | `src/wxcode/graph/impact_analyzer.py` | Reuse for impact analysis tools |

The `Neo4jConnection` class uses async context manager pattern compatible with MCP tool execution:

```python
from wxcode.graph.neo4j_connection import Neo4jConnection

async with Neo4jConnection() as conn:
    result = await conn.execute(cypher_query, params)
```

### 4. No Reuse from API Layer

The FastAPI API layer (`src/wxcode/api/`) will **not** be reused. MCP tools need different response shapes optimized for LLM consumption, not REST/JSON responses.

---

## New Components

### Directory Structure

```
src/wxcode/mcp/
├── __init__.py           # Package init, exports mcp instance
├── server.py             # FastMCP server setup + lifespan
├── tools/
│   ├── __init__.py       # Re-exports all tools
│   ├── elements.py       # get_element_definition
│   ├── controls.py       # get_controls, get_control_hierarchy
│   ├── procedures.py     # get_procedures, search_procedures
│   ├── dependencies.py   # get_dependencies (MongoDB + Neo4j)
│   ├── conversion.py     # get_conversion_candidates, mark_as_converted
│   ├── graph.py          # get_topological_order, get_impact
│   ├── schema.py         # get_schema, get_table_info
│   └── search.py         # search_code_patterns
└── resources/            # Optional: MCP resources (read-only context)
    ├── __init__.py
    └── project.py        # Project listing as resource
```

### Component Responsibilities

#### `server.py` - Server Core

```python
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP
from wxcode.database import init_db, close_db

@asynccontextmanager
async def mcp_lifespan(server: FastMCP):
    """Initialize database connections on startup."""
    client = await init_db()
    yield
    await close_db(client)

mcp = FastMCP(
    "windev-kb",
    lifespan=mcp_lifespan
)

# Import tools to register them
from wxcode.mcp.tools import *
```

**Responsibilities:**
- FastMCP instance creation
- Lifespan management (database init/shutdown)
- Tool registration via imports

#### `tools/*.py` - Tool Implementations

Each tool module contains related MCP tools using the `@mcp.tool()` decorator:

```python
from wxcode.mcp.server import mcp
from wxcode.models import Element, Project

@mcp.tool()
async def get_element_definition(
    project_name: str,
    element_name: str
) -> dict:
    """
    Get complete definition of a WinDev element.

    Returns source code, AST, dependencies, and conversion status.
    Use this to understand what a page/procedure/class does.
    """
    # Implementation
```

**Design principles:**
- One tool per specific query need
- Rich docstrings (Claude uses them for tool selection)
- Return dicts, not Pydantic models (MCP serialization)
- Include error handling with descriptive messages

---

## Data Flow

### Tool Invocation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Code (MCP Host)                       │
│                                                                  │
│  1. User: "What does PAGE_Login do?"                            │
│  2. Claude selects: get_element_definition(...)                 │
│  3. MCP Client sends JSON-RPC request via stdio                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │ stdio (stdin/stdout)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 MCP Server (wxcode.mcp.server)               │
│                                                                  │
│  4. FastMCP routes to get_element_definition tool               │
│  5. Tool executes async function                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│      MongoDB        │       │       Neo4j         │
│   (Beanie ODM)      │       │  (Neo4jConnection)  │
│                     │       │                     │
│  Element.find_one() │       │  conn.execute()     │
│  Control.find()     │       │  ImpactAnalyzer     │
│  Procedure.find()   │       │                     │
└─────────────────────┘       └─────────────────────┘
          │                               │
          └───────────────┬───────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 MCP Server Response                              │
│                                                                  │
│  6. Tool returns dict with element data                         │
│  7. FastMCP serializes to JSON-RPC response                     │
│  8. Response sent via stdout                                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │ stdio
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Code                                  │
│                                                                  │
│  9. Claude receives tool result                                 │
│  10. Claude formulates response to user                         │
└─────────────────────────────────────────────────────────────────┘
```

### Database Session Management

**Pattern:** Initialize once at startup, reuse throughout server lifetime.

```python
# Beanie manages connection pooling automatically
# after init_db() is called in lifespan

# Tools just use models directly:
element = await Element.find_one(...)

# Neo4j needs explicit connection per query (context manager):
async with Neo4jConnection() as conn:
    result = await conn.execute(query)
```

**Why this pattern:**
- Beanie/Motor handles MongoDB connection pooling
- Neo4j AsyncGraphDatabase driver has built-in pooling
- No need for per-request connection management
- Lifespan ensures clean shutdown

---

## Transport Architecture

### Recommended: stdio Transport

```
┌──────────────────┐    stdio     ┌─────────────────────┐
│   Claude Code    │◄────────────►│    MCP Server       │
│   (MCP Client)   │   pipes      │ (python -m wxcode│
│                  │              │       .mcp.server)  │
└──────────────────┘              └─────────────────────┘
```

**Configuration (`.mcp.json`):**
```json
{
  "mcpServers": {
    "windev-kb": {
      "command": "python",
      "args": ["-m", "wxcode.mcp.server"],
      "cwd": "/path/to/wxcode",
      "env": {
        "MONGODB_URL": "mongodb://localhost:27017",
        "NEO4J_URI": "bolt://localhost:7687"
      }
    }
  }
}
```

**Why stdio (not HTTP):**
- Claude Code expects stdio for local MCP servers
- No network exposure, simpler security model
- Lower latency for local development
- Process isolation for reliability

### Alternative: HTTP Transport (Future)

If needed for remote access or multi-client scenarios:

```python
# In server.py
if __name__ == "__main__":
    import sys
    if "--http" in sys.argv:
        mcp.run(transport="streamable-http", port=8080)
    else:
        mcp.run()  # Default: stdio
```

---

## Concurrency Model

### Single-threaded Async

MCP server runs single-threaded with asyncio event loop:

```
Event Loop
    │
    ├── Handle tool request 1 (get_element_definition)
    │       │
    │       └── await Element.find_one()  ← I/O, yields control
    │
    ├── Handle tool request 2 (get_controls)
    │       │
    │       └── await Control.find()  ← I/O, yields control
    │
    └── ... concurrent async operations
```

**Implications:**
- All tools must be async (`async def`)
- No blocking I/O allowed (use async MongoDB/Neo4j drivers)
- CPU-bound work should be offloaded (rare for KB queries)

### Tool Execution Pattern

```python
@mcp.tool()
async def get_element_definition(project_name: str, element_name: str) -> dict:
    # 1. Find project (async I/O)
    project = await Project.find_one(Project.name == project_name)
    if not project:
        return {"error": f"Project not found: {project_name}"}

    # 2. Find element (async I/O)
    element = await Element.find_one(
        {"project_id.$id": project.id},
        Element.source_name == element_name
    )
    if not element:
        return {"error": f"Element not found: {element_name}"}

    # 3. Build response (CPU, minimal)
    return {
        "name": element.source_name,
        "type": element.source_type.value,
        # ...
    }
```

---

## Error Handling Strategy

### Tool-Level Error Handling

Return error information in response, don't raise exceptions:

```python
@mcp.tool()
async def get_element_definition(project_name: str, element_name: str) -> dict:
    try:
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return {
                "error": True,
                "message": f"Project not found: {project_name}",
                "suggestion": "Use get_project_list to see available projects"
            }

        element = await Element.find_one(...)
        if not element:
            return {
                "error": True,
                "message": f"Element not found: {element_name}",
                "suggestion": f"Check element name spelling or use search_elements"
            }

        return {"success": True, "data": {...}}

    except Exception as e:
        return {
            "error": True,
            "message": f"Internal error: {str(e)}",
            "type": type(e).__name__
        }
```

**Why this pattern:**
- Claude can understand and act on error messages
- Exceptions in MCP tools cause cryptic failures
- Suggestions help Claude self-correct

### Connection Error Handling

```python
@mcp.tool()
async def get_dependencies_graph(project_name: str, element_name: str) -> dict:
    try:
        async with Neo4jConnection() as conn:
            result = await conn.execute(query)
            return {"data": result}
    except Neo4jConnectionError as e:
        return {
            "error": True,
            "message": "Neo4j not available - using MongoDB fallback",
            "fallback_data": await get_mongodb_dependencies(element_name)
        }
```

---

## Build Order

Recommended implementation sequence based on dependencies:

### Phase 1: Core Infrastructure

1. **Create `src/wxcode/mcp/__init__.py`**
   - Package initialization
   - No dependencies

2. **Create `src/wxcode/mcp/server.py`**
   - FastMCP instance
   - Lifespan with database init
   - Dependencies: `wxcode.database`, `wxcode.config`

### Phase 2: Essential Tools

3. **Create `src/wxcode/mcp/tools/__init__.py`**
   - Re-export all tools
   - Dependencies: Phase 1

4. **Create `src/wxcode/mcp/tools/elements.py`**
   - `get_element_definition` tool
   - Dependencies: `wxcode.models.Element`, `wxcode.models.Project`

5. **Create `src/wxcode/mcp/tools/controls.py`**
   - `get_controls` tool
   - Dependencies: `wxcode.models.Control`

6. **Create `src/wxcode/mcp/tools/procedures.py`**
   - `get_procedures` tool
   - Dependencies: `wxcode.models.Procedure`

### Phase 3: Graph Tools

7. **Create `src/wxcode/mcp/tools/dependencies.py`**
   - `get_dependencies` (MongoDB-based)
   - Dependencies: `wxcode.models.Element`

8. **Create `src/wxcode/mcp/tools/graph.py`**
   - `get_topological_order`, `get_impact`
   - Dependencies: `wxcode.graph.neo4j_connection`, `wxcode.graph.impact_analyzer`

### Phase 4: Conversion Tools

9. **Create `src/wxcode/mcp/tools/conversion.py`**
   - `get_conversion_candidates`, `mark_as_converted`
   - Dependencies: All previous phases

10. **Create `src/wxcode/mcp/tools/search.py`**
    - `search_code_patterns`
    - Dependencies: `wxcode.models.Element`

### Phase 5: Configuration and Testing

11. **Create `.mcp.json`**
    - MCP server configuration for Claude Code

12. **Test integration**
    - Verify all tools work in Claude Code

---

## Dependency Graph

```
                          ┌─────────────────┐
                          │   wxcode     │
                          │    .config      │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │   wxcode     │
                          │   .database     │
                          └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
           ┌────────▼───────┐ ┌───▼────┐  ┌──────▼──────┐
           │   wxcode    │ │wxcode│  │  wxcode  │
           │    .models     │ │ .graph  │  │ .mcp.server │
           └────────┬───────┘ └────┬────┘  └──────┬──────┘
                    │              │              │
                    └──────────────┴──────────────┘
                                   │
                          ┌────────▼────────┐
                          │   wxcode     │
                          │   .mcp.tools    │
                          └─────────────────┘
```

---

## Alternative Architectures Considered

### Option A: Mount MCP into FastAPI (Rejected)

```python
# Would look like:
from fastapi import FastAPI
from wxcode.mcp.server import mcp

app = FastAPI(lifespan=combined_lifespan)
app.mount("/mcp", mcp.http_app())
```

**Why rejected:**
- Claude Code expects stdio transport for local servers
- Adds complexity to existing FastAPI lifespan
- HTTP transport adds latency for local use
- MCP server lifecycle should be independent of API server

### Option B: Auto-generate from FastAPI routes (Rejected)

```python
# Would look like:
mcp = FastMCP.from_fastapi(app=existing_fastapi_app)
```

**Why rejected:**
- REST responses not optimized for LLM consumption
- Would expose all API endpoints as tools (too many)
- Tools need richer docstrings than OpenAPI provides
- Different error handling requirements

### Option C: Separate repository/package (Rejected)

**Why rejected:**
- Loses direct access to Beanie models
- Adds deployment complexity
- Requires publishing internal models as shared package
- Current codebase is cohesive enough to contain MCP

---

## Security Considerations

### No Authentication Needed

- stdio transport only accessible by parent process (Claude Code)
- No network exposure in default configuration
- MongoDB/Neo4j credentials from existing `.env`

### Data Access Scope

- MCP tools access same data as REST API
- No additional data exposure
- Consider adding project-scoped access if multi-tenant

### Sensitive Data Handling

```python
@mcp.tool()
async def get_element_definition(...) -> dict:
    # Don't include API keys, passwords, connection strings
    return {
        "name": element.source_name,
        "raw_content": element.raw_content,  # Code is OK
        # NOT: "connection_string": settings.mongodb_url
    }
```

---

## Performance Considerations

### Query Optimization

- Use Beanie indexes (already defined in models)
- Limit returned fields for large collections
- Paginate large result sets

```python
@mcp.tool()
async def get_controls(project_name: str, element_name: str, limit: int = 100) -> dict:
    controls = await Control.find(
        Control.element_id == element.id
    ).limit(limit).to_list()
```

### Neo4j Query Optimization

- Use parameterized queries (avoid injection, enable caching)
- Limit traversal depth
- Use indexes on frequently queried properties

---

## Quality Checklist

- [x] Integration points clearly identified (database, models, graph layers)
- [x] New vs modified components explicit (new mcp/ module, no modifications to existing)
- [x] Build order considers existing dependencies (5 phases, 12 steps)
- [x] Data flow documented (tool invocation diagram)
- [x] Transport architecture decided (stdio for Claude Code)
- [x] Error handling strategy defined (return errors, don't raise)
- [x] Alternatives considered and rejected with rationale

---

## Sources

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) - Official SDK documentation
- [FastMCP FastAPI Integration](https://gofastmcp.com/integrations/fastapi) - Integration patterns
- [MCP Architecture Overview](https://modelcontextprotocol.io/docs/learn/architecture) - Protocol architecture
- [MCP Build Client](https://modelcontextprotocol.io/docs/develop/build-client) - Transport options
- Existing codebase: `src/wxcode/` - Current implementation patterns
- Handoff document: `.planning/HANDOFF_MCP_KB_INTEGRATION.md` - Project context
