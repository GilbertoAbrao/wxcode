---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/global_state_context.py
type: model
updated: 2026-01-21
status: active
---

# global_state_context.py

## Purpose

Defines Pydantic models for global state intermediate representation (IR). Captures global variables, constants, and shared state patterns extracted from WinDev projects. Enables conversion to proper dependency injection or module-level state in Python.

## Exports

- `GlobalVariable` - Pydantic model for global variables with name, type, initial value, scope
- `GlobalStateContext` - Pydantic model aggregating all global state for a project

## Dependencies

- pydantic - Data validation and BaseModel

## Used By

TBD
