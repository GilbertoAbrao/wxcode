---
phase: 05-essential-retrieval-tools
plan: 02
subsystem: mcp-tools
tags: [fastmcp, beanie, controls, data-binding, ui-hierarchy]

# Dependency graph
requires:
  - phase: 04-core-infrastructure
    provides: MCP server with lifespan, database connections
provides:
  - get_controls MCP tool for UI hierarchy queries
  - get_data_bindings MCP tool for control-to-table mappings
  - Control query patterns for future tools
affects: [05-03-procedures, 06-graph-tools, conversion-workflow]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - _find_element helper for project-scoped element lookup
    - Control hierarchy sorted by full_path (depth-first order)
    - Error dict response pattern for MCP tools

key-files:
  created:
    - src/wxcode/mcp/tools/controls.py
  modified:
    - src/wxcode/mcp/tools/__init__.py

key-decisions:
  - "Duplicate _find_element helper in controls.py (elements.py runs in parallel)"
  - "Include role field in events for browser/server distinction"
  - "Query both data_binding and is_bound fields for complete binding coverage"

patterns-established:
  - "Control tools return hierarchy sorted by full_path for tree order"
  - "Type names resolved via ControlTypeDefinition lookup"
  - "Bindings include variable_name and binding_path for complex cases"

# Metrics
duration: 4min
completed: 2026-01-22
---

# Phase 5 Plan 02: Control Tools Summary

**MCP tools for UI control hierarchy and data binding queries, enabling page structure analysis for conversion**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-22T00:00:00Z
- **Completed:** 2026-01-22T00:04:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `get_controls` tool returns full control hierarchy with type names, events, and properties
- `get_data_bindings` tool extracts control-to-table field mappings
- Integrated with existing Control and ControlTypeDefinition models
- Error handling follows established MCP tool patterns

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement control tools** - `42da085` (feat)
2. **Task 2: Register controls module** - `2b6270a` (chore)

## Files Created/Modified

- `src/wxcode/mcp/tools/controls.py` - 270 lines, get_controls and get_data_bindings tools
- `src/wxcode/mcp/tools/__init__.py` - Added controls import and __all__ entry

## Decisions Made

1. **Duplicated _find_element helper** - Since 05-01 (elements.py) runs in parallel, duplicated the element lookup helper to avoid import race. Can be refactored to shared module later.

2. **Include event role field** - Added `role` (B=Browser, S=Server) to event info since it's critical for understanding where code executes.

3. **Query both data_binding and is_bound** - Used `$or` query to catch all bound controls, as some may have is_bound=True without full data_binding info.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation followed research patterns from gsd_context_collector.py.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Control tools ready for use in Claude Code
- 3 tools now registered in MCP server (1 from 05-01 + 2 from this plan)
- Ready for 05-03 (procedure tools) to complete essential retrieval set

---
*Phase: 05-essential-retrieval-tools*
*Completed: 2026-01-22*
