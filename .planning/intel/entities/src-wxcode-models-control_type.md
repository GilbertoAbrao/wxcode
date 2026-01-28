---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/control_type.py
type: model
updated: 2026-01-21
status: active
---

# control_type.py

## Purpose

Defines ControlTypeDefinition Beanie document for cataloging WinDev control types discovered during parsing. Maps numeric type codes to human-readable names and tracks which controls are containers. Includes PREFIX_TO_TYPE mapping for inferring control types from naming conventions (EDT_, BTN_, IMG_, etc.).

## Exports

- `PREFIX_TO_TYPE` - Dict mapping control name prefixes to type codes
- `ControlTypeDefinition` - Beanie Document storing type_code, type_name, is_container flag, occurrence count, and example names

## Dependencies

- beanie - Document ODM
- pydantic - Data validation

## Used By

TBD
