# Phase 5: Essential Retrieval Tools - Research

**Researched:** 2026-01-21
**Domain:** FastMCP tool registration, Beanie query patterns, MongoDB aggregation, tool response formatting
**Confidence:** HIGH

## Summary

Phase 5 implements 9 read-only MCP tools that expose the wxcode Knowledge Base to Claude Code. The research confirms that **FastMCP's `@mcp.tool` decorator** with **type-annotated parameters** is the correct approach for tool registration. The existing Beanie models (`Element`, `Control`, `Procedure`, `DatabaseSchema`) provide well-indexed collections that can be queried efficiently. The lifespan context from Phase 4 provides database connections that tools access via `ctx.lifespan_context`.

Key findings:
1. FastMCP automatically generates JSON schemas from Python type hints - use explicit types
2. Access lifespan context via `ctx.lifespan_context["key"]` in every tool that needs database
3. Beanie queries use `Model.find()`, `Model.find_one()`, and `Model.aggregate()` patterns
4. Return dicts, not Pydantic models (MCP serialization requires JSON-serializable return values)
5. Error handling should return error objects, not raise exceptions
6. GSD context collector (`gsd_context_collector.py`) has battle-tested query patterns to adapt

**Primary recommendation:** Create one tool file per domain (elements, controls, procedures, schema) with 2-3 tools each. Use existing query patterns from `gsd_context_collector.py`. Return structured dicts with explicit error handling.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastmcp | 2.14.x | MCP tool registration | `@mcp.tool` decorator with type hints |
| beanie | 2.0.x | MongoDB ODM | Async queries, already has models |
| pydantic | 2.10.x | Data validation | Type hints for tool parameters |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| bson | via pymongo | ObjectId handling | When querying by `_id` |
| re | stdlib | Regex patterns | For `search_code` tool |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Beanie queries | Raw Motor | More boilerplate, less type safety |
| Return dicts | Return Pydantic | FastMCP serializes dicts natively |
| Multiple tool files | Single file | Organization vs fewer imports |

**Installation:**
No additional packages needed. All dependencies already in project.

## Architecture Patterns

### Recommended Project Structure
```
src/wxcode/mcp/
├── __init__.py
├── server.py                 # FastMCP server (from Phase 4)
└── tools/
    ├── __init__.py           # Re-exports, registers all tools
    ├── elements.py           # get_element, list_elements, search_code
    ├── controls.py           # get_controls, get_data_bindings
    ├── procedures.py         # get_procedures, get_procedure
    └── schema.py             # get_schema, get_table
```

### Pattern 1: Tool Registration with Type Hints
**What:** Use `@mcp.tool` decorator with fully typed parameters
**When to use:** Every MCP tool
**Example:**
```python
# Source: FastMCP official docs + project patterns
from fastmcp import Context
from wxcode.mcp.server import mcp

@mcp.tool
async def get_element(
    ctx: Context,
    element_name: str,
    project_name: str | None = None,
    include_raw_content: bool = True
) -> dict:
    """
    Get complete definition of a WinDev element.

    Returns source code, AST, dependencies, and conversion status.
    Use this to understand what a page/procedure/class does.

    Args:
        element_name: Name of the element (e.g., PAGE_Login, ServerProcedures)
        project_name: Optional project name. If omitted, searches all projects.
        include_raw_content: Include full raw source code (default True)

    Returns:
        Complete element definition or error if not found
    """
    # Implementation
    ...
```

**Key points:**
- `ctx: Context` is automatically injected by FastMCP
- `str | None = None` provides optional parameters with defaults
- Docstring becomes tool description (Claude uses this for selection)
- Return `dict`, not Pydantic model

### Pattern 2: Accessing Lifespan Context
**What:** Get database connections from lifespan via context
**When to use:** Every tool that queries MongoDB or Neo4j
**Example:**
```python
# Source: https://gofastmcp.com/servers/lifespan
from fastmcp import Context

@mcp.tool
async def get_element(ctx: Context, element_name: str) -> dict:
    """Get element by name."""
    # Access lifespan context
    neo4j_available = ctx.lifespan_context.get("neo4j_available", False)
    neo4j_conn = ctx.lifespan_context.get("neo4j_conn")

    # MongoDB doesn't need explicit client access - Beanie is initialized
    element = await Element.find_one(Element.source_name == element_name)
    ...
```

**Key insight:** MongoDB/Beanie doesn't require passing the client after `init_beanie()`. The ODM is globally initialized. Neo4j connection must be explicitly accessed from context.

### Pattern 3: Project-Scoped Queries with DBRef
**What:** Query elements within a specific project using DBRef
**When to use:** When `project_name` parameter is provided
**Example:**
```python
# Source: gsd_context_collector.py lines 170-198
from bson import DBRef
from wxcode.config import get_settings
from wxcode.models import Project, Element

async def find_element_in_project(
    ctx: Context,
    element_name: str,
    project_name: str
) -> Element | None:
    """Find element within specific project."""
    project = await Project.find_one(Project.name == project_name)
    if not project:
        return None

    # Get raw Motor collection for DBRef query
    settings = get_settings()
    mongo_client = ctx.lifespan_context["mongo_client"]
    db = mongo_client[settings.mongodb_database]
    collection = db["elements"]

    # Query with DBRef comparison
    project_dbref = DBRef("projects", project.id)
    elem_dict = await collection.find_one({
        "source_name": element_name,
        "project_id": project_dbref
    })

    if elem_dict:
        return await Element.get(elem_dict["_id"])
    return None
```

**Why this pattern:** Beanie's `Link` fields store DBRefs internally, requiring raw Motor queries for proper comparison.

### Pattern 4: Error Response Pattern
**What:** Return structured error objects instead of raising exceptions
**When to use:** Any error condition in tools
**Example:**
```python
# Source: Phase 4 research + MCP best practices
@mcp.tool
async def get_element(ctx: Context, element_name: str) -> dict:
    """Get element by name."""
    try:
        element = await Element.find_one(Element.source_name == element_name)

        if not element:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Element '{element_name}' not found",
                "suggestion": "Use list_elements to see available elements"
            }

        return {
            "error": False,
            "data": {
                "name": element.source_name,
                "type": element.source_type.value,
                # ... more fields
            }
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__
        }
```

**Why this pattern:** MCP exceptions cause cryptic failures. Returning error objects lets Claude understand and recover.

### Pattern 5: Beanie to Dict Serialization
**What:** Convert Beanie documents to JSON-serializable dicts
**When to use:** Every tool return value
**Example:**
```python
# Source: gsd_context_collector.py, model_dump pattern
from datetime import datetime
from beanie import PydanticObjectId

def serialize_element(element: Element, include_raw: bool = True) -> dict:
    """Serialize Element to JSON-safe dict."""
    data = {
        "id": str(element.id),
        "name": element.source_name,
        "type": element.source_type.value,  # Enum to string
        "file": element.source_file,
        "layer": element.layer.value if element.layer else None,
        "topological_order": element.topological_order,
        "conversion_status": element.conversion.status.value,
    }

    if include_raw and element.raw_content:
        data["raw_content"] = element.raw_content

    if element.ast:
        data["ast"] = element.ast.model_dump(mode="json")

    if element.dependencies:
        data["dependencies"] = element.dependencies.model_dump(mode="json")

    return data
```

**Key point:** Use `model_dump(mode="json")` for nested Pydantic models. Convert `PydanticObjectId` to `str`.

### Pattern 6: Regex Search with MongoDB
**What:** Search code patterns using `$regex` operator
**When to use:** `search_code` tool
**Example:**
```python
# Source: MongoDB documentation + project patterns
import re
from wxcode.models import Element

@mcp.tool
async def search_code(
    ctx: Context,
    pattern: str,
    project_name: str | None = None,
    element_types: list[str] | None = None,
    limit: int = 50
) -> dict:
    """Search code patterns across elements using regex."""
    # Build query
    query = {}

    if project_name:
        project = await Project.find_one(Project.name == project_name)
        if project:
            query["project_id.$id"] = project.id

    if element_types:
        query["source_type"] = {"$in": element_types}

    # Regex search in raw_content
    query["raw_content"] = {"$regex": pattern, "$options": "i"}  # Case-insensitive

    # Execute with limit
    elements = await Element.find(query).limit(limit).to_list()

    return {
        "error": False,
        "pattern": pattern,
        "matches": len(elements),
        "results": [
            {
                "name": e.source_name,
                "type": e.source_type.value,
                "preview": extract_match_preview(e.raw_content, pattern)
            }
            for e in elements
        ]
    }

def extract_match_preview(content: str, pattern: str, context_chars: int = 100) -> str:
    """Extract preview around first match."""
    match = re.search(pattern, content, re.IGNORECASE)
    if not match:
        return ""
    start = max(0, match.start() - context_chars)
    end = min(len(content), match.end() + context_chars)
    preview = content[start:end]
    if start > 0:
        preview = "..." + preview
    if end < len(content):
        preview = preview + "..."
    return preview
```

### Anti-Patterns to Avoid
- **Raising exceptions:** Return error dicts instead
- **print() in tools:** Corrupts JSON-RPC, use `await ctx.info()` if needed
- **Returning Pydantic models:** MCP expects JSON-serializable dicts
- **Forgetting async:** All Beanie queries are async, must await
- **Large raw_content by default:** Consider `include_raw_content=False` default for list operations
- **No pagination:** Always use `limit` parameter for list/search operations

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Element lookup with project scope | Custom DBRef query | Pattern from `gsd_context_collector.py` | Already handles DBRef edge cases |
| Control hierarchy | Recursive queries | `Control.find().sort("+full_path")` | Full path encodes hierarchy |
| Procedure list by element | Custom join | `Procedure.find({"element_id": id})` | Index exists |
| Schema table lookup | Iterate all | `DatabaseSchema.find_one()` with project | Single document per project |
| JSON serialization | Custom encoder | `model_dump(mode="json")` | Handles ObjectIds, datetimes |

**Key insight:** The `gsd_context_collector.py` file contains production-tested patterns for every query we need. Adapt, don't reinvent.

## Common Pitfalls

### Pitfall 1: DBRef Comparison in Beanie
**What goes wrong:** `Element.project_id == project.id` doesn't work with Link fields
**Why it happens:** Beanie stores Link fields as DBRef, not raw ObjectId
**How to avoid:** Use raw Motor collection with DBRef comparison (see Pattern 3)
**Warning signs:** Empty results when project filter should match

### Pitfall 2: Large Response Payloads
**What goes wrong:** Tool returns huge `raw_content` for many elements, context window explodes
**Why it happens:** Including full code for list operations
**How to avoid:** Default `include_raw_content=False` for list operations; add `limit` parameter
**Warning signs:** Slow responses, Claude complains about context

### Pitfall 3: Enum Serialization
**What goes wrong:** `ElementType.PAGE` becomes `<ElementType.PAGE: 'page'>` in output
**Why it happens:** Not calling `.value` on enums
**How to avoid:** Always use `enum_field.value` when building response dicts
**Warning signs:** Claude tries to use enum repr as value

### Pitfall 4: ObjectId Serialization
**What goes wrong:** `ObjectId('...')` appears in JSON, breaks parsing
**Why it happens:** `PydanticObjectId` not JSON-serializable
**How to avoid:** Convert to `str(object_id)` in response
**Warning signs:** JSON parse errors, invalid tool responses

### Pitfall 5: Missing Tool in Claude Code
**What goes wrong:** Tool defined but not appearing in Claude Code
**Why it happens:** Tool file not imported in `tools/__init__.py`
**How to avoid:** Ensure all tool modules are imported in `__init__.py`
**Warning signs:** Tool works in tests but not in Claude Code

### Pitfall 6: Tool Count Explosion
**What goes wrong:** >15 tools causes context explosion in Claude
**Why it happens:** Each tool definition consumes context tokens
**How to avoid:** Monitor tool count; combine related tools if needed
**Warning signs:** Claude struggles to select tools, slow responses

## Tool Specifications

### CORE-01: `get_element`
**Purpose:** Get complete element definition by name
**Parameters:**
- `element_name: str` (required) - Element name (e.g., PAGE_Login)
- `project_name: str | None = None` - Project scope (optional)
- `include_raw_content: bool = True` - Include source code

**Returns:**
```python
{
    "error": False,
    "data": {
        "id": "...",
        "name": "PAGE_Login",
        "type": "page",
        "file": "PAGE_Login.wwh",
        "layer": "ui",
        "topological_order": 15,
        "conversion_status": "pending",
        "raw_content": "...",  # if include_raw_content
        "ast": {...},
        "dependencies": {
            "uses": [...],
            "used_by": [...],
            "data_files": [...],
            "external_apis": [...]
        }
    }
}
```

**Query pattern:**
```python
# If project_name provided
element = await find_element_in_project(ctx, element_name, project_name)
# Otherwise
element = await Element.find_one(Element.source_name == element_name)
```

### CORE-02: `list_elements`
**Purpose:** List elements with filters
**Parameters:**
- `project_name: str | None = None` - Filter by project
- `element_type: str | None = None` - Filter by type (page, procedure_group, class, etc.)
- `layer: str | None = None` - Filter by layer (schema, domain, business, api, ui)
- `conversion_status: str | None = None` - Filter by status
- `limit: int = 100` - Max results

**Returns:**
```python
{
    "error": False,
    "total": 250,
    "returned": 100,
    "elements": [
        {
            "name": "PAGE_Login",
            "type": "page",
            "layer": "ui",
            "conversion_status": "pending"
        },
        ...
    ]
}
```

**Query pattern:**
```python
query = {}
if project_name:
    project = await Project.find_one(Project.name == project_name)
    if project:
        query["project_id.$id"] = project.id
if element_type:
    query["source_type"] = element_type
if layer:
    query["layer"] = layer
if conversion_status:
    query["conversion.status"] = conversion_status

elements = await Element.find(query).limit(limit).to_list()
```

### CORE-03: `search_code`
**Purpose:** Search code patterns using regex
**Parameters:**
- `pattern: str` (required) - Regex pattern
- `project_name: str | None = None` - Filter by project
- `element_types: list[str] | None = None` - Filter by types
- `limit: int = 50` - Max results

**Returns:**
```python
{
    "error": False,
    "pattern": "HReadFirst.*CLIENTE",
    "matches": 12,
    "results": [
        {
            "name": "PAGE_Login",
            "type": "page",
            "preview": "...HReadFirst(CLIENTE, IDX_CPF)..."
        },
        ...
    ]
}
```

### UI-01: `get_controls`
**Purpose:** Get control hierarchy for an element
**Parameters:**
- `element_name: str` (required)
- `project_name: str | None = None`
- `include_events: bool = True`
- `include_properties: bool = True`

**Returns:**
```python
{
    "error": False,
    "element": "PAGE_Login",
    "total_controls": 45,
    "controls": [
        {
            "name": "EDT_LOGIN",
            "type_code": 8,
            "type_name": "Edit",
            "full_path": "CELL_NoName1.EDT_LOGIN",
            "depth": 1,
            "has_code": True,
            "is_bound": True,
            "properties": {...},  # if include_properties
            "events": [...]       # if include_events
        },
        ...
    ]
}
```

**Query pattern:**
```python
# From gsd_context_collector.py line 251
controls = await Control.find({"element_id": element.id}).sort("+full_path").to_list()

# Get type definitions for readable names
type_codes = list(set(c.type_code for c in controls))
type_defs = await ControlTypeDefinition.find({"type_code": {"$in": type_codes}}).to_list()
type_map = {td.type_code: td.type_name for td in type_defs}
```

### UI-02: `get_data_bindings`
**Purpose:** Get control-to-table data bindings for an element
**Parameters:**
- `element_name: str` (required)
- `project_name: str | None = None`

**Returns:**
```python
{
    "error": False,
    "element": "PAGE_Login",
    "total_bindings": 8,
    "bindings": [
        {
            "control_name": "EDT_LOGIN",
            "control_path": "CELL_NoName1.EDT_LOGIN",
            "binding_type": "simple",
            "table_name": "USUARIO",
            "field_name": "login"
        },
        ...
    ],
    "tables_referenced": ["USUARIO", "PERFIL"]
}
```

**Query pattern:**
```python
controls = await Control.find({
    "element_id": element.id,
    "is_bound": True
}).to_list()

bindings = []
tables = set()
for ctrl in controls:
    if ctrl.data_binding:
        bindings.append({
            "control_name": ctrl.name,
            "control_path": ctrl.full_path,
            "binding_type": ctrl.data_binding.binding_type.value,
            "table_name": ctrl.data_binding.table_name,
            "field_name": ctrl.data_binding.field_name,
        })
        if ctrl.data_binding.table_name:
            tables.add(ctrl.data_binding.table_name)
```

### PROC-01: `get_procedures`
**Purpose:** List procedures for an element
**Parameters:**
- `element_name: str` (required)
- `project_name: str | None = None`
- `include_code: bool = False` - Include full procedure code

**Returns:**
```python
{
    "error": False,
    "element": "ServerProcedures",
    "total_procedures": 25,
    "procedures": [
        {
            "name": "ValidaCPF",
            "signature": "PROCEDURE ValidaCPF(sCPF: string): boolean",
            "is_public": True,
            "is_local": False,
            "code_lines": 45,
            "code": "..."  # if include_code
        },
        ...
    ]
}
```

**Query pattern:**
```python
procedures = await Procedure.find({
    "element_id": element.id
}).sort("+name").to_list()
```

### PROC-02: `get_procedure`
**Purpose:** Get specific procedure by name
**Parameters:**
- `procedure_name: str` (required)
- `element_name: str | None = None` - Scope to element
- `project_name: str | None = None`

**Returns:**
```python
{
    "error": False,
    "data": {
        "name": "ValidaCPF",
        "element": "ServerProcedures",
        "signature": "PROCEDURE ValidaCPF(sCPF: string): boolean",
        "parameters": [
            {"name": "sCPF", "type": "string", "is_local": False}
        ],
        "return_type": "boolean",
        "code": "...",
        "code_lines": 45,
        "dependencies": {
            "calls_procedures": ["FormataCPF"],
            "uses_files": ["CLIENTE"],
            "uses_apis": [],
            "uses_queries": []
        }
    }
}
```

### SCHEMA-01: `get_schema`
**Purpose:** Get complete database schema for a project
**Parameters:**
- `project_name: str` (required)

**Returns:**
```python
{
    "error": False,
    "project": "Linkpay_ADM",
    "version": 26,
    "connections": [
        {
            "name": "CNX_BASE_HOMOLOG",
            "database_type": "sqlserver",
            "source": "servidor.database.net",
            "database": "LinkpayDB"
        }
    ],
    "total_tables": 45,
    "tables": [
        {
            "name": "USUARIO",
            "physical_name": "tbl_usuario",
            "column_count": 12,
            "primary_key": ["id"]
        },
        ...
    ]
}
```

**Query pattern:**
```python
project = await Project.find_one(Project.name == project_name)
schema = await DatabaseSchema.find_one({"project_id": project.id})
```

### SCHEMA-02: `get_table`
**Purpose:** Get detailed table definition
**Parameters:**
- `table_name: str` (required)
- `project_name: str` (required)

**Returns:**
```python
{
    "error": False,
    "table": {
        "name": "USUARIO",
        "physical_name": "tbl_usuario",
        "connection_name": "CNX_BASE_HOMOLOG",
        "columns": [
            {
                "name": "id",
                "python_type": "int",
                "is_primary_key": True,
                "is_auto_increment": True
            },
            {
                "name": "login",
                "python_type": "str",
                "size": 50,
                "nullable": False
            },
            ...
        ],
        "indexes": [
            {"name": "idx_login", "columns": ["login"], "is_unique": True}
        ]
    }
}
```

**Query pattern:**
```python
schema = await DatabaseSchema.find_one({"project_id": project.id})
table = next((t for t in schema.tables if t.name == table_name), None)
```

## Code Examples

Verified patterns from official sources and project codebase:

### Complete Tool File Template
```python
# src/wxcode/mcp/tools/elements.py
"""MCP tools for Element queries."""

from fastmcp import Context
from bson import DBRef

from wxcode.config import get_settings
from wxcode.mcp.server import mcp
from wxcode.models import Element, Project, ElementType, ElementLayer, ConversionStatus


async def _find_element(
    ctx: Context,
    element_name: str,
    project_name: str | None
) -> tuple[Element | None, str | None]:
    """
    Find element by name, optionally scoped to project.

    Returns:
        (element, error_message) - element is None if not found
    """
    if project_name:
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return None, f"Project '{project_name}' not found"

        # DBRef query via raw Motor
        settings = get_settings()
        mongo_client = ctx.lifespan_context["mongo_client"]
        db = mongo_client[settings.mongodb_database]
        collection = db["elements"]

        project_dbref = DBRef("projects", project.id)
        elem_dict = await collection.find_one({
            "source_name": element_name,
            "project_id": project_dbref
        })

        if not elem_dict:
            return None, f"Element '{element_name}' not found in project '{project_name}'"

        element = await Element.get(elem_dict["_id"])
        return element, None
    else:
        elements = await Element.find(Element.source_name == element_name).to_list()

        if not elements:
            return None, f"Element '{element_name}' not found"

        if len(elements) > 1:
            projects = [e.source_name for e in elements]  # Would need project lookup
            return None, f"Element '{element_name}' found in multiple projects. Use project_name to specify."

        return elements[0], None


def _serialize_element(element: Element, include_raw: bool = True) -> dict:
    """Serialize Element to JSON-safe dict."""
    data = {
        "id": str(element.id),
        "name": element.source_name,
        "type": element.source_type.value,
        "file": element.source_file,
        "layer": element.layer.value if element.layer else None,
        "topological_order": element.topological_order,
        "conversion_status": element.conversion.status.value,
    }

    if include_raw and element.raw_content:
        data["raw_content"] = element.raw_content

    if element.ast:
        data["ast"] = element.ast.model_dump(mode="json")

    if element.dependencies:
        data["dependencies"] = element.dependencies.model_dump(mode="json")

    return data


@mcp.tool
async def get_element(
    ctx: Context,
    element_name: str,
    project_name: str | None = None,
    include_raw_content: bool = True
) -> dict:
    """
    Get complete definition of a WinDev element.

    Returns source code, AST, dependencies, and conversion status.
    Use this to understand what a page, procedure group, class, or query does.

    Args:
        element_name: Name of the element (e.g., PAGE_Login, ServerProcedures)
        project_name: Optional project name to scope the search
        include_raw_content: Whether to include the full source code (default: True)

    Returns:
        Complete element definition including AST and dependencies
    """
    try:
        element, error = await _find_element(ctx, element_name, project_name)

        if error:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": error,
                "suggestion": "Use list_elements to see available elements"
            }

        return {
            "error": False,
            "data": _serialize_element(element, include_raw=include_raw_content)
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__
        }


@mcp.tool
async def list_elements(
    ctx: Context,
    project_name: str | None = None,
    element_type: str | None = None,
    layer: str | None = None,
    conversion_status: str | None = None,
    limit: int = 100
) -> dict:
    """
    List elements with optional filters.

    Use this to discover what elements exist in a project or find elements
    that need conversion.

    Args:
        project_name: Filter by project name
        element_type: Filter by type (page, procedure_group, class, query, report)
        layer: Filter by layer (schema, domain, business, api, ui)
        conversion_status: Filter by status (pending, in_progress, converted, validated)
        limit: Maximum number of results (default: 100)

    Returns:
        List of elements matching filters
    """
    try:
        query = {}

        if project_name:
            project = await Project.find_one(Project.name == project_name)
            if not project:
                return {
                    "error": True,
                    "code": "NOT_FOUND",
                    "message": f"Project '{project_name}' not found"
                }
            query["project_id.$id"] = project.id

        if element_type:
            query["source_type"] = element_type

        if layer:
            query["layer"] = layer

        if conversion_status:
            query["conversion.status"] = conversion_status

        # Count total before limit
        total = await Element.find(query).count()

        # Get limited results
        elements = await Element.find(query).limit(limit).to_list()

        return {
            "error": False,
            "total": total,
            "returned": len(elements),
            "elements": [
                {
                    "name": e.source_name,
                    "type": e.source_type.value,
                    "file": e.source_file,
                    "layer": e.layer.value if e.layer else None,
                    "conversion_status": e.conversion.status.value
                }
                for e in elements
            ]
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__
        }
```

### Tools Init Pattern
```python
# src/wxcode/mcp/tools/__init__.py
"""MCP Tools for wxcode Knowledge Base.

All tools are registered on import by using the @mcp.tool decorator.
Import this module to register all tools with the MCP server.
"""

# Import all tool modules to register them
from wxcode.mcp.tools import elements
from wxcode.mcp.tools import controls
from wxcode.mcp.tools import procedures
from wxcode.mcp.tools import schema

__all__ = ["elements", "controls", "procedures", "schema"]
```

### Server Integration
```python
# src/wxcode/mcp/server.py (updated)
# ... existing code ...

mcp = FastMCP("wxcode-kb", lifespan=app_lifespan)

# Register all tools by importing the tools package
from wxcode.mcp import tools  # noqa: F401 - import for side effects

if __name__ == "__main__":
    mcp.run()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual JSON schema | Type-hint inference | FastMCP 2.0 | No manual schema definition |
| Global DB connection | Lifespan context | FastMCP 2.0 | Proper resource lifecycle |
| Raise exceptions | Return error dicts | MCP best practices | Claude can understand errors |
| Return Pydantic | Return dicts | MCP requirement | Proper JSON serialization |

**Deprecated/outdated:**
- `@mcp.tool()` with empty parens: Can use `@mcp.tool` without parens
- Manual schema in decorator: Use type hints instead

## Open Questions

Things that couldn't be fully resolved:

1. **Token count for 9 tools**
   - What we know: Each tool definition consumes ~50-100 tokens
   - What's unclear: Exact Claude context impact with all tool docstrings
   - Recommendation: Monitor during implementation; combine tools if >15 needed

2. **Neo4j tools in Phase 5 or 6?**
   - What we know: Phase 5 is read-only, Neo4j has graph queries
   - What's unclear: Should `get_impact` (Neo4j) be Phase 5 or later?
   - Recommendation: Phase 5 focuses on MongoDB; add Neo4j tools in Phase 6

3. **Pagination for large results**
   - What we know: `limit` parameter exists
   - What's unclear: Should we add `offset` for cursor-based pagination?
   - Recommendation: Start with `limit` only; add pagination if needed

## Sources

### Primary (HIGH confidence)
- [FastMCP official docs](https://gofastmcp.com/) - tool decorator, lifespan context
- [FastMCP context](https://gofastmcp.com/servers/context) - accessing lifespan_context
- [Beanie ODM docs](https://beanie-odm.dev/) - find, find_one, aggregate patterns
- Project source: `src/wxcode/services/gsd_context_collector.py` - battle-tested query patterns
- Project source: `src/wxcode/models/` - model schemas and indexes

### Secondary (MEDIUM confidence)
- [MongoDB $regex docs](https://www.mongodb.com/docs/manual/reference/operator/query/regex/) - regex search
- Phase 4 research and verification - lifespan patterns confirmed working

### Tertiary (LOW confidence)
- Web search for MCP error handling patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - FastMCP patterns verified with Phase 4
- Architecture: HIGH - based on working gsd_context_collector.py patterns
- Query patterns: HIGH - existing Beanie usage in project
- Tool specifications: MEDIUM - detailed but untested
- Pitfalls: HIGH - learned from Phase 4 and existing code

**Research date:** 2026-01-21
**Valid until:** 2026-02-21 (30 days - tools are read-only, low change risk)
