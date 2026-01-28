---
phase: 19
plan: 01
title: Connection Extraction
completed: 2026-01-24

subsystem: services
tags: [prompt-builder, schema-extractor, context-generation, connections]

requires:
  - phase-14 (PromptBuilder created)
  - phase-15 (schema_extractor created)

provides:
  - extract_connections_for_project() function
  - format_connections() method in PromptBuilder
  - format_env_example() method in PromptBuilder
  - CONTEXT.md sections for Database Connections and .env.example

affects:
  - future phases needing connection context
  - output project initialization flow

tech-stack:
  added: []
  patterns:
    - Static method formatters for template sections
    - Safe attribute access with getattr() for model fields

key-files:
  created: []
  modified:
    - src/wxcode/services/schema_extractor.py
    - src/wxcode/services/prompt_builder.py
    - src/wxcode/api/output_projects.py

decisions:
  - id: conn-01
    title: Use getattr() for connection field access
    choice: Safe attribute access with fallbacks
    rationale: Handles missing/None fields gracefully

metrics:
  duration: ~10 minutes
  tasks: 2/2
  commits: 2
---

# Phase 19 Plan 01: Connection Extraction Summary

**Connection extraction and CONTEXT.md extensions for database connection info**

## What Was Built

### Task 1: Connection extraction and PromptBuilder extensions

Added `extract_connections_for_project()` function to `schema_extractor.py`:
- Queries DatabaseSchema for project
- Returns schema.connections list (SchemaConnection objects)
- Returns empty list if no schema found

Added two static methods to `PromptBuilder`:

1. `format_connections(connections)` - Formats connections as markdown table:
   - Columns: Connection, Host, Port, Database, Driver
   - Uses `*local*`, `*default*`, `*n/a*` for empty values
   - Shows informative message when no connections

2. `format_env_example(connections, project_name)` - Generates .env.example:
   - Creates bash code block with environment variable placeholders
   - Variables: `{CONN_NAME}_HOST`, `_PORT`, `_DATABASE`, `_USER`, `_PASSWORD`
   - Includes driver info as comments

Extended `PROMPT_TEMPLATE` with two new sections:
- `## Database Connections` - Shows connection table
- `## Environment Variables (.env.example)` - Shows env variable placeholders

Updated `build_context()` and `write_context_file()` to accept `connections` parameter.

**Commit:** `c1ac6c7`

### Task 2: Wire API to extract and pass connections

Updated `output_projects.py`:
- Added import for `extract_connections_for_project`
- Called extraction function in `initialize_output_project()` WebSocket handler
- Pass connections to `PromptBuilder.write_context_file()`
- Added WebSocket info message with connection count

**Commit:** `4d47dfc`

## Decisions Made

1. **Safe attribute access**: Used `getattr(conn, 'field', default)` pattern for all connection field access. This handles cases where fields might be missing or None gracefully.

2. **Never expose extended_info**: The `extended_info` field may contain passwords or sensitive connection strings. It is intentionally never accessed or included in the output.

3. **Informative empty states**: When no connections exist, display informative messages rather than empty sections.

## Key Files

| File | Lines | Changes |
|------|-------|---------|
| `src/wxcode/services/schema_extractor.py` | 160 | +23 lines (extract_connections_for_project) |
| `src/wxcode/services/prompt_builder.py` | 295 | +79 lines (methods + template sections) |
| `src/wxcode/api/output_projects.py` | 420 | +12 lines (extraction call + wiring) |

## Example Output

### Database Connections section:
```markdown
| Connection | Host | Port | Database | Driver |
|------------|------|------|----------|--------|
| CNX_BASE_HOMOLOG | 192.168.1.100 | 1433 | LINKPAY_HOM | SQL Server |
| CNX_BASE_PROD | *local* | *default* | *n/a* | HyperFileSQL |
```

### Environment Variables section:
```bash
# Environment variables for my-project

# CNX_BASE_HOMOLOG (SQL Server)
CNX_BASE_HOMOLOG_HOST=
CNX_BASE_HOMOLOG_PORT=1433
CNX_BASE_HOMOLOG_DATABASE=
CNX_BASE_HOMOLOG_USER=
CNX_BASE_HOMOLOG_PASSWORD=
```

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

Phase 19 complete. Ready for Phase 20 (Global State Extraction).

### Blockers
None.

### Dependencies Provided
- Connection info now included in CONTEXT.md
- .env.example template helps starter projects configure database access
