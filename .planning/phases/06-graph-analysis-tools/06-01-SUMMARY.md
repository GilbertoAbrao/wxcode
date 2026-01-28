---
phase: 06-graph-analysis-tools
plan: 01
subsystem: mcp-tools
tags: [neo4j, graph-analysis, mcp, dependencies]
requires:
  - phase-04-mcp-server
  - phase-05-retrieval-tools
provides:
  - get_dependencies tool for direct dependency lookup
  - get_impact tool for change impact analysis
  - get_path tool for path finding between elements
affects:
  - phase-06-plan-02 (adds remaining 3 graph tools)
tech-stack:
  added: []
  patterns:
    - Neo4j availability check helper
    - ImpactAnalyzer wrapper pattern
    - Dataclass-to-dict conversion for MCP responses
key-files:
  created:
    - src/wxcode/mcp/tools/graph.py
  modified:
    - src/wxcode/mcp/tools/__init__.py
decisions: []
metrics:
  duration: "1.5 minutes"
  completed: "2026-01-22"
---

# Phase 6 Plan 1: Core Graph Analysis Tools Summary

**One-liner:** 3 MCP tools wrapping ImpactAnalyzer for Neo4j dependency queries

## What Changed

1. **Created graph.py** with Neo4j graph analysis tools
   - `_check_neo4j` helper for graceful Neo4j unavailability handling
   - `get_dependencies` for direct 1-hop relationship queries (custom Cypher)
   - `get_impact` wrapping ImpactAnalyzer.get_impact with dataclass conversion
   - `get_path` wrapping ImpactAnalyzer.get_path for shortest path finding

2. **Registered graph module** in tools package
   - Added to docstring (documents all 6 tools, 3 implemented now)
   - Added import statement
   - Updated `__all__` to include graph

## Key Implementation Details

**Neo4j Availability Pattern:**
```python
def _check_neo4j(ctx: Context) -> tuple[Neo4jConnection | None, dict | None]:
    neo4j_available = ctx.request_context.lifespan_context.get("neo4j_available", False)
    if not neo4j_available:
        return None, {"error": True, "code": "NEO4J_UNAVAILABLE", ...}
    return ctx.request_context.lifespan_context["neo4j_conn"], None
```

**get_dependencies uses custom Cypher** (not ImpactAnalyzer) for direct 1-hop queries:
```python
query = """
MATCH (n {name: $name})
OPTIONAL MATCH (n)-[r]->(target)
WHERE target IS NOT NULL
RETURN type(r) as rel_type, target.name as name, labels(target)[0] as type
"""
```

**get_impact and get_path wrap ImpactAnalyzer** with dataclass-to-dict conversion for MCP serialization.

## Verification Results

All verifications pass:
- Tool imports work: get_dependencies, get_impact, get_path
- Graph module registered in tools.__all__
- MCP server loads all 12 tools without errors
- Tools handle Neo4j unavailability with structured error response

## Commits

| Commit | Description |
|--------|-------------|
| 4898db5 | feat(06-01): add core graph analysis MCP tools |
| 8e1a59e | chore(06-01): register graph module in tools package |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Ready for 06-02-PLAN.md:**
- graph.py structure supports adding 3 more tools (find_hubs, find_dead_code, find_cycles)
- Same patterns apply (Neo4j check + ImpactAnalyzer wrapper)
- All ImpactAnalyzer methods already exist and tested via CLI

**Remaining work in Phase 6:**
- Plan 02: Add find_hubs, find_dead_code, find_cycles tools
