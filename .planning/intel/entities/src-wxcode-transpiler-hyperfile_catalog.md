---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/transpiler/hyperfile_catalog.py
type: util
updated: 2026-01-21
status: active
---

# hyperfile_catalog.py

## Purpose

Comprehensive catalog of WinDev HyperFile (H*) functions with their MongoDB/Beanie equivalents. Maps over 100 H* functions like HReadFirst, HAdd, HModify, HExecuteQuery to corresponding async MongoDB operations. Provides conversion templates with parameter mapping for accurate code transpilation.

## Exports

- `HYPERFILE_CATALOG` - Dict mapping H* function names to conversion info
- `get_mongo_equivalent(h_function)` - Get MongoDB equivalent for H* function
- `HFunctionInfo` - Dataclass with function name, params, return type, mongo equivalent

## Dependencies

- dataclasses - HFunctionInfo definition

## Used By

TBD
