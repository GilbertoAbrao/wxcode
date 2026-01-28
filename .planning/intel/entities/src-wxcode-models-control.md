---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/control.py
type: model
updated: 2026-01-21
status: active
---

# control.py

## Purpose

Defines the Control Beanie document representing UI controls within WinDev pages/windows. Stores control hierarchy (parent-child relationships), properties, events with code, and data binding information. Critical for UI-to-template conversion capturing control positioning, visibility, and behavior.

## Exports

- `ControlEvent` - Pydantic model for control events (OnClick, OnChange, etc.) with code
- `ControlCodeBlock` - Pydantic model for code blocks associated with controls
- `ControlDataBinding` - Pydantic model for table/field bindings
- `Control` - Beanie Document with control hierarchy, properties, events, and bindings

## Dependencies

- [[src-wxcode-models-control_type]] - ControlTypeDefinition link
- beanie - Document ODM
- pydantic - Data validation

## Used By

TBD
