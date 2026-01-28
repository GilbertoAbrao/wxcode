---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/analyzer/cycle_detector.py
type: module
updated: 2026-01-21
status: active
---

# cycle_detector.py

## Purpose

Detects cycles in the dependency graph that would prevent topological sorting. Identifies all strongly connected components (cycles) and suggests optimal edges to remove for breaking cycles while minimizing impact. Reports cycle information for manual review when needed.

## Exports

- `CycleDetector` - Class for detecting cycles in dependency graphs
- `detect_cycles(graph)` - Find all cycles returning CycleInfo list
- `suggest_breaks(cycle)` - Suggest which edges to remove to break cycle

## Dependencies

- [[src-wxcode-analyzer-models]] - CycleInfo model
- networkx - Graph cycle detection algorithms

## Used By

TBD
