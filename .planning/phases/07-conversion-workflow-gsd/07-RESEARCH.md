# Phase 7: Conversion Workflow + GSD Integration - Research

**Researched:** 2026-01-22
**Domain:** Conversion state management, topological ordering, write operations, GSD templates, documentation
**Confidence:** HIGH

## Summary

Phase 7 completes the MCP Server integration by adding **conversion workflow tools** that enable tracking and managing the conversion process, plus **GSD templates** specifically designed for WinDev conversion milestones. This phase builds upon the existing infrastructure from Phases 4-6.

Key findings:
1. **Existing infrastructure supports all requirements:** MongoDB models (`Element`, `Conversion`) already have conversion status fields; `TopologicalSorter` provides ordering
2. **Conversion tools are straightforward queries:** `get_conversion_candidates` and `get_topological_order` use existing `DependencyAnalyzer` and `TopologicalSorter`
3. **Write operation requires confirmation pattern:** `mark_converted` should require explicit confirmation to prevent accidental state changes
4. **GSD templates exist but need customization:** Project has `.claude/skills/wxcode/` with CLI skills; need MCP-aware milestone templates
5. **Documentation gap:** No existing documentation explains how to use MCP Server with GSD workflow

**Primary recommendation:** Create `src/wxcode/mcp/tools/conversion.py` with 4 tools following Phase 5-6 patterns. Write operation (`mark_converted`) should include audit logging and require explicit confirmation. GSD templates go in `.claude/commands/` as custom slash commands.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastmcp | 2.14.x (`<3`) | MCP tool registration | Established in Phase 4 |
| beanie | 2.0.x | MongoDB ODM | Element, Conversion models exist |
| networkx | 3.x | Graph operations | Used by DependencyAnalyzer |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime | stdlib | Timestamps | Audit logging for write operations |
| logging | stdlib | Audit trail | Track conversion state changes |

### Existing Code to Reuse
| Module | Purpose | Reuse Strategy |
|--------|---------|----------------|
| `models/element.py` | ConversionStatus, ElementConversion | Query/update directly |
| `models/conversion.py` | Conversion document tracking | Project-level stats |
| `analyzer/topological_sorter.py` | Ordering logic | Wrap for MCP tool |
| `analyzer/dependency_analyzer.py` | Full analysis orchestration | For get_topological_order |
| `mcp/tools/elements.py` | `_find_element` helper | Copy pattern |

**Installation:**
No additional packages needed. All dependencies already in project.

## Architecture Patterns

### Recommended Project Structure
```
src/wxcode/mcp/
├── __init__.py
├── server.py
└── tools/
    ├── __init__.py
    ├── elements.py       # Phase 5
    ├── controls.py       # Phase 5
    ├── procedures.py     # Phase 5
    ├── schema.py         # Phase 5
    ├── graph.py          # Phase 6
    └── conversion.py     # NEW: 4 conversion workflow tools

.claude/
├── commands/
│   └── wx-convert/       # NEW: GSD templates for conversion
│       ├── milestone.md  # Template for /wx-convert:milestone
│       └── phase.md      # Template for /wx-convert:phase
└── skills/
    └── wxcode/        # Existing CLI skills
```

### Pattern 1: Conversion Candidates Query
**What:** Find elements ready for conversion (dependencies already converted)
**When to use:** CONV-01 tool
**Example:**
```python
# Source: Existing DependencyAnalyzer patterns + conversion status filtering
from wxcode.models import Element, Project
from wxcode.models.element import ConversionStatus

async def _get_conversion_candidates(
    ctx: Context,
    project_name: str,
    layer: str | None = None,
    limit: int = 20
) -> list[dict]:
    """
    Find elements whose dependencies are already converted.

    Logic:
    1. Get all elements with status == pending
    2. For each, check if all elements in dependencies.uses are converted
    3. Return those where all dependencies are satisfied
    """
    project = await Project.find_one(Project.name == project_name)
    if not project:
        return []

    # Query pending elements
    query = {
        "project_id.$id": project.id,
        "conversion.status": ConversionStatus.PENDING.value
    }
    if layer:
        query["layer"] = layer

    # Get all pending elements
    pending = await Element.find(query).to_list()

    # Get all converted element names for quick lookup
    converted_query = {
        "project_id.$id": project.id,
        "conversion.status": {"$in": [
            ConversionStatus.CONVERTED.value,
            ConversionStatus.VALIDATED.value
        ]}
    }
    converted_elements = await Element.find(converted_query).to_list()
    converted_names = {e.source_name for e in converted_elements}

    # Filter candidates: those whose dependencies are all converted
    candidates = []
    for elem in pending:
        if not elem.dependencies or not elem.dependencies.uses:
            # No dependencies = ready
            candidates.append(elem)
        else:
            # Check if all dependencies are converted
            deps = set(elem.dependencies.uses)
            if deps.issubset(converted_names):
                candidates.append(elem)

    # Sort by topological_order and return limited
    candidates.sort(key=lambda e: e.topological_order or 999999)
    return candidates[:limit]
```

### Pattern 2: Topological Order with NetworkX
**What:** Get conversion order from dependency graph
**When to use:** CONV-02 tool
**Example:**
```python
# Source: DependencyAnalyzer + TopologicalSorter patterns
from wxcode.analyzer.dependency_analyzer import DependencyAnalyzer
from wxcode.models import Project

@mcp.tool
async def get_topological_order(
    ctx: Context,
    project_name: str,
    layer: str | None = None,
    include_converted: bool = False
) -> dict:
    """
    Get recommended conversion order based on dependencies.
    """
    project = await Project.find_one(Project.name == project_name)
    if not project:
        return {"error": True, "code": "NOT_FOUND", "message": "Project not found"}

    analyzer = DependencyAnalyzer(project.id)
    result = await analyzer.analyze(persist=False)  # Don't persist, just compute

    # Get order (already sorted by layers + dependencies)
    order = result.topological_order

    # Get layers for grouping
    layers = result.layers

    # Filter if layer specified
    if layer:
        order = [node_id for node_id in order if node_id in layers.get(layer, [])]

    # Filter out converted if requested
    if not include_converted:
        # Need to check conversion status for each
        converted_names = set()
        elements = await Element.find({
            "project_id.$id": project.id,
            "conversion.status": {"$in": ["converted", "validated"]}
        }).to_list()
        converted_names = {e.source_name for e in elements}

        # Filter order - node_id format is "type:name", extract name
        def extract_name(node_id: str) -> str:
            return node_id.split(":", 1)[1] if ":" in node_id else node_id

        order = [n for n in order if extract_name(n) not in converted_names]

    return {
        "error": False,
        "data": {
            "project": project_name,
            "total_elements": len(order),
            "layer_filter": layer,
            "include_converted": include_converted,
            "order": order,
            "by_layer": layers
        }
    }
```

### Pattern 3: Write Operation with Confirmation
**What:** Require explicit confirmation for state mutations
**When to use:** CONV-03 tool (mark_converted)
**Example:**
```python
# Source: MCP best practices for write operations
import logging
from datetime import datetime

audit_logger = logging.getLogger("wxcode.mcp.audit")

@mcp.tool
async def mark_converted(
    ctx: Context,
    element_name: str,
    project_name: str,
    confirm: bool = False,
    notes: str | None = None
) -> dict:
    """
    Mark an element as converted.

    IMPORTANT: This is a write operation that changes element state.
    Set confirm=True to actually execute the change.

    Args:
        element_name: Name of the element to mark
        project_name: Project containing the element
        confirm: Must be True to execute (safety check)
        notes: Optional notes about the conversion

    Returns:
        Confirmation request (if confirm=False) or result
    """
    # Find element (reuse _find_element pattern)
    element, error = await _find_element(ctx, element_name, project_name)
    if error:
        return {"error": True, "code": "NOT_FOUND", "message": error}

    # Check current status
    current_status = element.conversion.status.value

    if not confirm:
        # Return preview of what would happen
        return {
            "error": False,
            "action": "mark_converted",
            "requires_confirmation": True,
            "preview": {
                "element": element_name,
                "project": project_name,
                "current_status": current_status,
                "new_status": "converted",
                "will_set_converted_at": True
            },
            "instruction": "Set confirm=True to execute this change"
        }

    # Execute the change
    old_status = current_status
    element.conversion.status = ConversionStatus.CONVERTED
    element.conversion.converted_at = datetime.utcnow()
    if notes:
        element.conversion.issues.append(f"[{datetime.utcnow().isoformat()}] {notes}")

    await element.save()

    # Audit log
    audit_logger.info(
        f"mark_converted: {project_name}/{element_name} "
        f"status changed from {old_status} to converted"
    )

    return {
        "error": False,
        "action": "mark_converted",
        "executed": True,
        "data": {
            "element": element_name,
            "project": project_name,
            "previous_status": old_status,
            "new_status": "converted",
            "converted_at": element.conversion.converted_at.isoformat(),
            "notes": notes
        }
    }
```

### Pattern 4: Conversion Statistics Aggregation
**What:** Aggregate conversion progress across elements
**When to use:** CONV-04 tool
**Example:**
```python
# Source: MongoDB aggregation patterns
@mcp.tool
async def get_conversion_stats(
    ctx: Context,
    project_name: str
) -> dict:
    """
    Get conversion progress statistics for a project.
    """
    project = await Project.find_one(Project.name == project_name)
    if not project:
        return {"error": True, "code": "NOT_FOUND", "message": "Project not found"}

    # Use aggregation pipeline for efficiency
    from wxcode.config import get_settings
    settings = get_settings()
    mongo_client = ctx.request_context.lifespan_context["mongo_client"]
    db = mongo_client[settings.mongodb_database]
    collection = db["elements"]

    from bson import DBRef
    project_dbref = DBRef("projects", project.id)

    pipeline = [
        {"$match": {"project_id": project_dbref}},
        {"$group": {
            "_id": "$conversion.status",
            "count": {"$sum": 1}
        }}
    ]

    cursor = collection.aggregate(pipeline)
    status_counts = {doc["_id"]: doc["count"] async for doc in cursor}

    # Also get by layer
    layer_pipeline = [
        {"$match": {"project_id": project_dbref}},
        {"$group": {
            "_id": {"layer": "$layer", "status": "$conversion.status"},
            "count": {"$sum": 1}
        }}
    ]

    cursor = collection.aggregate(layer_pipeline)
    layer_stats = {}
    async for doc in cursor:
        layer = doc["_id"]["layer"] or "unknown"
        status = doc["_id"]["status"]
        if layer not in layer_stats:
            layer_stats[layer] = {}
        layer_stats[layer][status] = doc["count"]

    # Calculate totals
    total = sum(status_counts.values())
    converted = status_counts.get("converted", 0) + status_counts.get("validated", 0)
    pending = status_counts.get("pending", 0)
    in_progress = status_counts.get("in_progress", 0)

    return {
        "error": False,
        "data": {
            "project": project_name,
            "total_elements": total,
            "converted": converted,
            "pending": pending,
            "in_progress": in_progress,
            "progress_percentage": round((converted / total * 100) if total > 0 else 0, 1),
            "by_status": status_counts,
            "by_layer": layer_stats
        }
    }
```

### Anti-Patterns to Avoid
- **Write without confirmation:** Never mutate state without explicit `confirm=True`
- **Skipping audit logging:** All writes must be logged for traceability
- **Large result sets:** Always use `limit` parameter for list operations
- **Blocking graph analysis:** Use `persist=False` when just reading order
- **Hardcoded status values:** Use `ConversionStatus` enum consistently

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Topological sorting | Custom algorithm | `TopologicalSorter` | Handles cycles, layers, edge cases |
| Dependency analysis | Manual graph building | `DependencyAnalyzer` | Production-tested, handles all element types |
| Element lookup | Simple query | `_find_element` pattern | Handles DBRef, multi-project ambiguity |
| Conversion status enum | String constants | `ConversionStatus` | Type safety, IDE support |
| Progress calculation | Manual counting | MongoDB aggregation | Efficient for large projects |

**Key insight:** The conversion workflow tools are thin wrappers around existing functionality. `DependencyAnalyzer` and `TopologicalSorter` do the heavy lifting.

## Common Pitfalls

### Pitfall 1: Accidental Status Change
**What goes wrong:** Element marked converted without user intent
**Why it happens:** Write operation executed without confirmation
**How to avoid:** Require `confirm=True` parameter; return preview if not set
**Warning signs:** Users report unexpected status changes

### Pitfall 2: Stale Topological Order
**What goes wrong:** Order doesn't reflect recent dependency changes
**Why it happens:** Using cached order from MongoDB instead of fresh computation
**How to avoid:** Call `analyze(persist=False)` for fresh order; persist=True only for explicit re-analysis
**Warning signs:** Circular dependency errors, wrong conversion order

### Pitfall 3: Missing Audit Trail
**What goes wrong:** Cannot trace who/when changed conversion status
**Why it happens:** No logging for write operations
**How to avoid:** Log all `mark_converted` calls with timestamp, user context, before/after
**Warning signs:** Debugging conversion issues impossible

### Pitfall 4: Layer Confusion
**What goes wrong:** Wrong elements returned for a layer filter
**Why it happens:** `TopologicalSorter` uses different layer values than `Element.layer`
**How to avoid:** Verify layer values match; use `ElementLayer` enum
**Warning signs:** Empty results, unexpected elements

### Pitfall 5: Performance with Large Projects
**What goes wrong:** `get_conversion_candidates` times out on large projects
**Why it happens:** Loading all pending elements, then checking each
**How to avoid:** Use MongoDB aggregation for candidates; index conversion.status
**Warning signs:** Slow responses, memory issues

### Pitfall 6: GSD Template Not Found
**What goes wrong:** Custom slash command doesn't work
**Why it happens:** Template file in wrong location or format
**How to avoid:** Templates go in `.claude/commands/<name>/` as markdown files
**Warning signs:** "Command not found" in Claude Code

## GSD Integration Patterns

### GSD-01: Conversion Milestone Template

**Location:** `.claude/commands/wx-convert/milestone.md`

**Purpose:** Orchestrate conversion of a WinDev module as a GSD milestone

**Template Structure:**
```markdown
# WinDev Conversion Milestone: {{module_name}}

## Context
- Project: {{project_name}}
- Module: {{module_name}}
- Target Stack: FastAPI + Jinja2 + HTMX

## Objective
Convert all elements in {{module_name}} to the target stack,
following topological order to respect dependencies.

## Prerequisites
1. Project imported: `wxcode import` completed
2. Analysis done: `wxcode analyze` and `wxcode sync-neo4j` completed
3. MCP Server running: `python -m wxcode.mcp.server`

## Workflow

### Phase 1: Discovery
Use MCP tools to understand scope:
- `get_conversion_stats` - Current progress
- `get_topological_order` - Recommended order
- `get_conversion_candidates` - Elements ready now

### Phase 2: Conversion Phases
For each element in topological order:
1. Get element details: `get_element`
2. Get controls: `get_controls`
3. Get procedures: `get_procedures`
4. Convert using generator patterns
5. Mark complete: `mark_converted` with confirm=True

### Phase 3: Validation
- Check `get_conversion_stats` for 100% completion
- Run validation tests
- Generate final output

## Success Criteria
- [ ] All elements in module have status "converted" or "validated"
- [ ] Generated code passes syntax validation
- [ ] Integration tests pass
```

### GSD-02: Phase Template with KB Query

**Location:** `.claude/commands/wx-convert/phase.md`

**Purpose:** Convert a single element with KB-powered context

**Template Structure:**
```markdown
# Convert Element: {{element_name}}

## Context from Knowledge Base

### Element Definition
Use `get_element(element_name="{{element_name}}", project_name="{{project_name}}")`
to retrieve:
- Raw WLanguage source code
- Parsed AST (procedures, variables, events)
- Dependencies (uses, used_by, data_files)
- Current conversion status

### UI Structure
Use `get_controls(element_name="{{element_name}}", project_name="{{project_name}}")`
to retrieve:
- Control hierarchy (name, type, full_path)
- Events with code
- Data bindings (table.field mappings)
- Properties (visual configuration)

### Business Logic
Use `get_procedures(element_name="{{element_name}}", project_name="{{project_name}}")`
to retrieve:
- Local procedures (is_local=True)
- Signatures (parameters, return types)
- Code bodies

### Data Dependencies
Use `get_schema(project_name="{{project_name}}")` and `get_table` for:
- Table definitions
- Column types (mapped to Python)
- Relationships

## Conversion Tasks

### Task 1: Generate Pydantic Models
Based on data_bindings and schema, create models for:
- Request validation
- Response serialization
- Database mapping

### Task 2: Generate FastAPI Route
Based on element type and events:
- Route handler for GET/POST
- Form handling (if UI element)
- Business logic from procedures

### Task 3: Generate Jinja2 Template
Based on controls:
- HTML structure matching control hierarchy
- HTMX attributes for interactivity
- Alpine.js for client-side logic

### Task 4: Mark Complete
Call `mark_converted(element_name="{{element_name}}", project_name="{{project_name}}", confirm=True)`

## Verification
- [ ] Route returns 200
- [ ] Template renders without errors
- [ ] Data bindings work
```

### GSD-03: Documentation Structure

**Location:** `docs/mcp-gsd-integration.md`

**Content Sections:**
1. **Overview:** What the MCP Server provides, how it connects to GSD
2. **Setup:** Starting MCP Server, configuring `.mcp.json`
3. **Tool Reference:** All tools with examples
4. **Workflow Examples:** Step-by-step conversion using tools
5. **Troubleshooting:** Common issues and solutions

## Tool Specifications

### CONV-01: `get_conversion_candidates`
**Purpose:** Get elements ready for conversion (dependencies satisfied)
**Parameters:**
- `project_name: str` (required) - Project name
- `layer: str | None = None` - Filter by layer (schema, domain, business, api, ui)
- `limit: int = 20` - Maximum results

**Returns:**
```python
{
    "error": False,
    "data": {
        "project": "Linkpay_ADM",
        "candidates_count": 5,
        "layer_filter": "ui",
        "candidates": [
            {
                "name": "PAGE_Login",
                "type": "page",
                "layer": "ui",
                "topological_order": 15,
                "dependencies_satisfied": True
            }
        ]
    }
}
```

### CONV-02: `get_topological_order`
**Purpose:** Get recommended conversion order
**Parameters:**
- `project_name: str` (required) - Project name
- `layer: str | None = None` - Filter by layer
- `include_converted: bool = False` - Include already converted elements

**Returns:**
```python
{
    "error": False,
    "data": {
        "project": "Linkpay_ADM",
        "total_elements": 150,
        "layer_filter": None,
        "include_converted": False,
        "order": [
            "table:USUARIO",
            "class:classUsuario",
            "proc:ValidaCPF",
            "page:PAGE_Login"
        ],
        "by_layer": {
            "schema": ["table:USUARIO", "table:CLIENTE"],
            "domain": ["class:classUsuario"],
            "business": ["proc:ValidaCPF"],
            "ui": ["page:PAGE_Login"]
        }
    }
}
```

### CONV-03: `mark_converted`
**Purpose:** Mark element as converted (WRITE OPERATION)
**Parameters:**
- `element_name: str` (required) - Element name
- `project_name: str` (required) - Project name
- `confirm: bool = False` (required for execution) - Safety confirmation
- `notes: str | None = None` - Optional conversion notes

**Returns (confirm=False):**
```python
{
    "error": False,
    "action": "mark_converted",
    "requires_confirmation": True,
    "preview": {
        "element": "PAGE_Login",
        "project": "Linkpay_ADM",
        "current_status": "pending",
        "new_status": "converted"
    },
    "instruction": "Set confirm=True to execute this change"
}
```

**Returns (confirm=True):**
```python
{
    "error": False,
    "action": "mark_converted",
    "executed": True,
    "data": {
        "element": "PAGE_Login",
        "project": "Linkpay_ADM",
        "previous_status": "pending",
        "new_status": "converted",
        "converted_at": "2026-01-22T15:30:00Z",
        "notes": "Converted using route-generator"
    }
}
```

### CONV-04: `get_conversion_stats`
**Purpose:** Get conversion progress statistics
**Parameters:**
- `project_name: str` (required) - Project name

**Returns:**
```python
{
    "error": False,
    "data": {
        "project": "Linkpay_ADM",
        "total_elements": 250,
        "converted": 45,
        "pending": 180,
        "in_progress": 25,
        "progress_percentage": 18.0,
        "by_status": {
            "pending": 180,
            "in_progress": 25,
            "converted": 40,
            "validated": 5
        },
        "by_layer": {
            "schema": {"converted": 20, "pending": 5},
            "domain": {"converted": 10, "pending": 15},
            "business": {"converted": 10, "pending": 80},
            "ui": {"converted": 5, "pending": 80, "in_progress": 25}
        }
    }
}
```

## Code Examples

### Complete Conversion Tools File
```python
# src/wxcode/mcp/tools/conversion.py
"""MCP tools for conversion workflow management.

Provides tools to track conversion progress, get conversion order,
and mark elements as converted. Includes one write operation (mark_converted)
which requires explicit confirmation.
"""

import logging
from datetime import datetime
from typing import Any

from bson import DBRef
from fastmcp import Context

from wxcode.analyzer.dependency_analyzer import DependencyAnalyzer
from wxcode.config import get_settings
from wxcode.mcp.server import mcp
from wxcode.models import Element, Project
from wxcode.models.element import ConversionStatus

# Audit logger for write operations
audit_logger = logging.getLogger("wxcode.mcp.audit")


async def _find_element(
    ctx: Context,
    element_name: str,
    project_name: str,
) -> tuple[Element | None, str | None]:
    """
    Find element by name in project (duplicated for parallel execution).
    """
    project = await Project.find_one(Project.name == project_name)
    if not project:
        return None, f"Project '{project_name}' not found"

    settings = get_settings()
    mongo_client = ctx.request_context.lifespan_context["mongo_client"]
    db = mongo_client[settings.mongodb_database]
    collection = db["elements"]

    project_dbref = DBRef("projects", project.id)
    elem_dict = await collection.find_one({
        "source_name": element_name,
        "project_id": project_dbref,
    })

    if not elem_dict:
        return None, f"Element '{element_name}' not found in project '{project_name}'"

    element = await Element.get(elem_dict["_id"])
    return element, None


@mcp.tool
async def get_conversion_candidates(
    ctx: Context,
    project_name: str,
    layer: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Get elements ready for conversion (dependencies already converted).

    Returns elements whose dependency prerequisites are satisfied,
    sorted by topological order for optimal conversion sequence.

    Args:
        project_name: Name of the project
        layer: Optional layer filter (schema, domain, business, api, ui)
        limit: Maximum candidates to return (default: 20)

    Returns:
        List of conversion candidates with metadata
    """
    try:
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Project '{project_name}' not found",
            }

        # Get pending elements
        query: dict[str, Any] = {
            "project_id.$id": project.id,
            "conversion.status": ConversionStatus.PENDING.value,
        }
        if layer:
            query["layer"] = layer

        pending = await Element.find(query).to_list()

        # Get converted element names
        converted_query = {
            "project_id.$id": project.id,
            "conversion.status": {"$in": [
                ConversionStatus.CONVERTED.value,
                ConversionStatus.VALIDATED.value,
            ]},
        }
        converted_elements = await Element.find(converted_query).to_list()
        converted_names = {e.source_name for e in converted_elements}

        # Filter candidates
        candidates = []
        for elem in pending:
            if not elem.dependencies or not elem.dependencies.uses:
                candidates.append(elem)
            else:
                deps = set(elem.dependencies.uses)
                if deps.issubset(converted_names):
                    candidates.append(elem)

        # Sort by topological order
        candidates.sort(key=lambda e: e.topological_order or 999999)
        candidates = candidates[:limit]

        return {
            "error": False,
            "data": {
                "project": project_name,
                "candidates_count": len(candidates),
                "layer_filter": layer,
                "candidates": [
                    {
                        "name": c.source_name,
                        "type": c.source_type.value,
                        "layer": c.layer.value if c.layer else None,
                        "topological_order": c.topological_order,
                        "dependencies_satisfied": True,
                    }
                    for c in candidates
                ],
            },
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def get_topological_order(
    ctx: Context,
    project_name: str,
    layer: str | None = None,
    include_converted: bool = False,
) -> dict[str, Any]:
    """
    Get recommended conversion order based on dependencies.

    Returns elements sorted by topological order (dependencies first),
    respecting layer hierarchy (schema -> domain -> business -> api -> ui).

    Args:
        project_name: Name of the project
        layer: Optional layer filter
        include_converted: Include already converted elements (default: False)

    Returns:
        Ordered list of elements with layer grouping
    """
    try:
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Project '{project_name}' not found",
            }

        # Build dependency graph
        analyzer = DependencyAnalyzer(project.id)
        result = await analyzer.analyze(persist=False)

        order = result.topological_order
        layers = result.layers

        # Filter by layer if specified
        if layer:
            layer_nodes = layers.get(layer, [])
            order = [n for n in order if n in layer_nodes]

        # Filter out converted if requested
        if not include_converted:
            converted_elements = await Element.find({
                "project_id.$id": project.id,
                "conversion.status": {"$in": ["converted", "validated"]},
            }).to_list()
            converted_names = {e.source_name for e in converted_elements}

            def extract_name(node_id: str) -> str:
                return node_id.split(":", 1)[1] if ":" in node_id else node_id

            order = [n for n in order if extract_name(n) not in converted_names]

        return {
            "error": False,
            "data": {
                "project": project_name,
                "total_elements": len(order),
                "layer_filter": layer,
                "include_converted": include_converted,
                "order": order,
                "by_layer": layers,
            },
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def mark_converted(
    ctx: Context,
    element_name: str,
    project_name: str,
    confirm: bool = False,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Mark an element as converted (WRITE OPERATION).

    This changes element state in the database. Requires confirm=True
    to execute - returns a preview if confirm is False.

    Args:
        element_name: Name of the element to mark
        project_name: Project containing the element
        confirm: Must be True to execute (safety check)
        notes: Optional notes about the conversion

    Returns:
        Preview (if confirm=False) or execution result
    """
    try:
        element, error = await _find_element(ctx, element_name, project_name)
        if error:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": error,
            }

        current_status = element.conversion.status.value

        if not confirm:
            return {
                "error": False,
                "action": "mark_converted",
                "requires_confirmation": True,
                "preview": {
                    "element": element_name,
                    "project": project_name,
                    "current_status": current_status,
                    "new_status": "converted",
                    "will_set_converted_at": True,
                },
                "instruction": "Set confirm=True to execute this change",
            }

        # Execute the change
        old_status = current_status
        element.conversion.status = ConversionStatus.CONVERTED
        element.conversion.converted_at = datetime.utcnow()
        if notes:
            element.conversion.issues.append(
                f"[{datetime.utcnow().isoformat()}] {notes}"
            )

        await element.save()

        # Audit log
        audit_logger.info(
            f"mark_converted: {project_name}/{element_name} "
            f"status changed from {old_status} to converted"
        )

        return {
            "error": False,
            "action": "mark_converted",
            "executed": True,
            "data": {
                "element": element_name,
                "project": project_name,
                "previous_status": old_status,
                "new_status": "converted",
                "converted_at": element.conversion.converted_at.isoformat(),
                "notes": notes,
            },
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def get_conversion_stats(
    ctx: Context,
    project_name: str,
) -> dict[str, Any]:
    """
    Get conversion progress statistics for a project.

    Returns element counts by status and layer, plus overall
    progress percentage.

    Args:
        project_name: Name of the project

    Returns:
        Statistics including total, converted, pending, by_status, by_layer
    """
    try:
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Project '{project_name}' not found",
            }

        settings = get_settings()
        mongo_client = ctx.request_context.lifespan_context["mongo_client"]
        db = mongo_client[settings.mongodb_database]
        collection = db["elements"]

        project_dbref = DBRef("projects", project.id)

        # Aggregate by status
        pipeline = [
            {"$match": {"project_id": project_dbref}},
            {"$group": {"_id": "$conversion.status", "count": {"$sum": 1}}},
        ]
        cursor = collection.aggregate(pipeline)
        status_counts = {doc["_id"]: doc["count"] async for doc in cursor}

        # Aggregate by layer and status
        layer_pipeline = [
            {"$match": {"project_id": project_dbref}},
            {
                "$group": {
                    "_id": {"layer": "$layer", "status": "$conversion.status"},
                    "count": {"$sum": 1},
                }
            },
        ]
        cursor = collection.aggregate(layer_pipeline)
        layer_stats: dict[str, dict[str, int]] = {}
        async for doc in cursor:
            layer = doc["_id"]["layer"] or "unknown"
            status = doc["_id"]["status"]
            if layer not in layer_stats:
                layer_stats[layer] = {}
            layer_stats[layer][status] = doc["count"]

        # Calculate totals
        total = sum(status_counts.values())
        converted = status_counts.get("converted", 0) + status_counts.get("validated", 0)
        pending = status_counts.get("pending", 0)
        in_progress = status_counts.get("in_progress", 0)

        return {
            "error": False,
            "data": {
                "project": project_name,
                "total_elements": total,
                "converted": converted,
                "pending": pending,
                "in_progress": in_progress,
                "progress_percentage": round((converted / total * 100) if total > 0 else 0, 1),
                "by_status": status_counts,
                "by_layer": layer_stats,
            },
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }
```

### Tools Init Update
```python
# src/wxcode/mcp/tools/__init__.py (updated)
"""MCP Tools for wxcode Knowledge Base.

All tools are registered on import by using the @mcp.tool decorator.
Import this module to register all tools with the MCP server.

Tools available:
- elements: get_element, list_elements, search_code
- controls: get_controls, get_data_bindings
- procedures: get_procedures, get_procedure
- schema: get_schema, get_table
- graph: get_dependencies, get_impact, get_path, find_hubs, find_dead_code, find_cycles
- conversion: get_conversion_candidates, get_topological_order, mark_converted, get_conversion_stats
"""

# Import all tool modules to register them with @mcp.tool
from wxcode.mcp.tools import elements  # noqa: F401
from wxcode.mcp.tools import controls  # noqa: F401
from wxcode.mcp.tools import procedures  # noqa: F401
from wxcode.mcp.tools import schema  # noqa: F401
from wxcode.mcp.tools import graph  # noqa: F401
from wxcode.mcp.tools import conversion  # noqa: F401

__all__ = ["elements", "controls", "procedures", "schema", "graph", "conversion"]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual status tracking | `mark_converted` tool | Phase 7 | Automated, audited state changes |
| CLI for order | `get_topological_order` tool | Phase 7 | Order available during planning |
| Manual candidate finding | `get_conversion_candidates` tool | Phase 7 | Automated dependency checking |
| Scattered progress checks | `get_conversion_stats` tool | Phase 7 | Single source of truth |

**Deprecated/outdated:**
- Direct MongoDB updates without confirmation: Use `mark_converted` with confirm=True
- CLI-only ordering: MCP tools now available

## Open Questions

Things that couldn't be fully resolved:

1. **Undo for mark_converted**
   - What we know: Tool changes state permanently
   - What's unclear: Should there be a `mark_pending` to undo?
   - Recommendation: Start without undo; add if users request

2. **Batch mark_converted**
   - What we know: Tool marks one element at a time
   - What's unclear: Should there be batch operation for efficiency?
   - Recommendation: Start with single element; batch adds complexity

3. **GSD Template Location**
   - What we know: `.claude/commands/` for custom commands, `.claude/skills/` for skills
   - What's unclear: Best location for MCP-aware templates
   - Recommendation: Use `.claude/commands/wx-convert/` for conversion-specific commands

4. **Audit Log Persistence**
   - What we know: Using Python logging for audit
   - What's unclear: Should audit be persisted to MongoDB?
   - Recommendation: Start with file logging; add DB audit if needed for compliance

## Sources

### Primary (HIGH confidence)
- Project source: `src/wxcode/models/element.py` - ConversionStatus, ElementConversion
- Project source: `src/wxcode/models/conversion.py` - Conversion tracking
- Project source: `src/wxcode/analyzer/topological_sorter.py` - Ordering logic
- Project source: `src/wxcode/analyzer/dependency_analyzer.py` - Graph analysis
- Project source: `src/wxcode/mcp/tools/elements.py` - _find_element pattern
- Phase 5-6 research - Established tool patterns

### Secondary (MEDIUM confidence)
- Project source: `.claude/skills/wxcode/` - Existing skill structure
- MCP documentation - Write operation patterns

### Tertiary (LOW confidence)
- GSD template format - Based on project observation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - reuses existing modules
- Architecture: HIGH - follows Phase 5-6 patterns exactly
- Conversion tools: HIGH - thin wrappers around existing code
- GSD templates: MEDIUM - template structure clear, exact format needs validation
- Audit logging: MEDIUM - pattern clear, persistence strategy TBD

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - conversion workflow is stable domain)
