---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/wdg_parser.py
type: module
updated: 2026-01-21
status: active
---

# wdg_parser.py

## Purpose

Parses WinDev procedure group files (.wdg) to extract server-side procedures. Handles procedure declarations with parameters, return types, and body code. Identifies procedure scope (local/global) and compilation targets (server/browser). Essential for service layer conversion.

## Exports

- `WDGParser` - Class for parsing procedure group files
- `parse_wdg(content)` - Parse .wdg content returning list of procedures
- `extract_procedures(content)` - Extract procedure definitions with signatures

## Dependencies

- [[src-wxcode-models-procedure]] - Procedure document creation
- re - Regular expression parsing for WLanguage syntax

## Used By

TBD
