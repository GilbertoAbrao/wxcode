---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/graph/impact_analyzer.py
type: service
updated: 2026-01-21
status: active
---

# impact_analyzer.py

## Purpose

Performs graph analysis using Neo4j for advanced dependency queries. Provides impact analysis (what changes if I modify X?), path finding between elements, hub detection (highly connected nodes), and dead code identification. Leverages Cypher queries for efficient graph traversal across large codebases.

## Exports

- `ImpactAnalyzer` - Class for Neo4j-based graph analysis
- `analyze_impact(element_name, depth)` - Find all elements affected by changes to given element
- `find_path(source, target)` - Find dependency path between two elements
- `find_hubs(min_connections)` - Find highly connected elements
- `find_dead_code()` - Find elements with no incoming dependencies

## Dependencies

- [[src-wxcode-config]] - Neo4j connection settings
- neo4j - Neo4j Python driver
- asyncio - Async Neo4j operations

## Used By

TBD
