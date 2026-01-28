---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/dependency_extractor.py
type: module
updated: 2026-01-21
status: active
---

# dependency_extractor.py

## Purpose

Analyzes WLanguage code to extract dependency relationships between elements. Identifies procedure calls, class usage, table access (H* functions), and external API calls. Builds the dependency graph that drives topological sorting and impact analysis.

## Exports

- `DependencyExtractor` - Class for extracting dependencies from WLanguage code
- `extract_dependencies(code)` - Analyze code returning ElementDependencies
- `find_procedure_calls(code)` - Find calls to other procedures
- `find_table_access(code)` - Find HyperFile table operations

## Dependencies

- [[src-wxcode-models-element]] - ElementDependencies model
- [[src-wxcode-transpiler-hyperfile_catalog]] - H* function recognition
- re - Regular expression pattern matching

## Used By

TBD
