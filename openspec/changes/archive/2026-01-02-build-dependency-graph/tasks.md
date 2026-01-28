# Tasks: build-dependency-graph

## Overview
Implementar o analisador de dependências (Fase 3.1) que constrói um grafo de relacionamentos e calcula a ordem topológica para conversão.

## Task List

### 1. Create Analyzer Models
**File**: `src/wxcode/analyzer/models.py`

- [x] 1.1 Create `NodeType` enum (TABLE, CLASS, PROCEDURE, PAGE, QUERY)
- [x] 1.2 Create `EdgeType` enum (INHERITS, USES_CLASS, CALLS_PROCEDURE, USES_TABLE)
- [x] 1.3 Create `GraphNode` model (id, name, node_type, layer, mongo_id, collection)
- [x] 1.4 Create `GraphEdge` model (source, target, edge_type, weight)
- [x] 1.5 Create `CycleInfo` model (nodes, suggested_break)
- [x] 1.6 Create `AnalysisResult` model (stats, cycles, topological_order, layers)
- [x] 1.7 Export models in `__init__.py`

**Validation**: ✅ Models importable, type hints correct

---

### 2. Implement GraphBuilder
**File**: `src/wxcode/analyzer/graph_builder.py`

- [x] 2.1 Create `GraphBuilder` class with NetworkX DiGraph
- [x] 2.2 Implement `_add_table_nodes()` from DatabaseSchema
- [x] 2.3 Implement `_add_class_nodes()` from ClassDefinition
- [x] 2.4 Implement `_add_class_edges()` (inheritance, uses_classes, uses_files)
- [x] 2.5 Implement `_add_procedure_nodes()` from Procedure
- [x] 2.6 Implement `_add_procedure_edges()` (calls_procedures, uses_files)
- [x] 2.7 Implement `_add_page_nodes()` from Element (type=PAGE)
- [x] 2.8 Implement `_add_page_edges()` (dependencies.uses)
- [x] 2.9 Implement `build()` async method that orchestrates all
- [x] 2.10 Handle missing dependencies gracefully (log warning, don't fail)

**Validation**: ✅ Graph built with correct node/edge counts

---

### 3. Implement CycleDetector
**File**: `src/wxcode/analyzer/cycle_detector.py`

- [x] 3.1 Create `CycleDetector` class
- [x] 3.2 Implement `detect_cycles()` using NetworkX
- [x] 3.3 Implement `_find_best_break_point()` (node with lowest in-degree)
- [x] 3.4 Implement `get_cycle_report()` for formatted output
- [x] 3.5 Implement `remove_cycle_edges()` for cycle-free subgraph

**Validation**: ✅ Cycles detected correctly, break points suggested

---

### 4. Implement TopologicalSorter
**File**: `src/wxcode/analyzer/topological_sorter.py`

- [x] 4.1 Create `TopologicalSorter` class
- [x] 4.2 Implement `_group_by_layer()` to separate nodes by layer
- [x] 4.3 Implement `_sort_within_layer()` topological sort per layer
- [x] 4.4 Implement `compute_order()` combining layers in correct sequence
- [x] 4.5 Handle cycles (use cycle-free subgraph)
- [x] 4.6 Return order_map: dict[node_id, order_number]

**Validation**: ✅ Order respects dependencies and layer hierarchy

---

### 5. Implement DependencyAnalyzer (Orchestrator)
**File**: `src/wxcode/analyzer/dependency_analyzer.py`

- [x] 5.1 Create `DependencyAnalyzer` class
- [x] 5.2 Implement `analyze()` async method (orchestrates builder, detector, sorter)
- [x] 5.3 Implement `get_statistics()` for summary stats
- [x] 5.4 Implement `persist_order()` to update MongoDB documents
- [x] 5.5 Implement `export_dot()` for GraphViz export
- [x] 5.6 Update exports in `analyzer/__init__.py`

**Validation**: ✅ Full analysis pipeline works end-to-end

---

### 6. Add CLI Command
**File**: `src/wxcode/cli.py`

- [x] 6.1 Update `analyze` command with DependencyAnalyzer
- [x] 6.2 Add `--export-dot` option (GraphViz DOT file)
- [x] 6.3 Add `--no-persist` option (don't persist to MongoDB)
- [x] 6.4 Display summary statistics with Rich panels
- [x] 6.5 Display layer assignment summary
- [x] 6.6 Display cycle details
- [x] 6.7 Handle errors gracefully

**Validation**: ✅ `wxcode analyze Linkpay_ADM` works

---

### 7. Create Unit Tests
**File**: `tests/test_analyzer.py`

- [x] 7.1 Test `GraphNode`, `GraphEdge`, `CycleInfo` models
- [x] 7.2 Test `CycleDetector` with known cycles
- [x] 7.3 Test `TopologicalSorter` with simple graph
- [x] 7.4 Test layer ordering (schema < domain < business < ui)
- [x] 7.5 Test handling of missing dependencies
- [x] 7.6 Test cycle break point selection
- [x] 7.7 Test integration pipeline

**Validation**: ✅ `pytest tests/test_analyzer.py` passes (29 tests)

---

### 8. End-to-End Test
- [x] 8.1 Run `analyze` on Linkpay_ADM
- [x] 8.2 Verify all nodes created (50 tables + 14 classes + 369 procedures + 60 pages = 493)
- [x] 8.3 Verify edge counts (951 calls_proc + 241 uses_table + 6 inherits + 3 uses_class = 1201)
- [x] 8.4 Verify cycles detected (1 cycle found)
- [x] 8.5 Verify topological_order persisted in MongoDB
- [x] 8.6 Verify layer assignment correct (schema:0-49, domain:50-63, business:64-432, ui:433-492)

**Validation**: ✅ All data consistent with MongoDB content

---

### 9. Documentation
- [x] 9.1 Update CLAUDE.md with analyze command
- [x] 9.2 Update CLAUDE.md status table (3.1 complete)
- [x] 9.3 Update file reference table with analyzer files

**Validation**: ✅ Documentation accurate and complete

---

## Dependencies
- Task 1 must complete before Tasks 2-5
- Tasks 2, 3, 4 can run in parallel
- Task 5 depends on Tasks 2, 3, 4
- Task 6 depends on Task 5
- Tasks 7-9 can run in parallel after Task 6

## Estimated Scope
- Models: ~80 lines ✅
- GraphBuilder: ~150 lines ✅
- CycleDetector: ~100 lines ✅
- TopologicalSorter: ~150 lines ✅
- DependencyAnalyzer: ~150 lines ✅
- CLI: ~100 lines ✅
- Tests: ~350 lines ✅
- **Total**: ~1080 lines ✅

## External Dependencies
- NetworkX (pip install networkx) ✅ Already installed
