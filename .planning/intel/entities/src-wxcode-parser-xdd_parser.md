---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/xdd_parser.py
type: module
updated: 2026-01-21
status: active
---

# xdd_parser.py

## Purpose

Parses WinDev Analysis files (.xdd) containing database schema definitions. Extracts tables, columns with types, primary/foreign keys, indexes, and relationships. Produces DatabaseSchema document that drives Pydantic model generation in the schema conversion layer.

## Exports

- `XDDParser` - Class for parsing Analysis files
- `parse_xdd(file_path)` - Parse .xdd file returning DatabaseSchema
- `extract_tables(content)` - Extract table definitions
- `extract_relations(content)` - Extract foreign key relationships

## Dependencies

- [[src-wxcode-models-schema]] - DatabaseSchema, SchemaTable, SchemaColumn models
- xml.etree - XML parsing for .xdd format
- re - Regular expression for type parsing

## Used By

TBD
