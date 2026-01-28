---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/project_mapper.py
type: module
updated: 2026-01-21
status: active
---

# project_mapper.py

## Purpose

Streaming parser that maps all elements from a WinDev project file (.wwp) to MongoDB. Processes the project structure efficiently using batched MongoDB inserts. Creates Project and Element documents while preserving raw content for later parsing. Foundation of the import pipeline.

## Exports

- `ProjectMapper` - Class that parses .wwp files and creates Element documents in batches
- `map_project(project_path, batch_size)` - Async function to import entire project

## Dependencies

- [[src-wxcode-models-project]] - Project document creation
- [[src-wxcode-models-element]] - Element document creation
- [[src-wxcode-parser-wwp_parser]] - Project file parsing
- [[src-wxcode-database]] - MongoDB batch operations

## Used By

TBD
