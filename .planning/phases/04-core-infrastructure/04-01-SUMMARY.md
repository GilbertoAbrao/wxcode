---
phase: 04-core-infrastructure
plan: 01
subsystem: mcp-server
tags: [mcp, fastmcp, mongodb, neo4j, lifespan, stdio]
requires: [database.py, neo4j_connection.py]
provides: [mcp-server-package, app-lifespan, database-initialization]
affects: [phase-5-tools, phase-7-integration]
tech-stack:
  added: [fastmcp-2.14.3]
  patterns: [lifespan-context-manager, graceful-fallback, stderr-logging]
key-files:
  created:
    - src/wxcode/mcp/__init__.py
    - src/wxcode/mcp/server.py
  modified:
    - requirements.txt
decisions:
  - id: fastmcp-version
    choice: fastmcp<3 (v2.14.3)
    reason: v3 is beta with breaking changes
  - id: lifespan-pattern
    choice: asynccontextmanager decorator
    reason: FastMCP expects callable returning AbstractAsyncContextManager
  - id: neo4j-fallback
    choice: graceful fallback with warning
    reason: Neo4j is optional, server should start even if unavailable
metrics:
  duration: 3 minutes
  completed: 2026-01-22
---

# Phase 4 Plan 1: MCP Server Foundation Summary

FastMCP server with lifespan-based MongoDB/Neo4j initialization using STDIO transport.

## Objective Achieved

Created the foundational MCP Server package at `src/wxcode/mcp/` that:
- Initializes MongoDB via existing `init_db()` at startup (required)
- Initializes Neo4j with graceful fallback (optional)
- Logs only to stderr (stdout reserved for JSON-RPC)
- Runs via `python -m wxcode.mcp.server`

## Task Results

| Task | Name | Status | Commit | Key Changes |
|------|------|--------|--------|-------------|
| 1 | Add FastMCP dependency | Done | 18ffec4 | requirements.txt |
| 2 | Create MCP server package | Done | f2be677 | mcp/__init__.py, mcp/server.py |

## Decisions Made

### 1. FastMCP Version Pinning
**Decision:** Pin to `fastmcp<3` (installed v2.14.3)
**Rationale:** v3 is currently in beta (3.0.0b1) with breaking API changes. v2.14.x is stable and well-documented.
**Affects:** All future MCP development must use v2 API until upgrade decision.

### 2. Lifespan Implementation
**Decision:** Use `@asynccontextmanager` decorator from contextlib
**Rationale:** FastMCP's `lifespan` parameter expects a callable returning `AbstractAsyncContextManager[T]`, not a custom decorator. The research doc mentioned `@lifespan` decorator but the actual API uses standard Python async context managers.
**Code:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    # initialization
    yield {"mongo_client": ..., "neo4j_conn": ..., "neo4j_available": ...}
    # cleanup
```

### 3. Neo4j Graceful Fallback
**Decision:** Server starts even if Neo4j is unavailable
**Rationale:** Neo4j provides enhanced dependency analysis but is not required for core functionality. Tools should check `neo4j_available` before attempting Neo4j queries.
**Warning logged:** `Neo4j unavailable: {e}, using MongoDB only`

## Verification Results

All success criteria met:

- [x] FastMCP dependency installed (`fastmcp<3` in requirements.txt)
- [x] MCP server module exists at src/wxcode/mcp/server.py
- [x] Server starts via `python -m wxcode.mcp.server`
- [x] MongoDB connection established during startup (via init_db())
- [x] Neo4j connection attempted with graceful fallback
- [x] All logging goes to stderr only (stdout clean for JSON-RPC)

**Test output:**
```
2026-01-21 20:09:55 - __main__ - INFO - Starting wxcode MCP Server...
2026-01-21 20:09:57 - __main__ - INFO - MongoDB connected and Beanie initialized
2026-01-21 20:09:57 - __main__ - INFO - Neo4j connected
Starting MCP server 'wxcode-kb' with transport 'stdio'
```

## Deviations from Plan

### 1. Lifespan Decorator Import
**[Rule 3 - Blocking]** The research doc indicated `from fastmcp.server.lifespan import lifespan` but this module doesn't exist in FastMCP 2.14.3.
**Fix:** Used standard library `@asynccontextmanager` from contextlib instead.
**Commit:** f2be677

## Files Changed

**Created:**
- `src/wxcode/mcp/__init__.py` (6 lines) - Package marker with docstring
- `src/wxcode/mcp/server.py` (102 lines) - FastMCP server with lifespan

**Modified:**
- `requirements.txt` - Added `fastmcp<3`

## Key Code Patterns

### Lifespan Context for Tools
Tools will access database connections via `ctx.lifespan_context`:
```python
@mcp.tool
async def example_tool(ctx: Context) -> dict:
    neo4j_available = ctx.lifespan_context["neo4j_available"]
    neo4j_conn = ctx.lifespan_context["neo4j_conn"]
    # ...
```

### Logging Configuration
All logging configured to stderr before any imports that might log:
```python
handler = logging.StreamHandler(sys.stderr)
root.addHandler(handler)
```

## Next Phase Readiness

**Phase 5 (Read Tools) can proceed:**
- Server foundation is in place
- Lifespan provides database connections
- Tools can be registered via `@mcp.tool` decorator

**Prerequisites for Phase 5:**
- Import `mcp` from server module
- Access databases via `ctx.lifespan_context`
- Follow same stderr logging pattern

## Performance Notes

- Server startup: ~2 seconds (MongoDB + Neo4j connection)
- If Neo4j unavailable: ~5 seconds (connection timeout)
- Consider reducing Neo4j timeout for faster fallback in MCP context
