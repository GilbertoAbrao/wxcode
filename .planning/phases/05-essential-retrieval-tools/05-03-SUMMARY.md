---
phase: 05-essential-retrieval-tools
plan: 03
subsystem: mcp-tools
tags: [mcp, tools, procedures, schema, queries]

dependency-graph:
  requires: ["05-01"]
  provides: ["procedure-tools", "schema-tools", "complete-read-tools"]
  affects: ["06"]

tech-stack:
  added: []
  patterns:
    - "Duplicate _find_element helper for parallel execution"
    - "Case-insensitive table lookup for schema queries"
    - "Ambiguous result handling with suggestions"

file-tracking:
  key-files:
    created:
      - src/wxcode/mcp/tools/procedures.py
      - src/wxcode/mcp/tools/schema.py
    modified:
      - src/wxcode/mcp/tools/__init__.py

decisions:
  - id: "proc-element-lookup"
    choice: "Fetch element name from MongoDB when not provided"
    rationale: "Procedure model only stores element_id, not element_name"
  - id: "table-case-insensitive"
    choice: "Case-insensitive table lookup using .upper()"
    rationale: "WinDev table names may vary in casing across imports"
  - id: "helper-duplication"
    choice: "Duplicate _find_element helper in procedures.py (follows controls.py pattern)"
    rationale: "Avoid import cycles and support parallel tool execution"

metrics:
  duration: "2.5 minutes"
  completed: "2026-01-22"
---

# Phase 5 Plan 3: Procedure and Schema Tools Summary

Implemented 4 MCP tools for querying WinDev procedures and database schema, completing the read-only tool suite.

## One-Liner

**Procedure inspection and schema query tools: get_procedures, get_procedure, get_schema, get_table**

## What Was Built

### Procedure Tools (`procedures.py` - 283 lines)

| Tool | Purpose | Key Features |
|------|---------|--------------|
| `get_procedures` | List all procedures in an element | Optional code inclusion, signature parsing |
| `get_procedure` | Get single procedure with full details | Ambiguous result handling, dependencies |

**Query patterns:**
- Element lookup via `_find_element` helper
- Procedure query by `element_id` for scoping
- Element name resolution when procedure found without context

### Schema Tools (`schema.py` - 202 lines)

| Tool | Purpose | Key Features |
|------|---------|--------------|
| `get_schema` | Get complete database schema | Connections, tables summary, version info |
| `get_table` | Get detailed table definition | Columns, indexes, case-insensitive lookup |

**Query patterns:**
- Project -> DatabaseSchema lookup
- Tables embedded in schema document (not separate collection)
- Case-insensitive table matching via `.upper()`

### Tools Registry Update (`__init__.py`)

All 4 modules now imported:
```python
from wxcode.mcp.tools import elements  # 3 tools
from wxcode.mcp.tools import controls  # 2 tools
from wxcode.mcp.tools import procedures  # 2 tools
from wxcode.mcp.tools import schema  # 2 tools
```

**Total: 9 tools registered**

## Commits

| Hash | Type | Description |
|------|------|-------------|
| `0c65296` | feat | Implement procedure query tools |
| `977d7de` | feat | Implement schema query tools |
| `2681f96` | chore | Register all 9 MCP tools |

## Verification Results

```
All 9 tools imported successfully
- get_element
- list_elements
- search_code
- get_controls
- get_data_bindings
- get_procedure
- get_procedures
- get_schema
- get_table

MCP server: wxcode-kb
Tools registered: 9
```

## Deviations from Plan

### Model Field Adaptations

**1. ProcedureParameter.is_optional -> is_local**
- Plan expected `is_optional` field
- Model has `is_local` field instead
- Adapted to use actual model fields

**2. SchemaColumn.windev_type -> hyperfile_type**
- Plan expected `windev_type` field
- Model has `hyperfile_type` field instead
- Adapted to use actual model fields

### Other Adaptations

**3. Controls import was missing from __init__.py**
- Previous plan (05-02) created controls.py but commit order issue left import missing
- This plan fixed by including all 4 modules in final __init__.py update

## Technical Decisions

### 1. Helper Function Duplication

Duplicated `_find_element` in `procedures.py` rather than importing from `elements.py`:

- **Reason:** Follows pattern established in `controls.py`
- **Benefit:** Avoids potential import cycles
- **Benefit:** Supports parallel tool execution without shared state

### 2. Ambiguous Procedure Handling

When procedure name exists in multiple elements:

```python
return {
    "error": True,
    "code": "AMBIGUOUS",
    "message": f"Procedure '{procedure_name}' found in multiple elements",
    "suggestion": f"Use element_name to specify. Found in: {', '.join(element_names)}"
}
```

- **Reason:** Procedures can have same name in different elements
- **Benefit:** Clear guidance for user to resolve ambiguity

### 3. Schema Table Lookup Strategy

Tables are embedded documents in DatabaseSchema, not separate collection:

```python
table = next(
    (t for t in (schema.tables or []) if t.name.upper() == table_name.upper()),
    None
)
```

- **Reason:** DatabaseSchema model stores tables as list
- **Benefit:** Single query to get schema + table

## Next Phase Readiness

### Provided to Phase 6

- Complete read-only tool suite (9 tools)
- Procedure inspection for business logic understanding
- Schema access for data model conversion planning

### Potential Issues for Phase 6

- None identified - all foundation tools complete
- Phase 6 (Dependency Navigation) can proceed with Neo4j tools

## Success Criteria Status

- [x] `src/wxcode/mcp/tools/procedures.py` exists with 2 tools (283 lines)
- [x] `src/wxcode/mcp/tools/schema.py` exists with 2 tools (202 lines)
- [x] `__init__.py` imports all 4 modules
- [x] All 9 tools have @mcp.tool decorator
- [x] All tools have proper docstrings
- [x] Server starts without errors (9 tools registered)
- [x] Tools follow consistent error handling pattern
