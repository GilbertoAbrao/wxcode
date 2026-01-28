---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/global_state_extractor.py
type: module
updated: 2026-01-21
status: active
---

# global_state_extractor.py

## Purpose

Extracts global variable declarations and constants from WLanguage code. Identifies GLOBAL, PERSISTENT, and module-level variables that represent shared state. Produces GlobalStateContext for conversion to proper Python patterns (module globals, dependency injection, or configuration).

## Exports

- `GlobalStateExtractor` - Class for extracting global state
- `extract_globals(code)` - Find all global variable declarations
- `extract_constants(code)` - Find constant definitions

## Dependencies

- [[src-wxcode-models-global_state_context]] - GlobalStateContext, GlobalVariable models
- re - Regular expression pattern matching

## Used By

TBD
