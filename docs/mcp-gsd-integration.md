# MCP Server + GSD Integration Guide

This document explains how to use the wxcode MCP Server with the GSD (Get Stuff Done) workflow for systematic WinDev project conversion.

## Overview

### What the MCP Server Provides

The wxcode MCP Server exposes 19 tools that provide structured access to the project Knowledge Base:

| Category | Tools | Purpose |
|----------|-------|---------|
| Elements | 3 | Query element definitions, search code |
| Controls | 2 | Access UI structure, data bindings |
| Procedures | 2 | Retrieve business logic |
| Schema | 2 | Query database structure |
| Graph | 6 | Dependency analysis, impact assessment |
| Conversion | 4 | Track and manage conversion progress |

### How It Connects to GSD

The GSD workflow uses MCP tools to:

1. **Discover** conversion scope and order using graph analysis tools
2. **Gather context** for each element using element/control/procedure tools
3. **Track progress** using conversion tools to manage state
4. **Validate** completion using stats and candidate tools

### Benefits of MCP-Powered Conversion

- **Single source of truth:** All project data accessible through MCP tools
- **Structured workflow:** Templates guide consistent conversion process
- **Progress tracking:** Real-time visibility into conversion status
- **Dependency awareness:** Topological ordering ensures correct conversion sequence
- **Audit trail:** Write operations logged for traceability

## Setup

### Starting the MCP Server

The MCP Server runs as a stdio-based server compatible with Claude Code:

```bash
# From project root
python -m wxcode.mcp.server
```

Requirements:
- Python 3.11+
- MongoDB running with project data imported
- Neo4j running (optional, for graph analysis tools)

### Configuring Claude Code

Add to your project `.mcp.json`:

```json
{
  "mcpServers": {
    "wxcode": {
      "command": "python",
      "args": ["-m", "wxcode.mcp.server"],
      "cwd": "/path/to/wxcode",
      "env": {
        "PYTHONPATH": "/path/to/wxcode/src"
      }
    }
  }
}
```

Replace `/path/to/wxcode` with your actual project path.

### Verifying Connection

After configuring, Claude Code should show the wxcode tools available. You can verify by asking Claude to call:

```
get_conversion_stats(project_name="YourProject")
```

If successful, you'll see project statistics. If it fails, check:
- MongoDB is running and accessible
- Project was imported with `wxcode import`
- PYTHONPATH is set correctly in .mcp.json

## Tool Reference

### Element Tools

#### get_element

Retrieve complete element definition including AST, dependencies, and raw content.

**Parameters:**
- `element_name` (required): Name of the element (e.g., "PAGE_Login")
- `project_name` (optional): Project name to scope the search

**Returns:**
- `source_name`, `source_type`, `source_file`
- `raw_content`: Original WLanguage source code
- `ast`: Parsed procedures, variables, events, queries
- `dependencies`: uses, used_by, data_files, external_apis
- `conversion`: Current conversion status and metadata

**Example:**
```
get_element(element_name="PAGE_Login", project_name="Linkpay_ADM")
```

#### list_elements

List all elements in a project with optional filtering.

**Parameters:**
- `project_name` (required): Project name
- `source_type` (optional): Filter by type (page, procedure, class, query, report)
- `layer` (optional): Filter by layer (schema, domain, business, api, ui)
- `limit` (optional): Maximum results (default: 100)

**Returns:**
- List of elements with basic metadata (name, type, file, layer, status)

**Example:**
```
list_elements(project_name="Linkpay_ADM", source_type="page", limit=20)
```

#### search_code

Search for patterns in element raw_content and AST.

**Parameters:**
- `pattern` (required): Search pattern (regex supported)
- `project_name` (optional): Scope to specific project
- `limit` (optional): Maximum results (default: 50)

**Returns:**
- List of matching elements with match context

**Example:**
```
search_code(pattern="HReadSeek.*USUARIO", project_name="Linkpay_ADM")
```

### Control Tools

#### get_controls

Retrieve UI control hierarchy for an element.

**Parameters:**
- `element_name` (required): Element name
- `project_name` (optional): Project name

**Returns:**
- `controls`: List of controls with:
  - `name`, `type_name`, `full_path`
  - `events`: List of event handlers with code
  - `data_bindings`: Table.field mappings
  - `properties`: Visual configuration

**Example:**
```
get_controls(element_name="PAGE_Login", project_name="Linkpay_ADM")
```

#### get_data_bindings

Get all data bindings for an element's controls.

**Parameters:**
- `element_name` (required): Element name
- `project_name` (optional): Project name

**Returns:**
- List of bindings with control_name, table_name, field_name

**Example:**
```
get_data_bindings(element_name="PAGE_Login", project_name="Linkpay_ADM")
```

### Procedure Tools

#### get_procedures

List procedures associated with an element.

**Parameters:**
- `element_name` (required): Element name
- `project_name` (optional): Project name
- `include_code` (optional): Include procedure code (default: False)

**Returns:**
- `procedures`: List with name, source_element, is_local, parameters, return_type

**Example:**
```
get_procedures(element_name="PAGE_Login", project_name="Linkpay_ADM", include_code=True)
```

#### get_procedure

Get a specific procedure by name.

**Parameters:**
- `procedure_name` (required): Procedure name
- `project_name` (optional): Project name

**Returns:**
- Single procedure with full details including code

**Example:**
```
get_procedure(procedure_name="ValidaCPF", project_name="Linkpay_ADM")
```

### Schema Tools

#### get_schema

Get database schema overview for a project.

**Parameters:**
- `project_name` (required): Project name

**Returns:**
- `tables`: List of tables with name, column_count, primary_key
- `relationships`: Foreign key relationships
- `total_columns`: Total column count across all tables

**Example:**
```
get_schema(project_name="Linkpay_ADM")
```

#### get_table

Get detailed table definition.

**Parameters:**
- `table_name` (required): Table name
- `project_name` (required): Project name

**Returns:**
- `columns`: List with name, data_type, nullable, default_value
- `primary_key`: Primary key column(s)
- `foreign_keys`: Relationships
- `indexes`: Index definitions

**Example:**
```
get_table(table_name="USUARIO", project_name="Linkpay_ADM")
```

### Graph Tools

#### get_dependencies

Get direct dependencies of an element.

**Parameters:**
- `element_name` (required): Element name
- `project_name` (required): Project name
- `direction` (optional): "outgoing" (uses), "incoming" (used_by), or "both" (default)

**Returns:**
- `outgoing`: Elements this depends on
- `incoming`: Elements that depend on this
- `data_files`: Tables accessed

**Example:**
```
get_dependencies(element_name="PAGE_Login", project_name="Linkpay_ADM", direction="both")
```

#### get_impact

Analyze impact of changing an element.

**Parameters:**
- `element_name` (required): Element name
- `project_name` (required): Project name
- `depth` (optional): How many levels to traverse (default: 2)

**Returns:**
- `direct_impact`: Immediately affected elements
- `indirect_impact`: Transitively affected elements
- `total_affected`: Count of all affected elements

**Example:**
```
get_impact(element_name="classUsuario", project_name="Linkpay_ADM", depth=3)
```

#### get_path

Find dependency path between two elements.

**Parameters:**
- `from_element` (required): Source element name
- `to_element` (required): Target element name
- `project_name` (required): Project name

**Returns:**
- `path`: List of elements forming shortest path
- `path_length`: Number of hops
- `path_found`: Boolean indicating if path exists

**Example:**
```
get_path(from_element="PAGE_Login", to_element="TABLE:USUARIO", project_name="Linkpay_ADM")
```

#### find_hubs

Find elements with many connections (potential refactoring targets).

**Parameters:**
- `project_name` (required): Project name
- `min_connections` (optional): Minimum connection count (default: 5)
- `limit` (optional): Maximum results (default: 20)

**Returns:**
- List of hub elements with incoming/outgoing counts

**Example:**
```
find_hubs(project_name="Linkpay_ADM", min_connections=10)
```

#### find_dead_code

Find potentially unused code (no incoming dependencies).

**Parameters:**
- `project_name` (required): Project name
- `layer` (optional): Filter by layer

**Returns:**
- List of elements with no incoming dependencies

**Example:**
```
find_dead_code(project_name="Linkpay_ADM", layer="business")
```

#### find_cycles

Detect circular dependencies in the project.

**Parameters:**
- `project_name` (required): Project name
- `limit` (optional): Maximum cycles to return (default: 10)

**Returns:**
- `cycles`: List of circular dependency chains
- `cycles_count`: Total number of cycles found

**Example:**
```
find_cycles(project_name="Linkpay_ADM")
```

### Conversion Tools

#### get_conversion_stats

Get conversion progress statistics.

**Parameters:**
- `project_name` (required): Project name

**Returns:**
- `total_elements`: Total element count
- `completed`: Converted + validated count
- `progress_percentage`: Completion percentage
- `by_status`: Breakdown by conversion status
- `by_layer`: Breakdown by layer and status

**Example:**
```
get_conversion_stats(project_name="Linkpay_ADM")
```

#### get_topological_order

Get recommended conversion order based on dependencies.

**Parameters:**
- `project_name` (required): Project name
- `layer` (optional): Filter by layer
- `include_converted` (optional): Include already converted (default: False)

**Returns:**
- `order`: List of elements in dependency order
- `by_layer`: Grouped by layer
- `total_nodes`: Total node count

**Example:**
```
get_topological_order(project_name="Linkpay_ADM", layer="ui")
```

#### get_conversion_candidates

Find elements ready for conversion (dependencies satisfied).

**Parameters:**
- `project_name` (required): Project name
- `layer` (optional): Filter by layer
- `limit` (optional): Maximum results (default: 20)

**Returns:**
- `candidates`: Elements whose dependencies are all converted
- `candidates_count`: Number of ready elements

**Example:**
```
get_conversion_candidates(project_name="Linkpay_ADM", layer="ui", limit=10)
```

#### mark_converted

Mark an element as converted (WRITE OPERATION).

**Parameters:**
- `element_name` (required): Element name
- `project_name` (required): Project name
- `confirm` (required for execution): Must be True to execute
- `notes` (optional): Conversion notes

**Returns without confirm:**
- Preview of the change with `requires_confirmation: True`

**Returns with confirm=True:**
- `executed: True` with new status and timestamp

**Example:**
```
# Preview first
mark_converted(element_name="PAGE_Login", project_name="Linkpay_ADM")

# Then execute
mark_converted(element_name="PAGE_Login", project_name="Linkpay_ADM", confirm=True, notes="Route and template generated")
```

## Workflow Examples

### Example 1: Check Conversion Progress

Start by understanding current state:

```
get_conversion_stats(project_name="Linkpay_ADM")
```

Sample response:
```json
{
  "data": {
    "project": "Linkpay_ADM",
    "total_elements": 250,
    "completed": 45,
    "progress_percentage": 18.0,
    "by_status": {
      "pending": 180,
      "in_progress": 25,
      "converted": 40,
      "validated": 5
    },
    "by_layer": {
      "schema": {"converted": 20, "pending": 5},
      "ui": {"pending": 100, "in_progress": 25}
    }
  }
}
```

### Example 2: Find Next Elements to Convert

Get elements ready for conversion:

```
get_conversion_candidates(project_name="Linkpay_ADM", layer="ui", limit=5)
```

Sample response:
```json
{
  "data": {
    "candidates_count": 5,
    "candidates": [
      {"name": "PAGE_Login", "type": "page", "topological_order": 15},
      {"name": "PAGE_Home", "type": "page", "topological_order": 16}
    ]
  }
}
```

Then get full order for planning:

```
get_topological_order(project_name="Linkpay_ADM", layer="ui")
```

### Example 3: Convert Element and Mark Complete

1. **Get element context:**
```
get_element(element_name="PAGE_Login", project_name="Linkpay_ADM")
get_controls(element_name="PAGE_Login", project_name="Linkpay_ADM")
get_procedures(element_name="PAGE_Login", project_name="Linkpay_ADM", include_code=True)
```

2. **Generate code** (using templates from /wx-convert:phase)

3. **Preview the status change:**
```
mark_converted(element_name="PAGE_Login", project_name="Linkpay_ADM")
```

4. **Execute the change:**
```
mark_converted(element_name="PAGE_Login", project_name="Linkpay_ADM", confirm=True, notes="Route, template, models generated")
```

## Troubleshooting

### MCP Server Not Starting

**Symptoms:**
- "ModuleNotFoundError: No module named 'wxcode'"
- Connection refused

**Solutions:**
1. Verify PYTHONPATH in .mcp.json includes `src/` directory
2. Check Python version is 3.11+
3. Verify all dependencies installed: `pip install -e .`

### Neo4j Unavailable

**Symptoms:**
- Graph tools return "Neo4j unavailable" error
- Impact analysis fails

**Solutions:**
1. Graph tools gracefully degrade when Neo4j is unavailable
2. Start Neo4j: `docker-compose up neo4j`
3. Sync graph: `wxcode sync-neo4j ProjectName`

Non-graph tools (elements, controls, procedures, schema, conversion) work without Neo4j.

### Element Not Found

**Symptoms:**
- "Element 'X' not found in project 'Y'"
- Empty results from queries

**Solutions:**
1. Verify project was imported: `wxcode list-projects`
2. Check element name spelling (case-sensitive)
3. If element exists in multiple projects, specify `project_name`
4. Re-import if needed: `wxcode import project.wwp`

### Confirmation Required Errors

**Symptoms:**
- mark_converted returns `requires_confirmation: True`
- Status not changing

**Solutions:**
1. This is expected behavior - write operations require explicit confirmation
2. First call without `confirm` to preview the change
3. Then call with `confirm=True` to execute
4. If you want to abort, simply don't call with confirm=True

### Slow Performance

**Symptoms:**
- Long response times for list operations
- Timeouts on large projects

**Solutions:**
1. Use `limit` parameter to reduce result set
2. Filter by `layer` or `source_type` when possible
3. For graph analysis, ensure Neo4j indexes are created
4. Consider running `wxcode analyze` to update topological order

## GSD Templates

Two slash commands are available for conversion workflow:

### /wx-convert:milestone

Use for converting a complete module or feature set:
- Guides through Discovery, Conversion, and Validation phases
- References all relevant MCP tools
- Includes success criteria checklist

### /wx-convert:phase

Use for converting a single element:
- Step-by-step context gathering from KB
- Code generation patterns for models, routes, templates
- Type and control mapping tables
- Verification checklist

## Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Project overview and WLanguage reference
- [docs/architecture.md](architecture.md) - Target stack architecture
- [docs/adr/](adr/) - Architectural decision records
