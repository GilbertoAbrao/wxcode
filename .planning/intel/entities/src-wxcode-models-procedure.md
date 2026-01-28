---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/procedure.py
type: model
updated: 2026-01-21
status: active
---

# procedure.py

## Purpose

Defines the Procedure Beanie document representing WLanguage procedures extracted from .wdg files or embedded in pages. Stores procedure signature, parameters, return type, body code, visibility scope, and compilation context (browser vs server). Essential for service layer conversion.

## Exports

- `ProcedureParameter` - Pydantic model for procedure parameters with type and default
- `ProcedureScope` - Enum for visibility (LOCAL, GLOBAL, PUBLIC, PRIVATE)
- `CompilationTarget` - Enum for execution context (SERVER, BROWSER, BOTH)
- `Procedure` - Beanie Document with full procedure definition and metadata

## Dependencies

- [[src-wxcode-models-project]] - Project link
- [[src-wxcode-models-element]] - Element link (parent container)
- beanie - Document ODM
- pydantic - Data validation

## Used By

TBD
