---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/element.py
type: model
updated: 2026-01-21
status: active
---

# element.py

## Purpose

Defines the Element Beanie document representing individual WinDev project components (pages, procedures, classes, queries, reports). Core model for the conversion pipeline storing raw content, parsed AST, dependency graph, chunking for large files, and conversion status/output. Supports topological ordering for dependency-respecting conversion.

## Exports

- `ElementType` - Enum of WinDev element types (PAGE, PROCEDURE_GROUP, CLASS, QUERY, etc.)
- `ElementLayer` - Enum for conversion layers (SCHEMA, DOMAIN, BUSINESS, API, UI)
- `ConversionStatus` - Enum for conversion states (PENDING, IN_PROGRESS, CONVERTED, etc.)
- `ElementChunk` - Pydantic model for chunked content with token counts
- `ElementAST` - Pydantic model for parsed AST (procedures, variables, controls, events, queries)
- `ElementDependencies` - Pydantic model for dependency graph (uses, used_by, data_files)
- `ConvertedFile` - Pydantic model for generated output files
- `ElementConversion` - Pydantic model for conversion metadata
- `Element` - Beanie Document with full element data

## Dependencies

- [[src-wxcode-models-project]] - Project link reference
- beanie - Document ODM with Link support
- pydantic - Data validation and BaseModel

## Used By

TBD
