---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/wdc_parser.py
type: module
updated: 2026-01-21
status: active
---

# wdc_parser.py

## Purpose

Parses WinDev class files (.wdc) to extract class definitions including inheritance, member properties, and methods. Handles WLanguage class syntax with constructors, destructors, and visibility modifiers. Foundation for domain layer conversion to Python classes.

## Exports

- `WDCParser` - Class for parsing .wdc class files
- `parse_wdc(content)` - Parse class content returning ClassDefinition
- `extract_members(content)` - Extract class properties with types
- `extract_methods(content)` - Extract method definitions

## Dependencies

- [[src-wxcode-models-class_definition]] - ClassDefinition document creation
- [[src-wxcode-models-procedure]] - Method as Procedure model
- re - Regular expression parsing

## Used By

TBD
