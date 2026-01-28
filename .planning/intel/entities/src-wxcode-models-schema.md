---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/schema.py
type: model
updated: 2026-01-21
status: active
---

# schema.py

## Purpose

Defines Beanie documents for WinDev database schema (Analysis) representation. Models tables, columns with types, indexes, and foreign key relationships extracted from .xdd files. Serves as the foundation for Pydantic model generation in the schema conversion layer.

## Exports

- `ColumnType` - Enum mapping WinDev column types to Python equivalents
- `SchemaColumn` - Pydantic model for table columns with name, type, nullable, key flags
- `SchemaIndex` - Pydantic model for table indexes
- `SchemaRelation` - Pydantic model for foreign key relationships
- `SchemaTable` - Pydantic model for complete table definition
- `DatabaseSchema` - Beanie Document containing all tables for a project

## Dependencies

- [[src-wxcode-models-project]] - Project link
- beanie - Document ODM
- pydantic - Data validation

## Used By

TBD
