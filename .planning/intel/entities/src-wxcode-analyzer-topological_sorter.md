---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/analyzer/topological_sorter.py
type: module
updated: 2026-01-21
status: active
---

# topological_sorter.py

## Purpose

Performs layer-aware topological sorting of the dependency graph. Orders elements so dependencies are processed before dependents while respecting conversion layers (Schema -> Domain -> Business -> API -> UI). Handles cycles by breaking them at suggested points. Critical for correct conversion ordering.

## Exports

- `TopologicalSorter` - Class for sorting dependency graphs
- `sort(graph)` - Return elements in dependency-respecting order
- `sort_by_layer(graph)` - Sort within each conversion layer separately

## Dependencies

- [[src-wxcode-analyzer-models]] - GraphNode, GraphEdge, AnalysisResult
- [[src-wxcode-analyzer-cycle_detector]] - Cycle detection and breaking
- networkx - Graph algorithms

## Used By

TBD
