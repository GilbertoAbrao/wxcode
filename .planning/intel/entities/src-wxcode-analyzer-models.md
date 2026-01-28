---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/analyzer/models.py
type: model
updated: 2026-01-21
status: active
---

# models.py (analyzer)

## Purpose

Defines Pydantic models for dependency graph analysis results. Represents graph nodes, edges, detected cycles, and overall analysis output. Used by graph builder, cycle detector, and topological sorter to communicate analysis results.

## Exports

- `GraphNode` - Pydantic model for graph vertices with element info and layer
- `GraphEdge` - Pydantic model for dependencies with source, target, edge type
- `CycleInfo` - Pydantic model for detected cycles with nodes and suggested break points
- `AnalysisResult` - Pydantic model aggregating nodes, edges, cycles, layers, statistics

## Dependencies

- pydantic - Data validation and BaseModel
- [[src-wxcode-models-element]] - ElementType, ElementLayer enums

## Used By

TBD
